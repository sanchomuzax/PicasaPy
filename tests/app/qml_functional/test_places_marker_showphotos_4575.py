"""A Helyek jelölője szűrt rácsnézetet nyit, a vissza gomb pedig visszaállít (#4575)."""

from __future__ import annotations

import time

import pytest
from PySide6.QtCore import QPoint, QUrl, Qt
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


def _van_elem(window, object_name: str) -> bool:
    return any(item.objectName() == object_name for item in _walk(window.contentItem()))


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
def test_jelolore_kattintva_a_helyes_kepek_kerulnek_a_racsba_es_visszaallithato(
    qml_app, qt_app, tmp_path, magassag_delta
):
    window, controller, _engine = qml_app
    window.resize(window.width(), window.height() + magassag_delta)
    qt_app.processEvents()

    # A teszt-jelölő ugyanazt a PlacesPanel Loader-szerződést használja, mint
    # a QtLocation térkép, így a kattintás hálózat és QtLocation nélkül is mérhető.
    fake_map = tmp_path / "TesztHelyterkep.qml"
    fake_map.write_text(
        """import QtQuick
Item {
    property var markers: []
    property var mapTypeNames: []
    property int activeMapTypeIndex: 0
    property int clickCount: 0
    signal markerActivated(int row)
    signal placePicked(real latitude, real longitude)
    function selectMapType(index) {}
    Rectangle {
        objectName: "placesTestMarker"
        width: 30
        height: 30
        anchors.centerIn: parent
        color: "#d84040"
        MouseArea {
            anchors.fill: parent
            onClicked: {
                parent.parent.clickCount += 1
                if (parent.parent.markers.length > 0)
                    parent.parent.markerActivated(parent.parent.markers[0].row)
            }
        }
    }
}
""",
        encoding="utf-8",
    )
    loader = _elem(window, "placesMapLoader")
    assert loader.setProperty("source", QUrl.fromLocalFile(str(fake_map)))
    panel = _elem(window, "placesPanel")
    _kattint(window, _elem(window, "trayPanelToggle_places"), qt_app)
    assert _var(qt_app, lambda: panel.isVisible())
    assert _var(qt_app, lambda: _van_elem(window, "placesTestMarker"))

    controller.setGeotagRows([0], 47.5, 19.05)
    assert _var(qt_app, lambda: len(controller.geoMarkers) == 1)
    expected_name = controller.geoMarkers[0]["name"]
    marker = _elem(window, "placesTestMarker")
    _kattint(window, marker, qt_app)
    assert _var(qt_app, lambda: marker.parentItem().property("clickCount") == 1)

    assert _var(
        qt_app,
        lambda: controller.filterActive and controller.photos.rowCount() == 1,
    )
    assert [photo.name for photo in controller.photos.photos] == [expected_name]

    back_to_all = next(
        item
        for item in _walk(window.contentItem())
        if item.property("text") == "Back to View All"
    )
    _kattint(window, back_to_all, qt_app)
    assert _var(
        qt_app,
        lambda: not controller.filterActive and controller.photos.rowCount() == 2,
    )
