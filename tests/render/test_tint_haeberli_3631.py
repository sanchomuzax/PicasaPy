"""#3631 — a `Tint` (`TintImageOperation`) Haeberli-szürkével és a natív
`0x00bce2f0` táblájával színez, NEM Rec.601-es illesztett képlettel.

A #878-as golden-illesztés Rec.601-súlyokkal és folytonos, per-képpont
gamut-kompenzációval közelítette a `Tint`-et. A `docs/specs/
filterdesc-registry.md` „H) A `Tint` belseje" szakasza (2026-09-26, #626)
utasításszinten olvasta ki a natívot: a szürkítés Haeberli-súlyú
`ColorMatrix(s=-100)`, a színezés pedig egy 256 elemű, SZÍN SZERINT épített
tábla (`Resaturate`), amelyet a szürke érték (a bemenet Haeberli-lumája)
indexel. Szürke rámpán mérve a Rec.601-es modell telített kéknél/sárgánál
(`0x0000ff`, `0xffff00`) akár 71 szinttel tért el az emulált táblától — ez
a jegy lelete.

⚠️ **Amit ez a fájl NEM tud igazolni:** a `docs/specs/…` „Kész, ha" pontja
bitre egyező, 256 szintes táblát kér az emulátorból
(`~/picasapy-agent/eszkozok/nativ_emu/tint_lut.py`) legalább nyolc színre.
Ez a munkamenet a privát `picasapy-agent` repót NEM éri el (a feladatleírás
szerint), ezért a lenti tesztek a `docs/specs/filterdesc-registry.md`
szövegéből LEVEZETETT algoritmust ellenőrzik — a golden párból MÉRT
számhármasokkal (`test_neon_878.py`, `test_picniktint_884.py`) és a súlyok
mutáció-érzékenységével, nem a bitre egyező emulált táblával. A hiányzó
lépést a #3631 jegykommentje rögzíti.
"""

from __future__ import annotations

import numpy as np
import pytest

from picasapy.render.glimmer_ops import (
    _HAEBERLI_WEIGHTS,
    _haeberli_luma,
    _resaturate_color_luma,
    _resaturate_table,
    _resaturate_table_entry,
    tint_luma_preserving,
)

#: A „Kész, ha" nyolc színe: köztük a két korábban 71 szintig eltérő
#: telített szín (`0x0000ff`, `0xffff00`), a #878/#884 goldenjének színe
#: (`0x80cfff`), a `CrossProcess` sárgája (`0xfcff00`), a `Resaturate`
#: alapszíne (`0xddc9ae`), a Ghoul Eye zöldje (`0xc2ff9e`), egy neutrális
#: szürke és egy sötét kék-lila kontrollszín.
SZINEK: tuple[tuple[int, int, int], ...] = (
    (0x80, 0xCF, 0xFF),
    (0xFC, 0xFF, 0x00),
    (0x00, 0x00, 0xFF),
    (0xFF, 0xFF, 0x00),
    (0x80, 0x80, 0x80),
    (0xDD, 0xC9, 0xAE),
    (0xC2, 0xFF, 0x9E),
    (0x20, 0x20, 0x60),
)


def _flat(value: int, height: int = 4, width: int = 4) -> np.ndarray:
    return np.full((height, width, 3), value, dtype=np.uint8)


class TestATablaEgyszerEpul:
    """1. Kész-ha pont: a tábla szín szerint EGYSZER épül, és a
    `tint_luma_preserving` csak a szürke érték szerint indexel bele."""

    @pytest.mark.parametrize("szin", SZINEK)
    def test_a_tabla_256_sora_van(self, szin):
        tabla = _resaturate_table(szin)
        assert tabla.shape == (256, 3)
        assert tabla.dtype == np.uint8

    @pytest.mark.parametrize("szin", SZINEK)
    @pytest.mark.parametrize("szurke", [0, 1, 16, 64, 128, 200, 254, 255])
    def test_egyenletes_kepen_a_tabla_sorat_adja(self, szin, szurke):
        """Egyenletes szürke bemeneten a Haeberli-luma PONTOSAN a bemeneti
        érték, tehát az index nem kerekítési kérdés — a `tint_luma_
        preserving` kimenetének bitre egyeznie kell a tábla sorával."""
        tabla = _resaturate_table(szin)
        eredmeny = tint_luma_preserving(_flat(szurke), szin)[0, 0]
        np.testing.assert_array_equal(eredmeny, tabla[szurke])

    def test_a_tabla_gyorsitotarat_hasznal(self):
        """Ugyanaz a szín (más tuple-példány) ugyanazt a táblát adja —
        a `functools.lru_cache` a szín szerint kulcsol, nem hívásonként épít."""
        elso = _resaturate_table((10, 20, 30))
        masodik = _resaturate_table((10, 20, 30))
        assert elso is masodik


