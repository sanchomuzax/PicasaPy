"""#4127: a videóvezérlők látható kimenete kis, önálló QML-ablakban."""

from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


def main() -> None:
    import picasapy.app.application as app_module
    from PySide6.QtCore import QMetaObject, QObject, Qt
    from PySide6.QtGui import QGuiApplication, QImage
    from PySide6.QtMultimedia import QVideoFrame
    from PySide6.QtQml import QQmlApplicationEngine

    app = QGuiApplication([])
    engine = QQmlApplicationEngine()
    engine.addImportPath(str(app_module._APP_DIR / "qml"))
    engine.loadData(
        b"""import QtQuick
import QtQuick.Controls
import QtQuick.Window
import PicasaPy 1.0

ApplicationWindow {
    id: testWindow
    objectName: "videoControlsTestWindow"
    width: 800
    height: 600
    visible: true
    property bool actualSizeEnabled: false
    VideoViewport {
        id: viewport
        objectName: "videoViewportUnderTest"
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: parent.top
        anchors.bottom: controls.top
        actualSizeEnabled: testWindow.actualSizeEnabled
    }
    VideoPlayerControls {
        id: controls
        objectName: "videoControlsUnderTest"
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        actualSizeEnabled: testWindow.actualSizeEnabled
        onActualSizeToggled: function(enabled) {
            testWindow.actualSizeEnabled = enabled
        }
    }
}
"""
    )
    assert engine.rootObjects(), "a tesztablak QML-betöltése sikertelen"
    window = engine.rootObjects()[0]
    app.processEvents()

    def child(name: str) -> QObject:
        obj = window.findChild(QObject, name)
        assert obj is not None, f"{name} nem található"
        return obj

    child("videoControlsUnderTest")
    size_button = child("videoActualSizeButton")
    fullscreen_button = child("videoFullscreenButton")
    viewport = child("videoViewportUnderTest")
    video_output = viewport.findChild(QObject, "videoOutput")
    assert video_output is not None, "a VideoOutput nem található"

    sink = video_output.property("videoSink")
    assert sink is not None, "a videokimenet nem adott QVideoSink-et"
    # A képkockát közvetlenül adjuk a kimenetnek: a dekóder és a kodek nem
    # befolyásolja a natív méret mérését.
    frame = QImage(640, 360, QImage.Format.Format_RGB32)
    frame.fill(0xFF336699)
    sink.setVideoFrame(QVideoFrame(frame))
    app.processEvents()

    def kattint(gomb: QObject) -> None:
        siker = QMetaObject.invokeMethod(
            gomb, "click", Qt.ConnectionType.DirectConnection
        )
        assert siker, f"a(z) {gomb.objectName()} nem kattintható"
        app.processEvents()

    assert window.property("actualSizeEnabled") is False
    alap_meret = window.size()
    kattint(size_button)
    assert window.property("actualSizeEnabled") is True

    dpr = float(window.devicePixelRatio())
    vart_szelesseg = frame.width() / dpr
    vart_magassag = frame.height() / dpr
    for eltolás in (-5, 0, 5):
        window.resize(alap_meret.width(), alap_meret.height() + eltolás)
        app.processEvents()
        app.processEvents()
        assert abs(video_output.property("width") - vart_szelesseg) <= 3, (
            "1:1 módban a videó szélessége nem a képkocka mérete: "
            f"{video_output.property('width')} vs {vart_szelesseg}"
        )
        assert abs(video_output.property("height") - vart_magassag) <= 3, (
            "1:1 módban a videó magassága nem a képkocka mérete: "
            f"{video_output.property('height')} vs {vart_magassag}"
        )
        kozep = video_output.mapToItem(
            viewport, video_output.boundingRect().center()
        )
        assert abs(kozep.x() - viewport.property("width") / 2) <= 3
        assert abs(kozep.y() - viewport.property("height") / 2) <= 3

    window.resize(alap_meret)
    kattint(size_button)
    assert window.property("actualSizeEnabled") is False
    assert abs(
        video_output.property("width") - viewport.property("width")
    ) <= 3
    assert abs(
        video_output.property("height") - viewport.property("height")
    ) <= 3

    eredeti_lathatosag = window.visibility()
    kattint(fullscreen_button)
    assert window.visibility() == window.Visibility.FullScreen
    kattint(fullscreen_button)
    assert window.visibility() == eredeti_lathatosag
    print("OK #4127: képméret, középre igazítás, teljes képernyő")


if __name__ == "__main__":
    main()
