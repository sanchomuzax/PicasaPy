"""A #3647 PR (#3685) átnézésén talált leletek őrei.

Az itt rögzített hét lelet:

1. [KRITIKUS] Teljes oldal / A4-es 8×10: a cella nem fér el rácsként —
   a régi, egyképes, oldalra illesztő ágra kell visszaesni
   (`grid_layout.full_page_pages`), nem `printPageCount = 0`-ra.
2. — (a `test_nyomtatas_haladas_3016.py` fedi, egyetlen cellás lapra
   kényszerítve.)
3. — (a `printing/test_nyomtatasi_racs_3647.py` fedi: a `choose_page_orientation`
   a CELLÁT forgatja, nem a papírt.)
4. [MAGAS] Crop to Fit (FILL): a cella-tartalom NEM lóghat át a szomszéd
   cellába — `painter.save()`/`setClipRect()`/`restore()` cellánként.
5. — (a `printing/test_nyomtatasi_racs_3647.py` fedi: a részben teli sor
   balra zár, a teli sor oszloppozícióin.)
6. [KÖZEPES] Az előnézet és a nyomat UGYANAZT a cella-geometriát használja
   — a `_draw_options_page` nem vonhat le egy MÁSODIK margót.
7. [KÖZEPES] A `printFailed` fordítható szöveget kap, nem nyers kivétel-szöveget.

Ez a fájl a 1./4./6./7. leletet fedi a `PrintController` szintjén, plusz egy
KIRAJZOLT próbát (8. pont): az előnézeti PNG-t ténylegesen kirajzoltatjuk, és
a PIXELEKEN mérünk — a #2494-lecke szerint a számolt geometria önmagában nem
bizonyíték."""

from __future__ import annotations

import os
from dataclasses import dataclass

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PIL import Image
from PySide6.QtCore import QSettings
from PySide6.QtGui import QColor, QGuiApplication, QImage

try:
    from picasapy.app.print_controller import PrintController
    from picasapy.printing.dpi import NyomatMeret
    from picasapy.printing.grid_layout import GridCell, GridPage
    from picasapy.printing.layout import PrintFitMode
    from picasapy.printing.options import load_print_options

    _VAN = True
except ImportError:  # pragma: no cover — csonka PySide6-telepítésen
    PrintController = None
    _VAN = False

pytestmark = pytest.mark.skipif(
    not _VAN, reason="a PySide6.QtPrintSupport modul hiányzik ezen a gépen"
)


@pytest.fixture(scope="module")
def qt_app():
    return QGuiApplication.instance() or QGuiApplication([])


@dataclass
class _FakePhoto:
    folder_path: str
    name: str


def _szinkep(path, size=(60, 60), color=(220, 20, 20)):
    """Egyszínű JPEG — a `make_jpeg` mindig pirosat ad, itt SZÍNENKÉNT
    kell megkülönböztetni a cellákat/réseket a kirajzolt próbában."""
    Image.new("RGB", size, color).save(path, "JPEG", quality=95)
    return path


def _sajat_beallitasok(tmp_path, nev="settings.ini"):
    return QSettings(str(tmp_path / nev), QSettings.Format.IniFormat)


def _pixel(kep: QImage, x: float, y: float) -> QColor:
    return QColor(kep.pixel(int(round(x)), int(round(y))))


def _feher_e(szin: QColor, tures: int = 12) -> bool:
    return szin.red() >= 255 - tures and szin.green() >= 255 - tures and szin.blue() >= 255 - tures


class _HamisNyomtatoKep(QImage):
    """`QImage`, ami `.resolution()`-t is ad — a `_paint_pages_with_options`
    a `printer.resolution()`-t hívja a betűméretezéshez; a valódi `QPrinter`
    helyett ez a vászon áll a próbában, hogy pixelenként lehessen ellenőrizni
    a kirajzolt lapot `QPainter`/PDF nélkül."""

    def resolution(self) -> int:
        return 96


