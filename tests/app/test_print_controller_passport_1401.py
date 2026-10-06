"""#1401: az Útlevélkép a MEGLÉVŐ nyomtatási úton — `PrintController.
setPassportSource` / `clearPassportSource`.

A kivágott, ideiglenes fájl a kijelölés (`rows`) HELYÉRE lép, a
nyomatméret `ePassport` (2,0 × 2,0 hüvelyk). A lapszámot, az előnézetet
és a nyomtatást UGYANAZ a `_run`/`grid_layout` út adja, mint bármely más
méretnél — ezért az előnézeti lapot NÉZZÜK: a kirajzolt kép tényleg
2 × 2 hüvelyk, és egy van belőle a lapon."""

from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import re

import numpy as np
import pytest
from PySide6.QtCore import QLocale, QSettings, QUrl
from PySide6.QtGui import QColor, QGuiApplication, QImage

from picasapy.index import PhotoRecord

try:
    from picasapy.app import print_controller as pc_modul
    from picasapy.app.print_controller import PrintController

    _QTPRINTSUPPORT_VAN = True
except ImportError:  # pragma: no cover — csak a hiányos telepítésen fut
    pc_modul = None
    PrintController = None
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


_PIROS = (200, 30, 30)


def _kep(path, szin=_PIROS, meret=(600, 600)) -> str:
    kep = QImage(meret[0], meret[1], QImage.Format.Format_RGB32)
    kep.fill(QColor(*szin))
    assert kep.save(str(path))
    return QUrl.fromLocalFile(str(path)).toString()


def _rekord(path) -> PhotoRecord:
    return PhotoRecord(
        id=1, folder_path=str(path.parent), name=path.name, kind="image",
        size=0, mtime_ns=0, star=False, caption=None, keywords=None,
        rotate_steps=0, filters=None, taken_at=None, orientation=0,
        width=320, height=160,
    )


def _controller(tmp_path, fotok=()):
    settings = QSettings(str(tmp_path / "s.ini"), QSettings.Format.IniFormat)
    return PrintController(photo_source=lambda: list(fotok), settings=settings)


def _nem_feher_doboz(kep: QImage) -> tuple[int, int, int, int] | None:
    szurke = kep.convertToFormat(QImage.Format.Format_Grayscale8)
    sor = szurke.bytesPerLine()
    tomb = np.frombuffer(szurke.constBits(), dtype=np.uint8).reshape(
        szurke.height(), sor
    )[:, : szurke.width()]
    ys, xs = np.nonzero(tomb < 200)
    if xs.size == 0:
        return None
    return (
        int(xs.min()), int(ys.min()),
        int(xs.max() - xs.min() + 1), int(ys.max() - ys.min() + 1),
    )


class TestAForrasCsere:
    def test_a_kivagott_fajl_lep_a_kijeloles_helyere(self, qt_app, tmp_path):
        mappa_kep = tmp_path / "mappa.png"
        _kep(mappa_kep, (10, 200, 10), (320, 160))
        ctl = _controller(tmp_path, [_rekord(mappa_kep)])
        url = _kep(tmp_path / "utlevel.png")
        assert ctl.setPassportSource(url) is True
        rekordok = ctl._resolve_records([0])
        assert [r.name for r in rekordok] == ["utlevel.png"]
        assert (rekordok[0].width, rekordok[0].height) == (600, 600)

    def test_a_torles_utan_ujra_a_kijeloles_szamit(self, qt_app, tmp_path):
        mappa_kep = tmp_path / "mappa.png"
        _kep(mappa_kep, (10, 200, 10), (320, 160))
        ctl = _controller(tmp_path, [_rekord(mappa_kep)])
        ctl.setPassportSource(_kep(tmp_path / "utlevel.png"))
        ctl.clearPassportSource()
        assert [r.name for r in ctl._resolve_records([0])] == ["mappa.png"]

    def test_ures_url_elutasitva(self, qt_app, tmp_path):
        ctl = _controller(tmp_path)
        assert ctl.setPassportSource("") is False


class TestAzUtlevelMeret:
    def test_a_lapszam_egy_egy_peldanynal(self, qt_app, tmp_path):
        ctl = _controller(tmp_path)
        ctl.setPassportSource(_kep(tmp_path / "utlevel.png"))
        assert ctl.printPageCount([0], 1) == 1

    def test_az_elonezeten_EGY_2x2_huvelykes_kep_all(self, qt_app, tmp_path):
        ctl = _controller(tmp_path)
        ctl.setPassportSource(_kep(tmp_path / "utlevel.png"))
        cel = tmp_path / "lap.png"
        assert ctl.renderPreviewPage([0], "fill", "auto", 1, 0, str(cel))
        lap = QImage(str(cel))
        doboz = _nem_feher_doboz(lap)
        assert doboz is not None, "az előnézeti lapon nincs kép"
        _x, _y, szeles, magas = doboz
        vart = 2.0 * pc_modul._ELONEZET_DPI
        assert szeles == pytest.approx(vart, abs=2)
        assert magas == pytest.approx(vart, abs=2)

    def test_a_meretvalasztas_felulirja_az_utlevelet(
        self, qt_app, tmp_path, monkeypatch
    ):
        import picasapy.printing.dpi as dpi

        class ImperialQLocale:
            MeasurementSystem = QLocale.MeasurementSystem

            def measurementSystem(self):
                return QLocale.MeasurementSystem.ImperialUSSystem

        monkeypatch.setattr(dpi, "QLocale", ImperialQLocale, raising=False)
        ctl = _controller(tmp_path)
        ctl.setPassportSource(_kep(tmp_path / "utlevel.png"))
        ctl.setPrintSize("M4X6")
        cel = tmp_path / "lap.png"
        assert ctl.renderPreviewPage([0], "fill", "auto", 1, 0, str(cel))
        _x, _y, szeles, magas = _nem_feher_doboz(QImage(str(cel)))
        # 4 × 6 hüvelykes cella: a hosszabbik oldal már nem 2 hüvelyk
        assert max(szeles, magas) > 3.5 * pc_modul._ELONEZET_DPI

    def test_a_pdf_egy_oldalas(self, qt_app, tmp_path):
        ctl = _controller(tmp_path)
        ctl.setPassportSource(_kep(tmp_path / "utlevel.png"))
        cel = tmp_path / "ki.pdf"
        assert ctl.renderPrintPreviewPdf([0], "fill", "auto", str(cel), 1)
        adat = cel.read_bytes()
        assert len(re.findall(rb"/Type\s*/Page[^s]", adat)) == 1

    def test_a_minoseg_a_passport_mereten_szamol(self, qt_app, tmp_path):
        ctl = _controller(tmp_path)
        ctl.setPassportSource(_kep(tmp_path / "utlevel.png"))
        minoseg = ctl.printQuality([0], "PASSPORT")
        # 600 képpont / 2 hüvelyk = 300 ppi
        assert minoseg["smallest"] == 300
        assert minoseg["total"] == 1
