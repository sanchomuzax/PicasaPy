"""A néző (egyképes nézet) helyi menüjének tételei VALÓDI kattintással (#5150, 7. rész).

Lefedve: a `ViewerContextMenu.qml` B-listás tételei (a jegy „Néző” csoportja).
A nézőt valódi jobbklikkel nyitjuk (a néző `TapHandler`-je), a tételre valódi
`QTest.mouseClick`-kel kattintunk. Parancsot közvetlenül nem indítunk: nincs
`triggered`/`clicked`/`activated` hívás és nincs `.emit()`.

A hatást a vezérlő állapotán, a lemezen maradt `.picasa.ini`-n, a vágólapon
vagy a párbeszédek láthatóságán mérjük. A külső programot (társított
alkalmazás, fájlkezelő) helyettesítjük, ezt a teszt mindig kimondja.

Már lefedett tételek (nem ismételjük):
- `viewerMenuUndoAllEdits`, `viewerMenuLocateOriginal`, `viewerMenuLocateMenuItem`
  - `test_racs_helyimenuk_valodi_5150_c.py` (TestNezoMenu),
    `test_viewer_original_locate_4462.py`;
- `viewerMenuLocateFile` - `test_nezo_szerkeszto_valodi_5135.py`.

A szöveges tételek billentyűs/menüsoros párját a `test_viewer_context_menu.py`
már szerkezetileg fedi; ez a fájl a KATTINTÁS hatását méri.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import Qt
from PySide6.QtGui import QGuiApplication

import picasapy.app.fileops_controller as fileops_module
from support.qt_wait import wait_for_photo_op
from tests.app.qml_functional._mappa_kep_menu_5150_helpers import (
    app_epitese,
    nyitott,
    szures,
)
from tests.app.qml_functional._racs_helyimenuk_5150_helpers import (
    album_darab,
    almenu_megnyitasa,
    egyezik,
    elokeszit_str,
    foto_utja,
    gyerek,
    ini_ertek,
    keres_vizualis_mindenablakban,
    kattints,
    kijelol,
    mentett_eredetik,
    varj,
    zar,
)


@pytest.fixture
def mappa_app(qt_app, tmp_path):
    yield from app_epitese(qt_app, tmp_path)


def _nezo_nyit(window, qt_app, sor: int = 0) -> None:
    """A néző megnyitása a `sor` képre (a megnyitás maga nem a tesztelt tétel)."""
    window.setProperty("viewerOpen", True)
    gyerek(window, "photoViewer").setProperty("currentIndex", sor)
    qt_app.processEvents()


def _nezo_jobbklikk(window, qt_app):
    """Valódi jobbklikk a néző közepén: a néző TapHandler-je nyitja a helyi menüt."""
    kattints(window, qt_app, gyerek(window, "photoViewer"), Qt.MouseButton.RightButton)
    menu = gyerek(window, "viewerContextMenu")
    assert varj(qt_app, lambda: menu.property("opened") is True), (
        "a néző közepén végzett valódi jobbklikk nem nyitotta meg a helyi menüt"
    )
    return menu


def _tetel(window, qt_app, nev: str) -> None:
    """Valódi kattintás a helyi menü `nev` tételén."""
    kattints(window, qt_app, gyerek(window, nev))


def _megnyitas_rogzitese(monkeypatch) -> list[Path]:
    """Helyettesítő: a társított alkalmazás nem indul, a kért fájlt rögzítjük."""
    hivasok: list[Path] = []

    class _Fake:
        @staticmethod
        def openUrl(url) -> bool:  # noqa: N802 - a Qt-API neve
            hivasok.append(Path(url.toLocalFile()))
            return True

    monkeypatch.setattr(fileops_module, "QDesktopServices", _Fake)
    return hivasok


def _megmutatas_rogzitese(monkeypatch) -> list[Path]:
    """Helyettesítő: a fájlkezelő-indítás (`reveal_in_file_manager`) ki van váltva."""
    megmutatott: list[Path] = []
    monkeypatch.setattr(fileops_module, "reveal_in_file_manager", megmutatott.append)
    return megmutatott


def _szepia_a_nulladik_kepre(window, qt_app, controller) -> None:
    elokeszit_str(window, qt_app, controller)
    kijelol(window, qt_app, [0])
    wait_for_photo_op(
        controller, lambda: controller.applyEffectMany([0], "sepia"), qt_app=qt_app
    )
    assert varj(qt_app, lambda: "sepia=1;" in szures(controller, 0))


class TestNezoHelyiMenuTetelei:
    def test_vissza_a_konyvtarhoz_valodi_kattintassal_zarja_a_nezot(
        self, mappa_app, qt_app
    ):
        window, controller, _motor = mappa_app
        elokeszit_str(window, qt_app, controller)
        _nezo_nyit(window, qt_app)
        _nezo_jobbklikk(window, qt_app)

        _tetel(window, qt_app, "viewerMenuBackToLibrary")

        assert varj(qt_app, lambda: window.property("viewerOpen") is False), (
            "a Back to Library kattintás nem zárta be a nézőt"
        )

    def test_az_albumhoz_adas_valodi_kattintassal_hozzaadja_a_nezett_kepet(
        self, mappa_app, qt_app
    ):
        window, controller, _motor = mappa_app
        elokeszit_str(window, qt_app, controller)
        token = controller.createAlbum("Masik", [1])
        assert token, "az album nem jött létre"
        assert varj(qt_app, lambda: album_darab(controller, token) == 1)
        _nezo_nyit(window, qt_app)
        menu = _nezo_jobbklikk(window, qt_app)
        elotte = album_darab(controller, token)

        almenu_megnyitasa(window, qt_app, menu, "viewerMenuAddToAlbum")
        tetel = keres_vizualis_mindenablakban(
            window, f"viewerMenuAddToAlbumItem_{token}"
        )
        assert tetel is not None, "az album tétele nem jelent meg az Add to Album almenüben"
        kattints(window, qt_app, tetel)

        assert varj(qt_app, lambda: album_darab(controller, token) == elotte + 1), (
            "az Add to Album kattintás nem adta hozzá a nézett képet az albumhoz"
        )

    @pytest.mark.parametrize(
        ("nev", "elvart"),
        [("viewerMenuRotateRight", "rotate(1)"), ("viewerMenuRotateLeft", "rotate(3)")],
    )
    def test_a_forgatas_valodi_kattintassal_elmenti_az_iranyt(
        self, mappa_app, qt_app, nev, elvart
    ):
        window, controller, _motor = mappa_app
        elokeszit_str(window, qt_app, controller)
        _nezo_nyit(window, qt_app)
        assert ini_ertek(controller, 0, "rotate") is None, "a próba feltétele: nincs forgatás"
        _nezo_jobbklikk(window, qt_app)

        _tetel(window, qt_app, nev)

        assert varj(qt_app, lambda: ini_ertek(controller, 0, "rotate") == elvart), (
            f"a(z) {nev} kattintás nem mentette a forgatást ({elvart})"
        )

    def test_a_rejtes_valodi_kattintassal_elrejti_a_nezett_kepet(self, mappa_app, qt_app):
        window, controller, _motor = mappa_app
        elokeszit_str(window, qt_app, controller)
        _nezo_nyit(window, qt_app)
        nev = controller.photos.photos[0].name
        darab = len(controller.photos.photos)
        _nezo_jobbklikk(window, qt_app)

        _tetel(window, qt_app, "viewerMenuHide")

        assert varj(
            qt_app,
            lambda: len(controller.photos.photos) == darab - 1
            and nev not in [foto.name for foto in controller.photos.photos],
        ), "a Hide kattintás nem rejtette el a nézett képet"

    def test_a_megnyitas_valodi_kattintassal_a_tarsitott_programot_hivja(
        self, mappa_app, qt_app, monkeypatch
    ):
        """Helyettesítő: a társított alkalmazás nem indul; a kérést rögzítjük."""
        window, controller, _motor = mappa_app
        hivasok = _megnyitas_rogzitese(monkeypatch)
        elokeszit_str(window, qt_app, controller)
        kijelol(window, qt_app, [0])
        _nezo_nyit(window, qt_app)
        _nezo_jobbklikk(window, qt_app)

        _tetel(window, qt_app, "viewerMenuOpenFile")

        cel = foto_utja(controller, 0)
        assert varj(qt_app, lambda: any(egyezik(h, cel) for h in hivasok)), (
            f"a Open File kattintás nem a nézett képet adta át: {hivasok}"
        )

    def test_a_tarsitas_helyfoglalo_tetele_valodi_kattintasra_nincs_hatassal(
        self, mappa_app, qt_app
    ):
        """`Open With` = helyfoglaló (`placeholder`): nincs mögötte kezelő, a
        társított alkalmazások listája még nincs meg. A tétel szürke, és a
        kattintása nem zárja be a nézőt."""
        window, controller, _motor = mappa_app
        elokeszit_str(window, qt_app, controller)
        _nezo_nyit(window, qt_app)
        _nezo_jobbklikk(window, qt_app)

        assert gyerek(window, "viewerMenuOpenWith").property("enabled") is False, (
            "a helyfoglaló Open With tétel nem szürke"
        )
        _tetel(window, qt_app, "viewerMenuOpenWith")
        qt_app.processEvents()

        assert window.property("viewerOpen") is True, (
            "a helyfoglaló tétel kattintása bezárta a nézőt"
        )

    def test_a_mentes_valodi_kattintassal_a_mentes_megerositeset_nyitja(
        self, mappa_app, qt_app
    ):
        window, controller, _motor = mappa_app
        _szepia_a_nulladik_kepre(window, qt_app, controller)
        _nezo_nyit(window, qt_app)
        _nezo_jobbklikk(window, qt_app)
        assert varj(
            qt_app, lambda: gyerek(window, "viewerMenuSave").property("enabled") is True
        ), "a Save tétel szürke maradt a szerkesztett képen"

        _tetel(window, qt_app, "viewerMenuSave")

        dialog = gyerek(window, "saveConfirmDialog")
        assert varj(qt_app, lambda: nyitott(dialog)), (
            "a Save kattintás nem nyitotta meg a mentés megerősítését"
        )
        zar(qt_app, dialog)

    def test_a_visszaallitas_valodi_kattintassal_megerositest_ker(
        self, mappa_app, qt_app
    ):
        window, controller, _motor = mappa_app
        mentett_eredetik(controller)
        _szepia_a_nulladik_kepre(window, qt_app, controller)
        assert varj(qt_app, lambda: controller.hasSavedBackup([0]))
        _nezo_nyit(window, qt_app)
        _nezo_jobbklikk(window, qt_app)
        assert varj(
            qt_app, lambda: gyerek(window, "viewerMenuRevert").property("enabled") is True
        ), "a Revert tétel szürke maradt, pedig van mentett eredeti"

        _tetel(window, qt_app, "viewerMenuRevert")

        dialog = gyerek(window, "revertConfirmDialog")
        assert varj(qt_app, lambda: nyitott(dialog)), (
            "a Revert kattintás nem kért megerősítést"
        )
        zar(qt_app, dialog)

    def test_a_lemezen_valodi_kattintassal_a_fajlkezelobe_vezet(
        self, mappa_app, qt_app, monkeypatch
    ):
        """Helyettesítő: a fájlkezelő-indítás (`reveal_in_file_manager`) ki van váltva."""
        window, controller, _motor = mappa_app
        elokeszit_str(window, qt_app, controller)
        kijelol(window, qt_app, [0])
        _nezo_nyit(window, qt_app)
        megmutatott = _megmutatas_rogzitese(monkeypatch)
        _nezo_jobbklikk(window, qt_app)

        _tetel(window, qt_app, "viewerMenuLocate")

        assert varj(qt_app, lambda: len(megmutatott) == 1), (
            "a Locate on Disk kattintás nem a fájlkezelő-indítást hívta"
        )
        assert egyezik(megmutatott[0], foto_utja(controller, 0))

    def test_az_eleresi_ut_masolasa_valodi_kattintassal_a_vagolapra_kerul(
        self, mappa_app, qt_app
    ):
        window, controller, _motor = mappa_app
        elokeszit_str(window, qt_app, controller)
        kijelol(window, qt_app, [0])
        _nezo_nyit(window, qt_app)
        QGuiApplication.clipboard().setText("")
        _nezo_jobbklikk(window, qt_app)

        _tetel(window, qt_app, "viewerMenuCopyFullPath")

        cel = foto_utja(controller, 0)
        assert varj(qt_app, lambda: egyezik(
            QGuiApplication.clipboard().text(), cel
        )), "a Copy Full Path kattintás nem másolta a teljes útvonalat"

    @pytest.mark.parametrize("nev", ["viewerMenuQuickUpload", "viewerMenuBlockUpload"])
    def test_a_megszunt_szolgaltatas_tetele_szurke_es_kattintasra_nincs_hatasa(
        self, mappa_app, qt_app, nev
    ):
        """`retired`: a Webalbumok megszűnt; a tétel marad, de nem aktív."""
        window, controller, _motor = mappa_app
        elokeszit_str(window, qt_app, controller)
        _nezo_nyit(window, qt_app)
        _nezo_jobbklikk(window, qt_app)
        assert gyerek(window, nev).property("enabled") is False, (
            f"{nev}: a megszűnt tétel nincs letiltva"
        )

        _tetel(window, qt_app, nev)
        qt_app.processEvents()

        assert window.property("viewerOpen") is True, f"{nev} kattintása bezárta a nézőt"

    def test_az_arcok_visszaallitasa_valodi_kattintassal_a_nezett_kepre_hat(
        self, mappa_app, qt_app, monkeypatch
    ):
        """Helyettesítő: nincs valódi arcmodell; a `resetFacesForPhotos` hívását rögzítjük.

        A `Main.qml` a nézett kép útvonalát adja át; a rögzítés ezt méri."""
        window, controller, _motor = mappa_app
        elokeszit_str(window, qt_app, controller)
        kijelol(window, qt_app, [0])
        arcok = window.property("_faceScanController")
        assert arcok is not None, "az arcfelismerő vezérlő hiányzik a főablakból"
        hivasok: list[list[str]] = []

        def _rogzit(utak):
            hivasok.append(list(utak))
            return 0

        monkeypatch.setattr(type(arcok), "resetFacesForPhotos", lambda _s, utak: _rogzit(utak))
        _nezo_nyit(window, qt_app)
        _nezo_jobbklikk(window, qt_app)

        _tetel(window, qt_app, "viewerMenuResetFaces")

        cel = foto_utja(controller, 0)
        assert varj(qt_app, lambda: any(
            len(utak) == 1 and egyezik(utak[0], cel) for utak in hivasok
        )), f"a Reset Faces kattintás nem a nézett képet adta át: {hivasok}"

    def test_a_tulajdonsagok_valodi_kattintassal_megnyitja_a_tulajdonsag_fület(
        self, mappa_app, qt_app
    ):
        window, controller, _motor = mappa_app
        elokeszit_str(window, qt_app, controller)
        kijelol(window, qt_app, [0])
        _nezo_nyit(window, qt_app)
        _nezo_jobbklikk(window, qt_app)

        _tetel(window, qt_app, "viewerMenuProperties")

        assert varj(qt_app, lambda: window.property("activeDrawerTab") == "properties"), (
            "a Properties kattintás nem nyitotta meg a tulajdonságok fület"
        )
