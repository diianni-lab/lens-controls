#!/usr/bin/env python3
"""Measure rat pressure within the localized skull region."""

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

from nifti_masks import same_grid, save_mask


SKULL_LABEL = 2
CYLINDER_RADIUS_MM = 4.0
CYLINDER_LENGTH_MM = 10.0

SUMMARY_COLUMNS = [
    "subjectId",
    "condition",
    "status",
    "pressureFile",
    "analysisMaskFile",
    "analysisVoxels",
    "skullMeanKPa",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--simulation-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--subjects", nargs="+", required=True)
    return parser.parse_args()


def relative_path(path: Path, directory: Path) -> str:
    return Path(os.path.relpath(path, directory)).as_posix()


def source_cylinder(image: nib.Nifti1Image) -> np.ndarray:
    spacing_mm = nib.affines.voxel_sizes(image.affine)
    shape = image.shape[:3]
    center_y = (shape[1] - 1) // 2
    center_z = (shape[2] - 1) // 2

    depth_mm = np.arange(shape[0])[:, None, None] * spacing_mm[0]
    ml_mm = (
        np.arange(shape[1])[None, :, None] - center_y
    ) * spacing_mm[1]
    ap_mm = (
        np.arange(shape[2])[None, None, :] - center_z
    ) * spacing_mm[2]

    return (
        (depth_mm <= CYLINDER_LENGTH_MM)
        & (
            ml_mm**2 + ap_mm**2
            <= CYLINDER_RADIUS_MM**2
        )
    )


def condition_row(
    subject_id: str,
    condition: str,
    pressure_path: Path,
    pressure: np.ndarray,
    analysis_mask: np.ndarray,
    analysis_mask_path: Path,
    output_dir: Path,
) -> dict[str, object]:
    skull_mean_kpa = float(
        np.mean(
            pressure[analysis_mask], dtype=np.float64
        )
        / 1e3
    )
    return {
        "subjectId": subject_id,
        "condition": condition,
        "status": "ok",
        "pressureFile": relative_path(
            pressure_path, output_dir
        ),
        "analysisMaskFile": relative_path(
            analysis_mask_path, output_dir
        ),
        "analysisVoxels": int(
            np.count_nonzero(analysis_mask)
        ),
        "skullMeanKPa": skull_mean_kpa,
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
        (segmentation == SKULL_LABEL)
        & source_cylinder(no_lens_image)
        & np.isfinite(no_lens_pressure)
        & np.isfinite(lens_pressure)
    )

    analysis_mask_path = (
        output_dir / "masks" / f"{subject_id}_skull_mask.nii.gz"
    )
    save_mask(
        analysis_mask_path, analysis_mask, no_lens_image
    )

    return [
        condition_row(
            subject_id,
            "nolens",
            no_lens_path,
            no_lens_pressure,
            analysis_mask,
            analysis_mask_path,
            output_dir,
        ),
        condition_row(
            subject_id,
            "lens",
            lens_path,
            lens_pressure,
            analysis_mask,
            analysis_mask_path,
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
        "analysis": "pressure within the localized skull region",
        "simulationRoot": relative_path(
            args.simulation_root, args.output_dir
        ),
        "subjects": args.subjects,
        "skullLabel": SKULL_LABEL,
        "cylinder": {
            "radiusMm": CYLINDER_RADIUS_MM,
            "lengthMm": CYLINDER_LENGTH_MM,
            "axis": "k-Wave +x depth axis through source center",
            "depthRangeMm": [0.0, CYLINDER_LENGTH_MM],
            "center": "source ML/AP axis",
        },
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
