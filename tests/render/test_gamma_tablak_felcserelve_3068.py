"""#3068 — a Lineáris és a Mac gamma keresőtáblája NEM cserélhető fel.

## Mi történt

A `picasa-megjelenitesi-modok.md` 5.9 és 5.10 szakasza sokáig fel volt
cserélve, és a #1578 ebben az állapotban valósította meg a Lineáris gammát:
a `0x00d32bd0` beégetett táblát (≈ gamma 1,44) kapta a **lineáris** mód,
a Mac gamma pedig egy képernyőképből illesztett kitevőt (0,7743).

A spec önhelyesbítése 2026-09-09-én megtörtént (#2816), a kódba viszont nem
jutott el — a #1578 addigra zárt jegy volt.

## A mért igazság (spec 12.4)

| mód | átalakító | mit ad át | melyik tábla |
|---|---|---|---|
| `ID_VIEW_MAC` | `0x009e8b40` (`fldz`) | **0,0** | `0x00d32bd0` — **beégetve** |
| `ID_VIEW_LINEAR` | `0x009e8b60` (`fld [0xcf4140]`) | **2,2** | `0x00d32cd0` — futásidőben töltve |

A `0.0`-ág választása a `0x00aa3fd2`-n olvasható; a futásidejű kitöltő
(`0x00aa3ff0`–`0x00aa404a`) a `round(pow(i/255, 1/gamma) · 255)` képletet
számolja, tehát a lineáris mód **pontosan 2,2**-es.

## Amit ez a fájl őriz

A két tábla **nem cserélhető vissza** némán: az egyik bájtra a
binárisból jön, a másik képletből. A jegy a `0x00932bd0` fájloffszeten
újraolvasva is ugyanazt a 256 bájtot adta.
"""

from __future__ import annotations

import re
from pathlib import Path

import numpy as np
import pytest

from picasapy.render.display_modes import (
    LINEAR_GAMMA_LUT,
    MAC_GAMMA_LUT,
    apply_display_mode,
)

SPEC = Path(__file__).resolve().parents[2] / "docs/specs/picasa-megjelenitesi-modok.md"


def _spec_tablaja() -> tuple[int, ...]:
    """A spec 5.9 szakaszában kiírt 256 bájt — a `0x00d32bd0` tábla."""
    szoveg = SPEC.read_text(encoding="utf-8")
    blokk = szoveg[szoveg.index("### 5.9 ") : szoveg.index("### 5.10 ")]
    kod = re.search(r"```\n(.*?)```", blokk, re.S)
    assert kod is not None, "a spec 5.9 szakaszában nincs kódblokk"
    ertekek: list[int] = []
    for sor in kod.group(1).strip().splitlines():
        index, _, maradek = sor.partition(":")
        assert int(index.strip()) == len(ertekek), f"kihagyott sor: {sor!r}"
        ertekek.extend(int(v) for v in maradek.split())
    return tuple(ertekek)


class TestAMacGammaAMertTabla:
    def test_bajtra_egyezik_a_spec_tablajaval(self):
        assert tuple(MAC_GAMMA_LUT) == _spec_tablaja(), (
            "a Mac gamma táblája nem a binárisból kiolvasott `0x00d32bd0` — "
            "a spec 12.4 szerint a `0.0`-ág EZT választja"
        )

    def test_nem_a_kepernyokepbol_illesztett_kitevo(self):
        """A #1580 képernyőkép-mérése 0,7743-as kitevőt adott; a bináris
        tábláé 0,6945. A kettő nem ugyanaz, és a tábla az erősebb."""
        illesztett = tuple(
            int(round(255.0 * (i / 255.0) ** 0.7743)) for i in range(256)
        )
        assert tuple(MAC_GAMMA_LUT) != illesztett


class TestALinearisGammaSzamitott:
    def test_a_2_2_kepletet_koveti(self):
        """Az eredeti ezt a táblát futásidőben tölti fel
        (`0x00aa3ff0`–`0x00aa404a`), a `2,2`-es kitevővel."""
        vart = tuple(
            int(round(255.0 * (i / 255.0) ** (1.0 / 2.2))) for i in range(256)
        )
        assert tuple(LINEAR_GAMMA_LUT) == vart

    def test_nem_a_beegetett_tabla(self):
        assert tuple(LINEAR_GAMMA_LUT) != _spec_tablaja(), (
            "a lineáris mód még mindig a Mac gamma beégetett tábláját kapja"
        )


class TestAKetModKulonbozik:
    @pytest.mark.parametrize("ertek", [1, 32, 64, 128, 192, 240])
    def test_mindketto_vilagosit(self, ertek: int):
        kep = np.full((2, 2, 3), ertek, dtype=np.uint8)
        assert int(apply_display_mode(kep, "mac")[0, 0, 0]) > ertek
        assert int(apply_display_mode(kep, "linear")[0, 0, 0]) > ertek

    def test_a_linearis_ERŐSEBBEN_vilagosit(self):
        """A `1/2,2` kitevő kisebb, mint a tábla ≈`0,6945`-e, tehát a
        lineáris mód jobban nyitja a sötét részleteket. Ez a kontroll
        arra, hogy a kettő tényleg nem ugyanaz."""
        kep = np.full((2, 2, 3), 64, dtype=np.uint8)
        mac = int(apply_display_mode(kep, "mac")[0, 0, 0])
        lin = int(apply_display_mode(kep, "linear")[0, 0, 0])
        assert lin > mac > 64
