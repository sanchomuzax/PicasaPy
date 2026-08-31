"""A nyomtatás útja VÉGIG: menüpont/gyorsbillentyű → párbeszéd → vezérlő →
KIMENET (#1472).

## A lelet

A `print_controller.py` 213 sor kész kód volt, két tesztfájllal — és a
felhasználó nem érte el. A `PrintController` a termékkódban SOHA nem
példányosult, nem volt `setContextProperty`, és a 136 QML-fájlban NULLA
hivatkozás volt rá (két különböző alakú kereséssel igazolva). A `Fájl ▸
Nyomtatás…` (Ctrl+P) menüpont `placeholder` volt (azaz `enabled: false`),
`Ctrl+P` gyorsbillentyű sehol nem létezett, a képtálca „Nyomtatás" gombja
pedig egy olyan jelzést bocsátott ki (`TrayBar.printRequested`), amelynek
SEHOL nem volt kezelője. A teljes leltár: `docs/specs/lanc-szakadasok-
leltar.md` „A" sora.

## Miért ilyen ez a teszt

A vezérlő metódusait a `tests/app/test_print_controller.py` MÁR mérte — és
végig zöld volt, miközben a funkció elérhetetlen. Ez a fájl ezért
KIZÁRÓLAG a valódi felületi vezérlőkön át dolgozik: a menütételt aktiválja
(előbb megkövetelve, hogy egyáltalán engedélyezett legyen), a
gyorsbillentyűt valódi billentyűeseménnyel üti le, a párbeszéd valódi
gombját kattintja — és a végén a LEMEZRE ÍRT PDF-et méri, nem a hívás
visszatérési értékét.
"""

from __future__ import annotations

import re

import pytest
import pathlib
from pathlib import Path

from PySide6.QtCore import Q_ARG, QMetaObject, QObject, Qt, QUrl
from PySide6.QtTest import QTest

import picasapy.app

# #664 mintája: a QtPrintSupport nem minden PySide6-telepítésben van benne
# (a Debian/Ubuntu csomag modulokra bontja). Ahol hiányzik, ott a nyomtatás
# felületi bekötése sem mérhető.
try:
    import PySide6.QtPrintSupport  # noqa: F401

    _QTPRINTSUPPORT_VAN = True
except ImportError:  # pragma: no cover — csak a hiányos telepítésen fut
    _QTPRINTSUPPORT_VAN = False

pytestmark = pytest.mark.skipif(
    not _QTPRINTSUPPORT_VAN,
    reason=(
        "a PySide6.QtPrintSupport modul hiányzik ezen a gépen, ezért a "
        "nyomtatás felületi bekötésének tesztjei kimaradnak. Debian/Ubuntu "
        "alatt így pótolható: sudo apt install python3-pyside6.qtprintsupport"
    ),
)


def _elem(root, nev):
    obj = root.findChild(QObject, nev)
    assert obj is not None, f"{nev} nem található"
    return obj


def _kijelol(window, qt_app, sorok):
    window.setProperty("selectedIndexes", list(sorok))
    window.setProperty("selectedIndex", sorok[0] if sorok else -1)
    qt_app.processEvents()


def _menubol_nyit(window, qt_app):
    """A VALÓDI menütétel aktiválása.

    Előbb megköveteli, hogy a tétel egyáltalán engedélyezett legyen: egy
    `placeholder` tételen a `triggered` kibocsátása „sikerülne", miközben a
    felhasználó rá sem tud kattintani — pontosan ez a hibaosztály (#1472).
    """
    tetel = _elem(window, "menuFilePrint")
    assert tetel.property("enabled") is True, (
        "a Nyomtatás… menüpont le van tiltva — a felhasználó nem éri el"
    )
    assert not tetel.property("placeholder"), (
        "a Nyomtatás… menüpont még mindig helyfoglaló (#416), tehát halott"
    )
    QMetaObject.invokeMethod(tetel, "triggered", Qt.ConnectionType.DirectConnection)
    qt_app.processEvents()
    return _elem(window, "printDialog")


def _sorok(parbeszed) -> list[int]:
    """A párbeszéd `rows` property-je — a QML `var` lista `QJSValue`-ként jön."""
    ertek = parbeszed.property("rows")
    nyers = ertek.toVariant() if hasattr(ertek, "toVariant") else ertek
    return [int(r) for r in (nyers or [])]


def _pdf_oldalszam(adat: bytes) -> int:
    """A PDF oldalobjektumainak száma — a `/Type /Pages` gyűjtőt kizárva."""
    return len(re.findall(rb"/Type\s*/Page[^s]", adat))


