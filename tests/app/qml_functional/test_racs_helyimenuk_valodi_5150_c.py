"""A rács helyi menüi VALÓDI kattintással (#5150, 6. rész, 3. fájl).

Lefedve: a fotó-menü (PhotoContextMenu) B-listás tételei, a címke-menü
(TagContextMenu) három tétele, és a néző menüjének (ViewerContextMenu) Undo All
Edits tétele. A fotó-menü a bélyegképen (`thumbMouseArea`)
jobbkattintással nyílik; a menü `popupType: Popup.Window`, tehát külön
ablakban él, a kattintást annak az ablakának küldjük.

A külső programot (`QDesktopServices.openUrl`) helyettesítjük; a vágólapot a
teszt méri. A párbeszédeket megnyitva ellenőrizzük, és a takarításban `close`-zal
zárjuk. Az Undo All Edits tétel (fotó- és nézőmenü) megerősítést kér, és a
megerősítés után visszavonja a szerkesztéseket (#5163).
"""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import Q_ARG, QMetaObject, QObject, QPointF, Qt, QUrl
from PySide6.QtGui import QGuiApplication

from picasapy.metadata.iptc_writer import write_iptc_keywords
from support.qt_wait import wait_for_photo_op
from tests.app.qml_functional._mappa_kep_menu_5150_helpers import (
    KEPEK,
    MAPPA,
    app_epitese,
    keszits_konyvtarat,
    nyitott,
    szures,
    tetel_kattintasa,
)
from tests.app.qml_functional._racs_helyimenuk_5150_helpers import (
    album_darab,
    almenu_megnyitasa,
    egyezik,
    elokeszit_str,
    fileops_athelyezo,
    foto_utja,
    gyerek,
    ini_ertek,
    jobbklikk_fotón,
    keres_vizualis,
    keres_vizualis_mindenablakban,
    kattints,
    kijelol,
    mentett_eredetik,
    varj,
    vizualis_bejaras,
    zar,
)


@pytest.fixture
def mappa_app(qt_app, tmp_path):
    yield from app_epitese(qt_app, tmp_path)


def _keszits_cimkevel(lib: Path) -> None:
    """A fotós mappa, benne egy `kirandulas` kulcsszavas JPEG (a kulcsszó az IPTC-ben él)."""
    keszits_konyvtarat(lib)
    write_iptc_keywords(lib / MAPPA / "a_nagy.jpg", ("kirandulas",))


def _sor_a_nezetben(window, sor) -> bool:
    """A címkesor egészben a főablakon belül van.

    A Címkék-panel a jobb fiókban él, a fiók pedig 400 ms alatt nyílik. Nyitás
    közben a sor a fiók aktuális szélességéhez igazodik, és kieshet az ablak
    széléről: a kattintás ilyenkor nem a sorra megy."""
    bal = sor.mapToScene(QPointF(0, 0)).x()
    return bal >= 0 and bal + sor.width() <= window.width()


def _cimke_szovege(sor, cimke: str):
    """A címke neve a sorban: a kattintás ide menjen, ne a ✕ gombra (az a sor jobb szélén ül)."""
    for item in vizualis_bejaras(sor):
        if item.property("text") == cimke:
            return item
    raise AssertionError(f"a(z) {cimke} felirat nem található a sorban")


def _undo_megerositese(window, qt_app, controller) -> None:
    """Az Undo All Edits megerősítője: megnyílik, majd a valódi „Igen” kattintás viszi végbe."""
    assert varj(
        qt_app, lambda: nyitott(window.findChild(QObject, "undoAllEditsDialog"))
    ), "az Undo All Edits nem kért megerősítést"
    igen = keres_vizualis_mindenablakban(window, "undoAllEditsYesButton")
    assert igen is not None, "a megerősítő Igen gombja nem látszik"
    wait_for_photo_op(controller, lambda: kattints(window, qt_app, igen), qt_app=qt_app)


