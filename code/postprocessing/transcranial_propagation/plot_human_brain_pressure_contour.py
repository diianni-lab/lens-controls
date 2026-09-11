#!/usr/bin/env python3
"""Plot whole-brain pressure with the saved Active -6-dB region."""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import nibabel as nib
import numpy as np
from matplotlib.colors import Normalize
from scipy.ndimage import gaussian_filter, map_coordinates


CONTOUR_COLOR = "#e4553d"
TARGET_COLOR = "#9b2f73"
OUTLINE_COLOR = "#666666"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--subject", required=True)
    parser.add_argument("--pressure-max-kpa", type=float)
    return parser.parse_args()


def reference_plane_world_coordinates(
    reference: nib.Nifti1Image,
    slice_y: int,
) -> tuple[np.ndarray, tuple[int, int]]:
    nx, _, nz = reference.shape[:3]
    i_grid, k_grid = np.meshgrid(
        np.arange(nx),
        np.arange(nz),
        indexing="ij",
    )
    reference_indices = np.column_stack(
        [
            i_grid.ravel(),
            np.full(i_grid.size, slice_y),
            k_grid.ravel(),
        ]
    )
    world = nib.affines.apply_affine(
        reference.affine,
        reference_indices,
    )
    return world, (nx, nz)


def sample_plane(
    values: np.ndarray,
    image: nib.Nifti1Image,
    world: np.ndarray,
    plane_shape: tuple[int, int],
    order: int,
) -> np.ndarray:
    source_indices = nib.affines.apply_affine(
        np.linalg.inv(image.affine),
        world,
    )
    sampled = map_coordinates(
        values,
        source_indices.T,
        order=order,
        mode="constant",
        cval=0.0,
        prefilter=False,
    )
    return sampled.reshape(plane_shape)


def crop_bounds(
    mask: np.ndarray,
    spacing_mm: tuple[float, float],
    margin_mm: float = 8.0,
) -> tuple[slice, slice]:
    coordinates = np.argwhere(mask)
    x_margin = int(np.ceil(margin_mm / spacing_mm[0]))
    z_margin = int(np.ceil(margin_mm / spacing_mm[1]))
    x_start = max(0, int(coordinates[:, 0].min()) - x_margin)
    x_stop = min(
        mask.shape[0],
        int(coordinates[:, 0].max()) + x_margin + 1,
    )
    z_start = max(0, int(coordinates[:, 1].min()) - z_margin)
    z_stop = min(
        mask.shape[1],
        int(coordinates[:, 1].max()) + z_margin + 1,
    )
    return slice(x_start, x_stop), slice(z_start, z_stop)


def image_extent(
    affine: np.ndarray,
    x_slice: slice,
    z_slice: slice,
) -> list[float]:
    x_spacing = float(affine[0, 0])
    z_spacing = float(affine[2, 2])
    x_offset = float(affine[0, 3])
    z_offset = float(affine[2, 3])
    return [
        x_offset + (x_slice.start - 0.5) * x_spacing,
        x_offset + (x_slice.stop - 0.5) * x_spacing,
        z_offset + (z_slice.start - 0.5) * z_spacing,
        z_offset + (z_slice.stop - 0.5) * z_spacing,
    ]


def apply_style() -> None:
    plt.rcParams.update(
        {
            "font.family": "Arial",
            "font.size": 12.0,
            "axes.titlesize": 12.0,
            "axes.labelsize": 12.0,
            "xtick.labelsize": 10.8,
            "ytick.labelsize": 10.8,
            "savefig.dpi": 300,
            "figure.dpi": 300,
            "svg.fonttype": "none",
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
        }
    )


def anatomy_rgba(
    anatomy: np.ndarray,
    mask: np.ndarray,
) -> np.ndarray:
    lower, upper = np.percentile(
        anatomy[mask],
        [1.0, 99.4],
    )
    normalized = np.clip(
        (anatomy - lower) / (upper - lower),
        0.0,
        1.0,
    )
    gray = 0.68 + 0.29 * normalized
    rgba = np.ones((*gray.shape, 4), dtype=np.float32)
    rgba[..., :3] = gray[..., None]
    rgba[..., 3] = mask
    return rgba


