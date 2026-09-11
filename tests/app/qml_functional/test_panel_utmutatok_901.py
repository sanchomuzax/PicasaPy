"""#901 — a panelen BELÜLI útmutató-szövegek és az egységes súgó-késleltetés.

A `respack`-ben „tip"-nek nevezett elemek egy része **nem** lebegő buborék,
hanem a panel része, fix dobozzal:

| elem | MÉRT doboz | hol |
|---|---|---|
| `editpanel/text(crop tip): croptext` | **257 × 54** | vágó |
| `editpanel/text(redeye tip): redeyetext` | **242 × 129** | vörösszem |
| `editpanel/text(retouch tip): retouchtext` | **258 × 96** | retusálás |

Mindhárom szövege megvolt nálunk, de **átfogalmazva vagy csonkán**: a vágónál
a mi rövidebb mondatunk állt, a vörösszemnél az utolsó két mondat lemaradt, a
retusálásnál pedig épp a `Ctrl`-húzásos pásztázást eláruló megjegyzés.

A magyar szövegek a Picasa SAJÁT magyar erőforrásából jönnek
(`panel-feliratok-hu.tsv:4976`, `:4989`, `:5001`) — nem a mi fordításunk.

⚠️ Amit ez az őr NEM mér: a buborék-súgó RAJZÁT. Az eredeti `ytToolTip`
saját rajzolású, de a rajzhoz **nincs képréteg** (`respack`), tehát a háttér,
a keret és a betűméret nincs kimérve — az utánzás találgatás lenne. A jegy
ezért marad nyitva ezzel az EGY ponttal.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from PySide6.QtCore import QObject

import picasapy.app

_QML = Path(picasapy.app.__file__).parent / "qml"
_TS = (
    Path(picasapy.app.__file__).parent / "i18n" / "picasapy_hu.ts"
).read_text(encoding="utf-8")

#: elemnév → (fájl, MÉRT szélesség, MÉRT magasság, a mért angol szöveg VÉGE)
UTMUTATOK = {
    "cropGuideText": (
        "EditorCropPanel.qml", 257, 54,
        "the portion of the image you wish to crop.",
    ),
    "redeyeGuideText": (
        "EditorRedeyePanel.qml", 242, 129,
        "The Photo is displayed with the red-eye removed.",
    ),
    "retouchGuideText": (
        "EditorRetouchPanel.qml", 258, 96,
        "Note: you can use ctrl-drag to pan.",
    ),
}


def _forras(nev: str) -> str:
    return (_QML / "PicasaPy" / nev).read_text(encoding="utf-8")


def _qsTr_szoveg(forras: str, elemnev: str) -> str:
    i = forras.index(f'objectName: "{elemnev}"')
    blokk = forras[i : i + 1400]
    j = blokk.index("qsTr(")
    k = blokk.index(")\n", j)
    return "".join(re.findall(r'"([^"]*)"', blokk[j + 5 : k]))


class TestAMertDoboz:
    @pytest.mark.parametrize("elemnev", sorted(UTMUTATOK))
    def test_a_MERT_dobozmeret_all_a_forrasban(self, elemnev):
        fajl, szel, mag, _ = UTMUTATOK[elemnev]
        forras = _forras(fajl)
        i = forras.index(f'objectName: "{elemnev}"')
        blokk = forras[i : i + 600]
        assert f"Layout.preferredWidth: {szel}" in blokk, elemnev
        assert f"Layout.preferredHeight: {mag}" in blokk, elemnev


class TestAMertSzoveg:
    @pytest.mark.parametrize("elemnev", sorted(UTMUTATOK))
    def test_a_szoveg_VEGE_is_ott_van(self, elemnev):
        """Ismert negatív: két útmutatóból eddig épp az utolsó mondat(ok)
        maradtak le — a vörösszemnél a befejezés, a retusálásnál a
        `Ctrl`-húzásos pásztázás."""
        fajl, _, _, veg = UTMUTATOK[elemnev]
        szoveg = _qsTr_szoveg(_forras(fajl), elemnev)
        assert szoveg.endswith(veg), (
            f"{elemnev}: a mért szöveg vége hiányzik: {veg}"
        )

    @pytest.mark.parametrize("elemnev", sorted(UTMUTATOK))
    def test_a_HIVATALOS_magyar_forditas_all_a_ts_ben(self, elemnev):
        fajl, _, _, _ = UTMUTATOK[elemnev]
        szoveg = _qsTr_szoveg(_forras(fajl), elemnev)
        assert f"<source>{szoveg}</source>" in _TS, (
            f"{elemnev}: a mért angol szöveg nincs a .ts-ben"
        )

    def test_a_regi_atfogalmazas_ELTUNT(self):
        """A vágónál a mi rövidebb mondatunk állt."""
        assert "you want to keep" not in _forras("EditorCropPanel.qml")

    def test_a_magyar_a_PICASA_sajat_szovege(self):
        """Szúrópróba: a vágó magyar szövege a Picasa erőforrásának szó
        szerinti mondata („fogd és húzd módszerrel")."""
        assert "fogd és húzd módszerrel" in _TS


class TestEgysegesKesleltetes:
    def test_minden_ToolTip_delay_a_TOKENRE_hivatkozik(self):
        """Eddig háromféle volt: 400 ms három helyen, 500 ms hatvanhaton."""
        szamok = []
        for f in sorted(_QML.rglob("*.qml")):
            szamok += re.findall(r"ToolTip\.delay:\s*(\d+)", f.read_text(encoding="utf-8"))
        assert szamok == [], (
            f"beégetett súgó-késleltetés maradt: {sorted(set(szamok))} — "
            "a `Theme.tooltipDelay` az egyetlen hely (#901)"
        )

    def test_a_token_letezik_es_KIMONDJA_hogy_nem_meres(self):
        forras = _forras("Theme.qml")
        assert "readonly property int tooltipDelay:" in forras
        kezd = forras.index("readonly property int tooltipDelay:")
        elotte = forras[max(0, kezd - 800) : kezd]
        assert "nem mérés" in elotte, (
            "a token mellett nincs kimondva, hogy az érték a MI döntésünk"
        )


class TestARajzoltPanelek:
    def test_mind_a_harom_utmutato_felepul(self, qml_app, qt_app):
        window, _c, _e = qml_app
        window.setProperty("viewerOpen", True)
        qt_app.processEvents()
        hianyzo = [
            nev for nev in UTMUTATOK
            if window.findChild(QObject, nev) is None
        ]
        assert hianyzo == [], f"nem épült fel: {hianyzo}"
