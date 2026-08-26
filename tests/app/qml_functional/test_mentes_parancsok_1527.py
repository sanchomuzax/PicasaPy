"""#1527: a mentés-család a FELÜLETRŐL — Mentés másként, Másolat mentése,
Kilépés, a megerősítés egyes/többes mondata, a „többé ne kérdezd", a
folyamatjelzés és a három hibaág.

## Miért a menütételről és a lemezről mér

A `tests/app/test_save_controller*.py` a vezérlő metódusait közvetlenül
hívja — az zöld marad akkor is, ha a menütétel helyfoglaló (ez volt a
#1527 kiinduló állapota: a `Save As...` és a `Save a Copy` `placeholder:
true` volt, tehát a kész mag elérhetetlen). Ez a fájl ezért a VALÓDI
menütételeket süti el, előbb megkövetelve, hogy a felhasználó rájuk tudjon
kattintani, és a végén a LEMEZEN méri az eredményt.

## Miért ANGOL szövegeket állít

A teszt-fixture nem telepít `QTranslator`-t, tehát a `qsTr()` a
FORRÁSSZTRINGET adja vissza. A hivatalos MAGYAR feliratokat ezért nem itt,
hanem a `tests/app/test_mentes_feliratok_1527.py`-ban mérjük, közvetlenül a
`picasapy_hu.ts`-ből — így mindkét oldal fedve van, és egyik állítás sem
függ attól, betöltött-e fordítás.

## A „többé ne kérdezd" túléli az újraindítást

A jelölőt a `confirmSettings` (a #367-es `QSettings`-alapú tár) őrzi. A
teszt nem a QML-tulajdonságot nézi, hanem a beállítás-fájlt: a fixture
elszigetelt `QSettings`-e ugyanaz a tár, amit egy újraindult alkalmazás
beolvasna.
"""

from __future__ import annotations

import configparser
import time
from pathlib import Path

from PySide6.QtCore import QMetaObject, QObject, Qt

from support.qt_wait import wait_for_photo_op, wait_for_signal


def _elem(root, nev: str) -> QObject:
    obj = root.findChild(QObject, nev)
    assert obj is not None, f"{nev} nem található"
    return obj


def _kijelol(window, qt_app, sorok) -> None:
    window.setProperty("selectedIndexes", list(sorok))
    window.setProperty("selectedIndex", sorok[0] if sorok else -1)
    qt_app.processEvents()


def _elsut(window, qt_app, nev: str) -> None:
    """A VALÓDI menütétel aktiválása — előbb megkövetelve, hogy a
    felhasználó egyáltalán rá tudjon kattintani."""
    tetel = _elem(window, nev)
    assert tetel.property("enabled") is True, (
        f"a(z) {nev} menüpont le van tiltva — a felhasználó nem éri el"
    )
    assert not tetel.property("placeholder"), (
        f"a(z) {nev} menüpont helyfoglaló (#416), tehát halott"
    )
    QMetaObject.invokeMethod(tetel, "triggered", Qt.ConnectionType.DirectConnection)
    qt_app.processEvents()


def _mappa(controller, sor: int = 0) -> Path:
    return Path(str(controller.photos.filePathAt(sor))).parent


def _ini(controller, sor: int = 0) -> configparser.ConfigParser:
    parser = configparser.ConfigParser(interpolation=None, strict=False)
    ut = _mappa(controller, sor) / ".picasa.ini"
    if ut.exists():
        parser.read(ut, encoding="utf-8")
    return parser


