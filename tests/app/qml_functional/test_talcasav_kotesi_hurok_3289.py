"""#3289 — a tálcasáv szövegének mérése ne írjon QML-tulajdonságot.

## A tulajdonos konzolnaplója (Windows, indításkor)

```
TrayBar.qml:271:9: QML QQuickText*: Binding loop detected for property "text"
    TrayBar.qml:322:13
```

## A hurok mechanizmusa

A `trayInfoLabel.text` kötése a saját `szelessege()` függvényét hívja, az
pedig **imperatívan beírt** a mérő `TextMetrics` `text` tulajdonságába, és
onnan olvasta vissza a szélességet. A kötés KIÉRTÉKELÉSE közben írt
tulajdonságot a Qt függőségként jegyzi meg — a következő változása
újraértékelteti a kötést, és a kör bezárul.

⚠️ A `width` nem tehet róla: az `parent.width - 40`, nem a szövegtől függ
(mérve a jegy szűkítésekor).

## Miért ÍGY mérünk

A tálcasáv szövege végig **kötött, csak olvasható** tulajdonságokból jön
(`trayInfoText` ← `ctl.trayInfo()`, `statusText`, …). Egy „állítsuk be a
szöveget, és nézzük, van-e hurok" próba tehát **vakon zöld** maradna: az
értékadás meg sem történne. (Az első változatom pontosan ebbe futott bele.)

Ezért a mechanizmust mérjük, két irányban:

1. a RÉGI minta (írás a mérő `text`-jébe a kötésből) **tényleg hurkol** —
   enélkül nem tudnánk, hogy a próba egyáltalán képes hurkot látni;
2. az ÚJ minta (`FontMetrics.advanceWidth()`) **nem hurkol**, és ugyanazt
   a leépülést adja.

Plusz egy forrás-őr: a `TrayBar.qml` mérőfüggvénye ne írjon tulajdonságot.
"""

from __future__ import annotations

from pathlib import Path

import picasapy.app.application as app_module
from PySide6.QtCore import QObject, QUrl, qInstallMessageHandler
from PySide6.QtQml import QQmlComponent

_KEEP_ALIVE: list = []

#: A két minta — a `%s` helyére a mérőfüggvény törzse kerül.
_KERET = """
import QtQuick
import QtQuick.Controls
import PicasaPy 1.0
import "infosav.js" as InfoSav

Item {
    width: 200
    height: 40
    Text {
        id: cimke
        objectName: "cimke"
        width: 120
        font.pixelSize: 12
        property string nyers: "C:\\\\Users\\\\sancho\\\\Kepek\\\\nagyon_hosszu_fajlnev.jpg"
        text: InfoSav.lecsokkentve(cimke.nyers, cimke.width, cimke.szelessege)
%s
    }
}
"""

_REGI = """        TextMetrics { id: metrika; font: cimke.font }
        function szelessege(szoveg) {
            metrika.text = szoveg
            return metrika.width
        }"""

_UJ = """        FontMetrics { id: metrika; font: cimke.font }
        function szelessege(szoveg) {
            return metrika.advanceWidth(szoveg)
        }"""


def _hurkok(engine, qt_app, torzs: str) -> tuple[list[str], str]:
    """A minta betöltése közben keletkezett hurok-üzenetek és a kész szöveg."""
    uzenetek: list[str] = []

    def kezelo(_tipus, _ctx, uzenet):
        if "Binding loop" in uzenet:
            uzenetek.append(uzenet)

    elozo = qInstallMessageHandler(kezelo)
    try:
        comp = QQmlComponent(engine)
        comp.setData(
            (_KERET % torzs).encode("utf-8"),
            QUrl.fromLocalFile(
                str(app_module._APP_DIR / "qml" / "PicasaPy" / "proba.qml")
            ),
        )
        gyoker = comp.create()
        assert [e.toString() for e in comp.errors()] == [], comp.errors()
        assert gyoker is not None
        _KEEP_ALIVE.extend((comp, gyoker))
        for _ in range(10):
            qt_app.processEvents()
        cimke = gyoker.findChild(QObject, "cimke")
        return uzenetek, str(cimke.property("text"))
    finally:
        qInstallMessageHandler(elozo)


class TestAProbaLatHurkot:
    """⛔ Ellenpróba: a RÉGI minta tényleg hurkol. Enélkül az „új minta nem
    hurkol" állítás semmit nem érne — lehet, hogy a próba vak."""

    def test_a_regi_minta_hurkol(self, qml_app, qt_app):
        _, _, engine = qml_app

        uzenetek, _ = _hurkok(engine, qt_app, _REGI)

        assert uzenetek, "a próba nem látott hurkot a RÉGI mintán sem"


class TestAzUjMinta:
    def test_nem_hurkol(self, qml_app, qt_app):
        _, _, engine = qml_app

        uzenetek, _ = _hurkok(engine, qt_app, _UJ)

        assert not uzenetek, "\n  ".join(sorted(set(uzenetek)))

    def test_UGYANAZT_a_leepulest_adja(self, qml_app, qt_app):
        """A hurok megszüntetése nem ronthatja el a mért leépülést (#2581)."""
        _, _, engine = qml_app

        _, regi_szoveg = _hurkok(engine, qt_app, _REGI)
        _, uj_szoveg = _hurkok(engine, qt_app, _UJ)

        assert uj_szoveg == regi_szoveg
        assert uj_szoveg, "a leépülés nem törölheti ki a szöveget"

    def test_a_hosszu_szoveg_TENYLEG_leepul(self, qml_app, qt_app):
        """Ha a próbaszöveg kiférne, a mérőfüggvény meg sem hívódna, és a
        fenti állítások vakon zöldek lennének."""
        _, _, engine = qml_app

        _, szoveg = _hurkok(engine, qt_app, _UJ)

        assert "nagyon_hosszu_fajlnev.jpg" not in szoveg or "…" in szoveg


class TestForras:
    def test_a_talcasav_meroje_nem_ir_tulajdonsagot(self):
        forras = (
            Path(app_module.__file__).parent
            / "qml" / "PicasaPy" / "TrayBar.qml"
        ).read_text(encoding="utf-8")

        assert "advanceWidth" in forras
        assert "infoMetrika.text =" not in forras
