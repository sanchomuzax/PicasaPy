"""#1782 — a nyomat effektív felbontása és a „kicsi kép” figyelmeztetés.

## A lelet

> A felhasználó ma úgy nyomtathat ki egy 640×480-as képet 8×10 hüvelykre,
> hogy a program egy szót sem szól.

Az eredeti nyomtatási panel minőség-ellenőrzést végez: a választott
nyomatmérethez kiszámolja minden kép effektív felbontását, megszámolja a
túl kicsiket, és nyomtatás előtt ellenőrzésre szólít fel.

| szöveg | erőforrás |
|---|---|
| „Smallest picture: %d pixels/inch.” | `ThumbUIPrint::Smallest` |
| „%d small %s found.” + „Please review before printing.” | `ThumbUIPrint::ReviewPrompt` |
| „You are ready to print.” | — |

## ⚠️ A KÜSZÖB SAJÁT DÖNTÉS, nem mért érték

Hogy hány DPI alatt számít egy kép „kicsinek”, a binárisból **nincs
mérve**: a `0x00745980` a darabszámot paraméterként kapja, a küszöb a
hívóláncban van. A mechanizmust átvesszük, a küszöböt magunk választjuk —
és ezt a kód ki is mondja. A választás 150 DPI, a fotónyomtatás szokásos
alsó határa.
"""

from __future__ import annotations

import pytest

from picasapy.printing.dpi import (
    KICSI_KUSZOB_DPI,
    NyomatMeret,
    effektiv_dpi,
    minoseg_osszegzes,
)
from picasapy.printing.dpi import HUVELYK_KESZLET


class TestNyomatMeretek:
    def test_az_ot_mert_meret_megvan(self):
        """`0x00743700` / `0x00743980`: 3,5×5 · 4×6 · 5×7 · 8×10 + tárca.

        #1961: a felsorolás azóta a metrikus készletet is tartalmazza,
        ezért a HÜVELYKES készletre állítunk — az maradt ötös."""
        assert len(HUVELYK_KESZLET) == 5

    def test_minden_meretnek_van_hüvelykben_mert_oldala(self):
        for meret in NyomatMeret:
            assert meret.szeles_huvelyk > 0
            assert meret.magas_huvelyk > 0

    def test_a_tarcameret_a_legkisebb(self):
        """#1961: a HÜVELYKES készleten belül — a metrikus 5×8 cm
        (1,97 × 3,15 in) ennél kisebb, de az másik készlet."""
        legkisebb = min(
            HUVELYK_KESZLET, key=lambda m: m.szeles_huvelyk * m.magas_huvelyk
        )
        assert legkisebb is NyomatMeret.TARCA


class TestEffektivDpi:
    def test_a_hosszabb_oldalak_hanyadosa_dont(self):
        """A kép a nyomat területére illeszkedik: a szűkebb irány adja a
        felbontást, mert ott „nyúlik” a legjobban a képpont."""
        # 1200×1800 kép 4×6 hüvelykre: 1200/4 = 300 és 1800/6 = 300
        assert effektiv_dpi(1200, 1800, NyomatMeret.M4X6) == 300

    def test_a_rosszabbik_irany_dont(self):
        # 1200×900 kép 4×6-ra: a hosszabb kép-oldal a hosszabb nyomat-oldalra
        # kerül → 1200/6 = 200 és 900/4 = 225 → a kisebbik számít
        assert effektiv_dpi(1200, 900, NyomatMeret.M4X6) == 200

    def test_a_tajolas_nem_szamit(self):
        """Álló és fekvő kép ugyanazt adja — a nyomat elfordítható."""
        assert effektiv_dpi(1200, 900, NyomatMeret.M4X6) == effektiv_dpi(
            900, 1200, NyomatMeret.M4X6
        )

    def test_a_nagyobb_nyomat_kisebb_dpi_t_ad(self):
        kicsi = effektiv_dpi(1600, 1200, NyomatMeret.M3_5X5)
        nagy = effektiv_dpi(1600, 1200, NyomatMeret.M8X10)
        assert nagy < kicsi

    @pytest.mark.parametrize("szel,mag", [(0, 100), (100, 0), (-1, 10)])
    def test_ertelmetlen_meretre_nulla(self, szel: int, mag: int):
        """Hiányzó képméretből ne szülessen hamis megnyugtatás."""
        assert effektiv_dpi(szel, mag, NyomatMeret.M4X6) == 0


class TestMinosegOsszegzes:
    _NAGY = (4000, 3000)
    _KICSI = (640, 480)

    def test_csupa_nagy_kepre_keszen_all(self):
        osszegzes = minoseg_osszegzes([self._NAGY, self._NAGY], NyomatMeret.M4X6)
        assert osszegzes.kicsik == 0
        assert osszegzes.keszen_all is True

    def test_a_640x480_8x10_re_KICSI(self):
        """A jegy nyitómondata: ma erről egy szó sem esett."""
        osszegzes = minoseg_osszegzes([self._KICSI], NyomatMeret.M8X10)
        assert osszegzes.kicsik == 1
        assert osszegzes.keszen_all is False
        assert osszegzes.legkisebb_dpi < KICSI_KUSZOB_DPI

    def test_a_legkisebbet_jelenti_nem_az_atlagot(self):
        """`ThumbUIPrint::Smallest` — a kijelölés LEGROSSZABB képe."""
        osszegzes = minoseg_osszegzes(
            [self._NAGY, self._KICSI], NyomatMeret.M4X6
        )
        assert osszegzes.legkisebb_dpi == effektiv_dpi(
            *self._KICSI, NyomatMeret.M4X6
        )

    def test_a_darabszam_a_kuszob_alattiakat_szamolja(self):
        osszegzes = minoseg_osszegzes(
            [self._KICSI, self._KICSI, self._NAGY], NyomatMeret.M8X10
        )
        assert osszegzes.kicsik == 2
        assert osszegzes.osszes == 3

    def test_ures_kijelolesre_nem_allit_semmit(self):
        osszegzes = minoseg_osszegzes([], NyomatMeret.M4X6)
        assert osszegzes.osszes == 0
        assert osszegzes.legkisebb_dpi == 0
        assert osszegzes.keszen_all is False, (
            "üres kijelölésre ne mondja, hogy nyomtatásra kész"
        )

    def test_az_ismeretlen_meretu_kep_KICSINEK_szamit(self):
        """Ha nem tudjuk a képméretet, ne nyugtassuk meg a felhasználót."""
        osszegzes = minoseg_osszegzes([(0, 0)], NyomatMeret.M4X6)
        assert osszegzes.kicsik == 1
        assert osszegzes.keszen_all is False


class TestAKuszob:
    def test_kimondottan_sajat_dontes(self):
        """A jegy előírja: a küszöb egy helyen, névvel, és a komment
        mondja ki, hogy NEM mért érték."""
        from picasapy.printing import dpi

        assert KICSI_KUSZOB_DPI == 150
        # a sortörések összevonva: a docstring tördelése ne dönthesse el,
        # hogy az őr fog-e
        forras = " ".join((dpi.__doc__ or "").split())
        assert "nincs mérve" in forras, (
            "a modul docstringje nem mondja ki, hogy a küszöb NINCS MÉRVE"
        )
        assert "SAJÁT DÖNTÉS" in forras, (
            "a docstring nem mondja ki, hogy a küszöb a mi választásunk"
        )
