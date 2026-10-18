"""A Rács maradék vezérlői VALÓDI bemenettel (#5150, Rács-maradék, P. fájl).

Lefedve (az audit „Rács" csoportjából):
- Mappa-menü: Delete Folder (megerősítés után a lomtárba), Export as HTML.
- Mappalista és rács üres része: jobbklikk nyitja a menüt; a mappasor
  balklikkje kiválasztja a mappát; a lasszó húzással jelöl.
- Fejléc és mappa-tulajdonságok: a Sync to Web kapcsoló letiltott; a naptár-gomb
  megnyitja a naptárat; a zene-útvonal valódi bevitellel mentődik; a helyszín-mező
  mappa módban zárt.
- Mentés-sor: a mentetlen mappa pipája a sor kattintására kapcsol.
- Fotó-menü: View and Edit, Rotate Clockwise, Locate on Disk, Save,
  Add to Album, Add to People Album, Locate in Picasa, és a Locate almenü.
- Gyorscímke-beállítás: a mező és a két jelölő.
- Emberek kezelője: a keresőmező szűr; a három letiltott vezérlő nem vált.
- Név nélküliek: a mellőzött arc visszavonása; az arc névmezője Enterre nevet küld.

Nincs rajta teszt, mert a terméken nem érhető el valódi kattintással (jelentve):
- `ignoreFacesDontAskCheck`: a megerősítő párbeszéd jelölője; a
  `test_unnamed_faces_view.py` (TestDontAskAgain) valódi egérkattintással fedi.
  (A `unnamedNameField` és az `ignoreFacesButton` a kibontott nézetben látszik,
  és a `test_nev_nelkuliek_kibontott_5214.py` fedi; az `addNameButton` megszűnt.)
- `moreSuggestionsButton`: ugyanaz a sor; a `test_racs_vezerlok_valodi_5135_c`
  szerint a #5183 óta szándékosan nincs ebben az albumban.
- `unnamedWelcomeLearnMoreButton`: nincs kattintáskezelője.

A rontás-kontrollt futás közben végeztük: a teszt indulása után a vezérlőt
letiltottuk (a letiltott jelölőt, kapcsolót vagy gombot engedélyeztük), és a
célzott teszt pirosra vált. A két Emberek-gomb (`peopleManagerOnlineButton`,
`peopleManagerRefreshButton`) kattintáskezelő nélküli, ezért az engedélyezésük
sem változtat semmit, a tesztjük csak a „nem történik semmi"-t méri.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import QPointF, Qt
from PySide6.QtQuick import QQuickItem
from PySide6.QtTest import QTest

import picasapy.app.fileops_controller as fileops_module
from picasapy.edit.save import ORIGINALS_DIR_NAME
from picasapy.index import open_index, sync_tree
from picasapy.ini import load_document, load_or_empty, parse_faces, read_folder_music
from picasapy.scanner import PICASA_INI_NAME
from support.qt_wait import wait_for_photo_op
from test_unnamed_faces_view import _host_in_window, _make_view, _StubFaceScanController
from tests.app.qml_functional._mappa_kep_menu_5150_helpers import (
    MAPPA,
    MASIK,
    app_epitese,
    keszits_ket_mappat,
    nyitott,
    szures,
    zar,
)
from tests.app.qml_functional._racs_helyimenuk_5150_helpers import (
    album_darab,
    almenu_megnyitasa,
    elokeszit_str,
    foto_utja,
    kattints,
    ini_ertek,
    jobbklikk_fotón,
    jobbklikk_mappan,
    kijelol,
    kijelolt,
    mentett_eredetik,
    varj,
)
from tests.app.qml_functional._menusor_maradek_5150_helpers import tetel_kattintasa
from tests.app.qml_functional._racs_maradek_5150_helpers import (
    jobbklikk_a_ponton,
    keres_latszo,
    varj_helyen_all,
    kattint,
    keres,
    kep_cellaja,
    sor_pontja,
    ures_pont_a_folyamon,
    utvonal,
)


@pytest.fixture
def mappa_app(qt_app, tmp_path):
    yield from app_epitese(qt_app, tmp_path)


@pytest.fixture
def ket_mappa_app(qt_app, tmp_path):
    yield from app_epitese(qt_app, tmp_path, kepeket_keszit=keszits_ket_mappat)


def _huzas(window, qt_app, kezdet: QPointF, veg: QPointF) -> None:
    """Valódi húzás a főablakon: lenyomás, mozgatás, felengedés (`QTest`)."""
    gomb = Qt.MouseButton.LeftButton
    mod = Qt.KeyboardModifier.NoModifier
    QTest.mousePress(window, gomb, mod, kezdet.toPoint())
    qt_app.processEvents()
    QTest.mouseMove(window, veg.toPoint())
    qt_app.processEvents()
    QTest.mouseRelease(window, gomb, mod, veg.toPoint())
    qt_app.processEvents()


#: a nem betűs billentyűk neve a `Qt.Key`-ben (a betűk és számjegyek `Key_<NAGY>`)
_JELEK = {".": "Period", "/": "Slash", "-": "Minus", "_": "Underscore"}


def _gepeld(window, qt_app, szoveg: str) -> None:
    """Billentyűleütések sora (`QTest.keyClick`): a `QQuickWindow`-ra nincs `keyClicks`.

    A nagybetű a karakteres `keyClick`-kel megy: a szöveg attól lesz nagybetű,
    a billentyűkódtól nem."""
    for karakter in szoveg:
        if karakter.isupper():
            QTest.keyClick(window, karakter)
        else:
            nev = _JELEK.get(karakter, karakter.upper())
            QTest.keyClick(window, getattr(Qt.Key, f"Key_{nev}"))
        qt_app.processEvents()


def _mentes_gomb(dialog):
    """A mentés-megerősítő valódi Save gombja (a nyelvtől függően Save vagy Mentés)."""
    gombok = [
        elem for elem in dialog.findChildren(QQuickItem)
        if "Button" in elem.metaObject().className()
        and elem.property("text") in {"Save", "Mentés"}
    ]
    assert gombok, "a mentés megerősítő Save gombja hiányzik"
    return gombok[0]


def _tulajdonsagok_nyitasa(window, qt_app, cel):
    """Mappa-menü ▸ Edit Description: a mappa-tulajdonságok párbeszéd megnyitása."""
    jobbklikk_mappan(window, qt_app, cel)
    kattint(window, qt_app, "folderMenuEditDescription")
    dialog = keres(window, "folderPropertiesDialog")
    assert varj(qt_app, lambda: nyitott(dialog)), (
        "a Leírás szerkesztése nem nyitotta meg a mappa-tulajdonságokat"
    )
    return dialog


def _mappa_zene(cel) -> tuple[bool, str]:
    """A mappa `[Picasa]` zene-beállítása a lemezen maradt `.picasa.ini`-ből."""
    return read_folder_music(load_or_empty(Path(str(cel)) / PICASA_INI_NAME))


class TestMappaMenu:
    def test_a_mappa_torlese_valodi_kattintassal_a_lomtarba_viszi(
        self, mappa_app, qt_app, monkeypatch
    ):
        """Helyettesítő: a valódi lomtárba nem írunk, a hívás eljutását mérjük."""
        window, controller, _motor = mappa_app
        cel = elokeszit_str(window, qt_app, controller)
        lomtarba: list[Path] = []
        monkeypatch.setattr(
            fileops_module,
            "delete_to_trash",
            lambda utvonal_, trash_dir=None: lomtarba.append(Path(utvonal_)),
        )

        jobbklikk_mappan(window, qt_app, cel)
        kattint(window, qt_app, "folderMenuDeleteFolder")
        megerosites = keres(window, "deleteFolderConfirmDialog")
        assert varj(qt_app, lambda: nyitott(megerosites)), (
            "a Delete Folder kattintás nem kért megerősítést"
        )
        assert lomtarba == [], "a megerősítés nélkül a mappa a lomtárba került"

        kattint(window, qt_app, "deleteFolderConfirmYesButton")

        assert varj(qt_app, lambda: lomtarba == [Path(cel)]), (
            f"a megerősítés nem a mappát adta a lomtárnak: {lomtarba}"
        )

    def test_az_export_as_html_valodi_kattintassal_megnyitja_a_webexportot(
        self, mappa_app, qt_app
    ):
        window, controller, _motor = mappa_app
        cel = elokeszit_str(window, qt_app, controller)

        jobbklikk_mappan(window, qt_app, cel)
        kattint(window, qt_app, "folderMenuExportAsHtml")

        dialog = keres(window, "webExportDialog")
        assert varj(qt_app, lambda: nyitott(dialog)), (
            "az Export as HTML kattintás nem nyitotta meg a webexportot"
        )
        zar(qt_app, dialog)


class TestMappalista:
    def test_a_mappalista_uresen_valodi_jobbklikkre_megnyitja_a_menut(
        self, mappa_app, qt_app
    ):
        window, controller, _motor = mappa_app
        elokeszit_str(window, qt_app, controller)
        handler = keres(window, "folderPaneContextMenuHandler")
        assert handler.property("enabled") is True, "a kezelő le van tiltva"
        pane = keres(window, "folderPane")

        jobbklikk_a_ponton(
            window, qt_app, pane.mapToScene(QPointF(pane.width() / 2, pane.height() - 8))
        )

        menu = keres(window, "folderListContextMenu")
        assert varj(qt_app, lambda: menu.property("opened") is True), (
            "a bal oldali mappalista üres részén a jobbklikk nem nyitotta meg a menüt"
        )

    def test_a_mappasor_valodi_balklikkre_kivalasztja_a_mappat(
        self, ket_mappa_app, qt_app
    ):
        window, controller, _motor = ket_mappa_app
        window.show()
        window.requestActivate()
        qt_app.processEvents()
        masik = Path(str(controller.watchedFolders[0])) / MASIK

        kattint(
            window,
            qt_app,
            "folderRowMouse",
            feltetel=lambda elem: utvonal(elem.property("folderPath")) == masik,
        )

        assert varj(qt_app, lambda: utvonal(controller.currentFolder) == masik), (
            f"a mappasor kattintása nem a(z) {MASIK} mappát választotta: "
            f"{controller.currentFolder}"
        )


class TestRacsUresTerulet:
    def test_a_racs_ures_reszen_valodi_jobbklikk_megnyitja_a_mappamenut(
        self, mappa_app, qt_app
    ):
        window, controller, _motor = mappa_app
        elokeszit_str(window, qt_app, controller)
        handler = keres(window, "feedEmptyAreaContextMenu")
        assert handler.property("enabled") is True, "a kezelő le van tiltva"

        jobbklikk_a_ponton(window, qt_app, ures_pont_a_folyamon(window))

        menu = keres(window, "folderContextMenu")
        assert varj(qt_app, lambda: menu.property("visible") is True), (
            "a rács üres részének jobbklikkje nem nyitotta meg a mappa-menüt"
        )

    def test_az_ures_teruletrol_huzott_lasszo_kijelolt_a_keretbe_eso_kepet(
        self, mappa_app, qt_app
    ):
        window, controller, _motor = mappa_app
        elokeszit_str(window, qt_app, controller)
        lasszo = keres(window, "feedFlowLasso")
        assert lasszo.property("enabled") is True, "a lasszó le van tiltva"
        kijelol(window, qt_app, [])
        celpont = sor_pontja(kep_cellaja(window, 0))
        kezdet = ures_pont_a_folyamon(window)

        _huzas(window, qt_app, kezdet, celpont)

        assert varj(qt_app, lambda: 0 in kijelolt(window)), (
            f"az üres területről indított húzás nem jelölte ki a képet: {kijelolt(window)}"
        )


class TestFejlecKapcsolo:
    def test_a_letiltott_sync_kapcsolo_valodi_kattintasra_nem_valt(self, mappa_app, qt_app):
        """A „Sync to Web" kapcsoló a felületen letiltott (`enabled: false`).

        A kattintás nem változtathatja meg a bekapcsoltságát. A rontás-kontroll
        ezt a kapcsolót engedélyezi, és akkor a kattintás vált, a teszt piros."""
        window, controller, _motor = mappa_app
        elokeszit_str(window, qt_app, controller)
        kapcsolo = keres(window, "folderSyncSwitch")
        assert kapcsolo.property("enabled") is False, "a Sync to Web kapcsoló nincs letiltva"

        kattint(window, qt_app, "folderSyncSwitch")

        assert kapcsolo.property("checked") is False, (
            "a letiltott Sync to Web kapcsoló valódi kattintásra átváltott"
        )


class TestMappaTulajdonsagai:
    def test_a_naptar_gomb_valodi_kattintassal_megnyitja_a_naptart(self, mappa_app, qt_app):
        window, controller, _motor = mappa_app
        cel = elokeszit_str(window, qt_app, controller)
        dialog = _tulajdonsagok_nyitasa(window, qt_app, cel)

        kattint(window, qt_app, "folderPropertiesDateCalendarButton")

        naptar = keres(window, "folderPropertiesCalendar")
        assert varj(qt_app, lambda: naptar.property("opened") is True), (
            "a naptár-gomb nem nyitotta meg a naptárat"
        )
        zar(qt_app, dialog)

    def test_a_zene_kapcsolo_es_utvonal_valodi_bevitellel_menti_a_mappat(
        self, mappa_app, qt_app, tmp_path
    ):
        window, controller, _motor = mappa_app
        cel = elokeszit_str(window, qt_app, controller)
        assert _mappa_zene(cel) == (False, "")
        _tulajdonsagok_nyitasa(window, qt_app, cel)

        kattint(window, qt_app, "folderPropertiesUseMusic")
        kattint(window, qt_app, "folderPropertiesMusicPath")
        _gepeld(window, qt_app, "hatter.mp3")
        QTest.keyClick(window, Qt.Key.Key_Return)

        assert varj(qt_app, lambda: _mappa_zene(cel) == (True, "hatter.mp3")), (
            f"a zene-útvonal nem mentődött a mappához: {_mappa_zene(cel)}"
        )

    def test_a_helyszin_mezo_mappa_modban_nem_szerkesztheto(self, mappa_app, qt_app):
        window, controller, _motor = mappa_app
        cel = elokeszit_str(window, qt_app, controller)
        dialog = _tulajdonsagok_nyitasa(window, qt_app, cel)
        mezo = keres(window, "folderPropertiesLocation")
        assert mezo.property("enabled") is False, "a helyszín-mező mappa módban szerkeszthető"

        kattint(window, qt_app, "folderPropertiesLocation")

        assert mezo.property("activeFocus") is False, (
            "a letiltott helyszín-mező kattintásra fókuszt kapott"
        )
        zar(qt_app, dialog)


class TestFotoMenuMaradek:
    def test_a_megtekintes_valodi_kattintassal_megnyitja_a_nezot(self, mappa_app, qt_app):
        window, controller, _motor = mappa_app
        elokeszit_str(window, qt_app, controller)
        kijelol(window, qt_app, [0])

        jobbklikk_fotón(window, qt_app, 0)
        kattint(window, qt_app, "contextMenuOpen")

        assert varj(qt_app, lambda: window.property("viewerOpen") is True), (
            "a View and Edit kattintás nem nyitotta meg a nézetet"
        )

    def test_a_forgatas_jobbra_valodi_kattintassal_forgatast_ment(self, mappa_app, qt_app):
        window, controller, _motor = mappa_app
        elokeszit_str(window, qt_app, controller)
        kijelol(window, qt_app, [0])
        assert ini_ertek(controller, 0, "rotate") is None

        jobbklikk_fotón(window, qt_app, 0)
        kattint(window, qt_app, "contextMenuRotateRight")

        # a jobbra forgatás 1 lépés, a `rotate=` kulcs a szakaszban él
        assert varj(qt_app, lambda: ini_ertek(controller, 0, "rotate") == "rotate(1)"), (
            "a Rotate Clockwise kattintás nem mentett jobbra forgatást"
        )

    def test_a_lemezen_megkeresese_valodi_kattintassal_a_fajlkezelot_hivja(
        self, mappa_app, qt_app, monkeypatch
    ):
        """Helyettesítő: a fájlkezelőt nem indítjuk el, a hívás célját mérjük."""
        window, controller, _motor = mappa_app
        elokeszit_str(window, qt_app, controller)
        kijelol(window, qt_app, [0])
        megnyitva: list[Path] = []
        monkeypatch.setattr(
            fileops_module,
            "reveal_in_file_manager",
            lambda utvonal_: megnyitva.append(Path(utvonal_)),
        )

        jobbklikk_fotón(window, qt_app, 0)
        kattint(window, qt_app, "contextMenuLocate")

        assert varj(qt_app, lambda: megnyitva == [Path(foto_utja(controller, 0))]), (
            f"a Locate on Disk nem a kép útját adta át: {megnyitva}"
        )

    def test_a_mentes_valodi_kattintassal_beegeti_a_szerkesztest(self, mappa_app, qt_app):
        """A Save csak a szűrővel rendelkező képen (`filters=`) aktív: a sima forgatás
        nem szerkesztés. A mentés előtt másolatot készít, és a szűrőlánc beég."""
        window, controller, _motor = mappa_app
        cel = elokeszit_str(window, qt_app, controller)
        kijelol(window, qt_app, [0])
        wait_for_photo_op(
            controller, lambda: controller.applyEffectMany([0], "sepia"), qt_app=qt_app
        )
        assert varj(qt_app, lambda: "sepia=1;" in szures(controller, 0))

        menu = jobbklikk_fotón(window, qt_app, 0)
        assert varj(qt_app, lambda: menu.property("hasEdits") is True), (
            "a szűrt kép menüje nem jelezte a szerkesztést"
        )
        kattint(window, qt_app, "contextMenuSave")
        megerosites = keres(window, "saveConfirmDialog")
        assert varj(qt_app, lambda: nyitott(megerosites)), (
            "a Save kattintás nem nyitotta meg a mentés megerősítését"
        )
        mentes = _mentes_gomb(megerosites)
        wait_for_photo_op(controller, lambda: kattints(window, qt_app, mentes), qt_app=qt_app)

        eredeti = Path(str(cel)) / ORIGINALS_DIR_NAME / "a_nagy.jpg"
        assert varj(qt_app, lambda: eredeti.exists()), (
            "a mentés nem készített biztonsági másolatot az eredetiről"
        )
        assert varj(qt_app, lambda: szures(controller, 0) == ""), (
            "a mentés nem égette be a szűrőt (a filters lánc megmaradt)"
        )

    def test_az_albumhoz_adas_valodi_kattintassal_hozzaadja_a_kepet(self, mappa_app, qt_app):
        window, controller, _motor = mappa_app
        elokeszit_str(window, qt_app, controller)
        token = controller.createAlbum("Masik", [1])
        assert token, "az album nem jött létre"
        assert varj(qt_app, lambda: album_darab(controller, token) == 1)
        kijelol(window, qt_app, [0])
        elotte = album_darab(controller, token)

        menu = jobbklikk_fotón(window, qt_app, 0)
        almenu_megnyitasa(window, qt_app, menu, "contextMenuAddToAlbum")
        kattint(window, qt_app, "contextMenuAddToAlbumItem_" + token)

        assert varj(qt_app, lambda: album_darab(controller, token) == elotte + 1), (
            "az Add to Album tétel nem adta hozzá a képet az albumhoz"
        )


class TestGyorsCimkeBeallitas:
    """A gyorscímke-beállítás párbeszéde: a fogaskerék (`quickTagsGearButton`)
    nyitja, a mezői és a két jelölője a `controller` beállításait írják."""

    def _megnyitas(self, window, qt_app):
        window.setProperty("activeDrawerTab", "tags")
        qt_app.processEvents()
        dialog = keres(window, "quickTagsConfigDialog")
        varj_helyen_all(window, qt_app, keres(window, "quickTagsGearButton"))
        kattint(window, qt_app, "quickTagsGearButton")
        assert varj(qt_app, lambda: nyitott(dialog)), (
            "a fogaskerék kattintás nem nyitotta meg a gyorscímke-beállítást"
        )
        return dialog

    def test_a_mezo_valodi_bevitellel_menti_a_cimket(self, qml_app, qt_app):
        window, controller, _engine = qml_app
        dialog = self._megnyitas(window, qt_app)
        kattint(window, qt_app, "quickTagsReserveRecentCheck")
        assert varj(qt_app, lambda: controller.quickTagsReserveRecent is False)

        kattint(window, qt_app, "quickTagField0", feltetel=lambda elem: elem.property("enabled") is True)
        _gepeld(window, qt_app, "nyar")
        QTest.keyClick(window, Qt.Key.Key_Return)

        assert varj(qt_app, lambda: controller.quickTagConfigLabels[0] == "nyar"), (
            f"a gyorscímke-mező bevitele nem mentődött: {controller.quickTagConfigLabels[0]!r}"
        )
        zar(qt_app, dialog)

    def test_a_tartalek_jelolo_valodi_kattintassal_feloldja_a_ket_gombot(self, qml_app, qt_app):
        window, controller, _engine = qml_app
        dialog = self._megnyitas(window, qt_app)
        jelolo = keres(window, "quickTagsReserveRecentCheck")
        assert jelolo.property("checked") is True, "a tartalék jelölő alapból nincs bekapcsolva"
        mezo = keres(window, "quickTagField0")
        assert mezo.property("enabled") is False, "a bekapcsolt tartalék nem zárta a gombokat"

        kattint(window, qt_app, "quickTagsReserveRecentCheck")

        assert varj(qt_app, lambda: controller.quickTagsReserveRecent is False), (
            "a tartalék jelölő kattintása nem kapcsolta ki a beállítást"
        )
        assert varj(qt_app, lambda: mezo.property("enabled") is True), (
            "a kikapcsolt tartalék nem oldotta fel a gombok mezőit"
        )
        zar(qt_app, dialog)

    def test_az_automatikus_kitoltes_jelolo_valodi_kattintassal_bekapcsol(self, qml_app, qt_app):
        window, controller, _engine = qml_app
        dialog = self._megnyitas(window, qt_app)
        jelolo = keres(window, "quickTagsAutoFillCheck")
        assert jelolo.property("checked") is False

        kattint(window, qt_app, "quickTagsAutoFillCheck")

        assert varj(qt_app, lambda: controller.quickTagsAutoFillFrequent is True), (
            "az automatikus kitöltés jelölő kattintása nem kapcsolta be a beállítást"
        )
        zar(qt_app, dialog)



def _nevezet(qt_app, stub, mode="unnamed", groups=None):
    """A Név nélküliek nézet önálló példánya, valódi ablakban (a stub adatával)."""
    view = _make_view(qt_app, controller=stub)
    view.setProperty("mode", mode)
    window = _host_in_window(qt_app, view)
    return view, window


def _valasztas(view, qt_app, arcok: list[int]) -> None:
    """A kijelölés állapota: a kiválasztott arcok azonosítói."""
    view.setProperty("selectedFaceIds", {str(arc): True for arc in arcok})
    view.setProperty("selectedCount", len(arcok))
    qt_app.processEvents()


class TestNevNelkuliek:
    def test_a_mellozott_arc_visszavonasa_valodi_kattintassal_visszaadja_az_arcot(self, qt_app):
        stub = _StubFaceScanController()
        view, window = _nevezet(qt_app, stub, mode="ignored")
        _valasztas(view, qt_app, [4])

        kattint(view, qt_app, "unignoreFacesButton")

        assert varj(qt_app, lambda: ("unignoreFaces", [4]) in stub.calls), (
            f"a Stop ignoring nem vonta vissza a mellőzést: {stub.calls}"
        )


class TestArcNevMezo:
    def test_az_arc_nev_mezoje_valodi_bevitellel_es_enterrel_nevet_kuld(self, qt_app):
        """A kártya névmezője Enterre a `nameSubmitted(arc, nev)` jelet adja."""
        stub = _StubFaceScanController(groups=[{
            "label": "Csoport 1",
            "faces": [{"faceId": 12, "thumbUrl": "", "suggestedName": ""}],
        }])
        view, window = _nevezet(qt_app, stub)
        kuldott: list[tuple[int, str]] = []
        view.nameSubmitted.connect(lambda arc, nev: kuldott.append((arc, nev)))
        assert varj(qt_app, lambda: keres_latszo(window, "unnamedFaceNameField_12") is not None), (
            "a 12-es arc névmezője nem látszik"
        )

        kattint(view, qt_app, "unnamedFaceNameField_12")
        _gepeld(window, qt_app, "Anna")
        QTest.keyClick(window, Qt.Key.Key_Return)

        assert varj(qt_app, lambda: kuldott == [(12, "Anna")]), (
            f"az Enter nem küldte a nevet az arcnak: {kuldott}"
        )


@pytest.fixture
def emberek_app(qml_app):
    """A teljes app, a menüsorát élve tartva (a Python-wrapper GC-je ellen)."""
    window, _controller, _engine = qml_app
    menusor = window.property("menuBar")
    assert menusor is not None, "a főablak felső menüsora hiányzik"
    yield qml_app
    del menusor


_ANNA = "1111111111111111"
_BELA = "2222222222222222"
_EMBEREK_INI = (
    "[Contacts2]\n"
    f"{_ANNA}=Anna;;\n"
    f"{_BELA}=Béla;;\n"
    "[a.jpg]\n"
    f"faces=rect64(1e00280045006e00),{_ANNA}\n"
    "[b.jpg]\n"
    f"faces=rect64(1e00280045006e00),{_BELA}\n"
)


def _emberek_betoltese(qml_app, qt_app) -> Path:
    """Két személy (Anna, Béla) az indexbe: a mappa `.picasa.ini`-je és a szinkron."""
    window, controller, _engine = qml_app
    lib = Path(str(controller.watchedFolders[0]))
    (lib / PICASA_INI_NAME).write_text(_EMBEREK_INI, encoding="utf-8")
    with open_index(controller._db_path) as conn:
        sync_tree(conn, lib)
    controller._reload_after_sync()
    qt_app.processEvents()
    return lib


def _emberek_kezelo_nyitasa(window, qt_app):
    """Eszközök ▸ People Manager: a valódi menütétel, majd a párbeszéd megnyitása."""
    tetel_kattintasa(window, qt_app, "&Tools", "menuToolsPeopleManager")
    loader = keres(window, "peopleManagerLoader")
    assert varj(qt_app, lambda: loader.property("item") is not None), (
        "az Eszközök ▸ People Manager nem nyitotta meg a kezelőt"
    )
    dialog = loader.property("item")
    assert varj(qt_app, lambda: nyitott(dialog)), "a People Manager nem nyílt meg"
    return dialog


def _lista_darab(dialog) -> int:
    return int(keres(dialog, "peopleManagerContactList").property("count"))


class TestEmberekKezelo:
    def test_a_kereso_mezo_valodi_bevitellel_szuri_a_szemelyeket(self, emberek_app, qt_app):
        window, _controller, _engine = emberek_app
        _emberek_betoltese(emberek_app, qt_app)
        dialog = _emberek_kezelo_nyitasa(window, qt_app)
        assert varj(qt_app, lambda: _lista_darab(dialog) == 2), "a két személy nem látszik"

        kattint(dialog, qt_app, "peopleManagerSearchField")
        _gepeld(window, qt_app, "anna")

        assert varj(qt_app, lambda: _lista_darab(dialog) == 1), (
            f"a keresés nem szűkítette a listát: {_lista_darab(dialog)}"
        )

    def test_a_szinkron_jelolo_letiltott_valodi_kattintasra_nem_valt(self, emberek_app, qt_app):
        window, _controller, _engine = emberek_app
        _emberek_betoltese(emberek_app, qt_app)
        dialog = _emberek_kezelo_nyitasa(window, qt_app)
        jelolo = keres(dialog, "peopleManagerSyncCheck")
        assert jelolo.property("enabled") is False, "a Sync Face Tags jelölő nincs letiltva"

        kattint(dialog, qt_app, "peopleManagerSyncCheck")

        assert jelolo.property("checked") is False, (
            "a letiltott Sync Face Tags jelölő valódi kattintásra átváltott"
        )
        assert nyitott(dialog), "a letiltott jelölő bezárta a People Managert"

    def test_az_online_kontaktok_gomb_letiltott_valodi_kattintasra_nem_nyit_semmit(self, emberek_app, qt_app):
        window, _controller, _engine = emberek_app
        _emberek_betoltese(emberek_app, qt_app)
        dialog = _emberek_kezelo_nyitasa(window, qt_app)
        gomb = keres(dialog, "peopleManagerOnlineButton")
        assert gomb.property("enabled") is False, "a Manage Online Contacts nincs letiltva"
        darab = _lista_darab(dialog)

        kattint(dialog, qt_app, "peopleManagerOnlineButton")

        assert nyitott(dialog) and _lista_darab(dialog) == darab, (
            "a letiltott Manage Online Contacts gomb valódi kattintásra változtatott"
        )

    def test_a_kontaktok_frissitese_gomb_letiltott_valodi_kattintasra_nem_valtozik(self, emberek_app, qt_app):
        window, _controller, _engine = emberek_app
        _emberek_betoltese(emberek_app, qt_app)
        dialog = _emberek_kezelo_nyitasa(window, qt_app)
        gomb = keres(dialog, "peopleManagerRefreshButton")
        assert gomb.property("enabled") is False, "a Refresh Contacts nincs letiltva"
        darab = _lista_darab(dialog)

        kattint(dialog, qt_app, "peopleManagerRefreshButton")

        assert nyitott(dialog) and _lista_darab(dialog) == darab, (
            "a letiltott Refresh Contacts gomb valódi kattintásra változtatott"
        )


class TestFotoMenuEmberAlbum:
    def test_az_emberalbumhoz_adas_valodi_kattintassal_atrakja_az_arcot(self, emberek_app, qt_app):
        window, controller, _engine = emberek_app
        lib = _emberek_betoltese(emberek_app, qt_app)
        controller.showPerson("Anna")
        qt_app.processEvents()
        kijelol(window, qt_app, [0])

        jobbklikk_fotón(window, qt_app, 0)
        kattint(window, qt_app, "contextMenuAddToPeopleAlbum")
        almenu = keres(window, "contextMenuAddToPeopleAlbumMenu")
        assert varj(qt_app, lambda: almenu.property("opened") is True), (
            "az Add to People Album nem nyitotta meg az almenüt"
        )
        kattint(window, qt_app, "contextMenuAddToPeopleAlbumItem_" + "Béla")

        assert varj(qt_app, lambda: _arc_szemelye(lib, "a.jpg") == _BELA), (
            f"a Béla albumba adás nem helyezte át az arcot: {_arc_szemelye(lib, 'a.jpg')}"
        )


def _arc_szemelye(lib: Path, kep: str) -> str | None:
    """A kép első arcának személy-azonosítója a lemezen maradt `.picasa.ini`-ből."""
    arcok = parse_faces(load_document(lib / PICASA_INI_NAME).section(kep).get("faces") or "")
    return arcok[0].contact_id.casefold() if arcok else None


class TestFotoMenuHelyek:
    def test_a_locate_in_picasa_valodi_kattintassal_a_kep_mappajat_nyitja(
        self, ket_mappa_app, qt_app
    ):
        """Album-nézetből: a kép mappájára vált, és kilép az albumból."""
        window, controller, _motor = ket_mappa_app
        window.show()
        window.requestActivate()
        cel = Path(str(controller.watchedFolders[0])) / MAPPA
        masik = Path(str(controller.watchedFolders[0])) / MASIK
        controller.selectFolder(str(masik))
        assert varj(qt_app, lambda: any(f.name == "d_nagy.jpg" for f in controller.photos.photos)), (
            "a másik mappa képe nem töltődött be"
        )
        sor = next(i for i, f in enumerate(controller.photos.photos) if f.name == "d_nagy.jpg")
        token = controller.createAlbum("Masik kepe", [sor])
        assert varj(qt_app, lambda: album_darab(controller, token) == 1)
        controller.selectFolder(str(cel))
        assert varj(qt_app, lambda: len(controller.photos.photos) > 0)
        controller.showAlbum(token)
        assert varj(qt_app, lambda: controller.currentAlbumToken == token), (
            "az album nem lett az aktuális nézet"
        )
        kijelol(window, qt_app, [0])

        jobbklikk_fotón(window, qt_app, 0)
        kattint(window, qt_app, "contextMenuLocateInPicasa")

        assert varj(
            qt_app,
            lambda: utvonal(controller.currentFolder) == masik
            and controller.currentAlbumToken == "",
        ), (
            f"a Locate in PicasaPy nem a kép mappájára váltott: {controller.currentFolder}"
        )

    def test_az_eredeti_fajl_megkeresese_valodi_kattintassal_a_fajlkezelot_hivja(
        self, mappa_app, qt_app, monkeypatch
    ):
        """A „Locate" almenü (az eredetivel rendelkező képen) a Locate Original tétele."""
        window, controller, _motor = mappa_app
        mentett_eredetik(controller)
        elokeszit_str(window, qt_app, controller)
        kijelol(window, qt_app, [0])
        megnyitva: list[Path] = []
        monkeypatch.setattr(
            fileops_module,
            "reveal_in_file_manager",
            lambda utvonal_: megnyitva.append(Path(utvonal_)),
        )
        menu = jobbklikk_fotón(window, qt_app, 0)
        assert varj(qt_app, lambda: menu.property("_keresesAlmenu") is True), (
            "az eredetivel rendelkező kép menüjében nincs a Locate almenü"
        )
        kattint(window, qt_app, "contextMenuLocateMenuTetel")
        almenu = keres(window, "contextMenuLocateMenu")
        assert varj(qt_app, lambda: almenu.property("opened") is True), (
            "a Locate almenü nem nyílt meg"
        )

        kattint(window, qt_app, "contextMenuLocateOriginal")

        eredeti = Path(foto_utja(controller, 0)).parent / ORIGINALS_DIR_NAME / Path(foto_utja(controller, 0)).name
        assert varj(qt_app, lambda: megnyitva == [eredeti]), (
            f"a Locate Original nem az eredeti helyét adta át: {megnyitva}"
        )

    def test_a_fajl_megkeresese_almenuboll_valodi_kattintassal_a_kep_utjat_adja(
        self, mappa_app, qt_app, monkeypatch
    ):
        window, controller, _motor = mappa_app
        mentett_eredetik(controller)
        elokeszit_str(window, qt_app, controller)
        kijelol(window, qt_app, [0])
        megnyitva: list[Path] = []
        monkeypatch.setattr(
            fileops_module,
            "reveal_in_file_manager",
            lambda utvonal_: megnyitva.append(Path(utvonal_)),
        )
        menu = jobbklikk_fotón(window, qt_app, 0)
        assert varj(qt_app, lambda: menu.property("_keresesAlmenu") is True)
        kattint(window, qt_app, "contextMenuLocateMenuTetel")
        almenu = keres(window, "contextMenuLocateMenu")
        assert varj(qt_app, lambda: almenu.property("opened") is True)

        kattint(window, qt_app, "contextMenuLocateFile")

        assert varj(qt_app, lambda: megnyitva == [Path(foto_utja(controller, 0))]), (
            f"a File on Disk nem a kép útját adta át: {megnyitva}"
        )


