#!/usr/bin/env python3
"""Analyze and plot sensation-cluster prevalence by condition."""

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from questionnaire_data import (
    ARM_COLORS,
    ARM_LABEL,
    ARM_ORDER,
    CLUSTERS,
    load_questionnaire_data,
    style_axis,
    write_results,
)

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-path", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()

    # Load table
    df = pd.read_csv(
        args.data_path
    )

    # Difference in prevalence, expressed as percentage points
    df["difference"] = df["active_percent"] - df["control_percent"]

    # Newcombe CIs are stored as proportions, so convert to percentage points
    df["ci_low"] = df["newcomb_ci_low"] * 100
    df["ci_high"] = df["newcomb_ci_high"] * 100

    # Reverse order so first cluster appears at the top
    plot_df = df.iloc[::-1].reset_index(drop=True)

    y = np.arange(len(plot_df))

    # Asymmetric 95% CI error bars
    xerr = np.vstack([
        plot_df["difference"] - plot_df["ci_low"],
        plot_df["ci_high"] - plot_df["difference"]
    ])

    figure, axis = plt.subplots(figsize=(4.5, 5))

    axis.errorbar(
        plot_df["difference"],
        y,
        xerr=xerr,
        fmt="o",
        capsize=3,
        linewidth=1.5
    )

    # Null difference
    axis.axvline(0, linestyle="--", linewidth=1)

    axis.set_yticks(y)
    axis.set_yticklabels(plot_df["cluster"], rotation=45, ha="right", rotation_mode="anchor", fontsize=14)
    axis.set_xlabel(
        "Difference in subjects reporting sensation\n"
        "Active − Control (percentage points)"
    )
    axis.set_ylabel("")

    # Symmetric scale around zero
    axis.set_xlim(-55, 55)

    # Add Fisher's exact P values just outside the plotting area
    for i, row in plot_df.iterrows():
        axis.text(
            1.03,
            i,
            f"P = {row['fisher_p']:.2f}",
            transform=axis.get_yaxis_transform(),
            va="center",
            ha="left",
            fontsize=14,
            clip_on=False
        )

    axis.text(
        1.03,
        1.03,
        "Fisher's exact",
        transform=axis.transAxes,
        ha="left",
        va="bottom",
        fontsize=16,
        clip_on=False
    )

    axis.spines["top"].set_visible(False)
    axis.spines["right"].set_visible(False)

    style_axis(axis)

    output= args.output_dir / "cluster_prevalence_ci"
    figure.savefig(
        str(output) +".png",
        dpi=300,
        bbox_inches="tight",
        facecolor="white",
    )

    figure.savefig(
        str(output) +".svg",
        bbox_inches="tight",
        facecolor="white",
    )

    plt.close(figure)

if __name__ == "__main__":
    main()
