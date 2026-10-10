"""A Helyek térképe betöltés közben jelez, offline pedig magyarázatot ad (#4584)."""

from __future__ import annotations

import time
from pathlib import Path

from PySide6.QtCore import QPoint, QUrl, Qt
from PySide6.QtQuick import QQuickItem
from PySide6.QtTest import QTest


def _walk(item: QQuickItem):
    for child in item.childItems():
        yield child
        yield from _walk(child)


def _item(window, object_name: str) -> QQuickItem:
    for item in _walk(window.contentItem()):
        if item.objectName() == object_name:
            return item
    raise AssertionError(f"A főablakból hiányzik: {object_name}")


def _var(qt_app, predicate, timeout: float = 3.0) -> bool:
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
    center = item.mapToScene(item.boundingRect().center())
    QTest.mouseClick(
        window,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        QPoint(round(center.x()), round(center.y())),
    )
    qt_app.processEvents()


def test_helyek_kattintasra_betoltest_jelez_es_offline_magyarazatot_mutat(
    qml_app, qt_app, tmp_path
):
    window, _controller, _engine = qml_app
    map_source = (
        Path(__file__).resolve().parents[3]
        / "src/picasapy/app/qml/PicasaPy/PlacesMap.qml"
    ).read_text(encoding="utf-8")
    assert (
        "readonly property bool mapLoading: !map.mapReady "
        "&& map.error === Map.NoError"
    ) in map_source
    assert (
        "readonly property bool offline: map.error === Map.ConnectionError"
    ) in map_source

    loader = _item(window, "placesMapLoader")
    test_map = tmp_path / "TesztHelyterkep.qml"
    test_map.write_text(
        """import QtQuick
Item {
    property var markers: []
    property var mapTypeNames: []
    property int activeMapTypeIndex: 0
    property bool mapLoading: true
    property bool offline: false
    signal markerActivated(int row)
    signal placePicked(real latitude, real longitude)
    function selectMapType(index) {}
}
""",
        encoding="utf-8",
    )
    assert loader.setProperty("source", QUrl.fromLocalFile(str(test_map)))

    _kattint(window, _item(window, "trayPanelToggle_places"), qt_app)
    panel = _item(window, "placesPanel")
    assert _var(qt_app, panel.isVisible)
    assert _var(qt_app, lambda: loader.property("item") is not None)

    overlay = _item(window, "placesMapStatusOverlay")
    loading = _item(window, "placesMapLoadingIndicator")
    message = _item(window, "placesMapStatusText")
    assert _var(qt_app, overlay.isVisible)
    assert loading.isVisible()
    assert message.property("text") == "Loading Map..."

    map_item = loader.property("item")
    original_width, original_height = window.width(), window.height()
    for height_delta in (-5, 0, 5):
        window.resize(original_width, original_height + height_delta)
        qt_app.processEvents()
        assert _var(qt_app, lambda: overlay.width() > 0 and overlay.height() > 0)
        assert abs(overlay.width() - loader.width()) <= 3
        assert abs(overlay.height() - loader.height()) <= 3

    map_item.setProperty("mapLoading", False)
    map_item.setProperty("offline", True)
    assert _var(qt_app, lambda: overlay.isVisible() and not loading.isVisible())
    assert "Internet" in message.property("text")
    assert "Google Maps" in message.property("text")
    window.resize(original_width, original_height)
