#!/usr/bin/env python3
"""Extract the human simulation and hydrophone pressure ratios."""

import argparse
from pathlib import Path

import numpy as np
from scipy.io import loadmat

from pressure_ratio_processing import (
    Plane,
    crop,
    pressure_ratios,
    read_plane_csv,
    upsample,
    write_results,
)


LENS_CORRECTION = 1.206
KTX_OFFSET_MM = 5.09


def simulation(path, scale):
    data = loadmat(path, squeeze_me=True, struct_as_record=False)
    x = np.asarray(data["lateralXMm"], float).ravel()
    y = np.asarray(data["lateralYMm"], float).ravel()
    z = np.asarray(data["depthMm"], float).ravel()
    return {
        "xz": Plane(x, z, np.asarray(data["xzMpa"], float) * scale, "x", "z"),
        "xy": Plane(x, y, np.asarray(data["xyMpa"], float) * scale, "x", "y"),
    }


def hydrophone(data_root, condition):
    folder = data_root / "hydrophone" / condition
    scale = LENS_CORRECTION if condition == "lens" else 1

    x, z, values = read_plane_csv(folder / "xz.csv")
    z = -z - KTX_OFFSET_MM
    if z[0] > z[-1]:
        z, values = z[::-1], values[::-1]
    x, z, values = upsample(x, z, values * scale)

    xy_x, y, xy_values = read_plane_csv(folder / "xy.csv")
    xy_x, y, xy_values = upsample(xy_x, y - 40, xy_values * scale)
    return {
        "xz": Plane(x, z, values, "x", "z"),
        "xy": Plane(xy_x, y, xy_values, "x", "y"),
    }


def load_planes(data_root):
    hydrophone_no_lens = hydrophone(data_root, "no_lens")
    hydrophone_lens = hydrophone(data_root, "lens")
    folder = data_root / "simulation"
    simulation_no_lens = simulation(folder / "no_lens.mat", 1)
    simulation_lens = simulation(folder / "lens.mat", LENS_CORRECTION)
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
