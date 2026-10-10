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


def _item_scene_bounds(item):
    top_left = item.mapToScene(QPointF(0, 0))
    bottom_right = item.mapToScene(
        QPointF(item.property("width"), item.property("height"))
    )
    return (
        float(top_left.x()),
        float(top_left.y()),
        float(bottom_right.x()),
        float(bottom_right.y()),
    )


@pytest.mark.parametrize("height_delta", (-5, 0, 5), ids=("minus5", "normal", "plus5"))
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
                and int(dialog.property("previewDisplayedGeneration"))
                    >= int(dialog.property("previewLatestRequestGeneration"))
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
        initial_source = str(image.property("source"))
        assert QMetaObject.invokeMethod(dialog, "requestPreviewFrame")
        assert _wait(
            qt_app,
            lambda: str(image.property("source")) != initial_source
            and int(dialog.property("previewDisplayedGeneration"))
                >= int(dialog.property("previewLatestRequestGeneration"))
            and image.property("visible")
            and float(image.property("paintedWidth")) > 0,
        )
        before = _item_scene_bounds(image)

        _select_transition(window, qt_app, "wipeleft")
        dialog.setProperty("previewFromIndex", 0)
        dialog.setProperty("previewIndex", 1)
        dialog.setProperty("previewTransitionProgress", 0.02)
        previous_source = str(image.property("source"))
        assert QMetaObject.invokeMethod(dialog, "requestPreviewFrame")
        assert _wait(
            qt_app,
            lambda: str(image.property("source")) != previous_source
            and int(dialog.property("previewDisplayedGeneration"))
                >= int(dialog.property("previewLatestRequestGeneration"))
            and float(image.property("paintedWidth")) > 0,
        )
        during = _item_scene_bounds(image)

        dialog.setProperty("previewTransitionProgress", 1.0)
        previous_source = str(image.property("source"))
        assert QMetaObject.invokeMethod(dialog, "requestPreviewFrame")
        assert _wait(
            qt_app,
            lambda: str(image.property("source")) != previous_source
            and int(dialog.property("previewDisplayedGeneration"))
                >= int(dialog.property("previewLatestRequestGeneration"))
            and float(image.property("paintedWidth")) > 0,
        )
        after = _item_scene_bounds(image)

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


def test_a_nezoke_indexelesekor_a_kovetkezo_fotokocka_elore_cachelodik(
    qml_app, qt_app, tmp_path
):
    window, controller, _engine = qml_app
    current_path = tmp_path / "aktualis.png"
    next_path = tmp_path / "kovetkezo.png"
    _make_pattern(current_path, incoming=False)
    _make_pattern(next_path, incoming=True)
    sources = [
        QUrl.fromLocalFile(str(current_path)).toString(),
        QUrl.fromLocalFile(str(next_path)).toString(),
    ]
    dialog = _open_movie_dialog(window, qt_app, 800)
    try:
        dialog.setProperty("movieClipSources", sources)
        dialog.setProperty("previewFromIndex", -1)
        dialog.setProperty("previewIndex", 0)
        assert QMetaObject.invokeMethod(dialog, "requestPreviewFrame")
        provider = controller.movie_transition_preview_provider
        assert _wait(
            qt_app,
            lambda: any(
                key[0] == "photo" and key[1] == str(next_path)
                for key in provider._frames
            ),
        ), "a preview nem töltötte elő a következő dia alapképkockáját"
    finally:
        dialog.close()
        qt_app.processEvents()


