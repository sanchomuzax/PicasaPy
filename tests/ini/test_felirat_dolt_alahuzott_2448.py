"""#2448: a felirat dőlt/aláhúzott állapota a `text=` 9. mezőjében.

Eddig **megrajzoltuk, de nem mentettük**: a rajzoló ismeri az `italic` és
`underline` paramétert, a `.picasa.ini`-be viszont mindig `0xC000` ment ki,
mintha egyik sem volna bekapcsolva. Újranyitáskor elveszett; és fordítva, az
eredeti Picasával készített `0xC001`/`0xC008` sorokat sem értelmeztük.

## A két bit — a binárisból

| bit | maszk | jelentés | cím |
|---:|---:|---|---|
| 0 | `0x0001` | aláhúzott | `0x0062ebb3`–`0x0062ebb9` |
| 3 | `0x0008` | dőlt | `0x005ba7b0` + `0x0062ea5c` |

## ⚠️ A többi bitet NEM építjük újra

A `0x4000` és a `0x8000` jelentése **nincs feltárva**. A `with_style_flags`
ezért a beolvasott mezőt őrzi meg, és csak a két ismert bitet állítja —
egy újraépített mező némán elvinné azt, amit nem is értünk.
"""

from __future__ import annotations

import pytest

from picasapy.ini.text_overlay import TextStyle


def _stilus(*, trailer: int) -> TextStyle:
    """A kötelező szín-mezőket a korpusz tipikus értékeivel tölti ki —
    a vizsgált mező a 9., a színek itt közömbösek."""
    return TextStyle(fill_argb=0xFFFFFFFF, outline_argb=0xFF000000, trailer=trailer)


class TestABitekOlvasasa:
    @pytest.mark.parametrize(
        ("trailer", "dolt", "alahuzott"),
        [
            (0xC000, False, False),   # a korpusz leggyakoribb alakja
            (0xC001, False, True),    # aláhúzott
            (0xC008, True, False),    # dőlt
            (0xC009, True, True),     # MINDKETTŐ — ilyen a korpuszban nincs
        ],
    )
    def test_az_ismert_bitek(self, trailer, dolt, alahuzott):
        stilus = _stilus(trailer=trailer)
        assert stilus.italic is dolt
        assert stilus.underline is alahuzott


class TestATobbiBitMEGMARAD:
    """A lényeg: amit nem értünk, azt nem dobjuk el."""

    def test_a_0x4000_es_a_0x8000_atmegy(self):
        eredeti = _stilus(trailer=0xC000)
        uj = eredeti.with_style_flags(italic=True, underline=True)
        assert uj.trailer & 0xC000 == 0xC000, (
            f"a fel nem tárt bitek elvesztek: {uj.trailer:#06x}"
        )
        assert uj.trailer == 0xC009

    def test_egy_ISMERETLEN_bit_is_atmegy(self):
        """Nem csak a 0x4000/0x8000 — bármelyik, amit nem ismerünk."""
        eredeti = _stilus(trailer=0xC000 | 0x0040)
        uj = eredeti.with_style_flags(italic=False, underline=False)
        assert uj.trailer & 0x0040, "a 0x40-es bit elveszett"

    def test_a_KIKAPCSOLAS_is_csak_a_ket_bitet_erinti(self):
        eredeti = _stilus(trailer=0xC009)
        uj = eredeti.with_style_flags(italic=False, underline=False)
        assert uj.trailer == 0xC000

    def test_ujraepites_ESETEN_bukna(self):
        """A teszt fogát mutatja: ha a mezőt a két bitből ÉPÍTENÉNK újra,
        a `0xC000` eltűnne, és ez az állítás elbukna."""
        uj = _stilus(trailer=0xC008).with_style_flags(
            italic=True, underline=False
        )
        assert uj.trailer != 0x0008, (
            "a mező újraépült a két bitből — a fel nem tárt bitek elvesztek"
        )


class TestRoundTrip:
    @pytest.mark.parametrize("trailer", [0xC000, 0xC001, 0xC008, 0xC009])
    def test_a_beallitas_utan_ugyanaz_jon_vissza(self, trailer):
        eredeti = _stilus(trailer=trailer)
        uj = eredeti.with_style_flags(
            italic=eredeti.italic, underline=eredeti.underline
        )
        assert uj.trailer == trailer, (
            "a saját értékek visszaírása megváltoztatta a mezőt"
        )
