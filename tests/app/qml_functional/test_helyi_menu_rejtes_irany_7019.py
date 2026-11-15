"""Valódi kattintásos QML-teszt a helyi menü Elrejtés és Megjelenítés tételének irányára (#7019).

A helyi menü (PhotoContextMenu, ViewerContextMenu) tételének felirata szerinti irány
hat a teljes kijelölésre:
- Vegyes kijelölésnél a rejtett képre jobbklikkelve az „Unhide” / „Megjelenítés”
  mindkét képet megjeleníti (a látható képet nem rejti el).
- Vegyes kijelölésnél a látható képre jobbklikkelve a „Hide” / „Elrejtés”
  mindkét képet elrejti.
- A néző helyi menüje a felirata szerinti irányba hat.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import Qt

from picasapy.ini import load_document
from tests.app.qml_functional._mappa_kep_menu_5150_helpers import (
    app_epitese,
)
from tests.app.qml_functional._racs_helyimenuk_5150_helpers import (
    elokeszit_str,
    gyerek,
    jobbklikk_fotón,
    kattints,
    kijelol,
    varj,
)


@pytest.fixture
def mappa_app(qt_app, tmp_path):
    yield from app_epitese(qt_app, tmp_path)


def _nezo_nyit(window, qt_app, sor: int = 0) -> None:
    window.setProperty("viewerOpen", True)
    gyerek(window, "photoViewer").setProperty("currentIndex", sor)
    qt_app.processEvents()


def _nezo_jobbklikk(window, qt_app):
    kattints(window, qt_app, gyerek(window, "photoViewer"), Qt.MouseButton.RightButton)
    menu = gyerek(window, "viewerContextMenu")
    assert varj(qt_app, lambda: menu.property("opened") is True), (
        "a néző közepén végzett valódi jobbklikk nem nyitotta meg a helyi menüt"
    )
    return menu


def _ini_hidden_ertek(controller, sor: int) -> str | None:
    foto = controller.photos.photos[sor]
    ini_path = Path(foto.folder_path) / ".picasa.ini"
    if not ini_path.exists():
        return None
    doc = load_document(ini_path)
    sec = doc.section(foto.name)
    return None if sec is None else sec.get("hidden")


@pytest.mark.parametrize("magassag_delta", [-5, 0, 5])
def test_racs_helyi_menu_vegyes_kijelolesnel_rejtettre_jobbklikkelve_megjelenit_mindet(
    mappa_app, qt_app, magassag_delta
):
    """Vegyes kijelölésnél (sor 0 rejtett, sor 1 látható) a rejtett képre jobbklikkelve

    a „Megjelenítés” mindkét képet megjeleníti (a látható képet nem rejti el).
    """
    window, controller, _motor = mappa_app
    window.resize(window.width(), window.height() + magassag_delta)
    qt_app.processEvents()
    elokeszit_str(window, qt_app, controller)

    # Elrejtjük a 0. képet, majd bekapcsoljuk a rejtett képek mutatását
    controller.toggleHiddenRows([0])
    controller.setShowHidden(True)
    qt_app.processEvents()

    assert varj(qt_app, lambda: controller.photos.itemAt(0)["hidden"] is True)
    assert varj(qt_app, lambda: controller.photos.itemAt(1)["hidden"] is False)
    assert _ini_hidden_ertek(controller, 0) == "yes"
    assert _ini_hidden_ertek(controller, 1) is None

    # Vegyes kijelölés: mindkét kép kijelölve
    kijelol(window, qt_app, [0, 1])

    # Jobbklikk a rejtett képen (sor 0)
    menu = jobbklikk_fotón(window, qt_app, 0)
    assert menu.property("hideChecked") is True

    item = gyerek(window, "contextMenuHide")
    assert item.property("text") == "Megjelenítés" or item.property("text") == "Unhide"

    # Kattintás a Megjelenítés tételen
    kattints(window, qt_app, item)

    # Elvárt: mindkét kép látható lesz, egyik sem maradhat rejtett
    assert varj(
        qt_app,
        lambda: _ini_hidden_ertek(controller, 0) is None
        and _ini_hidden_ertek(controller, 1) is None,
    ), "a Megjelenítés kattintás nem jelenítette meg mindkét képet (.picasa.ini hiba)"


def test_racs_helyi_menu_vegyes_kijelolesnel_lathatora_jobbklikkelve_elrejt_mindet(
    mappa_app, qt_app
):
    """Vegyes kijelölésnél (sor 0 rejtett, sor 1 látható) a látható képre jobbklikkelve

    az „Elrejtés” mindkét képet elrejti.
    """
    window, controller, _motor = mappa_app
    elokeszit_str(window, qt_app, controller)

    # Elrejtjük a 0. képet, majd bekapcsoljuk a rejtett képek mutatását
    controller.toggleHiddenRows([0])
    controller.setShowHidden(True)
    qt_app.processEvents()

    assert varj(qt_app, lambda: controller.photos.itemAt(0)["hidden"] is True)
    assert varj(qt_app, lambda: controller.photos.itemAt(1)["hidden"] is False)
    assert _ini_hidden_ertek(controller, 0) == "yes"
    assert _ini_hidden_ertek(controller, 1) is None

    # Vegyes kijelölés: mindkét kép kijelölve
    kijelol(window, qt_app, [0, 1])

    # Jobbklikk a látható képen (sor 1)
    menu = jobbklikk_fotón(window, qt_app, 1)
    assert menu.property("hideChecked") is False

    item = gyerek(window, "contextMenuHide")
    assert item.property("text") == "Elrejtés" or item.property("text") == "Hide"

    # Kattintás az Elrejtés tételen
    kattints(window, qt_app, item)

    # Elvárt: mindkét kép rejtett lesz
    assert varj(
        qt_app,
        lambda: _ini_hidden_ertek(controller, 0) == "yes"
        and _ini_hidden_ertek(controller, 1) == "yes",
    ), "az Elrejtés kattintás nem rejtette el mindkét képet (.picasa.ini hiba)"


def test_nezo_helyi_menu_rejtett_kepen_megjelenit(mappa_app, qt_app):
    """A néző helyi menüje a felirata szerinti irányba hat:

    rejtett képen a Megjelenítés tétel megjeleníti a képet.
    """
    window, controller, _motor = mappa_app
    elokeszit_str(window, qt_app, controller)

    # Elrejtjük a 0. képet, bekapcsoljuk a mutatást
    controller.toggleHiddenRows([0])
    controller.setShowHidden(True)
    qt_app.processEvents()
    assert _ini_hidden_ertek(controller, 0) == "yes"

    # Megnyitjuk a nézőt a 0. képre
    _nezo_nyit(window, qt_app, 0)
    menu = _nezo_jobbklikk(window, qt_app)
    assert menu.property("hidden") is True

    item = gyerek(window, "viewerMenuHide")
    assert item.property("text") == "Megjelenítés" or item.property("text") == "Unhide"

    # Kattintás a Megjelenítés tételen
    kattints(window, qt_app, item)

    # Elvárt: a kép megjelenik (.picasa.ini hidden kulcs törlődik)
    assert varj(
        qt_app, lambda: _ini_hidden_ertek(controller, 0) is None
    ), "a nézőben a Megjelenítés kattintás nem vette le a hidden=yes kulcsot"
