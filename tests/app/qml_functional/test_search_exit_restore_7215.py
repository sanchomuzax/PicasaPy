"""#7215/#7216: keresőmező Esc- és keresésből kilépési viselkedése."""

from __future__ import annotations

from pathlib import Path
import time

import pytest
from PySide6.QtCore import (
    Q_ARG,
    Q_RETURN_ARG,
    QMetaObject,
    QObject,
    QPoint,
    QPointF,
    Qt,
)
from PySide6.QtTest import QTest

from support.jpeg_factory import make_jpeg
from tests.app.qml_functional.conftest import _build_qml_app


def _create_library(library):
    origin = library / "origin"
    matches = library / "matches"
    origin.mkdir()
    matches.mkdir()
    for index in range(20):
        make_jpeg(origin / f"origin-{index:02}.jpg", size=(100, 100))
    make_jpeg(matches / "needle.jpg", size=(320, 160))


@pytest.fixture
def qml_app_7215(qt_app, tmp_path, request):
    yield from _build_qml_app(
        qt_app,
        tmp_path,
        kepeket_keszit=_create_library,
        keep_modul=request.module,
    )


def _activate(window, qt_app):
    window.show()
    window.requestActivate()
    qt_app.processEvents()


def _wait_for_layout(item, timeout_s=3.0):
    """Megvárja, hogy az elem elrendezése lefusson (mérete ne legyen 0).

    A rétegben újonnan láthatóvá váló elem (pl. a zöld sáv gombja) `isVisible()`
    értéke azonnal igaz, de a mérete és helye csak a következő polish-körben
    áll be. A kattintás pontja addig a 0 x 0-s elem sarkába esne (#7319)."""
    deadline = time.monotonic() + timeout_s
    while (item.width() <= 0 or item.height() <= 0) and time.monotonic() < deadline:
        QTest.qWait(10)
    assert item.width() > 0 and item.height() > 0, (
        f"Az elem elrendezése {timeout_s} s alatt sem futott le "
        f"({item.width()} x {item.height()})"
    )


def _click(window, item, qt_app):
    assert item is not None and item.isVisible()
    _wait_for_layout(item)
    point = item.mapToScene(QPointF(item.width() / 2, item.height() / 2))
    QTest.mouseClick(
        window,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        QPoint(round(point.x()), round(point.y())),
    )
    qt_app.processEvents()


def _start_search(window, controller, qt_app, query="needle"):
    from PySide6.QtCore import Q_ARG, QMetaObject

    field = window.findChild(QObject, "searchField")
    toolbar = window.findChild(QObject, "mainToolbar")
    assert field is not None and toolbar is not None
    field.setProperty("text", query)
    QMetaObject.invokeMethod(
        toolbar,
        "searchEdited",
        Qt.ConnectionType.DirectConnection,
        Q_ARG("QString", query),
    )
    qt_app.processEvents()
    return field, toolbar


def _qml_value(obj, name):
    value = obj.property(name)
    if hasattr(value, "toVariant"):
        value = value.toVariant()
    return value


def _row_is_in_viewport(grid, row):
    bounds = QMetaObject.invokeMethod(
        grid,
        "rowBounds",
        Qt.ConnectionType.DirectConnection,
        Q_RETURN_ARG("QVariant"),
        Q_ARG("QVariant", row),
    )
    if hasattr(bounds, "toVariant"):
        bounds = bounds.toVariant()
    if bounds is None:
        return False
    content_y = grid.property("contentY")
    return (
        bounds["bottom"] > content_y
        and bounds["top"] < content_y + grid.height()
    )


def _wait_for_visible_row(grid, row, qt_app):
    deadline = time.monotonic() + 3.0
    while time.monotonic() < deadline:
        QMetaObject.invokeMethod(
            grid, "forceLayout", Qt.ConnectionType.DirectConnection
        )
        qt_app.processEvents()
        if _row_is_in_viewport(grid, row):
            return
        QTest.qWait(50)
    assert _row_is_in_viewport(grid, row), (
        f"A visszaállított {row}. kép nem látható a rács nézőterületén"
    )


