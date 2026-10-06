"""#4448: a zenevezérlő működik eltérő ablakmagasságok mellett is."""

from __future__ import annotations

import pytest
from PySide6.QtCore import QMetaObject, QObject, QPointF, Qt, QUrl
from PySide6.QtQml import QQmlComponent, QQmlEngine
from PySide6.QtTest import QTest

from support.qt_wait import varj_feltetelre

_KEEPALIVE = []


def _kozeppont(qt_app, elem):
    """A kattintás helye csak elrendezés UTÁN számolható: CI-n az első
    képkockánál a méret még 0, és a kattintás mellémegy."""
    assert varj_feltetelre(qt_app, lambda: elem.width() > 0 and elem.height() > 0, 3.0)
    return elem.mapToScene(QPointF(elem.width() / 2, elem.height() / 2)).toPoint()


def _parbeszed(qt_app, magassag: int):
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
            objectName: "tesztAblak"
            visible: true
            width: 640
            height: {magassag}
            FolderPropertiesDialog {{ objectName: "folderPropertiesDialog" }}
        }}
        """.encode("utf-8"),
        QUrl(),
    )
    window = component.create()
    assert [error.toString() for error in component.errors()] == []
    assert window is not None
    QQmlEngine.setObjectOwnership(window, QQmlEngine.ObjectOwnership.CppOwnership)
    dialog = window.findChild(QObject, "folderPropertiesDialog")
    assert dialog is not None
    _KEEPALIVE.extend((engine, component, window))
    QMetaObject.invokeMethod(dialog, "open", Qt.ConnectionType.DirectConnection)
    assert varj_feltetelre(qt_app, lambda: dialog.property("opened"), 3.0)
    assert QTest.qWaitForWindowExposed(window)
    return window, dialog


@pytest.mark.parametrize("eltolas", [-5, 0, 5])
def test_a_jelolo_es_a_fajlvalaszto_a_valodi_vezerloket_kapcsolja(
    qt_app, tmp_path, eltolas
):
    window, dialog = _parbeszed(qt_app, 480 + eltolas)
    checkbox = dialog.findChild(QObject, "folderPropertiesUseMusic")
    path = dialog.findChild(QObject, "folderPropertiesMusicPath")
    browse = dialog.findChild(QObject, "folderPropertiesMusicBrowseButton")
    file_dialog = dialog.findChild(QObject, "folderPropertiesMusicFileDialog")

    assert checkbox.property("enabled") is True
    assert checkbox.property("checked") is False
    assert path.property("enabled") is False
    assert browse.property("enabled") is False

    point = _kozeppont(qt_app, checkbox)
    QTest.mouseClick(window, Qt.MouseButton.LeftButton,
                     Qt.KeyboardModifier.NoModifier, point)
    assert varj_feltetelre(qt_app, lambda: checkbox.property("checked"), 3.0)
    assert path.property("enabled") is True
    assert browse.property("enabled") is True

    point = _kozeppont(qt_app, browse)
    QTest.mouseClick(window, Qt.MouseButton.LeftButton,
                     Qt.KeyboardModifier.NoModifier, point)
    assert varj_feltetelre(
        qt_app, lambda: file_dialog.property("visible"), 3.0
    ), "a Tallózás gomb nem nyitotta meg a fájlválasztót"
    file_dialog.close()

    music = tmp_path / "nyar.mp3"
    music.write_bytes(b"teszt")
    path.setProperty("text", str(music))
    accepted = []
    dialog.folderMusicAccepted.connect(lambda *args: accepted.append(args))
    QMetaObject.invokeMethod(dialog, "accept", Qt.ConnectionType.DirectConnection)
    assert accepted == [("", True, str(music))]
