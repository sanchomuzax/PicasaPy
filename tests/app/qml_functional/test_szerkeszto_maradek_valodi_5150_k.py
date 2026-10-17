"""A „Szerkesztő" csoport maradék vezérlői VALÓDI egérrel (#5150, 9. rész, K).

Az audit (`scripts/valodi_kattintas_audit.py`) szerinti maradék, a „Szerkesztő"
csoportból:
- a kollázs vászna és három helyi menüje (`collageContextArea`, a csomópont-,
  csoport- és vászon-menü tételei, `collageShuffleButton` a panelen);
- a film-párbeszéd jelölői és gombjai (`movie*`);
- a szerkesztő paneljei: a paraméteres jelölő, a szövegjelölő és a szöveg-mező;
- az e-mail választó tételei (`emailChoice*`, `emailComposeChangeUserButton`);
- a nyomtatás szegély-panel rádiói (`printOption*`).

Parancsot közvetlenül nem indítunk: nincs `triggered`/`clicked`/`activated`
hívás és nincs `.emit()`. A hatást a modell, a controller és a panel
állapotán mérjük. A külső program (`Qt.openUrlExternally`) hívását a
JS-globálison helyettesítjük, és a teszt ezt kimondja.

A helyi menük a főablak (vagy a kollázs-panel nézete) fájában élnek, ezért a
tételeket `findChild`-del keressük; a kattintást az ablak-feloldó `kattints`
küldi a megfelelő ablakba.
"""

from __future__ import annotations

import re

import pytest
from conftest import _build_qml_app, _negyzet_kepek
from PySide6.QtCore import QEvent, QMetaObject, QObject, QPointF, Qt, QUrl, Slot
from PySide6.QtGui import QDesktopServices, QGuiApplication, QKeyEvent
from PySide6.QtTest import QTest
from support.collage_canvas_harness import (
    _child,
    _panel,
    keszits_kepeket,
    nyitott_vezerlo,
)
from support.varakozas import hibaturo_feltetel, var_feltetelre
from _racs_helyimenuk_5150_helpers import gyerek, kattints
from _szerkeszto_5150_helpers import figyel, fulre, nyitott_panel, szerkeszto, szovegeszkoz
from test_menu_talca_egyeb_valodi_5135_b import (
    _beallitas,
    _elokeszit,
    _keszits_konyvtarat,
    _nyomtatas_megnyit,
    _nyomtatas_panel_megnyit,
    _zar,
)


class _UrlFogado(QObject):
    """Az URL-kezelő célja: a `Qt.openUrlExternally` hívásait rögzíti, nem nyit programot."""

    def __init__(self):
        super().__init__()
        self.hivasok: list[str] = []

    @Slot(QUrl)
    def urlt_kapott(self, url: QUrl) -> None:
        self.hivasok.append(url.toString())


def _varj(qt_app, feltetel, masodperc: float = 10.0) -> bool:
    return var_feltetelre(qt_app, hibaturo_feltetel(feltetel), masodperc)


def _gyerek_menu(gyoker, nev: str):
    elem = gyoker.findChild(QObject, nev)
    assert elem is not None, f"{nev} nem található"
    return elem


def _gepel(window, qt_app, szoveg: str) -> None:
    """Valódi billentyűlenyomások az ablakba (a QTest.keyClicks nem fogad QQuickWindow-t)."""
    for betu in szoveg:
        kod = ord(betu.upper())
        for tipus in (QEvent.Type.KeyPress, QEvent.Type.KeyRelease):
            QGuiApplication.sendEvent(
                window, QKeyEvent(tipus, kod, Qt.KeyboardModifier.NoModifier, betu)
            )
    qt_app.processEvents()


def _jobb_sarok(view, qt_app, terulet) -> None:
    """Valódi jobb egérkattintás a `terulet` bal-felső sarka közelében (üres vászon)."""
    pont = terulet.mapToScene(QPointF(3, 3)).toPoint()
    QTest.mouseClick(view, Qt.MouseButton.RightButton, Qt.KeyboardModifier.NoModifier, pont)
    qt_app.processEvents()