def _nezo_menu_nyit(window, qt_app) -> None:
    """Megnyitja a néző helyi menüjét a jobbklikk útján (`openContextMenu`), az első képen."""
    window.setProperty("viewerOpen", True)
    viewer = gyerek(window, "photoViewer")
    viewer.setProperty("currentIndex", 0)
    qt_app.processEvents()
    QMetaObject.invokeMethod(
        viewer, "openContextMenu", Qt.ConnectionType.DirectConnection,
        Q_ARG("QVariant", 5), Q_ARG("QVariant", 5),
    )
    qt_app.processEvents()


class _FakeDesktopServices:
    """Helyettesítő: a társított alkalmazást nem indítjuk el, a kérést rögzítjük."""

    hivasok: list[Path] = []

    @classmethod
    def openUrl(cls, url: QUrl) -> bool:  # noqa: N802 - a Qt-API neve
        cls.hivasok.append(Path(url.toLocalFile()))
        return True


class TestFotoMenu:
    def test_az_albumhoz_adas_valodi_kattintassal_hozzaadja_a_kepet(
        self, mappa_app, qt_app
    ):
        window, controller, _motor = mappa_app
        elokeszit_str(window, qt_app, controller)
        token = controller.createAlbum("Masik", [1])
        assert token, "az album nem jött létre"
        assert varj(qt_app, lambda: album_darab(controller, token) == 1)
        kijelol(window, qt_app, [0])
        elotte = album_darab(controller, token)

        menu = jobbklikk_fotón(window, qt_app, 0)
        almenu_megnyitasa(window, qt_app, menu, "contextMenuAddToAlbum")
        tetel = keres_vizualis_mindenablakban(
            window, f"contextMenuAddToAlbumItem_{token}"
        )
        assert tetel is not None, "az album tétele nem jelent meg az Add to Album almenüben"
        kattints(window, qt_app, tetel)

        assert varj(qt_app, lambda: album_darab(controller, token) == elotte + 1), (
            "az Add to Album kattintás nem adta hozzá a képet az albumhoz"
        )

    def test_az_albumbol_eltavolitas_valodi_kattintassal_megerositest_ker(
        self, mappa_app, qt_app
    ):
        window, controller, _motor = mappa_app
        elokeszit_str(window, qt_app, controller)
        token = controller.createAlbum("Masik", [1])
        assert varj(qt_app, lambda: keres_vizualis(window, f"albumItem_{token}") is not None)

        kattints(window, qt_app, keres_vizualis(window, f"albumItem_{token}"))
        assert varj(qt_app, lambda: controller.currentAlbumToken == token), (
            "az album sorára kattintás nem nyitotta meg az albumot"
        )

        jobbklikk_fotón(window, qt_app, 0)
        kattints(window, qt_app, gyerek(window, "contextMenuRemoveFromAlbum"))

        dialog = gyerek(window, "removeFromAlbumDialog")
        assert varj(qt_app, lambda: nyitott(dialog)), (
            "a Remove from album kattintás nem kért megerősítést"
        )
        zar(qt_app, dialog)

    def test_a_forgatas_balra_valodi_kattintassal_forgatast_ment(
        self, mappa_app, qt_app
    ):
        window, controller, _motor = mappa_app
        elokeszit_str(window, qt_app, controller)
        kijelol(window, qt_app, [0])
        assert ini_ertek(controller, 0, "rotate") is None

        jobbklikk_fotón(window, qt_app, 0)
        kattints(window, qt_app, gyerek(window, "contextMenuRotateLeft"))

        # a bal forgatás 3 lépés (-1 mod 4), a `rotate=` kulcs a szakaszban él
        assert varj(qt_app, lambda: ini_ertek(controller, 0, "rotate") == "rotate(3)"), (
            "a Rotate Left kattintás nem mentett bal forgatást a .picasa.ini-be"
        )

    def test_a_szerkesztesek_visszavonasa_valodi_kattintassal_torli_az_effekteket(
        self, mappa_app, qt_app
    ):
        window, controller, _motor = mappa_app
        elokeszit_str(window, qt_app, controller)
        kijelol(window, qt_app, [0])
        wait_for_photo_op(
            controller, lambda: controller.applyEffectMany([0], "sepia"), qt_app=qt_app
        )
        assert varj(qt_app, lambda: "sepia=1;" in szures(controller, 0))

        jobbklikk_fotón(window, qt_app, 0)
        kattints(window, qt_app, gyerek(window, "contextMenuUndoAllEdits"))
        _undo_megerositese(window, qt_app, controller)

        assert varj(qt_app, lambda: "sepia=1;" not in szures(controller, 0)), (
            "az Undo All Edits megerősítése nem törölte a szerkesztéseket"
        )

    def test_a_rejtes_valodi_kattintassal_elrejti_a_kepet(self, mappa_app, qt_app):
        window, controller, _motor = mappa_app
        elokeszit_str(window, qt_app, controller)
        kijelol(window, qt_app, [0])
        nev = controller.photos.photos[0].name
        darab = len(controller.photos.photos)

        jobbklikk_fotón(window, qt_app, 0)
        kattints(window, qt_app, gyerek(window, "contextMenuHide"))

        # a rejtett kép kikerül a látható rácsról (a jelölés az indexben van)
        assert varj(
            qt_app,
            lambda: len(controller.photos.photos) == darab - 1
            and nev not in [foto.name for foto in controller.photos.photos],
        ), "a Hide kattintás nem rejtette el a képet a rácsról"

    def test_az_athelyezes_valodi_kattintassal_megnyitja_a_mappavalasztot(
        self, mappa_app, qt_app
    ):
        window, controller, _motor = mappa_app
        elokeszit_str(window, qt_app, controller)
        kijelol(window, qt_app, [0])

        jobbklikk_fotón(window, qt_app, 0)
        kattints(window, qt_app, gyerek(window, "contextMenuMove"))

        dialog = fileops_athelyezo(window)
        assert dialog is not None, "a fájl-áthelyező párbeszéd nem jött létre"
        assert varj(qt_app, lambda: nyitott(dialog)), (
            "a Move kattintás nem nyitotta meg az áthelyező párbeszédet"
        )
        zar(qt_app, dialog)

    def test_a_torles_valodi_kattintassal_megerositest_ker(self, mappa_app, qt_app):
        window, controller, _motor = mappa_app
        elokeszit_str(window, qt_app, controller)
        kijelol(window, qt_app, [0])

        jobbklikk_fotón(window, qt_app, 0)
        kattints(window, qt_app, gyerek(window, "contextMenuDelete"))

        dialog = gyerek(window, "deleteConfirmDialog")
        assert varj(qt_app, lambda: nyitott(dialog)), (
            "a Delete kattintás nem kért megerősítést"
        )
        zar(qt_app, dialog)
        assert len(controller.photos.photos) == len(KEPEK), (
            "a megerősítés nélkül törlődött a kép"
        )

    def test_a_fajl_megnyitasa_valodi_kattintassal_a_tarsitott_programot_hivja(
        self, mappa_app, qt_app, monkeypatch
    ):
        """Helyettesítő: a társított alkalmazás nem indul; a kérést rögzítjük."""
        import picasapy.app.fileops_controller as fileops_module

        window, controller, _motor = mappa_app
        elokeszit_str(window, qt_app, controller)
        kijelol(window, qt_app, [0])
        _FakeDesktopServices.hivasok = []
        monkeypatch.setattr(fileops_module, "QDesktopServices", _FakeDesktopServices)

        jobbklikk_fotón(window, qt_app, 0)
        kattints(window, qt_app, gyerek(window, "contextMenuOpenFile"))

        cel = foto_utja(controller, 0)
        assert varj(qt_app, lambda: any(
            egyezik(h, cel) for h in _FakeDesktopServices.hivasok
        )), f"a Open File kattintás nem a képet adta át: {_FakeDesktopServices.hivasok}"

    def test_a_visszaallitas_valodi_kattintassal_megerositest_ker(
        self, mappa_app, qt_app
    ):
        window, controller, _motor = mappa_app
        mentett_eredetik(controller)
        elokeszit_str(window, qt_app, controller)
        kijelol(window, qt_app, [0])
        wait_for_photo_op(
            controller, lambda: controller.applyEffectMany([0], "sepia"), qt_app=qt_app
        )
        assert varj(qt_app, lambda: controller.hasSavedBackup([0]))

        jobbklikk_fotón(window, qt_app, 0)
        kattints(window, qt_app, gyerek(window, "contextMenuRevert"))

        dialog = gyerek(window, "revertConfirmDialog")
        assert varj(qt_app, lambda: nyitott(dialog)), (
            "a Revert kattintás nem kért megerősítést"
        )
        zar(qt_app, dialog)

    def test_a_teljes_eleresi_ut_masolasa_valodi_kattintassal_a_vagolapra_kerul(
        self, mappa_app, qt_app
    ):
        window, controller, _motor = mappa_app
        elokeszit_str(window, qt_app, controller)
        kijelol(window, qt_app, [0])
        QGuiApplication.clipboard().setText("")

        jobbklikk_fotón(window, qt_app, 0)
        kattints(window, qt_app, gyerek(window, "contextMenuCopyFullPath"))

        cel = foto_utja(controller, 0)
        assert varj(qt_app, lambda: egyezik(
            QGuiApplication.clipboard().text(), cel
        )), "a Copy Full Path kattintás nem másolta a teljes útvonalat"

    def test_a_tulajdonsagok_valodi_kattintassal_megnyitja_a_tulajdonsag_fület(
        self, mappa_app, qt_app
    ):
        window, controller, _motor = mappa_app
        elokeszit_str(window, qt_app, controller)
        kijelol(window, qt_app, [0])

        jobbklikk_fotón(window, qt_app, 0)
        kattints(window, qt_app, gyerek(window, "contextMenuProperties"))

        assert varj(qt_app, lambda: window.property("activeDrawerTab") == "properties"), (
            "a Properties kattintás nem nyitotta meg a tulajdonságok fület"
        )

    @pytest.mark.parametrize("nev", ["contextMenuUploadToWebAlbums", "contextMenuBlockUpload"])
    def test_a_megszunt_szolgaltatas_tetele_valodi_kattintasra_nem_csinal_semmit(
        self, mappa_app, qt_app, nev
    ):
        window, controller, _motor = mappa_app
        elokeszit_str(window, qt_app, controller)
        kijelol(window, qt_app, [0])
        elotte = [foto.name for foto in controller.photos.photos]

        jobbklikk_fotón(window, qt_app, 0)
        tetel = gyerek(window, nev)
        assert tetel.property("enabled") is False, f"{nev}: a megszűnt tétel nincs letiltva"
        kattints(window, qt_app, tetel)

        assert [foto.name for foto in controller.photos.photos] == elotte


