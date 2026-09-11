#!/usr/bin/env python3
"""Plot the pressure fields for the focal-distance simulations."""

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap
from scipy.io import loadmat


FOCUSES_MM = (60, 90, 120)
DX_MM = 0.5
LENS_SCALE = 1.206 / 1.27
DPI = 300
BLUE_CMAP = LinearSegmentedColormap.from_list(
    "pressure_blue",
    ["#f3f9fc", "#cfe7f4", "#8dc4e2", "#3f91c5", "#0b559f"],
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


def extract_planes(pressure, focus_mm):
    depth_mm = np.arange(pressure.shape[0]) * DX_MM
    lateral_mm = (
        np.arange(pressure.shape[1]) - (pressure.shape[1] - 1) / 2
    ) * DX_MM
    focus_index = int(round(focus_mm / DX_MM))
    return (
        lateral_mm,
        depth_mm,
        pressure[:, :, pressure.shape[2] // 2],
        pressure[focus_index, :, :].T,
    )


def draw(ax, x, y, values):
    ax.pcolormesh(
        x,
        y,
        values,
        shading="auto",
        cmap=BLUE_CMAP,
        vmin=0,
        vmax=1,
        rasterized=True,
    )
    ax.set_aspect("equal", adjustable="box")
    ax.tick_params(direction="in", length=2, width=0.6)


def plot_volume(output, title, planes):
    lateral_mm, depth_mm, xz, xy = planes

    figure_width = 3.6
    plot_width = 2.15
    scale = plot_width / 80
    xz_height = 225 * scale
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

    draw(xz_ax, lateral_mm, depth_mm, xz)
    xz_ax.set_xlim(-40, 40)
    xz_ax.set_ylim(225, 0)
    xz_ax.set_xticks([-40, -20, 0, 20, 40])
    xz_ax.set_yticks([0, 50, 100, 150, 200])
    xz_ax.set_xlabel("x (mm)")
    xz_ax.set_ylabel("z (mm)")

    draw(xy_ax, lateral_mm, lateral_mm, xy)
    xy_ax.set_xlim(-40, 40)
    xy_ax.set_ylim(40, -40)
    xy_ax.set_xticks([-40, -20, 0, 20, 40])
    xy_ax.set_yticks([-40, -20, 0, 20, 40])
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

    for focus_mm in FOCUSES_MM:
        no_lens = load_pressure(
            args.data_dir / f"sims_no_lens_focus_{focus_mm}_seed_1.mat"
        )
        lens = load_pressure(
            args.data_dir
            / f"sims_9mm_lens_pillar_width_7_focus_{focus_mm}_seed_8.mat",
            lens=True,
        )
        no_lens_planes = extract_planes(no_lens, focus_mm)
        lens_planes = extract_planes(lens, focus_mm)

        maximum = max(
            float(np.nanmax(plane))
            for plane in no_lens_planes[2:] + lens_planes[2:]
        )
        no_lens_planes = no_lens_planes[:2] + tuple(
            plane / maximum for plane in no_lens_planes[2:]
        )
        lens_planes = lens_planes[:2] + tuple(
            plane / maximum for plane in lens_planes[2:]
        )

        plot_volume(
            args.output_dir / f"focus_{focus_mm}_beam_nolens",
            f"{focus_mm} mm",
            no_lens_planes,
        )
        plot_volume(
            args.output_dir
            / f"focus_{focus_mm}_beam_9mm_lens_pillar_width_7",
            f"{focus_mm} mm",
            lens_planes,
        )


if __name__ == "__main__":
    main()
