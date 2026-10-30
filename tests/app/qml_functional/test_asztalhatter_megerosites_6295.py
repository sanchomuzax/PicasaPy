"""A Create > Set as Desktop parancs megerősítése (#6295)."""

from __future__ import annotations

import pytest
from PySide6.QtCore import QObject, QPointF, Qt
from PySide6.QtTest import QTest
from support.qt_wait import varj_feltetelre


_KERDES = (
    "This will replace your current desktop background with the current image.  "
    "Are you sure you want to proceed?"
)


def _elem(gyoker, nev):
    elem = gyoker.findChild(QObject, nev)
    assert elem is not None, f"{nev} nem található"
    return elem


def _kattint(ablak, elem, qt_app):
    assert elem.isVisible(), f"{elem.objectName()} nem látható"
    assert elem.isEnabled(), f"{elem.objectName()} le van tiltva"
    assert elem.width() > 0 and elem.height() > 0, (
        f"{elem.objectName()} nem kattintható"
    )
    kozep = elem.mapToScene(QPointF(elem.width() / 2, elem.height() / 2))
    QTest.mouseClick(
        ablak,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        kozep.toPoint(),
    )
    qt_app.processEvents()


def _asztal_parancs(ablak, qt_app):
    menu_sav = ablak.property("menuBar")
    create = next(
        item
        for item in menu_sav.findChildren(QObject)
        if "MenuBarItem" in item.metaObject().className()
        and item.property("text") == "&Create"
    )
    _kattint(ablak, create, qt_app)
    parancs = _elem(ablak, "menuCreateWallpaper")
    assert varj_feltetelre(
        qt_app, lambda: parancs.property("visible") is True, 3.0
    ), "a Create menü háttérbeállító parancsa nem jelent meg"
    _kattint(ablak, parancs, qt_app)


def _uj_parbeszed(ablak, qt_app):
    dialog = ablak.findChild(QObject, "wallpaperConfirmDialog")
    assert dialog is not None, "a háttérbeállító megerősítő párbeszéd hiányzik"
    assert varj_feltetelre(
        qt_app, lambda: dialog.property("visible") is True, 3.0
    ), "a háttérbeállítás parancs nem nyitotta meg a megerősítést"
    return dialog


@pytest.mark.parametrize("height_delta", [-5, 0, 5])
def test_no_nem_valtoztat_semmit(qml_app, qt_app, monkeypatch, height_delta):
    from picasapy.app import wallpaper

    ablak, _controller, _engine = qml_app
    celmagassag = ablak.height() + height_delta
    ablak.resize(ablak.width(), celmagassag)
    assert varj_feltetelre(qt_app, lambda: ablak.height() == celmagassag, 3.0)
    ablak.setProperty("selectedIndexes", [0])
    ablak.setProperty("selectedIndex", 0)
    qt_app.processEvents()

    beallitasok = []
    monkeypatch.setattr(
        wallpaper,
        "set_desktop_background",
        lambda bmp: beallitasok.append(bmp) or "teszteszköz",
    )
    banner = _elem(ablak, "errorBannerText")
    banner_elotte = banner.property("text")
    _asztal_parancs(ablak, qt_app)

    dialog = _uj_parbeszed(ablak, qt_app)
    assert dialog.property("title") == "Confirm"
    assert _elem(dialog, "wallpaperConfirmMessageLabel").property("text") == _KERDES
    assert _elem(dialog, "wallpaperConfirmYesButton").property("text") == "Set Desktop"
    assert _elem(dialog, "wallpaperConfirmNoButton").property("text") == "No"
    assert dialog.property("cancelVisible") is False
    assert dialog.property("rememberVisible") is False
    _kattint(ablak, _elem(dialog, "wallpaperConfirmNoButton"), qt_app)

    assert beallitasok == [], "a No ág meghívta az asztalbeállítót"
    assert banner.property("text") == banner_elotte, "a No ág megváltoztatta a visszajelzést"


@pytest.mark.parametrize("height_delta", [-5, 0, 5])
def test_set_desktop_a_megerosites_utan_beallitja(qml_app, qt_app, monkeypatch, height_delta):
    from picasapy.app import wallpaper

    ablak, _controller, _engine = qml_app
    celmagassag = ablak.height() + height_delta
    ablak.resize(ablak.width(), celmagassag)
    assert varj_feltetelre(qt_app, lambda: ablak.height() == celmagassag, 3.0)
    ablak.setProperty("selectedIndexes", [0])
    ablak.setProperty("selectedIndex", 0)
    qt_app.processEvents()

    beallitasok = []
    monkeypatch.setattr(
        wallpaper,
        "set_desktop_background",
        lambda bmp: beallitasok.append(bmp) or "teszteszköz",
    )
    _asztal_parancs(ablak, qt_app)
    dialog = _uj_parbeszed(ablak, qt_app)
    yes = _elem(dialog, "wallpaperConfirmYesButton")
    assert varj_feltetelre(qt_app, lambda: yes.property("activeFocus") is True, 3.0), (
        "a Set Desktop gomb nem kapta meg a kezdeti fókuszt"
    )
    _kattint(ablak, yes, qt_app)

    assert len(beallitasok) == 1, "a Set Desktop ág nem egyszer állította be a hátteret"
    assert beallitasok[0].is_file(), "az aktuális háttérmásolat nem készült el"
