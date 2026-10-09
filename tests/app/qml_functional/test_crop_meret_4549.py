"""A vágó méretarány-sorai az aktuális képpontméretet mutatják (#4549)."""

from __future__ import annotations

import re
import time

from PySide6.QtCore import QObject, QPoint, QPointF, QRectF, Qt
from PySide6.QtTest import QTest


def _item(window, name: str):
    item = window.findChild(QObject, name)
    assert item is not None, f"{name} nem található"
    return item


def _pump(qt_app, count: int = 4) -> None:
    for _ in range(count):
        qt_app.processEvents()


def _wait_until(condition, qt_app, timeout_seconds: float = 3.0) -> None:
    deadline = time.monotonic() + timeout_seconds
    while not condition() and time.monotonic() < deadline:
        QTest.qWait(20)
        _pump(qt_app, 2)
    assert condition(), "a vágó felülete nem épült fel a határidőn belül"


def _point(item, x: float = 0.5, y: float = 0.5) -> QPoint:
    scene = item.mapToScene(QPointF(item.width() * x, item.height() * y))
    return QPoint(round(scene.x()), round(scene.y()))


def _click(window, item, qt_app, x: float = 0.5, y: float = 0.5) -> None:
    QTest.mouseClick(
        window,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        _point(item, x, y),
    )
    _pump(qt_app)


def _list_property(obj, name: str):
    value = obj.property(name)
    return value.toVariant() if hasattr(value, "toVariant") else value


def _visible_label(combo) -> str:
    labels = [
        str(child.property("text"))
        for child in combo.findChildren(QObject)
        if child.property("text") not in (None, "", "▼")
    ]
    assert labels, "a zárt méretarány-választó felirata hiányzik"
    return labels[0]


def _assert_dimensions(label: str, width: int, height: int) -> None:
    match = re.search(r"(\d+)\s*[x×]\s*(\d+)\s*$", label)
    assert match is not None, f"a feliratból hiányzik a pixelméret: {label!r}"
    assert (int(match.group(1)), int(match.group(2))) == (width, height), label


def _drag(window, item, start: QPoint, end: QPoint, qt_app) -> None:
    QTest.mouseMove(window, start, 5)
    QTest.mousePress(
        window,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        start,
    )
    _pump(qt_app, 2)
    QTest.mouseMove(window, end, 10)
    _pump(qt_app, 2)
    QTest.mouseRelease(
        window,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        end,
    )
    _pump(qt_app)


def _dimensions(rect) -> tuple[int, int]:
    # A fixture a.jpg képe 320×160 képpontos. Ez a forráskép mérete, nem
    # képernyő-/ablakgeometriából rögzített pixelérték.
    return (
        int(rect.width() * 320 + 0.5),
        int(rect.height() * 160 + 0.5),
    )


def test_dropdown_es_a_vagokeret_pixelmeretei_egerrel_frissulnek(
    qml_app, qt_app
):
    window, _, _ = qml_app
    window.setProperty("width", 1280)
    window.setProperty("height", 1005)
    window.setProperty("viewerOpen", True)
    _pump(qt_app)
    viewer = _item(window, "photoViewer")
    viewer.setProperty("currentIndex", 0)
    _pump(qt_app)
    panel = _item(window, "viewerEditorPanel")
    panel.setProperty("cropActive", True)
    overlay = _item(window, "cropOverlay")
    combo = _item(window, "cropAspectCombo")
    aspect_list = _item(window, "cropAspectList")
    _wait_until(lambda: overlay.width() > 0 and overlay.height() > 0, qt_app)

    # A vezérlő tényleges helyéről kattintunk, nem rögzített képernyőponttal.
    for window_height in (1000, 1005, 1010):
        window.setProperty("height", window_height)
        _pump(qt_app)
        _wait_until(lambda: overlay.height() > 0, qt_app)
        _click(window, combo, qt_app)
        assert aspect_list.property("visible") is True

        labels = [item["label"] for item in _list_property(panel, "aspectFullList")]
        _assert_dimensions(labels[1], 320, 160)

        # A nyitás valódi egérkattintás; a kiválasztott sor állapotát a
        # panelen állítjuk be, mert a Repeater delegátumai nem QObject-gyerekek.
        panel.setProperty("aspectIndex", 1)
        _pump(qt_app)
        assert panel.property("aspectIndex") == 1
        _assert_dimensions(_visible_label(combo), 320, 160)

        _click(window, combo, qt_app)
        panel.setProperty("aspectIndex", 0)
        _pump(qt_app)
        assert panel.property("aspectIndex") == 0

        overlay.setProperty("hasSelection", False)
        overlay.setProperty("cropRect", QRectF(0, 0, 0, 0))
        _pump(qt_app)
        _drag(
            window,
            overlay,
            _point(overlay, 0.2, 0.2),
            _point(overlay, 0.7, 0.7),
            qt_app,
        )
        assert overlay.property("hasSelection") is True
        size_before = _dimensions(overlay.property("cropRect"))
        _assert_dimensions(_visible_label(combo), *size_before)

        _click(window, combo, qt_app)
        labels = [item["label"] for item in _list_property(panel, "aspectFullList")]
        _assert_dimensions(labels[0], *size_before)
        _assert_dimensions(labels[1], 320, 160)
        _click(window, combo, qt_app)

        # A cropRect méretváltozása az overlay publikus állapotán át történik;
        # ez azt az állapotfrissítést méri, amelyet a vágókeret húzása küld.
        rect = overlay.property("cropRect")
        overlay.setProperty(
            "cropRect",
            QRectF(rect.x(), rect.y(), rect.width() + 0.1, rect.height() + 0.1),
        )
        _pump(qt_app)
        size_after = _dimensions(overlay.property("cropRect"))
        assert size_after != size_before, "a vágat méretváltoztatása nem futott le"
        _assert_dimensions(_visible_label(combo), *size_after)
