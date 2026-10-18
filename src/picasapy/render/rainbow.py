"""A Picasa `rainbow` szűrője (#5304).

A lépések és a konstansok a `docs/specs/filters-decoded.md` #5296
szakaszából származnak: 30%-os szinthúzás CarefulEnhance móddal,
paraméterezett színmegőrzés, az első sáv színéből számolt gamma-LUT az egész
képre, majd a hat palettaszín
maximális csatornájával normalizált szorzókeverés.
"""

from __future__ import annotations

from functools import lru_cache

import numpy as np

from picasapy.render.curves import validate_image
from picasapy.render.ops import apply_channel_levels_stretch

_PALETTE: tuple[tuple[int, int, int], ...] = (
    (236, 66, 66),
    (236, 151, 66),
    (236, 236, 66),
    (63, 199, 63),
    (66, 66, 236),
    (127, 59, 161),
)


@lru_cache(maxsize=len(_PALETTE))
def _gamma_lut(palette: tuple[int, int, int]) -> np.ndarray:
    """A natív `0x00aa40a0` LUT-ja: `lroundf(powf(i/255, 1/k) * 255)`."""
    colors = np.asarray(palette, dtype=np.float32)
    maximum = np.float32(colors.max())
    total = np.sum(colors, dtype=np.float32)
    ratio = np.float32(maximum * np.float32(255.0)) / np.float32(
        total * np.float32(85.0)
    )
    gamma = np.float32(
        (ratio - np.float32(1.0)) * np.float32(0.5) + np.float32(1.0)
    )
    exponent = np.float32(np.float32(1.0) / gamma)
    values = np.arange(256, dtype=np.float32) / np.float32(255.0)
    curved = np.power(values, exponent) * np.float32(255.0)
    # lroundf kerekítése pozitív értékeknél floor(x + 0,5).
    return np.floor(curved + np.float32(0.5)).clip(0, 255).astype(np.uint8)


def _preserve_color(image: np.ndarray, preserve: int) -> np.ndarray:
    """A `0x009a9550` luma-keverése; 256-nál a natív callback kihagyja."""
    if preserve == 256:
        return image

    rgb = image.astype(np.int32)
    luma = (77 * rgb[..., 0] + 151 * rgb[..., 1] + 28 * rgb[..., 2]) >> 8
    weight = 256 - preserve
    adjusted = rgb + (((luma[..., None] - rgb) * weight) >> 8)
    return np.clip(adjusted, 0, 255).astype(np.uint8)


def _band_boundaries(height: int) -> tuple[int, ...]:
    """Az x87 `FISTP` nearest-even határai a tárolt float32 lépésközből."""
    band_height = np.float32(np.float32(height) / np.float32(6.0))
    return tuple(
        int(np.rint(np.float32(index) * band_height)) for index in range(7)
    )


def _colorize_bands(pixels: np.ndarray) -> np.ndarray:
    height = pixels.shape[0]
    output = np.empty_like(pixels)
    boundaries = _band_boundaries(height)
    # A callback a gamma-LUT-ot csak az első sávnál kéri (`0x008f94ac`
    # `test esi,esi`, `0x008f94c6` `jne`), és az egész képre alkalmazza:
    # minden sáv az első palettaszín görbéjét kapja (#5304).
    adjusted_all = _gamma_lut(_PALETTE[0])[pixels].astype(np.uint16)

    for index, palette in enumerate(_PALETTE):
        start, end = boundaries[index : index + 2]
        if start == end:
            continue
        maximum = max(palette)
        adjusted = adjusted_all[start:end]
        for channel, color in enumerate(palette):
            output[start:end, :, channel] = np.minimum(
                255, adjusted[..., channel] * color // maximum
            ).astype(np.uint8)

    return output


def apply_rainbow(image: np.ndarray, preserve: int = 0) -> np.ndarray:
    """A `rainbow` natív renderlánca a megadott színmegőrzési paraméterrel.

    A szinthúzó ugyanaz a `0x009db610`, amit az `enhance` és az
    `autocontrast` is használ, de a rainbow callback 0,30-as vágópont-keverést
    és CarefulEnhance állapotot ad át. A `preserve` egész értékét a lánc a
    második paraméterből csonkolja; 256-nál a telítetlenítő lépés kimarad.
    A mag képet vesz át és képet ad vissza, fájlhoz nem nyúl.
    """
    validate_image(image)
    stretched = apply_channel_levels_stretch(image, blend=0.30, careful=True)
    preserved = _preserve_color(stretched, preserve)
    return _colorize_bands(preserved)


__all__ = ["apply_rainbow"]
