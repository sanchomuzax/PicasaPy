"""#2535 — a szövegráíró panel hat feliratának HELYE és SZÖVEGE.

Az eredeti `edittextpanel` hat feliratot használ, mind mért betűmakróval és
igazítással (`docs/specs/szerkeszto-panel-meretek.md` 6.4):

| elem | méret · x | igazítás |
|---|---|---|
| `edittext_label` | 207 × 16 · 59..266 | balra, `m_displayfont18_Reg` |
| `font_label` | 66 × 15 · 0..66 | **jobbra** |
| `size_label` | 66 × 15 · 0..66 | **jobbra** |
| `style_label` | 46 × 15 · 121..167 | **jobbra** |
| `align_label` | 94 × 15 · 72..166 | **jobbra** |
| `transparency_label` | 127 × 15 · 79..206 | ⚠️ **középre**, a csúszka fölött |

A magyar feliratok a Picasa SAJÁT magyar erőforrásából jönnek
(`referencia/panel-feliratok-hu.tsv:247–258`) — nem a mi fordításunk.

⚠️ Amit ez az őr NEM méri: a képpontra pontos elhelyezést. A mért
szélességek felső korlátként állnak a QML-ben (a #779 windowsos tanulsága
miatt), a tényleges rajz a betűkészlettől függ. Amit mér: hogy a négy
vezérlő-címke a vezérlőjétől BALRA, jobbra igazítva áll, az átlátszóság
KÖZÉPRE, és hogy a fejléc betűje nagyobb a címkékénél.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import QObject

import picasapy.app

_PANEL = (
    Path(picasapy.app.__file__).parent
    / "qml" / "PicasaPy" / "EditorTextPanel.qml"
).read_text(encoding="utf-8")
_TS = (
    Path(picasapy.app.__file__).parent / "i18n" / "picasapy_hu.ts"
).read_text(encoding="utf-8")

#: elemnév → (angol felirat, hivatalos magyar felirat)
FELIRATOK = {
    "textPanelHeader": ("Edit Text", "Szöveg szerkesztése"),
    "textFontLabel": ("Font:", "Betűtípus:"),
    "textSizeLabel": ("Size:", "Méret:"),
    "textStyleLabel": ("Style:", "Stílus:"),
    "textAlignLabel": ("Alignment:", "Igazítás:"),
    "textTransparencyLabel": ("Transparency", "Átlátszóság"),
}

#: a négy CÍMKEOSZLOP-tag: jobbra igazítva, a vezérlőjétől balra
JOBBRA = ("textFontLabel", "textSizeLabel", "textStyleLabel", "textAlignLabel")


class TestASzovegek:
    @pytest.mark.parametrize("nev", sorted(FELIRATOK))
    def test_az_angol_felirat_a_panelen_all(self, nev):
        angol, _ = FELIRATOK[nev]
        assert f'objectName: "{nev}"' in _PANEL, f"nincs ilyen felirat: {nev}"
        kezd = _PANEL.index(f'objectName: "{nev}"')
        assert f'qsTr("{angol}")' in _PANEL[kezd : kezd + 700], nev

    @pytest.mark.parametrize("nev", sorted(FELIRATOK))
    def test_a_HIVATALOS_magyar_forditas_all_a_ts_ben(self, nev):
        """A Picasa saját magyar erőforrása a mérce — nem fordítunk újra."""
        angol, magyar = FELIRATOK[nev]
        assert f"<source>{angol}</source>" in _TS
        assert f"<translation>{magyar}</translation>" in _TS

    def test_a_regi_sajat_feliratok_ELTUNTEK(self):
        """Ismert negatív: a „Font"/„Opacity" szakaszcímek helyére a mért
        feliratok kerültek — ha valamelyik visszakerül, ez bukik."""
        assert 'qsTr("Font")' not in _PANEL
        assert 'qsTr("Opacity")' not in _PANEL
        assert 'qsTr("Text")' not in _PANEL


class TestAHelyEsAzIgazitas:
    @pytest.mark.parametrize("nev", JOBBRA)
    def test_a_cimke_JOBBRA_igazitott(self, nev):
        kezd = _PANEL.index(f'objectName: "{nev}"')
        blokk = _PANEL[kezd : kezd + 700]
        assert "horizontalAlignment: Text.AlignRight" in blokk, nev

    @pytest.mark.parametrize("nev", JOBBRA)
    def test_a_cimkenek_MERT_felso_korlatja_van(self, nev):
        """#779: felső korlát nélkül a felirat a saját szélességét kötelező
        minimumként adná, és a windowsos rendszerbetűvel a PANEL feszülne
        szét."""
        kezd = _PANEL.index(f'objectName: "{nev}"')
        assert "Layout.maximumWidth:" in _PANEL[kezd : kezd + 700], nev

    def test_az_atlatszosag_KOZEPRE_igazitott(self):
        """A hatodik felirat a kivétel: `Property textalign center`
        (`edittextpanel.tre:120`) + a csúszkával azonos szélesség."""
        kezd = _PANEL.index('objectName: "textTransparencyLabel"')
        blokk = _PANEL[kezd : kezd + 700]
        assert "horizontalAlignment: Text.AlignHCenter" in blokk
        assert "Layout.fillWidth: true" in blokk

    def test_a_cimke_a_vezerloje_ELOTT_all(self):
        """A címkeoszlop lényege: a felirat és a vezérlő EGY sorban, a
        felirat előbb. Ha a felirat a vezérlő fölé kerül vissza (szakaszcím),
        a sorrend megfordul."""
        for cimke, vezerlo in (
            ("textFontLabel", "textFontFamilyBox"),
            ("textSizeLabel", "textFontSizeBox"),
            ("textStyleLabel", "textBoldButton"),
            ("textAlignLabel", "textAlign_left"),
        ):
            assert _PANEL.index(f'objectName: "{cimke}"') < _PANEL.index(
                f'objectName: "{vezerlo}"'
            ), cimke


class TestARajzoltPanel:
    def test_mind_a_hat_felirat_LATSZIK(self, qml_app, qt_app):
        """A forrás nem elég: a felépült fában is ott kell lenniük."""
        window, _c, _e = qml_app
        hianyzo = [
            nev
            for nev in FELIRATOK
            if window.findChild(QObject, nev) is None
        ]
        assert hianyzo == [], f"nem épült fel: {hianyzo}"

    def test_a_fejlec_betuje_NAGYOBB_a_cimkeknel(self, qml_app, qt_app):
        """Az eredetiben 18 pt vs. 12 pt — a KÜLÖNBSÉG a mért tény."""
        window, _c, _e = qml_app
        fejlec = window.findChild(QObject, "textPanelHeader")
        cimke = window.findChild(QObject, "textFontLabel")
        assert fejlec is not None and cimke is not None
        assert fejlec.property("font").pixelSize() > cimke.property(
            "font"
        ).pixelSize()
