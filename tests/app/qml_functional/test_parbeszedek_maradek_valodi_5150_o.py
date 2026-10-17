"""A Párbeszédek csoport maradék tételei VALÓDI bemenettel (#5150).

A párbeszédet a menüjéből valódi kattintással nyitjuk, a mezőket valódi
kattintással és billentyűzettel érjük el. A tiltott vagy csak olvasható
vezérlőre is valódi kattintást adunk: ilyenkor azt mérjük, hogy a bemenet
NEM módosít rajta. A hatást a vezérlő állapotán, a megnyíló párbeszéden, a
lemezen maradt fájlnéven vagy a mező értékén mérjük.
"""

from __future__ import annotations

import pytest
from PySide6.QtCore import QPoint, QPointF, Qt
from PySide6.QtTest import QTest

from tests.app.qml_functional._felsomenupontok_helpers_4329 import _kattints, _objektum
from tests.app.qml_functional._mappa_kep_menu_5150_helpers import (
    app_epitese,
    elokeszit,
    kijelol,
    mappa_ut,
    szures,
)
from tests.app.qml_functional._menusor_maradek_5150_helpers import (
    billentyu,
    latszik,
    tetel_kattintasa,
    varj,
)

CTRL = Qt.KeyboardModifier.ControlModifier
CTRL_SHIFT = CTRL | Qt.KeyboardModifier.ShiftModifier


def _elem(window, nev: str):
    elem = _objektum(window, nev)
    assert elem is not None, f"{nev} nem található"
    return elem


def _gomb_felirattal(dialogus, felirat: str):
    """A párbeszéd láblécének gombja a `felirat` felirattal (Dialog.Ok stb.), rekurzívan."""
    sor = [dialogus.property("footer")]
    feliratok: list[str] = []
    while sor:
        elem = sor.pop()
        if elem is None:
            continue
        if elem.property("text"):
            feliratok.append(str(elem.property("text")))
        if elem.property("text") == felirat:
            return elem
        sor.extend(elem.childItems())
    raise AssertionError(f"a párbeszédnek nincs „{felirat}” gombja, a feliratok: {feliratok}")


def _kozep(elem) -> QPoint:
    kozep = elem.mapToScene(QPointF(elem.width() / 2, elem.height() / 2))
    return QPoint(round(kozep.x()), round(kozep.y()))


def _nev_kattintasa(window, qt_app, nev: str) -> None:
    """Valódi kattintás a `nev` vezérlőn; a vezérlőnek látszania és engedélyezettnek kell lennie."""
    elem = _elem(window, nev)
    assert varj(
        qt_app, lambda: elem.property("visible") is True and elem.width() > 0
    ), f"{nev} nem látszik kattintható méretben"
    _kattints(qt_app, elem)


def _tiltott_kattintasa(window, qt_app, nev: str) -> None:
    """Valódi kattintás a tiltott vezérlő közepén: az engedélyezettséget nem kéri."""
    elem = _elem(window, nev)
    assert elem.width() > 0 and elem.height() > 0, f"{nev}: nincs kattintható mérete"
    QTest.mouseClick(
        elem.window(), Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, _kozep(elem)
    )
    qt_app.processEvents()


def _gepeld(window, qt_app, szoveg: str) -> None:
    """Karakterenként valódi billentyűleütés az ablakra (a QQuick-ablakon a `keyClicks` nem megy)."""
    for jel in szoveg:
        QTest.keyClick(window, jel)
    qt_app.processEvents()


def _vegere_ir(window, qt_app, nev: str, szoveg: str) -> None:
    """A `nev` mezőre kattint, a kurzort a végére viszi, és valódi billentyűkkel ír."""
    mezo = _elem(window, nev)
    _nev_kattintasa(window, qt_app, nev)
    QTest.keyClick(mezo.window(), Qt.Key.Key_End)
    _gepeld(mezo.window(), qt_app, szoveg)


def _beallitasok_nyitasa(window, qt_app) -> None:
    tetel_kattintasa(window, qt_app, "&Tools", "menuToolsOptions")
    assert varj(qt_app, lambda: latszik(window, "optionsDialog")), (
        "a Beállítások párbeszéd nem nyílt meg"
    )