class TestRegisztracio:
    """⚠️ A `qml_app` fixture a `support/print_wiring.py`-val MAGA
    regisztrálja a vezérlőt, ezért egy `contextProperty(...) is not None`
    állítás itt a saját conftestjét mérné, nem a terméket — mutációval
    igazolva: az `application.py`-beli `setContextProperty` törlésére a
    fájl összes többi tesztje zöld maradt. A TERMÉK bekötését ezért a
    forrásban mérjük; a QML↔regisztráció összevetésének teljes őre
    változatlanul a `tests/app/test_vezerlo_regisztracio_1066.py`.
    """

    def test_az_application_py_letrehozza_es_regisztralja_a_vezerlot(self):
        forras = (
            Path(picasapy.app.__file__).parent / "application.py"
        ).read_text(encoding="utf-8")

        assert "PrintController(photo_source=" in forras, (
            "a termékkód nem hozza létre a PrintControllert"
        )
        assert 'setContextProperty("printController"' in forras, (
            "a termékkód nem regisztrálja a printControllert a QML felé"
        )

    def test_a_parbeszed_vezerlo_NELKUL_is_kimondja_a_hianyt(self, qt_app):
        """A hiányzó `QtPrintSupport` ága (`ctl === null`) — a legfontosabb
        kérdés, mert ezt a felhasználó gépén senki nem tudja kipróbálni.

        A párbeszédet KÜLÖN motorba töltjük be, `printController`
        regisztráció NÉLKÜL: pontosan az az állapot, ami a hiányos
        Qt-telepítésen áll elő. Az elvárás nem az, hogy ne dőljön el —
        hanem hogy MEGSZÓLALJON, és megmondja a teendőt is.
        """
        from PySide6.QtQml import QQmlComponent, QQmlEngine

        motor = QQmlEngine()
        motor.addImportPath(str(Path(picasapy.app.__file__).parent / "qml"))
        elem = QQmlComponent(
            motor,
            QUrl.fromLocalFile(
                str(
                    Path(picasapy.app.__file__).parent
                    / "qml" / "PicasaPy" / "PrintDialog.qml"
                )
            ),
        )
        assert elem.status() == QQmlComponent.Status.Ready, elem.errorString()
        parbeszed = elem.create()
        assert parbeszed is not None

        assert parbeszed.property("ctl") is None
        QMetaObject.invokeMethod(
            parbeszed,
            "openForRows",
            Qt.ConnectionType.DirectConnection,
            Q_ARG("QVariant", [0]),
        )
        qt_app.processEvents()

        uzenet = str(parbeszed.property("lastError"))
        assert uzenet, "a párbeszéd NÉMÁN nyílt meg működő vezérlő nélkül"
        assert "python3-pyside6.qtprintsupport" in uzenet, (
            "az üzenet nem mondja meg, mit tegyen a felhasználó"
        )
        assert parbeszed.property("canPrint") is False
        parbeszed.setProperty("visible", False)
        parbeszed.deleteLater()
        qt_app.processEvents()


