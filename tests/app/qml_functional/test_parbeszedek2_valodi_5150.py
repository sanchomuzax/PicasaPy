"""Az „Egyéb" maradék párbeszédei VALÓDI egérkattintással (#5150, 11. rész, 1. fájl).

A B-lista eddig nem érintett párbeszédei, első fele: a tömörítés, a
duplikátum-kezelő, a felülírt szerkesztések, az ütköző fájlnevek és a
Picasa-import. Minden tétel valódi `QTest.mouseClick`-kel indul; a hatást a
párbeszéd láthatóságán, a listáján és a lemezen mérjük.

Lefedve:
- `CompactDatabaseDialog` (Eszközök ▸ Compact Database): `compactCancelButton`
  (nincs futó tömörítés, a felirat Bezárás - a kattintás elrejti az ablakot).
- `DedupDialog` (Eszközök ▸ Show Duplicate Files): `dedupCloseButton`.
- `EditOverwriteDialog` (a controller `editsOverwritten` jelzése nyitja, ahogy
  a Main.qml-ben): `editOverwriteRestoreButton` (a lista kiürül, bezárul),
  `editOverwriteCloseButton` (ugyanez elvetéssel).
- `FileOpsDialogs` ütközési kérdése (`duplicateNamesDialog`): `duplicateRenameButton`
  (az ütköző fájl `-1` végződéssel landol a célban), `duplicateSkipButton`
  (a forrás helyben marad). A kérdést a `startBatch` nyitja, ahogy a
  áthelyezés után történik; a két gombot valódi kattintás viszi.
- `PicasaImportDialog` (`openAndDiscover`, a felderítés helyettesítve):
  `picasaImportAdoptButton` (a mappa a figyelt gyökerekbe kerül).

Parancsot közvetlenül nem indítunk: nincs `triggered`/`clicked`/`activated`
hívás és nincs `.emit()` a tesztelt vezérlőn. A jelzés, amely a párbeszédet
nyitja, a controller saját `editsOverwritten` jelzése (előkészítés).
"""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import Q_ARG, QMetaObject, QObject, Qt
from PySide6.QtQuick import QQuickWindow

from conftest import _build_qml_app
from support.jpeg_factory import make_jpeg
from tests.app.qml_functional._fomenu_4420_menu import _megnyit
from tests.app.qml_functional.test_menu_talca_egyeb_valodi_5135 import (
    _almenu_megnyitasa,
    _menupont_kattintasa,
)
from tests.app.qml_functional._racs_helyimenuk_5150_helpers import kattints
from tests.app.qml_functional.test_menu_talca_egyeb_valodi_5135_b import (
    _elokeszit,
    _gyerek,
    _keszits_konyvtarat,
    _klikk_ablakban,
    _latszik,
    _varj,
    _vizualis_bejaras,
)


@pytest.fixture
def parbeszed_app(qt_app, tmp_path):
    """Az app és a duplikátum-kezelő hídja (a DedupDialog a `dedupController`-t várja)."""
    from picasapy.app.application import wire_dedup
    from picasapy.app.dedup_controller import DedupController
    from picasapy.app.thumbnail_provider import ThumbnailProvider
    from picasapy.thumbs import ThumbnailCache

    epites = _build_qml_app(qt_app, tmp_path, kepeket_keszit=_keszits_konyvtarat)
    window, controller, engine = next(epites)
    dedup = DedupController(
        tmp_path / "index.db",
        ThumbnailProvider(ThumbnailCache(tmp_path / "thumbs", size=32)),
    )
    wire_dedup(dedup, controller)
    engine.rootContext().setContextProperty("dedupController", dedup)
    yield window, controller, engine
    yield from epites


def _lista(ertek) -> list:
    """A QML-tömb Python listaként (a QVariant és a QJSValue alakját is kezeli)."""
    return list(ertek.toVariant() if hasattr(ertek, "toVariant") else ertek)


def _bool(ertek) -> bool:
    """QSettings-érték (bool vagy szöveg) logikai értékként."""
    return ertek in (True, 1, "true", "1")


def _aktival(qt_app, ablak) -> None:
    """Önálló ablak aktiválása a kattintás előtt.

    Az aktiválás nélküli első kattintás egy külön ablakban elveszhet, ezért
    megvárjuk, hogy az ablak `active` lett.
    """
    ablak.requestActivate()
    assert _varj(qt_app, lambda: ablak.property("active") is True), (
        "az ablak nem aktiválódott"
    )


