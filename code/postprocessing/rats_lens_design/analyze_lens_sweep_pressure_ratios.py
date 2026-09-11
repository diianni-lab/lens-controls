#!/usr/bin/env python3
"""Measure lens-sweep pressure ratios in no-lens focal volumes."""

from __future__ import annotations

import argparse
import csv
import json
import os
import platform
import re
import sys
from pathlib import Path

import nibabel as nib
import numpy as np

NIFTI_UTILS_DIR = (
    Path(__file__).resolve().parents[1]
    / "transcranial_propagation"
)
sys.path.insert(0, str(NIFTI_UTILS_DIR))

from nifti_masks import same_grid, save_mask


DB_LEVELS = (6, 12)
PILLARED_PATTERN = re.compile(
    r"pressure_corrected_pw(?P<pillar>[\dp]+)mm_"
    r"th(?P<thickness>[\dp]+)mm\.nii\.gz"
)

SUMMARY_COLUMNS = [
    "db_level",
    "condition",
    "corrected",
    "seed",
    "pillar_width_mm",
    "thickness_mm",
    "nominal_thickness_mm",
    "flat_thickness_mm",
    "avg_p_in",
    "avg_p_out",
    "ratio",
    "pressure_file",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--simulation-root",
        type=Path,
        required=True,
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        required=True,
    )
    return parser.parse_args()


def relative_path(path: Path, directory: Path) -> str:
    return Path(os.path.relpath(path, directory)).as_posix()


def number_tag(value: float) -> str:
    return f"{value:.2f}".replace(".", "p")


def tag_value(tag: str) -> float:
    return float(tag.replace("p", "."))


def pressure_data(
    path: Path,
    reference: nib.Nifti1Image,
) -> np.ndarray:
    image = nib.load(str(path))
    if not same_grid(image, reference):
        raise ValueError(f"Pressure grid mismatch: {path}")
    return np.asanyarray(image.dataobj).astype(
        np.float32, copy=False
    )


def flat_cases(
    simulation_root: Path,
    output_dir: Path,
) -> list[dict[str, object]]:
    calibration_path = (
        simulation_root
        / "calibration"
        / "equivalent_uniform_thicknesses.csv"
    )
    with calibration_path.open(newline="") as handle:
        calibration = list(csv.DictReader(handle))

    cases = []
    for row in calibration:
        nominal_mm = float(row["nominal_thickness_mm"])
        flat_mm = float(row["uniform_thickness_mm"])
        tag = number_tag(flat_mm)

        for corrected in (0, 1):
            correction_label = (
                "corrected" if corrected else "uncorrected"
            )
            pressure_path = (
                simulation_root
                / "flat_lens"
                / f"pressure_{correction_label}_th{tag}mm.nii.gz"
            )
            cases.append(
                {
                    "condition": "flat_lens",
                    "corrected": corrected,
                    "seed": 1,
                    "pillar_width_mm": "",
                    "thickness_mm": tag_value(tag),
                    "nominal_thickness_mm": nominal_mm,
                    "flat_thickness_mm": flat_mm,
                    "pressure_path": pressure_path,
                    "pressure_file": relative_path(
                        pressure_path, output_dir
                    ),
                }
            )
    return cases


def pillared_cases(
    simulation_root: Path,
    output_dir: Path,
) -> list[dict[str, object]]:
    cases = []
    pillared_root = simulation_root / "pillared_lens"

    for seed_dir in sorted(pillared_root.glob("seed_*")):
        seed = int(seed_dir.name.removeprefix("seed_"))
        for pressure_path in sorted(
            seed_dir.glob("pressure_corrected_*.nii.gz")
        ):
            match = PILLARED_PATTERN.fullmatch(
                pressure_path.name
            )
            if match is None:
                continue

            pillar_width_mm = tag_value(match["pillar"])
            nominal_mm = tag_value(match["thickness"])
            cases.append(
                {
                    "condition": "pillared_lens",
                    "corrected": 1,
                    "seed": seed,
                    "pillar_width_mm": pillar_width_mm,
                    "thickness_mm": nominal_mm,
                    "nominal_thickness_mm": nominal_mm,
                    "flat_thickness_mm": "",
                    "pressure_path": pressure_path,
                    "pressure_file": relative_path(
                        pressure_path, output_dir
                    ),
                }
            )
    return cases


def exclusion_mask(
    simulation_root: Path,
    reference: nib.Nifti1Image,
) -> tuple[np.ndarray, int]:
    mask_paths = sorted(
        (simulation_root / "flat_lens").glob(
            "lens_mask_*.nii.gz"
        )
    )
    mask_paths.extend(
        sorted(
            (
                simulation_root
                / "pillared_lens"
                / "seed_01"
            ).glob("lens_mask_*.nii.gz")
        )
    )

    last_lens_x = 0
    for path in mask_paths:
        image = nib.load(str(path))
        if not same_grid(image, reference):
            raise ValueError(f"Lens-mask grid mismatch: {path}")
        mask = np.asanyarray(image.dataobj) > 0
        occupied_x = np.any(mask, axis=(1, 2))
        indices = np.flatnonzero(occupied_x)
        last_lens_x = max(last_lens_x, int(indices[-1]))

    excluded = np.zeros(reference.shape[:3], dtype=bool)
    excluded[: last_lens_x + 1, :, :] = True
    return excluded, last_lens_x