def _jobb_klikk(view, qt_app, elem) -> None:
    """Valódi jobb egérkattintás az elem közepén (csomópont-menü)."""
    kattints(view, qt_app, elem, Qt.MouseButton.RightButton)


# --- Kollázs: vászon-menü, csomópont-menük, a vászon parancsai -----------------


@pytest.fixture
def library(tmp_path):
    return keszits_kepeket(tmp_path)


@pytest.fixture
def collage_controller(qt_app, tmp_path, library):
    yield from nyitott_vezerlo(tmp_path, library)


@pytest.fixture
def collage_panel(collage_controller):
    return _panel(collage_controller)


def _csomopont_utvonalak(controller) -> list[str]:
    return [node.path for node in controller.collageNodes.nodes]


class TestKollazsVaszon:
    """A vászon jobb gombos menüje és a vászon-parancsai valódi kattintással."""

    def test_a_vaszon_ures_teruletere_jobb_klikk_megnyitja_a_vaszon_menut(
        self, collage_panel, qt_app
    ):
        view = collage_panel.property("_view")
        terulet = _gyerek_menu(collage_panel, "collageContextArea")
        menu = _gyerek_menu(collage_panel, "collageCanvasMenu")
        assert menu.property("visible") is False, "a próba feltétele: zárt menü"

        _jobb_sarok(view, qt_app, terulet)

        assert _varj(qt_app, lambda: menu.property("visible") is True), (
            "az üres vászonra kattintás nem nyitotta meg a vászon-menüt"
        )

    def test_mindent_kijelol_tetel_valodi_kattintasra_az_osszes_kepet_kijeloli(
        self, collage_panel, collage_controller, qt_app
    ):
        view = collage_panel.property("_view")
        _jobb_sarok(view, qt_app, _gyerek_menu(collage_panel, "collageContextArea"))
        tetel = _gyerek_menu(_gyerek_menu(collage_panel, "collageCanvasMenu"), "collageCanvasMenuSelectAll")
        assert len(collage_controller.collageSelection) == 0, "a próba feltétele: nincs kijelölés"

        kattints(view, qt_app, tetel)

        assert _varj(qt_app, lambda: len(collage_controller.collageSelection) == 3), (
            "a Select All kattintás nem jelölte ki az összes képet"
        )

    def test_kijelolés_megszuntetese_tetel_valodi_kattintasra_uriti_a_kijelolest(
        self, collage_panel, collage_controller, qt_app
    ):
        view = collage_panel.property("_view")
        collage_controller.selectAllNodes()
        assert _varj(qt_app, lambda: len(collage_controller.collageSelection) == 3)
        _jobb_sarok(view, qt_app, _gyerek_menu(collage_panel, "collageContextArea"))
        tetel = _gyerek_menu(_gyerek_menu(collage_panel, "collageCanvasMenu"), "collageCanvasMenuSelectNone")

        kattints(view, qt_app, tetel)

        assert _varj(qt_app, lambda: len(collage_controller.collageSelection) == 0), (
            "a Select None kattintás nem szüntette meg a kijelölést"
        )

    def test_keveres_tetel_valodi_kattintasra_atrendezi_a_kepeket(
        self, collage_panel, collage_controller, qt_app
    ):
        view = collage_panel.property("_view")
        elotte = _csomopont_utvonalak(collage_controller)
        _jobb_sarok(view, qt_app, _gyerek_menu(collage_panel, "collageContextArea"))
        tetel = _gyerek_menu(_gyerek_menu(collage_panel, "collageCanvasMenu"), "collageCanvasMenuShuffle")

        kattints(view, qt_app, tetel)

        assert _varj(qt_app, lambda: _csomopont_utvonalak(collage_controller) != elotte), (
            "a Shuffle Pictures kattintás nem rendezte át a képeket"
        )

    def test_szorasa_tetel_valodi_kattintasra_ujra_elrendezi_a_vasznat(
        self, collage_panel, collage_controller, qt_app
    ):
        view = collage_panel.property("_view")
        elotte = [(n.center_x, n.center_y) for n in collage_controller.collageNodes.nodes]
        _jobb_sarok(view, qt_app, _gyerek_menu(collage_panel, "collageContextArea"))
        tetel = _gyerek_menu(_gyerek_menu(collage_panel, "collageCanvasMenu"), "collageCanvasMenuScatter")

        kattints(view, qt_app, tetel)

        assert _varj(
            qt_app,
            lambda: [(n.center_x, n.center_y) for n in collage_controller.collageNodes.nodes] != elotte,
        ), "a Scatter Pictures kattintás nem sorsolta újra az elrendezést"