class TestHaeberliSzurkites:
    """A szürkítés Haeberli-súlyú, NEM Rec.601 (`docs/specs/…` H/2.1)."""

    def test_neutralis_szurke_szin_azonossagot_ad(self):
        """`0x808080`-nak nincs krómája: a tábla minden sora `(i, i, i)`,
        vagyis a szürkítés maga a bemenet — ez a legegyszerűbb bizonyíték,
        hogy a szürkítés a Haeberli-lumát adja vissza torzítás nélkül."""
        tabla = _resaturate_table((0x80, 0x80, 0x80))
        for i in (0, 1, 16, 128, 200, 254, 255):
            assert tuple(int(c) for c in tabla[i]) == (i, i, i)

    def test_a_szurkites_sulyai_haeberli(self):
        assert _HAEBERLI_WEIGHTS == pytest.approx((0.3086, 0.6094, 0.0820))
        assert sum(_HAEBERLI_WEIGHTS) == pytest.approx(1.0)

    def test_a_haeberli_luma_es_a_rec601_luma_kulonbozik(self):
        """Egy telített, nem-szürke pixelen a két luma ELTÉR — ha
        egyeznének, a #3631 lelete (71 szintes eltérés) nem létezne."""
        pixel = np.array([[[0, 255, 0]]], dtype=np.float32)  # telített zöld
        rec601 = 0.299 * 0 + 0.587 * 255 + 0.114 * 0
        haeberli = float(_haeberli_luma(pixel)[0, 0])
        assert abs(haeberli - rec601) > 5.0


class TestMertGoldenHarmasok:
    """A #878/#884 golden párjából mért, `test_neon_878.py`-ban is
    rögzített számhármasok — ugyanaz a mérce, most a Haeberli-modellel."""

    @pytest.mark.parametrize(
        ("ertek", "vart"),
        [(16, (0, 16, 65)), (128, (69, 147, 195)), (248, (231, 255, 255))],
    )
    def test_picniktint_alap_szinen(self, ertek, vart):
        eredmeny = tint_luma_preserving(_flat(ertek), (0x80, 0xCF, 0xFF))[0, 0]
        assert np.allclose(eredmeny, vart, atol=3), f"{tuple(int(c) for c in eredmeny)} != {vart}"


