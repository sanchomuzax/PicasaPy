"""Az „Egyéb" tételei VALÓDI egérkattintással (#5150, 10. rész, 3. fájl).

A Beállítások párbeszéd Általános, Hálózat, Web Albums, Fájltípusok és
Nyomtatás fülének vezérlői. Minden tétel valódi `QTest.mouseClick`-kel indul;
a hatást a vezérlő és a mögötte álló beállítás állapotán mérjük.

Lefedve:
- Általános: `optionsSkipDeleteConfirmCheck` (a törlés-megerősítés tára),
  `optionsAutoExcludeCheck` (az importáló `autoExclude` állapota),
  `optionsPrivacyLink` (a külső böngésző helyett a `https`-kezelő kapja a címet).
  Az `optionsUsageStatsCheck` tiltott: a kattintás nem vált.
- Hálózat: a proxy-csoport tiltott (`enabled: false`), így az
  `optionsNetworkAutoDetectCheck` kattintása nem vált. A naplózási vezérlők
  (#5145) működnek, azokat a `test_halozat_naplozas_valodi_5145.py` méri.
- Web Albums: a fül egésze tiltott (`enabled: false`), a három jelölő
  (`optionsWebStripedUploadCheck`, `optionsWebKeepJpegQualityCheck`,
  `optionsWebConfirmSyncDisableCheck`) kattintása nem vált.
- Fájltípusok: a kilenc jelölő (`optionsFileTypeBmpCheck` … `optionsFileTypeQuickTimeCheck`)
  átvált, és a vezérlő `fileTypeEnabled` állapota is.
- Nyomtatás: `optionsPrintSizeCombo0` - a gyorsgomb-legördülő valódi kattintással
  új méretet választ, és a nyomtatási beállítás is követi. Az elem ismétlőben
  van, ezért a vizuális fából keressük.

Export (Fájl ▸ Export Picture to Folder…), `ExportDialogs`: `exportAddNumbersCheck`,
`exportSizeOriginalRadio`, `exportSizeResizeRadio` (a méretsor engedélyezése),
`exportMovieFirstFrame`, `exportMovieFull` (a film-választó; a film jelenlétét a
teszt állítja be), `exportWatermarkCheck` (a vízjel-mező).

Nincs lefedve: `optionsFaceUploadContactPhotosCheck` (a Névcímkék fül jelölője
REJTETT, nincs olyan pixel, amelyre kattinthatnánk).

Parancsot közvetlenül nem indítunk: nincs `triggered`/`clicked`/`activated`
hívás és nincs `.emit()`. A párbeszédek takarításához a `close` hívás szabad.
"""

from __future__ import annotations

import pytest
from PySide6.QtCore import QObject, QSettings, QUrl, Slot
from PySide6.QtGui import QDesktopServices

from conftest import _build_qml_app
from tests.app.qml_functional._fomenu_4420_menu import _megnyit
from tests.app.qml_functional.test_menu_talca_egyeb_valodi_5135 import (
    _menupont_kattintasa,
)
from tests.app.qml_functional.test_menu_talca_egyeb_valodi_5135_b import (
    _elokeszit,
    _gyerek,
    _keszits_konyvtarat,
    _klikk_ablakban,
    _latszik,
    _valassz_legordulobol,
    _varj,
    _vizualis_bejaras,
    _zar,
)
from tests.app.qml_functional.test_parbeszedek_valodi_5150_b import (
    _beallitasok_megnyit,
    _fulre_kattint,
)


@pytest.fixture
def parbeszed_app(qt_app, tmp_path):
    yield from _build_qml_app(
        qt_app,
        tmp_path,
        kepeket_keszit=_keszits_konyvtarat,
    )


def _vizualis(window, nev: str):
    """Az elem a VIZUÁLIS fában: az ismétlő (Repeater) elemeinek nincs QObject-szülőjük."""
    for elem in _vizualis_bejaras(window.contentItem()):
        if elem.objectName() == nev:
            return elem
    raise AssertionError(f"{nev} nem található a vizuális fában")


class _UrlFogo(QObject):
    """A `https` séma kezelője a teszt idejére: a kért címeket eltárolja."""

    def __init__(self) -> None:
        super().__init__()
        self.cimek: list[str] = []

    @Slot(QUrl)
    def kezel(self, url: QUrl) -> None:  # noqa: D102 - a Qt hívja
        self.cimek.append(url.toString())


