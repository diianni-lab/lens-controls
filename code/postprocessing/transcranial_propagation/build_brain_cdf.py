#!/usr/bin/env python3
"""Build per-subject brain pressure CDF data."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

import nibabel as nib
import numpy as np


GRID_POINTS = 501
OUTPUT_COLUMNS = [
    "subjectId",
    "condition",
    "normalizedPressure",
    "cumulativeProbability",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--postprocessing-dir",
        type=Path,
        required=True,
    )
    return parser.parse_args()


def read_rows(
    summary_path: Path,
) -> dict[str, dict[str, dict[str, str]]]:
    rows: dict[str, dict[str, dict[str, str]]] = {}
    with summary_path.open(newline="") as handle:
        for row in csv.DictReader(handle):
            rows.setdefault(row["subjectId"], {})[
                row["condition"]
            ] = row
    return rows


def input_path(directory: Path, value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else directory / path


def pressure_values(
    pressure_path: Path,
    mask: np.ndarray,
) -> np.ndarray:
    pressure = np.asanyarray(
        nib.load(str(pressure_path)).dataobj
    ).astype(np.float32, copy=False)
    return pressure[
        mask & np.isfinite(pressure)
    ].astype(np.float64, copy=False) / 1e3


def empirical_cdf(
    values: np.ndarray,
    grid: np.ndarray,
) -> np.ndarray:
    return np.searchsorted(
        np.sort(values), grid, side="right"
    ) / values.size


def main() -> None:
    args = parse_args()
    rows = read_rows(args.postprocessing_dir / "summary.csv")
    grid = np.linspace(0.0, 1.0, GRID_POINTS)
    output_path = args.postprocessing_dir / "cdf.csv"

    with output_path.open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(OUTPUT_COLUMNS)

        for subject_id in sorted(rows):
            no_lens = rows[subject_id]["nolens"]
            lens = rows[subject_id]["lens"]

            mask_path = input_path(
                args.postprocessing_dir,
                no_lens["insideMaskFile"],
            )
            mask = np.asanyarray(
                nib.load(str(mask_path)).dataobj
            ) > 0

            no_lens_values = pressure_values(
                input_path(
                    args.postprocessing_dir,
                    no_lens["pressureFile"],
                ),
                mask,
            )
            lens_values = pressure_values(
                input_path(
                    args.postprocessing_dir,
                    lens["pressureFile"],
                ),
                mask,
            )

            combined = np.concatenate(
                [no_lens_values, lens_values]
            )
            minimum = combined.min()
            span = combined.max() - minimum

            for condition, values in (
                ("nolens", no_lens_values),
                ("lens", lens_values),
            ):
                normalized = np.clip(
                    (values - minimum) / span,
                    0.0,
                    1.0,
                )
                cdf = empirical_cdf(normalized, grid)
                writer.writerows(
                    zip(
                        [subject_id] * GRID_POINTS,
                        [condition] * GRID_POINTS,
                        grid,
                        cdf,
                    )
                )

    print(output_path)


if __name__ == "__main__":
    main()