class TestBelepesiPontok:
    """Három belépési pont vezet ugyanoda: a Fájl menü tétele, a Ctrl+P és
    a képtálca „Nyomtatás" gombja."""

    def test_a_menupont_megnyitja_a_parbeszedet(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        _kijelol(window, qt_app, [0])

        parbeszed = _menubol_nyit(window, qt_app)

        assert parbeszed.property("visible") is True

    def test_a_ctrl_p_megnyitja_a_parbeszedet(self, qml_app, qt_app):
        """VALÓDI billentyűleütés — nem a `Shortcut.activated` kibocsátása."""
        window, _controller, _engine = qml_app
        _kijelol(window, qt_app, [0])
        # #1720: a párbeszéd HALASZTOTT — a billentyű ELŐTT létre sem jön.
        assert window.findChild(QObject, "printDialog") is None, (
            "a nyomtatás ablaka már a billentyű előtt felépült — a #1720 "
            "halasztása elromlott"
        )

        QTest.keyClick(window, Qt.Key_P, Qt.ControlModifier)
        qt_app.processEvents()

        parbeszed = _elem(window, "printDialog")
        assert parbeszed.property("visible") is True, (
            "a Ctrl+P nem nyitotta meg a nyomtatás párbeszédét"
        )

    def test_a_talca_gombja_ugyanazt_a_parbeszedet_nyitja(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        _kijelol(window, qt_app, [0])
        gomb = _elem(window, "trayPrintButton")
        assert gomb.property("enabled") is True

        QMetaObject.invokeMethod(gomb, "clicked", Qt.ConnectionType.DirectConnection)
        qt_app.processEvents()

        assert _elem(window, "printDialog").property("visible") is True


class TestKimenet:
    """A lánc utolsó szeme: a párbeszéd VALÓDI gombja lemezre írt fájlt ad."""

    def test_egy_kijelolt_kep_egyoldalas_PDF_t_ad(self, qml_app, qt_app, tmp_path):
        window, _controller, _engine = qml_app
        _kijelol(window, qt_app, [0])
        parbeszed = _menubol_nyit(window, qt_app)
        cel = tmp_path / "nyomtatas.pdf"
        parbeszed.setProperty("pdfTarget", cel.as_uri())
        qt_app.processEvents()

        gomb = _elem(window, "printStartButton")
        assert gomb.property("enabled") is True, "a Nyomtatás gomb szürke maradt"
        QMetaObject.invokeMethod(gomb, "clicked", Qt.ConnectionType.DirectConnection)
        qt_app.processEvents()

        assert cel.exists(), "a nyomtatás gombja NEM írt fájlt"
        adat = cel.read_bytes()
        assert adat.startswith(b"%PDF")
        assert _pdf_oldalszam(adat) == 1

    def test_ket_kijelolt_kep_ketoldalas_PDF_t_ad(self, qml_app, qt_app, tmp_path):
        window, _controller, _engine = qml_app
        _kijelol(window, qt_app, [0, 1])
        parbeszed = _menubol_nyit(window, qt_app)
        cel = tmp_path / "ketto.pdf"
        parbeszed.setProperty("pdfTarget", cel.as_uri())
        qt_app.processEvents()

        QMetaObject.invokeMethod(
            _elem(window, "printStartButton"),
            "clicked",
            Qt.ConnectionType.DirectConnection,
        )
        qt_app.processEvents()

        assert _pdf_oldalszam(cel.read_bytes()) == 2

    def test_a_siker_visszajelzese_megjelenik(self, qml_app, qt_app, tmp_path):
        """A `printFinished` nem tűnhet el: a felhasználó lássa, hova ment."""
        window, _controller, _engine = qml_app
        _kijelol(window, qt_app, [0])
        parbeszed = _menubol_nyit(window, qt_app)
        parbeszed.setProperty("pdfTarget", (tmp_path / "ok.pdf").as_uri())
        qt_app.processEvents()

        QMetaObject.invokeMethod(
            _elem(window, "printStartButton"),
            "clicked",
            Qt.ConnectionType.DirectConnection,
        )
        qt_app.processEvents()

        eredmeny = _elem(window, "printResultText")
        assert eredmeny.property("visible") is True
        assert str(eredmeny.property("text")).strip()


class TestCelpont:
    """A nyomtatandó sorok HÁROM ágon dőlnek el (`Main.qml printTargetRows`)."""

    def test_a_nezoben_a_LATOTT_kep_a_celpont(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        _kijelol(window, qt_app, [0])
        nezo = _elem(window, "photoViewer")
        nezo.setProperty("currentIndex", 1)
        window.setProperty("viewerOpen", True)
        qt_app.processEvents()

        gomb = _elem(window, "trayPrintButton")
        assert gomb.property("enabled") is True, (
            "a nézőben a tálca nyomtatás-gombja nem él"
        )
        QMetaObject.invokeMethod(gomb, "clicked", Qt.ConnectionType.DirectConnection)
        qt_app.processEvents()

        parbeszed = _elem(window, "printDialog")
        assert _sorok(parbeszed) == [1], (
            "a néző képe helyett a rács kijelölése ment nyomtatásra"
        )

    def test_diavetites_kozben_a_VETITETT_kep_a_celpont(self, qml_app, qt_app):
        """A `startSlideshow()` NEM állítja a `viewerOpen`-t, tehát a menü és
        a Ctrl+P vetítés közben is él — a célpont mégsem a rács lehet."""
        window, _controller, _engine = qml_app
        _kijelol(window, qt_app, [0, 1])
        vetites = _elem(window, "slideshowView")
        QMetaObject.invokeMethod(
            window, "startSlideshow", Qt.ConnectionType.DirectConnection,
            Q_ARG("QVariant", 1),
        )
        qt_app.processEvents()
        assert vetites.property("visible") is True, "a diavetítés nem indult el"

        QTest.keyClick(window, Qt.Key_P, Qt.ControlModifier)
        qt_app.processEvents()

        parbeszed = _elem(window, "printDialog")
        assert _sorok(parbeszed) == [1], (
            "diavetítés közben a RÁCS kijelölése ment nyomtatásra"
        )


class TestNyomtatoValasztas:
    """⚠️ Amit a párbeszéd MUTAT, oda kell mennie a feladatnak.

    A `printerIndex` korábban külön, írható property volt a
    `ComboBox.currentIndex` mellett. A Qt a modell rövidülésekor
    IMPERATÍVAN visszaállítja a `currentIndex`-et (felülütve a kötést) — a
    külön property viszont a régi értéken maradt. Egy lecsatlakozó hálózati
    nyomtató így oda vezetett, hogy a párbeszéd „PDF-fájlba"-t mutatott, és
    közben a RENDSZER ALAPÉRTELMEZETT nyomtatójára ment ki papír.
    """

    def test_a_valaszto_es_a_celzott_nyomtato_egyutt_mozog(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        _kijelol(window, qt_app, [0])
        parbeszed = _menubol_nyit(window, qt_app)
        parbeszed.setProperty("printers", ["Alpha", "Beta"])
        valaszto = _elem(window, "printPrinterBox")
        valaszto.setProperty("currentIndex", 2)
        qt_app.processEvents()

        assert str(parbeszed.property("printerName")) == "Beta"
        assert parbeszed.property("pdfSelected") is False

    def test_a_lista_rovidulese_utan_a_kimenet_az_ELVART_helyre_megy(
        self, qml_app, qt_app, tmp_path
    ):
        """A mért forgatókönyv: „Beta" kiválasztva → a nyomtató eltűnik →
        újranyitás. A választó ilyenkor a 0. tételre („PDF-fájlba…") esik
        vissza; a kimenetnek is oda kell mennie."""
        window, _controller, _engine = qml_app
        _kijelol(window, qt_app, [0])
        parbeszed = _menubol_nyit(window, qt_app)
        parbeszed.setProperty("printers", ["Alpha", "Beta"])
        _elem(window, "printPrinterBox").setProperty("currentIndex", 2)
        qt_app.processEvents()
        assert str(parbeszed.property("printerName")) == "Beta"

        # a párbeszéd bezárul, közben a nyomtató lecsatlakozik: az
        # újranyitás a VALÓDI (itt üres) listával tölti újra a választót
        QMetaObject.invokeMethod(
            _elem(window, "printCloseButton"),
            "clicked",
            Qt.ConnectionType.DirectConnection,
        )
        qt_app.processEvents()
        parbeszed = _menubol_nyit(window, qt_app)

        assert parbeszed.property("pdfSelected") is True, (
            "a választó PDF-et mutat, a párbeszéd mégis nyomtatót céloz"
        )
        assert str(parbeszed.property("printerName")) == ""
        cel = tmp_path / "rovidult.pdf"
        parbeszed.setProperty("pdfTarget", cel.as_uri())
        qt_app.processEvents()
        QMetaObject.invokeMethod(
            _elem(window, "printStartButton"),
            "clicked",
            Qt.ConnectionType.DirectConnection,
        )
        qt_app.processEvents()

        assert cel.exists(), (
            "a párbeszéd PDF-et ígért, és nem PDF-be nyomtatott"
        )


class TestCelfajlNemRagad:
    def test_ujranyitaskor_a_PDF_cel_ures(self, qml_app, qt_app, tmp_path):
        """Ha a célfájl túlélné a bezárást, a gomb azonnal élő lenne, a
        `FileDialog` meg sem nyílna — tehát a Qt felülírás-kérdése sem —, és
        az előző PDF kérdés nélkül elveszne."""
        window, _controller, _engine = qml_app
        _kijelol(window, qt_app, [0])
        parbeszed = _menubol_nyit(window, qt_app)
        parbeszed.setProperty("pdfTarget", (tmp_path / "elso.pdf").as_uri())
        qt_app.processEvents()
        QMetaObject.invokeMethod(
            _elem(window, "printCloseButton"),
            "clicked",
            Qt.ConnectionType.DirectConnection,
        )
        qt_app.processEvents()

        parbeszed = _menubol_nyit(window, qt_app)

        assert str(parbeszed.property("pdfTarget")) == ""
        assert _elem(window, "printStartButton").property("enabled") is False


class TestReszlegesKihagyas:
    """⚠️ „Kész", miközben egy kép kimaradt.

    A `QImage` nem nyit meg videót és a legtöbb RAW-t — a rácsban viszont
    MINDKETTŐ látszik (a bélyegkép elkészül), és a képtálca
    nyomtatás-gombja rájuk is élő. A kihagyás korábban csak a naplóba
    került: a `printFinished` sikert jelzett, a lap meg hiányzott.

    Itt a második könyvtárbeli fájlt tesszük olvashatatlanná — a modellben
    változatlanul benne van, tehát ugyanaz az eset, mint a videó/RAW.
    """

    @staticmethod
    def _elrontja(controller, sor: int) -> str:
        ut = pathlib.Path(str(controller.photos.filePathAt(sor)))
        ut.write_bytes(b"ez nem kep")
        return ut.name

    def test_a_kihagyott_kepet_MEGNEVEZI_a_parbeszed(
        self, qml_app, qt_app, tmp_path
    ):
        window, controller, _engine = qml_app
        romlott = self._elrontja(controller, 1)
        _kijelol(window, qt_app, [0, 1])
        parbeszed = _menubol_nyit(window, qt_app)
        cel = tmp_path / "reszleges.pdf"
        parbeszed.setProperty("pdfTarget", cel.as_uri())
        qt_app.processEvents()

        QMetaObject.invokeMethod(
            _elem(window, "printStartButton"),
            "clicked",
            Qt.ConnectionType.DirectConnection,
        )
        qt_app.processEvents()

        # a jó kép kiment…
        assert _pdf_oldalszam(cel.read_bytes()) == 1
        # …de a kimaradt lapról a felhasználó is tud
        figyelmeztetes = _elem(window, "printSkippedText")
        assert figyelmeztetes.property("visible") is True, (
            "egy kép kimaradt, és a párbeszéd sikert mutatott"
        )
        assert romlott in str(figyelmeztetes.property("text"))

    def test_csak_olvashatatlan_kepeknel_az_uzenet_MEGNEVEZI_oket(
        self, qml_app, qt_app, tmp_path
    ):
        """A csak-videós kijelölésnél a „Nincs nyomtatható kép."
        félrevezet: a felhasználó képeket JELÖLT KI, és lát is róluk
        bélyegképet."""
        window, controller, _engine = qml_app
        elso = self._elrontja(controller, 0)
        masodik = self._elrontja(controller, 1)
        _kijelol(window, qt_app, [0, 1])
        parbeszed = _menubol_nyit(window, qt_app)
        parbeszed.setProperty("pdfTarget", (tmp_path / "semmi.pdf").as_uri())
        qt_app.processEvents()

        QMetaObject.invokeMethod(
            _elem(window, "printStartButton"),
            "clicked",
            Qt.ConnectionType.DirectConnection,
        )
        qt_app.processEvents()

        hiba = _elem(window, "printErrorText")
        assert hiba.property("visible") is True
        szoveg = str(hiba.property("text"))
        assert elso in szoveg and masodik in szoveg, (
            f"az üzenet nem nevezi meg a nyomtathatatlan képeket: {szoveg!r}"
        )


class TestNemaElutasitasNincs:
    """A projekt visszatérő hibaosztálya: a felület elfogadja a parancsot,
    aztán némán nem történik semmi."""

    def test_kijeloles_nelkul_MINDHAROM_belepesi_pont_szurke(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        _kijelol(window, qt_app, [])

        assert _elem(window, "menuFilePrint").property("enabled") is False
        assert _elem(window, "trayPrintButton").property("enabled") is False
        assert _elem(window, "shortcutPrint").property("enabled") is False

    def test_a_hibaüzenet_kiirodik_a_parbeszeden(self, qml_app, qt_app, tmp_path):
        """Nem írható célfájl: a vezérlő `printFailed`-je NEM nyelhető el —
        a felhasználó lássa, miért nem nyomtatott a gép."""
        window, _controller, _engine = qml_app
        _kijelol(window, qt_app, [0])
        parbeszed = _menubol_nyit(window, qt_app)
        parbeszed.setProperty(
            "pdfTarget", (tmp_path / "nincs-ilyen-mappa" / "x.pdf").as_uri()
        )
        qt_app.processEvents()

        QMetaObject.invokeMethod(
            _elem(window, "printStartButton"),
            "clicked",
            Qt.ConnectionType.DirectConnection,
        )
        qt_app.processEvents()

        hiba = _elem(window, "printErrorText")
        assert hiba.property("visible") is True, (
            "a nyomtatás elbukott, és a felület NEM szólt róla"
        )
        assert str(hiba.property("text")).strip()
