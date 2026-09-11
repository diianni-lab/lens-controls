"""Small shared operations for the hydrophone pressure-ratio scripts."""

import csv
from collections import namedtuple

import numpy as np
from scipy.ndimage import zoom


Plane = namedtuple(
    "Plane",
    "horizontal_mm vertical_mm values horizontal_label vertical_label",
)
UPSAMPLE = 4
MINUS_6DB = 10 ** (-6 / 20)


def read_plane_csv(path):
    table = np.genfromtxt(path, delimiter=",")
    return table[0, 1:], table[1:, 0], np.maximum(-table[1:, 1:], 0)


def upsample(x, y, values):
    return (
        np.linspace(x[0], x[-1], x.size * UPSAMPLE),
        np.linspace(y[0], y[-1], y.size * UPSAMPLE),
        zoom(values, (UPSAMPLE, UPSAMPLE), order=1),
    )


def crop(planes, reference):
    output = {}
    for name, plane in planes.items():
        limits = reference[name]
        x = (plane.horizontal_mm >= limits.horizontal_mm.min()) & (
            plane.horizontal_mm <= limits.horizontal_mm.max()
        )
        y = (plane.vertical_mm >= limits.vertical_mm.min()) & (
            plane.vertical_mm <= limits.vertical_mm.max()
        )
        output[name] = Plane(
            plane.horizontal_mm[x],
            plane.vertical_mm[y],
            plane.values[np.ix_(y, x)],
            plane.horizontal_label,
            plane.vertical_label,
        )
    return output


def normalize(no_lens, lens):
    maximum = max(
        np.nanmax(plane.values)
        for planes in (no_lens, lens)
        for plane in planes.values()
    )
    for planes in (no_lens, lens):
        for name, plane in planes.items():
            planes[name] = plane._replace(values=plane.values / maximum)


def minus6db_masks(no_lens):
    return {
        name: np.isfinite(plane.values)
        & (plane.values >= np.nanmax(plane.values) * MINUS_6DB)
        for name, plane in no_lens.items()
    }


def pressure_ratios(source, no_lens, lens):
    rows = []
    masks = minus6db_masks(no_lens)
    for name in ("xz", "xy"):
        inside = masks[name]
        outside = np.isfinite(no_lens[name].values) & ~inside
        for condition, plane in (("no_lens", no_lens[name]), ("lens", lens[name])):
            values = plane.values
            mean_inside = values[inside & np.isfinite(values)].mean()
            mean_outside = values[outside & np.isfinite(values)].mean()
            rows.append(
                {
                    "source": source,
                    "plane": name,
                    "condition": condition,
                    "inside_mean": float(mean_inside),
                    "outside_mean": float(mean_outside),
                    "ratio": float(mean_inside / mean_outside),
                }
            )
    return rows


def write_results(path, rows):
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
