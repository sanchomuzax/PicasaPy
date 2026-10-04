"""A Helyek helyi keresése a valódi főablakban — #4147."""

from __future__ import annotations

import time

import pytest
from PySide6.QtCore import QPoint, Qt
from PySide6.QtQuick import QQuickItem
from PySide6.QtTest import QTest


def _walk(item: QQuickItem):
    for child in item.childItems():
        yield child
        yield from _walk(child)


def _elem(window, object_name: str) -> QQuickItem:
    for item in _walk(window.contentItem()):
        if item.objectName() == object_name:
            return item
    raise AssertionError(f"A kirajzolt főablakból hiányzik: {object_name}")


def _variant_list(value):
    return value.toVariant() if hasattr(value, "toVariant") else value


def _var(qt_app, predicate, timeout: float = 5.0) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            if predicate():
                return True
        except (AttributeError, RuntimeError, TypeError):
            pass
        qt_app.processEvents()
        time.sleep(0.005)
    return bool(predicate())


def _kattint(window, item: QQuickItem, qt_app) -> None:
    assert _var(qt_app, lambda: item.width() > 0 and item.height() > 0)
    scene_point = item.mapToScene(item.boundingRect().center())
    point = QPoint(round(scene_point.x()), round(scene_point.y()))
    QTest.mouseClick(window, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, point)
    qt_app.processEvents()


@pytest.mark.parametrize("magassag_delta", [-5, 0, 5])
def test_a_helykereses_a_helyi_gps_kepeket_szuri_a_fomenu_kattintasa_utan(
    qml_app, qt_app, magassag_delta
):
    window, controller, _lib, _engine = qml_app
    window.resize(window.width(), window.height() + magassag_delta)
    qt_app.processEvents()

    _kattint(window, _elem(window, "trayPanelToggle_places"), qt_app)
    panel = _elem(window, "placesPanel")
    assert _var(qt_app, lambda: panel.isVisible())

    label = _elem(window, "placesSearchLabel")
    field = _elem(window, "placesSearchInput")
    button = _elem(window, "placesSearchButton")
    map_menu = _elem(window, "placesMapTypeMenu")
    assert label.property("text") == "Search for an address:"
    assert field.property("placeholderText") == ""
    assert map_menu.property("visible") is True

    controller.setGeotagRows([0, 1], 47.5, 19.05)
    assert _var(qt_app, lambda: len(controller.geoMarkers) == 2)
    first_name = controller.geoMarkers[0]["name"]

    _kattint(window, field, qt_app)
    field.setProperty("text", first_name)
    qt_app.processEvents()
    _kattint(window, button, qt_app)

    assert _var(
        qt_app,
        lambda: len(_variant_list(panel.property("filteredMarkers"))) == 1,
    )
    assert _variant_list(panel.property("filteredMarkers"))[0]["name"] == first_name
    assert "1" in _elem(window, "placesCountLabel").property("text")
