#!/usr/bin/env python3
"""Plot rat skull pressure with the saved localized skull region."""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import nibabel as nib
import numpy as np
from matplotlib.colors import Normalize

from nifti_masks import same_grid
from plot_human_skull_pressure_contour import (
    ELEMENT_COLOR,
    apply_style,
    draw_panel,
    pressure_colormap,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--subject", required=True)
    return parser.parse_args()


def display_plane(values: np.ndarray) -> np.ndarray:
    return values[::-1, :].T


def image_extent(
    shape: tuple[int, int],
    spacing_mm: tuple[float, float],
) -> list[float]:
    depth_samples, ml_samples = shape
    center_ml_index = (ml_samples - 1) // 2
    return [
        (-center_ml_index - 0.5) * spacing_mm[1],
        (ml_samples - center_ml_index - 0.5)
        * spacing_mm[1],
        -(depth_samples - 0.5) * spacing_mm[0],
        0.5 * spacing_mm[0],
    ]


def main() -> None:
    args = parse_args()
    subject_id = args.subject
    simulation_dir = (
        args.data_root / "simulation_outputs" / subject_id
    )
    postprocessing_dir = args.data_root / "postprocessing" / "skull"
    output_dir = postprocessing_dir / "pressure_plots"

    ct_image = nib.load(str(simulation_dir / "ct_hu.nii.gz"))
    active_image = nib.load(
        str(simulation_dir / "pressure_no_lens.nii.gz")
    )
    control_image = nib.load(
        str(simulation_dir / "pressure_lens.nii.gz")
    )
    device_image = nib.load(
        str(simulation_dir / "device_mask.nii.gz")
    )
    element_image = nib.load(
        str(simulation_dir / "element_labels.nii.gz")
    )
    lens_image = nib.load(
        str(simulation_dir / "lens_mask.nii.gz")
    )
    for image in (
        active_image,
        control_image,
        device_image,
        element_image,
        lens_image,
    ):
        if not same_grid(ct_image, image):
            raise ValueError(f"Grid mismatch: {subject_id}")

    ct = np.asanyarray(ct_image.dataobj).astype(
        np.float32, copy=False
    )
    active_pressure = np.asanyarray(
        active_image.dataobj
    ).astype(np.float32, copy=False)
    control_pressure = np.asanyarray(
        control_image.dataobj
    ).astype(np.float32, copy=False)
    device = np.asanyarray(device_image.dataobj) > 0
    element_labels = np.asanyarray(element_image.dataobj)
    lens = np.asanyarray(lens_image.dataobj) > 0

    slice_ap = (ct.shape[2] - 1) // 2
    ct_plane = ct[:, :, slice_ap]
    active_plane = active_pressure[:, :, slice_ap]
    control_plane = control_pressure[:, :, slice_ap]
    device_plane = device[:, :, slice_ap]
    element_plane = element_labels[:, :, slice_ap]
    lens_plane = lens[:, :, slice_ap]

    positive_pressure = np.concatenate(
        [
            active_plane[active_plane > 0],
            control_plane[control_plane > 0],
        ]
    )
    pressure_max_kpa = float(
        np.percentile(positive_pressure, 99.5) / 1e3
    )

    spacing = nib.affines.voxel_sizes(ct_image.affine)
    extent = image_extent(
        ct_plane.shape,
        (float(spacing[0]), float(spacing[1])),
    )

    ct_display = display_plane(ct_plane)
    active_display_kpa = display_plane(active_plane) / 1e3
    control_display_kpa = display_plane(control_plane) / 1e3
    device_display = display_plane(device_plane)
    element_display = display_plane(element_plane)
    lens_display = display_plane(lens_plane)
    pressure_mask = ~device_display

    colormap = pressure_colormap()
    apply_style()
    figure, axes = plt.subplots(
        1,
        2,
        figsize=(7.2, 3.25),
        sharex=True,
        sharey=True,
    )
    draw_panel(
        axes[0],
        ct_display,
        active_display_kpa,
        pressure_mask,
        None,
        None,
        device_display,
        element_display,
        None,
        extent,
        pressure_max_kpa,
        colormap,
        "Active",
        device_fill_color=ELEMENT_COLOR,
    )
    draw_panel(
        axes[1],
        ct_display,
        control_display_kpa,
        pressure_mask,
        None,
        None,
        device_display,
        element_display,
        lens_display,
        extent,
        pressure_max_kpa,
        colormap,
        "Control",
        device_fill_color=ELEMENT_COLOR,
    )
    figure.subplots_adjust(
        left=0.01,
        right=0.88,
        bottom=0.02,
        top=0.91,
        wspace=0.03,
    )
    colorbar_axes = figure.add_axes(
        [0.905, 0.20, 0.016, 0.62]
    )
    colorbar = figure.colorbar(
        plt.cm.ScalarMappable(
            norm=Normalize(0.0, pressure_max_kpa),
            cmap=colormap,
        ),
        cax=colorbar_axes,
    )
    colorbar.set_ticks([0.0, pressure_max_kpa])
    colorbar.ax.tick_params(length=0)
    colorbar.outline.set_visible(False)
    figure.text(
        0.970,
        0.51,
        "Pressure (kPa)",
        rotation=90,
        va="center",
        ha="center",
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{subject_id}_pressure_contour"
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
