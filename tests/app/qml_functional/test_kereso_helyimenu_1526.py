"""A keresőmezőn is van jobbklikk-menü (#1526).

A szövegmező-helyimenü (a Picasa `Address` menüosztálya) a #422 óta megvan,
de a KERESŐMEZŐRE nem volt rákötve — pedig azt használja a felhasználó a
leggyakrabban, és beilleszteni eddig csak billentyűvel lehetett bele.

A menü halasztott (#1720): induláskor nincs példány, csak az első
jobbklikkre épül fel. Ez a próba mindkettőt méri.
"""

from __future__ import annotations

from PySide6.QtCore import QObject


def _child(window, nev):
    obj = window.findChild(QObject, nev)
    assert obj is not None, f"{nev} nem található"
    return obj


def test_a_keresomezon_van_helyimenu_terulet(qml_app, qt_app):
    window = qml_app[0]
    terulet = _child(window, "searchFieldContextArea")

    assert terulet.property("field") is not None, (
        "a jobbklikk-terület nem a keresőmezőre mutat"
    )


def test_indulaskor_nincs_menu_peldany(qml_app, qt_app):
    """#1720: a menü csak az első jobbklikkre épül fel."""
    window = qml_app[0]
    terulet = _child(window, "searchFieldContextArea")

    assert terulet.property("contextMenu") is None, (
        "a menü már induláskor felépült — a halasztás elveszett"
    )
