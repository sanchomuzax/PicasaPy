"""#1778 — az állapotlap „következő öt” forrása az UI-lefedettségre vált.

**Miért.** A menüparancs-axis 2026-08-31-én kimerült: 138/138, tehát a
`kovetkezo_ot()` üres listát ad, és a lap szakasza üresen jelent meg.

**A KÉT axis másképp rendez.** A menü-sor ábécésorrend volt („bárki
futtatja, ugyanazt kapja”); az UI-sor a fehér foltok MÉRETE szerint
csökkenő. Mindkettő determinisztikus, de MÁST ígér — ezért a lap szövege
is más, és ezt a teszt őrzi.

**A hatókör-szűrő nem kényelmi.** Szűrő nélkül a rangsor 7–8. helyén álló
`upload` és `buzzupload` — mindkettő megszűnt Google-szolgáltatás — a
második ötösben már kutatói kört kapna.
"""

from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

import ui_lefedettseg_lap as ul  # noqa: E402

_MINTA = """\
# UI-lefedettség

**Generálva:** 2026-08-31 — ezt a fájlt ne írd kézzel.

## Összesítés

| mutató | darab |
|---|---:|
| párosítva | 135 |
| hiányzik | 396 |
| bizonytalan | 158 |

## Rangsor — a tíz legnagyobb fehér folt

| # | panel | hiány + bizonytalan | mit takar |
|---:|---|---:|---|
| 1 | `editpanel` | 83 | A szerkesztő bal oldali panelje |
| 2 | `thumbui` | 41 | A fő könyvtárnézet |
| 3 | `upload` | 21 | Picasa Web Albums feltöltő |
| 4 | `buzzupload` | 21 | Google Buzz feltöltés |
| 5 | `printpanel` | 26 | Nyomtatási panel |
| 6 | `compose_share` | 16 | Megosztási meghívó |
| 7 | `quicktagconfig` | 13 | Gyorscímke-beállító |
"""


@pytest.fixture
def meres(tmp_path: Path):
    ut = tmp_path / "ui-lefedettseg.md"
    ut.write_text(_MINTA, encoding="utf-8")
    return ul.olvas(ut)


class TestABeolvasas:
    def test_a_meres_datumat_kiolvassa(self, meres):
        assert meres.ideje == date(2026, 8, 31)

    def test_a_rangsort_kiolvassa(self, meres):
        assert [p.nev for p in meres.rangsor][:2] == ["editpanel", "thumbui"]
        assert meres.rangsor[0].hiany == 83

    def test_az_osszesito_szamait_kiolvassa(self, meres):
        assert (meres.parositva, meres.hianyzik, meres.bizonytalan) == (
            135, 396, 158
        )

    def test_hianyzo_fajlbol_None(self, tmp_path: Path):
        assert ul.olvas(tmp_path / "nincs.md") is None


class TestAHatokorSzuro:
    def test_a_megszunt_szolgaltatasok_kimaradnak(self, meres):
        nevek = [p.nev for p in meres.kovetkezo_ot]
        assert "upload" not in nevek
        assert "buzzupload" not in nevek
        assert "compose_share" not in nevek

    def test_a_helyukre_a_kovetkezok_lepnek(self, meres):
        """Nem rövidül a lista — feljebb lépnek a következők."""
        assert [p.nev for p in meres.kovetkezo_ot] == [
            "editpanel", "thumbui", "printpanel", "quicktagconfig"
        ]

    def test_a_kihagyottakat_KIMONDJA(self, meres):
        """A kihagyás ne látsszon feledékenységnek."""
        nevek = [n for n, _ in meres.kihagyott]
        assert nevek == ["upload", "buzzupload", "compose_share"]
        for _nev, indok in meres.kihagyott:
            assert "megszűnt" in indok, "az indok mondja meg, MIÉRT"

    def test_a_szuro_szandekosan_szuk(self):
        """Csak megszűnt szolgáltatás kerülhet ide — ne legyen belőle
        „ami nehéznek látszik” lista."""
        assert len(ul.HATOKORON_KIVUL) <= 5
        for indok in ul.HATOKORON_KIVUL.values():
            assert "megszűnt" in indok


class TestAzElavulas:
    def test_a_friss_meres_nem_elavult(self, meres):
        assert not meres.elavult(date(2026, 9, 5))

    def test_a_regi_meres_elavult(self, meres):
        assert meres.elavult(date(2026, 11, 1))

    def test_a_datum_nelkuli_meres_elavultnak_szamit(self, tmp_path: Path):
        ut = tmp_path / "x.md"
        ut.write_text("# nincs dátum\n", encoding="utf-8")
        assert ul.olvas(ut).elavult(date(2026, 9, 1))


class TestALapSzovege:
    """A szakasz szövege KÖVESSE, hogy melyik axis van soron."""

    @staticmethod
    def _lap():
        import allapotlap

        return allapotlap

    def test_a_menu_axis_szovege_abecerendet_iger(self):
        szoveg = self._lap()._kovetkezo_bevezeto(
            {"kovetkezo": ["ID_VALAMI"], "ui": None}
        )
        assert "Determinisztikus sorrend" in szoveg

    def test_az_ui_axis_szovege_MERETET_iger(self, meres):
        szoveg = self._lap()._kovetkezo_bevezeto(
            {"kovetkezo": [], "ui": meres}
        )
        assert "méret szerint" in szoveg
        assert "Determinisztikus sorrend" not in szoveg, (
            "az UI-sor nem ábécé — a régi ígéret félrevezetne"
        )

    def test_a_szam_JELOLTKENT_jelenik_meg_nem_iteletkent(self, meres):
        """Két egymást követő kör talált téves riasztást; ha a lap
        magyarázat nélkül ír ki 396 hiányt, rosszabb képet fest a
        valóságnál."""
        szoveg = self._lap()._kovetkezo_bevezeto(
            {"kovetkezo": [], "ui": meres}
        )
        assert "jelölt" in szoveg
        assert "nem megállapított hiány" in szoveg

    def test_a_felulbiralasok_szama_is_latszik(self, meres):
        """Enélkül a csökkenés a mérce lazulásának látszana."""
        szoveg = self._lap()._kovetkezo_bevezeto(
            {"kovetkezo": [], "ui": meres}
        )
        assert str(meres.felulbiralasok) in szoveg

    def test_a_meres_datuma_kimondva(self, meres):
        szoveg = self._lap()._kovetkezo_bevezeto(
            {"kovetkezo": [], "ui": meres}
        )
        assert "2026. 08. 31" in szoveg
