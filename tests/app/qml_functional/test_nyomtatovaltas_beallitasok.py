"""Nyomtatóváltás VALÓDI kattintásokkal: a párbeszéd nyitva marad, a beállítások megmaradnak.

## Miért van itt

Egy korábbi teszt-kör gyanította, hogy a nyomtató-választó (`printPrinterBox`)
valódi kattintásos kiválasztása után a párbeszéd C++ objektuma újra létrejön:
a régi Python-wrapper `shiboken6.isValid`-je hamis lesz. Ha ez igaz, a
párbeszéd bezáródik vagy újranyílik, és a felhasználó elveszíti a
beállításait (példányszám, méret, tájolás, illesztés).

## Mit mér ez a fájl

Két hamis nyomtató (`HamisInfo`) mellett, a Fájl menüből nyitott
párbeszédben: valódi kattintásokkal állítunk be több mindent, majd valódi
kattintással a másik nyomtatóra váltunk. Utána azt nézzük, hogy UGYANAZ a
párbeszéd-objektum még él-e, volt-e láthatósági átmenet, nem jött-e létre
második példány, és a beállítások, valamint a kijelölt képek megmaradtak-e.

A gyanú ezen az úton NEM igazolódott: az objektum ugyanaz marad, nem zárul be,
és a beállítások megmaradnak. A teszt ezt rögzíti; regresszió esetén bukik.

A nyomtatás maga nem fut: a nyomtatók nevei hamisak, a `printRows` nem
indul el.
"""

from __future__ import annotations

import pytest
import shiboken6
from PySide6.QtCore import QObject, QPointF
from PySide6.QtGui import QPageSize

from tests.app.qml_functional.test_nyomtatas_bekotes_1472 import (
    _kijelol,
    _menubol_nyit,
    _sorok,
)
from tests.app.qml_functional.test_nyomtatas_egyseges_meretlista_3712 import (
    _kattints_kozepere,
    _legordulo_tetele,
    _lista,
    _varakozzon,
)
from tests.support.varakozas import hibaturo_feltetel, var_feltetelre

# #664 mintája: a QtPrintSupport nélkül a nyomtatás bekötése sem mérhető.
try:
    import PySide6.QtPrintSupport  # noqa: F401

    _QTPRINTSUPPORT_VAN = True
except ImportError:  # pragma: no cover - csak a hiányos telepítésen fut
    _QTPRINTSUPPORT_VAN = False

pytestmark = pytest.mark.skipif(
    not _QTPRINTSUPPORT_VAN,
    reason=(
        "a PySide6.QtPrintSupport modul hiányzik ezen a gépen, ezért a "
        "nyomtatóváltás próbái kimaradnak. Debian/Ubuntu alatt így pótolható: "
        "sudo apt install python3-pyside6.qtprintsupport"
    ),
)

PRINTER_A = "PicasaPy-proba-nyomtato-A"
PRINTER_B = "PicasaPy-proba-nyomtato-B"
NYOMTATOK = [PRINTER_A, PRINTER_B]

# A `printPrinterBox` modellje: 0 = PDF-fájlba, utána a nyomtatók.
INDEX_PDF = 0
INDEX_A = 1
INDEX_B = 2
# A `printOrientationBox` modellje: Automatic, Portrait, Landscape.
INDEX_LANDSCAPE = 2


class HamisInfo:
    """A `QPrinterInfo` helyettese a `print_controller` modul névterében.

    Két ismert nyomtató van, mindkettő A4 alapmérettel. Az ismeretlen név
    `isNull()`-t ad, ahogy a valódi `QPrinterInfo` is.
    """

    def __init__(self, nev: str) -> None:
        self._nev = nev

    def isNull(self) -> bool:  # noqa: N802 - Qt-névalak
        return self._nev not in NYOMTATOK

    def defaultPageSize(self) -> QPageSize:  # noqa: N802 - Qt-névalak
        return QPageSize(QPageSize.PageSizeId.A4)

    @staticmethod
    def printerInfo(nev: str) -> "HamisInfo":  # noqa: N802 - Qt-névalak
        return HamisInfo(nev)

    @staticmethod
    def availablePrinterNames() -> list[str]:  # noqa: N802 - Qt-névalak
        return list(NYOMTATOK)


@pytest.fixture(autouse=True)
def _hamis_nyomtatok(monkeypatch):
    import picasapy.app.print_controller as pc_modul

    monkeypatch.setattr(pc_modul, "QPrinterInfo", HamisInfo)


@pytest.fixture(autouse=True)
def _huvelykes_terulet(monkeypatch):
    """A méretlista az eredeti hüvelykes készlet; a gép területi beállítása
    ne döntse el, melyik készletet kapjuk (#4435)."""
    from picasapy.printing import dpi

    monkeypatch.setattr(dpi, "_metrikus_teruleti_meres", lambda: False)


def _elem(root, nev):
    obj = root.findChild(QObject, nev)
    assert obj is not None, f"{nev} nem található"
    return obj


