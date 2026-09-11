"""#894 — a legördülő panel RAJZOLT ellenőrzése.

A forrás-szintű őr (`test_legordulo_rajza_894.py`) a mért SZÁMOKAT méri; ez a
próba azt, hogy a komponens fel is épül, a felugró megnyílik, és a háttere
tényleg a mért szín. A kettő együtt adja a bizonyítékot: „a teszt lásson,
ne csak számoljon".
"""

from __future__ import annotations

import time

import pytest
from PySide6.QtCore import QObject, QUrl
from PySide6.QtGui import QColor
from PySide6.QtQml import QQmlComponent
from PySide6.QtQuick import QQuickView

import picasapy.app.application as app_module

_QML = """
import QtQuick
import QtQuick.Controls
import PicasaPy 1.0
Item {
    id: gyoker
    objectName: "gyoker"
    width: 320; height: 240
    //: a felugrót csak QML-ből lehet megnyitni (a `popup` Pythonból nem
    //: olvasható ki — `Can't find converter for 'QQuickPopup*'`), a színeket
    //: pedig kötéssel hozzuk ki: a `background` a MÉRT árnyék-keret, az első
    //: gyereke a panel maga.
    function nyisd() { proba.popup.open() }
    readonly property string arnyekSzin:
        proba.popup && proba.popup.background
            ? String(proba.popup.background.color) : ""
    readonly property string panelSzin:
        proba.popup && proba.popup.background
            && proba.popup.background.children.length > 0
            ? String(proba.popup.background.children[0].color) : ""
    readonly property string keretSzin:
        proba.popup && proba.popup.background
            && proba.popup.background.children.length > 0
            ? String(proba.popup.background.children[0].border.color) : ""
    PicasaComboBox {
        id: proba
        objectName: "probaCombo"
        anchors.centerIn: parent
        width: 160
        model: ["egy", "ketto", "harom"]
    }
    ScrollBar {
        objectName: "nemhasznalt"
        visible: false
    }
    PicasaScrollBar {
        objectName: "probaSav"
        policy: ScrollBar.AlwaysOn
        size: 0.3
        orientation: Qt.Vertical
        height: 120
    }
}
"""


@pytest.fixture
def gyoker(qt_app):
    view = QQuickView()
    view.engine().addImportPath(str(app_module._APP_DIR / "qml"))
    component = QQmlComponent(view.engine())
    component.setData(_QML.encode("utf-8"), QUrl())
    hibak = [h.toString() for h in component.errors()]
    assert not hibak, "QML-hiba: " + "\n".join(hibak)
    item = component.create()
    assert item is not None, component.errorString()
    view.setContent(QUrl(), component, item)
    view.show()
    qt_app.processEvents()
    yield item
    view.hide()
    item.deleteLater()
    qt_app.processEvents()


def _gyerek(gyoker, nev):
    obj = gyoker.findChild(QObject, nev)
    assert obj is not None, f"{nev} nem található"
    return obj


class TestFelepul:
    def test_a_combobox_felepul_hiba_nelkul(self, gyoker):
        assert _gyerek(gyoker, "probaCombo") is not None

    def test_a_felugro_megnyilik_es_a_MERT_szineket_rajzolja(
        self, gyoker, qt_app
    ):
        from PySide6.QtCore import QMetaObject

        QMetaObject.invokeMethod(gyoker, "nyisd")
        hatarido = time.monotonic() + 3
        while time.monotonic() < hatarido and not gyoker.property("panelSzin"):
            qt_app.processEvents()
            time.sleep(0.01)
        qt_app.processEvents()

        panel = QColor(gyoker.property("panelSzin"))
        keret = QColor(gyoker.property("keretSzin"))
        arnyek = QColor(gyoker.property("arnyekSzin"))

        assert panel.name().lower() == "#e8e8e8", (
            f"a legördülő kitöltése nem a mért #E8E8E8, hanem {panel.name()}"
        )
        assert keret.name().lower() == "#bababa", (
            f"a keret nem a mért #BABABA, hanem {keret.name()}"
        )
        assert arnyek.name().lower() == "#d6d6d6", (
            f"az árnyék nem a mért #D6D6D6, hanem {arnyek.name()}"
        )

    def test_a_gorgetosav_huvelyke_atmenetes(self, gyoker, qt_app):
        """A hüvelyk `gradient`-je nem lehet `None` — enélkül visszaesnénk a
        sima színre, és a mérés nem látszana a rajzon."""
        sav = _gyerek(gyoker, "probaSav")
        huvelyk = sav.findChild(QObject, "picasaScrollThumb")
        assert huvelyk is not None, "nem épült fel a hüvelyk"
        assert huvelyk.property("gradient") is not None, (
            "a hüvelyknek nincs átmenete (#894)"
        )
