"""#1276 — a „Klipek" lap a VÁLASZTHATÓ képeket listázza, nem a felhasználtakat.

## A tulajdonos jelentése

> „A Kollázsok szerkesztésekor a »Klipek« menü kurvára semmit sem mutat."

Az ok nem a frissítés volt, hanem a **forrás**: a lap a kollázs SAJÁT
csomópontjait mutatta (`controller.collageNodes`) — vagyis a már feltett
képeket. Üres kollázsnál ez üres lap; és amint a felhasználó feltett
valamit, a lap azt mutatta, amit már NEM kell választani.

Az eredetiben a lap a **készlet**, amiből válogatni lehet („Unused
Pictures") — ezért van rajta „+", „–" és „Továbbiak…".

## A javítás forrása: a képtálca modellje

A #455/#1670 tálca-csomagjában a **felhasználtság az ADATMODELLBEN** él
(`TrayItem.used`), nem a nézetben. A lap ezt szűri (`used === false`), a
fülfelirat száma pedig a `trayUnusedCount`.

## ⚠️ Amit ez az őr NEM fed le

Nem rajzol ki élő kollázs-panelt. A #1153 tanulsága szerint a mesterséges
burokban felépített panel **hamis zöldet ad**, ezért itt szándékosan nem
építünk ilyet: a KÖTÉST állítjuk (forrás-szinten, mutációval mérve), és a
MODELL viselkedését (valódi `AppController`-en). A kirajzolt lista
geometriáját a `test_collage_clips_tab_949.py` fedi.
"""

from __future__ import annotations

from pathlib import Path

_TAB = (
    Path(__file__).resolve().parents[3]
    / "src/picasapy/app/qml/PicasaPy/CollageClipsTab.qml"
)
_PANEL = (
    Path(__file__).resolve().parents[3]
    / "src/picasapy/app/qml/PicasaPy/CollagePanel.qml"
)


class TestAForras:
    def test_a_lista_a_TALCABOL_tolt(self):
        forras = _TAB.read_text(encoding="utf-8")
        assert "model: tab.unusedClips" in forras
        assert "controller.trayItems" in forras

    def test_NEM_a_kollazs_csomopontjaibol(self):
        """Ez a teszt foga: a régi kötés visszatérése bukjon."""
        forras = _TAB.read_text(encoding="utf-8")
        assert "model: tab.controller ? tab.controller.collageNodes" not in forras, (
            "a lap újra a MÁR feltett képeket listázza"
        )

    def test_csak_a_FEL_NEM_HASZNALTAK(self):
        """`used === false` — a felhasznált kép kiesik a választhatókból."""
        forras = _TAB.read_text(encoding="utf-8")
        kezdet = forras.index("readonly property var unusedClips")
        assert "if (!elemek[i].used)" in forras[kezdet : kezdet + 500]

    def test_a_fulfelirat_szama_a_FEL_NEM_HASZNALTAKAT_szamolja(self):
        """A felirat a lap TARTALMÁT nevezi meg — a tulajdonos képernyőképén
        „Klipek (80)" állt egy néhány elemű kollázs mellett."""
        forras = _PANEL.read_text(encoding="utf-8")
        assert "controller.trayUnusedCount" in forras
        assert "controller.collageClipCount" not in forras


class TestAPlusGomb:
    def test_a_kep_a_TALCAN_MARAD(self):
        """A „+” nem eltávolít: felhasználtnak jelöl — a kép a tálcán
        marad, csak a választhatók közül esik ki."""
        forras = _TAB.read_text(encoding="utf-8")
        assert "setTrayUsedRows(tab.librarySelection, true)" in forras


class TestAModellViselkedese:
    """A valódi `AppController` tálca-API-ja — nem mesterséges burok."""

    def test_a_felhasznaltta_jeloles_kiveszi_a_valaszthatokbol(
        self, qml_app, qt_app
    ):
        _window, controller, _engine = qml_app
        elemek = controller.trayItems
        if not elemek:
            import pytest

            pytest.skip("üres tálca — a viselkedést a modell tesztjei fedik")
        elso = elemek[0]["photoId"]
        elotte = controller.trayUnusedCount
        controller._set_tray_used_ids([elso], True)
        assert controller.trayUnusedCount == elotte - 1
        controller._set_tray_used_ids([elso], False)
        assert controller.trayUnusedCount == elotte
