"""A Fájl ▸ Fájl felvétele a Picasába… és a `Ctrl+O` bekötése (#1633).

## A lelet

Ugyanaz a hibaosztály, mint a #1615-ben a `Ctrl+M`: a menüpont (`Add File to
Picasa...\tCtrl+O`) `PicasaMenuItem { placeholder: true }` volt — azaz
`enabled: false`, kattinthatatlan —, a `Ctrl+O`-hoz pedig SEHOL nem tartozott
`Shortcut`. Itt azonban a mögöttes funkció (natív fájlválasztó egyedi
kép-/videófájlok felvételéhez) korábban EGYÁLTALÁN NEM létezett — a
`docs/specs/picasa-menu-parancsok.csv` szerint ez a `ID_FILE_OPEN`
(`cmd 0xe101`), a szabványos MFC „Megnyitás" azonosító újrahasznosítása; a
PicasaPy adatmodellje (`library_controller.py`) mappaszinten tart nyilván,
ezért a kijelölt fájl(ok) SZÜLŐMAPPÁJA kerül a könyvtárba, a MEGLÉVŐ
`controller.addWatchedFolder` belépési ponton — ugyanazon, amit végső soron a
„Mappa hozzáadása a Picasához…" is elsüt (nem másolt logika).

## Miért ilyen ez a teszt

A helyfoglaló tételen a `triggered` KIBOCSÁTÁSA „sikerülne" — a felhasználó
mégsem tud rákattintani. Ez a fájl ezért a valódi felületi vezérlőkön megy
végig: előbb megköveteli, hogy a tétel engedélyezett és ne helyfoglaló
legyen, a gyorsbillentyűt pedig VALÓDI billentyűeseménnyel (`QTest.keyClick`)
üti le. A natív fájlválasztó offscreen platformon nem szimulálható
kattintással, ezért a tényleges hatást (a kijelölt fájlok szülőmappájának
felvétele) az `AddFileDialog.qml` `addSelectedFiles()` függvényén át mérjük
közvetlenül — ugyanaz a minta, mint az `ImportDropArea.qml` `submitUrls()`-
tesztje.

A várt értékek (`"Add File to Picasa..."`, `"Ctrl+O"`,
`"Fájl felvétele a Picasába…"`) szándékosan KIÍRT LITERÁLOK — nem a termék
konstansaiból olvassuk ki őket (#1576 tanulsága: az önmagát igazoló teszt
bármit elfogad).
"""

from __future__ import annotations

import re
from pathlib import Path
from xml.etree import ElementTree

import pytest

from PySide6.QtCore import QMetaObject, QObject, Qt, Q_ARG
from PySide6.QtTest import QTest

import picasapy.app
from support.jpeg_factory import make_jpeg
from support.qt_wait import wait_for_signal

_APP_DIR = Path(picasapy.app.__file__).parent
_MENU_QML = _APP_DIR / "qml" / "PicasaPy" / "PicasaMenuBar.qml"
_DIALOG_QML = _APP_DIR / "qml" / "PicasaPy" / "AddFileDialog.qml"
_TS_PATH = _APP_DIR / "i18n" / "picasapy_hu.ts"


def _elem(root, nev):
    obj = root.findChild(QObject, nev)
    assert obj is not None, f"{nev} nem található"
    return obj


def _parbeszed(window):
    return _elem(window, "addFileDialog")


def _bezar(window, qt_app):
    """⚠️ MÉRT teszt-higiénia (a #1615 mintájából): az `AddFileDialog`
    ÖNÁLLÓ `Window`-t nyit (a `FileDialog` QtQuick.Dialogs implementációja
    offscreen platformon QML-visszaesésre vált), nyitva hagyva a KÖVETKEZŐ
    teszt billentyűeseményeit nyelheti el."""
    parbeszed = window.findChild(QObject, "addFileDialog")
    if parbeszed is not None and parbeszed.property("visible"):
        parbeszed.setProperty("visible", False)
        qt_app.processEvents()


