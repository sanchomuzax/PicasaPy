"""#4637: a gombsor jobb klikk-menüje eléri a gombbeállító párbeszédet."""

from __future__ import annotations

import time

from PySide6.QtCore import QMetaObject, QObject, QPoint, QPointF, Qt
from PySide6.QtTest import QTest


def _var(qt_app, condition, seconds: float = 3.0) -> bool:
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        try:
            if condition():
                return True
        except (AttributeError, RuntimeError, TypeError):
            pass
        qt_app.processEvents()
        time.sleep(0.05)
    return False


def _visual_child(window, name: str):
    """A vizuális fában a Repeater-delegátumok is megtalálhatók."""
    stack = [window.contentItem()]
    while stack:
        item = stack.pop()
        if item.objectName() == name:
            return item
        stack.extend(item.childItems())
    return window.findChild(QObject, name)


def _right_click(window, item, qt_app):
    assert item.width() > 0 and item.height() > 0, (
        f"{item.objectName()} nem kattintható"
    )
    center = item.mapToScene(QPointF(item.width() / 2, item.height() / 2))
    QTest.mouseClick(
        window,
        Qt.MouseButton.RightButton,
        Qt.KeyboardModifier.NoModifier,
        QPoint(round(center.x()), round(center.y())),
    )
    qt_app.processEvents()


def _check_context_menu(window, control_name: str, qt_app):
    control = _visual_child(window, control_name)
    assert control is not None, f"{control_name} nincs a megjelenített ablakban"
    base_height = int(window.height())

    for offset in (-5, 0, 5):
        window.setHeight(base_height + offset)
        assert _var(
            qt_app,
            lambda offset=offset: int(window.height()) == base_height + offset,
        ), (
            f"az ablak nem vette fel a {base_height + offset} px magasságot"
        )
        qt_app.processEvents()

        _right_click(window, control, qt_app)
        menu = window.findChild(QObject, "configureButtonsContextMenu")
        assert _var(
            qt_app,
            lambda menu=menu: menu is not None
            and menu.property("visible") is True,
        ), f"a {control_name} jobb klikkje nem nyitotta meg a gombsor menüjét"

        item = window.findChild(QObject, "configureButtonsContextMenuItem")
        assert item is not None, "hiányzik a Gombok konfigurálása menüpont"
        assert int(menu.property("count")) == 1, (
            "a menüben csak a Gombok konfigurálása tétel szerepelhet; "
            "a Find buttons online… hatókörön kívüli"
        )

        QMetaObject.invokeMethod(
            item, "triggered", Qt.ConnectionType.DirectConnection
        )
        dialog = window.findChild(QObject, "configureButtonsDialog")
        assert _var(
            qt_app,
            lambda dialog=dialog: dialog is not None
            and dialog.property("visible") is True,
        ), "a menüpont nem nyitotta meg a Gombok konfigurálása párbeszédet"

        # Az Eszközök menü ugyanazt a DeferredDialog-példányt nyitja meg.
        dialog.close()
        qt_app.processEvents()
        menu_bar = window.property("menuBar")
        assert QMetaObject.invokeMethod(
            menu_bar, "configureButtonsRequested", Qt.ConnectionType.DirectConnection
        )
        assert _var(
            qt_app, lambda dialog=dialog: dialog.property("visible") is True
        )
        dialog.close()
        qt_app.processEvents()


def test_alsosav_gombsor_jobb_kattintasa(qml_app, qt_app):
    window, _controller, _engine = qml_app
    _check_context_menu(window, "trayPrintButton", qt_app)