class TestAltalanosFul:
    def test_a_torles_megerosites_jelolo_valodi_kattintassal_a_tarba_ir(
        self, parbeszed_app, qt_app
    ):
        window, controller, engine = parbeszed_app
        _elokeszit(window, qt_app, controller)
        beallitasok = _beallitasok_megnyit(window, qt_app)
        tar = engine.rootContext().contextProperty("confirmSettings")
        jelolo = _gyerek(beallitasok, "optionsSkipDeleteConfirmCheck")
        elotte = tar.isSuppressed("delete")

        _klikk_ablakban(qt_app, beallitasok, jelolo)

        assert _varj(qt_app, lambda: tar.isSuppressed("delete") is not elotte), (
            "a törlés-megerősítés jelölője nem írta a tárba az állapotot"
        )
        _zar(qt_app, beallitasok)

    def test_a_duplikatumok_jelolo_valodi_kattintassal_az_importalot_allitja(
        self, parbeszed_app, qt_app
    ):
        window, controller, engine = parbeszed_app
        _elokeszit(window, qt_app, controller)
        beallitasok = _beallitasok_megnyit(window, qt_app)
        importer = engine.rootContext().contextProperty("importSourceController")
        elotte = bool(importer.property("autoExclude"))

        _klikk_ablakban(qt_app, beallitasok, _gyerek(beallitasok, "optionsAutoExcludeCheck"))

        assert _varj(qt_app, lambda: bool(importer.property("autoExclude")) is not elotte), (
            "a Duplikátumok felismerése jelölő nem állította az importálót"
        )
        _zar(qt_app, beallitasok)

    def test_a_duplikatumok_jelolo_valodi_kattintassal_menti_az_erteket(
        self, parbeszed_app, qt_app
    ):
        """#5473: a valódi kattintás a Duplikátumok jelölőn a közös
        `import/autoexclude` kulcsot is átírja, és a lemezre kerül. A kiindulást
        a teszt maga állítja be: a beállítás-tár a teszt-munkamenetben közös,
        tehát a korábbi tesztek maradékára nem szabad hagyatkozni."""
        window, controller, engine = parbeszed_app
        _elokeszit(window, qt_app, controller)
        importer = engine.rootContext().contextProperty("importSourceController")
        importer.setAutoExclude(True)
        beallitasok = _beallitasok_megnyit(window, qt_app)
        jelolo = _gyerek(beallitasok, "optionsAutoExcludeCheck")
        assert jelolo.property("checked") is True, (
            "a Duplikátumok jelölő nem a bekapcsolt állapotot mutatja"
        )

        _klikk_ablakban(qt_app, beallitasok, jelolo)

        assert _varj(qt_app, lambda: jelolo.property("checked") is False), (
            "a kattintás nem kapcsolta ki a Duplikátumok jelölőt"
        )
        # a sync kiírja az importáló tárát a lemezre; az új példány már onnan olvas
        importer._get_settings().sync()
        assert QSettings("PicasaPy", "PicasaPy").value("import/autoexclude") == "false", (
            "a kikapcsolt Duplikátumok jelölő értéke nem került a lemezre"
        )
        _zar(qt_app, beallitasok)

    def test_a_statisztika_jelolo_tiltott_a_kattintas_nem_valt(self, parbeszed_app, qt_app):
        window, controller, _engine = parbeszed_app
        _elokeszit(window, qt_app, controller)
        beallitasok = _beallitasok_megnyit(window, qt_app)
        jelolo = _gyerek(beallitasok, "optionsUsageStatsCheck")
        assert jelolo.property("enabled") is False, "a statisztika jelölőnek tiltottnak kell lennie"
        elotte = jelolo.property("checked")

        _klikk_ablakban(qt_app, beallitasok, jelolo)

        assert jelolo.property("checked") == elotte, "a tiltott statisztika jelölő átváltott"
        _zar(qt_app, beallitasok)

    def test_az_adatvedelem_hivatkozas_valodi_kattintassal_a_bongeszot_hivna(
        self, parbeszed_app, qt_app
    ):
        window, controller, _engine = parbeszed_app
        _elokeszit(window, qt_app, controller)
        beallitasok = _beallitasok_megnyit(window, qt_app)
        fogo = _UrlFogo()
        # a böngésző helyettesítője: a Qt URL-kezelője a fogót hívja, nem indít programot
        QDesktopServices.setUrlHandler("https", fogo, "kezel")
        try:
            _klikk_ablakban(qt_app, beallitasok, _gyerek(beallitasok, "optionsPrivacyLink"))
            assert _varj(qt_app, lambda: len(fogo.cimek) == 1), (
                "az Adatvédelem hivatkozás nem adta át a címet a böngészőnek"
            )
        finally:
            QDesktopServices.unsetUrlHandler("https")
        assert fogo.cimek == ["https://policies.google.com/privacy"]
        _zar(qt_app, beallitasok)