class TestTeljesOldalEsNagyMeretVisszaeses:
    """1. lelet [KRITIKUS]: ha a cella egyik tájolással sem fér el
    rácsként a papíron, a régi egyképes ágra kell visszaesni — nem
    `printPageCount = 0`-ra, előnézet és nyomat nélkül."""

    def test_teljes_oldal_nem_ad_nulla_lapot(self, qt_app, tmp_path):
        """„Teljes oldal” (`TELJES_OLDAL`, csak a metrikus/hu készletben) —
        a nyomatméret majdnem akkora, mint maga a lap, tehát margóval
        CELLÁKÉNT egyik tájolással sem fér el."""
        foto = _szinkep(tmp_path / "kep.jpg")
        beallitasok = _sajat_beallitasok(tmp_path)
        beallitasok.setValue("general/language", "hu")
        vezerlo = PrintController(
            photo_source=lambda: [_FakePhoto(str(tmp_path), foto.name)],
            settings=beallitasok,
        )
        vezerlo.setPrintSize("TELJES_OLDAL")

        assert vezerlo.printPageCount([0], 1) >= 1, (
            "a Teljes oldal nyomatméret 0 lapot adott — a cella nem fér el "
            "rácsként, de a régi egyképes ágra kellett volna visszaesni"
        )

        elonezet = tmp_path / "elonezet.png"
        sikeres_e = []
        vezerlo.printFailed.connect(lambda _uzenet: sikeres_e.append(False))
        assert vezerlo.renderPreviewPage([0], "fit", "auto", 1, 0, str(elonezet))
        assert elonezet.exists() and elonezet.stat().st_size > 0

        pdf = tmp_path / "ki.pdf"
        hibak = []
        vezerlo.printFailed.connect(hibak.append)
        assert vezerlo.renderPrintPreviewPdf([0], "fit", "auto", str(pdf))
        assert pdf.exists() and pdf.stat().st_size > 0
        assert not hibak, f"printFailed jött, pedig sikeresnek kellett lennie: {hibak}"

    def test_8x10_a4n_nem_ad_nulla_lapot(self, qt_app, tmp_path):
        """A hüvelykes 8×10 az A4-es (210 × 297 mm) papírnál ALIG nagyobb —
        margóval már nem fér el cellaként, de ez sem adhat 0 lapot."""
        foto = _szinkep(tmp_path / "kep.jpg")
        vezerlo = PrintController(
            photo_source=lambda: [_FakePhoto(str(tmp_path), foto.name)],
            settings=_sajat_beallitasok(tmp_path),
        )
        vezerlo.setPrintSize("M8X10")

        assert vezerlo.printPageCount([0], 1) >= 1

        elonezet = tmp_path / "elonezet.png"
        assert vezerlo.renderPreviewPage([0], "fit", "auto", 1, 0, str(elonezet))
        assert elonezet.exists() and elonezet.stat().st_size > 0

    def test_tobb_kep_annyi_lapot_ad_a_visszaesett_agon(self, qt_app, tmp_path):
        """A visszaesett (egyképes) ágon is a szokásos szabály áll: N kép
        ⇒ N lap — a `full_page_pages` ezt garantálja."""
        fotok = [
            _szinkep(tmp_path / f"kep{i}.jpg", color=(20 * i, 20, 200))
            for i in range(3)
        ]
        beallitasok = _sajat_beallitasok(tmp_path)
        beallitasok.setValue("general/language", "hu")
        vezerlo = PrintController(
            photo_source=lambda: [
                _FakePhoto(str(tmp_path), f.name) for f in fotok
            ],
            settings=beallitasok,
        )
        vezerlo.setPrintSize("TELJES_OLDAL")
        assert vezerlo.printPageCount([0, 1, 2], 1) == 3


