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
from PySide6.QtCore import QSettings, QUrl
from PySide6.QtGui import QGuiApplication, QImage

from support.jpeg_factory import make_jpeg
from tests.support.qml_blokk import blokk_horgonyra, hivas_argumentumai

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


def _egyetlen_cellas_lapot_kenyszerit(monkeypatch, oldal: float = 700.0):
    """A lapgeometriát egy nagy, NÉGYZETES lapra rögzíti, hogy a #3647-es
    rács MINDIG pontosan egy cellát fogadjon laponként.

    Ez a fájl a PÉLDÁNYSZÁM-számlálást és a lapozást méri, nem a
    rácsba-rendezést — azt a `printing/test_nyomtatasi_racs_3647.py` fedi,
    saját, kontrollált lapmérettel. Enélkül ezek a próbák a valódi (A4
    alapértelmezésre eső) rácsszámításon múlnának, ami a nyomatmérettől és
    a lapmérettől függ, nem attól, amit itt tesztelünk."""
    import picasapy.app.print_controller as pc_modul

    def hamis_elonezeti(self, printer_name, *, landscape):  # noqa: ARG001
        return pc_modul.PageGeometry(width=oldal, height=oldal, margin=0.0)

    def hamis_eszkoz(printer, orientation):
        printer.setPageOrientation(orientation)
        meret = max(printer.resolution() * 15.0, oldal)
        return pc_modul.PageGeometry(width=meret, height=meret, margin=0.0)

    monkeypatch.setattr(
        pc_modul.PrintController, "_preview_page_geometry", hamis_elonezeti
    )
    monkeypatch.setattr(
        pc_modul.PrintController, "_device_page_geometry", staticmethod(hamis_eszkoz)
    )


@pytest.fixture
def ket_kep(qt_app, tmp_path):
    """⚠️ SAJÁT beállítás-tár, nem a gépé.

    A nyomatméret tartós beállítás (`print/lastSize`, #1782). Alapértelmezett
    `QSettings()`-szel a teszt a GÉP állapotára ül rá: Linuxon egy ini-fájlra
    a `~/.config`-ban, Windowson a **registrybe**. A CI windows-lába emiatt
    bukott vissza a 4×6-os alapértelmezésre a beállított 8×10 helyett
    (`0,667 == 0,8` — a lap aránya a rossz méreté volt).

    A tmp_path-beli ini-fájl tesztenként friss, tehát a teszt ugyanazt
    méri minden gépen és minden sorrendben.
    """
    egy = make_jpeg(tmp_path / "egy.jpg", size=(400, 200))
    ketto = make_jpeg(tmp_path / "ketto.jpg", size=(200, 400))
    photos = [
        _FakePhoto(folder_path=str(tmp_path), name=egy.name),
        _FakePhoto(folder_path=str(tmp_path), name=ketto.name),
    ]
    beallitasok = QSettings(
        str(tmp_path / "settings.ini"), QSettings.Format.IniFormat
    )
    return PrintController(photo_source=lambda: photos, settings=beallitasok)