@pytest.mark.parametrize("height_delta", (-5, 0, 5), ids=("minus5", "normal", "plus5"))
def test_az_1_1_es_a_kattintott_diaszerkesztes_a_nezoket_frissiti(
    qml_app, qt_app, tmp_path, height_delta
):
    window, _controller, _engine = qml_app
    photo_path = tmp_path / "meret.png"
    _make_pattern(photo_path, incoming=False)
    source = QUrl.fromLocalFile(str(photo_path)).toString()
    dialog = _open_movie_dialog(window, qt_app, 800 + height_delta)
    try:
        dialog.setProperty("movieClipSources", [source])
        _elem(window, "movieHeightBox").setProperty("currentIndex", 6)
        image = _elem(window, "moviePreviewTransitionImage")
        one_to_one = _elem(window, "video_control_bar2/1to1")
        assert one_to_one.property("visible")
        _click(window, qt_app, one_to_one)
        assert _wait(
            qt_app,
            lambda: image.property("sourceSize").width() == 1920
            and image.property("sourceSize").height() == 1080
            and float(image.property("paintedWidth")) > 0
            and int(dialog.property("previewDisplayedGeneration"))
                >= int(dialog.property("previewLatestRequestGeneration")),
        ), "az 1:1 gomb nem a film 1920×1080 képkockáját mutatta"
        dpr = float(window.devicePixelRatio())
        assert abs(
            float(image.property("width"))
            - float(image.property("sourceSize").width()) / dpr
        ) <= 2, "az 1:1 szélesség nem a forrásméret/DPR szerint állt be"
        assert abs(
            float(image.property("height"))
            - float(image.property("sourceSize").height()) / dpr
        ) <= 2, "az 1:1 magasság nem a forrásméret/DPR szerint állt be"

        dialog.setProperty("movieClipSources", [])
        _click(window, qt_app, _elem(window, "movieTabSlide"))
        _click(window, qt_app, _elem(window, "movieInsertSlideButton"))
        title_dialog = _elem(window, "movieTitleDialog")
        assert _wait(qt_app, lambda: title_dialog.property("visible"))
        _elem(window, "titledialog/captiontext").setProperty(
            "text", "4820 eredeti dia"
        )
        qt_app.processEvents()
        _click(window, qt_app, _elem(window, "titledialog/add"))
        assert _wait(qt_app, lambda: not title_dialog.property("visible"))

        slide_list = _elem(window, "movieSlideList")
        assert _wait(qt_app, lambda: int(slide_list.property("count")) == 1), (
            "a szöveges dia nem jelent meg a dia listájában"
        )
        row_height = float(slide_list.property("contentHeight"))
        click_y = row_height / 2 - float(slide_list.property("contentY"))
        assert 0 <= click_y < float(slide_list.property("height"))
        point = slide_list.mapToScene(
            QPointF(float(slide_list.property("width")) / 2, click_y)
        ).toPoint()
        QTest.mouseClick(
            slide_list.window(), Qt.MouseButton.LeftButton, pos=point
        )
        qt_app.processEvents()
        image = _elem(window, "moviePreviewTransitionImage")
        assert _wait(
            qt_app,
            lambda: image.property("visible")
            and int(dialog.property("previewDisplayedGeneration"))
                >= int(dialog.property("previewLatestRequestGeneration"))
            and float(image.property("paintedWidth")) > 0,
        ), (
            "a kezdő szöveges dia nem jelent meg: "
            f"items={dialog.property('previewItemCount')}, "
            f"slides={dialog.property('movieSlides')!r}, "
            f"source={image.property('source')!r}, "
            f"frame={dialog.property('previewTransitionFrameSource')!r}, "
            f"generations={dialog.property('previewDisplayedGeneration')}/"
            f"{dialog.property('previewLatestRequestGeneration')} "
            f"(floor={dialog.property('previewGenerationFloor')})"
        )

        field = _elem(window, "movieSlideText")
        assert field.property("visible")
        point = field.mapToScene(
            QPointF(field.property("width") / 2, field.property("height") / 2)
        ).toPoint()
        source_before_edit = str(image.property("source"))
        QTest.mouseClick(field.window(), Qt.MouseButton.LeftButton, pos=point)
        assert _wait(qt_app, lambda: field.property("activeFocus")), (
            "a dia szövegmezője nem kapott fókuszt kattintásra"
        )
        QTest.keyClick(field.window(), Qt.Key.Key_A, Qt.KeyboardModifier.ControlModifier)
        for character in "frissitett 4820 dia":
            key = (
                Qt.Key.Key_Space
                if character == " "
                else Qt.Key(ord(character.upper() if character.isalpha() else character))
            )
            QTest.keyClick(field.window(), key)
        qt_app.processEvents()
        assert field.property("text") == "frissitett 4820 dia", (
            f"a begépelt szöveg nem került a mezőbe: {field.property('text')!r}"
        )
        assert _wait(
            qt_app,
            lambda: str(image.property("source")) != source_before_edit
                and int(dialog.property("previewDisplayedGeneration"))
                    >= int(dialog.property("previewLatestRequestGeneration"))
                and str(field.property("text")) == "frissitett 4820 dia",
            ), (
                "a kattintással szerkesztett dia nem frissült: "
                f"mező={field.property('text')!r}, "
                f"frame={image.property('source')!r}, "
                f"preview={dialog.property('previewTransitionFrameSource')!r}, "
                f"generations={dialog.property('previewDisplayedGeneration')}/"
                f"{dialog.property('previewLatestRequestGeneration')} "
                f"(floor={dialog.property('previewGenerationFloor')})"
            )

        _click(window, qt_app, _elem(window, "movieRemoveSlideButton"))
        assert _wait(
            qt_app,
            lambda: dialog.property("previewItemCount") == 0
            and dialog.property("previewTransitionFrameSource") == ""
            and image.property("visible") is False,
        ), (
            "az utolsó dia törlése után a régi előnézeti kép kint maradt: "
            f"items={dialog.property('previewItemCount')}, "
            f"source={dialog.property('previewTransitionFrameSource')!r}, "
            f"visible={image.property('visible')!r}, "
            f"generations={dialog.property('previewDisplayedGeneration')}/"
            f"{dialog.property('previewLatestRequestGeneration')} "
            f"(floor={dialog.property('previewGenerationFloor')})"
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


def test_a_futo_elonezet_megallitas_nelkul_tobb_keveredo_kockat_mutat(
    qml_app, qt_app, tmp_path
):
    window, controller, _engine = qml_app
    sources = []
    for name, color in (("piros.png", Qt.GlobalColor.red), ("kek.png", Qt.GlobalColor.blue)):
        image = QImage(320, 240, QImage.Format.Format_RGB32)
        image.fill(color)
        assert image.save(str(tmp_path / name))
        sources.append(QUrl.fromLocalFile(str(tmp_path / name)).toString())
    dialog = _open_movie_dialog(window, qt_app, 800)
    provider = controller.movie_transition_preview_provider
    shown: list[bool] = []

    def collect(_source, _generation):
        with provider._image_lock:
            frame = provider._image.copy()
        mixed = any(
            35 < frame.pixelColor(x, y).red() < 220
            and 35 < frame.pixelColor(x, y).blue() < 220
            for x in range(0, frame.width(), max(1, frame.width() // 8))
            for y in range(0, frame.height(), max(1, frame.height() // 8))
        )
        shown.append(mixed)

    try:
        dialog.setProperty("movieClipSources", sources)
        dialog.setProperty("previewSource", sources[0])
        _elem(window, "movieSeconds").setProperty("value", 20)
        _elem(window, "movieOverlapSlider").setProperty("value", 0.4)
        _select_transition(window, qt_app, "dissolve")
        qt_app.processEvents()
        controller.movieTransitionPreviewReady.connect(collect)
        _click(window, qt_app, _elem(window, "moviePreviewButton"))
        transition = _elem(window, "moviePreviewTransition")
        assert _wait(qt_app, lambda: transition.property("running"), timeout=3.0), (
            "az átmenet nem indult el"
        )
        assert _wait(qt_app, lambda: not transition.property("running"), timeout=5.0), (
            "az átmenet nem fejeződött be"
        )
        assert len(shown) >= 3, f"futás közben csak {len(shown)} kocka jelent meg"
        assert any(shown), "egyik futás közbeni kockán sem volt keveredő képpont"
    finally:
        try:
            controller.movieTransitionPreviewReady.disconnect(collect)
        except (RuntimeError, TypeError):
            pass
        dialog.close()
        qt_app.processEvents()
