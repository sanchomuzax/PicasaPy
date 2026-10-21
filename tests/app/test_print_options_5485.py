"""#5485: a nyomtatási minőségek eredeti számai és régi értékei."""

from __future__ import annotations

import pytest
from PySide6.QtCore import QSettings
from PySide6.QtGui import QGuiApplication

from picasapy.app.print_controller import PrintController


@pytest.fixture(scope="module")
def qt_app():
    return QGuiApplication.instance() or QGuiApplication([])


def _vezerlo(settings: QSettings) -> PrintController:
    return PrintController(photo_source=lambda: (), settings=settings)


def test_print_resampler_quality_eredeti_szamokkal_es_regi_harmassal(
    qt_app, tmp_path
):
    settings = QSettings(str(tmp_path / "print.ini"), QSettings.Format.IniFormat)
    vezerlo = _vezerlo(settings)

    assert vezerlo.printResamplerQuality() == 5
    assert vezerlo._print_resampler_radius() == 3
    assert settings.value("printing/resamplerQuality") is None

    vezerlo.setPrintResamplerQuality(8)
    assert settings.value("printing/resamplerQuality") == 8
    assert vezerlo.printResamplerQuality() == 8
    assert vezerlo._print_resampler_radius() == 8

    vezerlo.setPrintResamplerQuality(5)
    assert settings.value("printing/resamplerQuality") == 5
    assert vezerlo.printResamplerQuality() == 5

    settings.setValue("printing/resamplerQuality", 3)
    regi_vezerlo = _vezerlo(settings)
    assert regi_vezerlo.printResamplerQuality() == 5
    assert regi_vezerlo._print_resampler_radius() == 3
    assert settings.value("printing/resamplerQuality") == 3


def test_printer_quality_eredeti_szamokkal_es_regi_szoveges_ertekekkel(
    qt_app, tmp_path
):
    settings = QSettings(str(tmp_path / "printer.ini"), QSettings.Format.IniFormat)
    vezerlo = _vezerlo(settings)

    assert vezerlo.printerQuality() == 2
    assert settings.value("printing/printerQuality") is None
    assert vezerlo._printer_output_scale() == 0.5

    vezerlo.setPrinterQuality(3)
    assert settings.value("printing/printerQuality") == 3
    assert vezerlo.printerQuality() == 3
    assert vezerlo._printer_output_scale() == 1.0

    vezerlo.setPrinterQuality(2)
    assert settings.value("printing/printerQuality") == 2
    assert vezerlo.printerQuality() == 2
    assert vezerlo._printer_output_scale() == 0.5

    settings.setValue("printing/printerQuality", "highQuality")
    assert _vezerlo(settings).printerQuality() == 3
    settings.setValue("printing/printerQuality", "compatible")
    assert _vezerlo(settings).printerQuality() == 2
