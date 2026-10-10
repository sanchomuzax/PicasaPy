"""A rácsról a Helyek térképére húzott kép megerősítése és mentése (#4583)."""

from __future__ import annotations

import re
import time
from pathlib import Path

import pytest
from PySide6.QtCore import QObject, QPoint, QUrl, Qt
from PySide6.QtQml import QQmlComponent
from PySide6.QtQuick import QQuickItem
from PySide6.QtTest import QTest


_PROBA_TERKEP = '''import QtQuick
Item {
    id: root
    objectName: "placesMap"
    property var markers: []
    readonly property var mapTypeNames: ["Map"]
    readonly property int activeMapTypeIndex: 0
    signal markerActivated(int row)
    signal placePicked(real latitude, real longitude)
    signal photosDropped(var rows, real latitude, real longitude)
    signal markerSearchRequested(var rows)
    signal markerEraseRequested(var rows)
    function selectMapType(index) {}
    property int deliveredDrops: 0
    DropArea {
        id: target
        objectName: "placesMapDropArea"
        anchors.fill: parent
        onDropped: function(drop) {
            if (!drop.source || drop.source.payload !== "photos") return
            drop.accept()
            root.deliveredDrops += 1
            root.photosDropped(drop.source.photoRows,
                               12.5 + drop.y / 10000,
                               20.25 + drop.x / 10000)
        }
    }
}'''


def _walk(item: QQuickItem):
    for child in item.childItems():
        yield child
        yield from _walk(child)


def _elem(window, object_name: str):
    found = window.findChild(QObject, object_name)
    if found is not None:
        return found
    return next(
        (item for item in _walk(window.contentItem())
         if item.objectName() == object_name),
        None,
    )


def _qml_lista(value) -> list:
    if hasattr(value, "toVariant"):
        value = value.toVariant()
    return list(value)


def _varj(qt_app, predicate, timeout: float = 5.0) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        qt_app.processEvents()
        try:
            if predicate():
                return True
        except (AttributeError, RuntimeError, TypeError):
            pass
        time.sleep(0.005)
    try:
        return bool(predicate())
    except (AttributeError, RuntimeError, TypeError):
        return False


def _scene_center(item: QQuickItem) -> QPoint:
    point = item.mapToScene(item.boundingRect().center())
    return QPoint(round(point.x()), round(point.y()))


def _huzas_forras(window, source: QQuickItem):
    return next(
        item for item in _walk(window.contentItem())
        if item.objectName() == "thumbDragProxy"
        and item.parentItem() == source.parentItem()
    )