class TestCropToFitNemLogAtSzomszedba:
    """4. lelet [MAGAS]: Crop to Fit (FILL) módban a kép a cellánál
    NAGYOBBRA nőhet — cellánként vágni kell, különben átlóg a szomszéd
    cellába (vagy a lap margójába)."""

    #: két cella, KÖZTÜK 50 képpontos réssel (y = 100 .. 150) — a rés az
    #: egyetlen olyan terület, amit SE cella 0, SE cella 1 saját tartalma
    #: nem fedhet le legitim módon (a FILL definíció szerint egy cella
    #: mindig a SAJÁT téglalapját teljesen kitölti — a rés ezért az
    #: egyetlen hely, ahol az átlógás egyértelműen mérhető).
    _CELLA0 = GridCell(x=0.0, y=0.0, width=200.0, height=100.0)
    _CELLA1 = GridCell(x=0.0, y=150.0, width=200.0, height=100.0)

    def _kepek(self):
        # cella0 aránya 200/100=2.0; egy 250×200-as (1.25 arányú) kép
        # FILL módban 200 széles × 160 magas lesz — 30-30 képpont
        # túllógással a cella felett ÉS alatt (a rés belsejébe, y=100..130).
        piros = QImage(250, 200, QImage.Format.Format_RGB32)
        piros.fill(QColor(220, 20, 20))
        kek = QImage(200, 100, QImage.Format.Format_RGB32)
        kek.fill(QColor(20, 20, 220))
        return piros, kek

    def test_paint_pages_nem_logat_at_a_resbe(self, qt_app):
        """A sima (szegély/felirat nélküli) rajzoló ág — `_paint_pages`."""
        lap = QImage(220, 320, QImage.Format.Format_RGB32)
        lap.fill(QColor(255, 255, 255))
        grid = (GridPage(first=0, count=2, cells=(self._CELLA0, self._CELLA1)),)
        piros, kek = self._kepek()

        PrintController._paint_pages(lap, grid, [piros, kek], PrintFitMode.FILL)

        # a rés belsejében (y=115, jóval a cella1 kezdete — y=150 — előtt)
        # a pixel a tesztelőtt (a javítás előtt) PIROS volt — a cella0
        # átlógott. Javítva FEHÉRNEK kell maradnia.
        resben = _pixel(lap, 100, 115)
        assert _feher_e(resben), (
            f"a cella0 (FILL) átlógott a résbe a szomszéd cella felé: {resben.getRgb()}"
        )
        # kontroll: a cella0 SAJÁT területén (y=50) tényleg piros
        assert not _feher_e(_pixel(lap, 100, 50))
        # kontroll: a cella1 SAJÁT területén (y=200) tényleg kék
        cella1_szin = _pixel(lap, 100, 200)
        assert cella1_szin.blue() > cella1_szin.red()

    def test_paint_pages_with_options_nem_logat_at_a_resbe(self, qt_app, tmp_path):
        """A szegély-/felirat-ág — `_paint_pages_with_options`, amely a
        `_draw_options_page`-et hívja cellánként."""
        lap = _HamisNyomtatoKep(220, 320, QImage.Format.Format_RGB32)
        lap.fill(QColor(255, 255, 255))
        grid = (GridPage(first=0, count=2, cells=(self._CELLA0, self._CELLA1)),)
        piros, kek = self._kepek()
        opciok = load_print_options(_sajat_beallitasok(tmp_path))
        rekord = _FakePhoto(str(tmp_path), "x.jpg")

        PrintController._paint_pages_with_options(
            lap, grid, [piros, kek], [rekord, rekord], PrintFitMode.FILL, opciok
        )

        resben = _pixel(lap, 100, 115)
        assert _feher_e(resben), (
            f"a cella0 (FILL) átlógott a résbe a szomszéd cella felé "
            f"(_paint_pages_with_options): {resben.getRgb()}"
        )

    def test_renderpreviewpage_nem_logat_at_a_resbe(self, qt_app, tmp_path, monkeypatch):
        """Az ELŐNÉZET (`renderPreviewPage`) ugyanígy vág — ez a
        `_paint_pages_with_options`-től FÜGGETLEN kódág (a hívó maga
        vágja a `painter`-t, nem közös metóduson át)."""
        import picasapy.app.print_controller as pc_modul

        lap_geometria = pc_modul.PageGeometry(width=220.0, height=320.0, margin=0.0)
        grid = (GridPage(first=0, count=2, cells=(self._CELLA0, self._CELLA1)),)

        def hamis_grid_for_job(*_args, **_kwargs):
            return False, lap_geometria, grid

        monkeypatch.setattr(
            pc_modul.PrintController, "_grid_for_job", staticmethod(hamis_grid_for_job)
        )

        piros = _szinkep(tmp_path / "piros.jpg", size=(250, 200), color=(220, 20, 20))
        kek = _szinkep(tmp_path / "kek.jpg", size=(200, 100), color=(20, 20, 220))
        vezerlo = PrintController(
            photo_source=lambda: [
                _FakePhoto(str(tmp_path), piros.name),
                _FakePhoto(str(tmp_path), kek.name),
            ],
            settings=_sajat_beallitasok(tmp_path),
        )
        cel = tmp_path / "elonezet.png"
        assert vezerlo.renderPreviewPage([0, 1], "fill", "auto", 1, 0, str(cel))

        kep = QImage(str(cel))
        resben = _pixel(kep, 100, 115)
        assert _feher_e(resben, tures=25), (
            f"az ELŐNÉZET (renderPreviewPage) átlógott a résbe: {resben.getRgb()}"
        )


