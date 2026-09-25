"""#3537 — a letiltott menütétel felirata SZÜRKE.

A spec (`ui-audit-context-menus.md` 5.1): az inaktív tétel szürkén látszik.
A mérés (a jegyben): a `PicasaStyle/MenuItem.qml` címkéje mindig
`control.palette.text`-et kapott, tehát a letiltott és az engedélyezett
tétel ugyanolyan színű volt (`#1c1b19`), a palettától függetlenül.

A mérce a HELYFOGLALÓ tétel színe: a `PicasaMenuItem` azt kifejezetten
`Theme.textGray`-jel szürkíti — a letiltott sima tétel ugyanazt kapja.

A képi ellenőrzés (egy menü tiltott és élő tétellel) a kiadás képén látszik;
ez a próba a címke tényleges `color`-ját olvassa ki.
"""

from __future__ import annotations

from PySide6.QtCore import QObject


def _tetel(window, nev: str):
    tetel = window.findChild(QObject, nev)
    assert tetel is not None, f"{nev} nem található"
    return tetel


def _felirat_szerint(window, felirat: str):
    for obj in window.findChildren(QObject):
        if obj.property("text") == felirat and obj.property("placeholder") is True:
            return obj
    raise AssertionError(f"nincs ilyen helyfoglaló tétel: {felirat}")


def _cimkeszin(tetel) -> str:
    cimke = tetel.property("contentItem")
    assert cimke is not None
    return cimke.property("color").name()


def test_a_letiltott_tetel_szurke(qml_app, qt_app):
    window, _controller, _ = qml_app
    window.setProperty("selectedIndexes", [])
    window.setProperty("selectedIndex", -1)
    qt_app.processEvents()

    mentes = _tetel(window, "menuFileSave")
    helyfoglalo = _felirat_szerint(window, "&Check for Updates")

    assert mentes.property("enabled") is False
    assert _cimkeszin(mentes) == _cimkeszin(helyfoglalo)


def test_az_engedelyezett_tetel_nem_szurke(qml_app, qt_app):
    window, _controller, _ = qml_app

    mentes_ki = _tetel(window, "menuToolsBackup")
    helyfoglalo = _felirat_szerint(window, "&Check for Updates")

    assert mentes_ki.property("enabled") is True
    assert _cimkeszin(mentes_ki) != _cimkeszin(helyfoglalo)


def test_a_tiltas_feloldasa_visszaadja_a_szint(qml_app, qt_app):
    """Ugyanaz a tétel: tiltva szürke, a kijelölés után újra élő színű."""
    window, _controller, _ = qml_app
    window.setProperty("selectedIndexes", [])
    window.setProperty("selectedIndex", -1)
    qt_app.processEvents()
    mentes = _tetel(window, "menuFileSave")
    tiltott = _cimkeszin(mentes)

    window.setProperty("selectedIndexes", [0])
    window.setProperty("selectedIndex", 0)
    qt_app.processEvents()

    assert mentes.property("enabled") is True
    assert _cimkeszin(mentes) != tiltott
