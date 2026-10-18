"""A #5296 specifikációból levezetett rainbow-láncpróbák (#5304).

Forrás: ``docs/specs/filters-decoded.md`` #5296, és a Picasa 3.9 job-194
``k08`` exportjának mért sávhatárai. A mérőképen a későbbi Sixties réteg
felülírja a palettaszíneket; itt ezért közvetlenül a rainbow köztes képét
ellenőrizzük.
"""

from __future__ import annotations

import math

import numpy as np

from picasapy.ini.filters import parse_filters
from picasapy.render.chain import KNOWN_UNRENDERED_OPS, _HANDLERS, apply_filters
from picasapy.render.ops import apply_channel_levels_stretch

_PALETTA = (
    (236, 66, 66),
    (236, 151, 66),
    (236, 236, 66),
    (63, 199, 63),
    (66, 66, 236),
    (127, 59, 161),
)


def _spec_szerinti_rainbow_kimenet(image: np.ndarray, preserve: int) -> np.ndarray:
    """A #5296 képleteit alkalmazó teszt-orákulum, a meglévő szinthúzóval."""
    stretched = apply_channel_levels_stretch(image, blend=0.30, careful=True)
    luma = (
        77 * stretched[..., 0].astype(np.int32)
        + 151 * stretched[..., 1].astype(np.int32)
        + 28 * stretched[..., 2].astype(np.int32)
    ) >> 8
    weight = 256 - preserve
    gray = np.clip(
        stretched.astype(np.int32)
        + (((luma[..., None] - stretched.astype(np.int32)) * weight) >> 8),
        0,
        255,
    ).astype(np.uint8)

    # #5304: a gamma-LUT-ot a callback csak az ELSŐ sávnál kéri (`0x008f94ac`
    # `test esi,esi` + `0x008f94c6` `jne`), és az egész képre alkalmazza; a k
    # tehát az első palettaszínből jön, a többi sáv ugyanazt a görbét kapja.
    first = _PALETTA[0]
    k = ((max(first) * 255 / (sum(first) * 85) - 1) * 0.5) + 1
    gamma_lut = np.array(
        [math.floor((i / 255.0) ** (1.0 / k) * 255.0 + 0.5) for i in range(256)],
        dtype=np.uint8,
    )
    adjusted_all = gamma_lut[gray]
    height = gray.shape[0]
    output = np.empty_like(gray)
    for band, palette in enumerate(_PALETTA):
        start = round(band * height / 6)
        end = round((band + 1) * height / 6)
        maximum = max(palette)
        adjusted = adjusted_all[start:end]
        for channel, color in enumerate(palette):
            output[start:end, :, channel] = np.minimum(
                255, adjusted[..., channel].astype(np.uint16) * color // maximum
            ).astype(np.uint8)
    return output


def test_rainbow_853px_savban_a_mert_hatarokat_es_a_hatos_palettat_adja() -> None:
    """Az 853 soros k08 minta nearest-even határai és a gamma+szorzópaletta."""
    ramp = np.arange(256, dtype=np.uint8)
    image = np.broadcast_to(ramp[None, :, None], (853, 256, 3)).copy()
    report = apply_filters(image, parse_filters("rainbow=1,0.000000;"))

    assert "rainbow" in _HANDLERS
    assert "rainbow" not in KNOWN_UNRENDERED_OPS
    assert report.skipped == ()
    assert np.array_equal(report.image, _spec_szerinti_rainbow_kimenet(image, 0))

    boundaries = (0, 142, 284, 426, 569, 711, 853)
    for band, (start, end) in enumerate(
        zip(boundaries[:-1], boundaries[1:], strict=True)
    ):
        assert np.array_equal(report.image[start, 255], report.image[end - 1, 255])
        if band < 5:
            assert not np.array_equal(
                report.image[end - 1, 255], report.image[end, 255]
            )


def test_rainbow_masodik_parametere_szabja_a_szinertek_megorzeset() -> None:
    """A 0 szürkeárnyalatot, a 256 teljes színmegőrzést kér (#5296)."""
    height, width = 48, 64
    y, x = np.indices((height, width))
    image = np.stack(
        (
            ((x * 11 + y * 3) % 256).astype(np.uint8),
            ((x * 5 + y * 13 + 17) % 256).astype(np.uint8),
            ((x * 7 + y * 19 + 31) % 256).astype(np.uint8),
        ),
        axis=-1,
    )

    grayscale, skipped_gray = apply_filters(
        image, parse_filters("rainbow=1,0.000000;")
    )
    preserved, skipped_preserved = apply_filters(
        image, parse_filters("rainbow=1,256.000000;")
    )

    assert skipped_gray == skipped_preserved == ()
    assert not np.array_equal(grayscale, preserved)
    assert np.array_equal(grayscale, _spec_szerinti_rainbow_kimenet(image, 0))
    assert np.array_equal(preserved, _spec_szerinti_rainbow_kimenet(image, 256))


def test_rainbow_minden_sava_az_elso_sav_gamma_gorbejet_kapja_5304() -> None:
    """A sárga sáv ugyanazt a gammát kapja, mint a piros (#5304, `0x008f94c6`)."""
    ramp = np.arange(256, dtype=np.uint8)
    image = np.broadcast_to(ramp[None, :, None], (60, 256, 3)).copy()
    out = apply_filters(image, parse_filters("rainbow=1,0.000000;")).image
    # a piros és a sárga sáv R-csatornája azonos (236/236), ha a gamma közös;
    # sávonkénti gammánál a középtónusokban eltérnének
    assert np.array_equal(out[5, :, 0], out[25, :, 0])