class TestALapszam:
    """#3647 óta a fizikai lapszám a nyomatmérettől és a papírtól függ (a
    rácsba rendezést önmagában a `printing/test_nyomtatasi_racs_3647.py`
    méri) — ezért itt egyetlen cellás lapra kényszerítve az „N cella = N
    lap" azonosság ellenőrizhető, a jegy #1819 eredeti szándéka szerint."""

    def test_ket_kep_ket_peldany_NEGY_lap(self, ket_kep, monkeypatch):
        """A #1819 jegy „Kész, ha" pontja, szó szerint."""
        _egyetlen_cellas_lapot_kenyszerit(monkeypatch)
        assert ket_kep.printPageCount([0, 1], 2) == 4

    def test_egy_peldany_valtozatlan(self, ket_kep, monkeypatch):
        _egyetlen_cellas_lapot_kenyszerit(monkeypatch)
        assert ket_kep.printPageCount([0, 1], 1) == 2

    def test_a_nulla_peldany_EGYNEK_szamit(self, ket_kep, monkeypatch):
        """A nulla nem „ne nyomtass", hanem hibás bemenet — a +/− úgyis
        egynél áll meg."""
        _egyetlen_cellas_lapot_kenyszerit(monkeypatch)
        assert ket_kep.printPageCount([0, 1], 0) == 2

    def test_a_nem_dekodolhato_kep_LAPOT_SEM_kap(self, qt_app, tmp_path, monkeypatch):
        """Videó/sérült fájl: a lapszám sem tartalmazhatja."""
        _egyetlen_cellas_lapot_kenyszerit(monkeypatch)
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
        _egyetlen_cellas_lapot_kenyszerit(monkeypatch)
        kapott: list[int] = []
        eredeti = PrintController._paint_pages

        def figyelo(printer, grid, images, mode, lap_kesz=None):
            # #3016: a rajzolo egy OPCIONALIS laponkenti visszahivast is kap
            # — a dublornek at kell adnia, kulonben a haladas-jelzes nema
            # marad, es a `_run` kapuja sem mérodne
            kapott.append(len(images))
            return eredeti(printer, grid, images, mode, lap_kesz)

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
        _egyetlen_cellas_lapot_kenyszerit(monkeypatch)
        kapott: list[int] = []
        eredeti = PrintController._paint_pages

        def figyelo(printer, grid, images, mode, lap_kesz=None):
            # #3016: a rajzolo egy OPCIONALIS laponkenti visszahivast is kap
            # — a dublornek at kell adnia, kulonben a haladas-jelzes nema
            # marad, es a `_run` kapuja sem mérodne
            kapott.append(len(images))
            return eredeti(printer, grid, images, mode, lap_kesz)

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
    def test_kirajzol_egy_lapot(self, ket_kep, tmp_path, monkeypatch):
        _egyetlen_cellas_lapot_kenyszerit(monkeypatch)
        cel = tmp_path / "elonezet.png"
        ok = ket_kep.renderPreviewPage([0, 1], "fit", "auto", 1, 0, str(cel))
        assert ok is True
        assert cel.exists() and cel.stat().st_size > 0

    def test_a_tartomanyon_KIVULI_lap_elutasitva(self, ket_kep, tmp_path, monkeypatch):
        _egyetlen_cellas_lapot_kenyszerit(monkeypatch)
        cel = tmp_path / "nincs.png"
        assert ket_kep.renderPreviewPage([0, 1], "fit", "auto", 1, 2, str(cel)) is False
        assert ket_kep.renderPreviewPage([0, 1], "fit", "auto", 1, -1, str(cel)) is False

    def test_a_peldanyszam_UJ_lapokat_ad(self, ket_kep, tmp_path, monkeypatch):
        """Két képnél a 2. lap csak akkor létezik, ha két példány van —
        EGYETLEN cellás lapra kényszerítve (#3647), különben a 2. lap egy
        nagyobb papíron/kisebb nyomatméretnél MÁR az első példánnyal is
        létezne, és a próba nem azt mérné, amit a neve ígér."""
        _egyetlen_cellas_lapot_kenyszerit(monkeypatch)
        cel = tmp_path / "p.png"
        assert ket_kep.renderPreviewPage([0, 1], "fit", "auto", 1, 2, str(cel)) is False
        assert ket_kep.renderPreviewPage([0, 1], "fit", "auto", 2, 2, str(cel)) is True

    def test_a_lap_a_PAPIRT_mutatja_nem_a_nyomatmeretet(
        self, ket_kep, tmp_path, monkeypatch
    ):
        """#3647: az előnézet a PAPÍRT mutatja, rajta a cellákkal — nem a
        választott nyomatméret arányát (a #2494-lecke: kirajzolt képen
        mérve). Egy nem négyzetes, kontrollált papírméretre kényszerítve
        az előnézeti PNG arányának a PAPÍRT kell követnie, nem az itt
        beállított M8X10 nyomatméretet (8/10 = 0,8 — jól megkülönböztethető
        a papír 0,5-ös arányától)."""
        import picasapy.app.print_controller as pc_modul

        def hamis_elonezeti(self, printer_name, *, landscape):  # noqa: ARG001
            szeles, magas = (2000.0, 1000.0) if landscape else (1000.0, 2000.0)
            return pc_modul.PageGeometry(width=szeles, height=magas, margin=0.0)

        monkeypatch.setattr(
            PrintController, "_preview_page_geometry", hamis_elonezeti
        )
        ket_kep.setPrintSize("M8X10")
        cel = tmp_path / "nagy.png"
        assert ket_kep.renderPreviewPage([0], "fit", "portrait", 1, 0, str(cel))
        kep = QImage(str(cel))
        assert kep.width() / kep.height() == pytest.approx(1000.0 / 2000.0, abs=0.01)

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
        assert "enabled: printWindow.copies > 1" in blokk_horgonyra(
            _DIALOG, 'objectName: "printCopiesMinusButton"'
        )

    def test_a_peldanyszam_ELJUT_a_nyomtatasig(self):
        """A #1153 osztálya: a gomb állít egy számot, amit senki nem visz
        tovább."""
        assert "printWindow.orientation, printWindow.copies)" in _DIALOG
        # ⚠️ #2540: a határ a hívás ZÁRÓJELPÁRJA. Rögzített ablakkal a
        # SZOMSZÉD hívás (`renderContactSheetPdf`) argumentumai is
        # belelógtak — egy oda átadott érték is „bizonyította" volna.
        assert "printWindow.copies" in hivas_argumentumai(
            _DIALOG, "renderPrintPreviewPdf"
        )

    def test_a_lapszam_a_mert_alakot_koveti(self):
        """#1960: a mért alak `%d / %d`, de a SORREND nyelvfüggő — az
        angol erőforrás `%1$d of %2$d`, a magyar `%2$d / %1$d`. Ezért
        összefűzés helyett pozíció-argumentumos, FORDÍTHATÓ sablonra
        állítunk: a sorrendet a `.ts` adja, nem a kód."""
        blokk = blokk_horgonyra(_DIALOG, 'objectName: "printPreviewPageText"')
        assert 'qsTr("%1 / %2")' in blokk
        assert ".arg(printWindow.previewPage + 1)" in blokk
        assert ".arg(printWindow.previewPageCount)" in blokk

    def test_a_lapozas_nem_lep_ki_a_tartomanybol(self):
        assert "enabled: printWindow.previewPage > 0" in blokk_horgonyra(
            _DIALOG, 'objectName: "printPreviewPrevButton"'
        )
        assert "previewPageCount - 1" in blokk_horgonyra(
            _DIALOG, 'objectName: "printPreviewNextButton"'
        )

    def test_az_elonezet_gyorstara_KI_van_kapcsolva(self):
        """Ugyanaz a fájlnév kap új tartalmat minden lapozáskor — a Qt
        URL szerint gyorstáraz (a #1186 hibaosztálya)."""
        assert "cache: false" in blokk_horgonyra(
            _DIALOG, 'objectName: "printPreviewImage"'
        )
