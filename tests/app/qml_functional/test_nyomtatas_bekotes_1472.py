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
from PySide6.QtCore import QMetaObject, QObject, Qt
from PySide6.QtTest import QTest

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


def _pdf_oldalszam(adat: bytes) -> int:
    """A PDF oldalobjektumainak száma — a `/Type /Pages` gyűjtőt kizárva."""
    return len(re.findall(rb"/Type\s*/Page[^s]", adat))


class TestRegisztracio:
    def test_a_printController_regisztralva_van(self, qml_app):
        """A lánc első szeme: a vezérlő létezik és a QML látja."""
        _window, _controller, engine = qml_app

        assert engine.rootContext().contextProperty("printController") is not None


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
        parbeszed = _elem(window, "printDialog")
        assert parbeszed.property("visible") is False

        QTest.keyClick(window, Qt.Key_P, Qt.ControlModifier)
        qt_app.processEvents()

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
