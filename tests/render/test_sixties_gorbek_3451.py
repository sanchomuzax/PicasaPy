"""#3451: a Sixties (60-as évek) görbéi a `filterdesc.xml` pontjai szerint.

A szállított `runtime/filterdesc.xml` `Sixties` blokkja:

    MasterCurve = (0,0) (150,104) (243,255)
    RedCurve    = (0,59) (96,156) (210,255)
    GreenCurve  = (0,22) (150,166) (255,216)
    BlueCurve   = (0,9) (126,98) (255,231)

A kódunk a három csatornagörbe ELSŐ pontját `(y, y)`-ként olvasta, és elé
tett egy `(0, 0)`-t: a piros `(0,0), (59,59), …` lett `(0,59), …` helyett, így
a fekete feketén maradt, holott a leíró 59-re emeli (a zöld 22-re, a kék 9-re)
— ez a meleg, fakó „régi fotó" alapja. A 684-es golden ΔE-je a javítással:
alap 15,81 → 1,72, min 20,06 → 1,62.

A `curves.curve_lut` a töréspontokon kívül a szélső értéket tartja, az
`adjust_curves` lánca viszont (#3942) extrapolál; mindkét esetben a pontok
kiegészítés nélkül, a leíró szerint adhatók meg.
"""

from __future__ import annotations

import numpy as np
import pytest

from picasapy.render import glimmer_tone as t
from picasapy.render.curves import curve_lut
from picasapy.render.glimmer_ops import adjust_curves

LEIRO = {
    "_SIXTIES_MASTER": ((0.0, 0.0), (150.0, 104.0), (243.0, 255.0)),
    "_SIXTIES_RED": ((0.0, 59.0), (96.0, 156.0), (210.0, 255.0)),
    "_SIXTIES_GREEN": ((0.0, 22.0), (150.0, 166.0), (255.0, 216.0)),
    "_SIXTIES_BLUE": ((0.0, 9.0), (126.0, 98.0), (255.0, 231.0)),
}


@pytest.mark.parametrize("nev", sorted(LEIRO))
def test_a_gorbe_pontjai_a_leiro_szerint(nev):
    assert getattr(t, nev) == LEIRO[nev]


@pytest.mark.parametrize(
    "nev, fekete",
    [("_SIXTIES_RED", 59.0), ("_SIXTIES_GREEN", 22.0), ("_SIXTIES_BLUE", 9.0)],
)
def test_a_fekete_a_leiro_szerinti_szintre_emelkedik(nev, fekete):
    """A 0-s bemenet a görbe első pontjának y-ját kapja, nem nullát."""
    assert curve_lut(getattr(t, nev))[0] == pytest.approx(fekete)


def test_a_master_243_folott_telitett_feher():
    lut = curve_lut(t._SIXTIES_MASTER)
    assert lut[243] == pytest.approx(255.0)
    assert lut[250] == pytest.approx(255.0)


def test_a_kek_lanc_a_mesterertek_extrapolaciojaval_szamol():
    """#3942: a mestergörbe kimenete a láncban NEM kerekül és NEM vágódik a
    255-ös töréspontnál — a kék csatornagörbe a saját 255 fölötti bemenetre
    a szélső szakaszát EXTRAPOLÁLJA, nem tartja a szélső értéket.

    `i = 240, 245, 250, 255` → `Master(i) = 249,6 / 258,6 / 267,6 / 276,6`
    (nem vágva 255-re) → `Blue(v)` extrapolálva → `225, 235, 245, 255`
    (a jegy „Kész, ha" listája, #3941 spec).
    """
    image = np.zeros((1, 4, 3), dtype=np.uint8)
    image[0, :, 2] = [240, 245, 250, 255]

    lanc = adjust_curves(image, master=t._SIXTIES_MASTER, blue=t._SIXTIES_BLUE)

    np.testing.assert_array_equal(lanc[0, :, 2], [225, 235, 245, 255])
