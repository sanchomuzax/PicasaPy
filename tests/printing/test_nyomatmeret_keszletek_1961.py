"""A nyomatméret-készlet nyelvfüggő: magyar felületen METRIKUS (#1961).

## A lelet

Magyar felületen hüvelykes nyomatméreteket kínáltunk (3,5×5 in, 4×6 in,
…). Egy magyar felhasználó tehát olyan méreteket látott, amilyeneket
magyar fotólaborban nem tud rendelni.

Az eredeti Picasa **tizenhét** nyomatméretet ismer
(`ytPrintSizes::` szövegcsalád, `stringres` 3478–3494), és a magyar
felületen a **metrikus hatost** mutatja. A tulajdonos felvételén
(`#1953-nyomtatas-kep-kicsi.jpg`) pontosan ez a hat csempe látszik:

    5x8 cm · 9x13 cm · 10x15 cm · 13x18 cm · 20x25 cm · Teljes oldal

⚠️ **NINCS mérve**, hogy MI választja ki a hatot — a nyelv, a területi
beállítás vagy a nyomtató papírmérete. Nálunk a **felület nyelve** dönt;
ez a mi döntésünk, nem az eredeti másolása, és a `dpi.py` egyetlen
helyén cserélhető, ha a mérés megszületik.

## Utólagos javítás (#3712-review)

A hüvelykes ötös **sorrendje és összetétele hibás volt**: a Tárca a lista
VÉGÉN állt, és a `TELJES_OLDAL` (Full Page) egyáltalán hiányzott belőle —
a `research/testdata/screenshot/Colab EN 29…`/`…30…` felvételek szerint
az eredeti hat gombja Wallet elöl, Full Page a végén sorrendben áll. A
metrikus hatos ÖSSZETÉTELE (nincs Tárca-tagja) ettől függetlenül MÉRT
viselkedés marad — a `printing/dpi.py` `METRIKUS_KESZLET` docsztringje
magyarázza, miért nem kap Tárcát.
"""

from __future__ import annotations

import pytest

from picasapy.printing.dpi import (
    HUVELYK_KESZLET,
    METRIKUS_KESZLET,
    NyomatMeret,
    keszlet_nyelvhez,
)


class TestAKetKeszlet:
    def test_a_metrikus_hatos_a_felvetel_szerint(self):
        assert [m.name for m in METRIKUS_KESZLET] == [
            "M5X8CM", "M9X13CM", "M10X15CM", "M13X18CM", "M20X25CM",
            "TELJES_OLDAL",
        ]

    def test_a_huvelykes_hatos_a_panel_gombsorrendjeben(self):
        """#3712-review: a korábbi ötös (Tárca a végén, Full Page nélkül)
        NEM egyezett a `printpanel.tre` hat gombjával — ld. a modul
        docsztringjét."""
        assert [m.name for m in HUVELYK_KESZLET] == [
            "TARCA", "M3_5X5", "M4X6", "M5X7", "M8X10", "TELJES_OLDAL",
        ]

    def test_a_gradualt_meretek_NEM_fedik_at_egymast(self):
        """A TARCA/M3_5X5/… és az M5X8CM/… sosem ugyanaz a fizikai méret —
        a `TELJES_OLDAL` viszont SZÁNDÉKOSAN közös tag (#3712-review): a
        Full Page mindkét nyelven ugyanaz az A4 lap, csak más felirattal."""
        gradualt_huvelykes = set(HUVELYK_KESZLET) - {NyomatMeret.TELJES_OLDAL}
        gradualt_metrikus = set(METRIKUS_KESZLET) - {NyomatMeret.TELJES_OLDAL}
        assert not gradualt_huvelykes & gradualt_metrikus

    def test_a_teljes_oldal_kozos_tagja_mindket_keszletnek(self):
        assert NyomatMeret.TELJES_OLDAL in HUVELYK_KESZLET
        assert NyomatMeret.TELJES_OLDAL in METRIKUS_KESZLET


class TestACentimeteresAtvaltas:
    #: (tag, cm-szélesség, cm-magasság) — a `ytPrintSizes::` feliratok
    ESETEK = (
        ("M5X8CM", 5, 8),
        ("M9X13CM", 9, 13),
        ("M10X15CM", 10, 15),
        ("M13X18CM", 13, 18),
        ("M20X25CM", 20, 25),
    )

    @pytest.mark.parametrize("nev,cm_szel,cm_mag", ESETEK)
    def test_a_huvelykertek_a_centimeterbol_jon(self, nev, cm_szel, cm_mag):
        """A foga: elgépelt hüvelyk-érték itt bukik, nem a felhasználónál."""
        tag = NyomatMeret[nev]
        assert tag.szeles_huvelyk == pytest.approx(cm_szel / 2.54, abs=1e-6)
        assert tag.magas_huvelyk == pytest.approx(cm_mag / 2.54, abs=1e-6)

    def test_a_teljes_oldal_A4(self):
        """DÖNTÉS: a „Teljes oldal" nálunk A4 (210 × 297 mm) — a metrikus
        készlet lapmérete. Az eredetiben a NYOMTATÓ papírja adja; ez a
        forrás egy helyén cserélhető."""
        tag = NyomatMeret.TELJES_OLDAL
        assert tag.szeles_huvelyk == pytest.approx(21.0 / 2.54, abs=1e-6)
        assert tag.magas_huvelyk == pytest.approx(29.7 / 2.54, abs=1e-6)


class TestAzUtlevelMeret:
    """#1401: `ePassport` — négyzet, és SZÁNDÉKOSAN egyik készletben sincs."""

    def test_negyzet_2x2_huvelyk(self):
        tag = NyomatMeret.PASSPORT
        assert tag.szeles_huvelyk == pytest.approx(2.0, abs=1e-9)
        assert tag.magas_huvelyk == pytest.approx(2.0, abs=1e-9)

    def test_nincs_a_huvelykes_keszletben(self):
        assert NyomatMeret.PASSPORT not in HUVELYK_KESZLET

    def test_nincs_a_metrikus_keszletben(self):
        assert NyomatMeret.PASSPORT not in METRIKUS_KESZLET


class TestANyelvValasztas:
    def test_magyarul_metrikus(self):
        assert keszlet_nyelvhez("hu") == METRIKUS_KESZLET

    def test_angolul_huvelykes(self):
        assert keszlet_nyelvhez("en") == HUVELYK_KESZLET

    def test_ismeretlen_nyelven_huvelykes(self):
        """Az alapértelmezés az angol (`DEFAULT_LANGUAGE`), tehát az
        ismeretlen kód se metrikusra váltson magától."""
        assert keszlet_nyelvhez("kl") == HUVELYK_KESZLET
        assert keszlet_nyelvhez("") == HUVELYK_KESZLET
        assert keszlet_nyelvhez(None) == HUVELYK_KESZLET