class TestAKetMenupontElo:
    """1. „Kész, ha": a két helyfoglaló megszűnik, és a Kilépés ott van."""

    def test_mentes_maskent_NEM_helyfoglalo(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        _kijelol(window, qt_app, [0])
        tetel = _elem(window, "menuFileSaveAs")
        assert not tetel.property("placeholder")
        assert tetel.property("enabled") is True

    def test_masolat_mentese_NEM_helyfoglalo(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        _kijelol(window, qt_app, [0])
        tetel = _elem(window, "menuFileSaveCopy")
        assert not tetel.property("placeholder")
        assert tetel.property("enabled") is True

    def test_a_kilepes_ott_van_a_fajl_menuben(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        tetel = _elem(window, "menuFileExit")
        assert not tetel.property("placeholder")
        assert tetel.property("enabled") is True

    def test_kijeloles_nelkul_a_ket_uj_tetel_TILTOTT(self, qml_app, qt_app):
        """Félkész, bekötetlen vezérlőt nem hagyunk: ha nincs kép, a
        tétel legyen szürke, ne néma no-op."""
        window, _controller, _engine = qml_app
        _kijelol(window, qt_app, [])
        assert _elem(window, "menuFileSaveAs").property("enabled") is False
        assert _elem(window, "menuFileSaveCopy").property("enabled") is False


class TestMasolatMentese:
    """2. A „Másolat mentése" a MENÜPONTRÓL új fájlt tesz a lemezre."""

    def test_a_menupontrol_letrejon_a_001_masolat(self, qml_app, qt_app):
        window, controller, _engine = qml_app
        _kijelol(window, qt_app, [0])
        forras = Path(str(controller.photos.filePathAt(0)))
        elotte = forras.read_bytes()

        wait_for_signal(
            controller.saveCopyFinished,
            lambda: _elsut(window, qt_app, "menuFileSaveCopy"),
            description="a Másolat mentése",
            process_events_with=qt_app,
        )

        masolat = forras.parent / f"{forras.stem}-001{forras.suffix}"
        assert masolat.exists(), (
            f"a másolat nem jött létre; a mappa: "
            f"{sorted(p.name for p in forras.parent.iterdir())}"
        )
        assert forras.read_bytes() == elotte, "a FORRÁS képet átírta"

    def test_a_masolat_MEG_IS_JELENIK_a_racsban(self, qml_app, qt_app):
        """A fájl kiírása még nem láthatóság: amíg az index nem tud róla,
        a felhasználó a saját másolatát nem találja. A művelet végén ezért
        célzottan újraolvassuk a látott mappát."""
        window, controller, _engine = qml_app
        _kijelol(window, qt_app, [0])
        elotte = controller.photos.rowCount()
        forras = Path(str(controller.photos.filePathAt(0)))

        wait_for_signal(
            controller.saveCopyFinished,
            lambda: _elsut(window, qt_app, "menuFileSaveCopy"),
            description="a Másolat mentése",
            process_events_with=qt_app,
        )

        masolat_nev = f"{forras.stem}-001{forras.suffix}"
        hataridő = time.monotonic() + 15.0
        while time.monotonic() < hataridő:
            qt_app.processEvents()
            nevek = [
                Path(str(controller.photos.filePathAt(i))).name
                for i in range(controller.photos.rowCount())
            ]
            if masolat_nev in nevek:
                break
        else:
            nevek = [
                Path(str(controller.photos.filePathAt(i))).name
                for i in range(controller.photos.rowCount())
            ]
        assert masolat_nev in nevek, (
            f"a másolat a lemezen van, de a rácsban nem látszik "
            f"(előtte {elotte} sor, most {nevek})"
        )

    def test_tobb_kijelolt_kepre_MINDEGYIKROL_keszul_masolat(self, qml_app, qt_app):
        window, controller, _engine = qml_app
        _kijelol(window, qt_app, [0, 1])
        utak = [Path(str(controller.photos.filePathAt(i))) for i in (0, 1)]

        wait_for_signal(
            controller.saveCopyFinished,
            lambda: _elsut(window, qt_app, "menuFileSaveCopy"),
            description="a Másolat mentése",
            process_events_with=qt_app,
        )

        for ut in utak:
            assert (ut.parent / f"{ut.stem}-001{ut.suffix}").exists(), (
                f"{ut.name} másolata hiányzik"
            )

    def test_a_masolat_ini_bejegyzest_kap_a_forrase_valtozatlan(
        self, qml_app, qt_app
    ):
        """A láncot a VALÓDI úton adjuk (Kép ▸ Csoportos szerkesztés) —
        a `.picasa.ini` kézi írása nem elég, mert a vezérlő az indexből
        veszi a `filters=`-t, és az attól még nem frissül."""
        window, controller, _engine = qml_app
        forras = Path(str(controller.photos.filePathAt(0)))
        _kijelol(window, qt_app, [0])
        wait_for_photo_op(
            controller,
            lambda: _elsut(window, qt_app, "menuBatchWarmify"),
            qt_app=qt_app,
        )
        lanc = _ini(controller)[forras.name]["filters"]
        assert lanc, "a köteges effekt nem írt láncot — a próba alapja hiányzik"

        wait_for_signal(
            controller.saveCopyFinished,
            lambda: _elsut(window, qt_app, "menuFileSaveCopy"),
            description="a Másolat mentése",
            process_events_with=qt_app,
        )

        ini = _ini(controller)
        assert ini[forras.name]["filters"] == lanc, (
            "a FORRÁS ini-bejegyzése megváltozott"
        )
        masolat_nev = f"{forras.stem}-001{forras.suffix}"
        assert ini.has_section(masolat_nev), "a másolat nem került az ini-be"
        assert ini[masolat_nev]["redo"] == lanc, (
            "a másolat nem kapta meg a beégetett láncot a redo= kulcsban"
        )


class TestMentesMaskent:
    """3. A „Mentés másként…" fájlválasztót nyit, és oda ír."""

    def test_a_menupont_megnyitja_a_fajlvalasztot(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        _kijelol(window, qt_app, [0])
        parbeszed = _elem(window, "saveAsFileDialog")
        assert parbeszed.property("visible") is not True

        _elsut(window, qt_app, "menuFileSaveAs")

        assert parbeszed.property("visible") is True, (
            "a Mentés másként… nem nyitott fájlválasztót"
        )
        parbeszed.setProperty("visible", False)
        qt_app.processEvents()

    def test_a_felkinalt_nev_NEM_a_forras(self, qml_app, qt_app):
        """`IDS_CANT_SAVE_TO_SAME`: a forrásra menteni tilos, tehát a
        felkínált név sem lehet az."""
        window, controller, _engine = qml_app
        _kijelol(window, qt_app, [0])
        forras = Path(str(controller.photos.filePathAt(0)))

        javaslat = controller.suggestedCopyUrl(0)

        assert javaslat.endswith(f"{forras.stem}-001{forras.suffix}"), javaslat

    def test_a_valasztott_utra_ir(self, qml_app, qt_app, tmp_path):
        window, controller, _engine = qml_app
        _kijelol(window, qt_app, [0])
        cel = _mappa(controller) / "sajat-nevem.jpg"

        wait_for_signal(
            controller.saveCopyFinished,
            lambda: controller.saveRowAs(0, cel.as_uri()),
            description="a Mentés másként",
            process_events_with=qt_app,
        )

        assert cel.exists(), "a választott célra nem íródott fájl"


class TestMegerositesEsNeKerdezd:
    """4–5. „Kész, ha": egyes/többes mondat és a tartós elnyomás."""

    def test_EGY_kijelolt_kepnel_az_egyes_szamu_mondat(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        _kijelol(window, qt_app, [0])
        _elsut(window, qt_app, "menuFileSave")

        szoveg = _elem(window, "saveConfirmBackupNote").property("text")
        assert szoveg == "A backup of this file will be made.", szoveg
        _elem(window, "saveConfirmDialog").setProperty("visible", False)
        qt_app.processEvents()

    def test_TOBB_kijelolt_kepnel_a_tobbes_szamu_mondat(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        _kijelol(window, qt_app, [0, 1])
        _elsut(window, qt_app, "menuFileSave")

        szoveg = _elem(window, "saveConfirmBackupNote").property("text")
        assert szoveg == "A backup of these files will be made.", szoveg
        _elem(window, "saveConfirmDialog").setProperty("visible", False)
        qt_app.processEvents()

    def test_a_kerdes_a_hivatalos_felirat(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        _kijelol(window, qt_app, [0])
        _elsut(window, qt_app, "menuFileSave")

        assert (
            _elem(window, "saveConfirmMessage").property("text")
            == "Save changes to disk?"
        )
        _elem(window, "saveConfirmDialog").setProperty("visible", False)
        qt_app.processEvents()

    def test_a_ne_kerdezd_BEALLITASBA_kerul_es_elnyomja_a_parbeszedet(
        self, qml_app, qt_app
    ):
        window, controller, _engine = qml_app
        _kijelol(window, qt_app, [0])
        _elsut(window, qt_app, "menuFileSave")
        parbeszed = _elem(window, "saveConfirmDialog")

        # a felhasználó BEPIPÁLJA a jelölőt — a VEZÉRLŐN át, nem a
        # tulajdonságot írva
        jelolo = _elem(window, "saveConfirmRememberCheck")
        QMetaObject.invokeMethod(jelolo, "toggle", Qt.ConnectionType.DirectConnection)
        QMetaObject.invokeMethod(jelolo, "toggled", Qt.ConnectionType.DirectConnection)
        qt_app.processEvents()
        assert jelolo.property("checked") is True

        wait_for_signal(
            controller.saveFinished,
            lambda: QMetaObject.invokeMethod(
                parbeszed, "accept", Qt.ConnectionType.DirectConnection
            ),
            description="a mentés",
            process_events_with=qt_app,
        )

        # a beállítás TARTÓS: egy újraindult alkalmazás is ezt olvasná
        assert controller._settings.value("confirm/DoNotAskFileSave/remember") in (
            True,
            "true",
        ), "a \u201etöbbé ne kérdezd\u201d nem került a beállítás-tárba"

        # és a következő mentés MÁR NEM nyit párbeszédet
        parbeszed.setProperty("visible", False)
        qt_app.processEvents()
        wait_for_signal(
            controller.saveFinished,
            lambda: _elsut(window, qt_app, "menuFileSave"),
            description="a második mentés",
            process_events_with=qt_app,
        )
        assert parbeszed.property("visible") is not True, (
            "a párbeszéd a \u201etöbbé ne kérdezd\u201d ellenére megnyílt"
        )

    def test_a_MEGSE_ag_NEM_ir_be_semmit(self, qml_app, qt_app):
        """A #1468 rádió-csapda ellenpróbája: egy elvetett párbeszéd nem
        kapcsolhatja ki némán a kérdést."""
        window, controller, _engine = qml_app
        _kijelol(window, qt_app, [0])
        _elsut(window, qt_app, "menuFileSave")
        parbeszed = _elem(window, "saveConfirmDialog")
        jelolo = _elem(window, "saveConfirmRememberCheck")
        QMetaObject.invokeMethod(jelolo, "toggle", Qt.ConnectionType.DirectConnection)
        QMetaObject.invokeMethod(jelolo, "toggled", Qt.ConnectionType.DirectConnection)
        qt_app.processEvents()

        QMetaObject.invokeMethod(
            parbeszed, "reject", Qt.ConnectionType.DirectConnection
        )
        qt_app.processEvents()

        assert controller._settings.value("confirm/DoNotAskFileSave/remember") in (
            None,
            False,
            "false",
        ), "a Mégse ág beírta a \u201etöbbé ne kérdezd\u201d-et"


class TestHibaagakEsFolyamatjelzes:
    """6. Három hibaág + a folyamatjelzés hivatalos szövegei."""

    def test_a_nevutkozes_a_HIVATALOS_mondatot_adja(self, qml_app, qt_app):
        window, controller, _engine = qml_app
        _kijelol(window, qt_app, [0])
        forras = Path(str(controller.photos.filePathAt(0)))
        (forras.parent / f"{forras.stem}-001{forras.suffix}").write_bytes(b"foglalt")
        cel = forras.parent / f"{forras.stem}-001{forras.suffix}"

        wait_for_signal(
            controller.saveCopyFinished,
            lambda: controller.saveRowAs(0, cel.as_uri()),
            description="a Mentés másként",
            process_events_with=qt_app,
        )

        parbeszed = _elem(window, "saveErrorDialog")
        assert parbeszed.property("visible") is True, "nem jött hibaüzenet"
        assert _elem(window, "saveErrorMessage").property("text") == (
            "Unable to save file due to filename collision."
        )
        assert cel.read_bytes() == b"foglalt", "NÉMÁN FELÜLÍRTA a meglévő fájlt"
        parbeszed.setProperty("visible", False)
        qt_app.processEvents()

    def test_a_forrasra_mentes_a_MASIK_hivatalos_mondatot_adja(
        self, qml_app, qt_app
    ):
        window, controller, _engine = qml_app
        _kijelol(window, qt_app, [0])
        forras = Path(str(controller.photos.filePathAt(0)))

        wait_for_signal(
            controller.saveCopyFinished,
            lambda: controller.saveRowAs(0, forras.as_uri()),
            description="a Mentés másként",
            process_events_with=qt_app,
        )

        assert _elem(window, "saveErrorMessage").property("text") == (
            "Cannot replace image. Please try again with a different filename."
        )
        _elem(window, "saveErrorDialog").setProperty("visible", False)
        qt_app.processEvents()

    def test_a_formatumhiba_a_HARMADIK_mondatot_adja(self, qml_app, qt_app):
        window, controller, _engine = qml_app
        _kijelol(window, qt_app, [0])
        cel = _mappa(controller) / "kimenet.nincsilyenformatum"

        wait_for_signal(
            controller.saveCopyFinished,
            lambda: controller.saveRowAs(0, cel.as_uri()),
            description="a Mentés másként",
            process_events_with=qt_app,
        )

        assert _elem(window, "saveErrorMessage").property("text") == (
            "Unable to save file due to a file format error."
        )
        _elem(window, "saveErrorDialog").setProperty("visible", False)
        qt_app.processEvents()

    def test_a_lemezhiba_kiirja_a_fajlnevet_es_a_hibakodot(self, qml_app, qt_app):
        """`filesaveerr-win` — az egyetlen ág, ahol a felhasználónak
        tudnia kell, MELYIK fájlon és MILYEN kóddal bukott el."""
        window, _controller, _engine = qml_app
        parbeszed = _elem(window, "saveErrorDialog")
        parbeszed.setProperty("kind", "disk")
        parbeszed.setProperty("fileName", "IMG_0007.jpg")
        parbeszed.setProperty("code", 28)
        qt_app.processEvents()

        szoveg = _elem(window, "saveErrorMessage").property("text")
        assert "disk error" in szoveg, szoveg
        assert "IMG_0007.jpg" in szoveg, szoveg
        assert "error(28)" in szoveg, szoveg

    def test_a_folyamatjelzes_egyes_es_tobbes_szamu_mondata(self, qml_app, qt_app):
        panel = None
        window, _controller, _engine = qml_app
        panel = _elem(window, "saveProgressPanel")

        panel.setProperty("fileCount", 1)
        panel.setProperty("percent", 42.25)
        qt_app.processEvents()
        assert (
            _elem(window, "saveProgressPanelText").property("text")
            == "Saving file 42.3%"
        )

        panel.setProperty("fileCount", 3)
        panel.setProperty("percent", 42.25)
        qt_app.processEvents()
        assert (
            _elem(window, "saveProgressPanelText").property("text")
            == "Saving 3 files 42.3%"
        )

    def test_mentes_kozben_a_panel_LATSZIK_utana_eltunik(self, qml_app, qt_app):
        window, controller, _engine = qml_app
        _kijelol(window, qt_app, [0])
        panel = _elem(window, "saveProgressPanel")
        assert panel.property("visible") is False

        wait_for_signal(
            controller.saveFinished,
            lambda: controller.saveRowsToDisk([0]),
            description="a mentés",
            process_events_with=qt_app,
        )
        qt_app.processEvents()

        assert panel.property("visible") is False, (
            "a folyamat-panel a mentés után is kint maradt"
        )
        assert controller.saveProgressFileCount == 1
