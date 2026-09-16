"""#1908 — az ECSET felülete: a festhető maszk vezérlői és a kép fölötti réteg.

Amit mérünk:

* az ecset-blokk CSAK akkor látszik, ha a nyitott effekt festhető maszkkal
  dolgozik (`paintMaskSupported`);
* a felirat a radír állásától függ — „Ecsetméret" vagy „Radír mérete"
  (mért, hivatalos magyar feliratok);
* a csúszka és a jelölő tényleg a vezérlőnek szól
  (`setPaintBrushRatio`, `setPaintEraser`);
* a kép fölötti festőréteg a KIRAJZOLT képhez normálva küldi a vonást.

⚠️ A LÁTVÁNYT (a kör alakú mutató rajzát) ez a teszt nem méri — ahhoz
referencia-képernyőkép kellene.
"""

from pathlib import Path

import pytest
from PySide6.QtCore import QObject, Property, Signal, Slot, QUrl
from PySide6.QtQml import QQmlComponent, QQmlEngine

_KEEPALIVE = []

_QML_DIR = Path(__file__).resolve().parents[2] / "src/picasapy/app/qml/PicasaPy"


class EcsetCsonk(QObject):
    """A vezérlő ecset-felülete, csak annyi, amennyit a panel megszólít."""

    paintMaskChanged = Signal()

    def __init__(self):
        super().__init__()
        self._tamogatott = True
        self._arany = 0.03
        self._radir = False
        self.hivasok = []

    @Property(bool, notify=paintMaskChanged)
    def paintMaskSupported(self):  # noqa: N802
        return self._tamogatott

    @Property(float, notify=paintMaskChanged)
    def paintBrushRatio(self):  # noqa: N802
        return self._arany

    @Property(float, notify=paintMaskChanged)
    def paintBrushMax(self):  # noqa: N802
        return 0.2

    @Property(bool, notify=paintMaskChanged)
    def paintEraser(self):  # noqa: N802
        return self._radir

    @Slot(float)
    def setPaintBrushRatio(self, arany):  # noqa: N802
        self._arany = arany
        self.hivasok.append(("meret", arany))
        self.paintMaskChanged.emit()

    @Slot(bool)
    def setPaintEraser(self, be):  # noqa: N802
        self._radir = bool(be)
        self.hivasok.append(("radir", self._radir))
        self.paintMaskChanged.emit()

    def allitsd_tamogatast(self, be):
        self._tamogatott = bool(be)
        self.paintMaskChanged.emit()


_PANEL_CSONK = """
import QtQuick
import PicasaPy 1.0

Item {
    width: 300
    height: 600
    property QtObject panel: QtObject {
        property bool enabled: true
        property string paramEffectTitle: "Boost"
        property var paramEffectParams: []
        function paramLabel(k) { return k }
        function updateParamValue(i, v) {}
        function applyParamPanel() {}
        function cancelParamPanel() {}
    }
    EditorParamPanel {
        objectName: "azPanel"
        anchors.fill: parent
        panel: parent.panel
    }
}
"""


@pytest.fixture
def betoltott(qt_app):
    import picasapy.app.application as app_module

    engine = QQmlEngine()
    engine.addImportPath(str(app_module._APP_DIR / "qml"))
    csonk = EcsetCsonk()
    engine.rootContext().setContextProperty("editController", csonk)
    component = QQmlComponent(engine)
    component.setData(_PANEL_CSONK.encode("utf-8"), QUrl())
    obj = component.create()
    assert [e.toString() for e in component.errors()] == []
    assert obj is not None
    QQmlEngine.setObjectOwnership(obj, QQmlEngine.ObjectOwnership.CppOwnership)
    _KEEPALIVE.extend([component, obj])
    yield obj, csonk
    engine.deleteLater()


def _gyerek(gyoker, nev):
    obj = gyoker.findChild(QObject, nev)
    assert obj is not None, f"{nev} nem található"
    return obj


class TestEcsetVezerlo:
    def test_festheto_effektnel_latszik(self, betoltott):
        gyoker, _csonk = betoltott
        assert _gyerek(gyoker, "effectParamBrushBlock").property("visible") is True

    def test_nem_festheto_effektnel_rejtve(self, betoltott):
        gyoker, csonk = betoltott
        csonk.allitsd_tamogatast(False)
        assert _gyerek(gyoker, "effectParamBrushBlock").property("visible") is False

    def test_a_felirat_a_radirral_valt(self, betoltott):
        gyoker, csonk = betoltott
        felirat = _gyerek(gyoker, "effectParamBrushLabel")
        assert felirat.property("text") == "Brush Size"
        csonk.setPaintEraser(True)
        assert felirat.property("text") == "Eraser Size"

    def test_a_csuszka_tartomanya_a_vezerlotol_jon(self, betoltott):
        gyoker, _csonk = betoltott
        csuszka = _gyerek(gyoker, "effectParamBrushSlider")
        assert csuszka.property("to") == pytest.approx(0.2)
        assert csuszka.property("value") == pytest.approx(0.03)

    def test_a_csuszka_mozgatasa_a_vezerlonek_szol(self, betoltott):
        gyoker, csonk = betoltott
        csuszka = _gyerek(gyoker, "effectParamBrushSlider")
        csuszka.setProperty("value", 0.1)
        csuszka.moved.emit()
        assert ("meret", pytest.approx(0.1)) in [
            (nev, ertek) for nev, ertek in csonk.hivasok
        ]

    def test_a_jelolo_radirra_valt(self, betoltott):
        gyoker, csonk = betoltott
        jelolo = _gyerek(gyoker, "effectParamEraserCheckbox")
        jelolo.setProperty("checked", True)
        jelolo.toggled.emit()
        assert ("radir", True) in csonk.hivasok


class TestFestoReteg:
    """A kép fölötti réteg — a forrásban mérve (a PhotoViewer önmagában
    nem tölthető be: a teljes fő ablak környezetét kéri)."""

    @property
    def forras(self):
        return (_QML_DIR / "PhotoViewer.qml").read_text(encoding="utf-8")

    def test_a_reteg_letezik(self):
        assert 'objectName: "paintMaskArea"' in self.forras

    def test_csak_festheto_effektnel_aktiv(self):
        assert "editController.paintMaskSupported" in self.forras

    def test_a_vonas_a_kirajzolt_kephez_normalt(self):
        f = self.forras
        assert "pont.x / Math.max(1, width)" in f
        assert "pont.y / Math.max(1, height)" in f

    def test_a_mutato_kor_alaku(self):
        f = self.forras
        assert 'objectName: "paintMaskCursor"' in f
        assert "radius: sugar" in f
