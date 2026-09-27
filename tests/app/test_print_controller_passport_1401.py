"""#1401: az Útlevélkép nyomtatása — `PrintController.printPassportPhoto` /
`renderPassportPreviewPdf`, egy MÁR kivágott, ideiglenes fájllal, rögzített
`ePassport` (2,0 × 2,0 hüvelyk) mérettel, a `rows` kijelölést megkerülve
(ld. `_passport_record`, `_run(..., paths_override=...)`)."""

from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6.QtGui import QGuiApplication

from support.jpeg_factory import make_jpeg

try:
    from PySide6.QtPrintSupport import QPrinterInfo

    from picasapy.app.print_controller import PrintController
    from picasapy.printing.dpi import NyomatMeret

    _QTPRINTSUPPORT_VAN = True
except ImportError:  # pragma: no cover — csak a hiányos telepítésen fut
    QPrinterInfo = None
    PrintController = None
    NyomatMeret = None
    _QTPRINTSUPPORT_VAN = False

pytestmark = pytest.mark.skipif(
    not _QTPRINTSUPPORT_VAN,
    reason=(
        "a PySide6.QtPrintSupport modul hiányzik ezen a gépen, ezért a "
        "nyomtatás-vezérlő tesztjei kimaradnak."
    ),
)


@pytest.fixture(scope="module")
def qt_app():
    return QGuiApplication.instance() or QGuiApplication([])


def _controller():
    # #1401: a passport-metódusok NEM a `photo_source`-on át kapják a
    # bemenetüket (`paths_override`), tehát üres forrás is elég.
    return PrintController(photo_source=lambda: [])


class TestRenderPassportPreviewPdf:
    def test_negyzet_kep_pdf_be_kerul(self, qt_app, tmp_path):
        # a kivágott passport-fájl előre elkészítve, MINDIG négyzet
        source = make_jpeg(tmp_path / "utlevel.jpg", size=(300, 300))
        controller = _controller()
        output = tmp_path / "out.pdf"
        finished = []
        controller.printFinished.connect(finished.append)
        ok = controller.renderPassportPreviewPdf(str(source), str(output), 1)
        assert ok is True
        assert output.exists()
        assert output.stat().st_size > 0
        assert finished == [str(output)]

    def test_ket_peldany_is_egy_hivasban_megy(self, qt_app, tmp_path):
        """#1401 „Kész, ha": a példányszám emelésével a képek rácsban
        kerülnek a lapra — ez itt csak azt ellenőrzi, hogy a hívás a
        `copies` paraméterrel is sikeres (a rács geometriáját a
        `grid_layout` saját tesztjei fedik, #3647)."""
        source = make_jpeg(tmp_path / "utlevel.jpg", size=(300, 300))
        controller = _controller()
        output = tmp_path / "out.pdf"
        ok = controller.renderPassportPreviewPdf(str(source), str(output), 2)
        assert ok is True
        assert output.stat().st_size > 0

    def test_hianyzo_forras_hibat_ad(self, qt_app, tmp_path):
        controller = _controller()
        events = []
        controller.printFailed.connect(events.append)
        output = tmp_path / "out.pdf"
        ok = controller.renderPassportPreviewPdf(
            str(tmp_path / "nincs-ilyen.png"), str(output), 1
        )
        assert ok is False
        assert events

    def test_ures_kimeneti_utvonal_hibat_ad(self, qt_app, tmp_path):
        source = make_jpeg(tmp_path / "utlevel.jpg", size=(300, 300))
        controller = _controller()
        ok = controller.renderPassportPreviewPdf(str(source), "", 1)
        assert ok is False

    def test_ures_forrasutvonal_hibat_ad(self, qt_app, tmp_path):
        controller = _controller()
        output = tmp_path / "out.pdf"
        ok = controller.renderPassportPreviewPdf("", str(output), 1)
        assert ok is False


class TestPassportRecord:
    def test_a_szintetikus_rekord_a_kep_tenyleges_meretet_adja(self, tmp_path):
        source = make_jpeg(tmp_path / "utlevel.jpg", size=(321, 321))
        rekord = PrintController._passport_record(source)
        assert rekord.width == 321
        assert rekord.height == 321
        assert rekord.name == source.name
        assert rekord.folder_path == str(source.parent)


class TestPrintPassportPhoto:
    def test_ismeretlen_nyomtato_hibat_ad(self, qt_app, tmp_path):
        source = make_jpeg(tmp_path / "utlevel.jpg", size=(300, 300))
        controller = _controller()
        events = []
        controller.printFailed.connect(events.append)
        ok = controller.printPassportPhoto(str(source), "nincs-ilyen-nyomtato", 1)
        assert ok is False
        assert events

    def test_ervenytelen_utvonal_hibat_ad(self, qt_app):
        controller = _controller()
        ok = controller.printPassportPhoto("", "", 1)
        assert ok is False