def _select_origin_photo(window, controller, origin_folder):
    controller.selectFolder(str(origin_folder))
    selected_row = controller.photos.rowOfPath(str(origin_folder / "origin-19.jpg"))
    assert selected_row >= 0
    selected_id = controller.photos.idAt(selected_row)
    window.setProperty("selectedIndexes", [selected_row])
    window.setProperty("selectedIndex", selected_row)
    return selected_id


def test_escape_closes_open_suggestions_and_ctrl_f_keeps_search(qml_app_7215, qt_app):
    window, controller, _engine = qml_app_7215
    _activate(window, qt_app)
    field, toolbar = _start_search(window, controller, qt_app, "needle")
    box = window.findChild(QObject, "searchSuggestions")
    timer = window.findChild(QObject, "suggestionsTimer")
    assert box is not None and timer is not None
    timer.stop()
    box.setProperty(
        "suggestions",
        [{"kind": "folder", "name": "matches", "count": 1, "param": "matches"}],
    )
    qt_app.processEvents()
    assert controller.searchActive
    assert box.property("visible") is True
    initial_count = controller.searchResultCount

    _click(window, field, qt_app)
    QTest.keyClick(window, Qt.Key.Key_Escape)
    qt_app.processEvents()

    assert field.property("text") == "needle"
    assert controller.searchActive
    assert controller.searchResultCount == initial_count
    assert box.property("visible") is False

    box.setProperty(
        "suggestions",
        [{"kind": "folder", "name": "matches", "count": 1, "param": "matches"}],
    )
    qt_app.processEvents()
    QTest.keyClick(window, Qt.Key.Key_F, Qt.KeyboardModifier.ControlModifier)
    qt_app.processEvents()
    assert controller.searchActive
    assert field.property("text") == "needle"
    assert box.property("visible") is True


def test_escape_with_closed_suggestions_clears_search_and_delete_still_works(
    qml_app_7215, qt_app
):
    window, controller, _engine = qml_app_7215
    _activate(window, qt_app)
    field, _toolbar = _start_search(window, controller, qt_app)
    box = window.findChild(QObject, "searchSuggestions")
    timer = window.findChild(QObject, "suggestionsTimer")
    timer.stop()
    box.setProperty("suggestions", [])
    _click(window, field, qt_app)
    assert controller.searchActive

    QTest.keyClick(window, Qt.Key.Key_Escape)
    qt_app.processEvents()

    assert field.property("text") == ""
    assert controller.searchActive is False
    assert field.property("activeFocus") is True
    field.setProperty("text", "abc")
    _click(window, field, qt_app)
    field.setProperty("cursorPosition", 1)
    QTest.keyClick(window, Qt.Key.Key_Delete)
    qt_app.processEvents()
    assert field.property("text") == "ac"


@pytest.mark.parametrize("height_delta", [-5, 0, 5])
def test_clear_button_restores_search_origin_selection(
    qml_app_7215, qt_app, height_delta
):
    window, controller, _engine = qml_app_7215
    _activate(window, qt_app)
    window.setHeight(window.height() + height_delta)
    qt_app.processEvents()
    library = Path(controller._roots[0])
    origin_folder = library / "origin"
    target_folder = library / "matches"
    selected_id = _select_origin_photo(window, controller, origin_folder)
    field, _toolbar = _start_search(window, controller, qt_app)
    assert controller.searchActive
    controller.selectFolderKeepSearch(str(target_folder))
    qt_app.processEvents()
    assert Path(controller.currentFolder) == target_folder

    clear = window.findChild(QObject, "searchClear")
    _click(window, clear, qt_app)

    restored_row = controller.photos.rowOfId(int(selected_id))
    assert controller.searchActive is False
    assert Path(controller.currentFolder) == origin_folder
    assert field.property("text") == ""
    assert _qml_value(window, "selectedIndexes") == [restored_row]
    assert window.property("selectedIndex") == restored_row
    _wait_for_visible_row(
        window.findChild(QObject, "photoGrid"), restored_row, qt_app
    )


