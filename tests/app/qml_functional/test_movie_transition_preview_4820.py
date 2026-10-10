"""A filmelőnézet mind a 22 átmenetet a renderelő geometriájával rajzolja (#4820)."""

from __future__ import annotations

import time
import re
from pathlib import Path

import numpy as np
import pytest
from PySide6.QtCore import QMetaObject, QObject, QPointF, Qt, QUrl
from PySide6.QtGui import QImage
from PySide6.QtTest import QTest

from picasapy.lazy_cv2 import cv2
from picasapy.movie.slideshow import (
    _TRANSITION_TYPES,
    _atmeneti_kocka,
    letterbox,
)


_ATMENETEK = (
    "cut", "dissolve", "dissolveblack", "dissolvewhite",
    "wipeleft", "wiperight", "wipeup", "wipedown",
    "diagwipeul", "diagwipeur", "diagwipedl", "diagwipedr",
    "pushleft", "pushright", "pushtop", "pushdown",
    "circlein", "circleout", "kenburns", "kenburnsaoi",
    "timelapse", "rect",
)
_MERENDO_ATMENETEK = ("wipeleft", "pushleft", "circlein", "kenburns")


def _elem(window, name):
    element = window.findChild(QObject, name)
    assert element is not None, f"{name} nem található"
    return element


def _wait(qt_app, condition, timeout=3.0):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        qt_app.processEvents()
        if condition():
            return True
        QTest.qWait(50)
    qt_app.processEvents()
    return bool(condition())


def _click(window, qt_app, item):
    assert item.property("visible"), f"{item.objectName()} nem látható"
    point = item.mapToScene(
        QPointF(item.property("width") / 2, item.property("height") / 2)
    ).toPoint()
    QTest.mouseClick(item.window() or window, Qt.MouseButton.LeftButton, pos=point)
    qt_app.processEvents()


def _open_movie_dialog(window, qt_app, height):
    window.resize(1280, height)
    window.setProperty("selectedIndexes", [0, 1])
    window.setProperty("selectedIndex", 0)
    qt_app.processEvents()
    _click(window, qt_app, _elem(window, "trayMovieButton"))
    dialog = _elem(window, "movieDialog")
    assert _wait(qt_app, lambda: dialog.property("visible"))
    return dialog


def _make_pattern(path: Path, incoming: bool) -> np.ndarray:
    height, width = 240, 320
    y, x = np.mgrid[0:height, 0:width]
    rgb = np.empty((height, width, 3), dtype=np.uint8)
    if incoming:
        rgb[..., 0] = 30 + x * 190 // width
        rgb[..., 1] = 20 + y * 210 // height
        rgb[..., 2] = 245 - x * 180 // width
    else:
        rgb[..., 0] = 245 - y * 180 // height
        rgb[..., 1] = 20 + x * 200 // width
        rgb[..., 2] = 30 + y * 210 // height
    image = QImage(
        rgb.data, width, height, rgb.strides[0], QImage.Format.Format_RGB888
    ).copy()
    assert image.save(str(path)), f"nem sikerült a tesztképet írni: {path}"
    return rgb


def _qimage_rgb_array(image: QImage) -> np.ndarray:
    rgb = image.convertToFormat(QImage.Format.Format_RGB888)
    bits = rgb.bits()
    rows = np.frombuffer(bits, dtype=np.uint8).reshape(
        rgb.height(), rgb.bytesPerLine()
    )
    return rows[:, : rgb.width() * 3].reshape(rgb.height(), rgb.width(), 3).copy()


def _painted_image_crop(window, screenshot, item):
    item_width = float(item.property("width"))
    item_height = float(item.property("height"))
    painted_width = float(item.property("paintedWidth"))
    painted_height = float(item.property("paintedHeight"))
    origin = item.mapToScene(QPointF(0, 0))
    x = float(origin.x()) + (item_width - painted_width) / 2
    y = float(origin.y()) + (item_height - painted_height) / 2
    scale_x = screenshot.width() / float(window.width())
    scale_y = screenshot.height() / float(window.height())
    rectangle = (
        round(x * scale_x),
        round(y * scale_y),
        max(1, round(painted_width * scale_x)),
        max(1, round(painted_height * scale_y)),
    )
    return screenshot.copy(*rectangle)


