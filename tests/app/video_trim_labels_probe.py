"""Standalone QML render probe for the #4273 trim-track labels."""

from __future__ import annotations

import sys
import time
from pathlib import Path

from PySide6.QtCore import QObject, QPointF, QTranslator, QUrl
from PySide6.QtGui import QColor, QGuiApplication
from PySide6.QtQml import QQmlComponent, QQmlEngine
from PySide6.QtQuick import QQuickWindow


def _required(root: QObject, name: str) -> QObject:
    item = root.findChild(QObject, name)
    assert item is not None, f"a(z) {name} elem nem jelent meg"
    return item


def _center_x(item: QObject) -> float:
    point = item.mapToScene(QPointF(item.width() / 2, item.height() / 2))
    return point.x()


def _has_rendered_ink(image, item: QObject, background: QColor) -> bool:
    origin = item.mapToScene(QPointF(0, 0))
    scale = image.devicePixelRatio()
    left = max(0, int(origin.x() * scale))
    top = max(0, int(origin.y() * scale))
    right = min(image.width(), int((origin.x() + item.width()) * scale + 1))
    bottom = min(image.height(), int((origin.y() + item.height()) * scale + 1))
    return any(
        image.pixelColor(x, y).name() != background.name()
        for y in range(top, bottom)
        for x in range(left, right)
    )


def main(height: int, screenshot: Path) -> None:
    app = QGuiApplication.instance() or QGuiApplication([])
    translator = QTranslator(app)
    qm = (
        Path(__file__).resolve().parents[2]
        / "src"
        / "picasapy"
        / "app"
        / "i18n"
        / "picasapy_hu.qm"
    )
    assert translator.load(str(qm)), f"a fordítás nem tölthető be: {qm}"
    app.installTranslator(translator)

    qml = (
        Path(__file__).resolve().parents[2]
        / "src"
        / "picasapy"
        / "app"
        / "qml"
        / "PicasaPy"
        / "VideoTrimSlider.qml"
    )
    engine = QQmlEngine()
    component = QQmlComponent(engine, QUrl.fromLocalFile(str(qml)))
    root = component.create()
    assert root is not None, "a vágócsúszka nem példányosítható: " + "\n".join(
        error.toString() for error in component.errors()
    )
    root.setProperty("durationMs", 100_000)
    root.setProperty("startMs", 25_000)
    root.setProperty("endMs", 75_000)
    root.setWidth(380)
    root.setHeight(34)

    window = QQuickWindow()
    window.setColor(QColor("#2b2b2b"))
    window.resize(400, height)
    root.setParentItem(window.contentItem())
    root.setX(10)
    root.setY((height - root.height()) / 2)
    window.show()

    start_label = _required(root, "videoTrimStartLabel")
    end_label = _required(root, "videoTrimEndLabel")
    start_thumb = _required(root, "videoTrimStartThumb")
    end_thumb = _required(root, "videoTrimEndThumb")

    deadline = time.monotonic() + 3.0
    image = None
    while time.monotonic() < deadline:
        app.processEvents()
        image = window.grabWindow()
        if image is not None and not image.isNull():
            break
        time.sleep(0.05)

    assert image is not None and not image.isNull(), "a QML-felület nem renderelődött"
    assert start_label.isVisible() and end_label.isVisible()
    assert start_label.property("text") == "Kezdőpont"
    assert end_label.property("text") == "Végpont"
    assert abs(_center_x(start_label) - _center_x(start_thumb)) <= 2
    assert abs(_center_x(end_label) - _center_x(end_thumb)) <= 2
    assert _has_rendered_ink(image, start_label, QColor("#2b2b2b"))
    assert _has_rendered_ink(image, end_label, QColor("#2b2b2b"))
    assert image.save(str(screenshot)), f"a renderelt kép nem menthető: {screenshot}"

    print(
        f"OK #4273 height={height} start=Kezdőpont end=Végpont "
        f"text-boxes={start_label.width():.1f}x{start_label.height():.1f},"
        f"{end_label.width():.1f}x{end_label.height():.1f}"
    )
    window.close()
    engine.deleteLater()
    app.processEvents()


if __name__ == "__main__":
    main(int(sys.argv[1]), Path(sys.argv[2]))
