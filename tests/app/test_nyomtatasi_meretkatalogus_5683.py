"""#5683: az eredeti `ytPrintSizes` katalógus és a fizikai méretleképezés."""

from __future__ import annotations

import pytest
from PySide6.QtCore import QSettings

from picasapy.app.print_controller import PrintController
from picasapy.printing.dpi import NyomatMeret


class TestEredetiNyomatmeretKatalogus:
    def test_a_valaszto_az_eredeti_17_azonositot_sorrendben_adja(self, tmp_path):
        settings = QSettings(
            str(tmp_path / "settings.ini"), QSettings.Format.IniFormat
        )
        ctl = PrintController(photo_source=list, settings=settings)

        assert ctl.printSizes() == [
            "M3X4",
            "M3_5X5",
            "M4X5",
            "M4X6",
            "M5X7",
            "M8X10",
            "M5X8CM",
            "M9X13CM",
            "M10X15CM",
            "M13X18CM",
            "M15X20CM",
            "M20X25CM",
            "TARCA",
            "CDSIZE",
            "PASSPORT",
            "CONTACT",
            "TELJES_OLDAL",
        ]

    @pytest.mark.parametrize(
        "azonosito,szelesseg,magassag",
        [
            ("M3X4", 3.0, 4.0),
            ("M3_5X5", 3.5, 5.0),
            ("M4X5", 4.0, 5.0),
            ("M4X6", 4.0, 6.0),
            ("M5X7", 5.0, 7.0),
            ("M8X10", 8.0, 10.0),
            ("M5X8CM", 5 * 0.3937, 8 * 0.3937),
            ("M9X13CM", 9 * 0.3937, 13 * 0.3937),
            ("M10X15CM", 10 * 0.3937, 15 * 0.3937),
            ("M13X18CM", 13 * 0.3937, 18 * 0.3937),
            ("M15X20CM", 15 * 0.3937, 20 * 0.3937),
            ("M20X25CM", 20 * 0.3937, 25 * 0.3937),
            ("TARCA", 2.5, 3.5),
            ("PASSPORT", 2.0, 2.0),
        ],
    )
    def test_a_meret_a_picasa_eredeti_huvelyk_erteke(
        self, azonosito, szelesseg, magassag
    ):
        meret = NyomatMeret[azonosito]

        assert meret.szeles_huvelyk == pytest.approx(szelesseg, abs=1e-10)
        assert meret.magas_huvelyk == pytest.approx(magassag, abs=1e-10)

    def test_a_kulon_utak_a_katalogusban_maradnak_fizikai_becsles_nelkul(
        self, tmp_path
    ):
        settings = QSettings(
            str(tmp_path / "settings.ini"), QSettings.Format.IniFormat
        )
        ctl = PrintController(photo_source=list, settings=settings)

        assert "PASSPORT" in ctl.printSizes()
        assert "CONTACT" in ctl.printSizes()
        assert "CONTACT" not in NyomatMeret.__members__
        assert "CDSIZE" not in NyomatMeret.__members__
