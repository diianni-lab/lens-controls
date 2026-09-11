#!/usr/bin/env python3
"""Analyze and plot the prevalence of any closed-list sensation report."""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
from scipy.stats import fisher_exact

from questionnaire_data import (
    ARM_COLORS,
    ARM_LABEL,
    ARM_ORDER,
    NO_SENSATION_COLOR,
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
    counts = {}
    contingency = []
    for arm in ARM_ORDER:
        values = subjects.loc[subjects["arm"] == arm, "any_report"]
        with_report = int(values.sum())
        total = int(len(values))
        counts[arm] = (with_report, total - with_report, total)
        contingency.append([with_report, total - with_report])
    odds_ratio, p_value = fisher_exact(contingency)

    rows = []
    for arm in ARM_ORDER:
        with_report, without_report, total = counts[arm]
        rows.append(
            {
                "condition": ARM_LABEL[arm],
                "n_subjects": total,
                "n_with_report": with_report,
                "n_without_report": without_report,
                "percent_with_report": 100 * with_report / total,
                "odds_ratio": odds_ratio,
                "fisher_p": p_value,
            }
        )
    table = pd.DataFrame(rows)

    figure, axis = plt.subplots(figsize=(3.6, 4.1))
    x = np.arange(len(ARM_ORDER))
    for index, arm in enumerate(ARM_ORDER):
        with_report, without_report, total = counts[arm]
        with_percent = 100 * with_report / total
        without_percent = 100 * without_report / total
        axis.bar(index, with_percent, color=ARM_COLORS[arm], width=0.58)
        axis.bar(
            index,
            without_percent,
            bottom=with_percent,
            color=NO_SENSATION_COLOR,
            width=0.58,
        )
        axis.text(
            index,
            with_percent / 2,
            f"{with_report}/{total}",
            ha="center",
            va="center",
            color="white",
            fontweight="bold",
        )
        axis.text(
            index,
            with_percent + without_percent / 2,
            f"{without_report}/{total}",
            ha="center",
            va="center",
            color="#555555",
        )
    axis.set_xticks(x)
    axis.set_xticklabels([ARM_LABEL[arm] for arm in ARM_ORDER])
    axis.set_ylim(0, 105)
    axis.set_ylabel("Subjects with ≥1 report (%)")
    axis.text(
        0.5,
        1.04,
        f"Fisher p={p_value:.2f}",
        transform=axis.transAxes,
        ha="center",
        va="bottom",
        fontsize=9.5,
        clip_on=False,
    )
    style_axis(axis)

    write_results(args.output_dir, "any_sensation", table, figure)
    plt.close(figure)


if __name__ == "__main__":
    main()