def _movie_reference(outgoing_path, incoming_path, transition, progress, size):
    width, height = size
    outgoing = cv2.imread(str(outgoing_path), cv2.IMREAD_COLOR)
    incoming = cv2.imread(str(incoming_path), cv2.IMREAD_COLOR)
    assert outgoing is not None and incoming is not None
    outgoing = letterbox(outgoing, width, height)
    incoming = letterbox(incoming, width, height)
    frame = _atmeneti_kocka(outgoing, incoming, transition, progress)
    return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)


def test_a_renderelt_elonezet_a_slideshow_atmeneti_kockajat_mutatja(
    qml_app, qt_app, tmp_path, height_delta
):
    window, _controller, _engine = qml_app
    outgoing_path = tmp_path / "kilepo.png"
    incoming_path = tmp_path / "erkezo.png"
    _make_pattern(outgoing_path, incoming=False)
    _make_pattern(incoming_path, incoming=True)
    sources = [
        QUrl.fromLocalFile(str(outgoing_path)).toString(),
        QUrl.fromLocalFile(str(incoming_path)).toString(),
    ]
    dialog = _open_movie_dialog(window, qt_app, 800 + height_delta)
    try:
        dialog.setProperty("movieClipSources", sources)
        dialog.setProperty("previewIndex", 0)
        dialog.setProperty("previewSource", sources[0])
        _elem(window, "movieHeightBox").setProperty("currentIndex", 1)
        qt_app.processEvents()

        transition = _elem(window, "moviePreviewTransition")
        incoming_frame = _elem(window, "moviePreviewIncomingFrame")
        rendered_image = window.findChild(QObject, "moviePreviewTransitionImage")
        if rendered_image is None:
            rendered_image = _elem(window, "moviePreviewImage")
        assert _wait(
            qt_app, lambda: incoming_frame.property("imageSourceWidth") > 0
        )
        measured_errors = {}
        for key in _MERENDO_ATMENETEK:
            dialog.setProperty("transitionIndex", _ATMENETEK.index(key))
            dialog.setProperty("previewIndex", 0)
            dialog.setProperty("previewSource", sources[0])
            dialog.setProperty("previewFromIndex", -1)
            transition.stop()
            qt_app.processEvents()
            assert QMetaObject.invokeMethod(dialog, "advancePreview")
            transition.setProperty("paused", True)
            dialog.setProperty("previewTransitionProgress", 0.5)
            qt_app.processEvents()
            assert _wait(
                qt_app,
                lambda: (
                    float(rendered_image.property("paintedWidth")) > 0
                    if rendered_image.objectName() == "moviePreviewTransitionImage"
                    else incoming_frame.property("imageSourceWidth") > 0
                ),
            )

            screenshot = window.grabWindow()
            assert not screenshot.isNull(), "az előnézeti ablak képe nem készült el"
            actual = _qimage_rgb_array(
                _painted_image_crop(window, screenshot, rendered_image)
            ).astype(np.int16)
            expected = _movie_reference(
                outgoing_path, incoming_path, key, 0.5, (640, 480)
            )
            expected_image = QImage(
                expected.data,
                expected.shape[1],
                expected.shape[0],
                expected.strides[0],
                QImage.Format.Format_RGB888,
            ).copy()
            expected = _qimage_rgb_array(
                expected_image.scaled(
                    actual.shape[1],
                    actual.shape[0],
                    Qt.AspectRatioMode.IgnoreAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            ).astype(np.int16)
            error = float(np.abs(actual - expected).mean())
            measured_errors[key] = error
            assert error <= 10.0, (
                f"{key}: az előnézet és a slideshow félidős képkockája eltér; "
                f"mért átlagos RGB-hiba={error:.2f}/255"
            )
            transition.stop()

        print(
            f"ablakmagasság={window.height()}, félidős átmeneti MAE: "
            + ", ".join(f"{key}={value:.2f}" for key, value in measured_errors.items())
        )
    finally:
        dialog.close()
        qt_app.processEvents()


def test_a_film_es_a_renderelo_atmenetkulcskeszlete_megegyezik():
    qml = (
        Path(__file__).parents[3]
        / "src/picasapy/app/qml/PicasaPy/CreateDialogs.qml"
    ).read_text(encoding="utf-8")
    match = re.search(
        r"readonly property var transitionKeys:\s*\[(.*?)\]", qml, re.DOTALL
    )
    assert match is not None, "a QML filmátmenet-lista nem található"
    qml_keys = set(re.findall(r'"([a-z]+)"', match.group(1)))
    assert qml_keys == _TRANSITION_TYPES


@pytest.fixture(params=(-5, 0, 5), ids=("minus5", "normal", "plus5"))
def height_delta(request):
    return request.param