class TestElonezetEsNyomatAzonosGeometria:
    """6. lelet [KÖZEPES]: a `_draw_options_page` a cellát korábban egy
    TELJES lapnak tekintette, és emiatt MÉG EGY margót levont a szélein —
    a `_paint_pages` (a sima ág) viszont a cella TELJES területét használja.
    A két ágnak UGYANAZT a képhelyet kell adnia egyforma bemenetre."""

    def test_ugyanolyan_kepelhelyezest_ad_mint_a_sima_ag(self, tmp_path, qt_app):
        from picasapy.printing.layout import PageGeometry, compute_print_layout

        cella = GridCell(x=10.0, y=20.0, width=300.0, height=200.0)
        kep = QImage(300, 150, QImage.Format.Format_RGB32)
        kep.fill(QColor(10, 10, 10))

        # a sima ág (`_paint_pages`) elhelyezése — margó nélküli cella
        vart = compute_print_layout(
            PageGeometry(width=cella.width, height=cella.height, margin=0.0),
            kep.width(),
            kep.height(),
            PrintFitMode.FIT,
        )
        vart_x = cella.x + vart.x
        vart_y = cella.y + vart.y

        # a szegély-/felirat-ág (`_draw_options_page`) elhelyezése —
        # szöveg/szegély NÉLKÜLI beállításokkal, hogy csak a margó-hiba
        # látszódjon
        opciok = load_print_options(_sajat_beallitasok(tmp_path))
        assert opciok.textSource == 0 and not opciok.border, (
            "a próba feltétele, hogy az alapbeállítás ne rajzoljon "
            "szegélyt/feliratot — különben nem a margóhibát mérnénk"
        )

        lap = QImage(400, 300, QImage.Format.Format_RGB32)
        lap.fill(QColor(255, 255, 255))
        from PySide6.QtCore import QRectF
        from PySide6.QtGui import QPainter

        painter = QPainter(lap)
        try:
            PrintController._draw_options_page(
                painter,
                QRectF(cella.x, cella.y, cella.width, cella.height),
                kep,
                _FakePhoto(str(tmp_path), "x.jpg"),
                PrintFitMode.FIT,
                opciok,
                96.0,
            )
        finally:
            painter.end()

        # a kép bal felső, nem-fehér pixelét keressük — annak a VÁRT
        # elhelyezés bal felső sarkával kell egyeznie
        talalt = None
        for y in range(lap.height()):
            for x in range(lap.width()):
                if not _feher_e(_pixel(lap, x, y), tures=5):
                    talalt = (x, y)
                    break
            if talalt:
                break
        assert talalt is not None, "a kép nem rajzolódott ki"
        assert talalt[0] == pytest.approx(vart_x, abs=1.5), (
            f"az X eltolás eltér a sima ágétól — a `_draw_options_page` "
            f"MÉG EGY margót vonhat le: kapott={talalt}, várt=({vart_x}, {vart_y})"
        )
        assert talalt[1] == pytest.approx(vart_y, abs=1.5), (
            f"az Y eltolás eltér a sima ágétól: kapott={talalt}, várt=({vart_x}, {vart_y})"
        )


