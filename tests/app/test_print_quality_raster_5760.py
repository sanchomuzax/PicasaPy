"""#5760: a per-feladat nyomtatási mód méretezi a rajzoló rasztert."""

from __future__ import annotations

import pytest
from PySide6.QtCore import QSettings, QRectF
from PySide6.QtGui import QGuiApplication, QImage

from picasapy.app.print_controller import PrintController


@pytest.fixture(scope="module")
def qt_app():
    return QGuiApplication.instance() or QGuiApplication([])


def _rendered_size(
    quality: int, use_tiles: int, *, tmp_path, qt_app
) -> tuple[int, int]:
    settings = QSettings(
        str(tmp_path / f"print-{quality}-{use_tiles}.ini"),
        QSettings.Format.IniFormat,
    )
    settings.setValue("printing/jobPrinterQuality", quality)
    settings.setValue("printing/jobPrinterUseTiles", use_tiles)
    controller = PrintController(photo_source=lambda: (), settings=settings)

    source = QImage(160, 80, QImage.Format.Format_RGB32)
    source.fill(0xFF123456)
    target = QRectF(0, 0, 80, 40)
    rendered = controller._resampled_for_target(
        source,
        target,
        radius=3,
        printer_output_scale=controller._printer_job_output_scale(),
    )
    return rendered.width(), rendered.height()


def test_normal_and_optimized_modes_render_different_raster_sizes(
    qt_app, tmp_path
):
    normal = _rendered_size(2, 0, tmp_path=tmp_path, qt_app=qt_app)
    optimized = _rendered_size(1, 1, tmp_path=tmp_path, qt_app=qt_app)

    assert normal == (40, 20)
    assert optimized == (80, 40)


@pytest.mark.parametrize(
    ("quality", "use_tiles", "expected"),
    [
        (2, 0, (40, 20)),
        (2, 1, (40, 20)),
        (1, 0, (80, 40)),
        (1, 1, (80, 40)),
    ],
)
def test_use_tiles_does_not_change_the_rendered_raster(
    qt_app, tmp_path, quality, use_tiles, expected
):
    assert _rendered_size(
        quality, use_tiles, tmp_path=tmp_path, qt_app=qt_app
    ) == expected


def test_normal_mode_keeps_the_options_full_resolution_choice(qt_app, tmp_path):
    """A Beállítások 3-as (teljes felbontású) minősége Normál módban sem vész el."""
    settings = QSettings(str(tmp_path / "print-q3.ini"), QSettings.Format.IniFormat)
    settings.setValue("printing/printerQuality", 3)
    settings.setValue("printing/jobPrinterQuality", 2)
    controller = PrintController(photo_source=lambda: (), settings=settings)
    assert controller._printer_job_output_scale() == 1.0
    settings.setValue("printing/printerQuality", 2)
    assert controller._printer_job_output_scale() == 0.5
    controller.setPrinterOptimized(True)
    assert controller._printer_job_output_scale() == 1.0
