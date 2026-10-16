"""#4623: a Nézet menü Kis / Normál indexképek és Szerkesztési nézet tétele
rádiócsoportot alkot (egy pipa a háromból), és a pipa követi a méretet.

A spec (`docs/specs/picasa-menusor-csoportok.md`, Nézet 2. csoport) szerint a
csoport rádiószerű: az aktuális előbeállítás pipás, más méretnél (csúszkával
állítva) egyik sincs pipálva. A Szerkesztési nézet a nézőben pipás, és ilyenkor
a két indexképtétel nem pipás.

A valódi kattintás előbb `toggle()`-t hív, és a már aktív tételre kattintva a
pipa elveszne (#1468). Ezért a kezelő visszakötött `checked`-et állít be, és a
teszt a menü ÚJRANYITÁSA után nézi a pipákat.
"""

from __future__ import annotations

from PySide6.QtCore import QMetaObject, QObject, QPoint, QPointF, Qt
from PySide6.QtTest import QTest

import pytest

from tests.app.qml_functional._fomenu_4420_menu import _varj

_ABLAKMAGASSAG_ELTOLASOK = (-5, 0, 5)
_KIS = 96
_NORMAL = 144
_KIS_NEV = "menuViewSmallThumbnails"
_NORMAL_NEV = "menuViewNormalThumbnails"
_SZERKESZTES_NEV = "menuViewEditView"
# a csúszka sávjának 0…1 arányú pontja, ami nem esik a két előbeállításra
_EGYEDI_ARANY = 0.26


class _TesztQmlElem(QObject):
    def __init__(self, nev, tulajdonsagok, osztaly="", szulo=None):
        super().__init__(szulo)
        self.setObjectName(nev)
        self._tulajdonsagok = tulajdonsagok
        self._osztaly = osztaly

    def property(self, nev):
        return self._tulajdonsagok.get(nev)

    def inherits(self, nev):
        return self._osztaly == nev


class _TesztNezetAblak(QObject):
    def property(self, nev):
        if nev == "menuBar":
            # A PySide wrapper-cache hibáját utánozza: a QObject property
            # olvasása QMetaObject wrapperrel tér vissza.
            return QMetaObject()
        return super().property(nev)


def _objektum(window, nev):
    return window.findChild(QObject, nev)


_NEZET_FELIRATOK = {"&View", "&Nézet"}
# A PySide-wrapperek élettartamát a teszt tartja: az eldobott referencia
# (GC) a QML-fa elemeit is megsemmisítette (a következő lépésnél „already
# deleted"), ezért a menüelemeket ide tesszük, mint a _fomenu_4420_menu.py.
_QML_ELEMEK: list = []


def test_nezet_menu_keresese_turi_a_menu_bar_property_qmetaobject_valaszat(
    qt_app,
):
    window = _TesztNezetAblak()
    menu = _TesztQmlElem(
        "menuView", {"title": "&View", "opened": True}, szulo=window
    )
    _TesztQmlElem(
        "viewHeader",
        {"text": "&View"},
        osztaly="QQuickMenuBarItem",
        szulo=window,
    )

    _nezet_menu(window, qt_app)

    assert menu.property("opened") is True


def _kattints(qt_app, elem) -> None:
    """Valódi egérkattintás az elem közepén (a menüsor fejlécén is)."""
    assert elem is not None, "a kattintandó menüelem hiányzik"
    kozep = elem.mapToScene(QPointF(elem.width() / 2, elem.height() / 2))
    QTest.mouseClick(
        elem.window(),
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        QPoint(round(kozep.x()), round(kozep.y())),
    )
    qt_app.processEvents()


def _nezet_menu(window, qt_app) -> None:
    """A felső Nézet menü megnyitása, a QML-fa kész állapotára várva.

    A `menuBar` QML property PySide-olvasása a QML-engine-ek újraépülése
    után elavult `QMetaObject` wrappert adhat vissza. A menü és a fejléce
    név/típus alapján közvetlenül az ablak objektumfájából kereshető; így nem
    használjuk a bizonytalan property-wrappert, és nem hagyunk életben
    `metaObject()` burkot sem.
    """
    talalat = [None, None]

    def menu_es_fejlec_elkeszult() -> bool:
        menu = _objektum(window, "menuView")
        fejlec = next(
            (
                item
                for item in window.findChildren(QObject)
                if item.inherits("QQuickMenuBarItem")
                and item.property("text") in _NEZET_FELIRATOK
            ),
            None,
        )
        if menu is None or fejlec is None:
            return False
        talalat[:] = [menu, fejlec]
        return True

    assert _varj(qt_app, menu_es_fejlec_elkeszult), (
        "a Nézet menü vagy a fejléce nem épült fel"
    )
    menu, fejlec = talalat
    _QML_ELEMEK.extend((menu, fejlec))
    if menu.property("opened") is not True:
        _kattints(qt_app, fejlec)
    assert _varj(qt_app, lambda: menu.property("opened") is True), (
        "a felső Nézet menü nem nyílt meg"
    )


def _zarj_nezet_menut(window, qt_app) -> None:
    menu = _objektum(window, "menuView")
    if menu is not None and menu.property("opened"):
        QMetaObject.invokeMethod(menu, "close", Qt.ConnectionType.DirectConnection)
    qt_app.processEvents()


