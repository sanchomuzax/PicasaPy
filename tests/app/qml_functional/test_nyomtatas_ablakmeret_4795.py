"""#4795 — a Nyomtatás ablak kezdőmagassága a tartalomhoz igazodik, a
Nyomtatás/Close gombsor és a nyomtatóválasztó nem lóg ki alóla.

Renderelt (mapToScene) és kattintásos (QTest.mouseClick) próbák; kis
ablakmagasságnál a gombsor rögzített marad, a tartalom görgethető.
"""

from __future__ import annotations

import time

import pytest
from PySide6.QtCore import QMetaObject, QObject, QPointF, Qt
from PySide6.QtTest import QTest

from tests.app.qml_functional.test_nyomtatas_bekotes_1472 import (
    _kijelol,
    _menubol_nyit,
)


@pytest.fixture(autouse=True)
def _huvelykes_terulet(monkeypatch):
    from picasapy.printing import dpi

    monkeypatch.setattr(dpi, "_metrikus_teruleti_meres", lambda: False)


def _elem(root, nev):
    obj = root.findChild(QObject, nev)
    assert obj is not None, f"{nev} nem található"
    return obj


def _alja(elem) -> float:
    return elem.mapToScene(QPointF(0, elem.height())).y()


def _tetje(elem) -> float:
    return elem.mapToScene(QPointF(0, 0)).y()


def _var(qt_app, feltetel, masodperc=3.0) -> bool:
    hatarido = time.monotonic() + masodperc
    while time.monotonic() < hatarido and not feltetel():
        qt_app.processEvents()
        time.sleep(0.01)
    return bool(feltetel())


def _nyit(qml_app, qt_app):
    window, _c, _e = qml_app
    _kijelol(window, qt_app, [0])
    parbeszed = _menubol_nyit(window, qt_app)
    # az első elrendezés után méretezi magát az ablak (nyitás-időzítő)
    _var(qt_app, lambda: False, 0.6)
    return window, parbeszed


def _hatar(parbeszed, elem) -> float:
    """Az elem LÁTHATÓ területének alja: a görgetett tartalomnál a Flickable
    alja (nem az ablaké), a rögzített részen az ablak alja."""
    szulo = elem.parent()
    while szulo is not None:
        if szulo.objectName() == "printContentFlick":
            return szulo.mapToScene(QPointF(0, szulo.height())).y()
        szulo = szulo.parent()
    return float(parbeszed.height())


def _bent_van(parbeszed, nevek):
    for nev in nevek:
        elem = _elem(parbeszed, nev)
        hatar = _hatar(parbeszed, elem)
        assert _alja(elem) <= hatar, (
            f"{nev} alja ({_alja(elem)}) kilóg a látható területből ({hatar} px)"
        )
        assert _tetje(elem) >= 0


def _nem_ures_a_kepkocka(parbeszed, nev) -> bool:
    """A renderelt kép az elem helyén nem csupa háttérszínű képpont."""
    kep = parbeszed.grabWindow()
    elem = _elem(parbeszed, nev)
    x = int(elem.mapToScene(QPointF(0, 0)).x())
    y = int(elem.mapToScene(QPointF(0, 0)).y())
    sz, m = int(elem.width()), int(elem.height())
    hatar = int(_hatar(parbeszed, elem))
    assert y + m <= hatar, f"{nev} kilóg, a képkockán nem látszik"
    kivagas = kep.copy(x, y, sz, m)
    szinek = {kivagas.pixel(i, j) for i in range(0, sz, 3) for j in range(0, m, 3)}
    return len(szinek) > 2


GOMBOK = ["printStartButton", "printCloseButton"]


