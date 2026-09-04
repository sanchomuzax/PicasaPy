"""A Fájl ▸ Importálás forrása… és a `Ctrl+M` bekötése (#1615).

## A lelet

Nem hiányzó funkció volt, hanem hiányzó BEKÖTÉS. Az `ImportSourceDialog`
kész, és az eszköztár „Import" gombjából (`MainToolbar.qml`
`toolbarImportButton` → `Main.qml` `onImportRequested`) meg is nyílt. A
Fájl menü tétele viszont `PicasaMenuItem { ... placeholder: true }` volt —
azaz `enabled: false`, kattinthatatlan —, a felirata pedig `Ctrl+M`-et
hirdetett, miközben ilyen `Shortcut` sehol nem létezett a fában. Aki a
menüből próbálta, azt látta, hogy „az importálás nem működik".

## Miért ilyen ez a teszt

A helyfoglaló tételen a `triggered` KIBOCSÁTÁSA „sikerülne" — a felhasználó
mégsem tud rákattintani. Ez a fájl ezért a valódi felületi vezérlőkön megy
végig: előbb megköveteli, hogy a tétel engedélyezett és ne helyfoglaló
legyen, a gyorsbillentyűt pedig VALÓDI billentyűeseménnyel (`QTest.keyClick`)
üti le, nem a `Shortcut.activated` kibocsátásával. A mért hatás mindkét
esetben a párbeszéd MEGNYÍLÁSA, nem a jelzés elmenetele.

A várt értékek (`"Import From..."`, `"Ctrl+M"`, `"Importálás forrása…"`)
szándékosan KIÍRT LITERÁLOK — nem a termék konstansaiból olvassuk ki őket
(#1576 tanulsága: az önmagát igazoló teszt bármit elfogad).
"""

from __future__ import annotations

import re
from pathlib import Path
from xml.etree import ElementTree

import pytest

from PySide6.QtCore import QMetaObject, QObject, Qt
from PySide6.QtTest import QTest

from support.halasztott_parbeszed import nyisd_meg

import picasapy.app

_APP_DIR = Path(picasapy.app.__file__).parent
_MENU_QML = _APP_DIR / "qml" / "PicasaPy" / "PicasaMenuBar.qml"
_TS_PATH = _APP_DIR / "i18n" / "picasapy_hu.ts"


def _elem(root, nev):
    obj = root.findChild(QObject, nev)
    assert obj is not None, f"{nev} nem található"
    return obj


def _parbeszed(window):
    return _elem(window, "importSourceDialog")


def _meg_nem_all(window):
    """#1720: a párbeszéd HALASZTOTT — a megnyitás ELŐTT létre sem jön."""
    assert window.findChild(QObject, "importSourceDialog") is None, (
        "az Import ablak már a megnyitás előtt felépült — a #1720 "
        "halasztása elromlott"
    )


def _bezar(window, qt_app):
    """⚠️ MÉRT teszt-higiénia, nem díszítés.

    Az `ImportSourceDialog` ÖNÁLLÓ `Window`. Az offscreen platformon a
    nyitva hagyott (exposed) ablakot a `qml_app` lebontása nem szedi el
    azonnal, és a KÖVETKEZŐ teszt `QTest.keyClick`-jei elnyelődnek —
    mérve: a fókusz-ablak és az `activeFocus` a következő tesztben helyes
    volt, a leütött betű mégsem ért a keresőmezőbe. Ezért minden nyitó
    teszt a végén becsukja a párbeszédet.
    """
    parbeszed = window.findChild(QObject, "importSourceDialog")
    if parbeszed is not None and parbeszed.property("visible"):
        parbeszed.setProperty("visible", False)
        qt_app.processEvents()


