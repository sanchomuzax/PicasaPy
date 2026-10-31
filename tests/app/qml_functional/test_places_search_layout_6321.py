"""A széles TextField sem tolhatja ki a Helyek keresőgombját (#6321)."""

from __future__ import annotations

import pytest
from PySide6.QtCore import QPoint, QPointF, Qt
from PySide6.QtQuick import QQuickItem
from PySide6.QtTest import QTest
from tests.support.qt_wait import varj_kattinthatora
from tests.support.varakozas import hibaturo_feltetel, var_feltetelre


def _walk(item: QQuickItem):
    for child in item.childItems():
        yield child
        yield from _walk(child)


def _elem(window, object_name: str) -> QQuickItem:
    for item in _walk(window.contentItem()):
        if item.objectName() == object_name:
            return item
    raise AssertionError(f"A kirajzolt főablakból hiányzik: {object_name}")


def _var(qt_app, predicate, timeout: float = 10.0) -> bool:
    return var_feltetelre(
        qt_app,
        hibaturo_feltetel(predicate, (AttributeError, RuntimeError, TypeError)),
        timeout,
    )


def _kattint(window, item: QQuickItem, qt_app) -> None:
    assert _var(qt_app, lambda: item.width() > 0 and item.height() > 0)
    varj_kattinthatora(window, item)
    point = item.mapToScene(item.boundingRect().center())
    QTest.mouseClick(
        window,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        QPoint(round(point.x()), round(point.y())),
    )
    qt_app.processEvents()


def _ancestors(item: QQuickItem) -> str:
    lines = []
    current = item
    while current is not None:
        origin = current.mapToScene(QPointF(0, 0))
        lines.append(
            f"{current.objectName() or current.metaObject().className()}: "
            f"x={origin.x():.1f}, width={current.width():.1f}, "
            f"implicitWidth={current.implicitWidth():.1f}"
        )
        current = current.parentItem()
    return " <- ".join(lines)


@pytest.mark.parametrize("magassag_delta", [-5, 0, 5])
def test_nagy_mezo_implicit_szelessegnel_a_keresogomb_a_panelben_marad(
    qml_app, qt_app, magassag_delta
):
    window, _controller, _engine = qml_app
    window.resize(window.width(), window.height() + magassag_delta)
    qt_app.processEvents()

    # A kereső már létrejött, amikor a panel rejtett. A nagy implicit
    # szélesség a panel első felépülése előtt utánozza a Windows-metrikát.
    field = _elem(window, "placesSearchInput")
    field.setProperty("implicitWidth", 2000.0)

    _kattint(window, _elem(window, "trayPanelToggle_places"), qt_app)
    panel = _elem(window, "placesPanel")
    drawer = _elem(window, "rightDrawer")
    group = _elem(window, "placesSearchGroup")
    button = _elem(window, "placesSearchButton")
    assert _var(qt_app, lambda: panel.isVisible())
    assert _var(qt_app, lambda: abs(drawer.width() - 280) <= 1)
    assert _var(qt_app, lambda: abs(panel.width() - 276) <= 1)

    assert _var(qt_app, lambda: field.implicitWidth() >= 1999.0)
    assert _var(qt_app, lambda: field.width() < field.implicitWidth()), (
        f"a keresőmező nem zsugorodott: width={field.width():.1f}, "
        f"implicitWidth={field.implicitWidth():.1f}; "
        f"ősök: {_ancestors(field)}"
    )
    assert _var(qt_app, lambda: button.width() > 0 and button.height() > 0)
    assert abs(button.width() - 28) <= 1

    button_right = button.mapToScene(QPointF(button.width(), 0)).x()
    panel_right = panel.mapToScene(QPointF(panel.width(), 0)).x()
    group_right = group.mapToScene(QPointF(group.width(), 0)).x()
    assert button_right <= group_right + 1, (
        f"a 28 px-es gomb jobb széle ({button_right:.1f}) kilóg a "
        f"keresősorból ({group_right:.1f}); ősök: {_ancestors(button)}"
    )
    assert button_right <= panel_right + 1, (
        f"a keresőgomb jobb széle ({button_right:.1f}) kilóg a panelből "
        f"({panel_right:.1f}); ősök: {_ancestors(button)}"
    )
    assert button_right <= window.width() + 1, (
        f"a keresőgomb jobb széle ({button_right:.1f}) kilóg az ablakból "
        f"({window.width()}); ősök: {_ancestors(button)}"
    )
