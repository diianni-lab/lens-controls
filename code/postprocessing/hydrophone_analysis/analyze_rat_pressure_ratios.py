#!/usr/bin/env python3
"""Extract the rat simulation and hydrophone pressure ratios."""

import argparse
from pathlib import Path

import nibabel as nib
import numpy as np

from pressure_ratio_processing import (
    Plane,
    crop,
    normalize,
    pressure_ratios,
    read_plane_csv,
    upsample,
    write_results,
)


LENS_CORRECTION = 1.274


def pressure(path):
    image = nib.load(str(path))
    values = np.asarray(image.dataobj, float)
    if np.nanmax(values) <= 0:
        values = -values
    return np.maximum(values, 0), image


def axis_mm(image, axis, start_at_zero=False):
    samples = image.shape[axis]
    spacing = image.header.get_zooms()[axis]
    values = (np.arange(samples) - (samples - 1) / 2) * spacing
    return values - values.min() if start_at_zero else values


def simulation(data_root):
    folder = data_root / "simulation"
    no_lens, image = pressure(folder / "no_lens.nii.gz")
    lens, _ = pressure(folder / "lens.nii.gz")
    maximum = max(np.nanmax(no_lens), np.nanmax(lens))
    no_lens, lens = no_lens / maximum, lens / maximum

    z = axis_mm(image, 0, True)
    y = axis_mm(image, 1)
    x = axis_mm(image, 2)
    center_y = np.argmin(abs(y))
    peak_z = np.unravel_index(np.nanargmax(no_lens), no_lens.shape)[0]

    def extract(volume):
        return {
            "xz": Plane(x, z, volume[:, center_y, :], "x", "z"),
            "xy": Plane(x, y, volume[peak_z, :, :], "x", "y"),
        }

    return extract(no_lens), extract(lens)


def hydrophone(data_root, condition):
    folder = data_root / "hydrophone" / condition
    scale = LENS_CORRECTION if condition == "lens" else 1
    x, z, values = read_plane_csv(folder / "xz.csv")
    x, z, values = upsample(x, z, values * scale)
    xy_x, y, xy_values = read_plane_csv(folder / "xy.csv")
    xy_x, y, xy_values = upsample(xy_x, y, xy_values * scale)
    return {
        "xz": Plane(x, z, values, "x", "z"),
        "xy": Plane(xy_x, y, xy_values, "x", "y"),
    }


def load_planes(data_root):
    hydrophone_no_lens = hydrophone(data_root, "no_lens")
    hydrophone_lens = hydrophone(data_root, "lens")
    normalize(hydrophone_no_lens, hydrophone_lens)
    simulation_no_lens, simulation_lens = simulation(data_root)
    return (
        crop(simulation_no_lens, hydrophone_no_lens),
        crop(simulation_lens, hydrophone_no_lens),
        hydrophone_no_lens,
        hydrophone_lens,
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    simulation_no_lens, simulation_lens, hydrophone_no_lens, hydrophone_lens = load_planes(args.data_root)
    rows = pressure_ratios("simulation", simulation_no_lens, simulation_lens)
    rows += pressure_ratios("hydrophone", hydrophone_no_lens, hydrophone_lens)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    write_results(args.output_dir / "pressure_ratios.csv", rows)


if __name__ == "__main__":
    main()
