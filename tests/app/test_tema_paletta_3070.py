"""#3070 2. lépés — a megjelenítési mód a FELÜLET színein (a tiszta réteg).

Ez a fájl a `app/theme_palette.py` tiszta függvényeit méri: a
tokennév → szín leképezést, az alfa érintetlenségét és azt, hogy a szabály a
`render/display_modes.py` MÉRT függvényeiből jön, nem QML-be másolva.

A renderelt, felületi mérést a testvérfájl végzi
(`tests/app/qml_functional/test_tema_paletta_kirajzolva_3070.py`) — a jegy
elfogadási feltétele kirajzolt kimenetet kér, nem csak színértéket.
"""

from __future__ import annotations

import pytest
from PySide6.QtGui import QColor

from picasapy.app.theme_palette import qobject_color_tokens, theme_palette
from picasapy.render.display_modes import (
    LCD_MULTIPLIER,
    PROJECTOR_MULTIPLIER,
)

#: Néhány valódi téma-token (a `Theme.qml`-ből), hogy a próba ne kitalált
#: színeken mérjen.
TOKENEK = {
    "canvasBg": QColor("#eaeaea"),
    "contentPanel": QColor("#ffffff"),
    "ink": QColor("#1c1b19"),
    "picasaGreen": QColor("#3b8f00"),
    #: áttetsző token — a szerkesztő kijelölésen kívüli sötétítése
    "selectionDim": QColor("#8f2f2f2f"),
}


class TestANoopModok:
    @pytest.mark.parametrize("mode", ["normal", "auto", "dither16", "rdesk", "", "nincs-ilyen"])
    def test_ures_palettat_ad(self, mode):
        """Üres paletta = a `Theme` a nyers értékeket használja, tehát a
        felület képe nem mozdul. Ez a mód-nélküli állapot is."""
        assert theme_palette(TOKENEK, mode) == {}

    def test_ures_tokenkeszletre_is_ures(self):
        assert theme_palette({}, "bw") == {}


class TestAModokHatasa:
    def test_minden_token_atjon(self):
        paletta = theme_palette(TOKENEK, "bw")
        assert set(paletta) == set(TOKENEK)

    def test_a_bw_szurket_ad(self):
        """A `bw` kereszt-csatornás: a három csatorna egyenlő lesz."""
        for szin in theme_palette(TOKENEK, "bw").values():
            c = QColor(szin)
            assert c.red() == c.green() == c.blue(), szin

    def test_a_szepia_melegit(self):
        """A szépia a szürkénél MELEGEBB: R > B minden nem-fekete tokenen."""
        paletta = theme_palette(TOKENEK, "sepia")
        c = QColor(paletta["canvasBg"])
        assert c.red() > c.blue(), paletta["canvasBg"]

    @pytest.mark.parametrize(
        "mode,szorzo", [("projector", PROJECTOR_MULTIPLIER), ("lcd", LCD_MULTIPLIER)]
    )
    def test_a_sotetitok_a_MERT_szorzot_hasznaljak(self, mode, szorzo):
        """Nem „kb. sötétebb": a mért egész aritmetika (`(c · m) >> 8`)."""
        paletta = theme_palette({"canvasBg": QColor("#eaeaea")}, mode)
        c = QColor(paletta["canvasBg"])
        assert c.red() == (0xEA * szorzo) >> 8

    def test_a_mac_gamma_vilagosit(self):
        """A #1580 mérése szerint a `mac` a FELÜLETET is világosítja."""
        paletta = theme_palette(TOKENEK, "mac")
        assert QColor(paletta["canvasBg"]).red() > 0xEA

    def test_az_overflow_a_TISZTA_fehéret_jeloli(self):
        """A 11.7 szerint az eredeti a GYÖKÉREN alkalmazza a módot, tehát a
        felület fehér paneljei is megkapják a jelölést. A `canvasBg` (#eaeaea)
        NEM tiszta fehér, tehát érintetlen."""
        paletta = theme_palette(TOKENEK, "overflow")
        assert QColor(paletta["contentPanel"]) == QColor("#ff7f7f")
        assert QColor(paletta["canvasBg"]) == QColor("#eaeaea")


class TestAzAlfa:
    def test_az_alfa_valtozatlan(self):
        """A módok RGB-n dolgoznak — az alfa a bemenetről jön (spec 5.4/5.5)."""
        for mode in ("bw", "sepia", "projector", "lcd", "mac", "linear", "overflow"):
            paletta = theme_palette(TOKENEK, mode)
            assert QColor(paletta["selectionDim"]).alpha() == 0x8F, mode

    def test_a_formatum_ARGB_hexa(self):
        """A QML a `#AARRGGBB` alakot olvassa — alfa nélkül a félig áttetsző
        tokenek átlátszatlanná válnának."""
        for szin in theme_palette(TOKENEK, "bw").values():
            assert szin.startswith("#") and len(szin) == 9, szin


class TestAMetaobjektumBejaras:
    def test_csak_a_szin_tulajdonsagokat_hozza(self, qt_app):
        """A bejárás a Qt metaobjektumán megy — így egy JÖVŐBEN hozzáadott
        token magától bekerül, felsorolás nélkül."""
        from PySide6.QtCore import Property, QObject

        class Proba(QObject):
            @Property(QColor)
            def piros(self):
                return QColor("#ff0000")

            @Property(int)
            def meret(self):
                return 12

        tokenek = qobject_color_tokens(Proba())
        assert list(tokenek) == ["piros"]
        assert tokenek["piros"] == QColor("#ff0000")