class TestKollazsCsomopontMenu:
    """Az egy- és többképes csomópont-menü tételei valódi kattintással."""

    def test_egy_kep_eltavolitas_tetel_valodi_kattintasra_kiveszi_a_kepet(
        self, collage_panel, collage_controller, qt_app
    ):
        view = collage_panel.property("_view")
        assert collage_controller.collageClipCount == 3, "a próba feltétele: három kép"
        _jobb_klikk(view, qt_app, _child(collage_panel, "collageNode0"))
        menu = _gyerek_menu(collage_panel, "collageNodeMenuSingle")
        assert _varj(qt_app, lambda: menu.property("visible") is True)

        kattints(view, qt_app, _gyerek_menu(menu, "collageMenuRemove"))

        assert _varj(qt_app, lambda: collage_controller.collageClipCount == 2), (
            "az Eltávolítás tétel nem vette ki a képet a kollázsból"
        )

    def test_tobb_kep_eltavolitas_tetel_valodi_kattintasra_kiveszi_a_kijeloltet(
        self, collage_panel, collage_controller, qt_app
    ):
        view = collage_panel.property("_view")
        collage_controller.setCollageSelection([0, 1])
        assert _varj(qt_app, lambda: len(collage_controller.collageSelection) == 2)
        _jobb_klikk(view, qt_app, _child(collage_panel, "collageNode0"))
        menu = _gyerek_menu(collage_panel, "collageNodeMenuGroup")
        assert _varj(qt_app, lambda: menu.property("visible") is True)

        kattints(view, qt_app, _gyerek_menu(menu, "collageGroupMenuRemove"))

        assert _varj(qt_app, lambda: collage_controller.collageClipCount == 1), (
            "a csoportos Eltávolítás tétel nem vette ki a kijelölt képeket"
        )

    def test_hatter_tetel_valodi_kattintasra_a_kepet_hatterkent_allitja_be(
        self, collage_panel, collage_controller, qt_app
    ):
        view = collage_panel.property("_view")
        assert collage_controller.collageBackgroundMode != "image", "a próba feltétele: nem kép a háttér"
        _jobb_klikk(view, qt_app, _child(collage_panel, "collageNode1"))
        menu = _gyerek_menu(collage_panel, "collageNodeMenuSingle")
        assert _varj(qt_app, lambda: menu.property("visible") is True)

        kattints(view, qt_app, _gyerek_menu(menu, "collageMenuSetBackground"))

        assert _varj(qt_app, lambda: collage_controller.collageBackgroundMode == "image"), (
            "a Set as Background tétel nem állította képre a hátteret"
        )

    def test_kepkocka_kozeppont_tetel_valodi_kattintasra_beallitja_a_kozeppontot(
        self, collage_panel, collage_controller, qt_app
    ):
        view = collage_panel.property("_view")
        assert collage_controller.collageFrameCenter != 2, "a próba feltétele: nem a 2. kép"
        _jobb_klikk(view, qt_app, _child(collage_panel, "collageNode2"))
        menu = _gyerek_menu(collage_panel, "collageNodeMenuSingle")
        assert _varj(qt_app, lambda: menu.property("visible") is True)

        kattints(view, qt_app, _gyerek_menu(menu, "collageMenuSetFrameCenter"))

        assert _varj(qt_app, lambda: collage_controller.collageFrameCenter == 2), (
            "a Set as Frame Center tétel nem állította be a középső képet"
        )

    def test_elore_hozas_tetel_valodi_kattintasra_a_legfelso_retegbe_viszi(
        self, collage_panel, collage_controller, qt_app
    ):
        view = collage_panel.property("_view")
        utvonal = _csomopont_utvonalak(collage_controller)[0]
        assert _csomopont_utvonalak(collage_controller)[-1] != utvonal, "a próba feltétele: nem felül"
        _jobb_klikk(view, qt_app, _child(collage_panel, "collageNode0"))
        menu = _gyerek_menu(collage_panel, "collageNodeMenuSingle")
        assert _varj(qt_app, lambda: menu.property("visible") is True)

        kattints(view, qt_app, _gyerek_menu(menu, "collageMenuMoveTop"))

        assert _varj(qt_app, lambda: _csomopont_utvonalak(collage_controller)[-1] == utvonal), (
            "a Bring to Top tétel nem vitte a képet a legfelső rétegbe"
        )

    def test_hatra_kuldes_tetel_valodi_kattintasra_a_legalso_retegbe_viszi(
        self, collage_panel, collage_controller, qt_app
    ):
        view = collage_panel.property("_view")
        utvonal = _csomopont_utvonalak(collage_controller)[2]
        assert _csomopont_utvonalak(collage_controller)[0] != utvonal, "a próba feltétele: nem alul"
        _jobb_klikk(view, qt_app, _child(collage_panel, "collageNode2"))
        menu = _gyerek_menu(collage_panel, "collageNodeMenuSingle")
        assert _varj(qt_app, lambda: menu.property("visible") is True)

        kattints(view, qt_app, _gyerek_menu(menu, "collageMenuMoveBottom"))

        assert _varj(qt_app, lambda: _csomopont_utvonalak(collage_controller)[0] == utvonal), (
            "a Move to Bottom tétel nem vitte a képet a legalsó rétegbe"
        )

    def test_megjelenites_es_szerkesztes_tetel_valodi_kattintasra_a_kepet_adja_at(
        self, collage_panel, collage_controller, qt_app
    ):
        view = collage_panel.property("_view")
        utvonal = _csomopont_utvonalak(collage_controller)[1]
        _jobb_klikk(view, qt_app, _child(collage_panel, "collageNode1"))
        menu = _gyerek_menu(collage_panel, "collageNodeMenuSingle")
        assert _varj(qt_app, lambda: menu.property("visible") is True)
        kapott = figyel(collage_controller.collageEditRequested)

        kattints(view, qt_app, _gyerek_menu(menu, "collageMenuViewAndEdit"))

        assert _varj(qt_app, lambda: len(kapott) == 1), (
            "a View and Edit tétel nem kérte a kép szerkesztését"
        )
        assert kapott[0][0] == utvonal, "a szerkesztésre küldött kép nem a kijelölt"


