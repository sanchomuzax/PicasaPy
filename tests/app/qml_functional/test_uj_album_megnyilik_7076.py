"""#7076: az új album létrehozása után az ÚJ ALBUM nyílik meg.

Az eredetiben (`0x005eb810` siker után) a `0x004af790`-től kapott új album
azonosítója lesz az aktuális album, és a nézet frissül. Nálunk a Fájl ▸ New
Album... és az eszköztár új album gombja ugyanazt az Album Properties
párbeszédet használja; jóváhagyás után annak rácsa nyílik, mégpedig ugyanazon
az úton, mint a bal hasáb albumsorának kattintása. Mégse vagy íráshiba esetén
a jelenlegi nézet és a kijelölés marad.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from PySide6.QtCore import QObject

from tests.app.qml_functional._felsomenupontok_helpers_4329 import _objektum
from tests.app.qml_functional._fomenu_4420_menu import _kattints
from tests.app.qml_functional._teszt_menu_6861 import megnyit_fomenu
from tests.app.qml_functional.conftest import _build_qml_app
from tests.support.jpeg_factory import make_minta_jpeg
from tests.support.varakozas import var_feltetelre

_MAGASSAG_ELTERESEK = [-5, 0, 5]


def _kepeket_keszit(mappa: Path) -> None:
    make_minta_jpeg(mappa / "a.jpg", size=(640, 400), seed=71)
    make_minta_jpeg(mappa / "b.jpg", size=(500, 500), seed=72)


@pytest.fixture
def qml_app(qt_app, tmp_path, request):
    yield from _build_qml_app(
        qt_app,
        tmp_path,
        kepeket_keszit=_kepeket_keszit,
        keep_modul=request.module,
    )


def _varj(qt_app, feltetel) -> bool:
    return var_feltetelre(qt_app, feltetel, 5.0)


def _elem(gyoker, nev: str) -> QObject:
    elem = _objektum(gyoker, nev)
    assert elem is not None, f"{nev} nem található"
    return elem


def _ablakmagassag(window, qt_app, offset: int) -> None:
    vart = window.height() + offset
    window.setHeight(vart)
    assert _varj(qt_app, lambda: window.height() == vart), (
        f"a főablak magassága nem állt be {vart} px-re"
    )


def _kijelol_ket_kept(window, qt_app, controller) -> None:
    assert _varj(qt_app, lambda: controller.photos.rowCount() == 2), (
        "a két tesztkép nem töltődött be"
    )
    window.setProperty("selectedIndexes", [0, 1])
    window.setProperty("selectedIndex", 0)
    qt_app.processEvents()


def _fajl_uj_album(window, qt_app) -> QObject:
    """Fájl ▸ New Album... valódi kattintással, a megnyílt párbeszéddel tér vissza."""
    megnyit_fomenu(window, qt_app, "&File")
    tetel = _elem(window, "menuFileNewAlbum")
    assert tetel.property("visible") is True
    _kattints(qt_app, tetel)
    return _megnyilt_parbeszed(window, qt_app)


def _eszkoztar_uj_album(window, qt_app) -> QObject:
    _kattints(qt_app, _elem(window, "toolbarNewAlbumButton"))
    return _megnyilt_parbeszed(window, qt_app)


def _megnyilt_parbeszed(window, qt_app) -> QObject:
    dialog = _elem(window, "toolbarNewAlbumPropertiesDialog")
    assert _varj(qt_app, lambda: dialog.property("opened") is True), (
        "az új album nem nyitotta meg az Album Properties ablakot"
    )
    return dialog


def _ok(window, qt_app, dialog) -> None:
    _kattints(qt_app, _elem(dialog, "folderPropertiesOkButton"))
    assert _varj(qt_app, lambda: dialog.property("opened") is False), (
        "az OK nem zárta be az Album Properties ablakot"
    )


def _kijeloles(window) -> list[int]:
    ertek = window.property("selectedIndexes")
    if hasattr(ertek, "toVariant"):
        ertek = ertek.toVariant()
    return [int(i) for i in (ertek or [])]


@pytest.mark.parametrize("height_offset", _MAGASSAG_ELTERESEK)
def test_file_menu_new_album_ok_utan_az_uj_album_nyilik_meg(
    qml_app, qt_app, height_offset
):
    window, controller, _engine = qml_app
    _ablakmagassag(window, qt_app, height_offset)
    _kijelol_ket_kept(window, qt_app, controller)
    assert controller.currentAlbumToken == ""
    assert controller.viewModeName == "folder"

    dialog = _fajl_uj_album(window, qt_app)
    _ok(window, qt_app, dialog)

    assert _varj(qt_app, lambda: len(controller.albums) == 1), (
        "az OK nem hozta létre az albumot"
    )
    token = controller.albums[0]["token"]
    assert _varj(qt_app, lambda: controller.currentAlbumToken == token), (
        "az új album létrehozása után nem az új album a nyitott nézet"
    )
    assert controller.viewModeName == "album"
    assert controller.filterActive is True
    assert controller.photos.rowCount() == 2, (
        "az új album rácsa a két kijelölt képet kell mutassa"
    )
    assert _kijeloles(window) == [], (
        "a bal hasábból nyitott albumhoz hasonlóan a kijelölés törlődik"
    )


@pytest.mark.parametrize("height_offset", _MAGASSAG_ELTERESEK)
def test_toolbar_new_album_ok_utan_az_uj_ures_album_nyilik_meg(
    qml_app, qt_app, height_offset
):
    window, controller, _engine = qml_app
    _ablakmagassag(window, qt_app, height_offset)
    assert _varj(qt_app, lambda: controller.photos.rowCount() == 2)
    assert controller.currentAlbumToken == ""

    dialog = _eszkoztar_uj_album(window, qt_app)
    _ok(window, qt_app, dialog)

    assert _varj(qt_app, lambda: len(controller.albums) == 1), (
        "az OK nem hozta létre az albumot"
    )
    token = controller.albums[0]["token"]
    assert _varj(qt_app, lambda: controller.currentAlbumToken == token), (
        "az eszköztárból létrehozott album nem nyílt meg"
    )
    assert controller.viewModeName == "album"
    assert controller.photos.rowCount() == 0, "az új album üres, rácsa is az"


@pytest.mark.parametrize("height_offset", _MAGASSAG_ELTERESEK)
def test_cancel_utan_marad_a_jelenlegi_nezet_es_kijeloles(
    qml_app, qt_app, height_offset
):
    window, controller, _engine = qml_app
    _ablakmagassag(window, qt_app, height_offset)
    _kijelol_ket_kept(window, qt_app, controller)
    mappa = controller.currentFolder

    dialog = _fajl_uj_album(window, qt_app)
    _kattints(qt_app, _elem(dialog, "folderPropertiesCancelButton"))
    assert _varj(qt_app, lambda: dialog.property("opened") is False)

    assert controller.albums == []
    assert controller.currentAlbumToken == ""
    assert controller.viewModeName == "folder"
    assert controller.currentFolder == mappa
    assert controller.photos.rowCount() == 2
    assert _kijeloles(window) == [0, 1], "a Mégse elvette a kijelölést"


@pytest.mark.skipif(os.name != "posix", reason="a chmod írásvédelme csak POSIX-on érvényesül (#1864)")
@pytest.mark.parametrize("height_offset", _MAGASSAG_ELTERESEK)
def test_irashiba_utan_marad_a_jelenlegi_nezet_es_kijeloles(
    qml_app, qt_app, tmp_path, height_offset
):
    window, controller, _engine = qml_app
    _ablakmagassag(window, qt_app, height_offset)
    _kijelol_ket_kept(window, qt_app, controller)
    mappa = Path(controller.currentFolder)
    hibak: list[str] = []
    controller.albumWriteFailed.connect(hibak.append)

    dialog = _fajl_uj_album(window, qt_app)
    eredeti_mod = mappa.stat().st_mode
    mappa.chmod(0o555)
    try:
        if os.access(mappa, os.W_OK):
            pytest.skip("a mappa írásvédelme itt nem érvényesül (rendszergazda?)")
        _ok(window, qt_app, dialog)
        assert _varj(qt_app, lambda: len(hibak) > 0), (
            "az íráshiba nem jelent meg albumhiba-jelzésként"
        )
    finally:
        mappa.chmod(eredeti_mod)

    assert controller.albums == []
    assert controller.currentAlbumToken == "", (
        "sikertelen létrehozás után nem nyílhat meg album"
    )
    assert controller.viewModeName == "folder"
    assert Path(controller.currentFolder) == mappa
    assert controller.photos.rowCount() == 2
    assert _kijeloles(window) == [0, 1], "az íráshiba elvette a kijelölést"
