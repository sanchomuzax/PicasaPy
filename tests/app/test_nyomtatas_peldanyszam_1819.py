"""Képenkénti példányszám és lapozható előnézet — #1819.

A #1782 két vezérlője, ami a DPI-őr körébe már nem fért bele:

* **`addprintsbutton` / `subprintsbutton`** — „Add another copy of each
  Photo to be printed". ⚠️ KÉPENKÉNTI, nem összes-példányszám: a +/− minden
  képhez ad egy további másolatot. Ez NEM a nyomtató saját
  példányszám-mezője, és a kettőt könnyű összekeverni — a jegy külön
  figyelmeztet rá, ezért a tesztek is a képenkéntiségre állítanak.
* **`prevbutton` / `nextbutton`**, a lapszám `%d / %d` alakban. A
  párbeszédnek eddig EGYÁLTALÁN nem volt előnézete.

A PDF-ből az oldalszám parszolás nélkül nem olvasható ki (ezt a meglévő
`test_print_controller` is kimondja), ezért a lapszámot ott állítjuk, ahol
mérhető: a `printPageCount`-on és a `_sokszorozva` magon — és a jegy
„két kép + két példány ⇒ négy lap" pontját mindkettő fedi.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import picasapy.app
import pytest
from PySide6.QtCore import QUrl
from PySide6.QtGui import QGuiApplication, QImage

from support.jpeg_factory import make_jpeg

try:
    from picasapy.app.print_controller import PrintController

    _VAN = True
except ImportError:  # pragma: no cover
    PrintController = None
    _VAN = False

pytestmark = pytest.mark.skipif(
    not _VAN, reason="a PySide6.QtPrintSupport modul hiányzik ezen a gépen"
)

_DIALOG = (
    Path(picasapy.app.__file__).parent
    / "qml" / "PicasaPy" / "PrintDialog.qml"
).read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def qt_app():
    return QGuiApplication.instance() or QGuiApplication([])


@dataclass
class _FakePhoto:
    folder_path: str
    name: str


@pytest.fixture
def ket_kep(qt_app, tmp_path):
    egy = make_jpeg(tmp_path / "egy.jpg", size=(400, 200))
    ketto = make_jpeg(tmp_path / "ketto.jpg", size=(200, 400))
    photos = [
        _FakePhoto(folder_path=str(tmp_path), name=egy.name),
        _FakePhoto(folder_path=str(tmp_path), name=ketto.name),
    ]
    return PrintController(photo_source=lambda: photos)


class TestALapszam:
    def test_ket_kep_ket_peldany_NEGY_lap(self, ket_kep):
        """A jegy „Kész, ha" pontja, szó szerint."""
        assert ket_kep.printPageCount([0, 1], 2) == 4

    def test_egy_peldany_valtozatlan(self, ket_kep):
        assert ket_kep.printPageCount([0, 1], 1) == 2

    def test_a_nulla_peldany_EGYNEK_szamit(self, ket_kep):
        """A nulla nem „ne nyomtass", hanem hibás bemenet — a +/− úgyis
        egynél áll meg."""
        assert ket_kep.printPageCount([0, 1], 0) == 2

    def test_a_nem_dekodolhato_kep_LAPOT_SEM_kap(self, qt_app, tmp_path):
        """Videó/sérült fájl: a lapszám sem tartalmazhatja."""
        jo = make_jpeg(tmp_path / "jo.jpg", size=(100, 100))
        (tmp_path / "film.mp4").write_bytes(b"\x00" * 32)
        photos = [
            _FakePhoto(folder_path=str(tmp_path), name=jo.name),
            _FakePhoto(folder_path=str(tmp_path), name="film.mp4"),
        ]
        ctl = PrintController(photo_source=lambda: photos)
        assert ctl.printPageCount([0, 1], 3) == 3


class TestANyomtatasVALOBAN:
    """⚠️ Ez a szakasz azért van itt, mert a `printPageCount` HAZUDHAT.

    Az első változatban a lapszám-teszt zöld maradt akkor is, amikor a
    példányszámot kivettem a `_run`-ból: a számláló külön úton számolt,
    mint amit a nyomtatás rajzol. A jegy „a nyomtatás tényleg annyi
    példányt ad" pontját ezért a RAJZOLÁSNÁL mérjük — azt figyeljük, hány
    lapot kap a festő."""

    def test_ket_kep_ket_peldany_NEGY_lapot_rajzol(
        self, ket_kep, tmp_path, monkeypatch
    ):
        kapott: list[int] = []
        eredeti = PrintController._paint_pages

        def figyelo(printer, images, mode):
            kapott.append(len(images))
            return eredeti(printer, images, mode)

        monkeypatch.setattr(
            PrintController, "_paint_pages", staticmethod(figyelo)
        )
        ok = ket_kep.renderPrintPreviewPdf(
            [0, 1], "fit", "auto", str(tmp_path / "ki.pdf"), 2
        )
        assert ok is True
        assert kapott == [4]

    def test_egy_peldany_KET_lapot_rajzol(
        self, ket_kep, tmp_path, monkeypatch
    ):
        kapott: list[int] = []
        eredeti = PrintController._paint_pages

        def figyelo(printer, images, mode):
            kapott.append(len(images))
            return eredeti(printer, images, mode)

        monkeypatch.setattr(
            PrintController, "_paint_pages", staticmethod(figyelo)
        )
        ket_kep.renderPrintPreviewPdf(
            [0, 1], "fit", "auto", str(tmp_path / "ki.pdf"), 1
        )
        assert kapott == [2]