class TestKollazsLetrehozas:
    """A kollázs-panel „Shuffle Pictures" gombja valódi kattintással.

    Ugyanezt az `objectName`-et viseli a `CreateDialogs.qml` „Scramble Collage"
    gombja is, de ahhoz a `collageDialog` nem jelenik meg a főablak fájában
    (a Collage gomb a kollázs-panelt nyitja), ezért azt ebben a teszten nem érjük el.
    """

    def test_a_kollazs_keveres_gomb_valodi_kattintasra_atrendezi_a_kepeket(
        self, qml_app_email, qt_app
    ):
        window, controller, _engine = qml_app_email
        window.setProperty("selectedIndexes", [0, 1])
        window.setProperty("selectedIndex", 0)
        qt_app.processEvents()
        kattints(window, qt_app, gyerek(window, "trayCollageButton"))
        gomb = gyerek(window, "collageShuffleButton")
        assert _varj(qt_app, lambda: gomb.isVisible()), (
            "a Collage gomb nem nyitotta meg a kollázs-panelt: nem látszik a Shuffle Pictures gomb"
        )
        assert _varj(qt_app, lambda: gomb.property("enabled") is True), (
            "a Shuffle Pictures gomb nem lett engedélyezett két kép mellett"
        )
        elotte = _csomopont_utvonalak(controller)

        # két képnél a véletlen sorrend az eredeti is lehet: legfeljebb három valódi kattintás,
        # és legalább egynek át kell rendeznie a képeket
        for _ in range(3):
            kattints(window, qt_app, gomb)
            if _varj(qt_app, lambda: _csomopont_utvonalak(controller) != elotte, 10.0):
                break
        assert _csomopont_utvonalak(controller) != elotte, (
            "a Shuffle Pictures kattintások nem rendezték át a kollázs képeit"
        )


