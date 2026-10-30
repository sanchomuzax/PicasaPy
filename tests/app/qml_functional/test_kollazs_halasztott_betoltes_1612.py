"""#1612 — a Kollázs-panel csak az első megnyitáskor jön létre.

## A mérés, amiből ez következik

A jegy komponensenkénti mérése (`eszkozok/meres/qml_komponens_idok.py`,
2026-09-15) a `Main.qml` fájában **két** olyan komponenst talált, ami az
induláskor MÁR létrejön, de a felhasználó akkor NEM látja:

| komponens | izolált példányosítás | látszik induláskor? |
|---|---:|---|
| `CollagePanel` (`Main.qml`) | 74,5 ms | nem — külön dokumentum-lap |
| `EditorPanel` (`PhotoViewer.qml`) | 76,8 ms | nem — csak szerkesztő módban |

A mérés azt is kimondta, ami MEGFORDÍTJA a kézenfekvő tervet: a legdrágább
komponens (`VideoPlayerView`, 674 ms) és az összes párbeszéd **már** halasztott,
ott nincs mit nyerni.

Ez a fájl a `CollagePanel`-t őrzi. (Az `EditorPanel` halasztása külön szelet:
a `PhotoViewer.qml`-ben **104** kötés hivatkozik rá közvetlenül, tehát ott a
halasztás nem egy `Loader`, hanem a kötések null-biztossá tétele — az a munka
más kockázatú, és önálló jegyet kapott.)

## Amit ez az őr állít

- induláskor a `collagePanel` **nem létezik** (a `Loader` inaktív);
- a Kollázs lap megnyitásakor létrejön és LÁTSZIK — tehát a halasztás nem
  helyfoglaló (#1475/#1052/#1526 hibaosztály);
- visszaváltás után **megmarad** (nem semmisül meg), így a félkész kollázs nem
  veszik el — ez a `Loader` `active`-jának ragadós ága;
- a `Loader` a mutáció-próbán is fog: ha valaki `active: true`-ra állítja, az
  első állítás bukik.
"""

from __future__ import annotations

import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from tests.support.collage_wiring_985 import (  # noqa: E402
    _elem,
    _keres,
    _kollazs_lapot_nyit,
    _konyvtar_fulre,
    _var,
)


class TestAHalasztas:
    def test_indulaskor_a_panel_MEG_NEM_letezik(self, qml_app, qt_app):
        window = qml_app[0]
        qt_app.processEvents()
        assert _keres(window, "collagePanel") is None, (
            "a Kollázs-panel az induláskor létrejött — a #1612 szerint ez "
            "74,5 ms, amit a felhasználó nem lát"
        )
        betolto = _elem(window, "collagePanelLoader")
        assert betolto.property("active") is False, (
            "a betöltő induláskor aktív — akkor a halasztás nem halaszt"
        )

    def test_a_lap_megnyitasakor_letrejon_es_LATSZIK(self, qml_app, qt_app):
        window = qml_app[0]
        _kollazs_lapot_nyit(window, qt_app)
        assert _var(qt_app, lambda: _keres(window, "collagePanel") is not None), (
            "a Kollázs lap megnyitása után sem jött létre a panel"
        )
        panel = _elem(window, "collagePanel")
        assert _var(qt_app, panel.isVisible), "a panel létrejött, de nem látszik"
        assert _var(qt_app, lambda: panel.height() > 0 and panel.width() > 0), (
            "a panelnek nincs mérete — a halasztás helyfoglalót hagyott"
        )

    def test_visszavaltas_utan_MEGMARAD(self, qml_app, qt_app):
        """A félkész kollázs nem veszhet el egy fülváltáson."""
        window = qml_app[0]
        _kollazs_lapot_nyit(window, qt_app)
        assert _var(qt_app, lambda: _keres(window, "collagePanel") is not None)
        _konyvtar_fulre(window, qt_app)
        qt_app.processEvents()
        panel = _keres(window, "collagePanel")
        assert panel is not None, (
            "a Könyvtár fülre váltás MEGSEMMISÍTETTE a Kollázs-panelt — a "
            "betöltő `active`-ja nem ragadós"
        )
        assert panel.isVisible() is False, "a rejtett lap panelje mégis látszik"


class TestAForrasAlakja:
    """A halasztást a forrás alakja is rögzíti — a `Loader` nem cserélhető
    vissza egyenes példányosításra észrevétlenül."""

    def test_a_Main_qml_betoltovel_hozza_a_panelt(self):
        import picasapy.app.application as app_module

        forras = (app_module._APP_DIR / "qml" / "Main.qml").read_text(
            encoding="utf-8"
        )
        assert "collagePanelLoader" in forras
        assert "CollagePanel {" in forras, "a komponens definíciója eltűnt"
        kezd = forras.index("id: collagePanelLoader")
        blokk = forras[kezd : kezd + 900]
        assert "active:" in blokk, "a betöltőnek `active` feltétele kell"
        assert "active: true" not in blokk, (
            "a betöltő fixen aktív — a halasztás elveszett"
        )
