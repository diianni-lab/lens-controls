#!/usr/bin/env python3
"""Plot paired brain inside/outside pressure ratios."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


VALUE_COLUMN = "insideOutsideMeanRatio"
Y_LABEL = "Pressure ratio in the brain"
Y_MAX = None
Y_TICKS = [0, 5, 10, 15]
OUTPUT_NAME = "pressure_ratio_boxplot"

NO_LENS_COLOR = "#345f9f"
LENS_COLOR = "#d8743c"
PAIR_COLOR = "#8c8c8c"
GRID_COLOR = "#d4d4d4"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--postprocessing-dir",
        type=Path,
        required=True,
    )
    return parser.parse_args()


def read_values(
    summary_path: Path,
) -> tuple[np.ndarray, np.ndarray]:
    values: dict[str, dict[str, float]] = {
        "nolens": {},
        "lens": {},
    }
    with summary_path.open(newline="") as handle:
        for row in csv.DictReader(handle):
            values[row["condition"]][row["subjectId"]] = float(
                row[VALUE_COLUMN]
            )

    subjects = sorted(values["nolens"])
    no_lens = np.asarray(
        [values["nolens"][subject] for subject in subjects]
    )
    lens = np.asarray(
        [values["lens"][subject] for subject in subjects]
    )
    return no_lens, lens


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
    no_lens, lens = read_values(
        args.postprocessing_dir / "summary.csv"
    )
    apply_style()

    figure, axes = plt.subplots(figsize=(3.1875, 3.20))
    positions = [1, 2]

    violin = axes.violinplot(
        [no_lens, lens],
        positions=positions,
        widths=0.72,
        showextrema=False,
    )
    for body, color in zip(
        violin["bodies"],
        [NO_LENS_COLOR, LENS_COLOR],
    ):
        body.set_facecolor(color)
        body.set_edgecolor("none")
        body.set_alpha(0.22)

    box = axes.boxplot(
        [no_lens, lens],
        positions=positions,
        widths=0.28,
        patch_artist=True,
        showfliers=False,
        medianprops={
            "color": "#1f1f1f",
            "linewidth": 1.25,
        },
        boxprops={"linewidth": 1.0, "color": "#404040"},
        whiskerprops={"linewidth": 0.9, "color": "#404040"},
        capprops={"linewidth": 0.9, "color": "#404040"},
    )
    for patch, color in zip(
        box["boxes"],
        [NO_LENS_COLOR, LENS_COLOR],
    ):
        patch.set_facecolor(color)
        patch.set_alpha(0.28)

    jitter = np.random.default_rng(42).normal(
        0.0, 0.025, size=no_lens.size
    )
    for no_lens_value, lens_value, offset in zip(
        no_lens, lens, jitter
    ):
        axes.plot(
            [1 + offset, 2 + offset],
            [no_lens_value, lens_value],
            color=PAIR_COLOR,
            linewidth=0.55,
            alpha=0.34,
            zorder=1,
        )
    axes.scatter(
        np.full(no_lens.size, 1) + jitter,
        no_lens,
        s=13,
        color=NO_LENS_COLOR,
        alpha=0.88,
        linewidths=0,
        zorder=3,
    )
    axes.scatter(
        np.full(lens.size, 2) + jitter,
        lens,
        s=13,
        color=LENS_COLOR,
        alpha=0.88,
        linewidths=0,
        zorder=3,
    )

    axes.set_xlim(0.45, 2.55)
    axes.set_ylim(bottom=0.0, top=Y_MAX)
    axes.set_yticks(Y_TICKS)
    axes.set_xticks(positions)
    axes.set_xticklabels(
        ["Active", "Control"],
        fontweight="bold",
    )
    axes.set_ylabel(Y_LABEL)
    axes.grid(
        axis="y",
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

    figure.subplots_adjust(
        left=0.36,
        right=0.98,
        bottom=0.16,
        top=0.98,
    )
    output_path = args.postprocessing_dir / OUTPUT_NAME
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