# --- Editor: paraméteres jelölő, szövegjelölő, szöveg-mező -------------------


@pytest.fixture
def negyzet_app(qt_app, tmp_path):
    yield from _build_qml_app(qt_app, tmp_path, kepeket_keszit=_negyzet_kepek)


def _szoveg_rakas(szerkeszto_vezerlo, szoveg: str) -> None:
    """Állapot-előkészítés: egy szövegdoboz a képen, a controlleren át."""
    szerkeszto_vezerlo.previewTextPlacement(0.3, 0.6)
    szerkeszto_vezerlo.setTextDraft(szoveg)
    szerkeszto_vezerlo.applyText()


class TestSzerkesztoPanelek:
    def test_parameter_jelolo_valodi_kattintasra_atallitja_a_parametert(
        self, negyzet_app, qt_app, tmp_path
    ):
        window, _c, viewer, panel = nyitott_panel(negyzet_app, qt_app)
        panel.setProperty("activeTab", 4)
        qt_app.processEvents()
        panel.setProperty("shiftMasodlagos", True)
        qt_app.processEvents()
        csempe = _gyerek_menu(panel, "effectPixelate")
        kattints(window, qt_app, csempe)
        assert _varj(qt_app, lambda: panel.property("paramPanelActive") is True), (
            "a próba feltétele: a paraméteres alpanel nyitva"
        )
        # a paraméter-sorok Repeater-delegáltak: nincs QObject-szülőjük, a vizuális fában keressük
        jelolo = _child(panel, "effectParamCheckbox" + str(6))
        elotte = jelolo.property("checked")

        kattints(window, qt_app, jelolo)

        assert _varj(qt_app, lambda: jelolo.property("checked") == (not elotte)), (
            "a paraméteres jelölő kattintás nem váltotta át az állapotát"
        )
        # a paraméter a szűrőben él: az alkalmazás után a .picasa.ini-ben látszik (az utolsó mező)
        kattints(window, qt_app, _gyerek_menu(panel, "effectParamApplyButton"))
        ini = tmp_path / "kepek" / ".picasa.ini"
        assert _varj(
            qt_app,
            lambda: ini.exists() and re.search(r"PicnikFocalPixelate=[^;]*,1;", ini.read_text(encoding="utf-8")),
        ), "a jelölő kattintás nem jutott el a mentett szűrő paraméteréig"

    def test_szovegjelolo_valodi_kattintasra_elrejti_a_kepre_irt_szoveget(
        self, negyzet_app, qt_app
    ):
        window, _c, viewer, panel = nyitott_panel(negyzet_app, qt_app)
        lanc = szerkeszto(viewer)
        fulre(window, qt_app, "editTabFixes")
        assert _varj(qt_app, lambda: panel.property("activeTab") == 0)
        _szoveg_rakas(lanc, "PicasaPy 5150")
        assert _varj(qt_app, lambda: lanc.property("hasTextOverlay") is True), (
            "a próba feltétele: van szövegréteg"
        )
        assert _varj(qt_app, lambda: lanc.property("textOverlayVisible") is True)

        kattints(window, qt_app, _gyerek_menu(panel, "showtextcheckbox"))

        assert _varj(qt_app, lambda: lanc.property("textOverlayVisible") is False), (
            "a Show Text jelölő kattintás nem rejtette el a szövegréteget"
        )

    def test_szovegmezo_gepeles_valodi_billentyuzettel_a_piszkozatba_kerul(
        self, negyzet_app, qt_app
    ):
        window, _c, viewer, panel = nyitott_panel(negyzet_app, qt_app)
        lanc = szerkeszto(viewer)
        szovegeszkoz(window, qt_app)
        assert _varj(qt_app, lambda: panel.property("textActive") is True)
        mezo = _gyerek_menu(panel, "textContentField")
        kattints(window, qt_app, mezo)
        assert _varj(qt_app, lambda: mezo.property("activeFocus") is True), (
            "a próba feltétele: a szöveg-mező fókuszt kapott"
        )

        # a billentyűk az ablakba mennek; a fókusz a kattintással a szöveg-mezőn van
        _gepel(window, qt_app, "Hello")

        assert _varj(qt_app, lambda: lanc.property("textDraft") == "Hello"), (
            "a billentyűzet bevitele nem jutott a szöveg piszkozatába"
        )