@pytest.fixture
def mentes_app(mappa_app, tmp_path, monkeypatch):
    """A mappa-app biztonsági mentés párbeszéddel: a Képek mappája a teszt mappája.

    A mentés-vezérlő a futtató gép Képek mappájától nem függhet (a CI-n más)."""
    import picasapy.app.backup_controller as backup_module
    from picasapy.app.backup_controller import BackupController

    window, controller, engine = mappa_app
    monkeypatch.setattr(backup_module, "_kepek_mappaja", lambda: str(tmp_path / "Kepek"))
    lib = Path(str(controller.watchedFolders[0]))
    vezerlo = BackupController(Path(str(controller._db_path)), (str(lib),))
    engine.rootContext().setContextProperty("backupController", vezerlo)
    vezerlo.ujKeszlet("Sajat mentes", str(tmp_path / "cel"), "minden", "lemez")
    menusor = window.property("menuBar")
    assert menusor is not None, "a főablak felső menüsora hiányzik"
    yield mappa_app
    del menusor


class TestMentesSzuroSor:
    def test_a_mentetlen_mappa_pipaja_valodi_kattintassal_jelolest_ad(
        self, mentes_app, qt_app
    ):
        window, controller, _engine = mentes_app
        cel = elokeszit_str(window, qt_app, controller)
        tetel_kattintasa(window, qt_app, "&Tools", "menuToolsBackup")
        host = keres(window, "backupHost")
        assert varj(qt_app, lambda: host.property("visible") is True), (
            "a Képek biztonsági mentése nem nyílt meg"
        )
        host.setProperty("kivalasztott", 0)
        assert varj(qt_app, lambda: host.property("mappakToltodnek") is False), (
            "a mentetlen mappák listája nem érkezett meg"
        )
        pipa = keres(window, "folderRowMentesCheck")
        assert varj(qt_app, lambda: pipa.property("checked") is False), (
            "a még nem pipált mappa pipája eleve be volt kapcsolva"
        )

        kattint(window, qt_app, "folderRowMentesCheck")

        assert varj(qt_app, lambda: pipa.property("checked") is True), (
            f"a mentetlen mappa pipája nem kapcsolt be: {cel}"
        )
