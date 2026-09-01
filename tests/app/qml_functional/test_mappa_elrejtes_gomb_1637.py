"""#1637 — a „Mappa elrejtése” menütétel a felületről.

A tétel eddig `placeholder: true` volt: **látszott, kattintható volt, és
nem csinált semmit**. Ez a fájl azt méri, hogy most tényleg hat — és hogy
a felirata az állapotot követi.

⚠️ A menütétel felirata a menü NYITÁSAKOR dől el (`isFolderHidden`), nem
kötésből: a rejtettség az indexben él, ami nem értesítő tulajdonság.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QObject

_MENU = (
    Path(__file__).resolve().parents[3]
    / "src/picasapy/app/qml/PicasaPy/FolderContextMenu.qml"
)
_PANE = (
    Path(__file__).resolve().parents[3]
    / "src/picasapy/app/qml/PicasaPy/FolderPane.qml"
)


class TestATetelELO:
    def test_mar_NEM_helyfoglalo(self):
        forras = _MENU.read_text(encoding="utf-8")
        kezdet = forras.index('objectName: "folderMenuHideFolder"')
        blokk = forras[kezdet : kezdet + 420]
        assert "placeholder: true" not in blokk, (
            "a „Mappa elrejtése” még mindig néma helyfoglaló (#1637)"
        )
        assert "onTriggered:" in blokk, "nincs kezelője"

    def test_a_jelzest_a_hasab_elkapja(self):
        assert "onHideFolderRequested" in _PANE.read_text(encoding="utf-8"), (
            "a jelzésnek nincs kezelője — néma vezérlő maradna"
        )

    def test_a_felirat_a_menu_nyitasakor_dol_el(self):
        """A rejtettség az indexben él, ami nem értesítő tulajdonság —
        kötésből a felirat sosem frissülne."""
        assert "folderContextMenu.folderHidden =" in _PANE.read_text(
            encoding="utf-8"
        )


class TestAzEloFaban:
    def test_a_tetel_letezik(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        assert window.findChild(QObject, "folderMenuHideFolder") is not None

    def test_a_vezerlo_utja_mukodik(self, qml_app, qt_app):
        """A vezérlő oldala: elrejt, majd visszahoz — kivétel nélkül,
        ismeretlen útvonalra is."""
        _window, controller, _engine = qml_app
        controller.toggleFolderHidden("")  # üres útvonal: ne szálljon el
        controller.toggleFolderHidden("/nincs/ilyen/mappa")
        assert controller.isFolderHidden("/nincs/ilyen/mappa") is False