@pytest.fixture
def kep_app(qt_app, tmp_path):
    yield from app_epitese(qt_app, tmp_path)


class TestBeallitasokAltalanos:
    def test_a_cel_mappa_mezo_csak_olvashato_valodi_bemenetre_sem_valtozik(
        self, kep_app, qt_app
    ):
        window, controller, _engine = kep_app
        elokeszit(window, qt_app, controller)
        _beallitasok_nyitasa(window, qt_app)
        mezo = _elem(window, "optionsImportDestField")
        assert mezo.property("readOnly") is True, "a mező nem csak olvasható"
        elotte = mezo.property("text")

        _vegere_ir(window, qt_app, "optionsImportDestField", "xyz")

        assert mezo.property("text") == elotte, (
            "a csak olvasható importcélmezőbe gépelés módosította az értéket"
        )


class TestBeallitasokHalozat:
    @pytest.mark.parametrize(
        "nev", ["optionsNetworkProxyUserField", "optionsNetworkProxyPasswordField"]
    )
    def test_a_proxy_mezo_tiltott_valodi_kattintasra_sem_kap_fokuszt(
        self, kep_app, qt_app, nev
    ):
        window, controller, _engine = kep_app
        elokeszit(window, qt_app, controller)
        _beallitasok_nyitasa(window, qt_app)
        _nev_kattintasa(window, qt_app, "optionsTabNetwork")
        mezo = _elem(window, nev)
        assert mezo.property("enabled") is False, (
            "a proxy-mező engedélyezett: a teszt nem a tiltottságot méri"
        )

        _tiltott_kattintasa(window, qt_app, nev)

        assert mezo.property("activeFocus") is False, (
            "a tiltott proxy-mező valódi kattintásra fókuszt kapott"
        )
        assert mezo.property("text") == "", "a tiltott proxy-mező értéke megváltozott"

    def test_a_naplo_utvonal_csak_olvashato(self, kep_app, qt_app):
        window, controller, _engine = kep_app
        elokeszit(window, qt_app, controller)
        _beallitasok_nyitasa(window, qt_app)
        _nev_kattintasa(window, qt_app, "optionsTabNetwork")
        mezo = _elem(window, "optionsNetworkLogPathField")
        elotte = mezo.property("text")
        assert mezo.property("readOnly") is True, "a naplófájl mező nem csak olvasható"

        _vegere_ir(window, qt_app, "optionsNetworkLogPathField", "xyz")

        assert mezo.property("text") == elotte, (
            "a csak olvasható naplómezőbe gépelés módosította az útvonalat"
        )