class TestCimkeMenu:
    @pytest.fixture
    def cimke_app(self, qt_app, tmp_path):
        yield from app_epitese(qt_app, tmp_path, kepeket_keszit=_keszits_cimkevel)

    def _cimke_panel(self, window, qt_app) -> None:
        """Valódi kattintással megnyitja a Nézet ▸ Címkék panelt."""
        tetel_kattintasa(window, qt_app, "&View", "menuViewTags")
        assert varj(
            qt_app, lambda: keres_vizualis(window, "tagRemove-kirandulas") is not None
        ), "a Nézet ▸ Címkék kattintás nem nyitotta meg a címkepanelt"

    def _cimke_menu(self, window, qt_app):
        """Valódi jobbklikk a `kirandulas` címkesor szövegén; a menü megnyílását is megvárjuk."""
        sor = keres_vizualis(window, "tagRemove-kirandulas")
        while sor is not None and sor.property("modelData") != "kirandulas":
            sor = sor.parentItem()
        assert sor is not None, "a kirandulas címkesor nem található"
        assert varj(qt_app, lambda: _sor_a_nezetben(window, sor)), (
            "a kirandulas címkesor nem került a főablak látható részére"
        )
        kattints(window, qt_app, _cimke_szovege(sor, "kirandulas"), Qt.MouseButton.RightButton)
        menu = gyerek(window, "tagContextMenu")
        assert varj(qt_app, lambda: menu.property("visible") is True), (
            "a címkesor jobbklikkje nem nyitotta meg a címke-menüt"
        )
        return menu

    def test_a_rateteles_a_kijelolesre_valodi_kattintassal(self, cimke_app, qt_app):
        window, controller, _motor = cimke_app
        elokeszit_str(window, qt_app, controller)
        # a 0. képen megvan a címke, a 1. képen nincs: a panel a kijelölésből épül
        kijelol(window, qt_app, [0, 1])
        self._cimke_panel(window, qt_app)
        self._cimke_menu(window, qt_app)

        kattints(window, qt_app, gyerek(window, "tagMenuAddToSelection"))

        assert varj(qt_app, lambda: "kirandulas" in controller.keywordsOfRows([1])), (
            "az Add this tag to entire selection kattintás nem tette rá a címkét a kijelölésre"
        )

    def test_a_cimke_keresese_valodi_kattintassal_a_cimkere_keres(
        self, cimke_app, qt_app
    ):
        window, controller, _motor = cimke_app
        elokeszit_str(window, qt_app, controller)
        self._cimke_panel(window, qt_app)
        self._cimke_menu(window, qt_app)

        kattints(window, qt_app, gyerek(window, "tagMenuFindTagged"))

        assert varj(qt_app, lambda: controller.searchQuery == "kirandulas"), (
            "a Find Items Tagged This Way kattintás nem a címkére keresett"
        )

    def test_a_cimke_eltavolitasa_valodi_kattintassal_leveszi_a_cimket(
        self, cimke_app, qt_app
    ):
        window, controller, _motor = cimke_app
        elokeszit_str(window, qt_app, controller)
        kijelol(window, qt_app, [0])
        self._cimke_panel(window, qt_app)
        self._cimke_menu(window, qt_app)

        kattints(window, qt_app, gyerek(window, "tagMenuRemove"))

        assert varj(qt_app, lambda: "kirandulas" not in controller.keywordsOfRows([0])), (
            "a Remove Tag kattintás nem vette le a címkét a kijelölésről"
        )


class TestNezoMenu:
    def test_a_nezo_undo_all_edits_valodi_kattintassal_megerositest_ker_es_torli(
        self, mappa_app, qt_app
    ):
        window, controller, _motor = mappa_app
        elokeszit_str(window, qt_app, controller)
        kijelol(window, qt_app, [0])
        wait_for_photo_op(
            controller, lambda: controller.applyEffectMany([0], "sepia"), qt_app=qt_app
        )
        assert varj(qt_app, lambda: "sepia=1;" in szures(controller, 0))

        _nezo_menu_nyit(window, qt_app)
        tetel = gyerek(window, "viewerMenuUndoAllEdits")
        assert varj(qt_app, lambda: tetel.property("enabled") is True), (
            "a néző menüjének Undo All Edits tétele szürke maradt"
        )
        kattints(window, qt_app, tetel)
        _undo_megerositese(window, qt_app, controller)

        assert varj(qt_app, lambda: "sepia=1;" not in szures(controller, 0)), (
            "a néző Undo All Edits megerősítése nem törölte a szerkesztéseket"
        )
