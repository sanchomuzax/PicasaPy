#!/usr/bin/env python3
"""PySide6/QML thumbnail-rács benchmark (GPU-s GridView, aszinkron képbetöltés).

Használat: qml_grid.py <thumbs_dir> [item_count]
FPS a bal felső sarokban; Esc = kilépés.
"""
import sys
import time
from pathlib import Path

from PySide6.QtCore import QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine

QML = """
import QtQuick
import QtQuick.Controls

ApplicationWindow {
    id: win
    visible: true
    width: 1280; height: 800
    title: "PicasaPy bench: PySide6/QML GridView"
    color: "#202020"

    property int frames: 0
    property real fps: 0

    FrameAnimation {
        running: true
        onTriggered: win.frames++
    }
    Timer {
        interval: 1000; running: true; repeat: true
        onTriggered: { win.fps = win.frames; win.frames = 0 }
    }

    GridView {
        id: grid
        anchors.fill: parent
        cellWidth: 176; cellHeight: 176
        cacheBuffer: 352
        model: itemPaths
        delegate: Item {
            width: 176; height: 176
            Rectangle { anchors.fill: parent; anchors.margins: 4; color: "#303030" }
            Image {
                anchors.fill: parent; anchors.margins: 6
                source: modelData
                asynchronous: true
                fillMode: Image.PreserveAspectFit
                sourceSize.width: 256
            }
        }
        ScrollBar.vertical: ScrollBar { }
        focus: true
        Keys.onEscapePressed: Qt.quit()
    }

    Rectangle {
        x: 8; y: 8; width: fpsText.width + 16; height: 28
        color: "#c0000000"; radius: 4
        Text {
            id: fpsText; anchors.centerIn: parent
            text: win.fps.toFixed(0) + " FPS"
            color: win.fps > 50 ? "#4caf50" : (win.fps > 25 ? "#ffc107" : "#f44336")
            font.pixelSize: 16; font.bold: true
        }
    }
}
"""


def main():
    thumbs = sorted(Path(sys.argv[1]).glob("*.jpg"))
    count = int(sys.argv[2]) if len(sys.argv) > 2 else 5000
    paths = [QUrl.fromLocalFile(str(thumbs[i % len(thumbs)])).toString()
             for i in range(count)]

    t0 = time.perf_counter()
    app = QGuiApplication(sys.argv)
    engine = QQmlApplicationEngine()
    engine.setInitialProperties({})
    engine.rootContext().setContextProperty("itemPaths", paths)
    engine.loadData(QML.encode())
    if not engine.rootObjects():
        sys.exit(1)
    print(f"indulás→ablak: {time.perf_counter() - t0:.2f}s", flush=True)
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