class TestMenupont:
    """A Fájl menü tétele ÉLŐ, és a natív fájlválasztót nyitja."""

    def test_a_tetel_nem_helyfoglalo_es_engedelyezett(self, qml_app):
        window, _controller, _engine = qml_app
        tetel = _elem(window, "menuFileAddFile")

        assert not tetel.property("placeholder"), (
            "a Fájl felvétele a Picasába… menüpont még mindig helyfoglaló, "
            "tehát a felhasználó rá sem tud kattintani (#1633)"
        )
        assert tetel.property("enabled") is True, (
            "a Fájl felvétele a Picasába… menüpont le van tiltva"
        )

    def test_a_felirat_a_hirdetett_billentyut_is_tartalmazza(self, qml_app):
        window, _controller, _engine = qml_app

        # kiírt literál: a `stringres` `ID_FILE_OPEN` forrásszövege és a
        # #1154 által MÉRT gyorsbillentyű.
        #
        # ⚠️ #2152: az `&` a MNEMONIK jelölése (`Add &File to Picasa...`),
        # nem a felirat tartalma — ez a próba a gyorsbillentyű
        # megjelenítését méri, azt pedig a mnemonik nem érinti. A
        # mnemonikot a saját őre méri (`test_menu_mnemonikok_2152.py`).
        felirat = str(_elem(window, "menuFileAddFile").property("text"))
        assert felirat.replace("&", "") == "Add File to Picasa...\tCtrl+O"

    def test_a_menupontra_kattintva_megnyilik_a_fajlvalaszto(
        self, qml_app, qt_app
    ):
        window, _controller, _engine = qml_app
        parbeszed = _parbeszed(window)
        assert parbeszed.property("visible") is False

        tetel = _elem(window, "menuFileAddFile")
        assert tetel.property("enabled") is True
        QMetaObject.invokeMethod(
            tetel, "triggered", Qt.ConnectionType.DirectConnection
        )
        qt_app.processEvents()

        assert parbeszed.property("visible") is True, (
            "a Fájl ▸ Fájl felvétele a Picasába… nem nyitotta meg a "
            "fájlválasztót"
        )
        _bezar(window, qt_app)


