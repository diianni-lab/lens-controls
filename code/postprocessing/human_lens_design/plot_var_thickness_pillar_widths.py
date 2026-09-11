#!/usr/bin/env python3
"""Plot the pressure fields for the pillar-width simulations."""

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap
from scipy.io import loadmat


SEEDS = (8, 9, 10)
PILLAR_WIDTHS_MM = (1, 3, 5, 7, 9)
DX_MM = 0.5
FOCUS_MM = 80
LENS_SCALE = 1.206 / 1.27
MINUS6DB = 10 ** (-6 / 20)
DPI = 300
BLUE_CMAP = LinearSegmentedColormap.from_list(
    "pressure_blue",
    ["#f3f9fc", "#cfe7f4", "#8dc4e2", "#3f91c5", "#0b559f"],
    N=256,
)
RED_CMAP = LinearSegmentedColormap.from_list(
    "pressure_red",
    ["#fff4ef", "#f8c7b2", "#ea835f", "#c84a1b", "#7f1d0b"],
    N=256,
)

plt.rcParams.update(
    {
        "font.family": "Arial",
        "font.size": 16,
        "axes.labelsize": 16,
        "axes.titlesize": 18,
        "xtick.labelsize": 14,
        "ytick.labelsize": 14,
        "svg.fonttype": "none",
    }
)


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    return parser.parse_args()


def load_pressure(path, lens=False):
    pressure = -np.asarray(
        loadmat(path, variable_names=["p_min_all"])["p_min_all"], dtype=float
    ) / 1e6
    return pressure * LENS_SCALE if lens else pressure


def extract_planes(pressure):
    depth_mm = np.arange(pressure.shape[0]) * DX_MM
    lateral_mm = (
        np.arange(pressure.shape[1]) - (pressure.shape[1] - 1) / 2
    ) * DX_MM
    focus_index = int(round(FOCUS_MM / DX_MM))
    return (
        lateral_mm,
        depth_mm,
        pressure[:, :, pressure.shape[2] // 2],
        pressure[focus_index, :, :].T,
    )


def draw(
    ax,
    x,
    y,
    values,
    mask,
    contour_values,
    contour_level,
    split_colors,
    contour_linewidth=1.2,
):
    if split_colors:
        outside = np.ma.masked_where(mask, values)
        inside = np.ma.masked_where(~mask, values)
        ax.pcolormesh(
            x, y, outside, shading="auto", cmap=BLUE_CMAP, vmin=0, vmax=1,
            rasterized=True,
        )
        ax.pcolormesh(
            x, y, inside, shading="auto", cmap=RED_CMAP, vmin=0, vmax=1,
            rasterized=True,
        )
    else:
        ax.pcolormesh(
            x, y, values, shading="auto", cmap=BLUE_CMAP, vmin=0, vmax=1,
            rasterized=True,
        )

    ax.contour(
        x,
        y,
        contour_values,
        levels=[contour_level],
        colors="#222222",
        linewidths=contour_linewidth,
        linestyles="--",
    )
    ax.set_aspect("equal", adjustable="box")
    ax.tick_params(direction="in", length=2, width=0.6)


def plot_volume(
    output, title, pressure, masks, contour_values, contour_level, split_colors
):
    lateral_mm, depth_mm, xz, xy = extract_planes(pressure)

    figure_width = 3.6
    plot_width = 2.15
    scale = plot_width / 80
    xz_height = 180 * scale
    xy_height = 80 * scale
    left, bottom, gap, top = 0.65, 0.55, 0.62, 0.70
    figure_height = bottom + xy_height + gap + xz_height + top

    figure = plt.figure(figsize=(figure_width, figure_height), dpi=DPI)
    xz_ax = figure.add_axes(
        [left / figure_width, (bottom + xy_height + gap) / figure_height,
         plot_width / figure_width, xz_height / figure_height]
    )
    xy_ax = figure.add_axes(
        [left / figure_width, bottom / figure_height,
         plot_width / figure_width, xy_height / figure_height]
    )

    draw(
        xz_ax,
        lateral_mm,
        depth_mm,
        xz,
        masks[0],
        contour_values[0],
        contour_level,
        split_colors,
    )
    xz_ax.set_xlim(-40, 40)
    xz_ax.set_ylim(180, 0)
    xz_ax.set_xticks([-25, 0, 25])
    xz_ax.set_yticks(np.arange(0, 176, 25))
    xz_ax.set_xlabel("x (mm)")
    xz_ax.set_ylabel("z (mm)")

    draw(
        xy_ax,
        lateral_mm,
        lateral_mm,
        xy,
        masks[1],
        contour_values[1],
        contour_level,
        split_colors,
    )
    xy_ax.set_xlim(-40, 40)
    xy_ax.set_ylim(40, -40)
    xy_ax.set_xticks([-25, 0, 25])
    xy_ax.set_yticks([-25, 0, 25])
    xy_ax.set_xlabel("x (mm)")
    xy_ax.set_ylabel("y (mm)")

    figure.suptitle(title, y=0.985)
    colorbar_ax = figure.add_axes(
        [3.02 / figure_width, bottom / figure_height,
         0.10 / figure_width, (xy_height + gap + xz_height) / figure_height]
    )
    colorbar = figure.colorbar(
        plt.cm.ScalarMappable(norm=plt.Normalize(0, 1), cmap=BLUE_CMAP),
        cax=colorbar_ax,
    )
    colorbar.set_ticks([])
    colorbar.outline.set_visible(False)
    colorbar.set_label("Normalized pressure")

    output.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(output.with_suffix(".png"), dpi=DPI, bbox_inches="tight")
    figure.savefig(output.with_suffix(".svg"), dpi=DPI, bbox_inches="tight")
    plt.close(figure)


def main():
    args = parse_args()
    no_lens = load_pressure(args.data_dir / "sims_no_lens_focus_80_seed_1.mat")
    _, _, no_lens_xz, no_lens_xy = extract_planes(no_lens)
    threshold = np.nanmax(no_lens) * MINUS6DB
    masks = (no_lens_xz >= threshold, no_lens_xy >= threshold)
    contour_values = (no_lens_xz, no_lens_xy)

    for seed in SEEDS:
        output_dir = args.output_dir / f"seed_{seed}"
        plot_volume(
            output_dir / "beam_nolens",
            "No lens",
            no_lens,
            masks,
            contour_values,
            threshold,
            True,
        )

        for width_mm in PILLAR_WIDTHS_MM:
            pressure = load_pressure(
                args.data_dir
                / f"sims_9mm_lens_pillar_width_{width_mm}_focus_80_seed_{seed}.mat",
                lens=True,
            )
            plot_volume(
                output_dir / f"beam_9mm_lens_pillar_width_{width_mm}",
                f"{width_mm}-mm pillars",
                pressure,
                masks,
                contour_values,
                threshold,
                False,
            )


if __name__ == "__main__":
    main()