def _pipak(window, qt_app) -> dict[str, bool]:
    """A három tétel pipája a Nézet menü ÚJRA-megnyitása után."""
    _nezet_menu(window, qt_app)
    elemek = {
        nev: _nezet_menupont(window, qt_app, nev)
        for nev in (_KIS_NEV, _NORMAL_NEV, _SZERKESZTES_NEV)
    }
    allapot = {
        nev: elem.property("checked") is True for nev, elem in elemek.items()
    }
    _zarj_nezet_menut(window, qt_app)
    return allapot


def _kattints_nezet(window, qt_app, nev: str) -> None:
    _nezet_menu(window, qt_app)
    _kattints(qt_app, _nezet_menupont(window, qt_app, nev))
    _zarj_nezet_menut(window, qt_app)


def _nezet_menupont(window, qt_app, nev: str):
    elem = [None]

    def menupont_lathato() -> bool:
        talalat = _objektum(window, nev)
        if talalat is None or talalat.property("visible") is not True:
            return False
        elem[0] = talalat
        return True

    assert _varj(qt_app, menupont_lathato), (
        f"a {nev} menüpont nem jelent meg a megnyitott menüben"
    )
    _QML_ELEMEK.append(elem[0])
    return elem[0]


def _magassag(window, offset: int) -> None:
    window.setHeight(window.height() + offset)


def _csuszkon_kattints(window, qt_app, arany: float) -> None:
    """Egérkattintás a `traySizeSlider` sínjén az adott arányú helyen.

    A sáv billentyűs léptetése ki van kapcsolva (`keyboardStepEnabled`
    hamis), ezért a csúszkát egérrel kell megmozgatni.
    """
    slider = _objektum(window, "traySizeSlider")
    assert slider is not None, "a csúszka hiányzik a párhuzamos sávból"
    kozep_y = slider.height() / 2
    pont = slider.mapToScene(QPointF(slider.width() * arany, kozep_y))
    QTest.mousePress(
        window,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        QPoint(round(pont.x()), round(pont.y())),
    )
    QTest.mouseRelease(
        window,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        QPoint(round(pont.x()), round(pont.y())),
    )
    qt_app.processEvents()


def _meret_allitas(window, qt_app, meret: int) -> None:
    window.setProperty("thumbSize", meret)
    qt_app.processEvents()


@pytest.mark.parametrize("height_offset", _ABLAKMAGASSAG_ELTOLASOK)
def test_normal_indexkep_pipas_alapmeretnel(qml_app, qt_app, height_offset):
    window, _controller, _engine = qml_app
    _magassag(window, height_offset)
    _meret_allitas(window, qt_app, _NORMAL)

    assert _pipak(window, qt_app) == {
        _KIS_NEV: False,
        _NORMAL_NEV: True,
        _SZERKESZTES_NEV: False,
    }


@pytest.mark.parametrize("height_offset", _ABLAKMAGASSAG_ELTOLASOK)
def test_menubol_valtas_es_ujrakattintas_megtartja_a_pipat(
    qml_app, qt_app, height_offset
):
    window, _controller, _engine = qml_app
    _magassag(window, height_offset)
    _meret_allitas(window, qt_app, _NORMAL)

    _kattints_nezet(window, qt_app, _KIS_NEV)
    assert window.property("thumbSize") == _KIS
    assert _pipak(window, qt_app) == {
        _KIS_NEV: True,
        _NORMAL_NEV: False,
        _SZERKESZTES_NEV: False,
    }

    _kattints_nezet(window, qt_app, _NORMAL_NEV)
    assert window.property("thumbSize") == _NORMAL
    _kattints_nezet(window, qt_app, _NORMAL_NEV)
    assert _pipak(window, qt_app) == {
        _KIS_NEV: False,
        _NORMAL_NEV: True,
        _SZERKESZTES_NEV: False,
    }


@pytest.mark.parametrize("height_offset", _ABLAKMAGASSAG_ELTOLASOK)
def test_csuszka_egyedi_meretnel_egyik_tetel_sincs_pipalva(
    qml_app, qt_app, height_offset
):
    window, _controller, _engine = qml_app
    _magassag(window, height_offset)
    _meret_allitas(window, qt_app, _NORMAL)

    _csuszkon_kattints(window, qt_app, _EGYEDI_ARANY)
    meret = window.property("thumbSize")
    assert meret not in (_KIS, _NORMAL), (
        f"a csúszka a célzott egyedi méretet nem adta: {meret}"
    )
    assert _pipak(window, qt_app) == {
        _KIS_NEV: False,
        _NORMAL_NEV: False,
        _SZERKESZTES_NEV: False,
    }


@pytest.mark.parametrize("height_offset", _ABLAKMAGASSAG_ELTOLASOK)
def test_szerkesztesi_nezetben_csak_a_szerkesztesi_tetel_pipas(
    qml_app, qt_app, height_offset
):
    window, _controller, _engine = qml_app
    _magassag(window, height_offset)
    _meret_allitas(window, qt_app, _NORMAL)
    window.setProperty("selectedIndexes", [0])
    window.setProperty("selectedIndex", 0)
    qt_app.processEvents()

    _kattints_nezet(window, qt_app, _SZERKESZTES_NEV)
    assert _varj(qt_app, lambda: window.property("viewerOpen") is True)

    assert _pipak(window, qt_app) == {
        _KIS_NEV: False,
        _NORMAL_NEV: False,
        _SZERKESZTES_NEV: True,
    }
