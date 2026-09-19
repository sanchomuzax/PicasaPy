"""A négy eszköz Alkalmaz/Mégse párja a SAJÁT paneljében áll (#3320).

## A mérés

A #3123 az `editpanel/tool_container` alapján a kép fölé vitte a vágás, a
retusálás, a szöveg és a vörösszem gombpárját. A #3234 mérése szerint ez a
sáv NEM az ő közös sávjuk: az `editpanel.tre` a
`#---Straighen Overlay---` szakaszfejléc alá teszi (`:1038`–`:1052`), és
mindegyik eszköznek SAJÁT párja van a saját `*_well`-jében:

| eszköz | mért bejegyzés |
|---|---|
| vágás | `editpanel/cropapply: editpanel/crop_well` (`:821`) |
| retusálás | `editpanel/retouchapply: editpanel/retouch_well` (`:894`) |
| vörösszem | `editpanel/redeyeapply: editpanel/redeye_well` (`:722`) |

## Amit ez az őr mér

1. a négy pár a saját paneljében van, a RÉGI objektumnevükön;
2. a kép fölötti sáv CSAK a kiegyenesítésnél jelenik meg;
3. a jel a közös, RAJZOLT `EditorActionBadge` marad (#710) — a
   Unicode-glif nem szivároghat vissza, mert hiányzó glifnél nyomtalanul
   eltűnik.

## Amit NEM mér

A LÁTVÁNYT: hogy a panelbeli gombpár képpontra ott van-e, ahol az
eredetiben. A `.tre` a SZERKEZETET adja meg (melyik elem melyik szülőben
ül), a geometriát a #741/#779 mérte külön.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

QML = Path(__file__).resolve().parents[3] / "src/picasapy/app/qml/PicasaPy"

#: eszköz → (panelfájl, a gombok objektumnév-előtagja)
ESZKOZOK = {
    "crop": ("EditorCropPanel.qml", "crop"),
    "retouch": ("EditorRetouchPanel.qml", "retouch"),
    "text": ("EditorTextPanel.qml", "text"),
    "redeye": ("EditorRedeyePanel.qml", "redeye"),
}


@pytest.mark.parametrize("eszkoz", sorted(ESZKOZOK))
def test_a_par_a_sajat_paneljeben_all(eszkoz: str) -> None:
    fajl, elotag = ESZKOZOK[eszkoz]
    forras = (QML / fajl).read_text(encoding="utf-8")
    for utotag in ("ApplyButton", "CancelButton"):
        assert f'objectName: "{elotag}{utotag}"' in forras, (
            f"{fajl}: hiányzik a `{elotag}{utotag}`")


@pytest.mark.parametrize("eszkoz", sorted(ESZKOZOK))
def test_a_par_a_panel_jelet_hasznalja(eszkoz: str) -> None:
    """#710: a jel a közös, RAJZOLT komponens — nem Unicode-glif."""
    fajl, _elotag = ESZKOZOK[eszkoz]
    forras = (QML / fajl).read_text(encoding="utf-8")
    assert "EditorActionBadge" in forras, f"{fajl}: nincs rajzolt jel"
    for glif in ("✔", "✘"):
        assert f'qsTr("Apply") + " {glif}"' not in forras, (
            f"{fajl}: visszaszivárgott a betűtípusfüggő glif")


def test_a_sav_csak_a_kiegyenesitesnel_jelenik_meg() -> None:
    """A `tool_container` a `#---Straighen Overlay---` alatt él."""
    forras = (QML / "PhotoViewer.qml").read_text(encoding="utf-8")
    kezd = forras.index("EditorToolBar {")
    blokk = forras[kezd:kezd + 2600]
    tool = re.search(r"tool:\s*(.+?)\n\s*(?://|[a-zA-Z]+:)", blokk, re.S)
    assert tool, "nincs `tool:` kötés a sávon"
    kifejezes = tool.group(1)
    for eszkoz in ("cropActive", "retouchActive", "textActive", "redeyeActive"):
        assert eszkoz not in kifejezes, (
            f"a sáv még mindig a {eszkoz}-ra is megjelenik")
    assert "tiltActive" in kifejezes


def test_a_sav_csak_a_kiegyenesites_gombjait_koti() -> None:
    forras = (QML / "PhotoViewer.qml").read_text(encoding="utf-8")
    kezd = forras.index("EditorToolBar {")
    blokk = forras[kezd:kezd + 4000]
    for jel in ("cropApplyRequested", "retouchApplyRequested",
                "textApplyRequested", "redeyeApplyRequested"):
        assert jel not in blokk, f"a sáv még hívja a(z) {jel} jelet"


def test_a_sav_eszkozlistaja_csak_a_tiltet_ismeri() -> None:
    forras = (QML / "EditorToolBar.qml").read_text(encoding="utf-8")
    assert re.search(r'property string tool:\s*""', forras)
    # a dokumentáló megjegyzés se hirdesse a négy eltávolított eszközt
    fejlec = forras[:forras.index("Item {")]
    assert "#3320" in fejlec, "a fejléc nem mondja el a szétválasztást"
