"""#4530: a keresősáv javaslatlistája billentyűzettel is kezelhető."""

from __future__ import annotations

import time

from PySide6.QtCore import QObject, QPoint, QPointF, Qt
from PySide6.QtTest import QTest


def _wait_until(qt_app, predicate, timeout: float = 3.0) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        qt_app.processEvents()
        if predicate():
            return True
        time.sleep(0.05)
    qt_app.processEvents()
    return bool(predicate())


def _walk(item):
    for child in item.childItems():
        yield child
        yield from _walk(child)


def _click(window, item, qt_app) -> None:
    assert item is not None and item.isVisible()
    point = item.mapToScene(QPointF(item.width() / 2, item.height() / 2))
    QTest.mouseClick(
        window,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        QPoint(round(point.x()), round(point.y())),
    )
    qt_app.processEvents()


def _open_popup(window, controller, field, popup, qt_app):
    field.setProperty("text", "ke")
    popup.setProperty(
        "suggestions",
        [
            {
                "kind": "folder",
                "name": "kepek",
                "count": 2,
                "param": controller.currentFolder,
            },
            {
                "kind": "folder",
                "name": "kepek-masodik",
                "count": 1,
                "param": controller.currentFolder,
            },
        ],
    )
    qt_app.processEvents()
    assert _wait_until(qt_app, lambda: popup.property("visible") is True)
    _click(window, field, qt_app)
    assert _wait_until(qt_app, lambda: field.property("activeFocus") is True)
    rows = [item for item in _walk(popup) if item.objectName() == "suggestionRow"]
    assert len(rows) == 2
    return rows


def test_search_suggestions_keyboard_and_click_at_height_variations(qml_app, qt_app):
    window, controller, _engine = qml_app
    window.show()
    window.requestActivate()
    qt_app.processEvents()
    base_height = window.height()

    # A QObject lookup keeps the helper independent of generated QML types.
    field = window.findChild(QObject, "searchField")
    popup = window.findChild(QObject, "searchSuggestions")
    assert field is not None and popup is not None

    chosen = []
    popup.chosen.connect(lambda kind, name, param: chosen.append((kind, name, param)))

    for height_delta in (-5, 0, 5):
        window.setHeight(base_height + height_delta)
        qt_app.processEvents()

        rows = _open_popup(window, controller, field, popup, qt_app)
        QTest.keyClick(window, Qt.Key.Key_Down)
        assert popup.property("selectedIndex") == 0
        assert rows[0].property("color") == rows[0].property(
            "keyboardSelectionColor"
        )

        QTest.keyClick(window, Qt.Key.Key_Down)
        assert popup.property("selectedIndex") == 1
        QTest.keyClick(window, Qt.Key.Key_Up)
        assert popup.property("selectedIndex") == 0
        QTest.keyClick(window, Qt.Key.Key_Up)
        assert popup.property("selectedIndex") == 0

        QTest.keyClick(window, Qt.Key.Key_Down)
        QTest.keyClick(window, Qt.Key.Key_Enter)
        qt_app.processEvents()
        assert chosen and chosen[-1][:2] == ("folder", "kepek-masodik")
        assert field.property("text") == ""
        assert popup.property("visible") is False
        assert field.property("activeFocus") is True

        _open_popup(window, controller, field, popup, qt_app)
        QTest.keyClick(window, Qt.Key.Key_Escape)
        qt_app.processEvents()
        assert popup.property("visible") is False
        assert field.property("text") == "ke"
        assert field.property("activeFocus") is True

        rows = _open_popup(window, controller, field, popup, qt_app)
        QTest.keyClick(window, Qt.Key.Key_Down)
        assert popup.property("selectedIndex") == 0
        _click(window, rows[1], qt_app)
        assert chosen and chosen[-1][:2] == ("folder", "kepek-masodik")
        assert popup.property("visible") is False
        assert field.property("activeFocus") is True
