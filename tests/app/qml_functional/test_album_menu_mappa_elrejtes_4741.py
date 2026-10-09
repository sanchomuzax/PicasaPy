"""#4741: az Album menü ne rejthesse el az előzőleg nézett mappát."""

from __future__ import annotations

import time

from PySide6.QtCore import QObject, QPoint, QPointF, Qt
from PySide6.QtTest import QTest


_ALBUM_TOKEN = "604c294a68b0de9cc9222c4714f289d5"
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
    for gyoker in (window, window.property("menuBar")):
        if gyoker is not None:
            elem = gyoker.findChild(QObject, nev)
            if elem is not None:
                return elem
    return None


def _kattints(qt_app, elem) -> None:
    """Valódi egérkattintás, a QML-elem pillanatnyi helyén."""
    assert elem is not None, "a kattintandó menüelem hiányzik"
    kozep = elem.mapToScene(QPointF(elem.width() / 2, elem.height() / 2))
    QTest.mouseClick(
        elem.window(),
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        QPoint(round(kozep.x()), round(kozep.y())),
    )
    qt_app.processEvents()


def _nyisd_meg_menu_tetelt(qt_app, window, tetel_nev):
    menu_bar = window.property("menuBar")
    assert menu_bar is not None, "a menüsáv nem található"
    album_cimek = {"&Album"}
    mappa_cimek = {"F&older", "&Folder", "&Mappa"}
    menu_cimek = (
        album_cimek
        if menu_bar.property("currentAlbumToken")
        else mappa_cimek
    )
    menu = next(
        (
            item
            for item in menu_bar.findChildren(QObject)
            if item.property("title") in menu_cimek
        ),
        None,
    )
    assert menu is not None, "a Mappa/Album menü nem található"
    fejlec = next(
        (
            item
            for item in menu_bar.findChildren(QObject)
            if "MenuBarItem" in item.metaObject().className()
            and item.property("text") in menu_cimek
        ),
        None,
    )
    assert fejlec is not None, "a Mappa/Album menü fejléce nem található"
    if menu.property("opened") is not True:
        _kattints(qt_app, fejlec)

    assert _varj(
        qt_app,
        lambda: menu.property("opened") is True
        and _objektum(window, tetel_nev) is not None
        and _objektum(window, tetel_nev).property("visible") is True,
    ), f"a {tetel_nev} tétel nem jelent meg a megnyitott menüben"
    return menu_bar, menu, fejlec, _objektum(window, tetel_nev)


def _kattints_menutetelre(qt_app, window, tetel_nev):
    hivatkozasok = _nyisd_meg_menu_tetelt(qt_app, window, tetel_nev)
    elem = hivatkozasok[-1]
    _kattints(qt_app, elem)
    return hivatkozasok


def test_album_es_szemelynezetben_a_mapparejtes_menupontok_nem_mukodnek(
    qml_app, qt_app
):
    window, controller, _engine = qml_app
    alapmagassag = int(window.height())
    controller.setShowHidden(True)
    mappa = controller.currentFolder
    assert mappa, "a próba mappanézetből indul"

    for eltolás in _ABLAKMAGASSAG_ELTOLASOK:
        window.setHeight(alapmagassag + eltolás)
        assert _varj(
            qt_app,
            lambda eltolás=eltolás: window.height() == alapmagassag + eltolás,
        ), (
            f"a főablak magassága nem állt be ({eltolás:+} px)"
        )

        # Mappanézetben mindkét valódi kattintás továbbra is a kijelölt
        # mappát rejti el, illetve állítja vissza.
        assert controller.isFolderHidden(mappa) is False
        _menu_bar, _menu, _fejlec, hide = _nyisd_meg_menu_tetelt(
            qt_app, window, "menuFolderHide"
        )
        assert hide.property("enabled") is True
        _kattints(qt_app, hide)
        assert _varj(qt_app, lambda: controller.isFolderHidden(mappa) is True), (
            "mappanézetben az Elrejtés kattintás nem rejtette el a kijelölt mappát"
        )

        _menu_bar, _menu, _fejlec, show = _nyisd_meg_menu_tetelt(
            qt_app, window, "menuFolderShow"
        )
        assert show.property("enabled") is True
        _kattints(qt_app, show)
        assert _varj(qt_app, lambda: controller.isFolderHidden(mappa) is False), (
            "mappanézetben a Megjelenítés kattintás nem állította vissza a mappát"
        )

        # Album nézetben a régi mappaútvonal megmarad, de egyik menükattintás
        # sem változtathatja meg annak rejtett állapotát.
        controller.showAlbum(_ALBUM_TOKEN)
        assert _varj(qt_app, lambda: controller.currentAlbumToken == _ALBUM_TOKEN)
        assert controller.currentFolder == mappa
        assert controller.isFolderHidden(mappa) is False
        _menu_bar, _menu, _fejlec, hide = _kattints_menutetelre(
            qt_app, window, "menuFolderHide"
        )
        assert hide.property("enabled") is False
        assert controller.isFolderHidden(mappa) is False, (
            "az Album ▸ Elrejtés kattintás elrejtette a korábbi mappát"
        )

        controller.toggleFolderHidden(mappa)
        assert controller.isFolderHidden(mappa) is True
        _menu_bar, _menu, _fejlec, show = _kattints_menutetelre(
            qt_app, window, "menuFolderShow"
        )
        assert show.property("enabled") is False
        assert controller.isFolderHidden(mappa) is True, (
            "az Album ▸ Megjelenítés kattintás visszaállította a korábbi mappát"
        )

        # A személynézet ugyanazt a mappakontextust őrzi meg, ezért mindkét
        # menüpontnak itt is letiltva kell maradnia kattintás közben.
        controller.toggleFolderHidden(mappa)
        assert controller.isFolderHidden(mappa) is False
        controller.showPerson("Anna")
        assert _varj(qt_app, lambda: controller.currentPersonName == "Anna")
        assert controller.currentFolder == mappa
        _menu_bar, _menu, _fejlec, hide = _kattints_menutetelre(
            qt_app, window, "menuFolderHide"
        )
        assert hide.property("enabled") is False
        assert controller.isFolderHidden(mappa) is False, (
            "személynézetben az Elrejtés kattintás elrejtette a korábbi mappát"
        )

        controller.toggleFolderHidden(mappa)
        assert controller.isFolderHidden(mappa) is True
        _menu_bar, _menu, _fejlec, show = _kattints_menutetelre(
            qt_app, window, "menuFolderShow"
        )
        assert show.property("enabled") is False
        assert controller.isFolderHidden(mappa) is True, (
            "személynézetben a Megjelenítés kattintás visszaállította a korábbi mappát"
        )

        controller.clearFilter()
        assert _varj(qt_app, lambda: controller.currentAlbumToken == "")
        assert _varj(qt_app, lambda: controller.currentPersonName == "")
        assert controller.currentFolder == mappa
        assert controller.isFolderHidden(mappa) is True
        controller.toggleFolderHidden(mappa)
        assert controller.isFolderHidden(mappa) is False
