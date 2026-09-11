#!/usr/bin/env python3
"""Plot skull pressure with the saved covered-skull region."""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import nibabel as nib
import numpy as np
from matplotlib.colors import (
    LinearSegmentedColormap,
    Normalize,
    to_rgb,
)
from scipy.ndimage import gaussian_filter, map_coordinates


SKULL_COLOR = "#e4553d"
TARGET_COLOR = "#9b2f73"
DEVICE_COLOR = "#d9d9d9"
ELEMENT_COLOR = "#ffffff"
LENS_COLOR = "#f27a38"


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


def pressure_colormap() -> LinearSegmentedColormap:
    return LinearSegmentedColormap.from_list(
        "pressure",
        [
            "#2c115f",
            "#1f5aa6",
            "#22b7c7",
            "#f4e061",
            "#f27024",
        ],
    )


def normalized_ct(ct_hu: np.ndarray) -> np.ndarray:
    clipped = np.clip(ct_hu, -650.0, 1900.0)
    normalized = (clipped + 650.0) / 2550.0
    return 0.12 + 0.84 * normalized


def draw_pressure(
    axes: plt.Axes,
    pressure_kpa: np.ndarray,
    mask: np.ndarray,
    extent: list[float],
    pressure_max_kpa: float,
    colormap: LinearSegmentedColormap,
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
    sigma: float = 1.0,
) -> None:
    if not np.any(mask):
        return
    field = gaussian_filter(mask.astype(np.float32), sigma=sigma)
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


def draw_element_contours(
    axes: plt.Axes,
    labels: np.ndarray,
    extent: list[float],
) -> None:
    for label in np.unique(labels):
        if label > 0:
            draw_smoothed_mask(
                axes,
                labels == label,
                extent,
                ELEMENT_COLOR,
                linewidth=0.55,
            )


