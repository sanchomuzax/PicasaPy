"""Az Eszközök, a Létrehozás és a Súgó menü valódi kattintásos teszt-segédei (#5150, 4. rész).

Minden tétel a főmenü fejlécére (és szükség esetén az almenü sorára) kattintva
indul, valódi `QTest.mouseClick`-kel. Ezek a segédek csak a menü megnyitását,
a kattintás helyének kiszámítását és a takarítást végzik; parancsot közvetlenül
nem indítanak.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QMetaObject, QObject, Qt

from support.jpeg_factory import make_jpeg
from support.varakozas import hibaturo_feltetel, var_feltetelre
from tests.app.qml_functional._felsomenupontok_helpers_4329 import (
    _kattints,
    _objektum,
)

MAPPA = "fotok"
KEPEK = ("a_elso.jpg", "b_masodik.jpg")


def keszits_konyvtarat(lib: Path) -> None:
    cel = lib / MAPPA
    cel.mkdir()
    for nev in KEPEK:
        make_jpeg(cel / nev, size=(320, 240))


def varj(qt_app, feltetel, masodperc: float = 10.0) -> bool:
    return var_feltetelre(qt_app, hibaturo_feltetel(feltetel), masodperc)


def gyerek(window, nev: str):
    elem = _objektum(window, nev)
    assert elem is not None, f"{nev} nem található"
    return elem


def latszik(window, nev: str) -> bool:
    elem = _objektum(window, nev)
    return elem is not None and elem.property("visible") is True


def zar(qt_app, objektum) -> None:
    """Takarítás: a megnyílt párbeszédet bezárja (a `close` szabad)."""
    QMetaObject.invokeMethod(objektum, "close", Qt.ConnectionType.DirectConnection)
    qt_app.processEvents()


def elokeszit(window, qt_app, controller) -> None:
    """Megjeleníti az ablakot, betölti a `fotok` mappát, és kijelöli az első képet."""
    window.show()
    window.requestActivate()
    qt_app.processEvents()
    cel = Path(str(controller.watchedFolders[0])) / MAPPA
    controller.selectFolder(str(cel))
    assert varj(
        qt_app, lambda: len(controller.photos.photos) == len(KEPEK)
    ), "a teszt mappája nem töltődött be"
    kijelol(window, qt_app, [0])


def kijelol(window, qt_app, sorok) -> None:
    window.setProperty("selectedIndexes", list(sorok))
    window.setProperty("selectedIndex", sorok[0] if sorok else -1)
    qt_app.processEvents()


def menupont_kattintasa(window, qt_app, nev: str):
    """Valódi kattintás egy már megnyitott menü pontján; visszaadja a pontot."""
    item = gyerek(window, nev)
    assert item.property("visible") is True, f"{nev} nem látszik a menüben"
    assert item.property("enabled") is True, f"{nev} tiltott"
    _kattints(qt_app, item)
    return item


def _almenu_objektum(menu_bar, cim: str):
    return next(
        (
            elem
            for elem in menu_bar.findChildren(QObject)
            if elem.property("title") == cim and elem.property("opened") is not None
        ),
        None,
    )


def _almenu_sora(szulo, cim: str):
    """A `szulo` menü azon sora, amely a `cim` almenüt nyitja (a szöveg egyezik)."""
    pending = [szulo.property("contentItem")]
    while pending:
        item = pending.pop()
        if (
            "MenuItem" in item.metaObject().className()
            and item.property("text") == cim
            and not item.objectName()
        ):
            return item
        pending.extend(item.childItems())
    raise AssertionError(f"a(z) {cim} almenü sora nem található")


def almenu_nyit(menu_bar, qt_app, szulo, cim: str):
    """Valódi kattintással megnyitja a `szulo` menü `cim` almenüjét; visszaadja azt."""
    almenu = _almenu_objektum(menu_bar, cim)
    assert almenu is not None, f"a(z) {cim} almenü nem található"
    _kattints(qt_app, _almenu_sora(szulo, cim))
    assert varj(qt_app, lambda: almenu.property("opened") is True), (
        f"a(z) {cim} almenü nem nyílt meg valódi kattintásra"
    )
    return almenu
