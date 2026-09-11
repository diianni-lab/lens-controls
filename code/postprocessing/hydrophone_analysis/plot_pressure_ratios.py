#!/usr/bin/env python3
"""Plot simulation and hydrophone pressure with no-lens -6 dB regions."""

import argparse
from pathlib import Path

import numpy as np

from analyze_human_pressure_ratios import load_planes as load_human
from analyze_rat_pressure_ratios import load_planes as load_rat
from pressure_ratio_processing import minus6db_masks


DPI = 300

import matplotlib.pyplot as plt  # noqa: E402


plt.rcParams.update(
    {
        "font.family": "Arial",
        "font.size": 16,
        "axes.labelsize": 16,
        "axes.titlesize": 18,
        "xtick.labelsize": 14,
        "ytick.labelsize": 14,
        "svg.fonttype": "none",
        "pdf.fonttype": 42,
    }
)


def draw(ax, plane, mask, title, cmap, maximum, x_ticks, y_ticks, y_limits=None):
    ax.pcolormesh(
        plane.horizontal_mm,
        plane.vertical_mm,
        plane.values,
        shading="auto",
        cmap=cmap,
        vmin=0,
        vmax=maximum,
        rasterized=True,
    )
    ax.contour(
        plane.horizontal_mm,
        plane.vertical_mm,
        mask.astype(float),
        levels=[0.5],
        colors="black",
        linewidths=1.6,
        linestyles="--",
    )
    ax.set_title(title)
    ax.set_xlabel(f"{plane.horizontal_label} (mm)")
    ax.set_ylabel(f"{plane.vertical_label} (mm)")
    ax.set_xlim(plane.horizontal_mm.min(), plane.horizontal_mm.max())
    ax.set_xticks(x_ticks)
    ax.set_yticks(y_ticks)
    ax.set_aspect("equal", adjustable="box")
    ax.tick_params(direction="in", length=2, width=0.6)
    if plane.vertical_label == "z":
        y_limits = y_limits or (plane.vertical_mm.min(), plane.vertical_mm.max())
        ax.set_ylim(y_limits[1], y_limits[0])


def plot_source(path, source, dataset, no_lens, lens, masks, cmap, xz_limits=None):
    maximum = max(
        float(np.nanmax(plane.values))
        for planes in (no_lens, lens)
        for plane in planes.values()
    )
    if dataset == "human":
        x_ticks = [-40, -20, 0, 20, 40]
        y_ticks = {"xz": [50, 100, 140], "xy": x_ticks}
    else:
        x_ticks = [-5, 0, 5]
        y_ticks = {"xz": [8, 10, 12, 14, 16], "xy": [-2.5, 0, 2.5]}

    spans = {}
    for name, plane in no_lens.items():
        vertical = xz_limits[1] - xz_limits[0] if name == "xz" and xz_limits else np.ptp(plane.vertical_mm)
        spans[name] = (float(np.ptp(plane.horizontal_mm)), float(vertical))

    figure_width = 8.2
    left, right, column_gap = 0.75, 0.25, 0.95
    row_gap, top, bottom = 0.85, 0.80, 0.65
    column_width = (figure_width - left - right - column_gap) / 2
    scale = column_width / max(horizontal for horizontal, _ in spans.values())
    sizes = {name: (horizontal * scale, vertical * scale) for name, (horizontal, vertical) in spans.items()}
    figure_height = bottom + sizes["xy"][1] + row_gap + sizes["xz"][1] + top

    figure = plt.figure(figsize=(figure_width, figure_height), dpi=DPI, facecolor="white")
    row_bottom = {"xy": bottom, "xz": bottom + sizes["xy"][1] + row_gap}
    column_left = [left, left + column_width + column_gap]

    for name in ("xz", "xy"):
        width, height = sizes[name]
        axes = []
        for column in column_left:
            centered = column + (column_width - width) / 2
            axes.append(
                figure.add_axes(
                    [
                        centered / figure_width,
                        row_bottom[name] / figure_height,
                        width / figure_width,
                        height / figure_height,
                    ]
                )
            )
        limits = xz_limits if name == "xz" else None
        draw(axes[0], no_lens[name], masks[name], f"{name.upper()} no lens", cmap, maximum, x_ticks, y_ticks[name], limits)
        draw(axes[1], lens[name], masks[name], f"{name.upper()} lens", cmap, maximum, x_ticks, y_ticks[name], limits)

    figure.suptitle(f"{source} pressure and no-lens -6 dB regions", y=0.985)
    figure.savefig(path.with_suffix(".png"), dpi=DPI, bbox_inches="tight")
    figure.savefig(path.with_suffix(".svg"), dpi=DPI, bbox_inches="tight")
    plt.close(figure)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", choices=("human", "rat"), default="human")
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    simulation_no_lens, simulation_lens, hydrophone_no_lens, hydrophone_lens = (
        load_rat(args.data_root) if args.dataset == "rat" else load_human(args.data_root)
    )
    hydrophone_limits = None
    if args.dataset == "rat":
        z = simulation_no_lens["xz"].vertical_mm
        hydrophone_limits = (float(z.min()), float(z.max()))

    plot_source(
        args.output_dir / "simulation_pressure_ratios",
        "Simulation",
        args.dataset,
        simulation_no_lens,
        simulation_lens,
        minus6db_masks(simulation_no_lens),
        "Blues",
    )
    plot_source(
        args.output_dir / "hydrophone_pressure_ratios",
        "Hydrophone",
        args.dataset,
        hydrophone_no_lens,
        hydrophone_lens,
        minus6db_masks(hydrophone_no_lens),
        "Greens",
        hydrophone_limits,
    )


if __name__ == "__main__":
    main()
