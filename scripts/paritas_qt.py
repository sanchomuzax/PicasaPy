"""A paritás-felvevő általános Qt-műveletei (#6845).

Valódi egér- és billentyűesemények (`QTest`), a vizuális fa bejárása minden
látható ablakban, összetett ablakkép és várakozás. Parancsot sehol nem hívunk
közvetlenül: a felületet úgy érjük el, ahogy a felhasználó.

A helyi menük és a felugró párbeszédek gyakran KÜLÖN `QQuickWindow`-ban élnek
(`popupType: Popup.Window`); az ablakkép ezeket is a főablakra komponálja,
ahogy egy képernyőfelvételen látszanának.
"""

from __future__ import annotations

import time
from collections.abc import Callable, Iterator
from typing import Any

import shiboken6
from PySide6.QtCore import QEvent, QPoint, QPointF, Qt
from PySide6.QtGui import QGuiApplication, QImage, QKeyEvent, QPainter
from PySide6.QtQuick import QQuickItem, QQuickWindow
from PySide6.QtTest import QTest

KATTINTAS_HATARIDO_MP = 5.0
HATTER_HATARIDO_MP = 30.0
STABIL_KOCKAK = 6
STABIL_HATARIDO_MP = 6.0
STABIL_MINTAKOZ_MP = 0.025
_ALVAS_MP = 0.02
_GORGETESI_MARGO = 24.0

_MODOSITOK = {
    "ctrl": Qt.KeyboardModifier.ControlModifier,
    "shift": Qt.KeyboardModifier.ShiftModifier,
    "alt": Qt.KeyboardModifier.AltModifier,
    "meta": Qt.KeyboardModifier.MetaModifier,
}
_NEVES_KULCSOK = {
    "return": Qt.Key.Key_Return,
    "escape": Qt.Key.Key_Escape,
    "tab": Qt.Key.Key_Tab,
    "backtab": Qt.Key.Key_Backtab,
    "backspace": Qt.Key.Key_Backspace,
    "delete": Qt.Key.Key_Delete,
    "insert": Qt.Key.Key_Insert,
    "space": Qt.Key.Key_Space,
    "up": Qt.Key.Key_Up,
    "down": Qt.Key.Key_Down,
    "left": Qt.Key.Key_Left,
    "right": Qt.Key.Key_Right,
    "home": Qt.Key.Key_Home,
    "end": Qt.Key.Key_End,
    "pageup": Qt.Key.Key_PageUp,
    "pagedown": Qt.Key.Key_PageDown,
}


class FuttatasiHiba(RuntimeError):
    """Egy lépés nem hajtható végre; az üzenet megmondja, mi hiányzik és mit látunk."""


# --- bejárás ------------------------------------------------------------------


def vizualis_bejaras(elem: QQuickItem) -> Iterator[QQuickItem]:
    """A VIZUÁLIS fa bejárása: a delegátumoknak nincs QObject-szülőjük."""
    for gyerek in elem.childItems():
        yield gyerek
        yield from vizualis_bejaras(gyerek)


def azonos(a: Any, b: Any) -> bool:
    return shiboken6.getCppPointer(a)[0] == shiboken6.getCppPointer(b)[0]


def lathato_ablakok(fo_ablak: Any) -> list[Any]:
    """A látható QQuickWindow-k: elöl a felugró ablakok, utolsónak a főablak."""
    masok = [
        ablak
        for ablak in QGuiApplication.topLevelWindows()
        if isinstance(ablak, QQuickWindow)
        and ablak.isVisible()
        and not azonos(ablak, fo_ablak)
    ]
    return [*masok, fo_ablak]


def lathato_e(elem: QQuickItem) -> bool:
    return bool(elem.isVisible()) and elem.width() > 0 and elem.height() > 0


def keres_lathato(fo_ablak: Any, objektumnev: str) -> tuple[Any, QQuickItem] | None:
    """Az első látható elem a névvel, az ablakával együtt (a felugró ablakok elsők)."""
    for ablak in lathato_ablakok(fo_ablak):
        for elem in vizualis_bejaras(ablak.contentItem()):
            if elem.objectName() == objektumnev and lathato_e(elem):
                return ablak, elem
    return None


def lathato_elemnevek(fo_ablak: Any, elotag: str = "") -> list[str]:
    """A látható, névvel bíró elemek nevei (hibaüzenethez és állapotkivonathoz)."""
    nevek: list[str] = []
    for ablak in lathato_ablakok(fo_ablak):
        for elem in vizualis_bejaras(ablak.contentItem()):
            nev = elem.objectName()
            if nev and nev.startswith(elotag) and lathato_e(elem):
                nevek.append(nev)
    return sorted(set(nevek))


