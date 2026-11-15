"""#6977: A Save As és a Save a Copy videónál tiltott, és lemezhibánál
az eredeti másolat-mentési hibaszöveget mutatja (CThumbUI::FileSaveCopy:err).
"""

from __future__ import annotations

import errno
from pathlib import Path
from unittest.mock import patch

import pytest
from PySide6.QtCore import QMetaObject, QObject, Qt

from conftest import _build_qml_app
from support.halasztott_parbeszed import epitsd_fel
from support.jpeg_factory import make_jpeg
from support.qt_wait import wait_for_signal
from tests.app.qml_functional._felsomenupontok_helpers_4329 import (
    _kattints,
    _objektum,
    _varj,
)
from tests.app.qml_functional._fomenu_4420_menu import _megnyit

_MAPPA = "vegyes"


def _keszits_vegyes_konyvtarat(lib: Path) -> None:
    mappa = lib / _MAPPA
    mappa.mkdir()
    make_jpeg(mappa / "a_foto.jpg", size=(320, 240))
    make_jpeg(mappa / "b_foto.jpg", size=(320, 240))
    (mappa / "c_video1.mp4").write_bytes(b"\x00" * 64)
    (mappa / "d_video2.avi").write_bytes(b"\x00" * 64)


@pytest.fixture
def vegyes_app(qt_app, tmp_path):
    yield from _build_qml_app(
        qt_app,
        tmp_path,
        kepeket_keszit=_keszits_vegyes_konyvtarat,
    )


def _mappa_ut(controller, mappa: str) -> Path:
    return Path(str(controller.watchedFolders[0])) / mappa


def _kijelol(window, qt_app, sorok) -> None:
    window.setProperty("selectedIndexes", list(sorok))
    window.setProperty("selectedIndex", sorok[0] if sorok else -1)
    qt_app.processEvents()


def _elokeszit(window, qt_app, controller) -> None:
    window.show()
    window.requestActivate()
    qt_app.processEvents()
    controller.selectFolder(str(_mappa_ut(controller, _MAPPA)))
    assert _varj(
        qt_app, lambda: len(controller.photos.photos) == 4
    ), "a teszt mappája nem töltődött be"
    _kijelol(window, qt_app, [0])


def _zar_ha_nyitva(window, qt_app, nev: str) -> None:
    elem = _objektum(window, nev)
    if elem is not None and elem.property("visible") is True:
        QMetaObject.invokeMethod(elem, "close", Qt.ConnectionType.DirectConnection)
        qt_app.processEvents()


