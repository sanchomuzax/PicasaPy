"""A Nézet (View) menü tételeinek valódi kattintásos teszt-segédei (#5150, 2. rész).

Minden tétel a Nézet menü fejlécére (és szükség esetén az almenü sorára),
majd magára a tételre kattintva indul, valódi `QTest.mouseClick`-kel. Ezek a
segédek csak a menü megnyitását és a kattintás helyének kiszámítását végzik;
parancsot közvetlenül nem indítanak.
"""

from __future__ import annotations

from pathlib import Path

import shiboken6
from PySide6.QtCore import QObject

from conftest import _build_qml_app
from support.jpeg_factory import make_jpeg
from support.varakozas import hibaturo_feltetel, var_feltetelre
from tests.app.qml_functional._felsomenupontok_helpers_4329 import (
    _kattints,
    _objektum,
)
from tests.app.qml_functional._fomenu_4420_menu import (
    _almenu,
    _megnyit,
    _menupont,
)

MAPPA = "fotok"
KEPEK = ("a_elso.jpg", "b_masodik.jpg")


def keszits_konyvtarakat(lib: Path) -> None:
    fotok = lib / MAPPA
    fotok.mkdir()
    for nev in KEPEK:
        make_jpeg(fotok / nev, size=(320, 240))


def nezet_app_epitese(qt_app, tmp_path):
    """Teljes app a `keszits_konyvtarakat` mappával; a menüsort élve tartja.

    A menüsor Python-wrappere a GC után megsemmisítené az ablakot (ld. a
    `qml-teszt-python-wrapper-torles` tanulságot), ezért a fixture kerete
    tartja a hivatkozást a teszt végéig.
    """
    gen = _build_qml_app(qt_app, tmp_path, kepeket_keszit=keszits_konyvtarakat)
    window, controller, engine = next(gen)
    menu_bar = window.property("menuBar")
    assert menu_bar is not None, "a főablak felső menüsora hiányzik"
    yield window, controller, engine
    del menu_bar
    next(gen, None)


def varj(qt_app, feltetel, masodperc: float = 10.0) -> bool:
    return var_feltetelre(qt_app, hibaturo_feltetel(feltetel), masodperc)


def azonos(a: QObject | None, b: QObject | None) -> bool:
    """Ugyanaz a C++ objektum-e (a Python-burkolók eltérhetnek)."""
    if a is None or b is None:
        return False
    return shiboken6.getCppPointer(a)[0] == shiboken6.getCppPointer(b)[0]


def elokeszit(window, qt_app, controller) -> None:
    """Megjeleníti az ablakot, betölti a `fotok` mappát, és kijelöli az első képet."""
    window.show()
    window.requestActivate()
    qt_app.processEvents()
    controller.selectFolder(str(Path(str(controller.watchedFolders[0])) / MAPPA))
    assert varj(qt_app, lambda: len(controller.photos.photos) == len(KEPEK)), (
        "a teszt mappája nem töltődött be"
    )
    window.setProperty("selectedIndexes", [0])
    window.setProperty("selectedIndex", 0)
    qt_app.processEvents()


def almenu_sora(window, szulo, almenu_nev: str):
    """A `szulo` menü azon sora, amelyik az `almenu_nev` almenüt nyitja."""
    menu_bar = window.property("menuBar")
    almenu = _objektum(window, almenu_nev)
    assert almenu is not None, f"{almenu_nev} almenü nem található"
    for index in range(int(szulo.property("count"))):
        sor = _menupont(szulo, index)
        if sor is not None and azonos(_almenu(menu_bar, szulo, sor), almenu):
            return sor, almenu
    raise AssertionError(f"{almenu_nev} almenüje nem látszik a szülő menüben")


def almenu_nyit(window, qt_app, almenu_utvonal=()):
    """Megnyitja a Nézet menüt, majd az almenü-láncot valódi kattintásokkal.

    Visszaadja a legmélyebben megnyitott menüt (vagy a Nézet menüt, ha nincs lánc).
    """
    menu_bar = window.property("menuBar")
    assert menu_bar is not None, "a főablak felső menüsora hiányzik"
    szulo = _megnyit(menu_bar, qt_app, "&View")
    for almenu_nev in almenu_utvonal:
        sor, almenu = almenu_sora(window, szulo, almenu_nev)
        _kattints(qt_app, sor)
        assert varj(qt_app, lambda almenu=almenu: almenu.property("opened") is True), (
            f"a {almenu_nev} almenü nem nyílt meg"
        )
        szulo = almenu
    return szulo


def tetel_kattintasa(window, qt_app, nev: str, almenu_utvonal=()) -> None:
    """Megnyitja a Nézet menü láncát, majd valódi kattintás a tételen."""
    almenu_nyit(window, qt_app, almenu_utvonal)
    tetel = _objektum(window, nev)
    assert tetel is not None, f"{nev} nem található"
    assert tetel.property("visible") is True, f"{nev} nem látszik a menüben"
    _kattints(qt_app, tetel)