# --- egér ----------------------------------------------------------------------


def lathatova_tesz(alkalmazas: Any, elem: QQuickItem) -> None:
    """Az elemet tartalmazó görgethető felületeket úgy görgeti, hogy az elem látsszon."""
    szulo = elem.parentItem()
    while szulo is not None:
        if (
            szulo.property("contentY") is not None
            and szulo.property("contentHeight") is not None
            and szulo.property("originY") is not None
        ):
            _gorget_hozza(alkalmazas, szulo, elem)
        szulo = szulo.parentItem()


def _gorget_hozza(alkalmazas: Any, gorgetheto: QQuickItem, elem: QQuickItem) -> None:
    magassag = float(gorgetheto.property("height"))
    teteje = float(elem.mapToItem(gorgetheto, QPointF(0, 0)).y())
    alja = teteje + float(elem.height())
    if teteje >= 0 and alja <= magassag:
        return
    cel = float(gorgetheto.property("contentY"))
    if teteje < 0:
        cel += teteje - _GORGETESI_MARGO
    else:
        cel += alja - magassag + _GORGETESI_MARGO
    kezdet = float(gorgetheto.property("originY"))
    veg = kezdet + max(0.0, float(gorgetheto.property("contentHeight")) - magassag)
    gorgetheto.setProperty("contentY", min(max(cel, kezdet), veg))
    for _ in range(3):
        alkalmazas.processEvents()


def kattint(
    alkalmazas: Any,
    ablak: Any,
    elem: QQuickItem,
    gomb: Qt.MouseButton = Qt.MouseButton.LeftButton,
    modosito: Qt.KeyboardModifier = Qt.KeyboardModifier.NoModifier,
) -> None:
    """Valódi egérkattintás az elem közepén (az elem saját ablakába)."""
    if not lathato_e(elem):
        raise FuttatasiHiba(f"{elem.objectName() or 'az elem'} nem látszik, nem kattintható.")
    kozep = elem.mapToScene(QPointF(elem.width() / 2, elem.height() / 2))
    QTest.mouseClick(ablak, gomb, modosito, QPoint(round(kozep.x()), round(kozep.y())))
    alkalmazas.processEvents()


# --- billentyű -------------------------------------------------------------------


def _fokuszablak(fo_ablak: Any) -> Any:
    return QGuiApplication.focusWindow() or fo_ablak


def billentyu_kuldese(alkalmazas: Any, fo_ablak: Any, leiras: str) -> None:
    """`ctrl+shift+o` alakú, már egységesített billentyűleírás küldése a fókuszba."""
    *modositok, gomb = leiras.split("+")
    jelzok = Qt.KeyboardModifier.NoModifier
    for modosito in modositok:
        jelzok = jelzok | _MODOSITOK[modosito]
    QTest.keyClick(_fokuszablak(fo_ablak), _kulcs(gomb), jelzok)
    alkalmazas.processEvents()


def _kulcs(gomb: str) -> Qt.Key:
    if gomb in _NEVES_KULCSOK:
        return _NEVES_KULCSOK[gomb]
    return getattr(Qt.Key, f"Key_{gomb.upper()}")


def szoveg_gepelese(alkalmazas: Any, fo_ablak: Any, szoveg: str) -> None:
    """A szöveget karakterenként, billentyűeseményként küldi a fókuszban lévő elemnek."""
    ablak = _fokuszablak(fo_ablak)
    for karakter in szoveg:
        jelzo = Qt.KeyboardModifier.NoModifier
        if karakter.isascii() and karakter.isalpha() and karakter.isupper():
            jelzo = Qt.KeyboardModifier.ShiftModifier
        if karakter.isascii():
            QTest.sendKeyEvent(
                QTest.KeyAction.Click, ablak, _karakter_kulcs(karakter), karakter, jelzo
            )
        else:
            _unicode_karakter(ablak, karakter, jelzo)
    alkalmazas.processEvents()


def _unicode_karakter(ablak: Any, karakter: str, jelzo: Qt.KeyboardModifier) -> None:
    """Nem ASCII karakter: a `QTest.sendKeyEvent` a PySide-ban `char` túlterhelést választ, és
    az UTF-8 első bájtját küldi (a `É` `Ã` lenne), ezért a billentyűeseményt magunk adjuk át."""
    for fajta in (QEvent.Type.KeyPress, QEvent.Type.KeyRelease):
        QGuiApplication.sendEvent(
            ablak, QKeyEvent(fajta, Qt.Key.Key_unknown, jelzo, karakter)
        )


