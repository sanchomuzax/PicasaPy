"""#1878 — a lefedettségi mérő nem hiheti el a SAJÁT kimenetét.

## A hibaosztály

A `menu_lefedettseg.py` a `docs/specs/*.md` lapjait olvassa **bizonyítékként**:
ha egy parancs viselkedése le van írva valamelyikben, „feltárt". Csakhogy a
`docs/specs/` alatt **generált jelentések** is vannak. Ha egy ilyen lap
felsorolja a parancsneveket, a mérő a saját (vagy egy testvér-eszköz)
kimenetét hiszi el — és a szám **némán 100%-ra ugorhat**.

⚠️ **Ez nem elméleti.** A testvér-mérőn (UI-lefedettség) lemérve: a naiv
névgrep 49 elemből **49 találatot** adott, amiből **31 hamis pozitív** —
mind körkörösségből, mert a generált `ui-lefedettseg.md` mind a 2020
elemnevet felsorolja.

A menü-mérőn ma **nem** okoz hibát: a két generált lap (`ui-lefedettseg.md`
és `lanc-szakadasok-leltar.md`) egyikében sincs `ID_*` token. **De ez
szerencse, nem szerkezet** — ezért kizárás, és ezért ez az őr.

## A foga

A mutáció egy ÁLGENERÁLT lap, ami minden parancsnevet felsorol. Kizárás
nélkül ettől a lefedettség 100%-ra ugrana, tehát a teszt bukik — ez a
próba dönti el, hogy a szabály él-e, vagy csak papíron van.
"""

from __future__ import annotations

import sys

import pytest

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[2]))

from scripts import menu_lefedettseg as ml  # noqa: E402


class TestAFelismeres:
    @pytest.mark.parametrize(
        "fejlec",
        [
            "# Cím\n\n**Generálva:** 2026-08-15 — ezt a fájlt ne írd kézzel.",
            "# Cím\n*A mérést a `kepesseg_or.py` végzi; az alábbi szakasz generált.*",
            "# Cím\n\nGENERÁLT — ne szerkeszd.",
        ],
    )
    def test_a_fejlecben_kimondott_jelolest_felismeri(self, fejlec):
        assert ml._generalt(fejlec)

    def test_a_PROZAT_nem_veszi_jelolesnek(self):
        """MÉRVE: a »generál« szótő a teljes szövegben 14 lapra illeszkedik,
        mert a próza is használja. A fejlécre szűkítve 2, hamis pozitív
        nélkül."""
        proza = (
            "# Keresési módok\n\n"
            "Egy hosszabb bevezető.\n\n"
            "…ellentétben a Picasa saját generált névszűrőivel, amelyek…\n"
        )
        assert not ml._generalt(proza)

    def test_az_ures_lap_nem_generalt(self):
        assert not ml._generalt("")


class TestAKizarasELO:
    def test_a_ket_ismert_generalt_lap_kimarad(self):
        nevek = set(ml._lapok())
        assert "ui-lefedettseg.md" not in nevek
        assert "lanc-szakadasok-leltar.md" not in nevek

    def test_a_kezi_lapok_BENNMARADNAK(self):
        """A kizárás nem söpörheti ki a valódi bizonyítékot."""
        nevek = set(ml._lapok())
        assert "picasa-menu-parancsok-viselkedes.md" in nevek
        assert "picasa-megjelenitesi-modok.md" in nevek
        assert len(nevek) > 50

    def test_a_meres_nem_valtozott_a_kizarastol(self):
        """A mai 138/138 nem a generált lapokon állt."""
        m = ml.merd()
        assert m["sehol"] == [] and m["csak_nev"] == []
        assert len(m["viselkedes"]) == 138


class TestAFog:
    """A döntő próba: a kizárás NÉLKÜL a szám tényleg hazudna-e?

    Az „a felismerés működik" önmagában kevés — azt kell megmutatni, hogy
    a kizárás **változtat az EREDMÉNYEN**. Ezért a mérést kétszer futtatjuk
    ugyanazon a szintetikus fán: kizárással és anélkül.
    """

    @pytest.fixture
    def alfa_specdir(self, tmp_path):
        """Szintetikus `docs/specs`: EGYETLEN álgenerált jelentés, ami
        minden parancsnevet felsorol — és semmi valódi feltárás."""
        parancsok = ml.merd()["osszes"]
        cel = tmp_path / "specs"
        cel.mkdir()
        (cel / "gepi-jelentes.md").write_text(
            "# Gépi jelentés\n\n**Generálva:** ma — ne szerkeszd.\n\n"
            + "\n".join(f"- `{p}`" for p in parancsok),
            encoding="utf-8",
        )
        return cel, parancsok

    def test_kizarassal_a_algeneralt_lap_NEM_bizonyitek(
        self, alfa_specdir, monkeypatch
    ):
        cel, parancsok = alfa_specdir
        monkeypatch.setattr(ml, "SPEC_DIR", cel)
        monkeypatch.setattr(ml, "VISELKEDES_LAP", "nincs-ilyen.md")
        m = ml.merd()
        assert m["viselkedes"] == [], "az álgenerált lapot bizonyítéknak vettük"
        assert len(m["sehol"]) == len(parancsok) - len(m["hatokoron_kivul"])

    def test_kizaras_NELKUL_ugyanaz_a_lap_bizonyiteknak_latszana(
        self, alfa_specdir, monkeypatch
    ):
        """Ez mutatja meg, hogy a szabály nem papíron van.

        A `_generalt`-ot letiltva ugyanaz a fa MINDEN parancsot
        „feltártnak" jelentene — egyetlen valódi feltárás nélkül."""
        cel, parancsok = alfa_specdir
        monkeypatch.setattr(ml, "SPEC_DIR", cel)
        monkeypatch.setattr(ml, "VISELKEDES_LAP", "nincs-ilyen.md")
        monkeypatch.setattr(ml, "_generalt", lambda _szoveg: False)
        m = ml.merd()
        assert m["sehol"] == [], "a kizárás nélkül is »sehol« maradt — a próba nem mér"
        assert m["erdemi"], "kizárás nélkül a lapnak bizonyítéknak KELL látszania"
