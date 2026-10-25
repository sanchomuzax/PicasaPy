"""A Fájl menü tételei VALÓDI egérkattintással (#5150, 1. rész).

Minden tétel a főmenü fejlécére, majd magára a tételre kattintva indul
(`_megnyit`, `_kattints`), tehát a menüsor kezelését is a valódi bemenet
viszi. Parancsot közvetlenül nem indítunk: nincs `triggered`/`clicked`/
`activated` hívás és nincs `.emit()`. A hatást a párbeszédek láthatóságán,
a lemezen maradt fájlokon és a jelzéseken mérjük. A párbeszédek takarításához
a `close` hívás szabad.

Már lefedett tételek (ezeket ebben a fájlban nem ismételjük):
- `menuFilePrint`: test_menusor_billentyu_valodi_5127.py:146
- `menuFileImportFrom`: test_menu_talca_egyeb_valodi_5135_e.py:64 (`_import_megnyit`)
- `menuFileExport`: test_menu_talca_egyeb_valodi_5135_e.py:193
- `menuFileRevert`: test_email_mentes_valodi_5135_b.py:276
- `menuFileEmail`: test_felsomenupontok_file_4329.py:19
- `menuFileOpenInEditor`: test_felsomenupontok_file_4329.py:49

Lefedve itt: `menuFileNewAlbum`, `menuFileAddFolder`, `menuFileAddFile`,
`menuFileMoveToNewFolder`, `menuFileRename`, `menuFileSave`,
`menuFileSaveAs`, `menuFileSaveCopy`, `menuFileLocate`, `menuFileDelete`,
`menuFileExit`.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import QMetaObject, Qt
from PySide6.QtTest import QSignalSpy

from conftest import _build_qml_app
from support.jpeg_factory import make_jpeg
from support.qt_wait import wait_for_photo_op, wait_for_signal
from support.varakozas import hibaturo_feltetel, var_feltetelre
from tests.app.qml_functional._felsomenupontok_helpers_4329 import (
    _kattints,
    _objektum,
)
from tests.app.qml_functional._fomenu_4420_menu import _megnyit

_MAPPA = "fotok"
_KEPEK = ("a_elso.jpg", "b_masodik.jpg")


def _keszits_konyvtarakat(lib: Path) -> None:
    fotok = lib / _MAPPA
    fotok.mkdir()
    for nev in _KEPEK:
        make_jpeg(fotok / nev, size=(320, 240))


@pytest.fixture
def fajl_app(qt_app, tmp_path):
    yield from _build_qml_app(
        qt_app,
        tmp_path,
        kepeket_keszit=_keszits_konyvtarakat,
    )


def _varj(qt_app, feltetel, masodperc: float = 10.0) -> bool:
    return var_feltetelre(qt_app, hibaturo_feltetel(feltetel), masodperc)


def _gyerek(window, nev: str):
    elem = _objektum(window, nev)
    assert elem is not None, f"{nev} nem található"
    return elem


def _latszik(window, nev: str) -> bool:
    elem = _objektum(window, nev)
    return elem is not None and elem.property("visible") is True


def _mappa_ut(controller, mappa: str) -> Path:
    return Path(str(controller.watchedFolders[0])) / mappa


def _kijelol(window, qt_app, sorok) -> None:
    window.setProperty("selectedIndexes", list(sorok))
    window.setProperty("selectedIndex", sorok[0] if sorok else -1)
    qt_app.processEvents()


def _elokeszit(window, qt_app, controller) -> None:
    """Megjeleníti az ablakot, betölti a `fotok` mappát, és kijelöli az első képet."""
    window.show()
    window.requestActivate()
    qt_app.processEvents()
    controller.selectFolder(str(_mappa_ut(controller, _MAPPA)))
    assert _varj(
        qt_app, lambda: len(controller.photos.photos) == len(_KEPEK)
    ), "a teszt mappája nem töltődött be"
    _kijelol(window, qt_app, [0])


def _tetel_kattintasa(window, qt_app, nev: str) -> None:
    """Valódi kattintás egy már megnyitott menü tételén."""
    tetel = _gyerek(window, nev)
    assert tetel.property("visible") is True, f"{nev} nem látszik a menüben"
    assert tetel.property("enabled") is True, f"{nev} tiltott"
    _kattints(qt_app, tetel)


def _fajl_tetelt_kattint(window, qt_app, nev: str) -> None:
    """Megnyitja a Fájl menüt valódi kattintással, majd a tételre kattint."""
    menu_bar = window.property("menuBar")
    menu = _megnyit(menu_bar, qt_app, "&File")
    assert menu is not None, "a Fájl menü nem nyílt meg"
    _tetel_kattintasa(window, qt_app, nev)


def _zar_ha_nyitva(window, qt_app, nev: str) -> None:
    """Takarítás: a megnyílt párbeszédet bezárja (a `close` szabad)."""
    elem = _objektum(window, nev)
    if elem is not None and elem.property("visible") is True:
        QMetaObject.invokeMethod(elem, "close", Qt.ConnectionType.DirectConnection)
        qt_app.processEvents()


class TestUjAlbumEsMappa:
    def test_az_uj_album_valodi_kattintassal_letrehozza_az_albumot(
        self, fajl_app, qt_app
    ):
        window, controller, _engine = fajl_app
        _elokeszit(window, qt_app, controller)
        assert controller.albums == []

        _fajl_tetelt_kattint(window, qt_app, "menuFileNewAlbum")

        assert _varj(
            qt_app, lambda: [a["name"] for a in controller.albums] == ["Untitled"]
        ), "a Fájl ▸ Új album… kattintás nem hozott létre albumot"

    def test_a_mappa_hozzaadasa_valodi_kattintassal_megnyitja_a_mappakezelot(
        self, fajl_app, qt_app
    ):
        window, controller, _engine = fajl_app
        _elokeszit(window, qt_app, controller)

        _fajl_tetelt_kattint(window, qt_app, "menuFileAddFolder")

        assert _varj(qt_app, lambda: _latszik(window, "folderManagerDialog")), (
            "a Fájl ▸ Mappa hozzáadása… nem nyitotta meg a mappakezelőt"
        )
        _zar_ha_nyitva(window, qt_app, "folderManagerDialog")

    def test_a_fajl_felvetele_valodi_kattintassal_megnyitja_a_fajlvalasztot(
        self, fajl_app, qt_app
    ):
        window, controller, _engine = fajl_app
        _elokeszit(window, qt_app, controller)

        _fajl_tetelt_kattint(window, qt_app, "menuFileAddFile")

        assert _varj(qt_app, lambda: _latszik(window, "addFileDialog")), (
            "a Fájl ▸ Fájl felvétele… nem nyitotta meg a fájlválasztót"
        )
        _zar_ha_nyitva(window, qt_app, "addFileDialog")

    def test_az_uj_mappaba_helyezes_valodi_kattintassal_megnyitja_a_nevet_kerdezo_parbeszedet(
        self, fajl_app, qt_app
    ):
        window, controller, _engine = fajl_app
        _elokeszit(window, qt_app, controller)

        _fajl_tetelt_kattint(window, qt_app, "menuFileMoveToNewFolder")

        assert _varj(qt_app, lambda: _latszik(window, "moveToNewFolderDialog")), (
            "a Fájl ▸ Áthelyezés új mappába… nem nyitotta meg a párbeszédet"
        )
        _zar_ha_nyitva(window, qt_app, "moveToNewFolderDialog")


class TestAtnevezesEsMentes:
    def test_az_atnevezes_valodi_kattintassal_megnyitja_a_parbeszedet(
        self, fajl_app, qt_app
    ):
        window, controller, _engine = fajl_app
        _elokeszit(window, qt_app, controller)

        _fajl_tetelt_kattint(window, qt_app, "menuFileRename")

        assert _varj(qt_app, lambda: _latszik(window, "renameManyDialog")), (
            "a Fájl ▸ Átnevezés… nem nyitotta meg a párbeszédet"
        )
        _zar_ha_nyitva(window, qt_app, "renameManyDialog")

    def test_a_mentes_valodi_kattintassal_megerositeset_keri(self, fajl_app, qt_app):
        window, controller, _engine = fajl_app
        _elokeszit(window, qt_app, controller)
        wait_for_photo_op(
            controller,
            lambda: controller.applyEffectMany([0], "enhance"),
            qt_app=qt_app,
        )

        _fajl_tetelt_kattint(window, qt_app, "menuFileSave")

        assert _varj(qt_app, lambda: _latszik(window, "saveConfirmDialog")), (
            "a Fájl ▸ Mentés nem kérte a megerősítést"
        )
        _zar_ha_nyitva(window, qt_app, "saveConfirmDialog")

    def test_a_mentes_masként_valodi_kattintassal_megnyitja_a_fajlvalasztot(
        self, fajl_app, qt_app
    ):
        window, controller, _engine = fajl_app
        _elokeszit(window, qt_app, controller)

        _fajl_tetelt_kattint(window, qt_app, "menuFileSaveAs")

        assert _varj(qt_app, lambda: _latszik(window, "saveAsFileDialog")), (
            "a Fájl ▸ Mentés másként… nem nyitott fájlválasztót"
        )
        _zar_ha_nyitva(window, qt_app, "saveAsFileDialog")

    def test_a_masolat_mentese_valodi_kattintassal_letrehozza_a_001_masolatot(
        self, fajl_app, qt_app
    ):
        window, controller, _engine = fajl_app
        _elokeszit(window, qt_app, controller)
        forras = Path(str(controller.photos.filePathAt(0)))
        masolat = forras.parent / f"{forras.stem}-001{forras.suffix}"
        assert not masolat.exists()

        wait_for_signal(
            controller.saveCopyFinished,
            lambda: _fajl_tetelt_kattint(window, qt_app, "menuFileSaveCopy"),
            description="a Fájl ▸ Másolat mentése",
            process_events_with=qt_app,
        )

        assert masolat.exists(), (
            "a Másolat mentése nem írt -001 másolatot a lemezre"
        )
        assert forras.exists(), "a forrás képet a másolat mentése elvitte"


class TestLemezEsTorles:
    def test_a_lemezen_megmutatas_valodi_kattintassal_a_fajlt_adja_at(
        self, fajl_app, qt_app, monkeypatch
    ):
        """Helyettesítő: a valódi fájlkezelő-indítás ki van váltva."""
        import picasapy.app.fileops_controller as fileops_module

        window, controller, _engine = fajl_app
        _elokeszit(window, qt_app, controller)
        megnyitva: list[Path] = []
        monkeypatch.setattr(
            fileops_module,
            "reveal_in_file_manager",
            lambda path: megnyitva.append(Path(path)),
        )
        forras = Path(str(controller.photos.filePathAt(0)))

        _fajl_tetelt_kattint(window, qt_app, "menuFileLocate")

        assert _varj(qt_app, lambda: megnyitva == [forras]), (
            f"a Lemezen megmutatás nem a kijelölt fájlt adta át: {megnyitva}"
        )

    def test_a_torles_valodi_kattintassal_megerositest_ker(self, fajl_app, qt_app):
        window, controller, _engine = fajl_app
        _elokeszit(window, qt_app, controller)

        _fajl_tetelt_kattint(window, qt_app, "menuFileDelete")

        assert _varj(qt_app, lambda: _latszik(window, "deleteConfirmDialog")), (
            "a Fájl ▸ Törlés nem kért megerősítést"
        )
        _zar_ha_nyitva(window, qt_app, "deleteConfirmDialog")
        assert Path(str(controller.photos.filePathAt(0))).exists(), (
            "a megerősítés nélkül a fájl eltűnt"
        )


class TestKilepes:
    def test_a_kilepes_valodi_kattintassal_kiadja_a_kilepesi_jelzest(
        self, fajl_app, qt_app
    ):
        """A kilépés teljes útját (Qt.quit) nem futtatjuk a tesztben: a
        menütétel kattintására a menüsor `exitRequested` jelzést bocsát ki,
        ezt mérjük (a `Main.qml` ebből hívja a `kilepes()`-t)."""
        window, controller, _engine = fajl_app
        _elokeszit(window, qt_app, controller)
        menu_bar = window.property("menuBar")
        jelzes = QSignalSpy(menu_bar.exitRequested)

        _fajl_tetelt_kattint(window, qt_app, "menuFileExit")

        assert _varj(qt_app, lambda: jelzes.count() == 1), (
            "a Fájl ▸ Kilépés kattintás nem bocsátotta ki a kilépési jelzést"
        )
