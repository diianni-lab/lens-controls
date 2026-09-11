"""NIfTI mask grid conversion and writing."""

from __future__ import annotations

from pathlib import Path

import nibabel as nib
import numpy as np
from nibabel.processing import resample_from_to


def same_grid(first: nib.Nifti1Image, second: nib.Nifti1Image) -> bool:
    return (
        first.shape[:3] == second.shape[:3]
        and np.allclose(first.affine, second.affine, atol=1e-4)
    )


def mask_on_grid(
    image: nib.Nifti1Image,
    reference: nib.Nifti1Image,
) -> np.ndarray:
    if not same_grid(image, reference):
        image = resample_from_to(
            image,
            (reference.shape[:3], reference.affine),
            order=0,
        )
    return np.asanyarray(image.dataobj) > 0


def matching_mask(
    path: Path,
    reference: nib.Nifti1Image,
) -> np.ndarray:
    image = nib.load(str(path))
    if not same_grid(image, reference):
        raise ValueError(f"Grid mismatch: {path}")
    return np.asanyarray(image.dataobj) > 0


def save_mask(
    path: Path,
    mask: np.ndarray,
    reference: nib.Nifti1Image,
) -> None:
    header = reference.header.copy()
    header.set_data_dtype(np.uint8)
    image = nib.Nifti1Image(
        mask.astype(np.uint8),
        reference.affine,
        header,
    )
    nib.save(image, str(path))
