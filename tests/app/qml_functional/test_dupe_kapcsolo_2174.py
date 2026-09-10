"""#2174 — a keresősáv duplikátum-kapcsolója (`searchoptions/dupesearch`).

MÉRVE: a kapcsoló **alapból REJTETT** — a főablak-építő a vtable `+0x68`-cal
elrejti (`0x0040c8c9`), a `Ctrl+F6` ága a `+0x6c`-vel megjeleníti
(`0x005e62c8`) —, és az átbillentése **bitre ugyanazt** a hívást indítja,
mint a menüparancs (`0x005d95af` → `0x0065b840`, a menüparancs
`0x005ccc14`-ből ugyanoda). Nálunk ezért nem lehet két külön ág: a kapcsoló
is a `showDuplicateFiles()` / `clearFilter()` páron megy, amit a menüpont hív.

A mód maga a #1398-ban készült el (`app/dupe_search_controller.py`); ez a
jegy csak a keresősáv kapcsolóját teszi mellé.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QObject
from tests.support.qml_blokk import blokk_horgonyra

_TOOLBAR = (
    Path(__file__).resolve().parents[3]
    / "src/picasapy/app/qml/PicasaPy/MainToolbar.qml"
)


class TestAKapcsoloMegvan:
    def test_a_szuro_zonaban_ott_a_kapcsolo(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        assert window.findChild(QObject, "dupeFilter") is not None, (
            "nincs duplikátum-kapcsoló a keresősávon (#2174)"
        )

    def test_van_hozza_buborekusgo(self):
        assert "Show duplicate files only" in _TOOLBAR.read_text(
            encoding="utf-8"
        )


class TestAlapbolREJTETT:
    def test_indulaskor_nem_latszik(self, qml_app, qt_app):
        """MÉRVE: a főablak-építő elrejti; csak a mód bekapcsolásakor jön elő."""
        window, controller, _engine = qml_app
        assert controller.viewModeName == "folder"
        kapcsolo = window.findChild(QObject, "dupeFilter")
        assert kapcsolo.property("visible") is False

    def test_a_modban_LATSZIK(self, qml_app, qt_app):
        window, controller, _engine = qml_app
        try:
            controller._on_dupes_ready(())
            qt_app.processEvents()
            kapcsolo = window.findChild(QObject, "dupeFilter")
            assert controller.viewModeName == "dupes"
            assert kapcsolo.property("visible") is True
        finally:
            controller.clearFilter()
            qt_app.processEvents()

    def test_masik_szuro_NEM_hozza_elo(self, qml_app, qt_app):
        """A csillag-szűrő nem duplikátum-mód — a kapcsoló maradjon rejtve."""
        window, controller, _engine = qml_app
        try:
            controller.showStarred()
            qt_app.processEvents()
            assert window.findChild(QObject, "dupeFilter").property(
                "visible"
            ) is False
        finally:
            controller.clearFilter()
            qt_app.processEvents()


class TestKOZOS_ut_a_menuponttal:
    def test_a_kapcsolo_ugyanazt_a_ket_belepot_hivja(self):
        """Az eredetiben a kapcsoló és a menüparancs bitre azonos hívás —
        nálunk sem lehet két külön ág."""
        blokk = blokk_horgonyra(
            _TOOLBAR.read_text(encoding="utf-8"), 'objectName: "dupeFilter"'
        )
        assert "controller.clearFilter()" in blokk
        assert "controller.showDuplicateFiles()" in blokk

    def test_a_kapcsolo_a_viewModeName_bol_dolgozik(self):
        blokk = blokk_horgonyra(
            _TOOLBAR.read_text(encoding="utf-8"), 'objectName: "dupeFilter"'
        )
        assert "viewModeName" in blokk
        assert '"dupes"' in blokk
