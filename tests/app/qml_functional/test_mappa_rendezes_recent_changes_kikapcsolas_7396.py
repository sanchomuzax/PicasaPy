"""#7396: A Mappa ▸ Rendezés ▸ Legutóbbi változtatások be- és kikapcsolása kattintással."""

from __future__ import annotations

import os
import time
from pathlib import Path

import pytest

from support.jpeg_factory import make_jpeg
from tests.app.qml_functional._felsomenupontok_helpers_4329 import (
    _kattints,
    _objektum,
)
from tests.app.qml_functional._fomenu_4420_menu import _megnyit
from tests.app.qml_functional._mappa_kep_menu_5150_helpers import (
    app_epitese,
    elokeszit,
    varj,
)
from tests.app.qml_functional._nezet_menu_5150_helpers import almenu_sora


def keszits_harom_kulonbozo_mappat(lib: Path) -> None:
    """Három mappa: alma, mokus, zebra.

    Névsorrend: alma, mokus, zebra.
    Dátumsorrend (legújabb elöl): mokus (2024), zebra (2022), alma (2020).
    Módosítás ideje (legfrissebb elöl): zebra (2025), mokus (2024), alma (2020).
    A három sorrend szándékosan különbözik.
    """
    for folder, taken, changed in (
        ("alma", "2020:01:01 10:00:00", (2020, 3, 1, 12, 0, 0)),
        ("mokus", "2024:01:01 10:00:00", (2024, 11, 1, 12, 0, 0)),
        ("zebra", "2022:01:01 10:00:00", (2025, 5, 1, 12, 0, 0)),
    ):
        mappa = lib / folder
        mappa.mkdir(parents=True)
        photo = mappa / "IMG_0001.jpg"
        make_jpeg(photo, taken_at=taken)
        stamp = time.mktime((*changed, 0, 0, -1))
        os.utime(photo, (stamp, stamp))


@pytest.fixture
def mappa_app_harom(qt_app, tmp_path):
    yield from app_epitese(
        qt_app, tmp_path, kepeket_keszit=keszits_harom_kulonbozo_mappat
    )


def _rendezesi_almenu_nyitasa(window, qt_app):
    menu_bar = window.property("menuBar")
    folder_menu = _megnyit(menu_bar, qt_app, "F&older")
    sor, almenu = almenu_sora(window, folder_menu, "menuFolderSortBy")
    _kattints(qt_app, sor)
    assert varj(qt_app, lambda: almenu.property("opened") is True), (
        "a Mappa ▸ Sort By almenü nem nyílt meg"
    )
    return almenu


def _feed_folder_names(controller) -> list[str]:
    seen: list[str] = []
    for photo in controller.photos.photos:
        nev = Path(photo.folder_path).name
        if nev not in seen:
            seen.append(nev)
    return seen


@pytest.mark.parametrize("magassag_elteres", [-5, 0, 5])
def test_legutobbi_valtoztatasok_kattintassal_kikapcsolhato(
    mappa_app_harom, qt_app, magassag_elteres
):
    window, controller, _engine = mappa_app_harom
    window.show()
    window.resize(window.width(), window.height() + magassag_elteres)
    window.requestActivate()
    qt_app.processEvents()
    elokeszit(window, qt_app, controller)

    # 1. Kezdetben a bal hasáb alapértelmezett (dátum: mokus, zebra, alma).
    # A rács mappasorrendje megegyezik a hasábéval.
    controller.setPaneSort("date")
    hasab_kezd = [Path(p).name for p in controller.folders.folder_paths()]
    assert hasab_kezd == ["mokus", "zebra", "alma"]
    assert _feed_folder_names(controller) == hasab_kezd

    # 2. Megnyitjuk a menüt: a Recent changes nincs bepipálva.
    _rendezesi_almenu_nyitasa(window, qt_app)
    changed = _objektum(window, "menuFolderSortByChanged")
    assert changed is not None
    assert changed.property("checkable") is True
    assert changed.property("checked") is False

    # 3. Első kattintás: bekapcsolás.
    _kattints(qt_app, changed)
    assert controller.folderSort == "changed"
    assert controller._get_settings().value("view/folderSort") == "changed"
    # A rács sorrendje átváltott a változtatási időre (zebra, mokus, alma)
    assert _feed_folder_names(controller) == ["zebra", "mokus", "alma"]

    # 4. Újra megnyitjuk a menüt: a pipának ott kell lennie.
    _rendezesi_almenu_nyitasa(window, qt_app)
    changed = _objektum(window, "menuFolderSortByChanged")
    assert changed.property("checked") is True

    # 5. Második kattintás: KIKAPCSOLÁS (#7396).
    _kattints(qt_app, changed)
    assert controller.folderSort != "changed"
    assert controller.folderSort == "date"
    assert controller._get_settings().value("view/folderSort") != "changed"

    # A rács mappasorrendje újra megegyezik a hasábéval!
    assert _feed_folder_names(controller) == hasab_kezd

    # 6. Menü újbóli megnyitása: a pipa eltűnt!
    _rendezesi_almenu_nyitasa(window, qt_app)
    changed = _objektum(window, "menuFolderSortByChanged")
    assert changed.property("checked") is False


def test_pane_sort_valtoztatas_kikapcsolja_a_changed_modot(
    mappa_app_harom, qt_app
):
    window, controller, _engine = mappa_app_harom
    window.show()
    window.requestActivate()
    qt_app.processEvents()
    elokeszit(window, qt_app, controller)

    # Bekapcsoljuk a changed módot kattintással
    _rendezesi_almenu_nyitasa(window, qt_app)
    changed = _objektum(window, "menuFolderSortByChanged")
    _kattints(qt_app, changed)
    assert controller.folderSort == "changed"

    # A hasáb rendezését átállítjuk név szerinti sorrendre (setPaneSort)
    controller.setPaneSort("name")
    assert controller.folderSort != "changed"
    assert controller.folderSort == "date"
    assert controller._get_settings().value("view/folderSort") != "changed"

    # A hasáb és a rács egyaránt a névsort mutatja
    hasab = [Path(p).name for p in controller.folders.folder_paths()]
    assert hasab == ["alma", "mokus", "zebra"]
    assert _feed_folder_names(controller) == hasab

    # És a menüben sem maradt pipa
    _rendezesi_almenu_nyitasa(window, qt_app)
    changed = _objektum(window, "menuFolderSortByChanged")
    assert changed.property("checked") is False
