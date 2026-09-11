"""#815: a gomb- és csempefelirat MÉRT tipográfiája.

Az erőforrásokból mért értékek (`macros.tre`, `fontmacros_win.tre`):

| makró | `typecolor` (alap · egér alatt · lenyomva) | használók |
|---|---|---:|
| `m_buttontypecolor` | `CC000000` · `CC000000` · `CC000000` | **136** |
| `m_buttontypecolor2` | `CC000000` · **`FFFFFFFF`** · `CC000000` | **0** |
| `m_buttontypecolor3` | `FFFFFFFF` · `CCFFFFFF` · `FFFFFFFF` | 6 |
| `m_buttontypecolor4` | `99000000` ×3 | 9 |
| `m_buttonfont12` | `FF000000` · **`FFFFFFFF`** · `FF000000` | **0** |

⚠️ **A fehérre váltó két makrónak NULLA használója van** — csak a saját
`#define`-juk hivatkozik rájuk (a `m_buttonfont12`-re a windowsos és a
mac-es fontmakró-fájl, mindkettő definíció). Halott erőforrás: a jegy
„egér alatt fehérre vált" pontja olyan viselkedést kért, ami az
eredetiben **egyetlen gombon sem** látszott.

A `fonttrack -1` viszont MINDEN érintett makróban ott van — a csempefeliratén
(`m_fxlabel`) és a gombfeliratokén (`m_buttonfontC`, `…Cbelow`, `…LC`) is.
"""

from __future__ import annotations

import pytest
from PySide6.QtCore import QObject

_ALAP_ALFA = 0.8


class TestABetukoz:
    """`fonttrack -1` — a panel egész tipográfiája szorosabb."""

    def test_a_csempefelirat_betukoze_minusz_egy(self, qml_app, qt_app):
        window, _, _ = qml_app
        window.setProperty("viewerOpen", True)
        viewer = window.findChild(QObject, "photoViewer")
        viewer.setProperty("currentIndex", 0)
        qt_app.processEvents()
        panel = window.findChild(QObject, "viewerEditorPanel")
        panel.setProperty("activeTab", 2)
        qt_app.processEvents()

        felirat = window.findChild(QObject, "effectSepiaLabel")
        assert felirat is not None, "az effekt-csempe felirata nincs a fában"
        assert felirat.property("font").letterSpacing() == -1.0

    def test_a_MEROELEM_is_ugyanazt_a_betukozt_hasznalja(self, qml_app, qt_app):
        """A #2597 fokozat-illesztése a mérőelemből számol: ha annak nincs
        betűköze, a SZÉLESEBB szöveggel számol, és a felirat a kelleténél
        kisebb fokozatra esik."""
        from pathlib import Path

        import picasapy.app

        forras = (
            Path(picasapy.app.__file__).parent / "qml" / "PicasaPy" / "PanelButton.qml"
        ).read_text(encoding="utf-8")
        kezd = forras.index("id: pbtnAlapMetrika")
        veg = forras.index("}", kezd)
        assert "letterSpacing: pbtn.labelBetukoz" in forras[kezd:veg]


class TestASzovegszin:
    def test_az_alapszin_alfaja_80_szazalek(self, qml_app, qt_app):
        """`CC` = 204/255 = 80% — a 136 elemen használt makró alfája."""
        window, _, _ = qml_app
        window.setProperty("viewerOpen", True)
        viewer = window.findChild(QObject, "photoViewer")
        viewer.setProperty("currentIndex", 0)
        qt_app.processEvents()
        panel = window.findChild(QObject, "viewerEditorPanel")
        panel.setProperty("activeTab", 2)
        qt_app.processEvents()

        felirat = window.findChild(QObject, "effectSepiaLabel")
        szin = felirat.property("color")
        assert szin.alphaF() == pytest.approx(_ALAP_ALFA, abs=0.01)

    def test_a_forras_kimondja_hogy_EGER_ALATT_nem_valt(self):
        """A „nem váltunk színt" MÉRÉS, nem kihagyás — a kódnak ezt ki kell
        mondania, különben a következő kör „hiányzó állapotnak" veszi, és
        beépít egy olyan hovert, ami az eredetiben egyetlen gombon sem volt."""
        from pathlib import Path

        import picasapy.app

        forras = (
            Path(picasapy.app.__file__).parent / "qml" / "PicasaPy" / "PanelButton.qml"
        ).read_text(encoding="utf-8")
        assert "nulla elemen" in forras
        assert "m_buttontypecolor2" in forras

    def test_a_felirat_szine_NEM_kot_egerallapotra(self):
        """Forrás-szintű őr: a felirat színe se `hovered`-re, se `containsMouse`-ra
        ne kötődjön — az eredetiben nincs ilyen váltás."""
        from pathlib import Path

        import picasapy.app
        from tests.support.qml_blokk import blokk_horgonyra

        forras = (
            Path(picasapy.app.__file__).parent / "qml" / "PicasaPy" / "PanelButton.qml"
        ).read_text(encoding="utf-8")
        #: ⚠️ A horgony SORVÉGGEL együtt: az `id: pbtnLabel` önmagában az
        #: `id: pbtnLabelMetrics`-re illeszkedett ELŐBB (az áll fentebb a
        #: fájlban), és akkor az őr egy három soros mérőelemet vizsgált —
        #: zöld maradt volna bármilyen hover-kötés mellett.
        blokk = blokk_horgonyra(forras, "id: pbtnLabel\n")
        assert "Theme.textDark" in blokk, "nincs színkötés a feliraton"
        assert "containsMouse" not in blokk
        assert "hovered" not in blokk


class TestAMertOldalbehuzas:
    def test_a_csempefelirat_oldalankent_4_px(self, qml_app, qt_app):
        """`XConstraint 0, 0, 4` / `1, 1, -4` — ez MÁR teljesült a #815 előtt
        is; az eset azért van itt, hogy ne csússzon el némán."""
        window, _, _ = qml_app
        window.setProperty("viewerOpen", True)
        viewer = window.findChild(QObject, "photoViewer")
        viewer.setProperty("currentIndex", 0)
        qt_app.processEvents()
        panel = window.findChild(QObject, "viewerEditorPanel")
        panel.setProperty("activeTab", 2)
        qt_app.processEvents()

        csempe = window.findChild(QObject, "effectSepia")
        felirat = window.findChild(QObject, "effectSepiaLabel")
        assert csempe is not None and felirat is not None
        assert csempe.width() - felirat.width() == pytest.approx(8.0, abs=0.5)