def _karakter_kulcs(karakter: str) -> Qt.Key:
    if karakter == " ":
        return Qt.Key.Key_Space
    if karakter.isascii() and karakter.isprintable():
        try:
            return Qt.Key(ord(karakter.upper()))
        except ValueError:
            return Qt.Key.Key_unknown
    return Qt.Key.Key_unknown


# --- várakozás ---------------------------------------------------------------------


def pergetes(alkalmazas: Any, masodperc: float) -> None:
    """Az eseményhurkot a megadott ideig pörgeti."""
    vege = time.monotonic() + masodperc
    while time.monotonic() < vege:
        alkalmazas.processEvents()
        time.sleep(_ALVAS_MP)


def var(alkalmazas: Any, masodperc: float) -> None:
    """Az eseményhurkot a megadott ideig pörgeti, majd bevárja a háttérszálakat."""
    pergetes(alkalmazas, masodperc)
    if not var_feltetelre(alkalmazas, lambda: not hatter_dolgozik(), HATTER_HATARIDO_MP):
        raise FuttatasiHiba(
            f"A háttérmunka {HATTER_HATARIDO_MP:g} másodperc alatt sem fejeződött be."
        )


def var_feltetelre(
    alkalmazas: Any, feltetel: Callable[[], bool], hatarido_mp: float
) -> bool:
    """Pörgeti az eseményhurkot, amíg a feltétel teljesül; `False`, ha lejár az idő."""
    vege = time.monotonic() + hatarido_mp
    while True:
        alkalmazas.processEvents()
        if feltetel():
            return True
        if time.monotonic() >= vege:
            return False
        time.sleep(_ALVAS_MP)


def hatter_dolgozik() -> bool:
    """Fut-e nyilvántartott háttérmunka (a nézőkép végleges kockáját háttérszál számolja)."""
    from picasapy.app.worker_thread import running_background_workers

    return bool(running_background_workers())


# --- ablakkép -------------------------------------------------------------------------


def osszetett_ablakkep(fo_ablak: Any) -> QImage:
    """A főablak képe, rajta a látható felugró ablakokkal (menük, párbeszédek)."""
    kep = fo_ablak.grabWindow()
    felugrok = [
        ablak for ablak in lathato_ablakok(fo_ablak) if not azonos(ablak, fo_ablak)
    ]
    if not felugrok:
        return kep
    festo = QPainter(kep)
    try:
        for ablak in felugrok:
            eltolas = ablak.geometry().topLeft() - fo_ablak.geometry().topLeft()
            festo.drawImage(eltolas, ablak.grabWindow())
    finally:
        festo.end()
    return kep


def betoltetlen_belyegkepek(fo_ablak: Any) -> int:
    """A főablakban látható, de még nem festett (betöltetlen) rácskép-elemek száma."""
    szelesseg, magassag = float(fo_ablak.width()), float(fo_ablak.height())
    darab = 0
    for elem in vizualis_bejaras(fo_ablak.contentItem()):
        if elem.objectName() != "thumbImage" or not lathato_e(elem):
            continue
        hely = elem.mapToScene(QPointF(0, 0))
        if (
            hely.x() + elem.width() <= 0
            or hely.y() + elem.height() <= 0
            or hely.x() >= szelesseg
            or hely.y() >= magassag
        ):
            continue
        if (
            float(elem.property("paintedWidth")) <= 0
            or float(elem.property("paintedHeight")) <= 0
        ):
            darab += 1
    return darab


def stabil_ablakkep(alkalmazas: Any, fo_ablak: Any) -> tuple[QImage, bool]:
    """Megvárja, hogy az ablakkép, a rácskép-betöltés és a háttérmunka megálljon.

    Visszaadja a képet és a stabilitás jelét.

    Ha a határidőig nem áll meg (pl. folyamatos animáció), az utolsó képet adja
    `False` jelzéssel: a felvevő a megfigyelést nem dobja el."""
    vege = time.monotonic() + STABIL_HATARIDO_MP
    elozo: bytes | None = None
    egyezo = 0
    kep = QImage()
    while time.monotonic() < vege:
        alkalmazas.processEvents()
        kep = osszetett_ablakkep(fo_ablak)
        if hatter_dolgozik() or kep.isNull() or betoltetlen_belyegkepek(fo_ablak):
            elozo, egyezo = None, 0
        else:
            bajtok = bytes(kep.constBits())
            egyezo = egyezo + 1 if bajtok == elozo else 1
            if egyezo >= STABIL_KOCKAK:
                return kep.copy(), True
            elozo = bajtok
        time.sleep(STABIL_MINTAKOZ_MP)
    return kep.copy(), False