class TestVideoMentésMenüTiltva:
    """Videó kijelölésekor a Fájl ▸ Save As és Save a Copy menüpont tiltott."""

    def test_csak_video_kijelolesnel_a_mentes_maskent_es_masolat_mentese_szurke(
        self, vegyes_app, qt_app
    ):
        window, controller, _engine = vegyes_app
        _elokeszit(window, qt_app, controller)

        # Keressük meg a videók és fotók sorait
        video_sorok = [
            i for i in range(controller.photos.rowCount())
            if controller.photos.isVideoAt(i)
        ]
        assert len(video_sorok) == 2, "két videónak kell lennie"

        item_save_as = _objektum(window, "menuFileSaveAs")
        item_save_copy = _objektum(window, "menuFileSaveCopy")
        assert item_save_as is not None and item_save_copy is not None

        # Egyetlen videó kijelölése -> tiltott
        _kijelol(window, qt_app, [video_sorok[0]])
        menu_bar = window.property("menuBar")
        menu = _megnyit(menu_bar, qt_app, "&File")
        assert _varj(qt_app, lambda: item_save_as.property("enabled") is False), (
            "Save As nem tiltott egyetlen videó kijelölésénél"
        )
        assert item_save_copy.property("enabled") is False, (
            "Save a Copy nem tiltott egyetlen videó kijelölésénél"
        )
        menu.close()
        qt_app.processEvents()

        # Csak videókat tartalmazó többes kijelölés -> tiltott
        _kijelol(window, qt_app, video_sorok)
        menu = _megnyit(menu_bar, qt_app, "&File")
        assert _varj(qt_app, lambda: item_save_as.property("enabled") is False), (
            "Save As nem tiltott csak videókat tartalmazó kijelölésnél"
        )
        assert item_save_copy.property("enabled") is False, (
            "Save a Copy nem tiltott csak videókat tartalmazó kijelölésnél"
        )
        menu.close()
        qt_app.processEvents()

    def test_foto_kijelolesnel_mindket_menupont_aktiv_es_vegyes_kijelolesnel_is(
        self, vegyes_app, qt_app
    ):
        window, controller, _engine = vegyes_app
        _elokeszit(window, qt_app, controller)

        foto_sorok = [
            i for i in range(controller.photos.rowCount())
            if not controller.photos.isVideoAt(i)
        ]
        video_sorok = [
            i for i in range(controller.photos.rowCount())
            if controller.photos.isVideoAt(i)
        ]
        assert len(foto_sorok) >= 1 and len(video_sorok) >= 1

        item_save_as = _objektum(window, "menuFileSaveAs")
        item_save_copy = _objektum(window, "menuFileSaveCopy")

        # Egy fotó kijelölése -> aktív
        _kijelol(window, qt_app, [foto_sorok[0]])
        menu_bar = window.property("menuBar")
        menu = _megnyit(menu_bar, qt_app, "&File")
        assert _varj(qt_app, lambda: item_save_as.property("enabled") is True)
        assert item_save_copy.property("enabled") is True
        menu.close()
        qt_app.processEvents()

        # Vegyes kijelölés (fotó + videó) -> aktív
        _kijelol(window, qt_app, [foto_sorok[0], video_sorok[0]])
        menu = _megnyit(menu_bar, qt_app, "&File")
        assert _varj(qt_app, lambda: item_save_as.property("enabled") is True)
        assert item_save_copy.property("enabled") is True
        menu.close()
        qt_app.processEvents()

    @pytest.mark.parametrize("magassag_elteres", [-5, 0, 5])
    def test_foto_kijelolesnel_kattinthato_a_mentes_maskent(
        self, vegyes_app, qt_app, magassag_elteres
    ):
        window, controller, _engine = vegyes_app
        _elokeszit(window, qt_app, controller)
        window.setHeight(window.height() + magassag_elteres)
        qt_app.processEvents()

        foto_sorok = [
            i for i in range(controller.photos.rowCount())
            if not controller.photos.isVideoAt(i)
        ]
        _kijelol(window, qt_app, [foto_sorok[0]])

        menu_bar = window.property("menuBar")
        _megnyit(menu_bar, qt_app, "&File")
        item_save_as = _objektum(window, "menuFileSaveAs")
        assert item_save_as.property("enabled") is True
        _kattints(qt_app, item_save_as)

        assert _varj(
            qt_app,
            lambda: _objektum(window, "saveAsFileDialog") is not None
            and _objektum(window, "saveAsFileDialog").property("visible") is True,
        ), "a Fájl ▸ Save As nem nyitott fájlválasztót kattintásra"
        _zar_ha_nyitva(window, qt_app, "saveAsFileDialog")

    def test_nezo_modban_video_eseten_tiltott_fotonál_aktiv(
        self, vegyes_app, qt_app
    ):
        window, controller, _engine = vegyes_app
        _elokeszit(window, qt_app, controller)

        foto_sor = next(
            i for i in range(controller.photos.rowCount())
            if not controller.photos.isVideoAt(i)
        )
        video_sor = next(
            i for i in range(controller.photos.rowCount())
            if controller.photos.isVideoAt(i)
        )

        window.setProperty("viewerOpen", True)
        assert _varj(
            qt_app, lambda: window.findChild(QObject, "photoViewer") is not None
        ), "a néző nem nyílt meg"
        viewer = _objektum(window, "photoViewer")

        item_save_as = _objektum(window, "menuFileSaveAs")
        item_save_copy = _objektum(window, "menuFileSaveCopy")
        menu_bar = window.property("menuBar")

        # Néző videón -> tiltott
        viewer.setProperty("currentIndex", video_sor)
        qt_app.processEvents()

        menu = _megnyit(menu_bar, qt_app, "&File")
        assert _varj(qt_app, lambda: item_save_as.property("enabled") is False)
        assert item_save_copy.property("enabled") is False
        menu.close()
        qt_app.processEvents()

        # Néző fotón -> aktív
        viewer.setProperty("currentIndex", foto_sor)
        qt_app.processEvents()

        menu = _megnyit(menu_bar, qt_app, "&File")
        assert _varj(qt_app, lambda: item_save_as.property("enabled") is True)
        assert item_save_copy.property("enabled") is True
        menu.close()
        qt_app.processEvents()


