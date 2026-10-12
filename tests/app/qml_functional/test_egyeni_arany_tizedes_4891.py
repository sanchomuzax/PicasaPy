"""#4891: az Egyéni méretarány párbeszéd tizedes értéke magyar és angol
területi beállításban — gépeléssel és az OK gomb KATTINTÁSÁVAL.

A hiba: a `DoubleValidator` magyar területi beállításban az `1,5`-öt
elfogadta, a `Number("1,5")` viszont NaN-t adott, így az OK gomb sosem
kapcsolt be. A teszt a felhasználó útját járja: mezőre kattint, gépel,
az OK gombra kattint — nem hív metódust."""

from __future__ import annotations


import pytest
from PySide6.QtCore import QLocale, QObject, QPointF, Qt, QUrl
from PySide6.QtQml import QQmlComponent
from PySide6.QtQuick import QQuickView
from PySide6.QtTest import QTest

_KEEPALIVE: list[object] = []

_QML = b"""
import QtQuick
import QtQuick.Controls
import PicasaPy 1.0
Item {
    id: gyoker
    width: 420
    height: 260
    property var kapott: []
    AddCustomAspectRatioDialog {
        id: parbeszed
        objectName: "addCustomAspectRatioDialog"
        parent: gyoker
        onCreated: function(w, h, n) { gyoker.kapott = [w, h, n] }
        Component.onCompleted: open()
        onOpened: standardButton(Dialog.Ok).objectName = "customAspectOkButton"
    }
}
"""


@pytest.fixture
def locale_vissza():
    regi = QLocale()
    yield
    QLocale.setDefault(regi)


def _parbeszed(qt_app, nyelv: str):
    import picasapy.app.application as app_module

    QLocale.setDefault(QLocale(nyelv))
    view = QQuickView()
    view.engine().addImportPath(str(app_module._APP_DIR / "qml"))
    component = QQmlComponent(view.engine())
    component.setData(_QML, QUrl())
    assert [e.toString() for e in component.errors()] == []
    root = component.create()
    assert root is not None
    root.setParentItem(view.contentItem())
    view.resize(420, 260)
    view.show()
    QTest.qWaitForWindowExposed(view)
    for _ in range(10):
        qt_app.processEvents()
    _KEEPALIVE.extend((view, root, component))
    return view, root


def _elem(root, nev: str):
    elem = root.findChild(QObject, nev)
    if elem is None:
        verem = [root.window().contentItem()]
        while verem and elem is None:
            x = verem.pop()
            if x.objectName() == nev:
                elem = x
            verem.extend(x.childItems())
    assert elem is not None, f"nem található: {nev}"
    return elem


def _kattint(qt_app, view, elem) -> None:
    pont = elem.mapToScene(QPointF(elem.width() / 2, elem.height() / 2)).toPoint()
    QTest.mouseClick(view, Qt.LeftButton, Qt.NoModifier, pont)
    qt_app.processEvents()


def _beir(qt_app, view, root, mezo: str, szoveg: str) -> None:
    _kattint(qt_app, view, _elem(root, mezo))
    for jel in szoveg:
        QTest.keyClick(view, jel)
    qt_app.processEvents()


def _kitolt(qt_app, nyelv, szel, mag, nev="Panorama"):
    view, root = _parbeszed(qt_app, nyelv)
    _beir(qt_app, view, root, "customAspectWidthField", szel)
    _beir(qt_app, view, root, "customAspectHeightField", mag)
    _beir(qt_app, view, root, "customAspectNameField", nev)
    return view, root


@pytest.mark.parametrize("szel", ["1,5", "1.5"])
def test_magyar_feluleten_a_vesszos_es_a_pontos_tizedes_is_elfogadott(
    qt_app, locale_vissza, szel
):
    view, root = _kitolt(qt_app, "hu_HU", szel, "1")
    ok = _elem(root, "customAspectOkButton")
    assert ok.property("enabled") is True
    _kattint(qt_app, view, ok)
    assert root.property("kapott").toVariant() == [1.5, 1.0, "Panorama"]


def test_angol_feluleten_a_pontos_tizedes_elfogadott(qt_app, locale_vissza):
    view, root = _kitolt(qt_app, "en_US", "1.5", "1")
    ok = _elem(root, "customAspectOkButton")
    assert ok.property("enabled") is True
    _kattint(qt_app, view, ok)
    assert root.property("kapott").toVariant() == [1.5, 1.0, "Panorama"]


def test_ervenytelen_szamnal_az_ok_gomb_tiltott(qt_app, locale_vissza):
    view, root = _kitolt(qt_app, "hu_HU", "0", "1")
    assert _elem(root, "customAspectOkButton").property("enabled") is False