def draw_pressure(
    axes: plt.Axes,
    pressure_kpa: np.ndarray,
    mask: np.ndarray,
    extent: list[float],
    pressure_max_kpa: float,
    colormap: str,
) -> None:
    visible = mask & np.isfinite(pressure_kpa) & (pressure_kpa > 0)
    display = np.ma.masked_where(~visible, pressure_kpa)
    alpha = np.zeros(pressure_kpa.shape, dtype=np.float32)
    alpha[visible] = (
        0.08
        + 0.62
        * np.clip(
            pressure_kpa[visible] / pressure_max_kpa,
            0.0,
            1.0,
        )
        ** 0.55
    )
    axes.imshow(
        display.T,
        origin="lower",
        extent=extent,
        cmap=colormap,
        vmin=0.0,
        vmax=pressure_max_kpa,
        alpha=alpha.T,
        interpolation="bilinear",
    )


def draw_smoothed_mask(
    axes: plt.Axes,
    mask: np.ndarray,
    extent: list[float],
    color: str,
    linewidth: float,
    linestyle: str | tuple[float, tuple[float, ...]] = "solid",
    fill_alpha: float | None = None,
) -> None:
    field = gaussian_filter(mask.astype(np.float32), sigma=1.0)
    if fill_alpha is not None:
        axes.contourf(
            field.T,
            levels=[0.5, 1.01],
            extent=extent,
            colors=[color],
            alpha=fill_alpha,
        )
    axes.contour(
        field.T,
        levels=[0.5],
        extent=extent,
        colors=[color],
        linewidths=linewidth,
        linestyles=[linestyle],
    )


