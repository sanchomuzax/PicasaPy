"""Nyomtatási Lanczos-átméretezés a Beállítások két minőségi módjához."""

from __future__ import annotations

import math

import numpy as np
from PySide6.QtGui import QImage


def _resample_axis(
    image: np.ndarray, output_size: int, axis: int, radius: int
) -> np.ndarray:
    moved = np.moveaxis(image, axis, 0)
    input_size = moved.shape[0]
    if input_size == output_size:
        return image

    scale = input_size / output_size
    kernel_scale = max(1.0, scale)
    taps = math.ceil(2 * radius * kernel_scale) + 2
    output = np.empty(
        (output_size, *moved.shape[1:]), dtype=np.float32
    )

    # Kis kötegekben dolgozunk: nagy felbontású fotón se keletkezzen egy
    # teljes kimeneti tengely × taps méretű ideiglenes tömb.
    for start in range(0, output_size, 8):
        stop = min(output_size, start + 8)
        centers = (np.arange(start, stop, dtype=np.float64) + 0.5) * scale
        first = np.floor(centers - radius * kernel_scale - 0.5).astype(int) + 1
        indices = first[:, None] + np.arange(taps)[None, :]
        distance = (indices + 0.5 - centers[:, None]) / kernel_scale
        weights = np.sinc(distance) * np.sinc(distance / radius)
        valid = (np.abs(distance) < radius) & (indices >= 0) & (indices < input_size)
        weights *= valid
        totals = weights.sum(axis=1, keepdims=True)
        weights = np.divide(
            weights,
            totals,
            out=np.zeros_like(weights),
            where=np.abs(totals) > 1e-12,
        ).astype(np.float32)
        samples = moved[np.clip(indices, 0, input_size - 1)]
        output[start:stop] = np.einsum(
            "nkoc,nk->noc", samples, weights, optimize=True
        )

    return np.moveaxis(output, 0, axis)


def lanczos_resize(image: QImage, width: int, height: int, radius: int) -> QImage:
    """A kép átméretezése Lanczos-3 vagy Lanczos-8 maggal.

    A célméretet a nyomtatási cella adja. A premultiplikált RGBA alak a
    részben átlátszó pixeleket is peremhalók nélkül kezeli.
    """
    if radius not in (3, 8):
        raise ValueError("A nyomtatási Lanczos-sugár 3 vagy 8 lehet")
    width, height = max(1, int(width)), max(1, int(height))
    if image.isNull() or (image.width() == width and image.height() == height):
        return image

    rgba = image.convertToFormat(QImage.Format.Format_RGBA8888_Premultiplied)
    bits = rgba.bits()
    if hasattr(bits, "setsize"):
        bits.setsize(rgba.sizeInBytes())
    else:
        bits = memoryview(bits)[: rgba.sizeInBytes()]
    rows = np.frombuffer(bits, dtype=np.uint8).reshape(
        rgba.height(), rgba.bytesPerLine()
    )
    pixels = rows[:, :rgba.width() * 4].reshape(rgba.height(), rgba.width(), 4)
    scaled = _resample_axis(pixels.astype(np.float32), width, 1, radius)
    scaled = _resample_axis(scaled, height, 0, radius)
    np.clip(np.rint(scaled), 0, 255, out=scaled)
    encoded = np.ascontiguousarray(scaled.astype(np.uint8))
    return QImage(
        encoded.data,
        width,
        height,
        width * 4,
        QImage.Format.Format_RGBA8888_Premultiplied,
    ).copy()
