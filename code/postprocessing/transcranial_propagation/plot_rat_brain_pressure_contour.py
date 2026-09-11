#!/usr/bin/env python3
"""Plot rat brain pressure with the saved Active -6-dB region."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt
import nibabel as nib
import numpy as np

from nifti_masks import same_grid
from plot_human_brain_pressure_contour import (
    CONTOUR_COLOR,
    OUTLINE_COLOR,
    add_pressure_colorbars,
    anatomy_rgba,
    apply_style,
    draw_pressure,
    draw_smoothed_mask,
)


CROP_MARGIN_MM = 0.75


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--subject", required=True)
    return parser.parse_args()


def crop_bounds(
    brain_mask: np.ndarray,
    spacing_mm: tuple[float, float],
    target_index: tuple[int, int],
) -> tuple[slice, slice]:
    coordinates = np.argwhere(brain_mask)
    depth_margin = int(
        np.ceil(CROP_MARGIN_MM / spacing_mm[0])
    )
    ml_margin = int(
        np.ceil(CROP_MARGIN_MM / spacing_mm[1])
    )

    depth_start = min(
        int(coordinates[:, 0].min()), target_index[0]
    )
    depth_stop = max(
        int(coordinates[:, 0].max()), target_index[0]
    )
    ml_start = min(
        int(coordinates[:, 1].min()), target_index[1]
    )
    ml_stop = max(
        int(coordinates[:, 1].max()), target_index[1]
    )

    return (
        slice(
            max(0, depth_start - depth_margin),
            min(
                brain_mask.shape[0],
                depth_stop + depth_margin + 1,
            ),
        ),
        slice(
            max(0, ml_start - ml_margin),
            min(
                brain_mask.shape[1],
                ml_stop + ml_margin + 1,
            ),
        ),
    )


def image_extent(
    depth_slice: slice,
    ml_slice: slice,
    spacing_mm: tuple[float, float],
    center_ml_index: int,
) -> list[float]:
    depth_start = (depth_slice.start - 0.5) * spacing_mm[0]
    depth_stop = (depth_slice.stop - 0.5) * spacing_mm[0]
    ml_start = (
        ml_slice.start - center_ml_index - 0.5
    ) * spacing_mm[1]
    ml_stop = (
        ml_slice.stop - center_ml_index - 0.5
    ) * spacing_mm[1]
    return [ml_start, ml_stop, -depth_stop, -depth_start]


def display_plane(
    values: np.ndarray,
    depth_slice: slice,
    ml_slice: slice,
) -> np.ndarray:
    return values[depth_slice, ml_slice][::-1, :].T


def draw_panel(
    axes: plt.Axes,
    anatomy: np.ndarray,
    brain_mask: np.ndarray,
    pressure_kpa: np.ndarray,
    inside_mask: np.ndarray,
    extent: list[float],
    pressure_max_kpa: float,
    title: str,
) -> None:
    axes.imshow(
        anatomy_rgba(anatomy, brain_mask).transpose(1, 0, 2),
        origin="lower",
        extent=extent,
        interpolation="nearest",
    )

    draw_pressure(
        axes,
        pressure_kpa,
        brain_mask & ~inside_mask,
        extent,
        pressure_max_kpa,
        "Reds",
    )
    draw_pressure(
        axes,
        pressure_kpa,
        brain_mask & inside_mask,
        extent,
        pressure_max_kpa,
        "Blues",
    )

    draw_smoothed_mask(
        axes,
        brain_mask,
        extent,
        OUTLINE_COLOR,
        linewidth=0.75,
    )
    draw_smoothed_mask(
        axes,
        inside_mask,
        extent,
        CONTOUR_COLOR,
        linewidth=1.4,
        linestyle=(0, (4.0, 2.5)),
    )
    axes.set_title(title, pad=4.0)
    axes.set_aspect("equal")
    axes.set_xticks([])
    axes.set_yticks([])
    for spine in axes.spines.values():
        spine.set_visible(False)


def main() -> None:
    args = parse_args()
    subject_id = args.subject
    simulation_dir = (
        args.data_root / "simulation_outputs" / subject_id
    )
    postprocessing_dir = args.data_root / "postprocessing" / "brain"
    output_dir = postprocessing_dir / "pressure_plots"

    anatomy_image = nib.load(
        str(simulation_dir / "ct_hu.nii.gz")
    )
    segmentation_image = nib.load(
        str(simulation_dir / "segmentation_labels.nii.gz")
    )
    active_image = nib.load(
        str(simulation_dir / "pressure_no_lens.nii.gz")
    )
    control_image = nib.load(
        str(simulation_dir / "pressure_lens.nii.gz")
    )
    inside_image = nib.load(
        str(
            postprocessing_dir
            / "masks"
            / f"{subject_id}_inside_mask.nii.gz"
        )
    )

    for image in (
        segmentation_image,
        active_image,
        control_image,
        inside_image,
    ):
        if not same_grid(anatomy_image, image):
            raise ValueError(f"Grid mismatch: {subject_id}")

    anatomy = np.asanyarray(anatomy_image.dataobj).astype(
        np.float32, copy=False
    )
    segmentation = np.asanyarray(segmentation_image.dataobj)
    active_pressure = np.asanyarray(active_image.dataobj).astype(
        np.float32, copy=False
    )
    control_pressure = np.asanyarray(
        control_image.dataobj
    ).astype(np.float32, copy=False)
    inside = np.asanyarray(inside_image.dataobj) > 0

    slice_ap = (anatomy.shape[2] - 1) // 2
    anatomy_plane = anatomy[:, :, slice_ap]
    brain_plane = segmentation[:, :, slice_ap] == 1
    active_plane = active_pressure[:, :, slice_ap]
    control_plane = control_pressure[:, :, slice_ap]
    inside_plane = inside[:, :, slice_ap] & brain_plane

    config_path = (
        Path(__file__).resolve().parents[2]
        / "k_wave_engine"
        / "configs"
        / "rat"
        / "simulation.json"
    )
    simulation_config = json.loads(config_path.read_text())
    target_depth_mm = 1e3 * float(
        simulation_config["transducer"][
            "sourceToTargetDistanceM"
        ]
    )

    spacing = nib.affines.voxel_sizes(anatomy_image.affine)
    plane_spacing = (float(spacing[0]), float(spacing[1]))
    center_ml_index = (anatomy.shape[1] - 1) // 2
    target_index = (
        int(np.rint(target_depth_mm / plane_spacing[0])),
        center_ml_index,
    )
    depth_slice, ml_slice = crop_bounds(
        brain_plane,
        plane_spacing,
        target_index,
    )
    extent = image_extent(
        depth_slice,
        ml_slice,
        plane_spacing,
        center_ml_index,
    )

    positive_pressure = np.concatenate(
        [
            active_plane[active_plane > 0],
            control_plane[control_plane > 0],
        ]
    )
    pressure_max_kpa = float(
        np.percentile(positive_pressure, 99.5) / 1e3
    )

    anatomy_display = display_plane(
        anatomy_plane, depth_slice, ml_slice
    )
    brain_display = display_plane(
        brain_plane, depth_slice, ml_slice
    )
    inside_display = display_plane(
        inside_plane, depth_slice, ml_slice
    )
    active_display_kpa = display_plane(
        active_plane, depth_slice, ml_slice
    ) / 1e3
    control_display_kpa = display_plane(
        control_plane, depth_slice, ml_slice
    ) / 1e3

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
        anatomy_display,
        brain_display,
        active_display_kpa,
        inside_display,
        extent,
        pressure_max_kpa,
        "Active",
    )
    draw_panel(
        axes[1],
        anatomy_display,
        brain_display,
        control_display_kpa,
        inside_display,
        extent,
        pressure_max_kpa,
        "Control",
    )
    figure.subplots_adjust(
        left=0.01,
        right=0.87,
        bottom=0.02,
        top=0.91,
        wspace=0.03,
    )
    add_pressure_colorbars(figure, pressure_max_kpa)

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
