"""A tálca Album menüjének különleges céljai (#5846)."""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import QObject, QPoint, QPointF, Qt
from PySide6.QtQuick import QQuickItem
from PySide6.QtTest import QTest

from conftest import _build_qml_app
from tests.support.jpeg_factory import make_minta_jpeg
from tests.support.varakozas import hibaturo_feltetel, var_feltetelre


def _kepeket_keszit(mappa: Path) -> None:
    make_minta_jpeg(mappa / "a.jpg", size=(640, 400), seed=2)
    make_minta_jpeg(mappa / "b.jpg", size=(500, 500), seed=5)


@pytest.fixture
def tray_app(qt_app, tmp_path, request):
    yield from _build_qml_app(
        qt_app,
        tmp_path,
        kepeket_keszit=_kepeket_keszit,
        belyegkep_meret=256,
        valodi_belyegkep=True,
        keep_modul=request.module,
    )


def _varj(qt_app, condition, seconds: float = 10.0) -> bool:
    return var_feltetelre(qt_app, hibaturo_feltetel(condition), seconds)


def _elem(parent, name: str, item_type=QObject):
    item = parent.findChild(item_type, name)
    assert item is not None, f"{name} nem található"
    return item


def _kattints(qt_app, item) -> None:
    assert item.isVisible() and item.width() > 0 and item.height() > 0, (
        f"{item.objectName()}: nem látszik, nem kattintható"
    )
    center = item.mapToScene(QPointF(item.width() / 2, item.height() / 2))
    QTest.mouseClick(
        item.window(),
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        QPoint(round(center.x()), round(center.y())),
    )
    qt_app.processEvents()


def _kijelol(window, qt_app, controller) -> int:
    row = int(controller.photos.rowOfPath(str(Path(controller.currentFolder) / "a.jpg")))
    assert row >= 0
    window.setProperty("selectedIndexes", [row])
    window.setProperty("selectedIndex", row)
    assert _varj(qt_app, lambda: controller.heldCount == 1), (
        "a kijelölt kép nem került a tálcára"
    )
    return row


def _menu_nyitasa(window, qt_app):
    button = _elem(window, "trayAddToButton", QQuickItem)
    assert button.property("enabled") is True, (
        "saját album nélkül, kijelölt képpel is engedélyezni kell a gombot"
    )
    _kattints(qt_app, button)
    menu = _elem(window, "trayAddToMenu")
    assert _varj(qt_app, lambda: menu.property("opened") is True), (
        "a tálca albumgombja nem nyitotta meg a menüt"
    )
    return menu


def _specialis_sorok(window):
    return [
        _elem(window, "trayAddToScreensaverItem", QQuickItem),
        _elem(window, "trayAddToStarredPhotosItem", QQuickItem),
        _elem(window, "trayAddToNewAlbumItem", QQuickItem),
    ]


@pytest.mark.parametrize("height_offset", [-5, 0, 5])
def test_sajat_album_nelkul_a_harom_kulonleges_cel_sorrendben_latszik_es_rajta_a_menukep(
    tray_app, qt_app, tmp_path, height_offset
):
    window, controller, _engine = tray_app
    assert controller.albums == []
    _kijelol(window, qt_app, controller)

    target_height = window.height() + height_offset
    window.setHeight(target_height)
    assert _varj(qt_app, lambda: window.height() == target_height)
    menu = _menu_nyitasa(window, qt_app)

    rows = _specialis_sorok(window)
    assert [str(row.property("text")) for row in rows] == [
        "Screensaver",
        "Starred Photos",
        "New Album...",
    ]
    y_positions = [row.mapToScene(QPointF(0, 0)).y() for row in rows]
    assert y_positions == sorted(y_positions), (
        "a különleges célok felületi sorrendje eltér"
    )
    button = _elem(window, "trayAddToButton", QQuickItem)
    button_top_left = button.mapToScene(QPointF(0, 0))
    last_bottom = rows[-1].mapToScene(QPointF(0, rows[-1].height())).y()
    assert last_bottom <= button_top_left.y() + 1, (
        "a menü nem a gomb fölött nyílik (felfelé nyíló menü)"
    )
    assert abs(rows[0].mapToScene(QPointF(0, 0)).x() - button_top_left.x()) < 40, (
        "a menü vízszintesen nem a gombhoz igazodik"
    )

    if height_offset == 0:
        screenshot = rows[0].window().grabWindow()
        assert not screenshot.isNull(), "az Album menü képkockája üres"
        output = tmp_path / "5846-tray-add-to-menu.png"
        assert screenshot.save(str(output), "PNG"), (
            "az Album menü kiadásképe nem menthető"
        )

    assert menu.property("opened") is True


def test_starred_photos_a_kijelolt_kepet_csillagozza(tray_app, qt_app):
    window, controller, _engine = tray_app
    _kijelol(window, qt_app, controller)
    _menu_nyitasa(window, qt_app)
    _kattints(qt_app, _elem(window, "trayAddToStarredPhotosItem", QQuickItem))

    ini_path = Path(controller.currentFolder) / ".picasa.ini"
    assert _varj(qt_app, lambda: ini_path.is_file() and "star=yes" in ini_path.read_text(
        encoding="utf-8"
    )), "a Starred Photos kattintása nem írt star=yes értéket az ini-be"


def test_new_album_az_album_properties_parbeszedbol_a_kijelolt_kepet_is_felveszi(
    tray_app, qt_app
):
    window, controller, _engine = tray_app
    _kijelol(window, qt_app, controller)
    _menu_nyitasa(window, qt_app)
    _kattints(qt_app, _elem(window, "trayAddToNewAlbumItem", QQuickItem))

    dialog = _elem(window, "toolbarNewAlbumPropertiesDialog")
    assert _varj(qt_app, lambda: dialog.property("opened") is True), (
        "a New Album... sor nem nyitotta meg az Album Properties párbeszédet"
    )
    assert dialog.property("title") == "Album Properties"
    name_field = _elem(dialog, "folderPropertiesNameField")
    assert name_field.property("text") == "Untitled"
    _kattints(qt_app, _elem(dialog, "folderPropertiesOkButton", QQuickItem))

    assert _varj(qt_app, lambda: len(controller.albums) == 1), (
        "a párbeszéd jóváhagyása nem hozott létre albumot"
    )
    album = controller.albums[0]
    assert album["name"] == "Untitled"
    assert album["count"] == 1, "az új albumnak a kijelölt képet is tartalmaznia kell"

    ini = (Path(controller.currentFolder) / ".picasa.ini").read_text(
        encoding="utf-8"
    )
    assert f"[.album:{album['token']}]" in ini
    assert f"albums={album['token']}" in ini

    pane = _elem(window, "folderPane")
    model = pane.property("albumsModel")
    if hasattr(model, "toVariant"):
        model = model.toVariant()
    assert any(row["token"] == album["token"] and row["count"] == 1 for row in model)
