"""#6301 — Ctrl+T a Címkék panel beviteli mezőjére viszi a fókuszt."""

# rontás-kontroll: a javítás előtti Ctrl+T ág → 3 failed (hiányzó fókusz).

from __future__ import annotations

import pytest
from PySide6.QtCore import QObject, QPoint, QPointF, Qt
from PySide6.QtTest import QTest

from support.qt_wait import varj_ablakon_belulre, varj_feltetelre


def _walk(item):
    for child in item.childItems():
        yield child
        yield from _walk(child)


def _visual_item(window, object_name: str):
    return next(
        (
            item
            for item in _walk(window.contentItem())
            if item.objectName() == object_name
        ),
        None,
    )


def _click_item(window, item, qt_app) -> None:
    assert varj_ablakon_belulre(qt_app, window, item), (
        f"a kattintási cél közepe nem került az ablakba: {item.objectName()}"
    )
    pont = item.mapToScene(QPointF(item.width() / 2, item.height() / 2))
    QTest.mouseClick(
        window,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        QPoint(round(pont.x()), round(pont.y())),
    )
    qt_app.processEvents()


@pytest.mark.parametrize("height_delta", [-5, 0, 5])
def test_ctrl_t_focus_types_and_returns_to_grid_shortcuts(
    qml_app, qt_app, height_delta
):
    window, _controller, _engine = qml_app
    window.setHeight(window.height() + height_delta)
    window.show()
    window.requestActivate()
    assert varj_feltetelre(qt_app, lambda: window.isActive(), 3.0)

    window.setProperty("selectedIndexes", [0])
    window.setProperty("selectedIndex", 0)
    qt_app.processEvents()
    thumb = _visual_item(window, "thumbMouseArea")
    assert thumb is not None and thumb.isVisible()
    _click_item(window, thumb, qt_app)

    QTest.keyClick(window, Qt.Key.Key_T, Qt.KeyboardModifier.ControlModifier)
    qt_app.processEvents()

    tag_input = window.findChild(QObject, "tagInput")
    drawer = window.findChild(QObject, "rightDrawer")
    assert varj_feltetelre(
        qt_app,
        lambda: (
            tag_input is not None
            and tag_input.isVisible()
            and tag_input.isEnabled()
            and tag_input.property("activeFocus") is True
            and drawer is not None
            and drawer.property("width")
            >= drawer.property("kivantSzelesseg") - 0.5
        ),
        3.0,
    ), "a Ctrl+T nem a teljesen kinyílt Címkék panel mezőjére vitte a fókuszt"

    for key in (Qt.Key.Key_X, Qt.Key.Key_Y, Qt.Key.Key_Z):
        QTest.keyClick(window, key)
    qt_app.processEvents()
    assert tag_input.property("text") == "xyz"

    QTest.keyClick(window, Qt.Key.Key_T, Qt.KeyboardModifier.ControlModifier)
    qt_app.processEvents()
    assert window.property("activeDrawerTab") == "tags"
    assert tag_input.property("activeFocus") is True

    _click_item(window, thumb, qt_app)
    assert varj_feltetelre(
        qt_app, lambda: tag_input.property("activeFocus") is not True, 3.0
    )
    QTest.keyClick(window, Qt.Key.Key_T, Qt.KeyboardModifier.ControlModifier)
    qt_app.processEvents()
    assert varj_feltetelre(
        qt_app,
        lambda: window.property("activeDrawerTab") == "",
        3.0,
    ), "a rácsfókusz után a Ctrl+T nem zárta be a Címkék panelt"

    QTest.keyClick(window, Qt.Key.Key_Return, Qt.KeyboardModifier.AltModifier)
    qt_app.processEvents()
    assert varj_feltetelre(
        qt_app,
        lambda: window.property("activeDrawerTab") == "properties",
        3.0,
    ), "az Alt+Enter nem nyitotta meg a Tulajdonságok panelt"
