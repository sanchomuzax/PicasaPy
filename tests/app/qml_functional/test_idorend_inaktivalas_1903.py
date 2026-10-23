"""Az Időrend belépési pontjai a valódi teljes képernyős módra vezetnek (#5377).

Az eredeti Időrend nem rácsnézet, hanem teljes képernyős bemutató saját
rátétes vezérlősávval. A fejlécben nincs Időrend-gomb.

| bizonyíték | mit mond |
|---|---|
| `0x008037e0`: `oneup/timeline` + `BigSlideshow2` + `qshow` + `oneup/transtype` | a diavetítő motorján fut, `oneup` (teljes képernyős) módban |
| `0x00816b00`: `CTransTimeline` | ÁTMENET-osztály, nem nézetmód |
| `0x007fb210`: `overlays/timeline` · `timelinedot` · `sliderthumb` · `startbutton` · `exit` | saját, RÁTÉTES vezérlősáv |
| `CThumbUI::MakeTimeline` = „Időrend előkészítése…" | előkészítő fázis |

⇒ A miénk lapos rács volt hónap-fejlécekkel: **más felépítés, más vezérlők,
más motor.** A fejlécbe tett váltógomb az eredetiben ezen a helyen nem
létezik - az Időrend vezérlői a teljes képernyős rátéten ülnek.

## Belépési pontok

* a fejlécben nincs Időrend-gomb,
* a `Nézet ▸ Időrend` aktív,
* a `Ctrl+5` kijelölés nélkül is megnyitja a bemutatót.
"""

from __future__ import annotations

from pathlib import Path

import picasapy.app
from tests.support.qml_blokk import blokk_horgonyra

_TOOLBAR = (
    Path(picasapy.app.__file__).parent
    / "qml" / "PicasaPy" / "MainToolbar.qml"
).read_text(encoding="utf-8")
#: ⚠️ #2152: az `&` a MNEMONIK jelölése, nem a felirat tartalma. Ez a fájl a
#: menütételek MEGLÉTÉT és a gyorsbillentyűjüket méri, arra nézve jelölés.
_MENU = (
    Path(picasapy.app.__file__).parent
    / "qml" / "PicasaPy" / "PicasaMenuBar.qml"
).read_text(encoding="utf-8").replace("&", "")
_MAIN = (
    Path(picasapy.app.__file__).parent / "qml" / "Main.qml"
).read_text(encoding="utf-8")


class TestAFejlecGomb:
    def test_nincs_tobbe_idorend_gomb_az_eszkoztaron(self):
        assert 'objectName: "toolbarTimelineButton"' not in _TOOLBAR

    def test_az_arva_jelzes_es_allapot_is_eltunt(self):
        """Bekötetlen jelzés/állapot néma lánc-szakadás lenne."""
        assert "timelineRequested" not in _TOOLBAR
        assert "timelineActive" not in _TOOLBAR

    def test_a_gazdaablak_sem_koti_be(self):
        assert "onTimelineRequested: window.toggleTimeline()" in _MAIN
        assert "timelineActive:" not in _MAIN


class TestAMenutetel:
    def test_a_tetel_HELYE_megmarad(self):
        """Az eredetiben létezik - a hely nem tűnhet el, csak a tartalom
        nincs kész."""
        assert 'objectName: "menuViewTimeline"' in _MENU
        assert 'text: qsTr("Timeline") + "\\tCtrl+5"' in _MENU

    def test_a_tetel_aktiv(self):
        assert "enabled: true" in blokk_horgonyra(
            _MENU, 'objectName: "menuViewTimeline"'
        )


class TestABillentyu:
    def test_a_Ctrl5_aktiv(self):
        assert "enabled: !window.viewerOpen && !slideshow.visible" in blokk_horgonyra(
            _MAIN, 'sequence: "Ctrl+5"'
        )


class TestAKirajzoltFelulet:
    def test_a_menutetel_aktiv_a_valodi_ablakban(self, qml_app, qt_app):
        from PySide6.QtCore import QObject

        window, _controller, _engine = qml_app[:3]
        tetel = window.findChild(QObject, "menuViewTimeline")
        assert tetel is not None, "a menütétel eltűnt a kirajzolt ablakból"
        assert tetel.property("enabled") is True

    def test_nincs_idorend_gomb_a_kirajzolt_fejlecben(self, qml_app, qt_app):
        from PySide6.QtCore import QObject

        window, _controller, _engine = qml_app[:3]
        assert window.findChild(QObject, "toolbarTimelineButton") is None
