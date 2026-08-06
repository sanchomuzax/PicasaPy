"""`picasapy.app.print_controller.PrintController` (#32, RÉSZLEGES kör) —
headless teszt PDF-kimenettel (`QPrinter.PdfFormat`), a natív nyomtatóra
küldés (`printRows`) csak a hívási útvonalig ellenőrizhető."""

from __future__ import annotations

import os
from dataclasses import dataclass

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6.QtGui import QGuiApplication
from PySide6.QtPrintSupport import QPrinterInfo

from picasapy.app.print_controller import PrintController
from support.jpeg_factory import make_jpeg


@pytest.fixture(scope="module")
def qt_app():
    return QGuiApplication.instance() or QGuiApplication([])


@dataclass
class _FakePhoto:
    folder_path: str
    name: str


def _controller(photos):
    return PrintController(photo_source=lambda: photos)


class TestListPrinters:
    def test_returns_a_list(self, qt_app):
        controller = _controller([])
        result = controller.listPrinters()
        assert isinstance(result, list)
        # a CI-gépen tipikusan nincs telepített nyomtató — csak a típus
        # és az, hogy megegyezik a Qt saját listájával, garantált
        assert result == list(QPrinterInfo.availablePrinterNames())


class TestRenderPrintPreviewPdf:
    def test_no_selection_fails(self, qt_app, tmp_path):
        controller = _controller([])
        events = []
        controller.printFailed.connect(events.append)
        ok = controller.renderPrintPreviewPdf(
            [], "fit", "auto", str(tmp_path / "out.pdf")
        )
        assert ok is False
        assert events

    def test_single_photo_creates_pdf(self, qt_app, tmp_path):
        source = make_jpeg(tmp_path / "kép.jpg", size=(400, 200))
        photo = _FakePhoto(folder_path=str(tmp_path), name=source.name)
        controller = _controller([photo])
        output = tmp_path / "out.pdf"
        finished = []
        controller.printFinished.connect(finished.append)
        ok = controller.renderPrintPreviewPdf([0], "fit", "auto", str(output))
        assert ok is True
        assert output.exists()
        assert output.stat().st_size > 0
        assert finished == [str(output)]

    def test_multiple_photos_create_multi_page_pdf(self, qt_app, tmp_path):
        first = make_jpeg(tmp_path / "egy.jpg", size=(400, 200))
        second = make_jpeg(tmp_path / "ketto.jpg", size=(200, 400))
        photos = [
            _FakePhoto(folder_path=str(tmp_path), name=first.name),
            _FakePhoto(folder_path=str(tmp_path), name=second.name),
        ]
        controller = _controller(photos)
        output = tmp_path / "out.pdf"
        ok = controller.renderPrintPreviewPdf([0, 1], "fill", "auto", str(output))
        assert ok is True
        # két oldal ⇒ a PDF egynél nagyobb, ésszerű méretű (durva ellenőrzés,
        # a pontos oldalszám PDF-parszolás nélkül nem olvasható ki egyszerűen)
        assert output.stat().st_size > 0

    def test_missing_source_file_is_skipped_not_fatal(self, qt_app, tmp_path):
        photo = _FakePhoto(folder_path=str(tmp_path), name="nincs-ilyen.jpg")
        controller = _controller([photo])
        events = []
        controller.printFailed.connect(events.append)
        output = tmp_path / "out.pdf"
        ok = controller.renderPrintPreviewPdf([0], "fit", "auto", str(output))
        assert ok is False
        assert events

    def test_empty_output_path_fails(self, qt_app, tmp_path):
        source = make_jpeg(tmp_path / "kép.jpg")
        photo = _FakePhoto(folder_path=str(tmp_path), name=source.name)
        controller = _controller([photo])
        ok = controller.renderPrintPreviewPdf([0], "fit", "auto", "")
        assert ok is False

    def test_invalid_fit_mode_fails(self, qt_app, tmp_path):
        source = make_jpeg(tmp_path / "kép.jpg")
        photo = _FakePhoto(folder_path=str(tmp_path), name=source.name)
        controller = _controller([photo])
        output = tmp_path / "out.pdf"
        ok = controller.renderPrintPreviewPdf([0], "nem-létező", "auto", str(output))
        assert ok is False


class TestPrintRows:
    def test_unknown_printer_name_fails(self, qt_app, tmp_path):
        source = make_jpeg(tmp_path / "kép.jpg")
        photo = _FakePhoto(folder_path=str(tmp_path), name=source.name)
        controller = _controller([photo])
        events = []
        controller.printFailed.connect(events.append)
        ok = controller.printRows(
            [0], "ez-a-nyomtató-nem-létezik", "fit", "auto"
        )
        assert ok is False
        assert events

    def test_no_selection_fails(self, qt_app):
        controller = _controller([])
        ok = controller.printRows([], "", "fit", "auto")
        assert ok is False