def pressure_metrics(
    pressure: np.ndarray,
    focal_mask: np.ndarray,
    excluded: np.ndarray,
) -> tuple[float, float, float]:
    valid = ~excluded & np.isfinite(pressure)
    inside = focal_mask & valid
    outside = ~focal_mask & valid

    inside_mean = float(
        np.mean(pressure[inside], dtype=np.float64)
    )
    outside_mean = float(
        np.mean(pressure[outside], dtype=np.float64)
    )
    return inside_mean, outside_mean, inside_mean / outside_mean


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    no_lens_path = (
        args.simulation_root / "no_lens" / "pressure.nii.gz"
    )
    no_lens_image = nib.load(str(no_lens_path))
    no_lens_pressure = np.asanyarray(
        no_lens_image.dataobj
    ).astype(np.float32, copy=False)

    excluded, last_lens_x = exclusion_mask(
        args.simulation_root, no_lens_image
    )
    save_mask(
        args.output_dir / "exclusion_mask.nii.gz",
        excluded,
        no_lens_image,
    )

    focal_masks = {}
    thresholds_pa = {}
    no_lens_peak_pa = float(np.max(no_lens_pressure))
    for db_level in DB_LEVELS:
        threshold_pa = (
            no_lens_peak_pa * 10 ** (-db_level / 20)
        )
        focal_mask = no_lens_pressure >= threshold_pa
        focal_masks[db_level] = focal_mask
        thresholds_pa[db_level] = threshold_pa
        save_mask(
            args.output_dir
            / f"focal_volume_{db_level}db.nii.gz",
            focal_mask,
            no_lens_image,
        )

    no_lens_case = {
        "condition": "nolens",
        "corrected": 0,
        "seed": 0,
        "pillar_width_mm": "",
        "thickness_mm": "",
        "nominal_thickness_mm": "",
        "flat_thickness_mm": "",
        "pressure_path": no_lens_path,
        "pressure_file": relative_path(
            no_lens_path, args.output_dir
        ),
    }
    cases = [no_lens_case]
    cases.extend(flat_cases(args.simulation_root, args.output_dir))
    cases.extend(
        pillared_cases(args.simulation_root, args.output_dir)
    )

    rows = {db_level: [] for db_level in DB_LEVELS}
    for index, case in enumerate(cases, start=1):
        if case["condition"] == "nolens":
            pressure = no_lens_pressure
        else:
            pressure = pressure_data(
                case["pressure_path"], no_lens_image
            )

        for db_level in DB_LEVELS:
            inside_mean, outside_mean, ratio = pressure_metrics(
                pressure,
                focal_masks[db_level],
                excluded,
            )
            rows[db_level].append(
                {
                    "db_level": db_level,
                    "condition": case["condition"],
                    "corrected": case["corrected"],
                    "seed": case["seed"],
                    "pillar_width_mm": case[
                        "pillar_width_mm"
                    ],
                    "thickness_mm": case["thickness_mm"],
                    "nominal_thickness_mm": case[
                        "nominal_thickness_mm"
                    ],
                    "flat_thickness_mm": case[
                        "flat_thickness_mm"
                    ],
                    "avg_p_in": inside_mean,
                    "avg_p_out": outside_mean,
                    "ratio": ratio,
                    "pressure_file": case["pressure_file"],
                }
            )

        if index % 100 == 0 or index == len(cases):
            print(f"Processed {index}/{len(cases)} pressure files")

    summary_files = {}
    for db_level in DB_LEVELS:
        summary_path = (
            args.output_dir
            / f"pressure_ratios_{db_level}db.csv"
        )
        with summary_path.open("w", newline="") as handle:
            writer = csv.DictWriter(
                handle, fieldnames=SUMMARY_COLUMNS
            )
            writer.writeheader()
            writer.writerows(rows[db_level])
        summary_files[str(db_level)] = summary_path.name

    manifest = {
        "analysis": "lens-sweep pressure ratios",
        "simulationRoot": relative_path(
            args.simulation_root, args.output_dir
        ),
        "dbLevels": list(DB_LEVELS),
        "thresholdFraction": {
            str(db_level): 10 ** (-db_level / 20)
            for db_level in DB_LEVELS
        },
        "thresholdPa": {
            str(db_level): thresholds_pa[db_level]
            for db_level in DB_LEVELS
        },
        "noLensPeakPa": no_lens_peak_pa,
        "focalVolume": (
            "all no-lens voxels at or above the threshold"
        ),
        "exclusion": (
            "all x slices from the source through the last lens voxel"
        ),
        "lastExcludedXIndexZeroBased": last_lens_x,
        "pressureFiles": len(cases),
        "rowsPerDbLevel": len(cases),
        "summaries": summary_files,
        "software": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "nibabel": nib.__version__,
        },
    }
    (args.output_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n"
    )

    for db_level in DB_LEVELS:
        print(
            args.output_dir
            / f"pressure_ratios_{db_level}db.csv"
        )


if __name__ == "__main__":
    main()
