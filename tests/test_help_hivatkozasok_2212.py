"""#2212 — a súgó Markdown-hivatkozásainak feloldása.

A nyitólap a súgó tartalomjegyzéke: csupa relatív hivatkozás. Ha ezek nem
oldódnak fel fejezetnévvé, a felhasználó a súgó fő navigációs felületét
látja működésképtelenül.

A feloldás a **hivatkozó fejezethez képest** relatív — a `features/`
alatti lapokról a `../index.md` a gyökérbe kell mutasson.
"""

from __future__ import annotations

import re

import pytest

from picasapy.help_content import (
    FOOLDAL,
    fejezetek,
    fejezet_szovege,
    hivatkozas_celja,
)


class TestAFooldalMindenHivatkozasaMukodik:
    """A felhasználó ezt látja elsőként — itt egy törött link is sok."""

    def test_a_fooldal_minden_hivatkozasa_letezo_fejezetre_mutat(self):
        szoveg = fejezet_szovege(FOOLDAL) or ""
        celok = re.findall(r"\[[^\]]*\]\(([^)]+)\)", szoveg)
        assert celok, "a nyitólapon nincs hivatkozás — elromlott a súgó?"
        ismert = set(fejezetek())
        for cel in celok:
            feloldott = hivatkozas_celja(FOOLDAL, cel)
            assert feloldott is not None, f"a nyitólap {cel!r} hivatkozása nem oldható fel"
            assert feloldott in ismert, f"{cel!r} → {feloldott!r} nincs a fejezetek közt"

    def test_a_sugo_MINDEN_lapjanak_minden_hivatkozasa_mukodik(self):
        """Nem csak a nyitólap: a fejezetek egymásra is hivatkoznak."""
        ismert = set(fejezetek())
        hibak = []
        for nev in ismert:
            szoveg = fejezet_szovege(nev) or ""
            for cel in re.findall(r"\[[^\]]*\]\(([^)]+)\)", szoveg):
                feloldott = hivatkozas_celja(nev, cel)
                if feloldott is None or feloldott not in ismert:
                    hibak.append(f"{nev} → {cel}")
        assert not hibak, "törött hivatkozások: " + ", ".join(hibak)


class TestAFeloldasRelativ:
    def test_a_gyokerbol_almappaba(self):
        assert (
            hivatkozas_celja("index.md", "features/konyvtar.md")
            == "features/konyvtar.md"
        )

    def test_az_almappabol_a_gyokerbe(self):
        assert hivatkozas_celja("features/konyvtar.md", "../index.md") == "index.md"

    def test_az_almappan_belul(self):
        assert (
            hivatkozas_celja("features/konyvtar.md", "kereses.md")
            == "features/kereses.md"
        )

    def test_a_horgony_reszt_levagja(self):
        """`konyvtar.md#szakasz` — a fejezet akkor is megnyílik."""
        assert (
            hivatkozas_celja("index.md", "features/konyvtar.md#albumok")
            == "features/konyvtar.md"
        )


class TestAmiNEM_nyilhatMeg:
    """A cél a felületről jön, tehát nem megbízható bemenet."""

    @pytest.mark.parametrize(
        "cel",
        [
            "../../../etc/passwd",
            "../../pyproject.toml",
            "/etc/passwd",
        ],
    )
    def test_a_sugo_mappajabol_nem_lehet_kilepni(self, cel):
        assert hivatkozas_celja("index.md", cel) is None

    @pytest.mark.parametrize(
        "cel",
        ["https://example.com", "http://example.com", "mailto:a@b.c"],
    )
    def test_a_kulso_hivatkozas_nem_fejezet(self, cel):
        """Ma nincs ilyen a súgóban (mérve: 0 db), de ha lesz, a feloldás
        NEM adhat rá fejezetnevet — a felület dolga eldönteni, mit tesz."""
        assert hivatkozas_celja("index.md", cel) is None

    def test_a_nem_letezo_fejezet_nem_nyilik(self):
        assert hivatkozas_celja("index.md", "nincs-ilyen.md") is None

    def test_az_ures_cel_nem_dol_el(self):
        assert hivatkozas_celja("index.md", "") is None