def _kiserleti_menupont(window, qt_app, tetel: str) -> None:
    """Eszközök ▸ Experimental ▸ `tetel`, valódi kattintásokkal."""
    menu_bar = window.property("menuBar")
    menu = _megnyit(menu_bar, qt_app, "&Tools")
    _almenu_megnyitasa(menu_bar, qt_app, menu, "Experimental")
    _menupont_kattintasa(window, qt_app, tetel)


def _ablak(window, nev: str) -> QQuickWindow:
    """Önálló (Window típusú) párbeszéd; a `findChild` típusos, hogy az `active` elérhető legyen."""
    ablak = window.findChild(QQuickWindow, nev)
    assert ablak is not None, f"{nev} nem önálló ablak"
    return ablak


class TestTomorites:
    def test_a_bezaras_valodi_kattintassal_elrejti_az_ablakot(self, parbeszed_app, qt_app):
        window, controller, _engine = parbeszed_app
        _elokeszit(window, qt_app, controller)
        _kiserleti_menupont(window, qt_app, "menuToolsCompactDatabase")
        assert _varj(qt_app, lambda: _latszik(window, "compactDatabaseDialog")), (
            "az Eszközök ▸ Compact Database nem nyitotta meg az ablakot"
        )
        ablak = _ablak(window, "compactDatabaseDialog")
        _aktival(qt_app, ablak)
        gomb = _gyerek(window, "compactCancelButton")
        # nincs futó tömörítés, ezért a gomb Bezárás (nem Mégse)
        assert gomb.property("text") in ("Close", "Bezárás")

        _klikk_ablakban(qt_app, ablak, gomb)

        assert _varj(qt_app, lambda: ablak.property("visible") is False), (
            "a Bezárás valódi kattintás nem zárta be a tömörítés ablakát"
        )


class TestDuplikatumKezelo:
    def test_a_bezaras_valodi_kattintassal_zarja_a_duplikatum_ablakot(
        self, parbeszed_app, qt_app
    ):
        window, controller, _engine = parbeszed_app
        _elokeszit(window, qt_app, controller)
        # a „Show Duplicate Files" a keresési módot kapcsolja; a kezelőt a
        # „Manage Duplicates…" tétel nyitja
        _kiserleti_menupont(window, qt_app, "menuToolsDedupManager")
        assert _varj(qt_app, lambda: _latszik(window, "dedupDialog")), (
            "az Eszközök ▸ Manage Duplicates… nem nyitotta meg az ablakot"
        )
        ablak = _ablak(window, "dedupDialog")
        _aktival(qt_app, ablak)

        _klikk_ablakban(qt_app, ablak, _gyerek(window, "dedupCloseButton"))

        assert _varj(qt_app, lambda: ablak.property("visible") is False), (
            "a Bezárás valódi kattintás nem zárta be a duplikátum-ablakot"
        )


class TestFelulirtSzerkesztes:
    def _nyit(self, window, qt_app, controller, lib: Path) -> object:
        """A másik program felülírása: a controller jelzése nyitja a párbeszédet."""
        lost = [{"path": str(lib / "fotok" / "a_elso.jpg"), "name": "a_elso.jpg", "chain": "sepia=1;"}]
        controller.editsOverwritten.emit(lost)  # előkészítés: a jelzés a Main.qml-hez fut be
        assert _varj(qt_app, lambda: _latszik(window, "editOverwriteDialog")), (
            "a felülírt szerkesztések párbeszéde nem nyílt meg"
        )
        _aktival(qt_app, window)
        ablak = _gyerek(window, "editOverwriteDialog")
        assert len(_lista(ablak.property("items"))) == 1
        return ablak

    def test_a_visszaallitas_valodi_kattintassal_uriti_a_listat_es_bezarul(
        self, parbeszed_app, qt_app
    ):
        window, controller, _engine = parbeszed_app
        _elokeszit(window, qt_app, controller)
        ablak = self._nyit(window, qt_app, controller, Path(controller.watchedFolders[0]))

        _klikk_ablakban(qt_app, window, _gyerek(window, "editOverwriteRestoreButton"))

        assert _varj(qt_app, lambda: ablak.property("visible") is False), (
            "a Visszaállítás nem zárta be a párbeszédet"
        )
        assert _lista(ablak.property("items")) == [], (
            "a Visszaállítás után a felülírt lista nem ürült ki"
        )

    def test_a_bezaras_valodi_kattintassal_uriti_a_listat(self, parbeszed_app, qt_app):
        window, controller, _engine = parbeszed_app
        _elokeszit(window, qt_app, controller)
        ablak = self._nyit(window, qt_app, controller, Path(controller.watchedFolders[0]))

        _klikk_ablakban(qt_app, window, _gyerek(window, "editOverwriteCloseButton"))

        assert _varj(qt_app, lambda: ablak.property("visible") is False), (
            "a Bezárás nem zárta be a párbeszédet"
        )
        assert _lista(ablak.property("items")) == [], (
            "a Bezárás után a felülírt lista nem ürült ki"
        )


