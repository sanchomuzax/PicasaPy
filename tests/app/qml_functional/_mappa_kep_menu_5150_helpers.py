"""A Mappa és a Kép menü, valamint a Kép ▸ Csoportos szerkesztés valódi kattintásos
teszt-segédei (#5150, 3. rész).

Minden tétel a főmenü fejlécére (és szükség esetén az almenü sorára) kattintva
indul, valódi `QTest.mouseClick`-kel. Parancsot közvetlenül nem indítunk: nincs
`triggered`/`clicked`/`activated` hívás és nincs `.emit()`. A hatást a vezérlő
állapotán, a lemezen maradt `.picasa.ini`-n vagy a párbeszédek láthatóságán
mérjük. A párbeszédek takarításához a `close` hívás szabad.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QMetaObject, QObject, Qt

from conftest import _build_qml_app
from picasapy.ini import load_document
from picasapy.scanner import PICASA_INI_NAME
from support.jpeg_factory import make_jpeg
from support.varakozas import hibaturo_feltetel, var_feltetelre
from tests.app.qml_functional._felsomenupontok_helpers_4329 import (
    _kattints,
    _objektum,
)
from tests.app.qml_functional._fomenu_4420_menu import _megnyit
from tests.app.qml_functional._nezet_menu_5150_helpers import almenu_sora

MAPPA = "fotok"
KEPEK = ("a_nagy.jpg", "b_kicsi.jpg", "c_kozepes.jpg")
#: a `size` (bájt) szerinti növekvő sorrend, a név- és dátumsorrendtől eltérően
MERET_SZERINT = ["b_kicsi.jpg", "c_kozepes.jpg", "a_nagy.jpg"]


#: a rács mappa-blokkjainak második mappája (a Mappa ▸ Rendezés teszteléséhez)
MASIK = "masik"


def keszits_konyvtarat(lib: Path) -> None:
    fotok = lib / MAPPA
    fotok.mkdir()
    make_jpeg(fotok / "a_nagy.jpg", size=(640, 480))
    make_jpeg(fotok / "b_kicsi.jpg", size=(40, 30))
    make_jpeg(fotok / "c_kozepes.jpg", size=(200, 150))


def keszits_ket_mappat(lib: Path) -> None:
    """A `fotok` mappa mellé egy NAGYOBB `masik` mappa.

    Név szerint (növekvő) a `fotok` áll elöl; méret szerint (a Picasa alapján
    csökkenő) a `masik`, mert egyetlen 1600×1200-as képe (~30 KB) nagyobb, mint
    a `fotok` három képe együtt (~7 KB)."""
    keszits_konyvtarat(lib)
    masik = lib / MASIK
    masik.mkdir()
    make_jpeg(masik / "d_nagy.jpg", size=(1600, 1200))


def app_epitese(qt_app, tmp_path, kepeket_keszit=keszits_konyvtarat):
    """Teljes app a megadott képmappákkal; a menüsort élve tartja.

    A menüsor Python-wrappere a GC után megsemmisítené az ablakot (ld. a
    `qml-teszt-python-wrapper-torles` tanulságot), ezért a fixture kerete
    tartja a hivatkozást a teszt végéig.
    """
    gen = _build_qml_app(qt_app, tmp_path, kepeket_keszit=kepeket_keszit)
    window, controller, engine = next(gen)
    menu_bar = window.property("menuBar")
    assert menu_bar is not None, "a főablak felső menüsora hiányzik"
    yield window, controller, engine
    del menu_bar
    next(gen, None)


def varj(qt_app, feltetel, masodperc: float = 10.0) -> bool:
    return var_feltetelre(qt_app, hibaturo_feltetel(feltetel), masodperc)


def gyerek(window, nev: str):
    elem = _objektum(window, nev)
    assert elem is not None, f"{nev} nem található"
    return elem


def mappa_ut(controller) -> Path:
    return Path(str(controller.watchedFolders[0])) / MAPPA


def kijelol(window, qt_app, sorok) -> None:
    window.setProperty("selectedIndexes", list(sorok))
    window.setProperty("selectedIndex", sorok[0] if sorok else -1)
    qt_app.processEvents()


def elokeszit(window, qt_app, controller) -> Path:
    """Megjeleníti az ablakot, betölti a `fotok` mappát, és kijelöli az első képet."""
    window.show()
    window.requestActivate()
    qt_app.processEvents()
    cel = mappa_ut(controller)
    controller.selectFolder(str(cel))
    assert varj(qt_app, lambda: len(controller.photos.photos) == len(KEPEK)), (
        "a teszt mappája nem töltődött be"
    )
    kijelol(window, qt_app, [0])
    return cel


def tetel_kattintasa(window, qt_app, cim: str, nev: str, almenu_utvonal=()) -> None:
    """Valódi kattintásokkal megnyitja a `cim` menüt és az almenü-láncot, majd
    a `nev` tételre kattint."""
    menu_bar = window.property("menuBar")
    szulo = _megnyit(menu_bar, qt_app, cim)
    for almenu_nev in almenu_utvonal:
        sor, almenu = almenu_sora(window, szulo, almenu_nev)
        _kattints(qt_app, sor)
        assert varj(qt_app, lambda almenu=almenu: almenu.property("opened") is True), (
            f"a(z) {almenu_nev} almenü nem nyílt meg a valódi kattintásra"
        )
        szulo = almenu
    tetel = gyerek(window, nev)
    assert tetel.property("visible") is True, f"{nev} nem látszik a menüben"
    _kattints(qt_app, tetel)


def zar(qt_app, objektum) -> None:
    """Takarítás: a megnyílt párbeszédet bezárja (a `close` szabad)."""
    QMetaObject.invokeMethod(objektum, "close", Qt.ConnectionType.DirectConnection)
    qt_app.processEvents()


def szures(controller, sor: int) -> str:
    """A `sor`-hoz tartozó kép `filters=` lánca a lemezre írt `.picasa.ini`-ből."""
    foto = controller.photos.photos[sor]
    ini = Path(foto.folder_path) / PICASA_INI_NAME
    if not ini.exists():
        return ""
    szakasz = load_document(ini).section(foto.name)
    return (szakasz.get("filters") if szakasz is not None else None) or ""


def nyitott(elem: QObject | None) -> bool:
    """Látszik-e a párbeszéd: a `Popup`-alapú (`opened`) és az ablak-alapú
    (`visible`) párbeszédek egyaránt."""
    if elem is None:
        return False
    return elem.property("opened") is True or elem.property("visible") is True
