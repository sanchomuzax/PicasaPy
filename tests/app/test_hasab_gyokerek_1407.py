"""#1407 (5., 6., 8. pont) — a bal hasáb GYÖKERE: négy menütétel, a
fejlécfelirat és a gyökér tartós tárolása.

## A mérés forrása

`docs/specs/picasa-mappanezet.md` 2.2, 4.2, 4.3, 4.5/b, 4.5/c és 4.6.

Két állítás, amit a spec **helyesbítésként** mond ki, és ez a próba
mindkettőt méri:

1. **Csak KÉT valódi gyökér van** (`flat` és `all`, plusz az `all`
   `watched`-re szűkített változata). A három rendszermappa-tétel
   (`mypics` / `mydocs` / `desktop`) **előbb a teljes fára vált**
   (`push "all"`), és csak utána oldja fel és jelöli ki a mappát
   (`0x005753b2`, `0x0057540b`, `0x00575461`).
2. **Hibaeset = visszaesés a Sajátgép-gyökérre**, nem hibaüzenet: ha a
   rendszermappa nem oldható fel, a natív kód önmagát hívja `"all"`
   gyökérrel (`0x005753bd`, `0x00575416`, `0x0057546c`). A `mypics` külön
   még a Dokumentumokra is visszaesik (`0x00996747 call 0x996230`).

⚠️ Amit ez a próba NEM mér: a `LastViewRoot` / `LastViewRoot2` kettéosztást
(Win32 registry-részlet, a spec 8. pontja szerint hatókörön kívül), és a
felirat képernyőn mért helyét — csak azt, hogy a vezérlő MELYIK szöveget
adja.
"""

from __future__ import annotations

import pytest
from PySide6.QtCore import QSettings

from picasapy.app import folder_hierarchy_controller as fhc
from picasapy.app.folder_hierarchy_controller import FolderHierarchyController


@pytest.fixture
def beallitasok(tmp_path, qt_app):
    settings = QSettings(str(tmp_path / "proba.ini"), QSettings.Format.IniFormat)
    yield settings
    settings.clear()


@pytest.fixture
def mappak(tmp_path, monkeypatch):
    """A három rendszermappa VALÓDI, létező mappákra oldódjon fel.

    A modulszintű fogantyút cseréljük (a `_platform()` mintájára, #1217):
    így a próba kimondja, melyik ágat méri, és nem a futtató gép
    XDG-beállításaitól függ."""
    utak = {}
    for token, nev in (("mypics", "Kepek"), ("mydocs", "Iratok"),
                       ("desktop", "Asztal")):
        p = tmp_path / nev
        p.mkdir()
        utak[token] = str(p)
    monkeypatch.setattr(fhc, "_rendszermappa", lambda token: utak.get(token, ""))
    return utak


class TestAKetValodiGyoker:
    """`flat` ↔ `all` kizáró pár, a `watched` az `all` szűkítése."""

    def test_a_lapos_gyoker_kikapcsolja_a_fat(self, beallitasok):
        ctl = FolderHierarchyController(settings=beallitasok)
        ctl.setViewRoot("all")
        assert ctl.treeView is True
        ctl.setViewRoot("flat")
        assert ctl.treeView is False
        assert ctl.viewRoot == "flat"

    def test_a_sajatgep_nem_nyul_az_egyszerusiteshez(self, beallitasok):
        """Mért: a `SimplifiedHierarchy` FÜGGETLEN, tartós kapcsoló (spec 3.),
        és bekapcsolva az `all` gyökeret `watched`-re cseréli
        (`0x0057517c`–`0x005751ec`) — tehát a Sajátgép-tétel nem kapcsolja ki.

        ⚠️ Ezt a próbát a megvalósítás közben JAVÍTOTTAM: elsőre azt
        állítottam, hogy a Sajátgép a teljes fát adja. Az a feltevésem volt,
        nem mérés — és szembement a #2154-tel, ami szerint a kapcsoló
        túléli az újraindítást."""
        ctl = FolderHierarchyController(settings=beallitasok)
        ctl.setSimplified(True)
        ctl.setViewRoot("all")
        assert ctl.treeView is True
        assert ctl.simplified is True, "a Sajátgép kikapcsolta az egyszerűsítést"
        assert ctl.viewRoot == "watched"

    def test_az_egyszerusitett_a_watched_token(self, beallitasok):
        """A meglévő kapcsoló és az új gyökér-token EGY igazságforrás."""
        ctl = FolderHierarchyController(settings=beallitasok)
        ctl.setTreeView(True)
        ctl.setSimplified(True)
        assert ctl.viewRoot == "watched"
        ctl.setSimplified(False)
        assert ctl.viewRoot == "all"
        ctl.setTreeView(False)
        assert ctl.viewRoot == "flat"


