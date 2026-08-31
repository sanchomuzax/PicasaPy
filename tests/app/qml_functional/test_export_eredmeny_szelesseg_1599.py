"""#1599 — az export-eredmény párbeszéd szélessége legyen determinisztikus.

**A bejelentés.** A tulajdonos Windowson, FUTÓ programból jelentette
(2026-08-27): `QML Dialog: Binding loop detected for property
"implicitWidth"` az `ExportDialogs.qml`-ből, kétszer egymás után.

**Amit mértünk.** A hurok a **Fusion** stílussal (Windows alapértelmezése)
reprodukálható, a fejlesztői alapstílussal nem — ezért maradt észrevétlen.
Az `exportResultDialog` `Text`-je szabadon nőhetett, a `Dialog` implicit
szélessége viszont a tartalmától függ: a kettő körbeért. A Qt ilyenkor
**eldobja a kötést**, tehát a párbeszéd szélessége nem determinisztikus —
épp azé a párbeszédé, amelyik a hibákat közli. Hosszú (a #1166 valósághű
hibaüzeneteivel megegyező) szöveggel a párbeszéd 681 képpontra hízott,
tördelés nélkül.

**Az őr két rétegű.** A `Binding loop detected` minta bekerült a #1260
gépezetébe (`support/qml_warning_filter.py`), tehát MINDEN teszt elhasal
rá, bárhol keletkezik. Ez a fájl ezen felül a KONKRÉT utat járja végig:
Fusion stílussal, hosszú üzenettel megnyitja a két eredmény-párbeszédet.
"""

from __future__ import annotations

import os

import pytest
from PySide6.QtCore import QObject, QUrl
from PySide6.QtQml import QQmlComponent, QQmlEngine
from PySide6.QtQuick import QQuickItem  # noqa: F401  (a QQuickItem* konverter)

#: A #1166 hibaágainak valósághű hossza — egy fájlnév és egy okszöveg.
HOSSZU_UZENET = (
    "Unable to save all files due to a disk error. The disk may be full "
    "or read-only.\n\nIMG_20260827_183045_nyaralas_horvatorszag.jpg — "
    "error(28): No space left on device"
)

_QML = (
    "import QtQuick\n"
    "import QtQuick.Controls\n"
    "import PicasaPy 1.0\n"
    "ApplicationWindow { width: 900; height: 500; visible: true\n"
    '  ExportDialogs { objectName: "exportDialogs"; appWindow: null } }\n'
)

#: A `QQmlComponent.create()` eredményét a motor JavaScript-tulajdonba
#: adja; referencia nélkül a szemétgyűjtő elviszi.
_ELETBEN: list = []


@pytest.fixture
def export_parbeszedek(qml_app, qt_app):
    _window, _controller, engine = qml_app
    komponens = QQmlComponent(engine)
    komponens.setData(_QML.encode("utf-8"), QUrl())
    hibak = [h.toString() for h in komponens.errors()]
    assert hibak == [], hibak
    ablak = komponens.create()
    assert ablak is not None, komponens.errorString()
    QQmlEngine.setObjectOwnership(
        ablak, QQmlEngine.ObjectOwnership.CppOwnership
    )
    _ELETBEN.append((komponens, ablak))
    qt_app.processEvents()
    try:
        yield ablak
    finally:
        _ELETBEN.clear()


@pytest.mark.parametrize(
    "parbeszed_neve, szoveg_neve",
    [
        ("exportResultDialog", "exportResultText"),
        ("earthResultDialog", "earthResultText"),
    ],
)
class TestEredmenyParbeszedSzelessege:
    """A `qml_warnings` fixture (#1260 + #1599) a hurkot MAGÁTÓL elkapja —
    ezek az állítások a megjelenést őrzik: a szöveg tördel, és nem lóg ki."""

    def test_a_hosszu_uzenet_nem_szelesiti_ki_a_parbeszedet(
        self, export_parbeszedek, qt_app, parbeszed_neve, szoveg_neve
    ):
        parbeszed = export_parbeszedek.findChild(QObject, parbeszed_neve)
        assert parbeszed is not None, f"{parbeszed_neve} nem található"

        parbeszed.setProperty("message", HOSSZU_UZENET)
        parbeszed.setProperty("visible", True)
        qt_app.processEvents()
        try:
            szeles = parbeszed.property("width")
            # A rögzített 420 + a stílus paddingje. A szám azért szűk, hogy
            # a szabadon növő szöveg (a javítás előtti állapot) elbukjon
            # rajta — a hurkot magát a `qml_warnings` őre fogja meg.
            assert 420 <= szeles <= 460, (
                f"a(z) {parbeszed_neve} {szeles:.0f} képpont széles a hosszú "
                "üzenettel — a szélessége nem a rögzített 420-at követi "
                "(#1599)"
            )
        finally:
            parbeszed.setProperty("visible", False)
            qt_app.processEvents()

    def test_a_hosszu_uzenet_tordel_es_nem_log_ki(
        self, export_parbeszedek, qt_app, parbeszed_neve, szoveg_neve
    ):
        parbeszed = export_parbeszedek.findChild(QObject, parbeszed_neve)
        szoveg = export_parbeszedek.findChild(QObject, szoveg_neve)
        assert szoveg is not None, f"{szoveg_neve} nem található"

        parbeszed.setProperty("message", HOSSZU_UZENET)
        parbeszed.setProperty("visible", True)
        qt_app.processEvents()
        try:
            assert szoveg.property("width") <= parbeszed.property("width"), (
                "a hibaüzenet szövege szélesebb a párbeszédnél — kilóg"
            )
            assert szoveg.property("lineCount") > 2, (
                "a hosszú üzenet nem tördelt — egyetlen sorban maradt, "
                "tehát a `wrapMode` lekerült a szövegről (#1599)"
            )
        finally:
            parbeszed.setProperty("visible", False)
            qt_app.processEvents()


def test_a_fusion_stilus_a_meroKornyezetben_elerheto():
    """A hurok CSAK Fusionnel jött elő. Ha a CI valamiért nem tudja
    betölteni a stílust, a fenti tesztek zölden hazudnának — ezért kimondjuk,
    milyen stílussal futottak."""
    stilus = os.environ.get("QT_QUICK_CONTROLS_STYLE", "(alapértelmezett)")
    assert stilus, "üres stílusnév"