class TestGyorsbillentyu:
    """A `Ctrl+O` VALÓDI billentyűeseménnyel."""

    def test_a_ctrl_o_megnyitja_a_fajlvalasztot(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        parbeszed = _parbeszed(window)
        assert parbeszed.property("visible") is False

        QTest.keyClick(window, Qt.Key_O, Qt.ControlModifier)
        qt_app.processEvents()

        assert parbeszed.property("visible") is True, (
            "a Ctrl+O nem nyitotta meg a fájlválasztót"
        )
        _bezar(window, qt_app)

    def test_a_gyorsbillentyu_elo_es_a_sorozata_a_hirdetett(self, qml_app):
        window, _controller, _engine = qml_app
        rovidites = _elem(window, "shortcutAddFile")

        assert rovidites.property("enabled") is True
        # kiírt literál — nem a menüfeliratból származtatva
        assert str(rovidites.property("sequence")) == "Ctrl+O"


class TestSzovegmezoElsobbsege:
    """⚠️ MÉRT megállapítás, nem feltevés (#1526/#1571 hibaosztálya, a
    #1615-nél a `Ctrl+M`-re mérve — itt kontroll-méréssel megismételve a
    `Ctrl+O`-ra).

    A `Ctrl+O` ablak-szintű `Shortcut`. A Qt a leütést előbb
    `ShortcutOverride` eseményként ajánlja fel a fókuszált elemnek: a
    `QQuickTextInput` CSAK azokat fogadja el, amelyeket maga is kezelne
    (szerkesztő-billentyűk, sima karakterek). A `Ctrl+O` nem ilyen, ezért a
    mezőben ÁLLVA IS a gyorsbillentyű nyeri.

    A mező akkor van veszélyben, ha a gyorsbillentyű MÓDOSÍTÓ NÉLKÜLI betű
    lenne; a második teszt épp ezt méri: a puszta „o" a keresőmezőbe kerül,
    és NEM nyit fájlválasztót.
    """

    def test_a_ctrl_o_a_keresomezoben_allva_is_hat(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        mezo = _elem(window, "searchField")
        mezo.setProperty("focus", True)
        qt_app.processEvents()
        assert mezo.property("activeFocus") is True, (
            "a keresőmező nem kapott fókuszt — a mérés nem érvényes"
        )

        QTest.keyClick(window, Qt.Key_O, Qt.ControlModifier)
        qt_app.processEvents()

        assert _parbeszed(window).property("visible") is True, (
            "a Ctrl+O a keresőmezőben állva elveszett"
        )
        assert str(mezo.property("text")) == "", (
            "a Ctrl+O karaktert írt a keresőmezőbe"
        )
        _bezar(window, qt_app)

    def test_a_puszta_o_a_mezobe_kerul_es_nem_nyit_semmit(
        self, qml_app, qt_app
    ):
        window, _controller, _engine = qml_app
        mezo = _elem(window, "searchField")
        mezo.setProperty("focus", True)
        qt_app.processEvents()
        assert mezo.property("activeFocus") is True

        QTest.keyClick(window, Qt.Key_O, Qt.KeyboardModifier.NoModifier)
        qt_app.processEvents()

        assert str(mezo.property("text")) == "o", (
            "a keresőmező nem kapta meg a leütött betűt"
        )
        assert _parbeszed(window).property("visible") is False, (
            "egy sima betű megnyitotta a fájlválasztót"
        )


class TestValodiHatas:
    """A kijelölt fájl(ok) SZÜLŐMAPPÁJA a könyvtárba kerül — a meglévő
    `controller.addWatchedFolder` belépési ponton, TARTÓS figyeléssel."""

    def test_a_kijelolt_fajl_mappaja_bekerul_a_konyvtarba(
        self, qml_app, qt_app, tmp_path
    ):
        window, controller, _engine = qml_app
        uj_mappa = tmp_path / "uj-fenykepek"
        uj_mappa.mkdir()
        make_jpeg(uj_mappa / "kep.jpg")
        assert str(uj_mappa) not in controller.watchedFolders

        parbeszed = _parbeszed(window)
        wait_for_signal(
            controller.syncFinished,
            lambda: QMetaObject.invokeMethod(
                parbeszed,
                "addSelectedFiles",
                Qt.ConnectionType.DirectConnection,
                Q_ARG("QVariant", [(uj_mappa / "kep.jpg").as_uri()]),
            ),
            description="a Fájl felvétele a Picasába… szinkron",
            process_events_with=qt_app,
        )

        assert str(uj_mappa) in controller.watchedFolders, (
            "a kijelölt fájl mappája nem került a figyelt mappák közé"
        )
        assert controller.folders.rowOfPath(str(uj_mappa)) >= 0, (
            "a mappa tartalma nem került az indexbe"
        )

    def test_ket_azonos_mappas_fajl_csak_egyszer_adodik_hozza(
        self, qml_app, qt_app, tmp_path
    ):
        """Duplikáció-védelem: ugyanabból a mappából két fájl kijelölése
        NEM próbálja kétszer felvenni a mappát (a `path_key`-alapú védelem
        az `addWatchedFolder`-ben már megvan, ez csak nem terheli feleslegesen)."""
        window, controller, _engine = qml_app
        uj_mappa = tmp_path / "ket-fajl"
        uj_mappa.mkdir()
        make_jpeg(uj_mappa / "egy.jpg")
        make_jpeg(uj_mappa / "ketto.jpg")

        parbeszed = _parbeszed(window)
        elotte = list(controller.watchedFolders)
        wait_for_signal(
            controller.syncFinished,
            lambda: QMetaObject.invokeMethod(
                parbeszed,
                "addSelectedFiles",
                Qt.ConnectionType.DirectConnection,
                Q_ARG(
                    "QVariant",
                    [
                        (uj_mappa / "egy.jpg").as_uri(),
                        (uj_mappa / "ketto.jpg").as_uri(),
                    ],
                ),
            ),
            description="a Fájl felvétele a Picasába… szinkron",
            process_events_with=qt_app,
        )

        utana = list(controller.watchedFolders)
        assert utana.count(str(uj_mappa)) == 1, (
            "a mappa többször került fel a figyelt listára"
        )
        assert len(utana) == len(elotte) + 1


class TestForrasEsFordítas:
    """A forrásban is látszódjon, hogy a tétel élő — és a magyar felirat
    a `stringres` szerinti legyen."""

    def test_a_menupont_nem_placeholder_a_forrasban(self):
        forras = _MENU_QML.read_text(encoding="utf-8")
        tetel = re.search(
            r"MenuItem\s*\{[^}]*?menuFileAddFile[^}]*?\}", forras, re.S
        )
        assert tetel is not None, (
            "a menuFileAddFile tétel nem MenuItem a forrásban"
        )
        blokk = tetel.group(0)
        assert "placeholder" not in blokk, (
            "a tétel visszakerült helyfoglalóra (#1633)"
        )
        assert "addFileRequested()" in blokk

    def test_a_dialogus_a_meglevo_addwatchedfolder_utat_hasznalja(self):
        """NEM másolt logika: a szülőmappa-felvétel a MEGLÉVŐ
        `controller.addWatchedFolder`-en át megy, nem egy új,
        párhuzamos mappa-figyelő út épül."""
        forras = _DIALOG_QML.read_text(encoding="utf-8")
        assert "controller.addWatchedFolder(" in forras

    def test_a_magyar_felirat_a_stringres_szerinti(self):
        gyoker = ElementTree.parse(_TS_PATH).getroot()
        forditasok = {
            uzenet.findtext("source"): uzenet.findtext("translation")
            for uzenet in gyoker.iter("message")
        }

        # kiírt literál mindkét oldalon
        assert forditasok.get("Add File to Picasa...") == (
            "Fájl felvétele a Picasába…"
        )


@pytest.mark.parametrize(
    "nev", ["menuFileAddFile", "shortcutAddFile", "addFileDialog"]
)
def test_a_lanc_minden_szeme_megvan(qml_app, nev):
    window, _controller, _engine = qml_app
    assert window.findChild(QObject, nev) is not None, nev
