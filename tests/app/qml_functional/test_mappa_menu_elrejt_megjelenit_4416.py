"""#4416: a Felső Mappa menü rejtése és visszaállítása valóban működik."""

from __future__ import annotations

import time

import pytest
from PySide6.QtCore import QObject, QPoint, QPointF, Qt
from PySide6.QtTest import QTest


_ABLAKMAGASSAG_ELTOLASOK = (-5, 0, 5)


def _varj(qt_app, feltetel, masodperc: float = 3.0) -> bool:
    hatarido = time.monotonic() + masodperc
    while time.monotonic() < hatarido:
        qt_app.processEvents()
        if feltetel():
            return True
        time.sleep(0.01)
    qt_app.processEvents()
    return bool(feltetel())


def _objektum(window, nev):
    menu_bar = window.property("menuBar")
    for gyoker in (window, menu_bar):
        if gyoker is not None:
            elem = gyoker.findChild(QObject, nev)
            if elem is not None:
                return elem
    return None


def _kattints(qt_app, elem) -> None:
    assert elem is not None, "a kattintandó felületi elem hiányzik"
    assert elem.isEnabled(), f"{elem.objectName()}: a művelet le van tiltva"
    center = elem.mapToScene(QPointF(elem.width() / 2, elem.height() / 2))
    QTest.mouseClick(
        elem.window(),
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        QPoint(round(center.x()), round(center.y())),
    )
    qt_app.processEvents()


def _nyisd_meg_mappa_menut(qt_app, window, tetel_nev):
    menu_bar = window.property("menuBar")
    assert menu_bar is not None
    mappa_cimek = {"F&older", "&Folder", "&Mappa"}
    menu = next(
        (
            item
            for item in menu_bar.findChildren(QObject)
            if item.property("title") in mappa_cimek
        ),
        None,
    )
    fejlec = next(
        (
            item
            for item in menu_bar.findChildren(QObject)
            if "MenuBarItem" in item.metaObject().className()
            and item.property("text") in mappa_cimek
        ),
        None,
    )
    assert menu is not None, "a felső Mappa menü nem található"
    assert fejlec is not None, "a felső Mappa menü fejléce nem található"
    _kattints(qt_app, fejlec)
    assert _varj(
        qt_app,
        lambda: menu.property("opened") is True
        and _objektum(window, tetel_nev) is not None
        and _objektum(window, tetel_nev).property("visible") is True,
    ), f"a {tetel_nev} tétel nem jelent meg a megnyitott menüben"
    return menu_bar, menu, fejlec, _objektum(window, tetel_nev)


def _magassag(window, offset: int) -> None:
    window.setHeight(window.height() + offset)


def _ertek(value):
    return value.toVariant() if hasattr(value, "toVariant") else value


@pytest.mark.parametrize("height_offset", _ABLAKMAGASSAG_ELTOLASOK)
def test_mappa_menu_elrejt_es_megjelenit_valodi_kattintassal(
    qml_app, qt_app, height_offset
):
    """A menüsor ugyanazt az indexállapotot váltja, mint a helyi menü."""
    window, controller, _engine = qml_app
    _magassag(window, height_offset)
    controller.setShowHidden(True)
    mappa = controller.currentFolder
    assert mappa
    assert controller.isFolderHidden(mappa) is False

    _menu_bar, _menu, _fejlec, hide = _nyisd_meg_mappa_menut(
        qt_app, window, "menuFolderHide"
    )
    assert hide.property("enabled") is True
    _kattints(qt_app, hide)
    assert _varj(qt_app, lambda: controller.isFolderHidden(mappa) is True), (
        "a Mappa ▸ Hide kattintás nem rejtette el a kijelölt mappát"
    )

    _menu_bar, _menu, _fejlec, show = _nyisd_meg_mappa_menut(
        qt_app, window, "menuFolderShow"
    )
    assert show.property("enabled") is True
    _kattints(qt_app, show)
    assert _varj(qt_app, lambda: controller.isFolderHidden(mappa) is False), (
        "a Mappa ▸ Show kattintás nem állította vissza a kijelölt mappát"
    )


@pytest.mark.parametrize("height_offset", _ABLAKMAGASSAG_ELTOLASOK)
def test_mappa_menu_engedeje_megegyezik_a_helyi_menu_feltetelevel(
    qml_app, qt_app, height_offset
):
    window, controller, _engine = qml_app
    _magassag(window, height_offset)
    helyi_menu = _objektum(window, "folderContextMenu")
    helyi_hide = _objektum(window, "folderMenuHideFolder")
    assert helyi_menu is not None and helyi_hide is not None

    mappa = controller.currentFolder
    assert mappa
    helyi_menu.setProperty("folderPath", mappa)
    qt_app.processEvents()
    _menu_bar, _menu, _fejlec, helyi_hide_mappa = _nyisd_meg_mappa_menut(
        qt_app, window, "menuFolderHide"
    )
    helyi_show_mappa = _objektum(window, "menuFolderShow")
    assert _ertek(helyi_hide_mappa.property("enabled")) == _ertek(
        helyi_hide.property("enabled")
    )
    assert _ertek(helyi_show_mappa.property("enabled")) == _ertek(
        helyi_hide.property("enabled")
    )

    controller.selectFolder("")
    helyi_menu.setProperty("folderPath", "")
    qt_app.processEvents()
    assert _varj(
        qt_app,
        lambda: _ertek(helyi_hide_mappa.property("enabled"))
        == _ertek(helyi_hide.property("enabled")),
    )
    assert _ertek(helyi_hide_mappa.property("enabled")) is False
    assert _ertek(helyi_show_mappa.property("enabled")) is False