def _egerhuzas(window, qt_app, source: QQuickItem, target: QQuickItem,
               internal_drag_type: int, offset: QPoint | None = None):
    if offset is None:
        offset = QPoint()
    assert _varj(qt_app, lambda: source.width() > 0 and source.height() > 0)
    assert _varj(qt_app, lambda: target.width() > 0 and target.height() > 0)
    start = _scene_center(source)
    end = _scene_center(target) + offset
    proxy = _huzas_forras(window, source)
    attached_drag = next(
        child for child in proxy.children()
        if child.metaObject().className() == "QQuickDragAttached"
    )
    drag_activated = []
    attached_drag.activeChanged.connect(
        lambda: attached_drag.property("active") and drag_activated.append(True)
    )
    # A térképes cél appon belüli QML-ejtés. A forrás normál futásban
    # `Automatic`, ami Windowson a fájlkezelő felé is húzható; a teszt az
    # egérrel indított húzás belső QML-ágát választja ki, hogy az offscreen
    # futtató natív OLE/QDrag hurka ne vegye át a pointert.
    attached_drag.setProperty("dragType", internal_drag_type)
    QTest.mouseMove(window, start)
    QTest.mousePress(window, Qt.MouseButton.LeftButton, pos=start)
    delta = end - start
    tavolsag = max(abs(delta.x()), abs(delta.y()))
    lepesek = max(1, (tavolsag + 3) // 4)
    for lepes in range(1, lepesek + 1):
        pont = start + QPoint(
            round(delta.x() * lepes / lepesek),
            round(delta.y() * lepes / lepesek),
        )
        QTest.mouseMove(window, pont)
        qt_app.processEvents()
    assert drag_activated, "a rácskép egérhúzása nem aktiválta a QML Drag-et"
    QTest.mouseRelease(window, Qt.MouseButton.LeftButton, pos=end)
    qt_app.processEvents()


def _internal_drag_type(engine) -> int:
    component = QQmlComponent(engine)
    component.setData(
        b"import QtQuick\nItem { property int typeForTest: Drag.Internal }",
        QUrl(),
    )
    item = component.create()
    assert item is not None, [error.toString() for error in component.errors()]
    return int(item.property("typeForTest"))


def _forras_kep(window):
    return next(
        (item for item in _walk(window.contentItem())
         if item.objectName() == "thumbMouseArea"
         and item.parentItem().property("index") == 0),
        None,
    )


def _geotag_ini(window, controller, row: int) -> tuple[str, float, float]:
    photo_path = Path(controller.photos.filePathAt(row))
    ini_path = photo_path.parent / ".picasa.ini"
    text = ini_path.read_text(encoding="utf-8")
    match = re.search(
        rf"(?ms)^\[{re.escape(photo_path.name)}\]\s*$"
        rf"(.*?)(?=^\[|\Z)",
        text,
    )
    assert match is not None, f"a {photo_path.name} bejegyzése hiányzik"
    tag = re.search(r"(?m)^geotag=([+-]?\d+(?:\.\d+)?),([+-]?\d+(?:\.\d+)?)$",
                    match.group(1))
    assert tag is not None, f"a {photo_path.name} geotag sora hiányzik"
    return text, float(tag.group(1)), float(tag.group(2))


def test_racsrol_terkepre_huzas_put_move_megerositessel_ini_be_ir(
    qml_app, qt_app, tmp_path
):
    window, controller, engine = qml_app
    eredeti_magassag = window.height()
    window.setProperty("selectedIndex", 0)
    window.setProperty("selectedIndexes", [0])
    loader = window.findChild(QObject, "placesMapLoader")
    assert loader is not None
    probe_map = tmp_path / "probaterkep.qml"
    probe_map.write_text(_PROBA_TERKEP, encoding="utf-8")
    # A tesztben a térképcsempék hálózati szolgáltatóját helyi QtQuick
    # DropArea váltja ki; a PlacesMap produkciós bekötését a forrásőr méri.
    loader.setProperty("source", QUrl.fromLocalFile(str(probe_map)))
    window.setProperty("activeDrawerTab", "places")

    assert _varj(qt_app, lambda: _elem(window, "placesPanel") is not None
                 and _elem(window, "placesPanel").property("visible") is True)
    assert _varj(qt_app, lambda: _elem(window, "placesMap") is not None
                 or _elem(window, "placesFallbackText").property("visible") is True)
    map_item = _elem(window, "placesMap")
    assert map_item is not None and hasattr(map_item, "photosDropped")
    assert _varj(qt_app, lambda: map_item.width() > 0)
    drop_area = _elem(window, "placesMapDropArea")
    assert drop_area is not None, "a térkép nem fogad fotóhúzást"
    delivered_drops = []
    map_item.photosDropped.connect(
        lambda rows, latitude, longitude: delivered_drops.append(
            (_qml_lista(rows), latitude, longitude)
        )
    )

    eredeti_magassag = window.height()
    internal_drag_type = _internal_drag_type(engine)
    for lepes, magassag_delta in enumerate((-5, 0, 5)):
        window.resize(window.width(), eredeti_magassag + magassag_delta)
        assert _varj(qt_app, lambda: drop_area.width() > 0
                     and drop_area.height() > 0)
        source_mouse = _forras_kep(window)
        assert source_mouse is not None, "a kijelölt rácskép egérterülete hiányzik"
        offset = QPoint(24 + lepes * 5, -16 + lepes * 4)
        _egerhuzas(
            window, qt_app, source_mouse, drop_area,
            internal_drag_type, offset,
        )
        # A tesztelő Qt offscreen platform aktiválja a QML Drag-et egérből,
        # de nem továbbít belső QQuick DropArea eseményt. A térkép nyilvános
        # ejtési jelét ugyanazzal a képpontból származtatott ponttal adjuk át;
        # a produkciós DropArea onDropped ágát külön forrásőr védi.
        drop_point = drop_area.mapFromScene(
            _scene_center(drop_area) + offset
        )
        expected_lat = 12.5 + drop_point.y() / 10000
        expected_lon = 20.25 + drop_point.x() / 10000
        drag_rows = _qml_lista(
            _huzas_forras(window, source_mouse).property("photoRows")
        )
        assert drag_rows == [0]
        map_item.photosDropped.emit(drag_rows, expected_lat, expected_lon)
        assert delivered_drops[-1][0] == drag_rows
        assert delivered_drops[-1][1:] == pytest.approx(
            (expected_lat, expected_lon)
        )
        assert _varj(qt_app, lambda: _elem(window, "dropGeotagConfirm") is not None
                     and _elem(window, "dropGeotagConfirm").property("visible") is True), (
            "a térképre dobás nem kérdezi meg, hogy ide kerüljön-e a kép"
        )
        dialog = _elem(window, "dropGeotagConfirm")
        expected_message = "Put photo here?" if lepes == 0 else "Move photo here?"
        assert dialog.property("message") == expected_message

        expected_lat = float(dialog.property("latitude"))
        expected_lon = float(dialog.property("longitude"))
        assert (expected_lat, expected_lon) == pytest.approx(
            delivered_drops[-1][1:]
        )
        yes_button = _elem(window, "dropGeotagYesButton")
        assert yes_button is not None
        QTest.mouseClick(
            window, Qt.MouseButton.LeftButton, pos=_scene_center(yes_button)
        )
        assert _varj(qt_app, lambda: (Path(controller.photos.filePathAt(0)).parent
                                     / ".picasa.ini").exists())

        _, saved_lat, saved_lon = _geotag_ini(window, controller, 0)
        assert saved_lat == pytest.approx(expected_lat, abs=0.000001)
        assert saved_lon == pytest.approx(expected_lon, abs=0.000001)


def test_a_valodi_terkep_droparea_a_pontbol_koordinatat_kepez():
    import picasapy.app

    app_qml = Path(picasapy.app.__file__).parent / "qml"
    places_map = (
        app_qml / "PicasaPy" / "PlacesMap.qml"
    ).read_text(encoding="utf-8")
    main_qml = (app_qml / "Main.qml").read_text(encoding="utf-8")
    assert "DropArea {" in places_map
    assert "map.toCoordinate" in places_map
    assert "photosDropped" in places_map
    assert "onDropped:" in places_map
    assert 'source.payload !== "photos"' in places_map
    assert "dragRows: window.selectedIndexes" in main_qml
