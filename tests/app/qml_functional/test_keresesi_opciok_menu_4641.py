"""#4641: a View ▸ Search Options a keresési popup állapotát kapcsolja."""

from __future__ import annotations

import pytest
from PySide6.QtCore import QObject, QMetaObject, Qt
from PySide6.QtQml import QQmlExpression, qmlContext

from tests.app.qml_functional._fomenu_4420_menu import (
    _kattints_qobject,
    _megnyit,
)


def _keresesi_opciok_tetel(menu) -> QObject:
    for index in range(int(menu.property("count"))):
        expression = QQmlExpression(
            qmlContext(menu), menu, f"itemAt({index})"
        )
        item, error = expression.evaluate()
        assert not error, expression.error()
        if item is not None and item.property("text") == "Search &Options":
            return item
    raise AssertionError("a View menüben nincs Search Options tétel")


def _child(root, name: str) -> QObject:
    item = root.findChild(QObject, name)
    assert item is not None, f"{name} nem található"
    return item


@pytest.mark.parametrize("height_delta", [-5, 0, 5])
def test_valodi_menukattintas_es_toolbar_kattintas_ugyanazt_a_popupot_valtja(
    qml_app, qt_app, height_delta
):
    window, _controller, _engine = qml_app
    window.setHeight(window.height() + height_delta)
    window.show()
    window.requestActivate()
    qt_app.processEvents()

    menu_bar = window.property("menuBar")
    menu = _megnyit(menu_bar, qt_app, "View")
    item = _keresesi_opciok_tetel(menu)
    popup = _child(window, "searchOptionsPopup")
    button = _child(window, "searchbutton")

    assert item.property("enabled") is True, "a Search Options menüpont inaktív"
    assert item.property("checkable") is True
    assert item.property("checked") is False
    assert popup.property("opened") is False

    _kattints_qobject(qt_app, item)
    assert popup.property("opened") is True, (
        "a Nézet ▸ Keresési opciók nem nyitotta meg a keresési opció-popupot"
    )
    assert item.property("checked") is True, "a menüpipa nem követte a popupot"

    assert button.property("visible") is True
    _kattints_qobject(qt_app, button)
    assert popup.property("opened") is False, (
        "az eszköztár keresőgombja nem zárta be a menüből nyitott popupot"
    )
    assert item.property("checked") is False, (
        "a menüpipa nem követte a popup bezárását"
    )

    menu = _megnyit(menu_bar, qt_app, "View")
    item = _keresesi_opciok_tetel(menu)
    _kattints_qobject(qt_app, item)
    assert popup.property("opened") is True, (
        "a menüpont nem nyitotta meg újra az eszköztárból bezárt popupot"
    )
    assert item.property("checked") is True

    # Ha a popup nyitva van, a menüsor fejlécére kattintás maga is külső
    # kattintás és bezárná azt. A záró ágat ezért úgy mérjük, hogy a menü
    # megnyílik a popup mellett, utána a tényleges menüpontot kattintjuk.
    assert QMetaObject.invokeMethod(
        menu, "open", Qt.ConnectionType.DirectConnection
    )
    qt_app.processEvents()
    assert menu.property("opened") is True
    item = _keresesi_opciok_tetel(menu)
    _kattints_qobject(qt_app, item)
    assert popup.property("opened") is False, "a menüpont nem zárta be a popupot"
    assert item.property("checked") is False
