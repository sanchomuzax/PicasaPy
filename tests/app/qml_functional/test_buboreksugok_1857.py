"""Buboréksúgók a nézőn és a szerkesztő fülein — #1857.

Két különböző hiányt őriz ez a fájl:

* a nézőben kilenc gombnak EGYÁLTALÁN nem volt súgója, miközben a
  testvéreiknek — ugyanabban a sorban — volt;
* a szerkesztő fülei adtak súgót, de a fül SAJÁT NEVÉT ismételték, vagyis
  a felhasználó ugyanazt a szót kapta másodszor.

A `ToolTip` CSATOLT tulajdonság: a kirajzolt elemről Pythonból nem
olvasható ki (ld. `test_collage_clips_tab_949.TestFeliratok`). Ezért a
FORRÁST állítjuk — blokkonként, nem fájlra keresve. A fájlra keresés itt
hamis zöldet adna: a `qsTr("Next picture")` a fájlban akkor is ott van, ha
egy MÁSIK gombhoz tartozik.
"""

from __future__ import annotations

import re
from pathlib import Path

import picasapy.app
import pytest

_QML = Path(picasapy.app.__file__).parent / "qml" / "PicasaPy"
_NEZO = (_QML / "PhotoViewer.qml").read_text(encoding="utf-8")
_FULSAV = (_QML / "EditorTabBar.qml").read_text(encoding="utf-8")
_FULGOMB = (_QML / "EditTabButton.qml").read_text(encoding="utf-8")
_TS = (
    Path(picasapy.app.__file__).parent / "i18n" / "picasapy_hu.ts"
).read_text(encoding="utf-8")

#: A jegy kilenc gombja. A három összehasonlító gomb a #434-ig letiltott —
#: a súgó szövege akkor is KI VAN TÉVE, csak a Qt nem mutatja meg, amíg
#: `enabled: false` (letiltott gomb nem kap `hovered`-et).
KILENC_GOMB = (
    "viewerPlayButton",
    "compareButtonA",
    "compareButtonAB",
    "compareButtonAA",
    "viewerPrevButton",
    "viewerNextButton",
    "viewerCreateNowButton",
    "zoomFitButton",
    "zoomActualButton",
)

#: A hét szerkesztő-fül és a LEÍRÁSA. Az első öt az eredeti Picasa kimért
#: `editpanel/tabN` szövege; a 6.–7. a mi többletünk, saját szöveggel.
HET_FUL = {
    "editTabFixes": "Commonly needed fixes",
    "editTabFinetune": "Finely-tuned lighting and color fixes",
    "editTabEffects": "Fun and useful image processing",
    "editTabEffects2": "More fun and useful image processing",
    "editTabEffects3": "Even more fun and useful image processing",
    "editTabEffects4": "Glimmer effects beyond the three known tabs",
    "editTabLegacy": "Filters left in the Picasa engine but not on its surface",
}


def _blokk(forras: str, object_name: str) -> str:
    """Az `objectName`-et tartalmazó QML-blokk — a következő testvér elemig.

    A blokkhatár a *sajátnál nem mélyebb* behúzású, `{`-re végződő sor:
    ez a következő elem kezdete. Így a súgó-állítás ahhoz a gombhoz
    kötődik, amelyikről szól."""
    minta = re.compile(r'^([ \t]*)objectName: "%s"$' % re.escape(object_name), re.M)
    talalat = minta.search(forras)
    assert talalat, f"nincs ilyen elem: {object_name}"
    behuzas = len(talalat.group(1))
    sorok = forras[talalat.end() :].split("\n")
    ki = []
    for sor in sorok[1:]:
        csupasz = sor.strip()
        if csupasz.endswith("{") and len(sor) - len(sor.lstrip()) <= behuzas:
            break
        ki.append(sor)
    return "\n".join(ki)


class TestANezoKilencGombja:
    @pytest.mark.parametrize("gomb", KILENC_GOMB)
    def test_van_buboreksugoja(self, gomb):
        blokk = _blokk(_NEZO, gomb)
        assert "ToolTip.text:" in blokk, f"{gomb}: nincs buboréksúgója"

    @pytest.mark.parametrize("gomb", KILENC_GOMB)
    def test_a_sugo_szovege_NEM_ures(self, gomb):
        blokk = _blokk(_NEZO, gomb)
        talalat = re.search(r'ToolTip\.text: qsTr\("([^"]*)"\)', blokk)
        assert talalat, f"{gomb}: a súgó nem `qsTr`-rel fordítható"
        assert talalat.group(1).strip(), f"{gomb}: üres súgószöveg"

    @pytest.mark.parametrize("gomb", KILENC_GOMB)
    def test_a_testverek_mintajat_koveti(self, gomb):
        """`hovered` + 500 ms — a fájl saját, explicit konvenciója.

        (A jegy 400-at írt; a fájlban MINDEN kiírt késleltetés 500, tehát
        a mért testvéreket követjük, nem a jegy becslését.)"""
        blokk = _blokk(_NEZO, gomb)
        assert "ToolTip.visible: hovered" in blokk
        assert "ToolTip.delay: 500" in blokk

    @pytest.mark.parametrize("gomb", KILENC_GOMB)
    def test_a_sugo_le_van_forditva(self, gomb):
        blokk = _blokk(_NEZO, gomb)
        angol = re.search(r'ToolTip\.text: qsTr\("([^"]*)"\)', blokk).group(1)
        assert f"<source>{angol}</source>" in _TS, f"{gomb}: nincs a .ts-ben"


class TestASzerkesztoFulei:
    def test_a_sugo_NEM_a_feliratot_ismetli(self):
        """A `label` már nem önmagában a súgó szövege.

        Ez a jegy lényege: a `ToolTip.text: tbtn.label` alak azt adta a
        felhasználónak, amit már látott."""
        assert "ToolTip.text: tbtn.label\n" not in _FULGOMB
        assert "tbtn.description" in _FULGOMB

    @pytest.mark.parametrize("ful,leiras", sorted(HET_FUL.items()))
    def test_mind_a_het_ful_kap_leirast(self, ful, leiras):
        blokk = _blokk(_FULSAV, ful)
        assert f'description: qsTr("{leiras}")' in blokk, f"{ful}: nincs leírás"

    @pytest.mark.parametrize("ful,leiras", sorted(HET_FUL.items()))
    def test_a_leiras_NEM_egyezik_a_felirattal(self, ful, leiras):
        blokk = _blokk(_FULSAV, ful)
        felirat = re.search(r'label: qsTr\("([^"]*)"\)', blokk).group(1)
        assert felirat != leiras, f"{ful}: a leírás a feliratot ismétli"

    @pytest.mark.parametrize("leiras", sorted(HET_FUL.values()))
    def test_a_leiras_le_van_forditva(self, leiras):
        assert f"<source>{leiras}</source>" in _TS