def _fileops(window):
    """A FileOpsDialogs építése a burok `ensure()`-jével, majd a belső elem.

    A burok halasztott: az `ensure()` nélkül a `startBatch` nem található.
    """
    burok = window.findChild(QObject, "fileOpsDialogs")
    assert burok is not None, "a fileOpsDialogs burok nincs meg"
    assert QMetaObject.invokeMethod(burok, "ensure"), "az ensure() nem hívható"
    elem = window.findChild(QObject, "fileOpsDialogsItem")
    assert elem is not None, "az ensure() nem építette fel a párbeszédeket"
    return elem


class TestUtkozoFajlnevek:
    """Az áthelyezés ütköző nevet talál, és a kérdés gombjai döntenek."""

    def _kerdes_nyit(self, window, qt_app, lib: Path) -> tuple[Path, Path]:
        """A célmappában már van `a_elso.jpg`; az áthelyezés indul, a kérdés nyílik."""
        cel = lib.parent / "cel"
        cel.mkdir()
        make_jpeg(cel / "a_elso.jpg", size=(64, 48))
        forras = lib / "fotok" / "a_elso.jpg"
        # előkészítés: a köteg indítása, ahogy az áthelyezés teszi
        QMetaObject.invokeMethod(
            _fileops(window),
            "startBatch",
            Qt.ConnectionType.DirectConnection,
            Q_ARG("QVariant", "move"),
            Q_ARG("QVariant", [str(forras)]),
            Q_ARG("QVariant", str(cel)),
        )
        assert _varj(qt_app, lambda: _latszik(window, "duplicateNamesDialog")), (
            "az ütköző fájlnév kérdése nem nyílt meg"
        )
        return forras, cel

    def test_az_atnevezes_valodi_kattintassal_az_utkozo_fajlt_ujra_nevezi(
        self, parbeszed_app, qt_app
    ):
        window, controller, _engine = parbeszed_app
        _elokeszit(window, qt_app, controller)
        forras, cel = self._kerdes_nyit(window, qt_app, Path(controller.watchedFolders[0]))
        _aktival(qt_app, window)

        _klikk_ablakban(qt_app, window, _gyerek(window, "duplicateRenameButton"))

        assert _varj(qt_app, lambda: not forras.exists()), (
            "az Átnevezés nem mozgatta át a forrásfájlt"
        )
        assert (cel / "a_elso-1.jpg").exists(), "az ütköző fájl nem kapott -1 végződést"

    def test_a_kihagyas_valodi_kattintassal_helyben_hagyja_a_forrast(
        self, parbeszed_app, qt_app
    ):
        window, controller, _engine = parbeszed_app
        _elokeszit(window, qt_app, controller)
        forras, cel = self._kerdes_nyit(window, qt_app, Path(controller.watchedFolders[0]))
        ablak = _gyerek(window, "duplicateNamesDialog")
        _aktival(qt_app, window)

        _klikk_ablakban(qt_app, window, _gyerek(window, "duplicateSkipButton"))

        assert _varj(qt_app, lambda: ablak.property("visible") is False), (
            "a Kihagyás nem zárta be a kérdést"
        )
        assert forras.exists(), "a Kihagyás után a forrásfájl eltűnt"
        assert not (cel / "a_elso-1.jpg").exists(), "a Kihagyás mégis másolatot készített"


