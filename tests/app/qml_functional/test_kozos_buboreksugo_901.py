"""#901 — EGY közös buboréksúgó a felület minden `ToolTip`-jéhez.

A jegy a Picasa `ytToolTip` osztályából indult: a buborék ott **saját
rajzolású**, nem a Windows `tooltips_class32` vezérlője. Nálunk a felület
**24 fájlban** használ `ToolTip`-et, MIND a csatolt alakot
(`ToolTip.text`/`ToolTip.visible`/`ToolTip.delay`) — az pedig egyetlen,
a Quick Controls STÍLUSÁTÓL kapott példányt jelenít meg.

Ezért a közös komponens stílus-szinten él (`qml/PicasaStyle/ToolTip.qml`):
egy hely, a lebegtetés/pozicionálás logikájának érintése nélkül.

## Amit ez az őr mér

1. az alkalmazás a `PicasaStyle`-t állítja be (tartalék: `Fusion`);
2. a csatolt `ToolTip` valóban a MI példányunkat adja;
3. a késleltetése a MÉRT 600 ms (`Theme.tooltipDelay`);
4. a háttere a saját `Theme`-tokenünkből jön — vagyis EGY helyen
   cserélhető, ha a rajz egyszer kiolvasható lesz a binárisból.

⚠️ Amit NEM mér: hogy a rajz egyezik-e az eredetivel. A `respack.yt`-ben
nincs tooltip-réteg, a rajz konstansai nincsenek kiolvasva — a #901 emiatt
marad nyitva, és ez a modul ezt kimondja, hogy a zöldje ne tűnjön többnek.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import QMetaObject, QObject, Qt, Q_RETURN_ARG
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuickControls2 import QQuickStyle

import picasapy.app
from picasapy.app.application import allitsd_be_a_stilust

_QML = Path(picasapy.app.__file__).parent / "qml"

#: a próba-felület: egy gomb csatolt buboréksúgóval — pontosan az az alak,
#: amit a felület mind a 24 fájlja használ
_PROBA = """
import QtQuick
import QtQuick.Controls
import PicasaPy

Window {
    width: 200
    height: 120
    function sugoNeve() { return gomb.ToolTip.toolTip.objectName }
    function sugoKesleltetes() { return gomb.ToolTip.toolTip.delay }
    function sugoHatterSzine() {
        return String(gomb.ToolTip.toolTip.background.color)
    }
    function temaPanelSzine() { return String(Theme.panelBg) }

    Button {
        id: gomb
        objectName: "probaGomb"
        text: "x"
        ToolTip.text: "buborek"
        ToolTip.delay: Theme.tooltipDelay
        ToolTip.visible: true
    }
}
"""


def _hivd(ablak: QObject, nev: str):
    return QMetaObject.invokeMethod(
        ablak, nev, Qt.ConnectionType.DirectConnection, Q_RETURN_ARG("QVariant")
    )


@pytest.fixture
def ablak(qt_app):
    if not isinstance(QGuiApplication.instance(), QGuiApplication):
        pytest.skip("ebben a folyamatban nem QGuiApplication fut")
    # a stílus FOLYAMAT-szintű, és a motor létrehozása ELŐTT kell beállítani
    allitsd_be_a_stilust()
    engine = QQmlApplicationEngine()
    engine.addImportPath(str(_QML))
    engine.loadData(_PROBA.encode("utf-8"))
    gyokerek = engine.rootObjects()
    assert gyokerek, "a próba-felület nem töltődött be"
    qt_app.processEvents()
    try:
        yield gyokerek[0]
    finally:
        for gyoker in gyokerek:
            gyoker.close()
        engine.clearComponentCache()
        engine.deleteLater()
        qt_app.processEvents()


class TestAStilus:
    def test_az_alkalmazas_a_picasastyle_t_allitja_be(self):
        allitsd_be_a_stilust()
        assert QQuickStyle.name() == "PicasaStyle"


class TestAKozosBuborek:
    def test_a_csatolt_sugo_a_mi_peldanyunk(self, ablak):
        assert _hivd(ablak, "sugoNeve") == "picasaToolTip"

    def test_a_kesleltetes_a_mert_600_ms(self, ablak):
        assert _hivd(ablak, "sugoKesleltetes") == 600

    def test_a_hatter_a_tema_tokenjebol_jon(self, ablak):
        assert _hivd(ablak, "sugoHatterSzine") == _hivd(ablak, "temaPanelSzine")
