"""#4795 — a Nyomtatás ablak kezdőmagassága a tartalomhoz igazodik, a
Nyomtatás/Close gombsor és a nyomtatóválasztó nem lóg ki alóla.

Renderelt (mapToScene) és kattintásos (QTest.mouseClick) próbák; kis
ablakmagasságnál a gombsor rögzített marad, a tartalom görgethető.
"""

from __future__ import annotations

import time

import pytest
from PySide6.QtCore import QObject, QPointF, Qt
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
    qt_app.processEvents()
    return window, parbeszed


def _bent_van(parbeszed, nevek):
    magassag = parbeszed.height()
    for nev in nevek:
        elem = _elem(parbeszed, nev)
        assert _alja(elem) <= magassag, (
            f"{nev} alja ({_alja(elem)}) kilóg az ablakból ({magassag} px)"
        )
        assert _tetje(elem) >= 0


GOMBOK = ["printStartButton", "printCloseButton"]


class TestKezdomeret:
    def test_gombok_es_nyomtatovalaszto_az_ablakon_belul(self, qml_app, qt_app):
        _w, parbeszed = _nyit(qml_app, qt_app)
        _bent_van(parbeszed, GOMBOK + ["printPrinterBox"])

    def test_nyomtato_nelkul_is_bent_van(self, qml_app, qt_app):
        _w, parbeszed = _nyit(qml_app, qt_app)
        parbeszed.setProperty("printers", [])
        qt_app.processEvents()
        _bent_van(parbeszed, GOMBOK + ["printPrinterBox"])


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
        kepernyo = parbeszed.screen() if hasattr(parbeszed, "screen") else None
        if kepernyo is not None:
            assert parbeszed.height() <= kepernyo.availableGeometry().height()
