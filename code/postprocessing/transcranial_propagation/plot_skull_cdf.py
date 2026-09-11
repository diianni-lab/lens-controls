#!/usr/bin/env python3
"""Plot cohort skull pressure CDFs."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


NO_LENS_COLOR = "#345f9f"
LENS_COLOR = "#d8743c"
GRID_COLOR = "#d4d4d4"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--postprocessing-dir",
        type=Path,
        required=True,
    )
    return parser.parse_args()


def read_cdfs(
    cdf_path: Path,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    curves: dict[
        str,
        dict[str, list[tuple[float, float]]],
    ] = {"nolens": {}, "lens": {}}

    with cdf_path.open(newline="") as handle:
        for row in csv.DictReader(handle):
            curves[row["condition"]].setdefault(
                row["subjectId"], []
            ).append(
                (
                    float(row["normalizedPressure"]),
                    float(row["cumulativeProbability"]),
                )
            )

    subjects = sorted(curves["nolens"])
    grid = np.asarray(
        [value[0] for value in curves["nolens"][subjects[0]]]
    )
    no_lens = np.vstack(
        [
            [value[1] for value in curves["nolens"][subject]]
            for subject in subjects
        ]
    )
    lens = np.vstack(
        [
            [value[1] for value in curves["lens"][subject]]
            for subject in subjects
        ]
    )
    return grid, no_lens, lens


def apply_style() -> None:
    plt.rcParams.update(
        {
            "font.family": "Arial",
            "font.size": 12.0,
            "axes.labelsize": 12.0,
            "xtick.labelsize": 10.8,
            "ytick.labelsize": 10.8,
            "axes.linewidth": 1.2,
            "savefig.dpi": 300,
            "figure.dpi": 300,
            "svg.fonttype": "none",
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
        }
    )


def main() -> None:
    args = parse_args()
    grid, no_lens, lens = read_cdfs(
        args.postprocessing_dir / "cdf.csv"
    )
    apply_style()

    no_lens_q25, no_lens_median, no_lens_q75 = (
        np.percentile(no_lens, [25, 50, 75], axis=0)
    )
    lens_q25, lens_median, lens_q75 = np.percentile(
        lens, [25, 50, 75], axis=0
    )

    figure, axes = plt.subplots(figsize=(3.2, 2.25))
    axes.fill_between(
        grid,
        no_lens_q25,
        no_lens_q75,
        color=NO_LENS_COLOR,
        alpha=0.16,
        linewidth=0,
    )
    axes.fill_between(
        grid,
        lens_q25,
        lens_q75,
        color=LENS_COLOR,
        alpha=0.16,
        linewidth=0,
    )
    axes.plot(
        grid,
        no_lens_median,
        color=NO_LENS_COLOR,
        linewidth=1.8,
        label="Active",
    )
    axes.plot(
        grid,
        lens_median,
        color=LENS_COLOR,
        linewidth=1.8,
        label="Control",
    )
    axes.set_xlim(0.0, 1.0)
    axes.set_ylim(0.0, 1.04)
    axes.set_xticks(np.linspace(0.0, 1.0, 6))
    axes.set_yticks(np.linspace(0.0, 1.0, 5))
    axes.set_xlabel("Normalized pressure")
    axes.set_ylabel("Cumulative probability")
    axes.grid(
        color=GRID_COLOR,
        linewidth=0.55,
        alpha=0.75,
    )
    axes.set_axisbelow(True)
    axes.spines["top"].set_visible(False)
    axes.spines["right"].set_visible(False)
    for side in ("left", "bottom"):
        axes.spines[side].set_color("#4d4d4d")
        axes.spines[side].set_linewidth(0.8)
    axes.legend(
        frameon=False,
        loc="lower right",
        handlelength=2.4,
    )

    figure.subplots_adjust(
        left=0.18,
        right=0.98,
        bottom=0.22,
        top=0.98,
    )
    output_path = args.postprocessing_dir / "cdf"
    for extension in ("png", "pdf", "svg"):
        figure.savefig(
            output_path.with_suffix(f".{extension}"),
            dpi=300,
            bbox_inches="tight",
            facecolor="white",
        )
    plt.close(figure)
    print(output_path)


if __name__ == "__main__":
    main()