def draw_panel(
    axes: plt.Axes,
    ct_hu: np.ndarray,
    pressure_kpa: np.ndarray,
    pressure_mask: np.ndarray,
    skull_mask: np.ndarray | None,
    target_mask: np.ndarray | None,
    device_mask: np.ndarray,
    element_labels: np.ndarray,
    lens_mask: np.ndarray | None,
    extent: list[float],
    pressure_max_kpa: float,
    colormap: LinearSegmentedColormap,
    title: str,
    device_fill_color: str | None = None,
) -> None:
    axes.imshow(
        normalized_ct(ct_hu).T,
        origin="lower",
        extent=extent,
        cmap="gray",
        vmin=0.0,
        vmax=1.0,
        interpolation="nearest",
    )
    draw_pressure(
        axes,
        pressure_kpa,
        pressure_mask,
        extent,
        pressure_max_kpa,
        colormap,
    )
    if skull_mask is not None:
        draw_smoothed_mask(
            axes,
            skull_mask,
            extent,
            SKULL_COLOR,
            linewidth=1.2,
            linestyle=(0, (4.0, 2.5)),
            sigma=2.1,
        )
    if target_mask is not None:
        draw_smoothed_mask(
            axes,
            target_mask,
            extent,
            TARGET_COLOR,
            linewidth=1.3,
            fill_alpha=0.32,
        )
    if device_fill_color is not None:
        device_rgba = np.ones(
            (*device_mask.shape, 4), dtype=np.float32
        )
        device_rgba[..., :3] = to_rgb(device_fill_color)
        device_rgba[..., 3] = device_mask.astype(np.float32)
        axes.imshow(
            device_rgba.transpose(1, 0, 2),
            origin="lower",
            extent=extent,
            interpolation="nearest",
        )
    draw_smoothed_mask(
        axes,
        device_mask,
        extent,
        DEVICE_COLOR,
        linewidth=1.15,
    )
    draw_element_contours(axes, element_labels, extent)
    if lens_mask is not None:
        draw_smoothed_mask(
            axes,
            lens_mask,
            extent,
            LENS_COLOR,
            linewidth=1.1,
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
    planning_dir = (
        args.data_root
        / "planning_images"
        / subject_id
        / "planning_images"
    )
    simulation_dir = (
        args.data_root / "simulation_outputs" / subject_id
    )
    postprocessing_dir = args.data_root / "postprocessing" / "skull"
    output_dir = postprocessing_dir / "pressure_plots"

    ct_image = nib.load(
        str(planning_dir / f"{subject_id}_ct.nii.gz")
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
    device_image = nib.load(
        str(simulation_dir / "device_mask_native.nii.gz")
    )
    element_image = nib.load(
        str(simulation_dir / "element_labels_native.nii.gz")
    )
    lens_image = nib.load(
        str(simulation_dir / "lens_mask_native.nii.gz")
    )
    skull_image = nib.load(
        str(
            postprocessing_dir
            / "masks"
            / f"{subject_id}_skull_mask.nii.gz"
        )
    )

    target = np.asanyarray(target_image.dataobj) > 0
    target_world = nib.affines.apply_affine(
        target_image.affine,
        np.argwhere(target),
    )
    target_center_world = np.median(target_world, axis=0)
    target_center_reference = nib.affines.apply_affine(
        np.linalg.inv(ct_image.affine),
        target_center_world,
    )
    slice_y = int(
        np.rint(target_center_reference[1])
    )
    world, plane_shape = reference_plane_world_coordinates(
        ct_image,
        slice_y,
    )

    ct_plane = np.asanyarray(
        ct_image.dataobj[:, slice_y, :]
    ).astype(np.float32, copy=False)
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
    device = np.asanyarray(device_image.dataobj) > 0
    element_labels = np.asanyarray(element_image.dataobj)
    lens = np.asanyarray(lens_image.dataobj) > 0
    skull = np.asanyarray(skull_image.dataobj) > 0

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
    device_plane = sample_plane(
        device,
        device_image,
        world,
        plane_shape,
        order=0,
    ) > 0.5
    element_plane = np.rint(
        sample_plane(
            element_labels,
            element_image,
            world,
            plane_shape,
            order=0,
        )
    ).astype(np.uint8)
    lens_plane = sample_plane(
        lens,
        lens_image,
        world,
        plane_shape,
        order=0,
    ) > 0.5
    skull_plane = sample_plane(
        skull,
        skull_image,
        world,
        plane_shape,
        order=0,
    ) > 0.5

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
    pressure_floor_kpa = max(
        25.0,
        0.08 * pressure_max_kpa,
    )
    crop_mask = (
        skull_plane
        | coverage_plane
        | device_plane
        | (element_plane > 0)
        | lens_plane
        | target_plane
        | (active_plane_kpa > pressure_floor_kpa)
        | (control_plane_kpa > pressure_floor_kpa)
    )

    spacing = ct_image.header.get_zooms()[:3]
    x_slice, z_slice = crop_bounds(
        crop_mask,
        (float(spacing[0]), float(spacing[2])),
    )
    device_coordinates = np.argwhere(device_plane)
    if device_coordinates.size:
        target_coordinates = np.argwhere(target_plane)
        if np.median(device_coordinates[:, 0]) < np.median(
            target_coordinates[:, 0]
        ):
            x_slice = slice(
                int(device_coordinates[:, 0].min()),
                x_slice.stop,
            )
        else:
            x_slice = slice(
                x_slice.start,
                int(device_coordinates[:, 0].max()) + 1,
            )
    extent = image_extent(ct_image.affine, x_slice, z_slice)

    ct_plane = ct_plane[x_slice, z_slice]
    target_plane = target_plane[x_slice, z_slice]
    active_plane_kpa = active_plane_kpa[x_slice, z_slice]
    control_plane_kpa = control_plane_kpa[x_slice, z_slice]
    coverage_plane = coverage_plane[x_slice, z_slice]
    device_plane = device_plane[x_slice, z_slice]
    element_plane = element_plane[x_slice, z_slice]
    lens_plane = lens_plane[x_slice, z_slice]
    skull_plane = skull_plane[x_slice, z_slice]

    pressure_mask = coverage_plane & ~device_plane
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
        ct_plane,
        active_plane_kpa,
        pressure_mask,
        skull_plane,
        target_plane,
        device_plane,
        element_plane,
        None,
        extent,
        pressure_max_kpa,
        colormap,
        "Active",
    )
    draw_panel(
        axes[1],
        ct_plane,
        control_plane_kpa,
        pressure_mask,
        skull_plane,
        target_plane,
        device_plane,
        element_plane,
        lens_plane,
        extent,
        pressure_max_kpa,
        colormap,
        "Control",
    )
    figure.subplots_adjust(
        left=0.01,
        right=0.88,
        bottom=0.02,
        top=0.91,
        wspace=0.03,
    )
    colorbar_axes = figure.add_axes([0.905, 0.20, 0.016, 0.62])
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
