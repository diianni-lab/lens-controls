#!/usr/bin/env python3
"""Analyze and plot sensation-cluster prevalence by condition."""

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

    _, clusters = load_questionnaire_data(args.data_path)
    rows = []
    for cluster in CLUSTERS:
        row = {"cluster": cluster}
        contingency = []
        for arm in ARM_ORDER:
            condition = ARM_LABEL[arm].lower()
            values = clusters.loc[clusters["arm"] == arm, cluster]
            count = int(values.gt(0).sum())
            total = int(len(values))
            row[f"{condition}_with_report"] = count
            row[f"{condition}_total"] = total
            row[f"{condition}_percent"] = 100 * count / total
            contingency.append([count, total - count])
        odds_ratio, p_value = fisher_exact(contingency)
        row["odds_ratio"] = odds_ratio
        row["fisher_p"] = p_value
        rows.append(row)
    table = pd.DataFrame(rows)

    figure, axis = plt.subplots(figsize=(6.2, 4.7))
    x = np.arange(len(table))
    width = 0.34
    for index, arm in enumerate(ARM_ORDER):
        condition = ARM_LABEL[arm].lower()
        positions = x + (index - 0.5) * width
        bars = axis.bar(
            positions,
            table[f"{condition}_percent"],
            width=width,
            color=ARM_COLORS[arm],
            label=ARM_LABEL[arm],
            alpha=0.95,
        )
        for bar, (_, row) in zip(bars, table.iterrows()):
            axis.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + 1.3 + index * 3,
                f"{int(row[f'{condition}_with_report'])}/{int(row[f'{condition}_total'])}",
                ha="center",
                va="bottom",
                fontsize=7.4,
                color=ARM_COLORS[arm],
            )
    axis.set_xticks(x)
    axis.set_xticklabels(table["cluster"], rotation=45, ha="right", rotation_mode="anchor")
    axis.set_ylim(0, 105)
    axis.set_ylabel("Subjects with ≥1 report (%)")
    axis.set_title("Cluster prevalence", fontweight="bold", pad=6)
    axis.legend(frameon=False, loc="upper right", fontsize=8)
    style_axis(axis)

    write_results(args.output_dir, "cluster_prevalence", table, figure)
    plt.close(figure)


if __name__ == "__main__":
    main()
