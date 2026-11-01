"""A Névjegy verziója és a futó példány mappája (#6365)."""

from PySide6.QtCore import QMetaObject, QObject, Qt
from PySide6.QtQuick import QQuickItem

from support.varakozas import var_feltetelre


def test_a_verzio_kotolejellel_es_a_futasi_mappaval_latszik(qml_app, qt_app):
    window, _controller, engine = qml_app
    hely = r"C:\Program Files\PicasaPy"
    engine.rootContext().setContextProperty("appVersion", "v1.0.11 (dev)")
    engine.rootContext().setContextProperty("appLocation", hely)

    menu_bars = [
        item
        for item in window.findChildren(QObject)
        if item.metaObject().indexOfSignal("aboutRequested()") >= 0
    ]
    assert len(menu_bars) == 1, "a Névjegy megnyitó jele hiányzik vagy többszörös"
    assert QMetaObject.invokeMethod(
        menu_bars[0], "aboutRequested", Qt.ConnectionType.DirectConnection
    )

    assert var_feltetelre(
        qt_app, lambda: window.findChild(QObject, "aboutDialog") is not None, 3
    ), (
        "a Névjegy párbeszéd nem épült fel"
    )
    about_dialog = window.findChild(QObject, "aboutDialog")
    szovegek = [
        item
        for item in about_dialog.findChildren(QQuickItem)
        if item.property("text") is not None
    ]
    feliratok = [str(item.property("text")) for item in szovegek]
    felirat = next(
        (szoveg for szoveg in feliratok if szoveg.startswith("PicasaPy ")),
        "",
    )

    assert "v1.0.11 (dev) - " in felirat
    assert "—" not in felirat
    assert hely in felirat
    assert "Location: " in felirat or "Hely: " in felirat