class TestLemezhibaSzoveg:
    """A Save As és a Save a Copy lemezhibájánál a FileSaveCopy:err szövege jelenik meg."""

    def test_masolat_mentes_lemezhiba_dialogus_szoveg(self, vegyes_app, qt_app):
        window, _controller, _engine = vegyes_app
        epitsd_fel(window, "saveDialogs")
        parbeszed = _objektum(window, "saveErrorDialog")
        assert parbeszed is not None
        parbeszed.setProperty("kind", "copy_disk")
        parbeszed.setProperty("fileName", "teszt.jpg")
        parbeszed.setProperty("code", 28)
        qt_app.processEvents()

        szoveg = _objektum(window, "saveErrorMessage").property("text")
        # FileSaveCopy:err hivatalos angol szövege:
        # "Unable to save files due to a disk error. The disk may be full or read-only."
        assert szoveg == "Unable to save files due to a disk error. The disk may be full or read-only."
        # Fájlnév és hibakód nélkül!
        assert "teszt.jpg" not in szoveg
        assert "28" not in szoveg

    def test_normal_mentes_lemezhiba_szoveg_valtozatlan(self, vegyes_app, qt_app):
        window, _controller, _engine = vegyes_app
        epitsd_fel(window, "saveDialogs")
        parbeszed = _objektum(window, "saveErrorDialog")
        assert parbeszed is not None
        parbeszed.setProperty("kind", "disk")
        parbeszed.setProperty("fileName", "teszt.jpg")
        parbeszed.setProperty("code", 28)
        qt_app.processEvents()

        szoveg = _objektum(window, "saveErrorMessage").property("text")
        # filesaveerr-win: fájlnévvel és hibakóddal
        assert "Unable to save all files due to a disk error" in szoveg
        assert "teszt.jpg" in szoveg
        assert "error(28)" in szoveg

    def test_save_copy_lemezhiba_eseten_copy_disk_hibat_jelez(
        self, vegyes_app, qt_app
    ):
        window, controller, _engine = vegyes_app
        epitsd_fel(window, "saveDialogs")
        _elokeszit(window, qt_app, controller)

        foto_sor = next(
            i for i in range(controller.photos.rowCount())
            if not controller.photos.isVideoAt(i)
        )
        _kijelol(window, qt_app, [foto_sor])

        parbeszed = _objektum(window, "saveErrorDialog")
        assert parbeszed is not None

        with patch("picasapy.app.save_as_copy.save_copy", side_effect=OSError(errno.ENOSPC, "No space left")):
            wait_for_signal(
                controller.saveCopyFinished,
                lambda: controller.saveCopyRows([foto_sor]),
                description="a Másolat mentése hibaág",
                process_events_with=qt_app,
            )

        assert parbeszed.property("visible") is True
        szoveg = _objektum(window, "saveErrorMessage").property("text")
        assert szoveg == "Unable to save files due to a disk error. The disk may be full or read-only."
        parbeszed.setProperty("visible", False)
        qt_app.processEvents()