class TestBeallitasokDiasor:
    def test_a_ciklus_jelolo_valtja_a_beallitast(self, kep_app, qt_app):
        window, controller, _engine = kep_app
        elokeszit(window, qt_app, controller)
        _beallitasok_nyitasa(window, qt_app)
        _nev_kattintasa(window, qt_app, "optionsTabSlideshow")
        elotte = bool(controller.slideshowLoop)

        _nev_kattintasa(window, qt_app, "optionsSlideshowLoopCheck")

        assert varj(qt_app, lambda: bool(controller.slideshowLoop) is (not elotte)), (
            "a ciklus jelölőnégyzet kattintása nem váltotta a beállítást"
        )

    def test_a_zene_jelolo_kikapcsolja_a_mappavalasztast(self, kep_app, qt_app):
        window, controller, _engine = kep_app
        elokeszit(window, qt_app, controller)
        _beallitasok_nyitasa(window, qt_app)
        _nev_kattintasa(window, qt_app, "optionsTabSlideshow")
        assert controller.slideshowMusicEnabled is True, (
            "a zene alapból ki van kapcsolva: a teszt nem bizonyít"
        )
        gomb = _elem(window, "optionsSlideshowMusicBrowseButton")
        assert gomb.property("enabled") is True, "a tallózás gomb kiinduláskor tiltott"

        _nev_kattintasa(window, qt_app, "optionsSlideshowPlayMusicCheck")

        assert varj(qt_app, lambda: controller.slideshowMusicEnabled is False), (
            "a zenét játszó jelölő kattintása nem kapcsolta ki a zenét"
        )
        assert varj(qt_app, lambda: gomb.property("enabled") is False), (
            "a zene kikapcsolása után a tallózás gomb még engedélyezett"
        )

    def test_a_zene_mappa_mezo_csak_olvashato(self, kep_app, qt_app):
        window, controller, _engine = kep_app
        elokeszit(window, qt_app, controller)
        _beallitasok_nyitasa(window, qt_app)
        _nev_kattintasa(window, qt_app, "optionsTabSlideshow")
        mezo = _elem(window, "optionsSlideshowMusicPathField")
        elotte = mezo.property("text")
        assert mezo.property("readOnly") is True, "a zenemappa mező nem csak olvasható"

        _vegere_ir(window, qt_app, "optionsSlideshowMusicPathField", "xyz")

        assert mezo.property("text") == elotte, (
            "a csak olvasható zenemappa-mezőbe gépelés módosította az útvonalat"
        )

    def test_a_tallozas_gomb_megnyitja_a_mappavalasztot(self, kep_app, qt_app):
        window, controller, _engine = kep_app
        elokeszit(window, qt_app, controller)
        _beallitasok_nyitasa(window, qt_app)
        _nev_kattintasa(window, qt_app, "optionsTabSlideshow")
        valaszto = _elem(window, "optionsSlideshowMusicFolderDialog")
        assert valaszto.property("visible") is False, "a mappaválasztó már nyitva"

        _nev_kattintasa(window, qt_app, "optionsSlideshowMusicBrowseButton")

        assert varj(qt_app, lambda: valaszto.property("visible") is True), (
            "a Tallózás gomb nem nyitotta meg a zenemappa-választót"
        )


class TestBeallitasokWebAlbum:
    @pytest.mark.parametrize(
        "nev",
        [
            "optionsWebStarredOnlyCheck",
            "optionsWebUploadNameTagsCheck",
            "optionsWebWatermarkCheck",
        ],
    )
    def test_a_web_album_tiltott_jelolo_valodi_kattintasra_nem_valt(
        self, kep_app, qt_app, nev
    ):
        window, controller, _engine = kep_app
        elokeszit(window, qt_app, controller)
        _beallitasok_nyitasa(window, qt_app)
        _nev_kattintasa(window, qt_app, "optionsTabWebAlbums")
        jelolo = _elem(window, nev)
        assert jelolo.property("enabled") is False, (
            "a web album jelölő engedélyezett: a teszt nem a tiltottságot méri"
        )
        elotte = jelolo.property("checked")

        _tiltott_kattintasa(window, qt_app, nev)

        assert jelolo.property("checked") == elotte, (
            "a tiltott web album jelölő valódi kattintásra átváltott"
        )

    def test_a_web_album_vizjel_szovege_tiltott_es_nem_irhato(self, kep_app, qt_app):
        window, controller, _engine = kep_app
        elokeszit(window, qt_app, controller)
        _beallitasok_nyitasa(window, qt_app)
        _nev_kattintasa(window, qt_app, "optionsTabWebAlbums")
        mezo = _elem(window, "optionsWebWatermarkTextField")
        assert mezo.property("enabled") is False, "a vízjel-szöveg mező engedélyezett"
        elotte = mezo.property("text")

        _tiltott_kattintasa(window, qt_app, "optionsWebWatermarkTextField")
        _gepeld(mezo.window(), qt_app, "xyz")

        assert mezo.property("text") == elotte, (
            "a tiltott vízjel-szöveg mezőbe gépelés módosította az értéket"
        )


class TestWebExport:
    def test_a_webexport_cim_mezo_valodi_gepelessel_frissiti_a_cimet(self, kep_app, qt_app):
        window, controller, _engine = kep_app
        elokeszit(window, qt_app, controller)
        tetel_kattintasa(window, qt_app, "F&older", "menuFolderWebExport")
        assert varj(qt_app, lambda: latszik(window, "webExportDialog")), (
            "a HTML-export párbeszéd nem nyílt meg"
        )
        dialogus = _elem(window, "webExportDialog")
        elotte = dialogus.property("albumTitle")

        _vegere_ir(window, qt_app, "webExportTitleField", "Nyaralas")

        assert varj(qt_app, lambda: dialogus.property("albumTitle") == elotte + "Nyaralas"), (
            "a címmezőbe gépelt szöveg nem jutott el az album címéig"
        )


