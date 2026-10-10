"""A filmelőnézet mind a 22 átmenetet a renderelő geometriájával rajzolja (#4820)."""

from __future__ import annotations

import time
import re
from pathlib import Path

import numpy as np
import pytest
from PySide6.QtCore import QMetaObject, QObject, QPointF, Qt, QUrl
from PySide6.QtGui import QImage
from PySide6.QtQml import QQmlExpression, qmlContext
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
_DISSOLVE_VAGY_VAGAS = {"cut", "dissolve", "timelapse"}
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


def _click(window, qt_app, item, x_ratio=0.5):
    assert item.property("visible"), f"{item.objectName()} nem látható"
    point = item.mapToScene(
        QPointF(item.property("width") * x_ratio, item.property("height") / 2)
    ).toPoint()
    QTest.mouseClick(item.window() or window, Qt.MouseButton.LeftButton, pos=point)
    qt_app.processEvents()


def _select_transition(window, qt_app, transition):
    combo = _elem(window, "movieTransitionBox")
    index = _ATMENETEK.index(transition)
    _click(window, qt_app, combo, x_ratio=0.9)
    popup = combo.findChild(QObject, "picasaComboPopup")
    assert popup is not None, "az átmenetlista popupja nem található"
    assert _wait(qt_app, lambda: popup.property("visible")), (
        "az átmenetlista nem nyílt le"
    )
    rows = combo.findChild(QObject, "picasaComboList")
    assert rows is not None, "az átmenetlista nézete nem található"
    assert _wait(qt_app, lambda: int(rows.property("count")) == len(_ATMENETEK))
    row_height = float(rows.property("contentHeight")) / len(_ATMENETEK)
    list_height = float(rows.property("height"))
    assert row_height > 0 and list_height > row_height, (
        f"a legördülő lista mérete érvénytelen: "
        f"{row_height=} {list_height=}"
    )
    content_y = max(
        0.0,
        min(
            (index + 0.5) * row_height - list_height / 2,
            float(rows.property("contentHeight")) - list_height,
        ),
    )
    rows.setProperty("contentY", content_y)
    assert _wait(qt_app, lambda: abs(float(rows.property("contentY")) - content_y) <= 1)
    y_in_view = (index + 0.5) * row_height - float(rows.property("contentY"))
    assert 0 <= y_in_view < list_height, (
        f"a(z) {transition} sor nem látható a legördülő nézetben"
    )
    expression = QQmlExpression(
        qmlContext(rows), rows, f"itemAtIndex({index})"
    )

    def visible_row():
        value, error = expression.evaluate()
        assert not error, expression.error()
        return value.toVariant() if hasattr(value, "toVariant") else value

    assert _wait(qt_app, lambda: visible_row() is not None), (
        f"a(z) {transition} sor nem jelent meg"
    )
    row = visible_row()
    point = row.mapToScene(QPointF(row.width() / 2, row.height() / 2)).toPoint()
    QTest.mouseClick(window, Qt.MouseButton.LeftButton, pos=point)
    qt_app.processEvents()
    assert _wait(qt_app, lambda: combo.property("currentIndex") == index), (
        f"a kattintás nem választotta ki a(z) {transition} átmenetet"
    )


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


def _screenshot_content_bounds(window, screenshot, viewport):
    origin = viewport.mapToScene(QPointF(0, 0))
    scale_x = screenshot.width() / float(window.width())
    scale_y = screenshot.height() / float(window.height())
    rectangle = (
        round(origin.x() * scale_x),
        round(origin.y() * scale_y),
        max(1, round(float(viewport.property("width")) * scale_x)),
        max(1, round(float(viewport.property("height")) * scale_y)),
    )
    crop = _qimage_rgb_array(screenshot.copy(*rectangle))
    # A tesztképek színesek, a panel/vászonszegély szürke vagy fekete. Csak a
    # színes, szöveg nélküli képterületet mérjük, betűpixelt nem.
    colored = np.ptp(crop.astype(np.int16), axis=2) > 30
    ys, xs = np.where(colored)
    assert len(xs), "a nézőke képtartalma nem látszik a renderelt ablakon"
    return (int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1)


