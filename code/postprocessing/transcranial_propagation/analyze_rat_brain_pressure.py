#!/usr/bin/env python3
"""Measure rat pressure inside the no-lens -6 dB brain region."""

from __future__ import annotations

import argparse
import csv
import json
import os
import platform
from pathlib import Path

import nibabel as nib
import numpy as np
import scipy
from scipy import ndimage

from nifti_masks import same_grid, save_mask


DB_LEVEL = -6.0
THRESHOLD_FRACTION = 10 ** (DB_LEVEL / 20.0)
BRAIN_LABEL = 1

SUMMARY_COLUMNS = [
    "subjectId",
    "condition",
    "status",
    "pressureFile",
    "insideMaskFile",
    "insideVoxels",
    "insideMeanKPa",
    "outsideMeanKPa",
    "insideOutsideMeanRatio",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--simulation-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--subjects", nargs="+", required=True)
    return parser.parse_args()


def relative_path(path: Path, directory: Path) -> str:
    return Path(os.path.relpath(path, directory)).as_posix()


def inside_region(
    no_lens_pressure: np.ndarray,
    analysis_mask: np.ndarray,
) -> np.ndarray:
    masked_pressure = np.where(
        analysis_mask, no_lens_pressure, -np.inf
    )
    peak_index = np.unravel_index(
        int(np.argmax(masked_pressure)),
        no_lens_pressure.shape,
    )
    threshold = (
        THRESHOLD_FRACTION * masked_pressure[peak_index]
    )
    threshold_mask = (
        analysis_mask
        & np.isfinite(no_lens_pressure)
        & (no_lens_pressure >= threshold)
    )

    connectivity = ndimage.generate_binary_structure(
        rank=3, connectivity=3
    )
    labels, _ = ndimage.label(
        threshold_mask, structure=connectivity
    )
    peak_label = labels[peak_index]
    return labels == peak_label


def condition_row(
    subject_id: str,
    condition: str,
    pressure_path: Path,
    pressure: np.ndarray,
    inside_mask: np.ndarray,
    outside_mask: np.ndarray,
    inside_mask_path: Path,
    output_dir: Path,
) -> dict[str, object]:
    inside_mean_kpa = float(
        np.mean(pressure[inside_mask], dtype=np.float64) / 1e3
    )
    outside_mean_kpa = float(
        np.mean(pressure[outside_mask], dtype=np.float64) / 1e3
    )
    return {
        "subjectId": subject_id,
        "condition": condition,
        "status": "ok",
        "pressureFile": relative_path(
            pressure_path, output_dir
        ),
        "insideMaskFile": relative_path(
            inside_mask_path, output_dir
        ),
        "insideVoxels": int(np.count_nonzero(inside_mask)),
        "insideMeanKPa": inside_mean_kpa,
        "outsideMeanKPa": outside_mean_kpa,
        "insideOutsideMeanRatio": (
            inside_mean_kpa / outside_mean_kpa
        ),
    }


def analyze_subject(
    subject_id: str,
    simulation_root: Path,
    output_dir: Path,
) -> list[dict[str, object]]:
    simulation_dir = simulation_root / subject_id

    no_lens_path = simulation_dir / "pressure_no_lens.nii.gz"
    lens_path = simulation_dir / "pressure_lens.nii.gz"
    segmentation_path = (
        simulation_dir / "segmentation_labels.nii.gz"
    )

    no_lens_image = nib.load(str(no_lens_path))
    lens_image = nib.load(str(lens_path))
    segmentation_image = nib.load(str(segmentation_path))
    if not same_grid(no_lens_image, lens_image):
        raise ValueError(
            f"Pressure grid mismatch: {subject_id}"
        )
    if not same_grid(no_lens_image, segmentation_image):
        raise ValueError(
            f"Segmentation grid mismatch: {subject_id}"
        )

    no_lens_pressure = np.asanyarray(
        no_lens_image.dataobj
    ).astype(np.float32, copy=False)
    lens_pressure = np.asanyarray(
        lens_image.dataobj
    ).astype(np.float32, copy=False)
    segmentation = np.asanyarray(
        segmentation_image.dataobj
    )

    analysis_mask = (
        (segmentation == BRAIN_LABEL)
        & np.isfinite(no_lens_pressure)
        & np.isfinite(lens_pressure)
    )
    inside_mask = inside_region(
        no_lens_pressure, analysis_mask
    )
    outside_mask = analysis_mask & ~inside_mask

    inside_mask_path = (
        output_dir / "masks" / f"{subject_id}_inside_mask.nii.gz"
    )
    save_mask(inside_mask_path, inside_mask, no_lens_image)

    return [
        condition_row(
            subject_id,
            "nolens",
            no_lens_path,
            no_lens_pressure,
            inside_mask,
            outside_mask,
            inside_mask_path,
            output_dir,
        ),
        condition_row(
            subject_id,
            "lens",
            lens_path,
            lens_pressure,
            inside_mask,
            outside_mask,
            inside_mask_path,
            output_dir,
        ),
    ]


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "masks").mkdir(exist_ok=True)

    rows = []
    for subject_id in args.subjects:
        rows.extend(
            analyze_subject(
                subject_id,
                args.simulation_root,
                args.output_dir,
            )
        )

    summary_path = args.output_dir / "summary.csv"
    with summary_path.open("w", newline="") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=SUMMARY_COLUMNS
        )
        writer.writeheader()
        writer.writerows(rows)

    manifest = {
        "analysis": "no-lens -6 dB brain region",
        "simulationRoot": relative_path(
            args.simulation_root, args.output_dir
        ),
        "subjects": args.subjects,
        "brainMask": "segmentation label 1",
        "dbLevel": DB_LEVEL,
        "thresholdFraction": THRESHOLD_FRACTION,
        "component": (
            "26-connected component containing the no-lens peak"
        ),
        "coverage": "simulation grid",
        "summary": "summary.csv",
        "maskDirectory": "masks",
        "software": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "nibabel": nib.__version__,
            "scipy": scipy.__version__,
        },
    }
    (args.output_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n"
    )

    print(summary_path)


if __name__ == "__main__":
    main()
