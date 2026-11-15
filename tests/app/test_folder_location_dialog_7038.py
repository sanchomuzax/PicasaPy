"""#7038: a mappa Hely mezője szerkeszthető, és hiba esetén nyitva marad."""

from __future__ import annotations

import pytest
from PySide6.QtCore import QObject, QPoint, QPointF, QUrl, Qt
from PySide6.QtQml import QQmlComponent, QQmlEngine
from PySide6.QtTest import QTest

from tests.support.varakozas import var_feltetelre

_KEEPALIVE = []


@pytest.mark.parametrize("height_delta", (-5, 0, 5))
def test_hely_prefill_irasihibanal_nyitva_marad_es_megjegyzi_a_beirast(
    qt_app, height_delta
):
    import picasapy.app.application as app_module

    engine = QQmlEngine()
    engine.addImportPath(str(app_module._APP_DIR / "qml"))
    component = QQmlComponent(engine)
    component.setData(
        f"""
        import QtQuick
        import QtQuick.Controls
        import QtQuick.Window
        import PicasaPy 1.0
        Window {{
            id: frame
            objectName: "frame"
            visible: true
            width: 600
            height: {500 + height_delta}
            property string lastPath: ""
            property string lastLocation: ""
            FolderPropertiesDialog {{
                objectName: "properties"
                folderLocationHandler: function(path, location) {{
                    frame.lastPath = path
                    frame.lastLocation = location
                    return false
                }}
            }}
        }}
        """.encode("utf-8"),
        QUrl(),
    )
    window = component.create()
    assert [error.toString() for error in component.errors()] == []
    assert window is not None
    dialog = window.findChild(QObject, "properties")
    assert dialog is not None
    QQmlEngine.setObjectOwnership(window, QQmlEngine.ObjectOwnership.CppOwnership)
    _KEEPALIVE.extend((engine, component, window))

    dialog.setProperty("folderPath", "/kepek/nyar")
    dialog.setProperty("folderName", "nyar")
    dialog.setProperty("folderLocation", "Balaton")
    assert QTest.qWaitForWindowExposed(window)
    dialog.open()
    assert var_feltetelre(qt_app, lambda: dialog.property("opened"), 3.0)

    field = window.findChild(QObject, "folderPropertiesLocation")
    assert field is not None
    assert field.property("enabled") is True
    assert field.property("text") == "Balaton"
    point = field.mapToScene(
        QPointF(float(field.property("width")) / 2,
                float(field.property("height")) / 2)
    )
    QTest.mouseClick(
        window,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        QPoint(round(point.x()), round(point.y())),
    )
    QTest.keyClick(window, Qt.Key.Key_A, Qt.KeyboardModifier.ControlModifier)
    for character in "Tihany":
        QTest.keyEvent(QTest.KeyAction.Click, window, ord(character))
    qt_app.processEvents()
    assert field.property("text") == "Tihany"

    ok = window.findChild(QObject, "folderPropertiesOkButton")
    assert ok is not None
    point = ok.mapToScene(
        QPointF(float(ok.property("width")) / 2,
                float(ok.property("height")) / 2)
    )
    QTest.mouseClick(
        window,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        QPoint(round(point.x()), round(point.y())),
    )
    qt_app.processEvents()

    assert window.property("lastPath") == "/kepek/nyar"
    assert window.property("lastLocation") == "Tihany"
    assert dialog.property("opened") is True
    assert field.property("text") == "Tihany"
    assert dialog.property("folderLocation") == "Balaton"
