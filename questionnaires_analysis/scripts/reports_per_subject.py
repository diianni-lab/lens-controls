#!/usr/bin/env python3
"""Analyze and plot closed-list sensation-report counts per subject."""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib
import numpy as np
from matplotlib import pyplot as plt
from scipy.stats import mannwhitneyu

from questionnaire_data import (
    ARM_COLORS,
    ARM_LABEL,
    ARM_ORDER,
    load_questionnaire_data,
    style_axis,
    write_results,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-path", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()

    subjects, _ = load_questionnaire_data(args.data_path)
    active = subjects.loc[subjects["arm"] == "NoLens", "report_count"]
    control = subjects.loc[subjects["arm"] == "Lens", "report_count"]
    statistic, p_value = mannwhitneyu(active, control, alternative="two-sided")

    table = subjects[["subject", "condition", "report_count"]].copy()
    table["mannwhitney_u"] = statistic
    table["mannwhitney_p"] = p_value

    figure, axis = plt.subplots(figsize=(3.6, 4.1))
    random = np.random.default_rng(7)
    for index, arm in enumerate(ARM_ORDER):
        values = subjects.loc[
            subjects["arm"] == arm,
            "report_count",
        ].to_numpy(dtype=float)
        axis.boxplot(
            values,
            positions=[index],
            widths=0.42,
            patch_artist=True,
            showfliers=False,
            medianprops={"color": "#222222", "linewidth": 1.2},
            boxprops={
                "facecolor": ARM_COLORS[arm],
                "alpha": 0.22,
                "edgecolor": ARM_COLORS[arm],
                "linewidth": 1.1,
            },
            whiskerprops={"color": ARM_COLORS[arm], "linewidth": 1},
            capprops={"color": ARM_COLORS[arm], "linewidth": 1},
        )
        jitter = random.normal(0, 0.035, values.size)
        axis.scatter(
            np.full(values.size, index) + jitter,
            values,
            s=24,
            color=ARM_COLORS[arm],
            edgecolors="none",
            alpha=0.92,
            zorder=3,
        )
    axis.set_xticks(np.arange(len(ARM_ORDER)))
    axis.set_xticklabels([ARM_LABEL[arm] for arm in ARM_ORDER])
    axis.set_ylabel("Reports per subject")
    axis.yaxis.set_major_locator(matplotlib.ticker.MaxNLocator(integer=True))
    axis.text(
        0.5,
        1.04,
        f"Mann-Whitney p={p_value:.2f}",
        transform=axis.transAxes,
        ha="center",
        va="bottom",
        fontsize=9.5,
        clip_on=False,
    )
    style_axis(axis)

    write_results(args.output_dir, "reports_per_subject", table, figure)
    plt.close(figure)


if __name__ == "__main__":
    main()