class TestPicasaImport:
    def test_a_picasa_forrasmappa_mezo_fogadja_a_beirast(self, kep_app, qt_app):
        window, controller, _engine = kep_app
        elokeszit(window, qt_app, controller)
        tetel_kattintasa(window, qt_app, "&Tools", "menuToolsImportFromPicasa")
        assert varj(qt_app, lambda: latszik(window, "picasaDataImportDialog")), (
            "a Picasa-adatimport párbeszéd nem nyílt meg"
        )
        mezo = _elem(window, "picasaImportSourceFolderField")
        elotte = mezo.property("text")

        _vegere_ir(window, qt_app, "picasaImportSourceFolderField", "xyz")

        assert mezo.property("text") == elotte + "xyz", (
            "a Picasa-forrásmappa mezőbe gépelt szöveg nem jelent meg"
        )


class TestAtnevezes:
    def test_az_atnevezes_mezo_valodi_bevitellel_atnevezi_a_fajlt(self, kep_app, qt_app):
        window, controller, _engine = kep_app
        elokeszit(window, qt_app, controller)
        mappa = mappa_ut(controller)
        regi = mappa / "a_nagy.jpg"
        uj = mappa / "uj_nev.jpg"
        assert regi.exists() and not uj.exists(), "a teszt fájlai nem a várt állapotban vannak"
        tetel_kattintasa(window, qt_app, "&File", "menuFileRename")
        assert varj(qt_app, lambda: latszik(window, "renameDialog")), (
            "az Átnevezés párbeszéd nem nyílt meg"
        )
        mezo = _elem(window, "renameField")
        _nev_kattintasa(window, qt_app, "renameField")
        QTest.keyClick(mezo.window(), Qt.Key.Key_A, CTRL)
        _gepeld(mezo.window(), qt_app, "uj_nev.jpg")

        _kattints(qt_app, _gomb_felirattal(_elem(window, "renameDialog"), "Rename"))

        assert varj(qt_app, lambda: uj.exists() and not regi.exists()), (
            "az Átnevezés mezőbe írt név nem nevezte át a fájlt, a mappa: "
            f"{sorted(p.name for p in mappa.iterdir())}"
        )


class TestVisszaallitas:
    @pytest.mark.parametrize("gomb", ["revertOkButton", "revertUndoSaveButton"])
    def test_a_visszaallitas_gomb_az_eredeti_kepet_allitja_vissza(
        self, kep_app, qt_app, gomb
    ):
        window, controller, _engine = kep_app
        elokeszit(window, qt_app, controller)
        kep = mappa_ut(controller) / "a_nagy.jpg"
        eredeti = kep.read_bytes()
        kijelol(window, qt_app, [0])
        billentyu(window, qt_app, "batchBwShortcut", Qt.Key.Key_B, CTRL_SHIFT)
        assert varj(qt_app, lambda: "bw=1;" in szures(controller, 0)), (
            "a fekete-fehér szűrő nem került a képre: a teszt nem bizonyít"
        )
        # Előfeltétel: a kép már mentve van. A Fájl ▸ Mentés UI-útja a megerősítés után
        # érvénytelenítette a főablak burkolóját a teszt-appban, ezért a mentést a kontroller végzi.
        controller.saveRowsToDisk([0])
        assert varj(qt_app, lambda: kep.read_bytes() != eredeti), (
            "a mentés nem írta ki a szerkesztett képet: a visszaállítás nem bizonyít"
        )
        # A Visszaállítás engedélyezése kötés: a mentés után a kijelölés újraírása frissíti.
        kijelol(window, qt_app, [0])
        assert varj(qt_app, lambda: controller.hasSavedBackup([0]) is True), (
            "a mentés után nincs mentett másolat: a Visszaállítás tiltott marad"
        )
        tetel_kattintasa(window, qt_app, "&File", "menuFileRevert")
        assert varj(qt_app, lambda: latszik(window, "revertConfirmDialog")), (
            "a Visszaállítás párbeszéd nem nyílt meg"
        )

        _nev_kattintasa(window, qt_app, gomb)

        assert varj(qt_app, lambda: kep.read_bytes() == eredeti), (
            f"a {gomb} gomb nem állította vissza az eredeti képet"
        )