class TestRontasKontroll:
    """3. Kész-ha pont (#139): a Haeberli-súlyok rontását el kell kapnia.

    ⚠️ Egy VALÓDI elgépelés (az utolsó tizedesjegy, `0,3086 → 0,3087`) 8
    bites képpontszinten `0,0001·255 ≈ 0,026` szintnyi hatással jár — ez a
    kerekítési zaj alatt van, tehát MEGBÍZHATATLANUL kapható el pixelre
    mérve. Ezért a lenti két teszt két, egyre durvább, de még mindig
    reális rontást mér: (1) EGYETLEN súly századnyi (`0,01`) elcsúszása a
    RÁ dominánsan érzékeny (tiszta primer) színen, (2) a teljes visszaállás
    Rec.601-re — ez a #3631 tényleges lelete, és a szürke rámpán a
    dokumentált (legfeljebb 71 szintes) nagyságrendet kell hoznia."""

    @staticmethod
    def _tabla_sulyokkal(szin: tuple[int, int, int], sulyok: tuple[float, float, float]) -> np.ndarray:
        """A `_resaturate_table_entry`/`_resaturate_color_luma` átjátszása
        MÁS súlyokkal — fehér doboz, hogy a rontás valóban a súlyt érje,
        ne a hívó kódot."""
        import picasapy.render.glimmer_ops as glimmer_ops

        eredeti = glimmer_ops._HAEBERLI_WEIGHTS
        glimmer_ops._HAEBERLI_WEIGHTS = sulyok
        glimmer_ops._resaturate_table.cache_clear()
        try:
            return np.array(glimmer_ops._resaturate_table(szin))
        finally:
            glimmer_ops._HAEBERLI_WEIGHTS = eredeti
            glimmer_ops._resaturate_table.cache_clear()

    @pytest.mark.parametrize(
        ("csatorna_index", "domi_szin"),
        [(0, (0xFF, 0x00, 0x00)), (1, (0x00, 0xFF, 0x00)), (2, (0x00, 0x00, 0xFF))],
    )
    def test_egyetlen_suly_szazadnyi_rontasat_a_domi_szinen_elkapja(self, csatorna_index, domi_szin):
        """Tiszta piros/zöld/kék: a Haeberli-lumájukat KIZÁRÓLAG a saját
        csatornájuk súlya adja — ha épp ANNAK a súlynak a rontását nem a rá
        dominánsan érzékeny színen mérnénk, a rontás elbújhatna (ld. a
        `PROBA_SZIN` mutáció-érzékenységi elv, `tests/app/qml_functional/
        conftest.py`)."""
        rontott_sulyok = list(_HAEBERLI_WEIGHTS)
        rontott_sulyok[csatorna_index] += 0.01
        helyes = self._tabla_sulyokkal(domi_szin, _HAEBERLI_WEIGHTS)
        rontott = self._tabla_sulyokkal(domi_szin, tuple(rontott_sulyok))
        legnagyobb_elteres = int(np.abs(helyes.astype(np.int32) - rontott.astype(np.int32)).max())
        assert legnagyobb_elteres >= 2, (
            f"a {csatorna_index}. súly rontása nem hozott mérhető eltérést ({domi_szin}): "
            f"{legnagyobb_elteres} szint"
        )

    @pytest.mark.parametrize("szin", [(0x00, 0x00, 0xFF), (0xFF, 0xFF, 0x00)])
    def test_a_rec601_sulyokra_visszarontas_a_lelet_hibajat_adja(self, szin):
        """A legdurvább rontás: a Haeberli-súlyokat visszaírjuk Rec.601-re
        — ennek a #3631 lelete szerint a szürke rámpán TÖBB TÍZ szintes
        eltérést kell adnia a helyes táblához képest."""
        REC601 = (0.299, 0.587, 0.114)
        helyes = self._tabla_sulyokkal(szin, _HAEBERLI_WEIGHTS)
        rec601 = self._tabla_sulyokkal(szin, REC601)
        legnagyobb_eltmes = int(np.abs(helyes.astype(np.int32) - rec601.astype(np.int32)).max())
        assert legnagyobb_eltmes >= 20, (
            f"a Rec.601-súly nem reprodukálta a lelet nagyságrendjét ({szin}): {legnagyobb_eltmes} szint"
        )


class TestNemMutalEsTiszta:
    def test_nem_mutalja_a_bemenetet(self):
        kep = _flat(128)
        eredeti = kep.copy()
        tint_luma_preserving(kep, (0x80, 0xCF, 0xFF))
        np.testing.assert_array_equal(kep, eredeti)

    def test_a_tabla_csak_olvashato(self):
        """A gyorsítótárazott tábla NEM mutálható kívülről (`setflags`),
        különben egy hívó véletlenül eltorzíthatná a megosztott gyorstárat."""
        tabla = _resaturate_table((0x80, 0xCF, 0xFF))
        with pytest.raises(ValueError):
            tabla[0] = (1, 2, 3)


class TestTablaBejegyzes:
    """A `_resaturate_table_entry`/`_resaturate_color_luma` közvetlen
    fehér-doboz próbái — a `docs/specs/…` 3.1–3.5 lépéseinek megfelelően."""

    def test_lc_a_szin_haeberli_lumaja_kerekitve(self):
        # 0x808080: Haeberli-luma pontosan 128 (a súlyok összege 1)
        assert _resaturate_color_luma((0x80, 0x80, 0x80)) == 128

    def test_neutralis_szinnel_a_tabla_azonossag(self):
        for level in (0, 63, 128, 255):
            assert _resaturate_table_entry((0x80, 0x80, 0x80), level) == (level, level, level)

    def test_a_kimenet_mindig_0_255_kozott(self):
        for szin in SZINEK:
            for level in (0, 128, 255):
                entry = _resaturate_table_entry(szin, level)
                assert all(0 <= c <= 255 for c in entry), entry