class TestHibauzenetForditva:
    """7. lelet [KÖZEPES]: a `printFailed` FORDÍTHATÓ szöveget kapjon, ne
    a nyers Python-kivétel szövegét."""

    def test_ervenytelen_fit_mode_forditott_uzenetet_ad(self, qt_app, tmp_path):
        foto = _szinkep(tmp_path / "kep.jpg")
        vezerlo = PrintController(
            photo_source=lambda: [_FakePhoto(str(tmp_path), foto.name)],
            settings=_sajat_beallitasok(tmp_path),
        )
        uzenetek = []
        vezerlo.printFailed.connect(uzenetek.append)
        ok = vezerlo.printRows([0], "", "nem-letezo-mod", "auto")
        assert ok is False
        assert uzenetek, "nem jött printFailed"
        # a NYERS Python `ValueError` szövege ('...' is not a valid
        # PrintFitMode) NEM mehet ki egyedül — a fordítható sablonnak
        # ('Invalid print settings: %1' / 'Érvénytelen nyomtatási
        # beállítás: %1') kell körbevennie
        assert uzenetek[0] != "'nem-letezo-mod' is not a valid PrintFitMode"
        assert "nem-letezo-mod" in uzenetek[0]

    def test_a_ts_fajl_tartalmazza_az_uj_sablont(self):
        from pathlib import Path

        import picasapy.app

        ts_ut = Path(picasapy.app.__file__).parent / "i18n" / "picasapy_hu.ts"
        szoveg = ts_ut.read_text(encoding="utf-8")
        assert "<source>Invalid print settings: %1</source>" in szoveg
        assert "Érvénytelen nyomtatási beállítás: %1" in szoveg