class TestPicasaImport:
    def test_a_hozzaadas_valodi_kattintassal_felveszi_a_felderitett_mappat(
        self, parbeszed_app, qt_app, monkeypatch, tmp_path
    ):
        window, controller, _engine = parbeszed_app
        from picasapy.scanner import PicasaInstallation

        uj_mappa = tmp_path / "atvett-mappa"
        uj_mappa.mkdir()
        installation = PicasaInstallation("Kézi mappa", None, None, None)
        # a felderítés helyettesítve: a valódi keresés a felhasználó gépét járná be
        monkeypatch.setattr(
            "picasapy.app.discovery_controller.discover_installations",
            lambda: (installation,),
        )
        monkeypatch.setattr(
            "picasapy.app.discovery_controller.propose_watched_folders",
            lambda inst, remap: (str(uj_mappa),),
        )
        _elokeszit(window, qt_app, controller)
        ablak = _gyerek(window, "picasaImportDialog")
        QMetaObject.invokeMethod(ablak, "openAndDiscover", Qt.ConnectionType.DirectConnection)
        lista = _gyerek(window, "picasaImportFolderList")
        assert _varj(qt_app, lambda: lista.property("count") == 1), (
            "a felderítés nem adta vissza a mappát"
        )
        _aktival(qt_app, window)

        _klikk_ablakban(qt_app, window, _gyerek(window, "picasaImportAdoptButton"))

        assert _varj(
            qt_app,
            lambda: any(Path(str(f)) == uj_mappa for f in controller.watchedFolders),
        ), "a Hozzáadás valódi kattintás nem vette fel a mappát a figyeltek közé"
        assert _varj(qt_app, lambda: ablak.property("visible") is False), (
            "a Hozzáadás után az importáló párbeszéd nem zárult be"
        )


def _menutetel_keres(window, szoveg: str):
    """A legördülő nyitott listájának `szoveg` tétele (MenuItem), a VIZUÁLIS fában, láthatóan."""
    for elem in _vizualis_bejaras(window.contentItem()):
        if (
            "MenuItem" in elem.metaObject().className()
            and elem.property("text") == szoveg
            and elem.isVisible()
        ):
            return elem
    return None


def _legordulo_valaszt(window, qt_app, legordulo, szoveg: str) -> None:
    """Valódi kattintás a legördülőn, majd valódi kattintás a `szoveg` tételen."""
    _klikk_ablakban(qt_app, window, legordulo)
    assert _varj(qt_app, lambda: _menutetel_keres(window, szoveg) is not None), (
        f"a legördülő nem nyílt meg, vagy nincs rajta: {szoveg!r}"
    )
    kattints(window, qt_app, _menutetel_keres(window, szoveg))


class TestKepernyovedo:
    def _megnyit_a_beallitast(self, window, qt_app):
        menu_bar = window.property("menuBar")
        _megnyit(menu_bar, qt_app, "&Tools")
        _menupont_kattintasa(window, qt_app, "menuToolsScreensaver")
        assert _varj(qt_app, lambda: _latszik(window, "screensaverDialog")), (
            "az Eszközök ▸ Configure Screensaver nem nyitotta meg a beállítást"
        )
        return _gyerek(window, "screensaverDialog")

    def test_a_hatas_legordulo_valodi_valasztasa_a_beallitasba_kerul(
        self, parbeszed_app, qt_app  # noqa: F811
    ):
        window, controller, _engine = parbeszed_app
        dialog = self._megnyit_a_beallitast(window, qt_app)
        effektek = _lista(dialog.property("effects"))
        valasztott = effektek[1]
        legordulo = _gyerek(window, "screensaverEffectBox")

        _legordulo_valaszt(window, qt_app, legordulo, valasztott["label"])

        assert _varj(
            qt_app,
            lambda: controller._settings.value("screensaver/effect") == valasztott["key"],
        ), "a hatás-választás valódi kattintása nem került a beállításba"

    def test_a_feliratok_jelolo_valodi_kattintassal_a_beallitasba_kerul(
        self, parbeszed_app, qt_app  # noqa: F811
    ):
        window, controller, _engine = parbeszed_app
        self._megnyit_a_beallitast(window, qt_app)
        jelolo = _gyerek(window, "screensaverCaptionCheck")
        elotte = bool(jelolo.property("checked"))
        # előkészítés: a beállítás a jelölő mostani állapotán áll, hogy a kattintás
        # váltását lehessen mérni (különben egy alapértéken álló beállítás hamis zöldet adna)
        controller.setScreensaverShowCaptions(elotte)
        controller._settings.sync()
        assert _bool(controller._settings.value("screensaver/showCaptions")) is elotte

        _klikk_ablakban(qt_app, window, jelolo)

        assert _varj(qt_app, lambda: jelolo.property("checked") is (not elotte))
        assert _varj(
            qt_app,
            lambda: _bool(controller._settings.value("screensaver/showCaptions"))
            is (not elotte),
        ), "a Feliratok jelölő kattintása nem került a beállításba"