class TestMenupont:
    """A Fájl menü tétele ÉLŐ, és ugyanoda vezet, mint az eszköztár gombja."""

    def test_a_tetel_nem_helyfoglalo_es_engedelyezett(self, qml_app):
        window, _controller, _engine = qml_app
        tetel = _elem(window, "menuFileImportFrom")

        assert not tetel.property("placeholder"), (
            "az Importálás forrása… menüpont még mindig helyfoglaló, "
            "tehát a felhasználó rá sem tud kattintani (#1615)"
        )
        assert tetel.property("enabled") is True, (
            "az Importálás forrása… menüpont le van tiltva"
        )

    def test_a_felirat_a_hirdetett_billentyut_is_tartalmazza(self, qml_app):
        window, _controller, _engine = qml_app

        # kiírt literál: a `stringres` `ID_FILE_IMPORTPICTURE` forrásszövege
        # és a #1154 által MÉRT gyorsbillentyű
        # ⚠️ #2152: az `&` a MNEMONIK jelölése, nem a felirat tartalma.
        felirat = str(_elem(window, "menuFileImportFrom").property("text"))
        assert felirat.replace("&", "") == "Import From...\tCtrl+M"

    def test_a_menupontra_kattintva_megnyilik_a_parbeszed(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        _meg_nem_all(window)

        tetel = _elem(window, "menuFileImportFrom")
        assert tetel.property("enabled") is True
        QMetaObject.invokeMethod(
            tetel, "triggered", Qt.ConnectionType.DirectConnection
        )
        qt_app.processEvents()

        assert _parbeszed(window).property("visible") is True, (
            "a Fájl ▸ Importálás forrása… nem nyitotta meg a párbeszédet"
        )
        _bezar(window, qt_app)

    def test_ugyanaz_a_parbeszed_mint_az_eszkoztar_gombjae(self, qml_app, qt_app):
        """Nem MÁSOLT út: a menü és az eszköztár gombja UGYANAZT a
        példányt nyitja — különben a két úton más állapot élne."""
        window, _controller, _engine = qml_app

        QMetaObject.invokeMethod(
            _elem(window, "toolbarImportButton"),
            "clicked",
            Qt.ConnectionType.DirectConnection,
        )
        qt_app.processEvents()
        gombbol = _parbeszed(window)
        assert gombbol.property("visible") is True
        gombbol.setProperty("visible", False)
        qt_app.processEvents()

        QMetaObject.invokeMethod(
            _elem(window, "menuFileImportFrom"),
            "triggered",
            Qt.ConnectionType.DirectConnection,
        )
        qt_app.processEvents()
        menubol = _parbeszed(window)

        assert menubol is gombbol, (
            "a menü egy MÁSIK párbeszéd-példányt nyit, mint az eszköztár"
        )
        assert menubol.property("visible") is True
        _bezar(window, qt_app)


class TestGyorsbillentyu:
    """A `Ctrl+M` VALÓDI billentyűeseménnyel."""

    def test_a_ctrl_m_megnyitja_a_parbeszedet(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        _meg_nem_all(window)

        QTest.keyClick(window, Qt.Key_M, Qt.ControlModifier)
        qt_app.processEvents()

        assert _parbeszed(window).property("visible") is True, (
            "a Ctrl+M nem nyitotta meg az importálás párbeszédét"
        )
        _bezar(window, qt_app)

    def test_a_gyorsbillentyu_elo_es_a_sorozata_a_hirdetett(self, qml_app):
        window, _controller, _engine = qml_app
        rovidites = _elem(window, "shortcutImportFrom")

        assert rovidites.property("enabled") is True
        # kiírt literál — nem a menüfeliratból származtatva
        assert str(rovidites.property("sequence")) == "Ctrl+M"


class TestSzovegmezoElsobbsege:
    """⚠️ MÉRT megállapítás, nem feltevés (#1526/#1571 hibaosztálya).

    A `Ctrl+M` ablak-szintű `Shortcut`. A Qt a leütést előbb
    `ShortcutOverride` eseményként ajánlja fel a fókuszált elemnek: a
    `QQuickTextInput` CSAK azokat fogadja el, amelyeket maga is kezelne
    (szerkesztő-billentyűk, sima karakterek). A `Ctrl+M` nem ilyen, ezért
    a mezőben ÁLLVA IS a gyorsbillentyű nyeri — és ez a helyes: az
    eredetiben a `Ctrl+M` a menüsáv kiosztásából jön, tehát globális.

    A mező akkor van veszélyben, ha a gyorsbillentyű MÓDOSÍTÓ NÉLKÜLI
    betű lenne; a második teszt épp ezt méri: a puszta „m" a keresőmezőbe
    kerül, és NEM nyit párbeszédet.
    """

    def test_a_ctrl_m_a_keresomezoben_allva_is_hat(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        mezo = _elem(window, "searchField")
        mezo.setProperty("focus", True)
        qt_app.processEvents()
        assert mezo.property("activeFocus") is True, (
            "a keresőmező nem kapott fókuszt — a mérés nem érvényes"
        )

        QTest.keyClick(window, Qt.Key_M, Qt.ControlModifier)
        qt_app.processEvents()

        assert _parbeszed(window).property("visible") is True, (
            "a Ctrl+M a keresőmezőben állva elveszett"
        )
        assert str(mezo.property("text")) == "", (
            "a Ctrl+M karaktert írt a keresőmezőbe"
        )
        _bezar(window, qt_app)

    def test_a_puszta_m_a_mezobe_kerul_es_nem_nyit_semmit(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        mezo = _elem(window, "searchField")
        mezo.setProperty("focus", True)
        qt_app.processEvents()
        assert mezo.property("activeFocus") is True

        QTest.keyClick(window, Qt.Key_M, Qt.KeyboardModifier.NoModifier)
        qt_app.processEvents()

        assert str(mezo.property("text")) == "m", (
            "a keresőmező nem kapta meg a leütött betűt"
        )
        # #1720: halasztás mellett a „nem nyílt meg" azt jelenti, hogy
        # a párbeszéd LÉTRE SEM JÖTT — ez erősebb állítás a `visible`-nél
        assert window.findChild(QObject, "importSourceDialog") is None, (
            "egy sima betű megnyitotta az importálás párbeszédét"
        )


class TestForrasEsFordítas:
    """A forrásban is látszódjon, hogy a tétel élő — és a magyar felirat
    a `stringres` szerinti legyen."""

    def test_a_menupont_nem_placeholder_a_forrasban(self):
        # #2152: az `&` a MNEMONIK jelölése, nem a felirat tartalma.
        forras = _MENU_QML.read_text(encoding="utf-8").replace("&", "")
        tetel = re.search(
            r"MenuItem\s*\{[^}]*?menuFileImportFrom[^}]*?\}", forras, re.S
        )
        assert tetel is not None, (
            "a menuFileImportFrom tétel nem MenuItem a forrásban"
        )
        blokk = tetel.group(0)
        assert "placeholder" not in blokk, (
            "a tétel visszakerült helyfoglalóra (#1615)"
        )
        assert "importSourceRequested()" in blokk

    def test_a_magyar_felirat_a_stringres_szerinti(self):
        gyoker = ElementTree.parse(_TS_PATH).getroot()
        forditasok = {
            uzenet.findtext("source"): uzenet.findtext("translation")
            for uzenet in gyoker.iter("message")
        }

        # kiírt literálok mindkét oldalon
        # ⚠️ #2152: a kulcs és a fordítás is mnemonikot kapott
        tiszta = {
            k.replace("&", ""): v.replace("&", "")
            for k, v in forditasok.items()
        }
        assert tiszta.get("Import From...") == "Importálás forrása…"


@pytest.mark.parametrize(
    "nev", ["menuFileImportFrom", "shortcutImportFrom", "importSourceDialog"]
)
def test_a_lanc_minden_szeme_megvan(qml_app, nev):
    window, _controller, _engine = qml_app
    # #1720: a párbeszéd halasztott — a lánc utolsó szeme a MENÜPONTON át
    # jön létre; épp ez bizonyítja, hogy a lánc végig ép
    if nev == "importSourceDialog":
        nyisd_meg(window, "importSourceDialog")
    assert window.findChild(QObject, nev) is not None, nev