class TestAHaromRendszermappa:
    """Mért: ELŐBB a teljes fára vált, AZTÁN ugrik."""

    @pytest.mark.parametrize("token", ["mypics", "mydocs", "desktop"])
    def test_elobb_a_fara_valt(self, beallitasok, mappak, token):
        ctl = FolderHierarchyController(settings=beallitasok)
        ctl.setTreeView(False)
        ctl.setViewRoot(token)
        assert ctl.treeView is True, "nem váltott a fára"
        assert ctl.viewRoot == token, "a rekesz a rendszermappa-tokent tárolja"

    @pytest.mark.parametrize("token", ["mypics", "mydocs", "desktop"])
    def test_jelzi_a_feloldott_mappat(self, beallitasok, mappak, token):
        ctl = FolderHierarchyController(settings=beallitasok)
        kapott = []
        ctl.rootFolderRevealed.connect(kapott.append)
        ctl.setViewRoot(token)
        assert kapott == [mappak[token]]

    def test_feloldhatatlan_mappa_visszaesik_a_sajatgepre(self, beallitasok,
                                                          monkeypatch):
        """Mért hibakezelés: `"all"` gyökér, NEM hibaüzenet."""
        monkeypatch.setattr(fhc, "_rendszermappa", lambda token: "")
        ctl = FolderHierarchyController(settings=beallitasok)
        kapott = []
        ctl.rootFolderRevealed.connect(kapott.append)

        ctl.setViewRoot("desktop")

        assert ctl.viewRoot == "all", "nem esett vissza a Sajátgép-gyökérre"
        assert ctl.treeView is True
        assert kapott == [], "feloldhatatlan mappára nem jelezhet ugrást"

    def test_a_kepek_mappa_az_iratokra_esik_vissza(self, beallitasok, tmp_path,
                                                   monkeypatch):
        """`0x00996747 call 0x996230` — a `mypics` feloldó maga hív `mydocs`-ot."""
        iratok = tmp_path / "Iratok"
        iratok.mkdir()
        monkeypatch.setattr(
            fhc, "_rendszermappa",
            lambda token: str(iratok) if token == "mydocs" else "",
        )
        ctl = FolderHierarchyController(settings=beallitasok)
        kapott = []
        ctl.rootFolderRevealed.connect(kapott.append)

        ctl.setViewRoot("mypics")

        assert kapott == [str(iratok)]
        assert ctl.viewRoot == "mypics"


class TestAFejlecFelirat:
    """4.2 és 4.5/c: pontosan KETTŐ rögzített szöveg van, és nem öt."""

    def test_a_lapos_gyoker_felirata(self, beallitasok):
        ctl = FolderHierarchyController(settings=beallitasok)
        ctl.setViewRoot("flat")
        assert ctl.rootLabel == "Default View"

    @pytest.mark.parametrize("token", ["all", "watched"])
    def test_a_teljes_fa_felirata(self, beallitasok, token):
        ctl = FolderHierarchyController(settings=beallitasok)
        ctl.setViewRoot("all")
        if token == "watched":
            ctl.setSimplified(True)
        assert ctl.rootLabel == "My Computer"

    @pytest.mark.parametrize("token", ["mypics", "mydocs", "desktop"])
    def test_a_rendszermappa_a_SAJAT_nevet_mutatja(self, beallitasok, mappak,
                                                   token):
        """Ezekhez NINCS erőforrás-szöveg — a feloldott mappa neve látszik."""
        import os

        ctl = FolderHierarchyController(settings=beallitasok)
        ctl.setViewRoot(token)
        assert ctl.rootLabel == os.path.basename(mappak[token])


class TestAGyokerTuleliAzUjrainditast:
    """8. pont: a választott gyökér újraindítás után visszaáll."""

    @pytest.mark.parametrize("token", ["flat", "all", "watched"])
    def test_uj_peldanyban_is_megvan(self, beallitasok, token):
        elso = FolderHierarchyController(settings=beallitasok)
        elso.setViewRoot(token)
        assert elso.viewRoot == token

        masodik = FolderHierarchyController(settings=beallitasok)
        assert masodik.viewRoot == token
        assert masodik.treeView is (token != "flat")

    def test_a_rendszermappa_token_is_megmarad(self, beallitasok, mappak):
        elso = FolderHierarchyController(settings=beallitasok)
        elso.setViewRoot("mypics")

        masodik = FolderHierarchyController(settings=beallitasok)
        assert masodik.viewRoot == "mypics"
        assert masodik.treeView is True
        assert masodik.simplified is False

    def test_ismeretlen_tarolt_token_a_laposra_esik(self, beallitasok):
        """Kontroll: elgépelt vagy régi beállítás ne törje el az indulást."""
        beallitasok.setValue("view/folderViewRoot", "zsiraf")
        beallitasok.sync()
        ctl = FolderHierarchyController(settings=beallitasok)
        assert ctl.viewRoot == "flat"

    def test_a_ket_kapcsolo_MARAD_az_igazsagforras(self, beallitasok):
        """Kontroll a #2154-re: a gyökér nem írhatja felül a tárolt
        kapcsolókat. A lapos nézetben bekapcsolt egyszerűsítés túléli az
        újraindítást, pedig a gyökér ilyenkor `flat`."""
        elso = FolderHierarchyController(settings=beallitasok)
        elso.setTreeView(False)
        elso.setSimplified(True)
        assert elso.viewRoot == "flat"

        masodik = FolderHierarchyController(settings=beallitasok)
        assert masodik.simplified is True, "az egyszerűsítés elveszett"
        assert masodik.treeView is False
