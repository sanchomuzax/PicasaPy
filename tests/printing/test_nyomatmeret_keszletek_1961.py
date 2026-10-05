"""A nyomatméret-készlet nyelvfüggő: magyar felületen METRIKUS (#1961).

## A lelet

Magyar felületen hüvelykes nyomatméreteket kínáltunk (3,5×5 in, 4×6 in,
…). Egy magyar felhasználó tehát olyan méreteket látott, amilyeneket
magyar fotólaborban nem tud rendelni.

Az eredeti Picasa **tizenhét** nyomatméretet ismer
(`ytPrintSizes::` szövegcsalád, `stringres` 3478–3494), és a magyar
felületen metrikus méreteket mutat. A tulajdonos felvételén
(`#1953-nyomtatas-kep-kicsi.jpg`) a #4257 előtti hat tétel látszik:

    5x8 cm · 9x13 cm · 10x15 cm · 13x18 cm · 20x25 cm · Teljes oldal

⚠️ **NINCS mérve**, hogy MI választja ki a listát — a nyelv, a területi
beállítás vagy a nyomtató papírmérete. Nálunk a **felület nyelve** dönt;
ez a mi döntésünk, nem az eredeti másolása. A #4257 a mért 15×20 cm-es
méretet az eredeti helyére illeszti; a CD-borító pontos méretét a spec
nem adja meg, ezért az kimarad.

## Utólagos javítás (#3712-review)

A hüvelykes ötös **sorrendje és összetétele hibás volt**: a Tárca a lista
VÉGÉN állt, és a `TELJES_OLDAL` (Full Page) egyáltalán hiányzott belőle —
a `research/testdata/screenshot/Colab EN 29…`/`…30…` felvételek szerint
az eredeti hat gombja Wallet elöl, Full Page a végén sorrendben áll. A
metrikus összeállításának nincs Tárca-tagja. A #4257 új méretekkel
bővített listái ettől függetlenek: a hüvelykes készlet két mért elemmel,
a metrikus egy tétellel bővül.
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
    def test_a_metrikus_meretek_az_eredeti_sorrendben(self):
        assert [m.name for m in METRIKUS_KESZLET] == [
            "M5X8CM", "M9X13CM", "M10X15CM", "M13X18CM", "M15X20CM",
            "M20X25CM", "TELJES_OLDAL",
        ]

    def test_a_huvelykes_meretek_az_eredeti_sorrendben(self):
        """#3712-review: a korábbi ötös (Tárca a végén, Full Page nélkül)
        NEM egyezett a `printpanel.tre` mért sorrendjével. A Tárca továbbra
        is elöl áll; a 3×4 és 4×5 a specifikáció szerinti helyre került."""
        assert [m.name for m in HUVELYK_KESZLET] == [
            "TARCA", "M3X4", "M3_5X5", "M4X5", "M4X6", "M5X7",
            "M8X10", "TELJES_OLDAL",
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
        ("M15X20CM", 15, 20),
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


class TestA4257HianyzoMeretei:
    def test_a_huvelykes_meretek_a_mert_oldalhosszal(self):
        assert (
            NyomatMeret.M3X4.szeles_huvelyk,
            NyomatMeret.M3X4.magas_huvelyk,
        ) == (3.0, 4.0)
        assert (
            NyomatMeret.M4X5.szeles_huvelyk,
            NyomatMeret.M4X5.magas_huvelyk,
        ) == (4.0, 5.0)

    def test_a_cd_borito_merete_nincs_becsulve(self):
        # A specifikáció csak a közös centiméteres ágra sorolja az eCDSize-t;
        # hozzá tartozó méretadatot nem közöl.
        assert all("CD" not in nev.upper() for nev in NyomatMeret.__members__)


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
