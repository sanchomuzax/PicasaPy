"""A néző többi B-listás vezérlője VALÓDI kattintással (#5150, 7. rész, 2. fájl).

Lefedve: PhotoViewer.qml (kollázs, lejátszás, létrehozás, arc-kapcsoló, pipetta,
retusálás, szöveg), SlideshowView.qml (kilépés, lejátszás, forgatás, felirat,
diaidő), VideoPlayerControls.qml (1:1, teljes képernyő), VideoPlayerView.qml
(vágás eleje és vége). A már lefedett tételeket (lásd a jelentést) nem ismételjük.

Parancsot közvetlenül nem indítunk: a vetítést a Nézet ▸ Diavetítés valódi
menüpontja indítja; a léptetés és a vezérlősáv állapotát előkészítjük.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from conftest import _build_qml_app
from PySide6.QtCore import QPoint, QPointF, Qt
from PySide6.QtGui import QWindow
from PySide6.QtTest import QTest

from picasapy.app.collage_controller import COLLAGE_OUTPUT_DIR_KEY
from picasapy.collage.autosave import AUTOSAVE_NAME
from picasapy.collage.cxf import dumps
from picasapy.collage.draft import project_from_nodes
from picasapy.collage.nodes import SHEET_UNITS, CollageNode
from picasapy.collage.picasa_render import PicasaCollageSettings
from picasapy.collage.themes import NOBORDER, PICTUREPILE
from support.jpeg_factory import make_jpeg
from tests.app.qml_functional._mappa_kep_menu_5150_helpers import (
    MAPPA,
    app_epitese,
    keszits_konyvtarat,
)
from tests.app.qml_functional._nezet_menu_5150_helpers import tetel_kattintasa
from tests.app.qml_functional._racs_helyimenuk_5150_helpers import (
    elokeszit_str, gyerek, kattints, varj, vizualis,
)


@pytest.fixture
def mappa_app(qt_app, tmp_path):
    yield from app_epitese(qt_app, tmp_path)


def _nezo_nyit(window, qt_app, sor: int = 0):
    window.setProperty("viewerOpen", True)
    nezo = gyerek(window, "photoViewer")
    nezo.setProperty("currentIndex", sor)
    qt_app.processEvents()
    return nezo


def _kattints_arany(window, qt_app, elem, fx: float, fy: float) -> None:
    """Valódi kattintás az `elem` belsejének (fx, fy) arányú pontjára."""
    pont = elem.mapToScene(QPointF(elem.width() * fx, elem.height() * fy))
    QTest.mouseClick(window, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier,
                     QPoint(round(pont.x()), round(pont.y())))
    qt_app.processEvents()


# -- PhotoViewer.qml --------------------------------------------------------


def _keszits_kollazst(lib: Path) -> None:
    """A fotós mappa + egy kollázs (JPEG + `.cxf`), ahogy a mentés hagyja."""
    keszits_konyvtarat(lib)
    mappa = lib / MAPPA
    make_jpeg(mappa / "kollazs.jpg", size=(200, 150))
    beallitas = PicasaCollageSettings(
        theme=PICTUREPILE, border=NOBORDER, width=1600, height=1200
    )
    csomopont = CollageNode(
        path=str(mappa / "a_nagy.jpg"), center_x=SHEET_UNITS * 0.5,
        center_y=SHEET_UNITS * 0.3, width=280.0, height=337.0, theta=0.0,
        border=NOBORDER,
    )
    projekt = project_from_nodes([csomopont], beallitas, album_title="Próba")
    (mappa / "kollazs.cxf").write_bytes(dumps(projekt))


def _piszkozatot_keszits(mappa: Path, forras: Path) -> Path:
    """Kép + `autosave.cxf`, saját `.cxf` nélkül: ez a piszkozat (spec 1.)."""
    mappa.mkdir(parents=True, exist_ok=True)
    kep = mappa / "AI10.jpg"
    make_jpeg(kep, size=(200, 150))
    beallitas = PicasaCollageSettings(theme=PICTUREPILE, border=NOBORDER, width=400, height=300)
    csomopont = CollageNode(
        path=str(forras), center_x=SHEET_UNITS * 0.5, center_y=SHEET_UNITS * 0.5,
        width=280.0, height=337.0, theta=0.0, border=NOBORDER,
    )
    projekt = project_from_nodes([csomopont], beallitas, album_title="AI10")
    (mappa / AUTOSAVE_NAME).write_bytes(dumps(projekt))
    return kep


@pytest.fixture
def kollazs_app(qt_app, tmp_path):
    yield from app_epitese(qt_app, tmp_path, kepeket_keszit=_keszits_kollazst)


class TestNezoPhotoViewerVezerlok:
    def test_kollazs_szerkesztese_valodi_kattintassal_megnyitja_a_kollazst(
        self, kollazs_app, qt_app
    ):
        window, controller, _engine = kollazs_app
        window.show()
        controller.selectFolder(str(Path(str(controller.watchedFolders[0])) / MAPPA))
        assert varj(qt_app, lambda: len(controller.photos.photos) == 4), "a mappa nem töltődött be"
        sor = [foto.name for foto in controller.photos.photos].index("kollazs.jpg")
        _nezo_nyit(window, qt_app, sor)
        gomb = gyerek(window, "viewerEditCollageButton")
        assert varj(qt_app, lambda: gomb.property("visible") is True), (
            "a Kollázs szerkesztése gomb nem látszik a kollázson"
        )

        kattints(window, qt_app, gomb)

        assert varj(qt_app, lambda: controller.collageOpen is True), (
            "a Kollázs szerkesztése kattintás nem nyitotta meg a kollázst"
        )
        assert window.property("viewerOpen") is False, "a néző nem záródott be"

    def test_lejatszas_valodi_kattintassal_elindítja_a_diavetitest(self, mappa_app, qt_app):
        window, controller, _motor = mappa_app
        elokeszit_str(window, qt_app, controller)
        _nezo_nyit(window, qt_app, 0)

        kattints(window, qt_app, gyerek(window, "viewerPlayButton"))

        show = gyerek(window, "slideshowView")
        assert varj(qt_app, lambda: show.property("visible") is True), (
            "a Lejátszás kattintás nem indította a diavetítést"
        )
        show.setProperty("playing", False)
        qt_app.processEvents()

    def test_letrehozas_most_valodi_kattintassal_elkeszíti_a_kollazst(
        self, mappa_app, qt_app
    ):
        window, controller, _motor = mappa_app
        lib = Path(str(controller.watchedFolders[0]))
        kollazsok = lib / "Kollazsok"
        controller._get_settings().setValue(COLLAGE_OUTPUT_DIR_KEY, str(kollazsok))
        piszkozat = _piszkozatot_keszits(kollazsok, lib / MAPPA / "a_nagy.jpg")
        controller.rescan()
        assert varj(qt_app, lambda: controller.waitForBackgroundWorkers(0.05))
        controller.selectFolder(str(kollazsok))
        sor = controller.photos.rowOfPath(str(piszkozat))
        assert sor >= 0, "a piszkozat nem került a nézetbe"
        _nezo_nyit(window, qt_app, sor)
        controller._collage_output_width = lambda: 400  # kicsi kimenet: a fájlpárról szól

        kattints(window, qt_app, gyerek(window, "viewerCreateNowButton"))

        assert varj(
            qt_app, lambda: piszkozat.with_suffix(".cxf").exists(), masodperc=30.0
        ), "a Létrehozás most kattintás nem készítette el a kollázst"

    def test_arc_kereteinek_kapcsolo_valodi_kattintassal_bekapcsolja_az_arcokat(
        self, mappa_app, qt_app
    ):
        window, controller, _motor = mappa_app
        elokeszit_str(window, qt_app, controller)
        nezo = _nezo_nyit(window, qt_app, 0)
        assert nezo.property("facesVisible") is False, "a próba feltétele: nincsenek keretek"

        kattints(window, qt_app, gyerek(window, "facesToggleButton"))

        assert varj(qt_app, lambda: nezo.property("facesVisible") is True), (
            "az arc-keretek kapcsoló kattintás nem kapcsolta be a kereteket"
        )

    def test_semleges_pipetta_valodi_kattintassal_kilep_a_pipetta_modbol(
        self, mappa_app, qt_app
    ):
        window, controller, _motor = mappa_app
        elokeszit_str(window, qt_app, controller)
        _nezo_nyit(window, qt_app, 0)
        panel = gyerek(window, "viewerEditorPanel")
        panel.setProperty("neutralPickerActive", True)
        qt_app.processEvents()

        kattints(window, qt_app, gyerek(window, "neutralPickArea"))

        assert varj(qt_app, lambda: panel.property("neutralPickerActive") is False), (
            "a pipetta-terület kattintása nem fejezte be a semleges színválasztást"
        )

    def test_retusalas_valodi_kattintassal_folt_celt_jelol(self, mappa_app, qt_app):
        window, controller, engine = mappa_app
        elokeszit_str(window, qt_app, controller)
        _nezo_nyit(window, qt_app, 0)
        gyerek(window, "viewerEditorPanel").setProperty("retouchActive", True)
        qt_app.processEvents()
        szerkeszto = engine.rootContext().contextProperty("editController")
        assert szerkeszto.retouchPatchPending is False, "a próba feltétele: nincs folt"

        kattints(window, qt_app, gyerek(window, "retouchClickArea"))

        assert varj(qt_app, lambda: szerkeszto.retouchPatchPending is True), (
            "a retusálás-terület kattintása nem jelölte ki a javítandó foltot"
        )

    def test_szovegre_kattintas_utan_ures_helyre_kattintva_megszunik_a_kijeloles(
        self, mappa_app, qt_app
    ):
        window, controller, engine = mappa_app
        elokeszit_str(window, qt_app, controller)
        _nezo_nyit(window, qt_app, 0)
        szerkeszto = engine.rootContext().contextProperty("editController")
        panel = gyerek(window, "viewerEditorPanel")
        panel.setProperty("textActive", True)
        szerkeszto.previewTextPlacement(0.3, 0.6)
        szerkeszto.setTextDraft("Nyaralás")
        szerkeszto.applyText()
        qt_app.processEvents()
        kattints(window, qt_app, vizualis(window, "textOverlayHitTarget_0"))
        assert varj(qt_app, lambda: szerkeszto.textSelectedIndex == 0), (
            "a próba feltétele: a mentett szöveg kijelölhető"
        )

        _kattints_arany(window, qt_app, gyerek(window, "textClickArea"), 0.85, 0.15)

        assert varj(qt_app, lambda: szerkeszto.textSelectedIndex == -1), (
            "az üres képpontra kattintás nem szüntette meg a szövegkijelölést"
        )


# -- SlideshowView.qml ------------------------------------------------------


def _diavetites_indul(window, qt_app):
    """A Nézet ▸ Diavetítés valódi menüponttal indul; a léptetés áll, a sáv látszik."""
    window.setProperty("selectedIndex", 0)
    tetel_kattintasa(window, qt_app, "menuViewSlideshow")
    show = gyerek(window, "slideshowView")
    assert varj(qt_app, lambda: show.property("visible") is True), (
        "a Diavetítés menüpont nem indította a vetítést"
    )
    show.setProperty("playing", False)
    sav = gyerek(window, "slideshowControls")
    sav.setProperty("shown", True)
    assert varj(qt_app, lambda: sav.property("opacity") > 0.99), (
        "a vezérlősáv nem jelent meg"
    )
    return show


class TestDiavetitesVezerlok:
    def test_kilepes_valodi_kattintassal_bezarja_a_vetitest(self, mappa_app, qt_app):
        window, controller, _motor = mappa_app
        elokeszit_str(window, qt_app, controller)
        show = _diavetites_indul(window, qt_app)

        kattints(window, qt_app, gyerek(window, "slideshowExitButton"))

        assert varj(qt_app, lambda: show.property("visible") is False), (
            "a Kilépés kattintás nem zárta be a vetítést"
        )

    def test_lejatszas_gomb_valodi_kattintassal_inditja_es_allitja(self, mappa_app, qt_app):
        window, controller, _motor = mappa_app
        elokeszit_str(window, qt_app, controller)
        show = _diavetites_indul(window, qt_app)

        kattints(window, qt_app, gyerek(window, "slideshowPlayButton"))

        assert varj(qt_app, lambda: show.property("playing") is True), (
            "a lejátszás-gomb kattintás nem indította el a vetítést"
        )
        kattints(window, qt_app, gyerek(window, "slideshowPlayButton"))
        assert varj(qt_app, lambda: show.property("playing") is False), (
            "a második kattintás nem állította meg a vetítést"
        )
        show.setProperty("playing", False)

    def test_jobbra_forgato_elforgatja_a_kepet(
        self, mappa_app, qt_app
    ):
        window, controller, _motor = mappa_app
        elokeszit_str(window, qt_app, controller)
        _diavetites_indul(window, qt_app)
        assert controller.photos.rotateAt(0) == 0, "a próba feltétele: 0 forgatás"

        kattints(window, qt_app, gyerek(window, "slideshowRotateRightButton"))

        assert varj(qt_app, lambda: controller.photos.rotateAt(0) % 4 == 1, 15.0), (
            "a jobbra forgató kattintás nem forgatta el a vetítés képét"
        )

    def test_felirat_mod_gomb_valodi_kattintassal_tovabblep_a_modok_kozott(
        self, mappa_app, qt_app
    ):
        window, controller, _motor = mappa_app
        elokeszit_str(window, qt_app, controller)
        _diavetites_indul(window, qt_app)
        assert controller.slideshowCaptionMode == "caption", "a próba feltétele: a kezdő mód"

        kattints(window, qt_app, gyerek(window, "slideshowCaptionModeButton"))

        assert varj(qt_app, lambda: controller.slideshowCaptionMode == "filename"), (
            "a felirat-mód gomb kattintás nem váltott a következő módra"
        )

    @pytest.mark.parametrize(
        ("nev", "elvart"),
        [("slideshowTimeMinus", 2), ("slideshowTimePlus", 4)],
    )
    def test_a_diaido_valodi_kattintassal_egy_maasodperccel_valtozik(
        self, mappa_app, qt_app, nev, elvart
    ):
        window, controller, _motor = mappa_app
        elokeszit_str(window, qt_app, controller)
        _diavetites_indul(window, qt_app)
        assert controller.slideshowSeconds == 3, "a próba feltétele: az alapérték 3 mp"

        kattints(window, qt_app, gyerek(window, nev))

        assert varj(qt_app, lambda: controller.slideshowSeconds == elvart), (
            f"a(z) {nev} kattintás nem állította a diaidőt {elvart} mp-re"
        )


# -- VideoPlayerControls.qml és VideoPlayerView.qml ---------------------------


def _videoleiras(lib: Path) -> None:
    make_jpeg(lib / "a.jpg", size=(320, 160))
    # szándékosan érvénytelen videó: a lejátszó a kiterjesztésből dönt
    (lib / "b.mp4").write_bytes(b"\x00" * 64)


@pytest.fixture
def video_app(qt_app, tmp_path):
    yield from _build_qml_app(qt_app, tmp_path, kepeket_keszit=_videoleiras)


def _videot_nyit(window, qt_app) -> int:
    """A videó a nézőben, a szerkesztő-sávval együtt (1280×1005, mint a #4566-nál)."""
    window.setProperty("width", 1280)
    window.setProperty("height", 1005)
    window.setProperty("viewerOpen", True)
    viewer = gyerek(window, "photoViewer")
    modell = viewer.property("photosModel")
    sor = next(s for s in range(2) if modell.isVideoAt(s))
    viewer.setProperty("currentIndex", sor)
    assert varj(qt_app, lambda: gyerek(window, "videoPlayerModeControls").isVisible()), (
        "a videó módvezérlője nem látszik a nézőben"
    )
    return sor


class TestNezoVideoVezerlok:
    def test_1_1_valodi_kattintassal_atallitja_a_mozgokep_meretet(self, video_app, qt_app):
        window, _controller, _engine = video_app
        _videot_nyit(window, qt_app)
        modok = gyerek(window, "videoPlayerModeControls")
        assert modok.property("actualSizeEnabled") is False, "a próba feltétele: alapméret"

        kattints(window, qt_app, gyerek(window, "videoActualSizeButton"))

        assert varj(qt_app, lambda: modok.property("actualSizeEnabled") is True), (
            "a 1:1 kattintás nem állította át a mozgókép méretét"
        )

    def test_teljes_kepernyo_valodi_kattintassal_atvalt(self, video_app, qt_app):
        window, _controller, _engine = video_app
        _videot_nyit(window, qt_app)

        kattints(window, qt_app, gyerek(window, "videoFullscreenButton"))

        assert varj(
            qt_app, lambda: window.visibility() == QWindow.Visibility.FullScreen
        ), "a teljes képernyő kattintás nem váltott teljes képernyőre"
        window.showNormal()

    def test_vagas_kezdete_valodi_kattintassal_kezdopontot_rogzit(self, video_app, qt_app):
        window, controller, _engine = video_app
        sor = _videot_nyit(window, qt_app)
        assert controller.photos.movieTrimAt(sor)["start"] == -1, "a próba feltétele: nincs vágás"

        kattints(window, qt_app, gyerek(window, "videoSetInButton"))

        assert varj(qt_app, lambda: controller.photos.movieTrimAt(sor)["start"] >= 0), (
            "a kezdőpont-gomb kattintás nem rögzített kezdőpontot"
        )

    def test_vagas_vege_valodi_kattintassal_befejezopontot_rogzit(self, video_app, qt_app):
        window, controller, _engine = video_app
        sor = _videot_nyit(window, qt_app)
        assert controller.photos.movieTrimAt(sor)["end"] == -1, "a próba feltétele: nincs vágás"

        kattints(window, qt_app, gyerek(window, "videoSetOutButton"))

        assert varj(qt_app, lambda: controller.photos.movieTrimAt(sor)["end"] >= 0), (
            "a befejezőpont-gomb kattintás nem rögzített befejezőpontot"
        )
