"""#7068: A szerkesztő diavetítés-gombjának súgója az eredeti szövegét mutassa.

Eredeti: `editpanel/sbutton` súgó (`editpaneltext.tre:8-9`), hivatalos magyar:
`Állítson össze és nézzen diavetítést ezekből a fotókból` (`panel-feliratok-hu.tsv:4914`).
Hivatalos forrás: `tooltips:Tooltip(editpanel/sbutton)`.
Angol: `Watch a slideshow of these photos`.
"""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from pathlib import Path

import picasapy.app

_APP_DIR = Path(picasapy.app.__file__).parent
_QML_DIR = _APP_DIR / "qml" / "PicasaPy"
_TOP_BAR_QML = (_QML_DIR / "PhotoViewerTopBar.qml").read_text(encoding="utf-8")
_QUICK_TOOLBAR_QML = (_QML_DIR / "PhotoViewerQuickToolbar.qml").read_text(encoding="utf-8")
_TS_PATH = _APP_DIR / "i18n" / "picasapy_hu.ts"

ELVART_ANGOL = "Watch a slideshow of these photos"
ELVART_MAGYAR = "Állítson össze és nézzen diavetítést ezekből a fotókból"
ELVART_ORIGIN_KEY = "tooltips:Tooltip(editpanel/sbutton)"


def _gomb_blokk(forras: str, object_name: str) -> str:
    minta = re.compile(r'^([ \t]*)objectName: "%s"$' % re.escape(object_name), re.M)
    talalat = minta.search(forras)
    assert talalat, f"nincs ilyen elem: {object_name}"
    behuzas = len(talalat.group(1))
    sorok = forras[talalat.end() :].split("\n")
    ki = []
    for sor in sorok[1:]:
        csupasz = sor.strip()
        beagyazott = ":" in csupasz.split("{")[0]
        if csupasz.endswith("{") and not beagyazott and len(sor) - len(sor.lstrip()) <= behuzas:
            break
        ki.append(sor)
    return "\n".join(ki)


def test_viewer_play_button_sugo_angol_szovege():
    """A PhotoViewerTopBar viewerPlayButton súgója az eredeti angol szöveg."""
    blokk = _gomb_blokk(_TOP_BAR_QML, "viewerPlayButton")
    talalat = re.search(r'ToolTip\.text:\s*qsTr\("([^"]+)"\)', blokk)
    assert talalat is not None, "viewerPlayButton: hiányzik a ToolTip.text"
    assert talalat.group(1) == ELVART_ANGOL


def test_viewer_quick_play_button_sugo_angol_szovege():
    """A PhotoViewerQuickToolbar viewerQuickPlayButton súgója az eredeti angol szöveg."""
    blokk = _gomb_blokk(_QUICK_TOOLBAR_QML, "viewerQuickPlayButton")
    talalat = re.search(r'ToolTip\.text:\s*qsTr\("([^"]+)"\)', blokk)
    assert talalat is not None, "viewerQuickPlayButton: hiányzik a ToolTip.text"
    assert talalat.group(1) == ELVART_ANGOL


def test_hivatalos_magyar_forditas_a_ts_ben():
    """A magyar .ts tartalmazza a hivatalos fordítást és eredetkulcsot."""
    root = ET.fromstring(_TS_PATH.read_bytes())
    megtalalt = False
    for msg in root.iterfind(".//message"):
        if msg.findtext("source") == ELVART_ANGOL:
            megtalalt = True
            assert msg.findtext("translation") == ELVART_MAGYAR
            extracomment = msg.findtext("extracomment") or ""
            assert "picasapy-origin: picasa" in extracomment
            assert f"picasapy-origin-key: {ELVART_ORIGIN_KEY}" in extracomment
    assert megtalalt, f"A(z) '{ELVART_ANGOL}' forrásszöveg hiányzik a {_TS_PATH.name} fájlból"