# --- Film-párbeszéd: jelölők, tallózók, hangsáv, szöveg-dia stílus ---------------


def _film_nyit(window, qt_app):
    """A tálca film-gombjával nyitja a film-párbeszédet, a Mozgás fülön (valódi kattintással)."""
    window.setProperty("selectedIndexes", [0, 1])
    window.setProperty("selectedIndex", 0)
    qt_app.processEvents()
    kattints(window, qt_app, gyerek(window, "trayMovieButton"))
    film = gyerek(window, "movieDialog")
    assert _varj(qt_app, lambda: film.property("visible") is True), (
        "a film-gomb nem nyitotta meg a film-párbeszédet"
    )
    kattints(window, qt_app, gyerek(window, "movieTabMotion"))
    qt_app.processEvents()
    return film


def _tallozo_ablakok(window, cel_utotag: str | None = None) -> list[QObject]:
    """A fájlválasztó párbeszédek (Qt Quick FileDialog); opcionálisan a kiterjesztés szerint szűrve."""
    talalt = []
    for objektum in window.findChildren(QObject):
        if "FileDialog" not in objektum.metaObject().className():
            continue
        if cel_utotag is not None and objektum.property("defaultSuffix") != cel_utotag:
            continue
        talalt.append(objektum)
    return talalt


def _dia_stilusa(film, kulcs: str) -> bool:
    """Az első szöveg-dia stílusjelzője; a dia a QML-ben JS-tömb, ezért QJSValue-ként jön."""
    dia = film.property("movieSlides")
    return dia.property(0).property(kulcs).toBool()


