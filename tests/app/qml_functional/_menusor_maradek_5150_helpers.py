"""A Menüsor maradék tételeinek valódi bemenetű segédei (#5150).

Minden tétel a főmenü fejlécére, az almenü-láncra, majd magára a tételre
kattintva indul (`QTest.mouseClick`), a gyorsbillentyűk pedig `QTest.keyClick`-kel
érkeznek az ablakra. Parancsot közvetlenül nem indítunk: nincs `triggered`,
`activated` vagy `.emit()` hívás.
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtTest import QTest

from tests.app.qml_functional._felsomenupontok_helpers_4329 import _kattints, _objektum
from tests.app.qml_functional._fomenu_4420_menu import (
    _almenu,
    _megnyit,
    _menupont,
    _normalizal,
    _szoveg,
)
from tests.app.qml_functional._nezet_menu_5150_helpers import (
    almenu_sora,
    elokeszit,
    nezet_app_epitese,
    varj,
)

__all__ = [
    "billentyu",
    "elokeszit",
    "keresomezo_szovege",
    "latszik",
    "megnyit_lanc",
    "nezet_app_epitese",
    "tetel_kattintasa",
    "tetel_kattintasa_cimlanc",
    "varj",
]


def megnyit_lanc(window, qt_app, cim: str, almenu_utvonal=()):
    """Valódi kattintásokkal megnyitja a `cim` főmenüt és az almenü-láncot.

    Visszaadja a legmélyebben megnyitott menüt.
    """
    menu_bar = window.property("menuBar")
    assert menu_bar is not None, "a főablak felső menüsora hiányzik"
    szulo = _megnyit(menu_bar, qt_app, cim)
    for almenu_nev in almenu_utvonal:
        sor, almenu = almenu_sora(window, szulo, almenu_nev)
        _kattints(qt_app, sor)
        assert varj(qt_app, lambda almenu=almenu: almenu.property("opened") is True), (
            f"a {almenu_nev} almenü nem nyílt meg valódi kattintásra"
        )
        szulo = almenu
    return szulo


def tetel_kattintasa(window, qt_app, cim: str, nev: str, almenu_utvonal=()) -> None:
    """Megnyitja a `cim` menü láncát, majd valódi kattintás a `nev` tételen."""
    megnyit_lanc(window, qt_app, cim, almenu_utvonal)
    tetel = _objektum(window, nev)
    assert tetel is not None, f"{nev} nem található"
    assert varj(qt_app, lambda: tetel.property("visible") is True), (
        f"{nev} nem látszik a megnyitott menüben"
    )
    # Az engedélyezést kötés adja (pl. Visszaállítás: a mentett másolat), ami
    # Windowson a menü megnyitása után frissülhet; a kattintás előtt kivárjuk.
    varj(qt_app, lambda: tetel.isEnabled())
    _kattints(qt_app, tetel)


def tetel_kattintasa_cimlanc(window, qt_app, cim: str, almenu_cimek, nev: str) -> None:
    """Mint a `tetel_kattintasa`, de az almenüket a FELIRATUKRA keresi.

    Az objectName nélküli almenüket (pl. az Eszközök ▸ Experimental) így lehet
    valódi kattintással megnyitni.
    """
    menu_bar = window.property("menuBar")
    assert menu_bar is not None, "a főablak felső menüsora hiányzik"
    szulo = _megnyit(menu_bar, qt_app, cim)
    for almenu_cim in almenu_cimek:
        sor, almenu = _almenu_cim_szerint(menu_bar, szulo, almenu_cim)
        _kattints(qt_app, sor)
        assert varj(qt_app, lambda almenu=almenu: almenu.property("opened") is True), (
            f"a(z) {almenu_cim} almenü nem nyílt meg valódi kattintásra"
        )
        szulo = almenu
    tetel = _objektum(window, nev)
    assert tetel is not None, f"{nev} nem található"
    assert varj(qt_app, lambda: tetel.property("visible") is True), (
        f"{nev} nem látszik a megnyitott menüben"
    )
    _kattints(qt_app, tetel)


def _almenu_cim_szerint(menu_bar, szulo, cim: str):
    kivant = _normalizal(cim)
    for index in range(int(szulo.property("count"))):
        sor = _menupont(szulo, index)
        if sor is None:
            continue
        almenu = _almenu(menu_bar, szulo, sor)
        if almenu is not None and _normalizal(_szoveg(almenu, "title")) == kivant:
            return sor, almenu
    raise AssertionError(f"a(z) {cim} almenü nem látszik a szülő menüben")


def keresomezo_szovege(window) -> str:
    mezo = _objektum(window, "searchField")
    assert mezo is not None, "a keresőmező (searchField) nem található"
    return mezo.property("text") or ""


def billentyu(window, qt_app, nev: str, kulcs, modifiers=Qt.KeyboardModifier.NoModifier) -> None:
    """A `nev` gyorsbillentyű valódi leütése az ablakon (`QTest.keyClick`)."""
    gyorsbillentyu = _objektum(window, nev)
    assert gyorsbillentyu is not None, f"{nev} nem található"
    assert gyorsbillentyu.property("enabled") is True, (
        f"{nev}: a gyorsbillentyű le van tiltva"
    )
    QTest.keyClick(window, kulcs, modifiers)
    qt_app.processEvents()


def latszik(window, nev: str) -> bool:
    elem = _objektum(window, nev)
    return elem is not None and elem.property("visible") is True
