"""#7350: a Shortcuts almenü Desktop és My Pictures tétele szürke, ha a
könyvtárban nincs alattuk mappa, mint az eredetiben.

## A mérés forrása

`docs/specs/paritas-folyamat-7326.md`, 3.2 és 8. szakasz (J7). Az eredeti
kezelő (`0x005e2000`) a három Shortcuts-gyerekre `EnableMenuItem(...,
(eredmény == 0))`-t hív (`0x005e2558`, `0x005e256a`, `0x005e257c`); a
`0x004f7e40` igaz, ha a rendszermappa útvonala előtagja a mappalista valamely
elemének. Mért: Colab job-804 17. kép: Desktop és My Pictures szürke, My
Documents és My Computer engedélyezett. A My Documents az eredetiben hibából
sosem tiltott (a Desktop azonosítót kétszer küldi), a viselkedést megtartjuk.

## Szándékos eltérés az eredetitől (a jegy mondja ki)

Az eredeti NYERS előtag-összevetést végez, a PicasaPy útvonal-HATÁRON (komponens
szerint) vet össze: a `/Kepek` rendszermappa nem előtagja a `/KepekMasolat`
mappának. A mappa maga is „alatta van" (egyezés is találat), mert az eredeti
nyers előtagja ilyenkor is igaz.

## Fok

A szabály statikus lelet és egy negatív mintán igazolt (job-804 17. kép); a
pozitív eset (mappa a Pictures alatt) és a lista azonosítása nincs mérve. Ez a
próba a szabály megvalósítását méri, az eredeti viselkedésével való egyezést
nem.
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
def gyokerek(monkeypatch):
    """A három rendszermappa: rögzített, létezőnek vett gyökerek (a modulszintű
    fogantyút cseréljük, a #1217 mintájára)."""
    utak = {
        "mypics": "/home/u/Kepek",
        "mydocs": "/home/u/Iratok",
        "desktop": "/home/u/Asztal",
    }
    monkeypatch.setattr(fhc, "_rendszermappa", lambda token: utak.get(token, ""))
    return utak


def _vezerlo(beallitasok, *utak: str) -> FolderHierarchyController:
    ctl = FolderHierarchyController(settings=beallitasok)
    ctl.setFolders([{"path": ut, "count": 1} for ut in utak])
    return ctl


class TestAKonyvtarEsARendszermappak:
    def test_mappa_a_kepek_alatt_engedelyezi_a_my_pictures_tetelt(
        self, beallitasok, gyokerek
    ):
        ctl = _vezerlo(beallitasok, "/home/u/Kepek/2024/nyaralas")
        assert ctl.picturesAvailable is True
        assert ctl.desktopAvailable is False

    def test_mappa_az_asztal_alatt_engedelyezi_a_desktop_tetelt(
        self, beallitasok, gyokerek
    ):
        ctl = _vezerlo(beallitasok, "/home/u/Asztal/regi")
        assert ctl.desktopAvailable is True
        assert ctl.picturesAvailable is False

    def test_idegen_mappak_mellett_mindketto_szurke(self, beallitasok, gyokerek):
        ctl = _vezerlo(beallitasok, "/mnt/nas/Fotok", "/home/u/Videok")
        assert ctl.desktopAvailable is False
        assert ctl.picturesAvailable is False

    def test_ures_konyvtarban_mindketto_szurke(self, beallitasok, gyokerek):
        ctl = _vezerlo(beallitasok)
        assert ctl.desktopAvailable is False
        assert ctl.picturesAvailable is False

    def test_a_gyoker_maga_is_talalat(self, beallitasok, gyokerek):
        """Az eredeti nyers előtagja a gyökér útvonalával egyező mappára is
        igaz."""
        ctl = _vezerlo(beallitasok, "/home/u/Kepek", "/home/u/Asztal")
        assert ctl.picturesAvailable is True
        assert ctl.desktopAvailable is True

    def test_zaro_perjeles_gyoker_is_talalat(self, beallitasok, monkeypatch):
        monkeypatch.setattr(
            fhc,
            "_rendszermappa",
            lambda token: "/home/u/Kepek/" if token == "mypics" else "",
        )
        ctl = _vezerlo(beallitasok, "/home/u/Kepek", "/home/u/Kepek/2024")
        assert ctl.picturesAvailable is True

    def test_utvonal_hatar_nem_nyers_elotag(self, beallitasok, gyokerek):
        """A `/Kepek` nem őse a `/KepekMasolat`-nak: a határon elválasztó kell
        (a jegy szándékos eltérése a nyers előtag-összevetéstől)."""
        ctl = _vezerlo(
            beallitasok, "/home/u/KepekMasolat", "/home/u/Asztal2/regi"
        )
        assert ctl.picturesAvailable is False
        assert ctl.desktopAvailable is False

    def test_a_my_documents_es_a_my_computer_nincs_a_tulajdonsagok_kozott(
        self, beallitasok, gyokerek
    ):
        """Az eredetiben a My Documents sosem tiltott, a My Computer sem: ezekhez
        nincs szabály, tehát nincs rájuk tulajdonság sem."""
        ctl = _vezerlo(beallitasok, "/mnt/nas/Fotok")
        assert not hasattr(ctl, "documentsAvailable")
        assert not hasattr(ctl, "computerAvailable")


class TestAWindowsosUtvonalak:
    def test_a_visszaper_es_a_kisbetu_nem_szamit(self, beallitasok, monkeypatch):
        """Windowson a felületi út `\\`-rel jön, a fa `/`-rel épül, és a
        fájlrendszer nem érzékeny a kis-nagybetűre (#1477)."""
        monkeypatch.setattr(fhc, "_platform", lambda: "win32")
        monkeypatch.setattr(
            fhc,
            "_rendszermappa",
            lambda token: "C:/Users/felhasznalo/Pictures" if token == "mypics" else "",
        )
        ctl = _vezerlo(beallitasok, "c:\\users\\felhasznalo\\pictures\\2024")
        assert ctl.picturesAvailable is True

    def test_linuxon_a_kisbetu_szamit(self, beallitasok, monkeypatch):
        """POSIX-on két eltérő betűzésű mappa két külön mappa lehet."""
        monkeypatch.setattr(fhc, "_platform", lambda: "linux")
        monkeypatch.setattr(
            fhc,
            "_rendszermappa",
            lambda token: "/home/u/Pictures" if token == "mypics" else "",
        )
        ctl = _vezerlo(beallitasok, "/home/u/pictures/2024")
        assert ctl.picturesAvailable is False


class TestAFeloldhatatlanGyoker:
    def test_feloldhatatlan_asztal_szurke(self, beallitasok, monkeypatch):
        monkeypatch.setattr(fhc, "_rendszermappa", lambda token: "")
        ctl = _vezerlo(beallitasok, "/home/u/Asztal/regi", "/home/u/Kepek/x")
        assert ctl.desktopAvailable is False
        assert ctl.picturesAvailable is False

    def test_a_kepek_a_dokumentumokra_esik_vissza_mint_a_ugras(
        self, beallitasok, monkeypatch
    ):
        """A `0x00996747 call 0x996230`: a Képek feloldó maga esik vissza a
        Dokumentumokra, tehát a tétel azt a gyökeret vizsgálja, ahová a
        kattintás ugrana (ld. `setViewRoot`)."""
        utak = {"mydocs": "/home/u/Iratok"}
        monkeypatch.setattr(fhc, "_rendszermappa", lambda token: utak.get(token, ""))
        ctl = _vezerlo(beallitasok, "/home/u/Iratok/szamlak")
        assert ctl.picturesAvailable is True


class TestAJelzes:
    def test_a_mappalista_cserejekor_jelez_es_frissul(self, beallitasok, gyokerek):
        ctl = _vezerlo(beallitasok, "/mnt/nas/Fotok")
        jelzesek: list[int] = []
        ctl.shortcutsAvailabilityChanged.connect(lambda: jelzesek.append(1))

        ctl.setFolders([{"path": "/home/u/Kepek/2024", "count": 3}])

        assert ctl.picturesAvailable is True
        assert jelzesek == [1]

    def test_valtozatlan_allapotnal_nem_jelez(self, beallitasok, gyokerek):
        ctl = _vezerlo(beallitasok, "/home/u/Kepek/2024")
        jelzesek: list[int] = []
        ctl.shortcutsAvailabilityChanged.connect(lambda: jelzesek.append(1))

        ctl.setFolders([{"path": "/home/u/Kepek/2025", "count": 3}])

        assert jelzesek == []
