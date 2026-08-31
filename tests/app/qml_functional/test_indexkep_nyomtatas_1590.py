"""Az indexkép-nyomtatás útja VÉGIG: menüpont → párbeszéd → vezérlő →
LEMEZRE ÍRT PDF (#1590).

## A lelet

A #1590 jegy azt írta, hogy a menüpont „nincs (grep: 0 találat a
QML-ben)", és hogy a `PrintController` „soha nem példányosul". MÉRVE
(2026-08-27) mindkettő elavult:

* a `Print Thumbnails...` tétel MEGVOLT a `PicasaMenuBar.qml`-ben, csak
  `PicasaMenuItem { placeholder: true }`-ként — vagyis szürkén,
  kattinthatatlanul;
* a `PrintController` a #1472 óta példányosul (`application.py:813`) és
  regisztrálva van (`application.py:883`).

Ami TÉNYLEG hiányzott: az indexkép-RAJZOLÓ. A `print_controller.py` egy
képet tett egy oldalra, és a #1472 ezért hagyta SZÁNDÉKOSAN
helyfoglalónak a tételt. Ez a kör azt a motort építi meg
(`printing/contact_sheet.py`), és teszi élővé a tételt.

## Miért ilyen ez a teszt

A vezérlő metódusait közvetlenül hívni semmit nem érne: pontosan az a
hibaosztály, hogy a kész motorhoz nem vezet felületi út (#1472/#1476).
Ezért a VALÓDI menütételt aktiválja — előbb megkövetelve, hogy ne legyen
helyfoglaló —, a párbeszéd VALÓDI gombját kattintja, és a végén a
LEMEZRE ÍRT PDF oldalszámát méri.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from PySide6.QtCore import QMetaObject, QObject, Qt
from PySide6.QtTest import QTest

import picasapy.app

try:
    import PySide6.QtPrintSupport  # noqa: F401

    _QTPRINTSUPPORT_VAN = True
except ImportError:  # pragma: no cover — csak a hiányos telepítésen fut
    _QTPRINTSUPPORT_VAN = False

pytestmark = pytest.mark.skipif(
    not _QTPRINTSUPPORT_VAN,
    reason=(
        "a PySide6.QtPrintSupport modul hiányzik ezen a gépen. Debian/Ubuntu "
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


def _pdf_oldalszam(adat: bytes) -> int:
    return len(re.findall(rb"/Type\s*/Page[^s]", adat))


def _menubol_nyit(window, qt_app):
    """A VALÓDI menütétel aktiválása."""
    tetel = _elem(window, "menuFolderPrintContactSheet")
    assert tetel.property("enabled") is True, (
        "az Indexképek nyomtatása… menüpont le van tiltva"
    )
    assert not tetel.property("placeholder"), (
        "az Indexképek nyomtatása… menüpont még mindig helyfoglaló (#416)"
    )
    QMetaObject.invokeMethod(tetel, "triggered", Qt.ConnectionType.DirectConnection)
    qt_app.processEvents()
    return _elem(window, "printDialog")


def _nyomtat(window, qt_app, parbeszed, cel: Path):
    parbeszed.setProperty("pdfTarget", cel.as_uri())
    qt_app.processEvents()
    gomb = _elem(window, "printStartButton")
    assert gomb.property("enabled") is True, "a Nyomtatás gomb szürke maradt"
    QMetaObject.invokeMethod(gomb, "clicked", Qt.ConnectionType.DirectConnection)
    qt_app.processEvents()


class TestBelepesiPont:
    def test_a_menupont_ELO_es_indexkep_modban_nyit(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        _kijelol(window, qt_app, [0, 1])

        parbeszed = _menubol_nyit(window, qt_app)

        assert parbeszed.property("visible") is True
        assert parbeszed.property("contactSheet") is True, (
            "a menüpont a KÉPENKÉNTI nyomtatást nyitotta meg"
        )

    def test_a_ctrl_shift_p_ugyanoda_vezet(self, qml_app, qt_app):
        """VALÓDI billentyűleütés — a felirat Ctrl+Shift+P-t hirdet."""
        window, _controller, _engine = qml_app
        _kijelol(window, qt_app, [0])
        # #1720: a párbeszéd HALASZTOTT — a billentyű ELŐTT létre sem jön.
        assert window.findChild(QObject, "printDialog") is None, (
            "a nyomtatás ablaka már a billentyű előtt felépült — a #1720 "
            "halasztása elromlott"
        )

        QTest.keyClick(
            window, Qt.Key_P, Qt.ControlModifier | Qt.ShiftModifier
        )
        qt_app.processEvents()

        parbeszed = _elem(window, "printDialog")
        assert parbeszed.property("visible") is True
        assert parbeszed.property("contactSheet") is True

    def test_a_Ctrl_P_UTANA_is_kepenkenti_lapot_nyit(self, qml_app, qt_app):
        """⚠️ Az indexkép-mód nem élheti túl a bezárást: a Ctrl+P
        legközelebb szó nélkül indexképet nyomtatna."""
        window, _controller, _engine = qml_app
        _kijelol(window, qt_app, [0, 1])
        parbeszed = _menubol_nyit(window, qt_app)
        assert parbeszed.property("contactSheet") is True
        QMetaObject.invokeMethod(
            _elem(window, "printCloseButton"),
            "clicked",
            Qt.ConnectionType.DirectConnection,
        )
        qt_app.processEvents()

        QTest.keyClick(window, Qt.Key_P, Qt.ControlModifier)
        qt_app.processEvents()

        assert parbeszed.property("contactSheet") is False


class TestKimenet:
    """A lánc utolsó szeme: a menüpont LEMEZRE ÍRT indexképet ad."""

    def test_ket_kep_EGY_lapra_kerul(self, qml_app, qt_app, tmp_path):
        """Ez a különbség a képenkénti nyomtatáshoz képest: ott két kép két
        lap (`test_nyomtatas_bekotes_1472.py`), itt EGY."""
        window, _controller, _engine = qml_app
        _kijelol(window, qt_app, [0, 1])
        parbeszed = _menubol_nyit(window, qt_app)
        cel = tmp_path / "indexkep.pdf"

        _nyomtat(window, qt_app, parbeszed, cel)

        assert cel.exists(), "a menüpont NEM írt fájlt"
        adat = cel.read_bytes()
        assert adat.startswith(b"%PDF")
        assert _pdf_oldalszam(adat) == 1, (
            "a két kép két külön lapra került — ez nem indexkép"
        )

    def test_az_oszlopszam_TOBB_lapra_bonthatja_a_feladatot(
        self, qml_app, qt_app, tmp_path
    ):
        """Egy oszlop mellett A4-en egyetlen sor fér ki, tehát a két kép
        két lapra kerül — a beállítás tehát TÉNYLEGESEN hat a kimenetre."""
        window, _controller, _engine = qml_app
        _kijelol(window, qt_app, [0, 1])
        parbeszed = _menubol_nyit(window, qt_app)
        parbeszed.setProperty("contactColumns", 1)
        qt_app.processEvents()
        cel = tmp_path / "egyoszlop.pdf"

        _nyomtat(window, qt_app, parbeszed, cel)

        assert _pdf_oldalszam(cel.read_bytes()) == 2

    def test_a_siker_visszajelzese_megjelenik(self, qml_app, qt_app, tmp_path):
        window, _controller, _engine = qml_app
        _kijelol(window, qt_app, [0, 1])
        parbeszed = _menubol_nyit(window, qt_app)

        _nyomtat(window, qt_app, parbeszed, tmp_path / "ok.pdf")

        eredmeny = _elem(window, "printResultText")
        assert eredmeny.property("visible") is True
        assert str(eredmeny.property("text")).strip()


class TestCelpont:
    """Kijelölés nélkül a MEGNYITOTT MAPPA egésze a célpont — az eredetiben
    ez a parancs a mappa tétele, nem a kijelölésé."""

    def test_kijeloles_nelkul_a_TELJES_mappa_megy(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        _kijelol(window, qt_app, [])

        parbeszed = _menubol_nyit(window, qt_app)

        ertek = parbeszed.property("rows")
        nyers = ertek.toVariant() if hasattr(ertek, "toVariant") else ertek
        assert sorted(int(r) for r in (nyers or [])) == [0, 1], (
            "kijelölés nélkül a menüpont üres feladatot nyitott"
        )

    def test_kijelolessel_CSAK_a_kijeloltek_mennek(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        _kijelol(window, qt_app, [1])

        parbeszed = _menubol_nyit(window, qt_app)

        ertek = parbeszed.property("rows")
        nyers = ertek.toVariant() if hasattr(ertek, "toVariant") else ertek
        assert [int(r) for r in (nyers or [])] == [1]


class TestKozosElrendezes:
    """A #1590 előírása: a rács ne legyen külön megvalósítás.

    ⚠️ A FEJLÉC viszont MÁS, és ez mérés, nem hanyagság: az eredeti
    nyomtatója címkézett mezőket rajzol (`ytPrinter::contactsheetalbum` =
    „Album:", `ytPrinter::contactsheetdate` = „Dátum:"), az indexkép-
    KOLLÁZS fejléce pedig a `CContactSheetTheme::subtitle_format`
    („%1$d kép, %2$s") mintát követi.
    """

    def test_a_racsot_a_kollazs_indexkep_elrendezese_adja(self):
        forras = (
            Path(picasapy.app.__file__).parents[1]
            / "printing"
            / "contact_sheet.py"
        ).read_text(encoding="utf-8")

        assert "from picasapy.collage.layout import" in forras, (
            "a nyomtatott indexkép SAJÁT rácsszámolót kapott a kollázsé helyett"
        )
        assert "contact_sheet_layout" in forras


class TestNemaElutasitasNincs:
    def test_ures_mappaban_a_gyorsbillentyu_szurke(self, qml_app, qt_app):
        """A gyorsbillentyűnek nincs hova visszajeleznie, ezért az —
        a menütétellel ellentétben — feltételhez kötött."""
        window, _controller, _engine = qml_app
        _kijelol(window, qt_app, [])

        assert (
            _elem(window, "shortcutPrintContactSheet").property("enabled")
            is False
        )

    def test_olvashatatlan_kepet_MEGNEVEZI(self, qml_app, qt_app, tmp_path):
        window, controller, _engine = qml_app
        ut = Path(str(controller.photos.filePathAt(1)))
        ut.write_bytes(b"ez nem kep")
        _kijelol(window, qt_app, [0, 1])
        parbeszed = _menubol_nyit(window, qt_app)

        _nyomtat(window, qt_app, parbeszed, tmp_path / "reszleges.pdf")

        figyelmeztetes = _elem(window, "printSkippedText")
        assert figyelmeztetes.property("visible") is True, (
            "egy kép kimaradt, és a párbeszéd sikert mutatott"
        )
        assert ut.name in str(figyelmeztetes.property("text"))
