"""#3419: a `DropShadow` kimeneti mérete a bináris kiterjesztője szerint.

A `0x00bcd760` oldalanként `ceil(blur · 1,3501)` képponttal tágít (HIGH
minőség, `0x00cf4368`), a `blur` KÉPPONT és `clamp(1, 255)` (`0x00bcd640`);
a kitágított dobozt az árnyék `(dx, dy)` eltolja, és a kimenet a kettő
UNIÓJA az eredeti képpel (`docs/specs/filterdesc-registry.md`, „A
`DropShadow` vászon-margója").

A három várt méret a 684-es golden valódi Picasa-exportjaiból MÉRVE
(960 × 640-es forrás): `alap` 988 × 668, `max` 1232 × 912, `min` 964 × 644.
"""

from __future__ import annotations

import numpy as np
import pytest

from picasapy.ini.filters import parse_filters
from picasapy.render.chain import apply_filters
from picasapy.render.chain_geometry import keret_geometria
from picasapy.render.glimmer_frames import apply_drop_shadow


def _kep(h: int = 640, w: int = 960) -> np.ndarray:
    return np.full((h, w, 3), 128, dtype=np.uint8)


@pytest.mark.parametrize(
    ("distance", "angle", "blur", "varhato"),
    [
        (4.0, 90.0, 10.0, (668, 988)),  # 684 `alap`: ceil(10 · 1,3501) = 14
        (30.0, 360.0, 100.0, (912, 1232)),  # 684 `max`: ceil(100 · 1,3501) = 136
        (0.0, 0.0, 0.0, (644, 964)),  # 684 `min`: blur → 1, ceil(1,3501) = 2
    ],
)
def test_a_meret_a_golden_szerint(distance, angle, blur, varhato):
    ki = apply_drop_shadow(_kep(), distance=distance, angle=angle, blur=blur, fade=30.0)
    assert ki.shape[:2] == varhato


def test_a_margot_meghalado_eltolas_aszimmetrikus_uniot_ad():
    """blur 1 → margó 2, de a 30 képpontos vízszintes eltolás kilóg belőle:
    a kimenet az eltolt doboz és az eredeti kép uniója — balra nincs
    tágítás, jobbra 30 + 2."""
    ki = apply_drop_shadow(_kep(), distance=30.0, angle=0.0, blur=1.0, fade=0.0)
    assert ki.shape[:2] == (640 + 2 + 2, 960 + 0 + 32)


def test_a_blur_kepppontban_ertendo_nem_a_rovidebb_oldal_szazalekaban():
    """Ugyanaz a `blur` két különböző méretű képen UGYANANNYI margót ad."""
    kicsi = apply_drop_shadow(_kep(100, 150), distance=0.0, angle=0.0, blur=10.0, fade=30.0)
    nagy = apply_drop_shadow(_kep(1000, 1500), distance=0.0, angle=0.0, blur=10.0, fade=30.0)
    assert kicsi.shape[0] - 100 == nagy.shape[0] - 1000 == 28


@pytest.mark.parametrize(
    "lanc",
    [
        "DropShadow=1,4.000000,90.000000,10.000000,00000000,00ffffff,30.000000;",
        "DropShadow=1,30.000000,0.000000,1.000000,00000000,00ffffff,0.000000;",
    ],
)
def test_a_szerkeszto_geometriaja_a_rendert_koveti(lanc):
    """A `chain_geometry` a kép HELYÉT és a kimenet méretét is a renderelő
    szerint adja — a jelölő-képpont a mátrix szerinti helyen van."""
    kep = np.full((64, 96, 3), 200, dtype=np.uint8)
    kep[10, 20] = (255, 0, 0)
    ops = parse_filters(lanc)
    ki = apply_filters(kep, ops).image
    geo = keret_geometria(ops, 96, 64)
    assert (geo.szelesseg, geo.magassag) == (ki.shape[1], ki.shape[0])
    (a, b, c), (d, e, f) = geo.matrix
    x, y = a * 20 + b * 10 + c, d * 20 + e * 10 + f
    assert tuple(int(v) for v in ki[int(round(y)), int(round(x))]) == (255, 0, 0)
