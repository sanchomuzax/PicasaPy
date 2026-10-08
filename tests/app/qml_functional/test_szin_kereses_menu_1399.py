"""A hét szín-keresés menüpontja a KÍSÉRLETI almenüben (#1399, #4689).

## A hely — mérve, és az első nekifutásom rossz volt

Az `eMenuTools` névtér mind a 36 kulcsát EGYETLEN menüépítő függvény
használja, és abból kiderül, hogy a `Searchfor ▸` almenü a **Kísérleti**
almenü HARMADIK tétele (a `Show Duplicate Files` után), nem a felső szinté
(`docs/specs/picasa-menusor-csoportok.md`, az `eMenuTools`-táblázat).

Az első változatom a felső szintre tette, és a menü-csoport őre
(`test_menusor_csoportok_1774`) joggal buktatta meg: a felső szint mért
sorrendjében nincs ilyen tétel. A visszavétel és a helyes hely megtalálása
ezért nem hangulat kérdése volt — a bizonyíték döntötte el.

## A viselkedés — szintén mérve

`0x005ccc41`–`0x005ccca2` + `0x0065b7b0`: mind a hat parancs ugyanazt teszi,
csak más tokennel — beírja a `color:<szín>`-t a keresőmezőbe, a kurzort a
szöveg végére viszi (`EM_SETSEL 0xFFFF,0xFFFF`), és lefuttatja a keresést.

Az eredeti hetedik tétele a `ID_VIEW_BW` (`&Black and White`, parancs
`0x9da9`), amely `color:black` keresést indít (`0x005ccca7`).
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
    ("menuToolsSearchBlack", "color:black"),
)


def _child(window, nev):
    obj = window.findChild(QObject, nev)
    assert obj is not None, f"{nev} nem található"
    return obj


@pytest.mark.parametrize("menupont,token", SZINEK)
def test_a_menupont_a_keresomezobe_ir(qml_app, qt_app, menupont, token):
    window = qml_app[0]
    QMetaObject.invokeMethod(
        _child(window, menupont), "triggered", Qt.ConnectionType.DirectConnection
    )
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
    window, controller = qml_app[0], qml_app[1]
    QMetaObject.invokeMethod(
        _child(window, "menuToolsSearchRed"), "triggered",
        Qt.ConnectionType.DirectConnection,
    )
    qt_app.processEvents()

    assert controller.viewModeName == "search", (
        "a keresés nem futott le — a menüpont csak beírta a tokent (az "
        "eredeti hatodik lépése a lista újraépítése)"
    )


def test_a_fekete_feher_tetel_megjelenik(qml_app):
    """Az eredeti `ID_VIEW_BW` parancsa a hetedik tétel."""
    tetel = qml_app[0].findChild(QObject, "menuToolsSearchBlack")
    assert tetel is not None, "a Search for... hetedik tétele hiányzik"
