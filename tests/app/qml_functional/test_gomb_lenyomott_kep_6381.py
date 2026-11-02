"""#6381: a gomb lenyomása már az első kirajzolt képkockán látható."""

from __future__ import annotations

import math
import time
from pathlib import Path

import pytest
from PySide6.QtCore import QPoint, QPointF, Qt, QUrl
from PySide6.QtQuick import QQuickView
from PySide6.QtTest import QTest

_QML = Path(__file__).resolve().parents[3] / "src" / "picasapy" / "app" / "qml"


def _wait_for(qt_app, condition, message: str) -> None:
    deadline = time.monotonic() + 3.0
    while time.monotonic() < deadline:
        qt_app.processEvents()
        if condition():
            return
        time.sleep(0.01)
    qt_app.processEvents()
    assert condition(), message


def _pressed_surface(qt_app, *, lenyomasra: bool, height_offset: int):
    view = QQuickView()
    view.engine().addImportPath(str(_QML))
    view.setResizeMode(QQuickView.ResizeMode.SizeRootObjectToView)
    view.setSource(QUrl.fromLocalFile(str(_QML / "PicasaPy" / "PicasaButton.qml")))
    assert view.status() == QQuickView.Status.Ready, [
        error.toString() for error in view.errors()
    ]
    button = view.rootObject()
    button.setProperty("objectName", "accentPressPixelProbe")
    button.setProperty("text", "")
    assert button.setProperty("accent", "#3c8f3c")
    button.setProperty("lenyomasra", lenyomasra)
    button.setProperty("x", 0)
    button.setProperty("y", 0)
    button.setProperty("width", 180)
    button.setProperty("height", 40 + height_offset)
    view.resize(180, 40 + height_offset)
    view.show()
    _wait_for(qt_app, view.isExposed, "a próbaablak nem jelent meg")

    view.requestUpdate()
    qt_app.processEvents()
    nyugalmi = view.grabWindow()
    assert not nyugalmi.isNull(), "a nyugalmi gombképkocka üres"

    center = button.mapToScene(
        QPointF(button.property("width") / 2, button.property("height") / 2)
    )
    QTest.mousePress(
        view,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        QPoint(round(center.x()), round(center.y())),
    )
    _wait_for(
        qt_app,
        lambda: bool(button.property("visiblyDown")),
        "a valódi egérlenyomás nem érte el a QML-gombot",
    )
    view.requestUpdate()
    qt_app.processEvents()
    lenyomott = view.grabWindow()
    assert not lenyomott.isNull(), "a lenyomott gombképkocka üres"

    dpr = lenyomott.width() / view.width()
    y = round(center.y() * dpr)
    left = math.ceil(4 * dpr)
    right = math.floor((button.property("width") - 4) * dpr)
    kulonbozo = sum(
        nyugalmi.pixelColor(x, y) != lenyomott.pixelColor(x, y)
        for x in range(left, right + 1)
    )

    QTest.mouseRelease(
        view,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        QPoint(round(center.x()), round(center.y())),
    )
    view.close()
    view.deleteLater()
    qt_app.processEvents()
    return kulonbozo


@pytest.mark.parametrize(
    ("lenyomasra", "height_offset"),
    [
        (lenyomasra, height_offset)
        for height_offset in (-5, 0, 5)
        for lenyomasra in (False, True)
    ],
    ids=[
        f"{allapot}_{height_offset:+d}px"
        for height_offset in (-5, 0, 5)
        for allapot in ("felengedes", "lenyomas")
    ],
)
def test_a_zold_gomb_lenyomasa_lathato_keppontvaltozast_ad(
    qt_app, lenyomasra, height_offset
):
    """A szöveg nélküli kitöltéssorban mérünk, betűmetrika nélkül."""
    valtozott = _pressed_surface(
        qt_app, lenyomasra=lenyomasra, height_offset=height_offset
    )
    assert valtozott > 0, (
        "a zöld PicasaButton lenyomott képkockája pixelre azonos a nyugalmi "
        f"állapottal (lenyomasra={lenyomasra}, height_offset={height_offset})"
    )
