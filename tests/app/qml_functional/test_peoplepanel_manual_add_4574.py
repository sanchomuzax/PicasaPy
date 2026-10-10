"""A kézi arc-hozzáadás az Emberek panelből indul, a panel útmutatójával (#4574)."""

from __future__ import annotations

import time
from pathlib import Path

import pytest
from PySide6.QtCore import QObject, QPoint, QPointF, Qt
from PySide6.QtQuick import QQuickItem
from PySide6.QtTest import QTest

_PEOPLE = (
    Path(__file__).resolve().parents[3]
    / "src/picasapy/app/qml/PicasaPy/PeoplePanel.qml"
)
_MANUAL_INSTRUCTIONS = (
    "Instructions:\n\n"
    "1) Manipulate the rectangle to fit the face of the person you want to add.\n\n"
    "You can drag the rectangle to position it, and move its sides to refine the shape.\n\n"
    '2) Click on "Add a name" under the rectangle and type in the person\'s name.\n\n'
    "(Be sure to either press Enter or click on an autocompleted name to indicate that you are done)"
)


def _wait(qt_app, predicate, description: str) -> None:
    deadline = time.monotonic() + 3.0
    while time.monotonic() < deadline:
        qt_app.processEvents()
        if predicate():
            return
        time.sleep(0.01)
    raise AssertionError(f"Időtúllépés: {description}")


def _item(window, name: str) -> QQuickItem:
    item = window.findChild(QQuickItem, name)
    assert item is not None, f"A(z) {name} elem nem található"
    return item


def _click(window, item: QQuickItem) -> None:
    center = item.mapToScene(QPointF(item.width() / 2, item.height() / 2))
    QTest.mouseClick(
        window,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        QPoint(round(center.x()), round(center.y())),
    )


def test_a_panel_tartalmazza_a_spec_szerinti_kezi_hozzaadas_allapotot():
    source = _PEOPLE.read_text(encoding="utf-8")
    assert 'objectName: "peoplePanelManualAddButton"' in source
    assert 'text: qsTr("Add a person manually")' in source
    assert 'objectName: "peoplePanelManualFrame"' in source
    assert 'objectName: "peoplePanelManualInstructions"' in source
    assert 'text: qsTr("Instructions:' in source
    assert 'objectName: "peoplePanelManualCancelButton"' in source


@pytest.mark.parametrize("height_delta", [-5, 0, 5])
def test_a_panel_gomb_kattintasa_elinditja_es_megallitja_a_kezi_hozzaadast(
    qml_app, qt_app, height_delta
):
    window, _controller, _engine = qml_app
    window.resize(window.width(), window.height() + height_delta)
    window.setProperty("activeDrawerTab", "people")
    window.setProperty("selectedIndex", 0)
    window.setProperty("selectedIndexes", [0])

    button = _item(window, "peoplePanelManualAddButton")
    _wait(
        qt_app,
        lambda: button.isVisible() and button.isEnabled() and button.width() > 0,
        "a panel kézi hozzáadás gombja megjelenjen",
    )
    _click(window, button)

    viewer = window.findChild(QObject, "photoViewer")
    assert viewer is not None
    _wait(
        qt_app,
        lambda: window.property("viewerOpen") is True
        and viewer.property("facesEditMode") is True,
        "a néző és a kézi arcmód elinduljon",
    )

    frame = _item(window, "peoplePanelManualFrame")
    instructions = _item(window, "peoplePanelManualInstructions")
    cancel = _item(window, "peoplePanelManualCancelButton")
    panel = window.findChild(QObject, "viewerPeoplePanel")
    assert panel is not None
    panel_button = panel.findChild(QQuickItem, "peoplePanelManualAddButton")
    assert panel_button is not None
    _wait(
        qt_app,
        lambda: frame.isVisible()
        and instructions.isVisible()
        and cancel.isVisible()
        and instructions.property("text") == _MANUAL_INSTRUCTIONS,
        "a panelen megjelenjen a spec szerinti útmutató és Mégse gomb",
    )

    _click(window, cancel)
    _wait(
        qt_app,
        lambda: viewer.property("facesEditMode") is False,
        "a panel Mégse gombja állítsa le a kézi arcmódot",
    )
    _wait(
        qt_app,
        lambda: panel_button.isVisible(),
        "a néző paneljén újra megjelenjen a kézi hozzáadás gomb",
    )
