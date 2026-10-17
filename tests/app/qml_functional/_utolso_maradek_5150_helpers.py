"""Az utolsó maradék vezérlők VALÓDI bemenetű segédei (#5150, utolsó rész).

A két tesztfájl (`test_utolso_maradek_valodi_5150_r.py` és `..._s.py`) közös
eszközei:

- `varj`: várakozás; a korlát 10 mp (`tests/test_varakozas_or_4970.py`).
- `kattint` / `kattint_elemre`: valódi egérkattintás. Előbb ellenőrzi, hogy a
  célelem látszik, van mérete, és (főablakban) az ablak területén belül van.
  Így a kattintás nem eshet néma kihagyásként a mögötte lévő elemre
  (ld. `test_mentes_fa_kattintas_5210.py`).
- `erintes_kattintas`: érintőkezelő (TapHandler) kattintása a szülőelemén.
- `gepel` / `kijelol_mindent`: billentyűleütések a fókuszált mezőre.
- `keszit_motort` / `keszit_ablakot`: inline QML-ből látszó ablak, a kattintás
  célja. Ugyanaz a stílus és betű, mint a valódi appban (#3696).
- `szoveges_elem`: a látható elem a `text` tulajdonsága alapján (például egy
  legördülő lista tétele, amelynek nincs objectName-je).
- `utvonal`: útvonal `Path`-ként (ld. `tests/test_utvonal_osszevetes_or_5155.py`).
- `lista`: a QML-tömb Python listaként.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import shiboken6
from PySide6.QtCore import QPointF, QUrl, Qt
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlComponent, QQmlEngine
from PySide6.QtTest import QTest

import picasapy.app.application as app_module
from support.varakozas import hibaturo_feltetel, var_feltetelre
from tests.app.qml_functional._racs_helyimenuk_5150_helpers import kattints
from tests.app.qml_functional._racs_maradek_5150_helpers import az_ablakban, keres

#: a Python-wrapperek GC-je alól kiveszi az inline QML-motort és ablakokat
_KEEPALIVE: list[object] = []

#: a nem betűs billentyűk neve a `Qt.Key`-ben (a betűk és számjegyek `Key_<NAGY>`)
_JELEK = {" ": "Space", ".": "Period", "/": "Slash", "-": "Minus", "_": "Underscore"}


def varj(qt_app, feltetel: Callable[[], bool], masodperc: float = 10.0) -> bool:
    """Megvárja a feltételt. A korlát legalább 10 mp (ld. a várakozás-őrt)."""
    return var_feltetelre(qt_app, hibaturo_feltetel(feltetel), masodperc)


def utvonal(ertek) -> Path:
    """Útvonalat `Path`-ként ad vissza, hogy a platformok összevetése egyezzen (#5155)."""
    return Path(str(ertek))


def kattint_elemre(window, qt_app, elem, gomb=Qt.MouseButton.LeftButton) -> None:
    """Valódi kattintás az `elem` közepén, az előzetes ellenőrzésekkel."""
    qt_app.processEvents()
    assert elem.isVisible() and elem.width() > 0 and elem.height() > 0, (
        f"{elem.objectName() or 'névtelen elem'}: nem látszik vagy nulla méretű"
    )
    kattints(window, qt_app, elem, gomb)


def kattint(window, qt_app, nev: str, gomb=Qt.MouseButton.LeftButton):
    """Valódi kattintás a `nev` objectName-ű elemen; előbb ellenőrzi a helyzetét.

    Megvárja, hogy az elem megálljon (az animált nyitás után). Ha a főablakban
    van, ellenőrzi, hogy teljesen látszik-e az ablakon belül. A saját ablakban
    nyíló menü- és párbeszédelemeknél csak a látszást és a méretet nézi.
    Visszaadja az elemet."""
    elem = keres(window, nev)
    _megall(qt_app, elem)
    if _fo_ablakban(window, elem):
        assert az_ablakban(window, elem), f"{nev}: nem látszik teljesen a főablakon belül"
    kattint_elemre(window, qt_app, elem, gomb)
    return elem


def _megall(qt_app, elem) -> None:
    """Megvárja, hogy az elem helye megálljon (az animált nyitás végére).

    Két egymás utáni azonos helyzet jelzi, hogy megállt. A helyzetet a saját
    ablakához képest mérjük, ezért itt nem nézzük a főablak határát."""
    elozo: list[tuple[float, float] | None] = [None]

    def megallt() -> bool:
        pont = elem.mapToScene(QPointF(0, 0))
        helyzet = (pont.x(), pont.y())
        allt = helyzet == elozo[0]
        elozo[0] = helyzet
        return allt

    assert varj(qt_app, megallt), f"{elem.objectName()}: a helye nem állt meg"


def _fo_ablakban(window, elem) -> bool:
    """Igaz, ha az elem a főablak vizuális fájában van (nem külön menü-ablakban).

    A C++-mutatót hasonlítjuk: a PySide-wrapper azonossága nem garantált."""
    cel = shiboken6.getCppPointer(elem)[0]
    return any(
        shiboken6.getCppPointer(item)[0] == cel
        for item in _leszarmazottak(window.contentItem())
    )


def _leszarmazottak(item):
    for gyerek in item.childItems():
        yield gyerek
        yield from _leszarmazottak(gyerek)


def erintes_kattintas(window, qt_app, nev: str) -> None:
    """Valódi kattintás egy érintőkezelő (TapHandler) szülőelemén.

    A kezelőnek nincs geometriája, ezért a szülőelemét (például a szöveget)
    kattintjuk. Előbb a kezelő létezését és a szülő látszását ellenőrizzük."""
    kezelo = keres(window, nev)
    kattint_elemre(window, qt_app, kezelo.parent())


def szoveges_elem(window, szoveg: str):
    """A látható elem, amelynek a `text` tulajdonsága `szoveg` (objectName nélkül is)."""
    talalat = _szoveges_talalat(window.contentItem(), szoveg)
    assert talalat is not None, f"nincs látható tétel ezzel a felirattal: {szoveg}"
    return talalat


def _szoveges_talalat(item, szoveg: str):
    for gyerek in item.childItems():
        if gyerek.isVisible() and gyerek.property("text") == szoveg:
            return gyerek
        talalat = _szoveges_talalat(gyerek, szoveg)
        if talalat is not None:
            return talalat
    return None


def gepel(window, qt_app, szoveg: str) -> None:
    """Billentyűleütések sora a fókuszált mezőre (`QTest.keyClick`).

    A nagybetűt a karakteres `keyClick` adja, a többi karaktert billentyűkód.
    Csak ASCII szöveget gépelünk, mert az ékezetes betűt a billentyűkód nem adja meg."""
    for karakter in szoveg:
        if karakter.isupper():
            QTest.keyClick(window, karakter)
        else:
            nev = _JELEK.get(karakter, karakter.upper())
            QTest.keyClick(window, getattr(Qt.Key, f"Key_{nev}"))
        qt_app.processEvents()


def kijelol_mindent(window, qt_app) -> None:
    """Ctrl+A: a fókuszált mező teljes tartalmát kijelöli, hogy a gépelés felülírja."""
    QTest.keyClick(window, Qt.Key.Key_A, Qt.KeyboardModifier.ControlModifier)
    qt_app.processEvents()


def keszit_motort(qt_app) -> QQmlEngine:
    """QML-motor a PicasaPy-modul könyvtárával; a stílus és a betű a valódi appé."""
    app_module.allitsd_be_a_stilust()
    app = QGuiApplication.instance()
    if app is not None:
        app_module._install_ui_font(app)
    motor = QQmlEngine()
    motor.addImportPath(str(app_module._APP_DIR / "qml"))
    _KEEPALIVE.append(motor)
    return motor


def keszit_ablakot(qt_app, motor: QQmlEngine, qml: str):
    """Inline QML-ből látszó ablak: a gyökér `Window`/`ApplicationWindow` példánya."""
    komponens = QQmlComponent(motor)
    komponens.setData(qml.encode(), QUrl())
    assert not komponens.errors(), komponens.errorString()
    ablak = komponens.create()
    assert ablak is not None, komponens.errorString()
    _KEEPALIVE.extend((komponens, ablak))
    assert varj(qt_app, lambda: ablak.isExposed()), "az ablak nem jelent meg"
    return ablak


def lista(ertek) -> list:
    """A QML-tömb Python listaként (a QVariant-csomagolót eltávolítja)."""
    if hasattr(ertek, "toVariant"):
        ertek = ertek.toVariant()
    return list(ertek or [])
