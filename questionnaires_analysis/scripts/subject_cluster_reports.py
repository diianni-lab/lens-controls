#!/usr/bin/env python3
"""Analyze and plot per-subject sensation-cluster reports."""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import numpy.ma as ma
import pandas as pd
from matplotlib import pyplot as plt
from matplotlib.colors import ListedColormap
from matplotlib.patches import Patch

from questionnaire_data import (
    ARM_COLORS,
    ARM_LABEL,
    ARM_ORDER,
    CLUSTERS,
    load_questionnaire_data,
    write_results,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-path", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()

    _, clusters = load_questionnaire_data(args.data_path)
    ordered = []
    for arm in ARM_ORDER:
        ordered.append(clusters[clusters["arm"] == arm].sort_values("subject"))
    table = pd.concat(ordered, ignore_index=True)

    values = table[list(CLUSTERS)].to_numpy(dtype=int)
    is_active = table["arm"].eq("NoLens").to_numpy()
    active_map = ListedColormap(["white", "#b8cbed", ARM_COLORS["NoLens"]])
    control_map = ListedColormap(["white", "#f2c2a8", ARM_COLORS["Lens"]])

    figure, axis = plt.subplots(figsize=(6.1, 5.0))
    axis.imshow(
        ma.masked_array(values, mask=np.broadcast_to(~is_active[:, None], values.shape)),
        aspect="auto",
        cmap=active_map,
        vmin=0,
        vmax=2,
        interpolation="nearest",
    )
    axis.imshow(
        ma.masked_array(values, mask=np.broadcast_to(is_active[:, None], values.shape)),
        aspect="auto",
        cmap=control_map,
        vmin=0,
        vmax=2,
        interpolation="nearest",
    )

    labels = []
    for arm in ARM_ORDER:
        count = int(table["arm"].eq(arm).sum())
        labels.extend(f"{ARM_LABEL[arm]} {index}" for index in range(1, count + 1))
    axis.set_xticks(np.arange(len(CLUSTERS)))
    axis.set_xticklabels(list(CLUSTERS), rotation=45, ha="right", rotation_mode="anchor")
    axis.set_yticks(np.arange(len(table)))
    axis.set_yticklabels(labels)
    for label, arm in zip(axis.get_yticklabels(), table["arm"]):
        label.set_color(ARM_COLORS[arm])
    axis.axhline(table["arm"].eq("NoLens").sum() - 0.5, color="#222222", linewidth=1)
    axis.tick_params(length=0)
    for spine in axis.spines.values():
        spine.set_visible(True)
        spine.set_color("#333333")
        spine.set_linewidth(0.8)
    axis.legend(
        handles=[
            Patch(facecolor="#4f4f4f", edgecolor="#333333", label="Most"),
            Patch(facecolor="#cfcfcf", edgecolor="#333333", label="Few"),
        ],
        frameon=False,
        loc="lower center",
        bbox_to_anchor=(0.5, 1.08),
        ncol=2,
        fontsize=8.5,
        handlelength=1.2,
        columnspacing=1.4,
    )

    result = table.drop(columns="arm")
    write_results(
        args.output_dir,
        "subject_cluster_reports",
        result,
        figure,
    )
    plt.close(figure)


if __name__ == "__main__":
    main()
