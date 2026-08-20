r"""A kollázs fájlnevének tisztítása — DOS-eszköznevek (#969).

A kollázs neve a **forrásmappa vagy az album címéből** jön, tehát a
felhasználótól. Windows máig lefoglalja a DOS-kori eszközneveket (`aux`,
`con`, `nul`, `prn`, `com1`…, `lpt1`…): ilyen nevű fájl **nem hozható
létre**, kiterjesztéssel sem. Egy „AUX" nevű album mentése enélkül némán
elbukna a tulajdonos gépén — ő Windowson használja a programot.

⚠️ **Ez a MI védőágunk, nem az eredeti mért viselkedése.** Hogy a Picasa
mit tesz ilyen címmel, nincs kimérve; a szabály célja csak annyi, hogy a
mentés ne bukjon el. A `.picasa.ini`-hez hasonlóan: ha valaha lemérjük,
ez felülírandó.

A jegy többi pontja (célmappa, számozás, `.cxf`-pár, q90, atomi írás)
**már készen volt** — a kódot tételesen átnéztem, ezért ez a kör csak a
hiányzó tételt szállítja.
"""

from __future__ import annotations

import pytest

from picasapy.app.collage_output import FILENAME_STEM, safe_stem


class TestAzEszkoznevekVedve:
    @pytest.mark.parametrize(
        "cim", ["aux", "AUX", "con", "CON", "nul", "prn", "com1", "LPT9"]
    )
    def test_alahuzas_kerul_a_vegere(self, cim):
        eredmeny = safe_stem(cim)

        assert eredmeny == f"{cim}_"

    def test_kiterjesztessel_is_foglalt(self):
        """`aux.jpg` ugyanúgy tilos — a vizsgálat az ELSŐ pontig tart."""
        assert safe_stem("nul.txt") == "nul.txt_"

    @pytest.mark.parametrize("cim", ["auxiliary", "console", "printer", "communism"])
    def test_a_hosszabb_szo_ERINTETLEN(self, cim):
        """Csak a PONTOS név foglalt — az „auxiliary" rendes fájlnév."""
        assert safe_stem(cim) == cim


class TestAmiEddigIsMukodott:
    """Kontroll: a jegy többi névtisztítási szabálya változatlan."""

    def test_a_szelso_szokoz_es_pont_lekerul(self):
        assert safe_stem("  szélső szóköz  ") == "szélső szóköz"
        assert safe_stem("pont...") == "pont"

    def test_az_elvalasztok_kiesnek(self):
        assert safe_stem(r"a/b\c:d") == "abcd"

    @pytest.mark.parametrize("cim", ["", "   ", "...", None])
    def test_ures_cimre_a_tartalek(self, cim):
        assert safe_stem(cim) == FILENAME_STEM

    def test_a_valodi_cim_valtozatlan(self):
        """A tulajdonos NAS-áról: a forrásmappa címe megy ki névnek."""
        assert safe_stem("2010-08-01 Sátor alkatrész") == "2010-08-01 Sátor alkatrész"
