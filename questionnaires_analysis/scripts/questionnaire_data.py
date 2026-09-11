#!/usr/bin/env python3
"""Shared questionnaire parsing and plotting definitions."""

from __future__ import annotations

import re
from collections import OrderedDict
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


SUBJECT_START = 21
SUBJECT_END = 44
ARM_ORDER = ["NoLens", "Lens"]
ARM_LABEL = {"NoLens": "Active", "Lens": "Control"}
ARM_COLORS = {"NoLens": "#345f9f", "Lens": "#d8743c"}
NO_SENSATION_COLOR = "#d9d9d9"
GRID_COLOR = "#d7d7d7"

CLUSTERS = OrderedDict(
    [
        (
            "Auditory",
            [
                "Buzz",
                "Humming",
                "Clicking",
                "Low-frequency rumble",
                "High-pitched tone",
            ],
        ),
        (
            "Vibratory",
            ["Vibration", "Pulsing", "Throbbing", "Tap", "Drilling"],
        ),
        (
            "Pressure",
            [
                "Pressure/pressing",
                "Squeezing",
                "Heaviness",
                "Tugging",
                "Pinching",
            ],
        ),
        ("Touch", ["Touch", "Movement on skin"]),
        (
            "Paresthesia",
            ["Tingle", "Prickling", "Itch", "Electric current", "Shock"],
        ),
        ("Thermal", ["Cold", "Freezing", "Warm"]),
    ]
)

ITEM_TO_CLUSTER = {
    item: cluster for cluster, items in CLUSTERS.items() for item in items
}


plt.rcParams.update(
    {
        "font.family": "Arial",
        "font.size": 12,
        "axes.labelsize": 12,
        "axes.titlesize": 12.9,
        "xtick.labelsize": 10.8,
        "ytick.labelsize": 10.8,
        "legend.fontsize": 12,
        "axes.linewidth": 1.2,
        "figure.dpi": 300,
        "savefig.dpi": 300,
        "svg.fonttype": "none",
        "pdf.fonttype": 42,
    }
)


def subject_number(subject: str) -> int | None:
    match = re.fullmatch(r"UNMET_(\d+)", str(subject).strip())
    return int(match.group(1)) if match else None


def specifier_column(column: str) -> str:
    if column.endswith(".1"):
        return column.replace(".1", "_spec.1")
    return f"{column}_spec"


def load_questionnaire_data(
    data_path: Path,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    responses = pd.read_csv(data_path, encoding="utf-8-sig")
    responses["ID"] = responses["ID"].astype(str).str.strip()
    numbers = responses["ID"].map(subject_number)
    responses = responses[
        numbers.between(SUBJECT_START, SUBJECT_END, inclusive="both")
        & responses["Arm"].isin(ARM_ORDER)
    ].copy()

    closed_columns = [
        column
        for column in responses.columns
        if column.startswith("Closed_") and not column.endswith("_spec")
    ]

    subject_rows = []
    cluster_rows = []
    for _, response in responses.iterrows():
        reports = []
        for column in closed_columns:
            item = response[column]
            if pd.isna(item):
                continue
            item = str(item).strip()
            if item == "Pressure":
                item = "Pressure/pressing"
            if item not in ITEM_TO_CLUSTER:
                continue
            specifier = str(response[specifier_column(column)]).strip().lower()
            reports.append((ITEM_TO_CLUSTER[item], 2 if specifier == "most" else 1))

        arm = response["Arm"]
        subject_rows.append(
            {
                "subject": response["ID"],
                "arm": arm,
                "condition": ARM_LABEL[arm],
                "any_report": not bool(response["None_closed"]),
                "report_count": len(reports),
            }
        )

        cluster_row = {
            "subject": response["ID"],
            "arm": arm,
            "condition": ARM_LABEL[arm],
        }
        for cluster in CLUSTERS:
            cluster_row[cluster] = max(
                (intensity for name, intensity in reports if name == cluster),
                default=0,
            )
        cluster_rows.append(cluster_row)

    return pd.DataFrame(subject_rows), pd.DataFrame(cluster_rows)


def style_axis(axis) -> None:
    axis.spines["top"].set_visible(False)
    axis.spines["right"].set_visible(False)
    for side in ("left", "bottom"):
        axis.spines[side].set_color("#4d4d4d")
        axis.spines[side].set_linewidth(0.8)
    axis.tick_params(colors="#303030", width=0.8, length=3)
    axis.grid(True, axis="y", color=GRID_COLOR, linewidth=0.6, alpha=0.8)
    axis.set_axisbelow(True)


def write_results(
    output_dir: Path,
    stem: str,
    table: pd.DataFrame,
    figure,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    output = output_dir / stem
    table.to_csv(output.with_suffix(".csv"), index=False)
    figure.savefig(
        output.with_suffix(".png"),
        dpi=300,
        bbox_inches="tight",
        facecolor="white",
    )
    figure.savefig(
        output.with_suffix(".svg"),
        bbox_inches="tight",
        facecolor="white",
    )