class TestHalozatFul:
    def test_a_tiltott_proxy_jelolo_kattintasa_nem_valt(self, parbeszed_app, qt_app):
        window, controller, _engine = parbeszed_app
        _elokeszit(window, qt_app, controller)
        beallitasok = _beallitasok_megnyit(window, qt_app)
        _fulre_kattint(qt_app, beallitasok, "optionsTabNetwork", 5)
        jelolo = _gyerek(beallitasok, "optionsNetworkAutoDetectCheck")
        assert jelolo.property("enabled") is False, "a proxy-csoport nincs tiltva"
        elotte = jelolo.property("checked")

        _klikk_ablakban(qt_app, beallitasok, jelolo)

        assert jelolo.property("checked") == elotte, "a tiltott proxy-jelölő átváltott"
        _zar(qt_app, beallitasok)


class TestWebAlbumsFul:
    @pytest.mark.parametrize(
        "nev",
        [
            "optionsWebStripedUploadCheck",
            "optionsWebKeepJpegQualityCheck",
            "optionsWebConfirmSyncDisableCheck",
        ],
    )
    def test_a_tiltott_fulon_a_jelolo_kattintasa_nem_valt(self, parbeszed_app, qt_app, nev):
        window, controller, _engine = parbeszed_app
        _elokeszit(window, qt_app, controller)
        beallitasok = _beallitasok_megnyit(window, qt_app)
        _fulre_kattint(qt_app, beallitasok, "optionsTabWebAlbums", 6)
        jelolo = _gyerek(beallitasok, nev)
        assert jelolo.property("enabled") is False, "a Web Albums fül tiltott"
        elotte = jelolo.property("checked")

        _klikk_ablakban(qt_app, beallitasok, jelolo)

        assert jelolo.property("checked") == elotte, f"{nev}: a tiltott jelölő átváltott"
        _zar(qt_app, beallitasok)


class TestFajltipusok:
    @pytest.mark.parametrize(
        ("nev", "csoport"),
        [
            ("optionsFileTypeBmpCheck", "bmp"),
            ("optionsFileTypeGifCheck", "gif"),
            ("optionsFileTypePngCheck", "png"),
            ("optionsFileTypeTgaCheck", "tga"),
            ("optionsFileTypeTiffCheck", "tiff"),
            ("optionsFileTypeWebpCheck", "webp"),
            ("optionsFileTypePsdCheck", "psd"),
            ("optionsFileTypeMoviesCheck", "movies"),
            ("optionsFileTypeQuickTimeCheck", "quicktime"),
        ],
    )
    def test_a_fajltipus_jelolo_valodi_kattintassal_atvalt_es_a_vezerlo_is(
        self, parbeszed_app, qt_app, nev, csoport
    ):
        window, controller, _engine = parbeszed_app
        _elokeszit(window, qt_app, controller)
        beallitasok = _beallitasok_megnyit(window, qt_app)
        _fulre_kattint(qt_app, beallitasok, "optionsTabFileTypes", 2)
        jelolo = _gyerek(beallitasok, nev)
        elotte = bool(controller.fileTypeEnabled(csoport))
        assert jelolo.property("checked") is elotte, "a próba feltétele: a jelölő a vezérlőt mutatja"

        _klikk_ablakban(qt_app, beallitasok, jelolo)

        assert _varj(qt_app, lambda: bool(controller.fileTypeEnabled(csoport)) is not elotte), (
            f"{nev}: a kattintás nem állította a(z) {csoport} típust"
        )
        assert jelolo.property("checked") is not elotte
        _zar(qt_app, beallitasok)


class TestNyomtatasFul:
    def test_a_gyorsgomb_legorulo_valodi_kattintassal_uj_meretet_valaszt(
        self, parbeszed_app, qt_app
    ):
        window, controller, engine = parbeszed_app
        _elokeszit(window, qt_app, controller)
        beallitasok = _beallitasok_megnyit(window, qt_app)
        _fulre_kattint(qt_app, beallitasok, "optionsTabPrinting", 4)
        legordulo = _vizualis(beallitasok, "optionsPrintSizeCombo0")
        nyomtatas = engine.rootContext().contextProperty("printController")
        elotte_meret = nyomtatas.printSizePresets()[0]
        cimkek = list(legordulo.property("model"))
        kovetkezo = (legordulo.property("currentIndex") + 1) % len(cimkek)

        _valassz_legordulobol(qt_app, beallitasok, legordulo, cimkek[kovetkezo])

        assert _varj(qt_app, lambda: legordulo.property("currentIndex") == kovetkezo), (
            "a gyorsgomb-legördülő valódi kattintása nem váltott tételt"
        )
        assert _varj(qt_app, lambda: nyomtatas.printSizePresets()[0] != elotte_meret), (
            "az új gyorsgomb-méret nem jutott el a nyomtatási beállításig"
        )
        _zar(qt_app, beallitasok)


