"""#6861: menüfejlécek kattintása a megtartott főablakra küldve."""

from __future__ import annotations

from PySide6.QtCore import QPoint, Qt
from PySide6.QtTest import QTest

from tests.app.qml_functional._fomenu_4420_menu import _gyoker_menu, _menu_fejlec
from tests.support.varakozas import var_feltetelre


def megnyit_fomenu(window, qt_app, cim: str):
    """Valódi kattintással nyitja meg a menüt, a már megtartott ablakon."""
    menu_bar = window.property("menuBar")
    menu = _gyoker_menu(menu_bar, cim)
    fejlec = _menu_fejlec(menu_bar, cim)
    if menu.property("opened") is not True:
        kozep = fejlec.mapToScene(fejlec.boundingRect().center())
        for _ in range(2):
            QTest.mouseClick(
                window,
                Qt.MouseButton.LeftButton,
                Qt.KeyboardModifier.NoModifier,
                QPoint(round(kozep.x()), round(kozep.y())),
            )
            if var_feltetelre(qt_app, lambda: menu.property("opened") is True, 5.0):
                break
    assert menu.property("opened") is True, f"a felső {cim} menü nem nyílt meg"
    return menu