class TestKezdomeret:
    def test_gombok_es_nyomtatovalaszto_az_ablakon_belul(self, qml_app, qt_app):
        _w, parbeszed = _nyit(qml_app, qt_app)
        _bent_van(parbeszed, GOMBOK + ["printPrinterBox"])

    def test_nyomtato_nelkul_is_bent_van(self, qml_app, qt_app, monkeypatch):
        from picasapy.app.print_controller import PrintController

        monkeypatch.setattr(PrintController, "listPrinters", lambda self: [])
        _w, parbeszed = _nyit(qml_app, qt_app)
        assert list(parbeszed.property("printers") or []) == []
        _bent_van(parbeszed, GOMBOK + ["printPrinterBox"])

    def test_nyomtatovalaszto_a_kepkockan_is_latszik(self, qml_app, qt_app):
        _w, parbeszed = _nyit(qml_app, qt_app)
        _bent_van(parbeszed, ["printPrinterBox"])
        assert _nem_ures_a_kepkocka(parbeszed, "printPrinterBox"), (
            "a nyomtatóválasztó helye a renderelt képen üres"
        )

    def test_indexkep_modban_nyitva_is_bent_van(self, qml_app, qt_app):
        window, _c, _e = qml_app
        _kijelol(window, qt_app, [0, 1])
        tetel = _elem(window, "menuFolderPrintContactSheet")
        QMetaObject.invokeMethod(
            tetel, "triggered", Qt.ConnectionType.DirectConnection
        )
        qt_app.processEvents()
        parbeszed = _elem(window, "printDialog")
        assert parbeszed.property("contactSheet") is True
        assert _var(qt_app, lambda: parbeszed.isVisible())
        _var(qt_app, lambda: False, 0.6)
        _bent_van(parbeszed, GOMBOK + ["printPrinterBox"])


class TestHibaSzoveg:
    def test_hiba_a_gombsor_folott_az_ablakon_belul_latszik(self, qml_app, qt_app):
        _w, parbeszed = _nyit(qml_app, qt_app)
        parbeszed.setProperty(
            "lastError", "Hiba: valami nagyon hosszú hibaüzenet, ami több sorba "
            "is tördelődhet, hogy a próba ne csak egy sort mérjen."
        )
        _var(qt_app, lambda: False, 0.3)
        hiba = _elem(parbeszed, "printErrorText")
        assert hiba.property("visible") is True
        gombsor = _elem(parbeszed, "printStartButton")
        assert _alja(hiba) <= _tetje(gombsor), "a hiba a gombsor alá/mögé lóg"
        assert _alja(hiba) <= parbeszed.height()
        assert _tetje(hiba) >= 0


class TestKattintas:
    def test_nyomtatas_gomb_kozepere_kattintva_elindul_a_nyomtatas(
        self, qml_app, qt_app, tmp_path
    ):
        window, parbeszed = _nyit(qml_app, qt_app)
        cel = tmp_path / "kattintas.pdf"
        parbeszed.setProperty("pdfTarget", cel.as_uri())
        qt_app.processEvents()

        gomb = _elem(parbeszed, "printStartButton")
        assert gomb.property("enabled") is True
        pont = gomb.mapToScene(
            QPointF(gomb.width() / 2, gomb.height() / 2)
        ).toPoint()
        assert 0 <= pont.y() < parbeszed.height()
        QTest.mouseClick(
            parbeszed,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
            pont,
        )
        assert _var(qt_app, cel.exists), "a kattintás nem indította el a nyomtatást"
        assert cel.read_bytes().startswith(b"%PDF")


class TestKisAblak:
    @pytest.mark.parametrize("magassag", [500, 420])
    def test_kis_ablakban_a_gombsor_latszik(self, qml_app, qt_app, magassag):
        _w, parbeszed = _nyit(qml_app, qt_app)
        parbeszed.resize(parbeszed.width(), magassag)
        assert _var(qt_app, lambda: parbeszed.height() == magassag)
        qt_app.processEvents()
        _bent_van(parbeszed, GOMBOK)
        # a tartalom görgethető: van Flickable a tartalom körül
        assert _elem(parbeszed, "printContentFlick") is not None

    def test_kezdomagassag_nem_nagyobb_a_kepernyonel(self, qml_app, qt_app):
        _w, parbeszed = _nyit(qml_app, qt_app)
        kepernyo = parbeszed.screen()
        assert kepernyo is not None, "az ablaknak nincs képernyője"
        assert parbeszed.height() <= kepernyo.availableGeometry().height()
