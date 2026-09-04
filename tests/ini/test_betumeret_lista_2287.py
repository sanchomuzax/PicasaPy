"""#2287 — a betűméret 16 abszolút értékből választható, `érték ÷ 360` tárolással.

**Az eredetiben nincs százalék.** A méretválasztó egy 16 elemű, abszolút
egész-lista, és a `.picasa.ini`-be írt szám a választott érték
**360-ad része** — a kép magassága a képletből kiesik.

A lista a `.data`-ból kiolvasva (két azonos példány, `0x00c7dab8` és
`0x00c7e4f0`, 16 × `int32`); az átváltás a `0x005b35a0`-ból utasításról
utasításra (`érték × magasság ÷ 360`, a `360.0` a `0xcf3d50`-en); az író
`méret ÷ magasság`-ot tárol (#2271) ⇒ **`tárolt = érték ÷ 360`**.

A kör három valódi exporton ellenőrizve: `0,033333 → 12`,
`0,061111 → 22`, `0,072222 → 26` — mindhárom szerepel a listában.
"""

from __future__ import annotations

import pytest

from picasapy.ini.text_overlay import (
    BETUMERETEK,
    DEFAULT_TEXT_SIZE,
    meret_taroltbol,
    tarolt_meret,
)


class TestALista:
    def test_a_tizenhat_ertek_a_binarisbol(self):
        assert BETUMERETEK == (
            8, 10, 12, 14, 16, 18, 20, 22, 26, 30, 36, 48, 60, 72, 84, 96
        )

    def test_az_alapertek_a_listaban_van(self):
        """A régi `0,1` × 360 = 36 véletlenül listaérték volt, de a
        vezérlőnk nem tudta előállítani — az alapérték az eredetiben 12."""
        assert DEFAULT_TEXT_SIZE == pytest.approx(12 / 360)


class TestAzAtvaltas:
    @pytest.mark.parametrize(
        "ertek,tarolt",
        [
            (8, 0.022222), (12, 0.033333), (22, 0.061111),
            (26, 0.072222), (36, 0.100000), (96, 0.266667),
        ],
    )
    def test_a_tarolt_ertek_a_lista_360_ad_resze(self, ertek, tarolt):
        assert tarolt_meret(ertek) == pytest.approx(tarolt, abs=5e-7)

    @pytest.mark.parametrize("ertek", BETUMERETEK)
    def test_oda_vissza(self, ertek):
        assert meret_taroltbol(tarolt_meret(ertek)) == ertek

    def test_a_harom_VALODI_export_visszaadja_a_listaerteket(self):
        """A tulajdonos mintáiból — ezek döntötték el a képletet."""
        for tarolt, vart in [(0.033333, 12), (0.061111, 22), (0.072222, 26)]:
            assert meret_taroltbol(tarolt) == vart

    def test_a_KEZZEL_meretezett_ertek_a_legkozelebbit_adja(self):
        """A fogantyúval átméretezett feliratok nem egész listaértékek —
        a választónak akkor is mutatnia kell valamit."""
        assert meret_taroltbol(0.051884) in BETUMERETEK  # 18,678 → 18 vagy 20
        assert meret_taroltbol(0.112358) in BETUMERETEK  # 40,449
