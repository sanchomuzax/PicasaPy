"""#3476: a fő könyvtárnézet négy súgója a HIVATALOS Picasa-szöveget mondja.

A `thumbui` 31 eredeti buborékjából 15 egyezett; ez a négy tért el
(`docs/specs/ui-audit-mainwindow.md`, „R5 — a fő könyvtárnézet súgói", B).
A hivatalos szövegek cél-azonosító szerint: `referencia/i18n/enUS/tooltips.xml`
és `referencia/i18n/hu/tooltips.xml` (`thumbui/…`).

Két szinten mér: a vezérlő SAJÁT blokkjában a hivatalos angol `qsTr` áll, és
a futásidő által betöltött `.qm` a hivatalos magyart adja vissza rá (a `.ts`
javítása önmagában nem elég — #2448, #3405).

Amit NEM mér: hogy a buborék a képernyőn megjelenik-e.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import QTranslator

import picasapy.app
from tests.support.qml_blokk import blokk_horgonyra

_APP = Path(picasapy.app.__file__).parent
_QML = _APP / "qml" / "PicasaPy"

#: (fájl, a vezérlő objectName-je, fordítási kontextus, hivatalos angol, hivatalos magyar)
SUGOK = [
    ("TrayBar.qml", "trayLoupeButton", "TrayBar",
     "Click and drag over photos to magnify them",
     "Ide kattintva és az egérmutatót a fotókra húzva kinagyíthatja a részleteket"),
    ("MainToolbar.qml", "toolbarFolderViewPopupButton", "MainToolbar",
     "View options", "Megjelenítési beállítások"),
    ("PhotoViewer.qml", "viewerBackButton", "PhotoViewer",
     "Return to organized thumbnails", "Vissza a rendezett indexképekhez"),
    ("TrayBar.qml", "traySingleActionClose", "TrayBar",
     'Cancel "Get more"', 'A "Továbbiak" művelet megszakítása'),
]


@pytest.fixture(scope="module")
def forditas(qt_app):
    tr = QTranslator()
    assert tr.load(str(_APP / "i18n" / "picasapy_hu.qm")), "a .qm nem tölthető be"
    return tr


def _qml_literal(szoveg: str) -> str:
    return 'qsTr("' + szoveg.replace('"', '\\"') + '")'


@pytest.mark.parametrize("fajl,nev,_ctx,angol,_magyar", SUGOK)
def test_a_vezerlo_a_hivatalos_angolt_mondja(fajl, nev, _ctx, angol, _magyar):
    blokk = blokk_horgonyra((_QML / fajl).read_text(encoding="utf-8"), f'"{nev}"')
    assert "ToolTip.text: " + _qml_literal(angol) in blokk, (
        f"{nev}: a súgó nem a hivatalos „{angol}”"
    )
    assert "ToolTip.visible" in blokk, f"{nev}: a súgó sosem jelenik meg"


@pytest.mark.parametrize("_fajl,_nev,ctx,angol,magyar", SUGOK)
def test_a_betoltott_qm_a_hivatalos_magyart_adja(forditas, _fajl, _nev, ctx, angol, magyar):
    assert forditas.translate(ctx, angol) == magyar


def test_a_regi_fogalmazas_nem_maradt():
    for fajl, regi in (
        ("TrayBar.qml", "Loupe — drag over the photos"),
        ("MainToolbar.qml", "Folder view options"),
    ):
        assert regi not in (_QML / fajl).read_text(encoding="utf-8")