class TestExport:
    def test_az_export_helye_csak_olvashato(self, kep_app, qt_app):
        window, controller, _engine = kep_app
        elokeszit(window, qt_app, controller)
        tetel_kattintasa(window, qt_app, "&File", "menuFileExport")
        assert varj(qt_app, lambda: latszik(window, "exportDialog")), (
            "az Exportálás párbeszéd nem nyílt meg"
        )
        mezo = _elem(window, "exportLocationBox")
        elotte = mezo.property("text")
        assert mezo.property("readOnly") is True, "az export helye nem csak olvasható"

        _vegere_ir(window, qt_app, "exportLocationBox", "xyz")

        assert mezo.property("text") == elotte, (
            "a csak olvasható export-helybe gépelés módosította az útvonalat"
        )

    def test_a_kimeneti_mappa_neve_fogadja_a_beirast(self, kep_app, qt_app):
        window, controller, _engine = kep_app
        elokeszit(window, qt_app, controller)
        tetel_kattintasa(window, qt_app, "&File", "menuFileExport")
        assert varj(qt_app, lambda: latszik(window, "exportDialog"))
        mezo = _elem(window, "exportFolderNameField")
        elotte = mezo.property("text")

        _vegere_ir(window, qt_app, "exportFolderNameField", "_teszt")

        assert mezo.property("text") == elotte + "_teszt", (
            "a kimeneti mappa nevébe gépelt szöveg nem jelent meg"
        )

    def test_a_meretmezo_csak_atmeretezes_mellett_irhato(self, kep_app, qt_app):
        window, controller, _engine = kep_app
        elokeszit(window, qt_app, controller)
        tetel_kattintasa(window, qt_app, "&File", "menuFileExport")
        assert varj(qt_app, lambda: latszik(window, "exportDialog"))
        mezo = _elem(window, "exportSizeField")
        assert mezo.property("enabled") is False, (
            "a méretmező az eredeti méret mellett engedélyezett"
        )
        elotte = mezo.property("text")
        _tiltott_kattintasa(window, qt_app, "exportSizeField")
        assert mezo.property("text") == elotte

        _nev_kattintasa(window, qt_app, "exportSizeResizeRadio")
        assert varj(qt_app, lambda: mezo.property("enabled") is True), (
            "az átméretezés kapcsoló nem engedélyezte a méretmezőt"
        )
        _vegere_ir(window, qt_app, "exportSizeField", "800")

        assert mezo.property("text").endswith("800"), (
            "az engedélyezett méretmezőbe gépelt szám nem jelent meg"
        )

    def test_a_vizjel_mezo_csak_a_jelolo_mellett_irhato(self, kep_app, qt_app):
        window, controller, _engine = kep_app
        elokeszit(window, qt_app, controller)
        tetel_kattintasa(window, qt_app, "&File", "menuFileExport")
        assert varj(qt_app, lambda: latszik(window, "exportDialog"))
        mezo = _elem(window, "exportWatermarkField")
        assert mezo.property("enabled") is False, "a vízjel-mező a jelölő nélkül is engedélyezett"

        _nev_kattintasa(window, qt_app, "exportWatermarkCheck")
        assert varj(qt_app, lambda: mezo.property("enabled") is True), (
            "a vízjel-jelölő nem engedélyezte a vízjel-mezőt"
        )
        _vegere_ir(window, qt_app, "exportWatermarkField", "(c)")

        assert mezo.property("text").endswith("(c)"), (
            "az engedélyezett vízjel-mezőbe gépelt szöveg nem jelent meg"
        )