class TestFilmParbeszed:
    @pytest.mark.parametrize(
        ("nev", "beallitas"),
        [
            ("movieShowCaptions", "captions"),
            ("movieCropToFit", "cropfit"),
            ("movieRemoveLowResFaces", "removeLowResFaces"),
        ],
    )
    def test_a_jelolo_valodi_kattintasra_valt_es_a_beallitast_menti(
        self, qml_app_email, qt_app, nev, beallitas
    ):
        window, vezerlo, _engine = qml_app_email
        _film_nyit(window, qt_app)
        jelolo = gyerek(window, nev)
        elotte = vezerlo.moviePreference(beallitas)
        assert jelolo.property("checked") == elotte, "a próba feltétele: a jelölő a mentett értéket mutatja"

        kattints(window, qt_app, jelolo)

        assert _varj(qt_app, lambda: jelolo.property("checked") == (not elotte)), (
            f"a(z) {nev} kattintás nem váltotta át a jelölőt"
        )
        assert _varj(qt_app, lambda: vezerlo.moviePreference(beallitas) == (not elotte)), (
            f"a(z) {nev} kattintás nem mentette a(z) {beallitas} beállítást"
        )

    def test_a_datum_jelolo_valodi_kattintasra_valt(self, qml_app_email, qt_app):
        window, _controller, _engine = qml_app_email
        _film_nyit(window, qt_app)
        jelolo = gyerek(window, "movieShowDates")
        elotte = jelolo.property("checked")

        kattints(window, qt_app, jelolo)

        assert _varj(qt_app, lambda: jelolo.property("checked") == (not elotte)), (
            "a Show Dates kattintás nem váltotta át a jelölőt"
        )

    @pytest.mark.parametrize(
        ("nev", "kulcs"),
        [("movieBoldBox", "bold"), ("movieItalicBox", "italic")],
    )
    def test_a_szoveg_stilus_jelolo_valodi_kattintasra_a_kivalasztott_diara_hat(
        self, qml_app_email, qt_app, nev, kulcs
    ):
        window, _controller, _engine = qml_app_email
        film = _film_nyit(window, qt_app)
        kattints(window, qt_app, gyerek(window, "movieTabSlide"))
        # állapot-előkészítés: egyetlen szöveg-dia, kijelölve
        film.setProperty(
            "movieSlides",
            [
                {
                    "text": "Szöveg",
                    "font": "DejaVuSans",
                    "size": 16,
                    "style": 0,
                    "bold": False,
                    "italic": False,
                    "outline": False,
                    "textColor": "#ffffff",
                    "backgroundColor": "#000000",
                }
            ],
        )
        gyerek(window, "movieSlideList").setProperty("currentIndex", 0)
        jelolo = gyerek(window, nev)
        assert _varj(qt_app, lambda: jelolo.isVisible()), "a stílus-jelölő nem látszik"

        kattints(window, qt_app, jelolo)

        assert _varj(qt_app, lambda: _dia_stilusa(film, kulcs)), (
            f"a(z) {nev} kattintás nem állította a kijelölt szöveg-dia {kulcs} stílusát"
        )

    def test_a_hangsav_torles_gomb_valodi_kattintasra_uritti_a_hangot(self, qml_app_email, qt_app):
        window, _controller, _engine = qml_app_email
        film = _film_nyit(window, qt_app)
        film.setProperty("audioFile", "/tmp/nincs-ilyen-hang.mp3")
        gomb = gyerek(window, "movieRemoveAudioButton")
        assert _varj(qt_app, lambda: gomb.isVisible()), "a Clear gomb nem látszik"

        kattints(window, qt_app, gomb)

        assert _varj(qt_app, lambda: film.property("audioFile") == ""), (
            "a Clear gomb nem ürítette ki a hangsávot"
        )

    def test_a_hangsav_tallozo_valodi_kattintasra_megnyitja_a_valasztot(
        self, qml_app_email, qt_app
    ):
        window, _controller, _engine = qml_app_email
        _film_nyit(window, qt_app)
        gomb = gyerek(window, "movieAddAudioButton")
        kattints(window, qt_app, gomb)
        valasztok = _tallozo_ablakok(window)
        try:
            assert _varj(qt_app, lambda: any(v.property("visible") is True for v in valasztok)), (
                "a Load gomb nem nyitotta meg a hangfájl-választót"
            )
        finally:
            for valaszto in valasztok:
                QMetaObject.invokeMethod(valaszto, "close", Qt.ConnectionType.DirectConnection)

    def test_a_cel_tallozo_valodi_kattintasra_megnyitja_a_mentesi_valasztot(
        self, qml_app_email, qt_app
    ):
        window, _controller, _engine = qml_app_email
        _film_nyit(window, qt_app)
        gomb = gyerek(window, "movieBrowseButton")
        kattints(window, qt_app, gomb)
        valasztok = _tallozo_ablakok(window, "mp4")
        try:
            assert _varj(qt_app, lambda: any(v.property("visible") is True for v in valasztok)), (
                "a Browse gomb nem nyitotta meg a film mentési választót"
            )
        finally:
            for valaszto in valasztok:
                QMetaObject.invokeMethod(valaszto, "close", Qt.ConnectionType.DirectConnection)


# --- E-mail választó -----------------------------------------------------------


def _email_nyit(window, qt_app, engine):
    window.show()
    window.requestActivate()
    engine.rootContext().contextProperty("emailController").setUseDefaultClient(False)
    window.setProperty("selectedIndexes", [0])
    window.setProperty("selectedIndex", 0)
    qt_app.processEvents()
    kattints(window, qt_app, gyerek(window, "trayEmailButton"))
    dialog = gyerek(window, "emailChoiceDialog")
    assert _varj(qt_app, lambda: dialog.property("opened") is True), (
        "a tálca e-mail gombja nem nyitotta meg a választót"
    )
    return dialog