@pytest.mark.parametrize("height_delta", [-5, 0, 5])
def test_back_to_view_all_restores_search_origin_selection(
    qml_app_7215, qt_app, height_delta
):
    window, controller, _engine = qml_app_7215
    _activate(window, qt_app)
    window.setHeight(window.height() + height_delta)
    qt_app.processEvents()
    library = Path(controller._roots[0])
    origin_folder = library / "origin"
    selected_id = _select_origin_photo(window, controller, origin_folder)
    field, _toolbar = _start_search(window, controller, qt_app)
    assert controller.searchActive

    back = window.findChild(QObject, "searchBackToViewAll")
    _click(window, back, qt_app)

    restored_row = controller.photos.rowOfId(int(selected_id))
    assert controller.searchActive is False
    assert Path(controller.currentFolder) == origin_folder
    assert field.property("text") == ""
    assert _qml_value(window, "selectedIndexes") == [restored_row]
    assert window.property("selectedIndex") == restored_row
    _wait_for_visible_row(
        window.findChild(QObject, "photoGrid"), restored_row, qt_app
    )


def test_back_to_view_all_click_waits_for_the_layout_7319(qml_app_7215, qt_app):
    """#7319: a zöld sáv gombja a keresés után LÁTSZIK, de az elrendezés csak
    a következő polish-körben méretezi: addig 0 x 0. Windowson (szálas
    render-hurok) a keresést követő egyetlen `processEvents` nem biztos, hogy
    lefuttatja a polish-t, ezért a gombra kattintás a semmibe ment, és a
    keresés élve maradt. Itt az eseményhurok SZÁNDÉKOSAN nem fut a keresés
    és a kattintás között: a segéd a kattintás előtt megvárja az elrendezést."""
    window, controller, _engine = qml_app_7215
    _activate(window, qt_app)
    controller.search("needle")
    back = window.findChild(QObject, "searchBackToViewAll")
    assert controller.searchActive
    assert back.isVisible() and back.width() == 0 and back.height() == 0

    _click(window, back, qt_app)

    assert controller.searchActive is False


def test_search_only_shows_matching_album_and_people_categories(
    qml_app_7215, qt_app
):
    window, controller, _engine = qml_app_7215
    _activate(window, qt_app)
    pane = window.findChild(QObject, "folderPane")
    assert pane is not None
    pane.setProperty(
        "albumsModel",
        [
            {"token": "album-beach", "name": "Beach", "count": 1},
            {"token": "album-trip", "name": "Road Trip", "count": 1},
        ],
    )
    pane.setProperty(
        "peopleModel",
        [
            {"name": "Bea", "person_id": "bea", "count": 1, "thumbUrl": ""},
            {"name": "Alice", "person_id": "alice", "count": 1, "thumbUrl": ""},
        ],
    )
    pane.setProperty("albumsCollapsed", False)
    pane.setProperty("peopleCollapsed", False)
    albums_header = window.findChild(QObject, "albumsHeader")
    people_header = window.findChild(QObject, "peopleHeader")
    album_rows = window.findChild(QObject, "albumRepeater")
    people_rows = window.findChild(QObject, "peopleRepeater")

    controller.search("missing")
    qt_app.processEvents()
    assert albums_header.isVisible() is False
    assert people_header.isVisible() is False
    assert album_rows.property("count") == 0
    assert people_rows.property("count") == 0

    controller.search("bea")
    qt_app.processEvents()
    assert albums_header.isVisible() is True
    assert people_header.isVisible() is True
    assert album_rows.property("count") == 1
    assert people_rows.property("count") == 1
