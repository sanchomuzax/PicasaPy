"""#7027 (J1, J8) - a felirat-sáv és a törlési kérdés hivatalos szövegei.

Az eredeti Picasa katalógusából (`stringres`, `tooltips`):

| angol forrás | azonosító | magyar |
|---|---|---|
| Make a caption! | `CTextCaptionNode::defname` | Készítsen képaláírást! |
| Show/Hide Caption | `Tooltip(editpanel/captionbutton)` | Képfelirat megjelenítése/elrejtése |
| Delete this caption | `Tooltip(editpanel/captiontrash)` | Képfelirat törlése |
| Are you sure you want to delete the caption for this image? | `IDS_CONFIRM_CAPTION_TRASH` | Biztosan törli a kép feliratát? |
| Delete Caption | `IDS_CONFIRM_CAPTION_YES_BUTTON` | Képfelirat törlése |
| Confirm | `ytApp::ConfirmTitle` | Jóváhagyás |

A magyar szöveget a próba rögzíti; a másik 40 nyelvnél azt méri, hogy a
bejegyzés megvan, befejezett, és az eredetet jelöli.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

_I18N = Path(__file__).resolve().parents[2] / "src" / "picasapy" / "app" / "i18n"
_KONTEXTUS = "PhotoViewerOverlayControls"

_HU = {
    "Make a caption!": "Készítsen képaláírást!",
    "Show/Hide Caption": "Képfelirat megjelenítése/elrejtése",
    "Delete this caption": "Képfelirat törlése",
    "Are you sure you want to delete the caption for this image?": (
        "Biztosan törli a kép feliratát?"
    ),
    "Delete Caption": "Képfelirat törlése",
    "Confirm": "Jóváhagyás",
}

_EREDET = {
    "Make a caption!": "stringres:CTextCaptionNode::defname",
    "Show/Hide Caption": "tooltips:Tooltip(editpanel/captionbutton)",
    "Delete this caption": "tooltips:Tooltip(editpanel/captiontrash)",
    "Are you sure you want to delete the caption for this image?": (
        "stringres:IDS_CONFIRM_CAPTION_TRASH"
    ),
    "Delete Caption": "stringres:IDS_CONFIRM_CAPTION_YES_BUTTON",
    "Confirm": "stringres:ytApp::ConfirmTitle",
}


def _uzenetek(nyelv: str) -> dict[str, ET.Element]:
    gyoker = ET.parse(_I18N / f"picasapy_{nyelv}.ts").getroot()
    for kontextus in gyoker.findall("context"):
        if kontextus.findtext("name") == _KONTEXTUS:
            return {
                uzenet.findtext("source"): uzenet
                for uzenet in kontextus.findall("message")
            }
    raise AssertionError(f"{nyelv}: nincs {_KONTEXTUS} kontextus")


_NYELVEK = sorted(
    fajl.stem.split("_", 1)[1] for fajl in _I18N.glob("picasapy_*.ts")
)


def test_mind_a_41_nyelv_megvan():
    assert len(_NYELVEK) == 41


@pytest.mark.parametrize(("forras", "vart"), sorted(_HU.items()))
def test_a_magyar_szoveg_a_hivatalos(forras, vart):
    uzenet = _uzenetek("hu")[forras]
    assert uzenet.findtext("translation") == vart


@pytest.mark.parametrize("nyelv", _NYELVEK)
def test_minden_nyelvben_megvan_a_hat_szoveg_befejezve_es_eredet_jelolve(nyelv):
    uzenetek = _uzenetek(nyelv)
    for forras, eredet in _EREDET.items():
        assert forras in uzenetek, f"{nyelv}: hiányzik: {forras}"
        fordites = uzenetek[forras].find("translation")
        assert (fordites.text or "").strip(), f"{nyelv}: üres fordítás: {forras}"
        assert fordites.get("type") != "unfinished", f"{nyelv}: befejezetlen: {forras}"
        megjegyzes = uzenetek[forras].findtext("extracomment") or ""
        assert "picasapy-origin: picasa\n" in megjegyzes + "\n", (
            f"{nyelv}: nincs eredet-jelölés: {forras}"
        )
        assert f"picasapy-origin-key: {eredet}" in megjegyzes, (
            f"{nyelv}: rossz eredet-kulcs: {forras}"
        )