def _export_megnyit(window, qt_app):
    """Fájl ▸ Export Picture to Folder… valódi kattintással; visszaadja a párbeszédet."""
    menu_bar = window.property("menuBar")
    _megnyit(menu_bar, qt_app, "&File")
    _menupont_kattintasa(window, qt_app, "menuFileExport")
    assert _varj(qt_app, lambda: _latszik(window, "exportDialog")), (
        "a Fájl ▸ Export Picture to Folder… nem nyitotta meg az exportot"
    )
    return _gyerek(window, "exportDialog")


class TestExportParbeszed:
    def test_a_szamozas_jelolo_valodi_kattintassal_atvalt(self, parbeszed_app, qt_app):
        window, controller, _engine = parbeszed_app
        _elokeszit(window, qt_app, controller)
        dialog = _export_megnyit(window, qt_app)
        jelolo = _gyerek(dialog, "exportAddNumbersCheck")
        elotte = jelolo.property("checked")

        _klikk_ablakban(qt_app, window, jelolo)

        assert _varj(qt_app, lambda: jelolo.property("checked") is not elotte), (
            "a számozás jelölő kattintása nem váltott"
        )
        _zar(qt_app, dialog)

    def test_az_atmeretezes_radio_valodi_kattintassal_engedelyezi_a_meretsort(
        self, parbeszed_app, qt_app
    ):
        window, controller, _engine = parbeszed_app
        _elokeszit(window, qt_app, controller)
        dialog = _export_megnyit(window, qt_app)
        sor = _gyerek(dialog, "exportSizeRow")
        assert sor.property("enabled") is False, "az eredeti méret az alapérték"

        _klikk_ablakban(qt_app, window, _gyerek(dialog, "exportSizeResizeRadio"))

        assert _varj(qt_app, lambda: sor.property("enabled") is True), (
            "az Átméretezés radio kattintása nem engedélyezte a méretsort"
        )
        assert _gyerek(dialog, "exportSizeResizeRadio").property("checked") is True
        _klikk_ablakban(qt_app, window, _gyerek(dialog, "exportSizeOriginalRadio"))
        assert _varj(qt_app, lambda: sor.property("enabled") is False), (
            "az Eredeti méret radio kattintása nem tiltotta le a méretsort"
        )
        _zar(qt_app, dialog)

    def test_a_film_radio_tiltott_film_nelkul_valodi_kattintassal_mentes_utan_valt(
        self, parbeszed_app, qt_app
    ):
        window, controller, _engine = parbeszed_app
        _elokeszit(window, qt_app, controller)
        dialog = _export_megnyit(window, qt_app)
        teljes = _gyerek(dialog, "exportMovieFull")
        elso = _gyerek(dialog, "exportMovieFirstFrame")
        assert teljes.property("enabled") is False, "film nélkül a film-választónak tiltottnak kell lennie"

        _klikk_ablakban(qt_app, window, teljes)
        assert teljes.property("checked") is False, "a tiltott film-radio átváltott"

        # előkészítés: a kijelölésben van film (a párbeszéd saját jelzője)
        dialog.setProperty("hasVideo", True)
        assert _varj(qt_app, lambda: teljes.property("enabled") is True)
        _klikk_ablakban(qt_app, window, teljes)
        assert _varj(qt_app, lambda: teljes.property("checked") is True), (
            "a Teljes film kattintás nem jelölte ki a radiót"
        )
        assert elso.property("checked") is False
        _klikk_ablakban(qt_app, window, elso)
        assert _varj(qt_app, lambda: elso.property("checked") is True), (
            "az Első képkocka kattintás nem jelölte ki a radiót"
        )
        assert teljes.property("checked") is False
        _zar(qt_app, dialog)

    def test_a_vizjel_jelolo_valodi_kattintassal_engedelyezi_a_mezot(
        self, parbeszed_app, qt_app
    ):
        window, controller, _engine = parbeszed_app
        _elokeszit(window, qt_app, controller)
        dialog = _export_megnyit(window, qt_app)
        mezo = _gyerek(dialog, "exportWatermarkField")
        assert mezo.property("enabled") is False, "a vízjel-mező jelölés nélkül tiltott"

        _klikk_ablakban(qt_app, window, _gyerek(dialog, "exportWatermarkCheck"))

        assert _varj(qt_app, lambda: mezo.property("enabled") is True), (
            "a Vízjel jelölő kattintása nem engedélyezte a mezőt"
        )
        _zar(qt_app, dialog)