class TestEmailValasztas:
    def test_a_gmail_felado_valasztoja_tiltott_es_kattintasra_nem_valt(
        self, qml_app_email, qt_app
    ):
        window, _controller, engine = qml_app_email
        _email_nyit(window, qt_app, engine)
        radio = gyerek(window, "emailChoiceGsender")
        assert radio.property("enabled") is False, "a próba feltétele: a Gmail-választó tiltott"

        kattints(window, qt_app, radio)
        qt_app.processEvents()

        assert radio.property("checked") is False, (
            "a tiltott Gmail-feladó választó kattintásra mégis bekapcsolt"
        )

    def test_a_gmail_regisztracio_linkje_valodi_kattintasra_a_levelezo_oldalt_nyitja(
        self, qml_app_email, qt_app
    ):
        window, _controller, engine = qml_app_email
        _email_nyit(window, qt_app, engine)
        link = gyerek(window, "emailChoiceSignupLink")
        fogado = _UrlFogado()
        # a külső böngésző helyett a Qt URL-kezelője fogja fel a hívást: a tesztgépen nem indul program
        QDesktopServices.setUrlHandler("http", fogado, "urlt_kapott")
        try:
            kattints(window, qt_app, link)

            assert _varj(qt_app, lambda: len(fogado.hivasok) == 1), (
                "a Gmail-regisztráció link nem kérte a levelezős oldal megnyitását"
            )
            assert "mail.google.com" in fogado.hivasok[0], (
                f"rossz cím ment a böngészőnek: {fogado.hivasok[0]}"
            )
        finally:
            QDesktopServices.unsetUrlHandler("http")

    def test_a_valtas_gomb_tiltott_es_kattintasra_nincs_hatasa(self, qml_app_email, qt_app):
        window, _controller, engine = qml_app_email
        dialog = _email_nyit(window, qt_app, engine)
        # a Change User gomb a „compose" szakaszban él: állapot-előkészítés a szakasz váltásával
        dialog.setProperty("stage", "compose")
        gomb = gyerek(window, "emailComposeChangeUserButton")
        assert _varj(qt_app, lambda: gomb.isVisible()), "a próba feltétele: a szakasz látszik"
        assert gomb.property("enabled") is False, "a próba feltétele: a Change User gomb tiltott"

        kattints(window, qt_app, gomb)
        qt_app.processEvents()

        assert dialog.property("stage") == "compose", "a tiltott gomb kattintása váltott a szakaszon"
        assert dialog.property("opened") is True, "a tiltott gomb kattintása bezárta a választót"


# --- Nyomtatás: szegély-panel rádiói -------------------------------------------


@pytest.fixture
def egyeb_app(qt_app, tmp_path):
    yield from _build_qml_app(qt_app, tmp_path, kepeket_keszit=_keszits_konyvtarat)


def _radio_kattint(window, qt_app, nev: str) -> None:
    kattints(window, qt_app, gyerek(window, nev))


def _nyomtatasi_elem(nev: str):
    """A nyomtatás-párbeszéd eleme: a párbeszéd önálló ablak, ezért minden nyitott ablakban keresünk."""
    for ablak in QGuiApplication.topLevelWindows():
        elem = ablak.findChild(QObject, nev)
        if elem is not None:
            return elem
    raise AssertionError(f"{nev} nem található a nyitott ablakokban")


class TestNyomtatasSzegelyPanel:
    @pytest.mark.parametrize(
        ("nev", "masik", "kulcs", "ertek"),
        [
            ("printOptionSource1", "printOptionSource3", "textSource", 1),
            ("printOptionSource3", "printOptionSource1", "textSource", 3),
            ("printOptionPlacement1", "printOptionPlacement2", "textPlacement", 1),
            ("printOptionPlacement2", "printOptionPlacement1", "textPlacement", 2),
        ],
    )
    def test_a_radio_valodi_kattintasra_atallitja_a_beallitast(
        self, egyeb_app, qt_app, nev, masik, kulcs, ertek
    ):
        window, controller, _engine = egyeb_app
        _elokeszit(window, qt_app, controller)
        nyomtatas = _nyomtatas_megnyit(window, qt_app, window.property("menuBar"))
        panel = _nyomtatas_panel_megnyit(window, qt_app)
        if _beallitas(panel, "options", kulcs) == ertek:
            # a próba feltétele: más érték álljon, mint amit a rádió ad
            kattints(window, qt_app, _nyomtatasi_elem(masik))
        assert _beallitas(panel, "options", kulcs) != ertek, "a próba feltétele: más érték áll"

        kattints(window, qt_app, _nyomtatasi_elem(nev))

        assert _varj(qt_app, lambda: _beallitas(panel, "options", kulcs) == ertek), (
            f"a(z) {nev} rádió kattintás nem írta át a(z) {kulcs} beállítást"
        )
        kattints(window, qt_app, _nyomtatasi_elem("printOptionsCancelButton"))
        _zar(qt_app, nyomtatas)