def test_a_renderelt_elonezet_a_slideshow_atmeneti_kockajat_mutatja(
    qml_app, qt_app, tmp_path
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
    dialog = _open_movie_dialog(window, qt_app, 800)
    try:
        dialog.setProperty("movieClipSources", sources)
        dialog.setProperty("previewIndex", 0)
        dialog.setProperty("previewSource", sources[0])
        _elem(window, "movieHeightBox").setProperty("currentIndex", 1)
        qt_app.processEvents()

        transition = _elem(window, "moviePreviewTransition")
        rendered_image = _elem(window, "moviePreviewTransitionImage")
        initial_source = str(rendered_image.property("source"))
        assert QMetaObject.invokeMethod(dialog, "requestPreviewFrame")
        assert _wait(
            qt_app,
            lambda: str(rendered_image.property("source")) != initial_source
            and float(rendered_image.property("paintedWidth")) > 0,
        ), "a kezdő, a slideshow geometriájú képkocka nem készült el"
        measured_errors = {}
        for key in _ATMENETEK:
            _select_transition(window, qt_app, key)
            previous_source = str(rendered_image.property("source"))
            dialog.setProperty("previewIndex", 0)
            dialog.setProperty("previewSource", sources[0])
            transition.stop()
            dialog.setProperty("previewFromIndex", 0)
            dialog.setProperty("previewIndex", 1)
            dialog.setProperty("previewTransitionProgress", 0.5)
            assert QMetaObject.invokeMethod(dialog, "requestPreviewFrame")
            qt_app.processEvents()
            assert _wait(
                qt_app,
                lambda previous_source=previous_source: rendered_image.property("visible")
                and str(rendered_image.property("source")) != previous_source
                and float(rendered_image.property("paintedWidth")) > 0,
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
            if key not in _DISSOLVE_VAGY_VAGAS:
                dissolve_reference = _movie_reference(
                    outgoing_path,
                    incoming_path,
                    "dissolve",
                    0.5,
                    (expected.shape[1], expected.shape[0]),
                ).astype(np.int16)
                dissolve_error = float(
                    np.abs(expected - dissolve_reference).mean()
                )
                assert dissolve_error > 2.0, (
                    f"{key}: a slideshow definíciója szerint különbözik a sima "
                    "áttűnéstől, az előnézeti képkocka mégis annak felel meg"
                )
            transition.stop()

        print(
            f"ablakmagasság={window.height()}, félidős átmeneti MAE: "
            + ", ".join(f"{key}={value:.2f}" for key, value in measured_errors.items())
        )
    finally:
        dialog.close()
        qt_app.processEvents()


@pytest.mark.parametrize("height_delta", (-5, 0, 5), ids=("minus5", "normal", "plus5"))
def test_a_kezdo_atmeneti_es_vegkep_nezoke_geometriaja_egyezik(
    qml_app, qt_app, tmp_path, height_delta
):
    window, _controller, _engine = qml_app
    outgoing_path = tmp_path / "kilepo.jpg"
    incoming_path = tmp_path / "erkezo.jpg"
    _make_pattern(outgoing_path, incoming=False)
    _make_pattern(incoming_path, incoming=True)
    sources = [
        QUrl.fromLocalFile(str(outgoing_path)).toString(),
        QUrl.fromLocalFile(str(incoming_path)).toString(),
    ]
    dialog = _open_movie_dialog(window, qt_app, 800 + height_delta)
    try:
        dialog.setProperty("movieClipSources", sources)
        dialog.setProperty("previewSource", sources[0])
        _elem(window, "movieHeightBox").setProperty("currentIndex", 5)
        _elem(window, "video_control_bar2/1to1").setProperty("checked", True)
        dialog.setProperty("previewActualSizeEnabled", True)
        dialog.setProperty("previewFromIndex", -1)
        dialog.setProperty("previewIndex", 0)
        assert QMetaObject.invokeMethod(dialog, "requestPreviewFrame")
        qt_app.processEvents()
        image = _elem(window, "moviePreviewTransitionImage")
        viewport = _elem(window, "moviePreviewViewport")
        initial_source = str(image.property("source"))
        assert QMetaObject.invokeMethod(dialog, "requestPreviewFrame")
        assert _wait(
            qt_app,
            lambda: str(image.property("source")) != initial_source
            and image.property("visible")
            and float(image.property("paintedWidth")) > 0,
        )
        before = _screenshot_content_bounds(window, window.grabWindow(), viewport)

        _select_transition(window, qt_app, "wipeleft")
        dialog.setProperty("previewFromIndex", 0)
        dialog.setProperty("previewIndex", 1)
        dialog.setProperty("previewTransitionProgress", 0.02)
        previous_source = str(image.property("source"))
        assert QMetaObject.invokeMethod(dialog, "requestPreviewFrame")
        assert _wait(
            qt_app,
            lambda: str(image.property("source")) != previous_source
            and float(image.property("paintedWidth")) > 0,
        )
        during = _screenshot_content_bounds(window, window.grabWindow(), viewport)

        dialog.setProperty("previewTransitionProgress", 1.0)
        previous_source = str(image.property("source"))
        assert QMetaObject.invokeMethod(dialog, "requestPreviewFrame")
        assert _wait(
            qt_app,
            lambda: str(image.property("source")) != previous_source
            and float(image.property("paintedWidth")) > 0,
        )
        after = _screenshot_content_bounds(window, window.grabWindow(), viewport)

        for phase, bounds in (("0,02", during), ("utána", after)):
            assert all(
                abs(a - b) <= 3 for a, b in zip(before, bounds, strict=True)
            ), (
                f"{phase}: a képtéglalap elmozdult; előtte={before}, "
                f"{phase}={bounds}, ablakmagasság={window.height()}"
            )
    finally:
        dialog.close()
        qt_app.processEvents()


def test_a_szovegdia_vagasa_felirata_es_datuma_is_a_kozos_kockaba_kerul(
    qml_app, qt_app, tmp_path
):
    window, controller, _engine = qml_app
    photo_path = tmp_path / "filmkep.png"
    _make_pattern(photo_path, incoming=False)
    (tmp_path / ".picasa.ini").write_text(
        "[filmkep.png]\ncaption=4820 tesztfelirat\n", encoding="utf-8"
    )
    source = QUrl.fromLocalFile(str(photo_path)).toString()
    dialog = _open_movie_dialog(window, qt_app, 800)
    try:
        dialog.setProperty("movieClipSources", [source])
        dialog.setProperty("movieSlides", [{
            "text": "4820 szöveges dia",
            "style": 4,
            "backgroundColor": "#304050",
            "textColor": "#ffffff",
            "size": 24,
        }])
        _elem(window, "movieCropToFit").setProperty("checked", True)
        _elem(window, "movieShowCaptions").setProperty("checked", True)
        _elem(window, "movieShowDates").setProperty("checked", True)
        _select_transition(window, qt_app, "wipeleft")
        dialog.setProperty("previewIndex", 0)
        dialog.setProperty("previewFromIndex", 0)
        dialog.setProperty("previewIndex", 1)
        dialog.setProperty("previewTransitionProgress", 0.5)
        previous_source = str(_elem(window, "moviePreviewTransitionImage").property("source"))
        assert QMetaObject.invokeMethod(dialog, "requestPreviewFrame")
        qt_app.processEvents()

        rendered_image = _elem(window, "moviePreviewTransitionImage")
        incoming = _elem(window, "moviePreviewIncomingFrame")
        assert _wait(
            qt_app,
            lambda: rendered_image.property("visible")
            and str(rendered_image.property("source")) != previous_source
            and rendered_image.property("paintedWidth") > 0,
        ), "a szöveges diás átmenet képkockája nem készült el"
        assert incoming.property("isTextSlide") is True
        assert incoming.property("displayText") == "4820 szöveges dia"

        cached_photo = next(
            frame
            for key, frame in controller.movie_transition_preview_provider._frames.items()
            if key[0] == "photo" and key[1] == str(photo_path)
        )
        assert cached_photo.shape[0] > 0 and cached_photo.shape[1] > 0
        assert cached_photo[-1, 0].mean() < 180, (
            "a felirat/dátum alatti, szöveg nélküli képpont nem sötétült el"
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