def draw_panel(
    axes: plt.Axes,
    anatomy: np.ndarray,
    brain_mask: np.ndarray,
    pressure_kpa: np.ndarray,
    coverage_mask: np.ndarray,
    inside_mask: np.ndarray,
    target_mask: np.ndarray,
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

    pressure_mask = brain_mask & coverage_mask
    draw_pressure(
        axes,
        pressure_kpa,
        pressure_mask & ~inside_mask,
        extent,
        pressure_max_kpa,
        "Reds",
    )
    draw_pressure(
        axes,
        pressure_kpa,
        pressure_mask & inside_mask,
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
    draw_smoothed_mask(
        axes,
        target_mask,
        extent,
        TARGET_COLOR,
        linewidth=1.3,
        fill_alpha=0.32,
    )

    axes.set_title(title, pad=4.0)
    axes.set_aspect("equal")
    axes.set_xticks([])
    axes.set_yticks([])
    for spine in axes.spines.values():
        spine.set_visible(False)


def add_pressure_colorbars(
    figure: plt.Figure,
    pressure_max_kpa: float,
) -> None:
    normalization = Normalize(0.0, pressure_max_kpa)
    red_axes = figure.add_axes([0.892, 0.20, 0.012, 0.62])
    blue_axes = figure.add_axes([0.910, 0.20, 0.012, 0.62])

    red_bar = figure.colorbar(
        plt.cm.ScalarMappable(
            norm=normalization,
            cmap="Reds",
        ),
        cax=red_axes,
    )
    red_bar.set_ticks([])
    red_bar.outline.set_visible(False)

    blue_bar = figure.colorbar(
        plt.cm.ScalarMappable(
            norm=normalization,
            cmap="Blues",
        ),
        cax=blue_axes,
    )
    blue_bar.set_ticks([0.0, pressure_max_kpa])
    blue_bar.outline.set_visible(False)
    blue_bar.ax.tick_params(length=0)
    figure.text(
        0.970,
        0.51,
        "Pressure (kPa)",
        rotation=90,
        va="center",
        ha="center",
    )


def main() -> None:
    args = parse_args()
    subject_id = args.subject
    planning_dir = (
        args.data_root
        / "planning_images"
        / subject_id
        / "planning_images"
    )
    simulation_dir = (
        args.data_root / "simulation_outputs" / subject_id
    )
    postprocessing_dir = args.data_root / "postprocessing" / "brain"
    output_dir = postprocessing_dir / "pressure_plots"

    anatomy_image = nib.load(
        str(planning_dir / f"{subject_id}_fgatir.nii.gz")
    )
    brain_image = nib.load(
        str(planning_dir / f"{subject_id}_brainmask.nii.gz")
    )
    target_image = nib.load(
        str(planning_dir / f"{subject_id}_drtt.nii.gz")
    )
    active_image = nib.load(
        str(simulation_dir / "pressure_no_lens_native.nii.gz")
    )
    control_image = nib.load(
        str(simulation_dir / "pressure_lens_native.nii.gz")
    )
    coverage_image = nib.load(
        str(simulation_dir / "coverage_mask_native.nii.gz")
    )
    inside_image = nib.load(
        str(
            postprocessing_dir
            / "masks"
            / f"{subject_id}_inside_mask.nii.gz"
        )
    )

    target = np.asanyarray(target_image.dataobj) > 0
    target_world = nib.affines.apply_affine(
        target_image.affine,
        np.argwhere(target),
    )
    target_center_world = np.median(target_world, axis=0)
    target_center_reference = nib.affines.apply_affine(
        np.linalg.inv(anatomy_image.affine),
        target_center_world,
    )
    slice_y = int(
        np.rint(target_center_reference[1])
    )
    world, plane_shape = reference_plane_world_coordinates(
        anatomy_image,
        slice_y,
    )

    anatomy_plane = np.asanyarray(
        anatomy_image.dataobj[:, slice_y, :]
    ).astype(np.float32, copy=False)
    brain_plane = (
        np.asanyarray(brain_image.dataobj[:, slice_y, :]) > 0
    )
    target_plane = sample_plane(
        target,
        target_image,
        world,
        plane_shape,
        order=0,
    ) > 0.5

    active_pressure = np.asanyarray(
        active_image.dataobj
    ).astype(np.float32, copy=False)
    control_pressure = np.asanyarray(
        control_image.dataobj
    ).astype(np.float32, copy=False)
    coverage = np.asanyarray(coverage_image.dataobj) > 0
    inside = np.asanyarray(inside_image.dataobj) > 0

    active_plane_kpa = sample_plane(
        active_pressure,
        active_image,
        world,
        plane_shape,
        order=1,
    ) / 1e3
    control_plane_kpa = sample_plane(
        control_pressure,
        control_image,
        world,
        plane_shape,
        order=1,
    ) / 1e3
    coverage_plane = sample_plane(
        coverage,
        coverage_image,
        world,
        plane_shape,
        order=0,
    ) > 0.5
    inside_plane = sample_plane(
        inside,
        inside_image,
        world,
        plane_shape,
        order=0,
    ) > 0.5
    inside_plane &= brain_plane & coverage_plane

    spacing = anatomy_image.header.get_zooms()[:3]
    x_slice, z_slice = crop_bounds(
        brain_plane,
        (float(spacing[0]), float(spacing[2])),
    )
    extent = image_extent(
        anatomy_image.affine,
        x_slice,
        z_slice,
    )

    anatomy_plane = anatomy_plane[x_slice, z_slice]
    brain_plane = brain_plane[x_slice, z_slice]
    target_plane = target_plane[x_slice, z_slice]
    active_plane_kpa = active_plane_kpa[x_slice, z_slice]
    control_plane_kpa = control_plane_kpa[x_slice, z_slice]
    coverage_plane = coverage_plane[x_slice, z_slice]
    inside_plane = inside_plane[x_slice, z_slice]

    pressure_values_kpa = np.concatenate(
        [
            active_pressure[active_pressure > 0],
            control_pressure[control_pressure > 0],
        ]
    ) / 1e3
    pressure_max_kpa = args.pressure_max_kpa
    if pressure_max_kpa is None:
        pressure_max_kpa = float(
            np.percentile(pressure_values_kpa, 99.5)
        )

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
        anatomy_plane,
        brain_plane,
        active_plane_kpa,
        coverage_plane,
        inside_plane,
        target_plane,
        extent,
        pressure_max_kpa,
        "Active",
    )
    draw_panel(
        axes[1],
        anatomy_plane,
        brain_plane,
        control_plane_kpa,
        coverage_plane,
        inside_plane,
        target_plane,
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
