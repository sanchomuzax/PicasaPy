"""#4420: a főmenü-bejáró segédfüggvényének regressziós próbája."""

from __future__ import annotations

from PySide6.QtCore import QMetaObject, QObject

from tests.app.qml_functional import _fomenu_4420_menu as _menu_segedek


def test_parancsok_kihagyja_a_nem_qobject_menuelemet(monkeypatch):
    class Kifejezes:
        def evaluate(self):
            return QMetaObject(), None

    monkeypatch.setattr(
        _menu_segedek,
        "QQmlExpression",
        lambda *_args: Kifejezes(),
    )
    menu = QObject()
    menu.setProperty("count", 1)

    assert _menu_segedek._parancsok(menu, QObject()) == []
