"""A hat szín-keresés menüpontja az Eszközök menüben (#1399).

MÉRVE (`0x005ccc41`–`0x005ccca2` + `0x0065b7b0`): mind a hat parancs
UGYANAZT teszi, csak más tokennel — beírja a `color:<szín>`-t a
keresőmezőbe, a kurzort a szöveg végére viszi, és lefuttatja a keresést.
Nincs mögötte külön szűrő-mechanizmus, tehát a próba is ezt méri: a mező
SZÖVEGÉT és a lefutott keresést.

A hetedik kezelő (`color:black`) szándékosan NEM kap menüpontot: az
eredetiben sincs hozzá felirat.
"""

from __future__ import annotations

import pytest
from PySide6.QtCore import QMetaObject, QObject, Qt

SZINEK = (
    ("menuToolsSearchRed", "color:red"),
    ("menuToolsSearchOrange", "color:orange"),
    ("menuToolsSearchYellow", "color:yellow"),
    ("menuToolsSearchGreen", "color:green"),
    ("menuToolsSearchBlue", "color:blue"),
    ("menuToolsSearchPurple", "color:purple"),
)


def _child(window, nev):
    obj = window.findChild(QObject, nev)
    assert obj is not None, f"{nev} nem található"
    return obj


@pytest.mark.parametrize("menupont,token", SZINEK)
def test_a_menupont_a_keresomezobe_ir(qml_app, qt_app, menupont, token):
    window = qml_app[0]
    tetel = _child(window, menupont)

    QMetaObject.invokeMethod(tetel, "triggered", Qt.ConnectionType.DirectConnection)
    qt_app.processEvents()

    mezo = _child(window, "searchField")
    assert mezo.property("text") == token, (
        f"a {menupont} nem a keresőmezőbe írt — az eredeti a mező szövegét "
        "állítja (0x0065b7b0), nem rejtett szűrő-állapotot"
    )
    assert mezo.property("cursorPosition") == len(token), (
        "a kurzornak a szöveg VÉGÉN kell lennie (EM_SETSEL 0xFFFF,0xFFFF)"
    )


def test_a_kereses_le_is_fut(qml_app, qt_app):
    """A menüpont nemcsak ír: a nézet keresésre vált."""
    window, controller = qml_app[0], qml_app[1]
    QMetaObject.invokeMethod(
        _child(window, "menuToolsSearchRed"), "triggered",
        Qt.ConnectionType.DirectConnection,
    )
    qt_app.processEvents()

    assert controller.viewModeName == "search", (
        "a keresés nem futott le — a menüpont csak beírta a tokent, de a "
        "találatok nem frissültek (az eredeti hatodik lépése a lista "
        "újraépítése)"
    )


def test_a_feketehez_NINCS_menupont(qml_app, qt_app):
    """A hetedik kezelő (`color:black`) szándékosan kimarad.

    A diszpécserben van kezelője, de a szövegtárban nincs felirata, tehát az
    eredetiben menüből nem érhető el. Ha valaki „a teljesség kedvéért"
    felveszi, ez a próba bukik el."""
    window = qml_app[0]
    assert window.findChild(QObject, "menuToolsSearchBlack") is None
