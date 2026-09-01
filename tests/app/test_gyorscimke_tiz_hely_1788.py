"""Tíz gyorscímke-hely, migrációval és elvethető szerkesztéssel — #1788.

## A tízes szám

Két független mérésből: a `quicktagconfig` panel elemleltára `edit_0` …
`edit_9` mezőket sorol (tíz), a kezelő ciklushatára pedig
`cmp eax, 0xa` (0x0083efa2). Nálunk nyolc volt.

## A gombok — KIMONDOTT döntés

A jegy a megvalósítóra bízta, de kikötötte, hogy ki kell mondani. A
döntés: **átvesszük az eredeti OK/Mégse mintát** (a panelen
`quicktagconfig/ok` és `/cancel` vezérlő is van). A „Bezárás"-nál maradni
azért lett elvetve, mert a mezők AZONNAL írnak (`onEditingFinished`) — egy
elgépelt címke visszavonhatatlan lett volna.

Ez a teszt azért állítja a döntést, mert a #416/#422 tanulsága szerint a
kimondatlan eltérésből egy későbbi kör „hibát" csinál, és újra levezeti.
"""

from __future__ import annotations

from pathlib import Path

import picasapy.app
import pytest
from PySide6.QtCore import QSettings
from support.jpeg_factory import make_jpeg

from picasapy.app.keywords_controller import (
    _KEY_QUICK_LABELS,
    _QUICK_TAG_SLOTS,
)

_DIALOG = (
    Path(picasapy.app.__file__).parent
    / "qml" / "PicasaPy" / "QuickTagsConfigDialog.qml"
).read_text(encoding="utf-8")
_PANEL = (
    Path(picasapy.app.__file__).parent
    / "qml" / "PicasaPy" / "TagsPanel.qml"
).read_text(encoding="utf-8")


@pytest.fixture
def library(tmp_path):
    root = tmp_path / "kepek"
    (root / "nyaralas").mkdir(parents=True)
    make_jpeg(root / "nyaralas" / "IMG_0001.jpg")
    return root


def _controller(tmp_path, library, settings):
    from picasapy.app.controller import AppController
    from picasapy.app.thumbnail_provider import ThumbnailProvider
    from picasapy.index import open_index, sync_tree
    from picasapy.thumbs import ThumbnailCache

    with open_index(tmp_path / "index.db") as conn:
        sync_tree(conn, library)
    provider = ThumbnailProvider(ThumbnailCache(tmp_path / "thumbs", size=32))
    return AppController(
        tmp_path / "index.db", (str(library),), provider, settings=settings
    )


class TestATizHely:
    def test_a_konstans_tiz(self):
        assert _QUICK_TAG_SLOTS == 10

    def test_a_dialogusban_tiz_mezo_van(self):
        for slot in range(10):
            assert f"slot: {slot} }}" in _DIALOG, f"hiányzik a(z) {slot}. mező"
        assert "slot: 10 }" not in _DIALOG

    def test_a_panelen_tiz_gomb_van(self):
        for slot in range(10):
            assert f"QuickTagButton {{ slot: {slot} }}" in _PANEL, slot
        assert "QuickTagButton { slot: 10 }" not in _PANEL

    def test_a_dialogus_szovege_is_tizet_mond(self):
        """A felirat nem maradhat »8« — azt a felhasználó olvassa."""
        assert "Edit the 10 quick tag buttons" in _DIALOG
        assert "Edit the 8 quick tag buttons" not in _DIALOG


class TestAMigracio:
    def test_a_nyolc_mentett_ertek_NEM_vesz_el(self, qt_app, tmp_path, library):
        """A jegy migrációs pontja: nyolc mentett érték, tíz mező.

        Ez a bővítés valódi kockázata — a régi beállítás a felhasználó
        munkája, és a listahossz-változás némán elnyelhetné."""
        settings = QSettings(
            str(tmp_path / "settings.ini"), QSettings.Format.IniFormat
        )
        regi = [f"cimke{i}" for i in range(8)]
        settings.setValue(_KEY_QUICK_LABELS, regi)
        settings.sync()

        ctl = _controller(tmp_path, library, settings)
        labels = ctl.quickTagConfigLabels

        assert len(labels) == 10
        assert labels[:8] == regi, "a régi nyolc érték nem maradt a helyén"
        assert labels[8:] == ["", ""], "a két új hely nem üresen indul"

    def test_a_ket_uj_hely_ir_es_megmarad(self, qt_app, tmp_path, library):
        settings = QSettings(
            str(tmp_path / "settings.ini"), QSettings.Format.IniFormat
        )
        ctl = _controller(tmp_path, library, settings)
        ctl.setQuickTagLabel(9, "tizedik")
        ctl._get_settings().sync()

        masik = _controller(tmp_path, library, settings)
        assert masik.quickTagConfigLabels[9] == "tizedik"


class TestAFelsoKetto:
    def test_a_lefoglalas_tovabbra_is_az_elso_kettot_tiltja(self):
        """A bővítés nem tolhatja el a »felső kettő« határát."""
        assert "field.slot < 2" in _DIALOG


class TestAGombdontes:
    def test_OK_es_Megse_van_Bezaras_helyett(self):
        assert "standardButtons: Dialog.Ok | Dialog.Cancel" in _DIALOG
        assert "standardButtons: Dialog.Close" not in _DIALOG

    def test_a_Megse_VISSZAALLIT(self):
        """Nem elég a gomb: a mezők már írtak, tehát vissza kell írni."""
        assert "onRejected:" in _DIALOG
        kezd = _DIALOG.index("onRejected:")
        blokk = _DIALOG[kezd : kezd + 420]
        assert "setQuickTagLabel" in blokk
        assert "setQuickTagsReserveRecent" in blokk
        assert "setQuickTagsAutoFillFrequent" in blokk

    def test_a_megnyitas_PILLANATFELVETELT_vesz(self):
        """Visszaállítani csak abból lehet, amit megnyitáskor eltettünk."""
        kezd = _DIALOG.index("onOpened:")
        blokk = _DIALOG[kezd : kezd + 420]
        assert "kiindulasiCimkek" in blokk
        assert "kiindulasiReserve" in blokk
        assert "kiindulasiAutoFill" in blokk

    def test_a_dontes_INDOKA_le_van_irva(self):
        """A #416/#422 tanulsága: a kimondatlan eltérésből egy későbbi kör
        »hibát« csinál. A fájl fejlécének meg kell mondania, MIÉRT."""
        fejlec = _DIALOG[: _DIALOG.index("Dialog {")]
        assert "#1788" in fejlec
        assert "onEditingFinished" in fejlec, "hiányzik az azonnali írás indoka"
        assert "quicktagconfig/ok" in fejlec, "hiányzik a mért erőforrás"