def _kattint(parbeszed, qt_app, nev):
    """Valódi bal kattintás a `nev` elem közepére."""
    elem = _elem(parbeszed, nev)
    assert elem.property("enabled") is True, f"{nev}: le van tiltva, a kattintás nem hatna"
    pont = elem.mapToScene(QPointF(elem.width() / 2, elem.height() / 2))
    assert 0 <= pont.y() < parbeszed.height(), f"{nev}: a kattintási pont az ablakon kívül esik"
    _kattints_kozepere(parbeszed, qt_app, elem)


def _valaszt(parbeszed, qt_app, doboz_nev, index):
    """Valódi kattintás a legördülő fejlécén, majd a `index`-edik tételen."""
    doboz = _elem(parbeszed, doboz_nev)
    _kattints_kozepere(parbeszed, qt_app, doboz)
    assert _varakozzon(
        qt_app, hibaturo_feltetel(lambda: doboz.findChild(QObject, "picasaComboList") is not None)
    ), f"{doboz_nev}: a legördülő nem nyílt meg"
    lista = doboz.findChild(QObject, "picasaComboList")
    _kattints_kozepere(parbeszed, qt_app, _legordulo_tetele(qt_app, lista, index))


def _meret_index(parbeszed, azonosito: str) -> int:
    return _lista(parbeszed.property("printSizeIds")).index(azonosito)


def _nyisd_ket_kepperl(window, qt_app):
    _kijelol(window, qt_app, [0, 1])
    parbeszed = _menubol_nyit(window, qt_app)
    assert var_feltetelre(qt_app, hibaturo_feltetel(parbeszed.isVisible)), (
        "a párbeszéd nem nyílt meg"
    )
    # nyitáskor a méretezés később fut le: amíg tart, a tartalom a 420 px-es
    # kezdőmagasságon van, és a lejjebbi vezérlők az ablakon kívül esnek
    assert var_feltetelre(
        qt_app, lambda: not parbeszed.property("meretezesFuggoben")
    ), "a párbeszéd méretezése nem fejeződött be"
    return parbeszed


class TestNyomtatoValtasKattintassal:
    def test_a_beallitasok_es_a_kepek_megmaradnak_a_nyomtatovaltas_utan(
        self, qml_app, qt_app
    ):
        window, _controller, _engine = qml_app
        parbeszed = _nyisd_ket_kepperl(window, qt_app)
        # ha a párbeszéd bezárul és újranyílik, ez a jel minden átmenetet rögzít
        lathatosag = []
        parbeszed.visibleChanged.connect(lathatosag.append)

        _valaszt(parbeszed, qt_app, "printPrinterBox", INDEX_A)
        assert parbeszed.property("printerName") == PRINTER_A

        _kattint(parbeszed, qt_app, "printCopiesPlusButton")
        assert parbeszed.property("copies") == 2

        _valaszt(parbeszed, qt_app, "printSizeBox", _meret_index(parbeszed, "M4X6"))
        assert parbeszed.property("printSize") == "M4X6"

        _valaszt(parbeszed, qt_app, "printOrientationBox", INDEX_LANDSCAPE)
        assert parbeszed.property("orientation") == "landscape"

        _kattint(parbeszed, qt_app, "printFillRadio")
        assert parbeszed.property("fitMode") == "fill"

        # a másik nyomtatóra váltás: a beállításoknak itt kell megmaradniuk
        _valaszt(parbeszed, qt_app, "printPrinterBox", INDEX_B)

        assert shiboken6.isValid(parbeszed), (
            "a párbeszéd C++ objektuma megsemmisült a nyomtatóváltáskor"
        )
        assert lathatosag == [], (
            f"a láthatóság változott a nyomtatóváltáskor: {lathatosag}"
        )
        assert parbeszed.isVisible(), "a párbeszéd bezáródott a nyomtatóváltáskor"
        assert len(window.findChildren(QObject, "printDialog")) == 1, (
            "több példány él a nyomtatás-párbeszédből"
        )
        assert _elem(window, "printDialog") is parbeszed

        assert parbeszed.property("printerName") == PRINTER_B
        assert _elem(parbeszed, "printPrinterBox").property("currentIndex") == INDEX_B
        assert parbeszed.property("copies") == 2
        assert _elem(parbeszed, "printCopiesText").property("text") == "2"
        assert parbeszed.property("printSize") == "M4X6"
        assert _elem(parbeszed, "printSizeBox").property("currentIndex") == _meret_index(
            parbeszed, "M4X6"
        )
        assert parbeszed.property("orientation") == "landscape"
        assert _elem(parbeszed, "printOrientationBox").property("currentIndex") == INDEX_LANDSCAPE
        assert parbeszed.property("fitMode") == "fill"
        assert _elem(parbeszed, "printFillRadio").property("checked") is True
        assert _sorok(parbeszed) == [0, 1], "a kijelölt képek megváltoztak"
