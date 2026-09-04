"""Az Időrend belépési pontjai inaktívak, amíg a valódi nézet nincs kész — #1903.

A tulajdonos élesben jelentette, két képernyőképpel (PicasaPy vs. Picasa 3),
és a bináris megerősíti: **az eredeti Időrend nem rácsnézet**, hanem TELJES
KÉPERNYŐS, ANIMÁLT BEMUTATÓ a diavetítő motorján.

| bizonyíték | mit mond |
|---|---|
| `0x008037e0`: `oneup/timeline` + `BigSlideshow2` + `qshow` + `oneup/transtype` | a diavetítő motorján fut, `oneup` (teljes képernyős) módban |
| `0x00816b00`: `CTransTimeline` | ÁTMENET-osztály, nem nézetmód |
| `0x007fb210`: `overlays/timeline` · `timelinedot` · `sliderthumb` · `startbutton` · `exit` | saját, RÁTÉTES vezérlősáv |
| `CThumbUI::MakeTimeline` = „Időrend előkészítése…" | előkészítő fázis |

⇒ A miénk lapos rács volt hónap-fejlécekkel: **más felépítés, más vezérlők,
más motor.** A fejlécbe tett váltógomb az eredetiben ezen a helyen nem
létezik — az Időrend vezérlői a teljes képernyős rátéten ülnek.

## Amit ez a kör tesz — és amit NEM

A valódi nézet megépítése külön kör (a görbe alakja, a képek elhelyezése és
az animáció időzítése **nincs feltárva**). Ez a kör csak annyit tesz, hogy a
felület **ne ígérjen olyat, amit nem ad**:

* a fejléc váltógombja eltűnik,
* a `Nézet ▸ Időrend` **inaktív**, a `Ctrl+5` nem sül el,
* a menütétel **HELYE és FELIRATA megmarad** — az eredetiben létezik, csak
  a tartalma nincs kész.

Egy kattintható vezérlő, ami mást ad, mint amit ígér, rosszabb, mint a
hiánya (#936).
"""

from __future__ import annotations

from pathlib import Path

import picasapy.app

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
        assert "onTimelineRequested" not in _MAIN
        assert "timelineActive:" not in _MAIN


class TestAMenutetel:
    def test_a_tetel_HELYE_megmarad(self):
        """Az eredetiben létezik — a hely nem tűnhet el, csak a tartalom
        nincs kész."""
        assert 'objectName: "menuViewTimeline"' in _MENU
        assert 'text: qsTr("Timeline") + "\\tCtrl+5"' in _MENU

    def test_a_tetel_INAKTIV(self):
        kezd = _MENU.index('objectName: "menuViewTimeline"')
        assert "enabled: false" in _MENU[kezd : kezd + 300]


class TestABillentyu:
    def test_a_Ctrl5_NEM_sul_el(self):
        """A billentyű nem kerülheti meg a szürke menüpontot — a #1686
        fordított esete: ott a billentyű MŰKÖDÖTT, miközben a tétel
        helyfoglaló volt."""
        kezd = _MAIN.index('sequence: "Ctrl+5"')
        assert "enabled: false" in _MAIN[kezd : kezd + 200]


class TestAKirajzoltFelulet:
    def test_a_menutetel_szurke_a_valodi_ablakban(self, qml_app, qt_app):
        from PySide6.QtCore import QObject

        window, _controller, _engine = qml_app[:3]
        tetel = window.findChild(QObject, "menuViewTimeline")
        assert tetel is not None, "a menütétel eltűnt a kirajzolt ablakból"
        assert tetel.property("enabled") is False

    def test_nincs_idorend_gomb_a_kirajzolt_fejlecben(self, qml_app, qt_app):
        from PySide6.QtCore import QObject

        window, _controller, _engine = qml_app[:3]
        assert window.findChild(QObject, "toolbarTimelineButton") is None