class TestASokszorozas:
    def test_KEPENKENT_csoportosit(self, qt_app):
        """A sorrend: A, A, B, B — nem A, B, A, B.

        A felirat képenként fogalmaz („each Photo"); a másik olvasat a
        nyomtató példányszám-mezőjének viselkedése lenne, amitől ez a
        vezérlő épp különbözik. (A sorrend maga NINCS kimérve — a döntés a
        forrásban ki van mondva.)"""
        a = QImage(4, 4, QImage.Format.Format_RGB32)
        b = QImage(8, 8, QImage.Format.Format_RGB32)
        eredmeny = PrintController._sokszorozva([a, b], 2)
        assert [kep.width() for kep in eredmeny] == [4, 4, 8, 8]

    def test_egy_peldanynal_ugyanaz_a_lista(self, qt_app):
        a = QImage(4, 4, QImage.Format.Format_RGB32)
        lista = [a]
        assert PrintController._sokszorozva(lista, 1) is lista


class TestAzElonezetiLap:
    def test_kirajzol_egy_lapot(self, ket_kep, tmp_path):
        cel = tmp_path / "elonezet.png"
        ok = ket_kep.renderPreviewPage([0, 1], "fit", "auto", 1, 0, str(cel))
        assert ok is True
        assert cel.exists() and cel.stat().st_size > 0

    def test_a_tartomanyon_KIVULI_lap_elutasitva(self, ket_kep, tmp_path):
        cel = tmp_path / "nincs.png"
        assert ket_kep.renderPreviewPage([0, 1], "fit", "auto", 1, 2, str(cel)) is False
        assert ket_kep.renderPreviewPage([0, 1], "fit", "auto", 1, -1, str(cel)) is False

    def test_a_peldanyszam_UJ_lapokat_ad(self, ket_kep, tmp_path):
        """Két képnél a 2. lap csak akkor létezik, ha két példány van."""
        cel = tmp_path / "p.png"
        assert ket_kep.renderPreviewPage([0, 1], "fit", "auto", 1, 2, str(cel)) is False
        assert ket_kep.renderPreviewPage([0, 1], "fit", "auto", 2, 2, str(cel)) is True

    def test_a_lap_ARANYA_a_valasztott_nyomatmereté(self, ket_kep, tmp_path):
        """Az előnézet a VÁLASZTOTT méretet mutatja, nem a nyomtatóét —
        akkor is, ha a gépen nincs nyomtató."""
        ket_kep.setPrintSize("M8X10")
        cel = tmp_path / "nagy.png"
        assert ket_kep.renderPreviewPage([0], "fit", "portrait", 1, 0, str(cel))
        kep = QImage(str(cel))
        assert kep.width() / kep.height() == pytest.approx(8.0 / 10.0, abs=0.01)

    def test_az_elonezeti_fajl_URL_letezo_mappara_mutat(self, ket_kep):
        url = ket_kep.previewImageUrl()
        #: #1019: URL, nem kézzel fűzött „file://" + útvonal.
        assert url.startswith("file://")
        ut = Path(QUrl(url).toLocalFile())
        assert ut.parent.is_dir()
        assert ut.name.endswith(".png")


class TestAFelulet:
    def test_van_plusz_es_minusz_gomb(self):
        assert 'objectName: "printCopiesPlusButton"' in _DIALOG
        assert 'objectName: "printCopiesMinusButton"' in _DIALOG

    def test_a_minusz_egy_ALATT_tiltott(self):
        kezd = _DIALOG.index('objectName: "printCopiesMinusButton"')
        assert "enabled: printWindow.copies > 1" in _DIALOG[kezd : kezd + 420]

    def test_a_peldanyszam_ELJUT_a_nyomtatasig(self):
        """A #1153 osztálya: a gomb állít egy számot, amit senki nem visz
        tovább."""
        assert "printWindow.orientation, printWindow.copies)" in _DIALOG
        kezd = _DIALOG.index("renderPrintPreviewPdf(")
        assert "printWindow.copies" in _DIALOG[kezd : kezd + 260]

    def test_a_lapszam_a_mert_alakot_koveti(self):
        kezd = _DIALOG.index('objectName: "printPreviewPageText"')
        blokk = _DIALOG[kezd : kezd + 320]
        assert "+ \" / \" +" in blokk.replace("\n", " ").replace("  ", " ") \
            or '" / "' in blokk

    def test_a_lapozas_nem_lep_ki_a_tartomanybol(self):
        elozo = _DIALOG.index('objectName: "printPreviewPrevButton"')
        assert "enabled: printWindow.previewPage > 0" in _DIALOG[elozo : elozo + 420]
        kovetkezo = _DIALOG.index('objectName: "printPreviewNextButton"')
        assert "previewPageCount - 1" in _DIALOG[kovetkezo : kovetkezo + 460]

    def test_az_elonezet_gyorstara_KI_van_kapcsolva(self):
        """Ugyanaz a fájlnév kap új tartalmat minden lapozáskor — a Qt
        URL szerint gyorstáraz (a #1186 hibaosztálya)."""
        kezd = _DIALOG.index('objectName: "printPreviewImage"')
        assert "cache: false" in _DIALOG[kezd : kezd + 620]
