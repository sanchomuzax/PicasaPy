"""#7231: az Eszközök menü nézőfüggő állapotai valódi menünyitással."""

from __future__ import annotations

import pytest
from PySide6.QtCore import Q_ARG, QMetaObject, QObject, Qt

from tests.app.qml_functional._fomenu_4420_menu import _megnyit
from tests.app.qml_functional._felsomenupontok_helpers_4329 import _objektum
from tests.support.varakozas import var_feltetelre


_ABLAKMAGASSAG_ELTOLASOK = (-5, 0, 5)


def _elem_nevvel(window, nev: str):
    elem = _objektum(window, nev)
    assert elem is not None, f"{nev} menüpont nem található"
    return elem


def _elem_felirattal(menu, felirat: str, *, retired: bool = False):
    talalatok = [
        elem
        for elem in menu.findChildren(QObject)
        if elem.property("text") == felirat
        and (not retired or elem.property("retired") is True)
    ]
    assert len(talalatok) == 1, (
        f"a(z) {felirat!r} menüpontból {len(talalatok)} található"
    )
    return talalatok[0]


def _almenu_felirattal(menu, felirat: str):
    talalatok = [
        elem
        for elem in menu.findChildren(QObject)
        if elem.property("title") == felirat
        and elem.property("opened") is not None
    ]
    assert len(talalatok) == 1, (
        f"a(z) {felirat!r} almenüből {len(talalatok)} található"
    )
    return talalatok[0]


@pytest.mark.parametrize("viewer_open", (False, True), ids=("konyvtar", "nezo"))
@pytest.mark.parametrize("magassag_eltolas", _ABLAKMAGASSAG_ELTOLASOK)
def test_tools_menu_allapotai_nezoben_es_konyvtarban(
    qml_app, qt_app, viewer_open: bool, magassag_eltolas: int
):
    window, _controller, _engine = qml_app
    window.show()
    window.requestActivate()
    window.setHeight(window.height() + magassag_eltolas)
    window.setProperty("selectedIndexes", [0])
    window.setProperty("selectedIndex", 0)
    qt_app.processEvents()

    if viewer_open:
        window.setProperty("viewerOpen", True)
        viewer = _elem_nevvel(window, "photoViewer")
        assert QMetaObject.invokeMethod(
            viewer,
            "show",
            Qt.ConnectionType.DirectConnection,
            Q_ARG("QVariant", 0),
        ), "a fotónéző nem nyitható meg"
        assert var_feltetelre(
            qt_app,
            lambda: window.property("viewerOpen") is True
            and viewer.property("visible") is True,
            3.0,
        ), "az egyképes néző nem nyílt meg"
    else:
        assert window.property("viewerOpen") is False

    menu_bar = window.property("menuBar")
    tools_menu = _megnyit(menu_bar, qt_app, "&Tools")
    assert tools_menu.property("opened") is True, (
        "a Tools menü valódi megnyitása nem sikerült"
    )

    elemek = {
        "Folder Manager": _elem_nevvel(window, "menuToolsFolderManager"),
        "Upload Manager": _elem_felirattal(
            tools_menu, "&Upload Manager...", retired=True
        ),
        "Configure Photo Viewer": _elem_nevvel(
            window, "menuToolsPhotoViewerSettings"
        ),
        "Configure Screensaver": _elem_nevvel(window, "menuToolsScreensaver"),
        "Back Up Pictures": _elem_nevvel(window, "menuToolsBackup"),
        "Batch Upload": _elem_felirattal(
            tools_menu, "Batch Upload...", retired=True
        ),
        "People Manager": _elem_nevvel(window, "menuToolsPeopleManager"),
        "Adjust Date and Time": _elem_nevvel(
            window, "menuToolsAdjustTimestamp"
        ),
        "Upload": _almenu_felirattal(tools_menu, "U&pload"),
        "Geotag": _almenu_felirattal(tools_menu, "&Geotag"),
        "Experimental": _elem_nevvel(window, "menuToolsExperimental"),
        "Configure Buttons": _elem_nevvel(window, "menuConfigureButtons"),
        "Options": _elem_nevvel(window, "menuToolsOptions"),
    }
    assert all(elem.property("visible") is True for elem in list(elemek.values())[:6]), (
        "a hat vizsgált Tools-menütétel nem látható a megnyitott menüben"
    )

    tenyleges = {
        nev: elem.property("enabled") for nev, elem in elemek.items()
    }
    elvart = {
        "Folder Manager": not viewer_open,
        "Upload Manager": False,
        "Configure Photo Viewer": not viewer_open,
        "Configure Screensaver": not viewer_open,
        "Back Up Pictures": not viewer_open,
        "Batch Upload": False,
        "People Manager": True,
        "Adjust Date and Time": True,
        "Upload": True,
        "Geotag": True,
        "Experimental": True,
        "Configure Buttons": True,
        "Options": True,
    }
    assert tenyleges == elvart, (
        f"viewerOpen={viewer_open}: Tools-menü állapotai eltérnek; "
        f"tényleges={tenyleges}, elvárt={elvart}"
    )