class TestKirajzoltProba:
    """8. pont: az előnézeti lapot ténylegesen kirajzoltatjuk, és a
    PIXELEKEN mérünk — a #2494-lecke szerint a számolt geometria önmagában
    nem bizonyíték, a kirajzolt kép a mérce."""

    def _vezerlo(self, tmp_path, *, szin=(220, 20, 20), meret_px=(60, 60)):
        foto = _szinkep(tmp_path / "kep.jpg", size=meret_px, color=szin)
        return PrintController(
            photo_source=lambda: [_FakePhoto(str(tmp_path), foto.name)],
            settings=_sajat_beallitasok(tmp_path),
        )

    def test_4x6_5_pelany_harom_lapot_ad_fekvo_cellakkal(self, qt_app, tmp_path):
        """Élő referencia (Colab EN 29, „1 of 3”): ÁLLÓ A4-en két FEKVŐ
        6×4 cella egymás alatt, 3 lapon 2+2+1 elosztásban."""
        vezerlo = self._vezerlo(tmp_path)
        vezerlo.setPrintSize("M4X6")
        assert vezerlo.printPageCount([0], 5) == 3

        # a nyers rács a KIRAJZOLÁS ELŐTT, hogy tudjuk, HOVA mérjünk —
        # de a próba a TÉNYLEGES PNG pixeleit ellenőrzi, nem áll meg a
        # számításnál (#2494-lecke)
        from picasapy.printing.grid_layout import choose_page_orientation

        portrait_page = vezerlo._preview_page_geometry("", landscape=False)
        meret = NyomatMeret.M4X6
        dpi = 96.0
        fekvo_e, lapok = choose_page_orientation(
            portrait_page, meret.szeles_huvelyk * dpi, meret.magas_huvelyk * dpi, 5
        )
        assert fekvo_e is True, "a cellának FEKVŐ tájolásúnak kell lennie"
        assert [lap.count for lap in lapok] == [2, 2, 1]

        elso_lap = lapok[0]
        c0, c1 = elso_lap.cells
        assert c0.width > c0.height, "a cella nem FEKVŐ tájolású"
        assert c1.x == pytest.approx(c0.x), "a két cella nem áll egymás ALATT"
        assert c1.y > c0.y

        cel = tmp_path / "utana_4x6_5.png"
        assert vezerlo.renderPreviewPage([0], "fit", "auto", 5, 0, str(cel))
        kep = QImage(str(cel))
        assert kep.width() == pytest.approx(portrait_page.width, abs=1)
        assert kep.height() == pytest.approx(portrait_page.height, abs=1)

        # a KIRAJZOLT lapon a két cella KÖZEPÉN a mi színünknek kell
        # állnia (nem fehérnek) — ez bizonyítja, hogy a lap tényleg a
        # számolt geometria szerint rajzolódott ki
        for cella in (c0, c1):
            kozep = _pixel(kep, cella.x + cella.width / 2, cella.y + cella.height / 2)
            assert not _feher_e(kozep), (
                f"a kirajzolt lapon a {cella} cella közepén FEHÉR van — a "
                "kép nem a számolt cellára rajzolódott"
            )
        # a két cella KÖZÖTTI rés közepén viszont fehérnek kell maradnia
        res_kozep_y = (c0.y + c0.height + c1.y) / 2
        assert _feher_e(_pixel(kep, c0.x + c0.width / 2, res_kozep_y))

    def test_tarca_5_pelany_masodik_sora_balra_zar(self, qt_app, tmp_path):
        """Élő referencia (Colab EN 30): a 3+2-es rács MÁSODIK sora az 1.
        és 2. oszlop ALATT áll, nem középen."""
        vezerlo = self._vezerlo(tmp_path, szin=(20, 140, 20))
        vezerlo.setPrintSize("TARCA")
        assert vezerlo.printPageCount([0], 5) == 1

        from picasapy.printing.grid_layout import choose_page_orientation

        portrait_page = vezerlo._preview_page_geometry("", landscape=False)
        meret = NyomatMeret.TARCA
        dpi = 96.0
        _fekvo_e, lapok = choose_page_orientation(
            portrait_page, meret.szeles_huvelyk * dpi, meret.magas_huvelyk * dpi, 5
        )
        (lap,) = lapok
        elso_sor = lap.cells[:3]
        masodik_sor = lap.cells[3:]
        assert len(elso_sor) == 3
        assert len(masodik_sor) == 2

        cel = tmp_path / "utana_tarca_5.png"
        assert vezerlo.renderPreviewPage([0], "fit", "auto", 5, 0, str(cel))
        kep = QImage(str(cel))

        # a kirajzolt lapon: a 2. sor cellái a kirajzolt tartalom szerint
        # is az 1. és 2. OSZLOP alatt vannak — az X-koordinátájuk
        # megegyezik az 1. sor megfelelő celláiéval
        for felso, also in zip(elso_sor[:2], masodik_sor, strict=True):
            felso_kozep = _pixel(kep, felso.x + felso.width / 2, felso.y + felso.height / 2)
            also_kozep = _pixel(kep, also.x + also.width / 2, also.y + also.height / 2)
            assert not _feher_e(felso_kozep)
            assert not _feher_e(also_kozep)
            assert also.x == pytest.approx(felso.x)

    def test_fullpage_visszaesett_agat_is_kirajzolja(self, qt_app, tmp_path):
        """1. lelet, kirajzolva: a Teljes oldal (visszaesett, egyképes ág)
        előnézete is TÉNYLEGESEN kirajzolódik, nem üres/fehér lap."""
        vezerlo = self._vezerlo(tmp_path, szin=(140, 20, 140))
        beallitasok = vezerlo._settings
        beallitasok.setValue("general/language", "hu")
        vezerlo.setPrintSize("TELJES_OLDAL")
        assert vezerlo.printPageCount([0], 1) >= 1

        cel = tmp_path / "utana_fullpage.png"
        assert vezerlo.renderPreviewPage([0], "fit", "auto", 1, 0, str(cel))
        kep = QImage(str(cel))
        kozep = _pixel(kep, kep.width() / 2, kep.height() / 2)
        assert not _feher_e(kozep), (
            "a Teljes oldal (visszaesett) előnézete a lap közepén FEHÉR — "
            "a kép nem rajzolódott ki"
        )
