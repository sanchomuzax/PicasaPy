"""#5684: a nyomtatási mód az eredeti PrinterQuality/PrinterUseTiles pár."""

from __future__ import annotations

import pytest
from PySide6.QtCore import QSettings
from PySide6.QtGui import QGuiApplication

from picasapy.app.print_controller import PrintController


@pytest.fixture(scope="module")
def qt_app():
    return QGuiApplication.instance() or QGuiApplication([])


@pytest.mark.parametrize(
    ("optimalizalt", "vart_par"),
    [(False, (2, 0)), (True, (1, 1))],
    ids=("normal-2-0", "optimalizalt-1-1"),
)
def test_nyomtatasi_mod_eredeti_parja_tartos_es_ujranyitas_utan_visszaolvashato(
    qt_app, tmp_path, optimalizalt, vart_par
):
    beallitas_fajl = tmp_path / "printer-mode.ini"
    elso_beallitasok = QSettings(
        str(beallitas_fajl), QSettings.Format.IniFormat
    )
    elso_vezerlo = PrintController(photo_source=lambda: (), settings=elso_beallitasok)

    elso_vezerlo.setPrinterOptimized(optimalizalt)
    elso_beallitasok.sync()

    uj_beallitasok = QSettings(str(beallitas_fajl), QSettings.Format.IniFormat)
    uj_vezerlo = PrintController(photo_source=lambda: (), settings=uj_beallitasok)

    assert (
        uj_beallitasok.value("printing/jobPrinterQuality", type=int),
        uj_beallitasok.value("printing/jobPrinterUseTiles", type=int),
    ) == vart_par
    assert uj_vezerlo.printerOptimized() is optimalizalt
