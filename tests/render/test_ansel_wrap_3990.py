"""#3990 — `ansel` N 32 bites körbefordulása.

Forrás: `docs/specs/filters-decoded.md`, „Az `ansel` akkumulátorainak
szélessége és a nagy képen átforduló `N` (#3990)”; a táblázat a natív
callback mért eredményeit rögzíti.
"""

from __future__ import annotations

import numpy as np

from picasapy.render import tinting
from picasapy.render.tinting import _ansel_strength


def _uniform_image(pixel: tuple[int, int, int], count: int) -> np.ndarray:
    """Nézetet ad vissza; a nagy szintetikus képhez nem foglal uint8 tömböt."""
    sample = np.asarray(pixel, dtype=np.uint8).reshape(1, 1, 3)
    return np.broadcast_to(sample, (1, count, 3))


def test_j128_n_32_bites_elofelesnel_megforditja_a_k_erosseget() -> None:
    # (131,255,0), W=(85,85,85): Y=32810, j=128, pixelenkénti N=256,
    # S₁=192, S₂=128. 8 388 608 képpontnál N előjelesen −2³¹, így k=−64.
    image = _uniform_image((131, 255, 0), 8_388_608)

    assert _ansel_strength(image, (85, 85, 85)) == -64


_SPEC_TABLE = (
    # j=128: N, S₁, S₂, k és az első kimeneti pixel.
    (
        (131, 255, 0),
        8_388_607,
        (2_147_483_392, 1_610_612_544, 1_073_741_696, 64, 192),
    ),
    (
        (131, 255, 0),
        8_388_608,
        (-2_147_483_648, 1_610_612_736, 1_073_741_824, -64, 64),
    ),
    (
        (131, 255, 0),
        8_388_609,
        (-2_147_483_392, 1_610_612_928, 1_073_741_952, -64, 64),
    ),
    # j=127: ettől eltér a körbefordulási küszöb.
    (
        (128, 128, 127),
        8_388_608,
        (2_139_095_040, 1_073_741_824, 1_065_353_216, 1, 128),
    ),
    (
        (128, 128, 127),
        8_421_504,
        (2_147_483_520, 1_077_952_512, 1_069_531_008, 1, 128),
    ),
    (
        (128, 128, 127),
        8_421_505,
        (-2_147_483_521, 1_077_952_640, 1_069_531_135, -1, 126),
    ),
)


def test_a_spec_hatarertek_tablazata() -> None:
    weights = (85, 85, 85)
    for pixel, count, expected in _SPEC_TABLE:
        image = _uniform_image(pixel, count)
        expected_n, expected_s1, expected_s2, expected_k, expected_pixel = expected

        # Ez az állítás a régi, int64-es N-nel már a teszt hozzáadásakor piros.
        assert _ansel_strength(image, weights) == expected_k
        assert tinting._ansel_strength_details(image, weights) == (
            expected_n,
            expected_s1,
            expected_s2,
            expected_k,
        )

        sample = np.asarray(pixel, dtype=np.uint8).reshape(1, 1, 3)
        gray = tinting._ansel_gray16(sample, weights)
        lift = tinting._ansel_curve_lift(gray, expected_k)
        actual_pixel = int(np.clip(gray + lift, 0, 0xFFFF)[0, 0] >> 8)
        assert actual_pixel == expected_pixel


def test_a_32_bites_n_nulla_kapuja_a_16_777_216_pixeles_esetben() -> None:
    image = _uniform_image((131, 255, 0), 16_777_216)

    strength = _ansel_strength(image, (85, 85, 85))
    assert strength is None
    assert tinting._ansel_strength_details(image, (85, 85, 85)) == (
        0,
        3_221_225_472,
        2_147_483_648,
        None,
    )
    sample = np.asarray((131, 255, 0), dtype=np.uint8).reshape(1, 1, 3)
    gray = tinting._ansel_gray16(sample, (85, 85, 85))
    lift = tinting._ansel_curve_lift(gray, strength or 0)
    assert int(lift[0, 0]) == 0
    assert int(np.clip(gray + lift, 0, 0xFFFF)[0, 0] >> 8) == 128


def test_negativ_k_elotti_aritmetikai_jobbra_tolasa_lefele_kerekit() -> None:
    # j=127-nél 8 421 505 képpont N-je −2 147 483 521, ezért k=−1.
    image = _uniform_image((128, 128, 127), 8_421_505)
    assert _ansel_strength(image, (85, 85, 85)) == -1

    gray = tinting._ansel_gray16(
        np.asarray((128, 128, 127), dtype=np.uint8).reshape(1, 1, 3),
        (85, 85, 85),
    )
    product = int((((0xFFFF - int(gray[0, 0])) * int(gray[0, 0])) >> 14) * -1)
    lift = tinting._ansel_curve_lift(gray, -1)

    assert int(lift[0, 0]) == -256
    assert int(lift[0, 0]) != int(product / 256)  # csonkítás a nulla felé: −255
    assert int(np.clip(gray + lift, 0, 0xFFFF)[0, 0] >> 8) == 126
