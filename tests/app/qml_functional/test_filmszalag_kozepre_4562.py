"""#4562: a filmstrip seven fixed cells wide and keeps the selected photo centered."""

from __future__ import annotations

import math
import time
from pathlib import Path

from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QImage
from PySide6.QtQuick import QQuickItem
from PySide6.QtTest import QTest

from support.jpeg_factory import make_jpeg


_FILMSTRIP_WIDTH = 214  # 7 * 28 px thumbnails + 6 * 3 px gaps.
_THUMB_SIZE = 28
_SLOT_PITCH = 31
_OUTER_FRAME = (0, 158, 255)
_INNER_FRAME = (212, 212, 212)


def _walk(item: QQuickItem):
    for child in item.childItems():
        yield child
        yield from _walk(child)


def _elem(window, name: str):
    for item in _walk(window.contentItem()):
        if item.objectName() == name:
            return item
    return window.findChild(QQuickItem, name)


def _var(qt_app, predicate, seconds: float = 5.0) -> bool:
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        try:
            if predicate():
                return True
        except (AttributeError, RuntimeError, TypeError):
            pass
        qt_app.processEvents()
        time.sleep(0.005)
    return False


def _folder_start(controller, folder_name: str) -> int:
    for row in range(controller.photos.rowCount()):
        if folder_name in controller.photos.filePathAt(row):
            return row
    return -1


def _delegate_for_row(filmstrip, row: int):
    for item in _walk(filmstrip):
        try:
            if item.property("racsSor") == row:
                return item
        except RuntimeError:
            continue
    return None


def _open_five_photo_folder(qml_app, qt_app):
    window, controller, _engine = qml_app
    folder_name = "filmszalag_4562"
    folder = Path(controller.watchedFolders[0]) / folder_name
    folder.mkdir(exist_ok=True)
    for index in range(5):
        make_jpeg(folder / f"photo-{index}.jpg", size=(60, 40))

    controller.rescan()
    assert _var(
        qt_app,
        lambda: _folder_start(controller, folder_name) >= 0
        and controller.photos.folderRowRange(
            _folder_start(controller, folder_name)
        )[1]
        == 5,
    ), "az ötképes próbamappa nem került be a modellbe"

    start = _folder_start(controller, folder_name)
    window.setProperty("selectedIndexes", [start])
    window.setProperty("selectedIndex", start)
    viewer = _elem(window, "photoViewer")
    assert viewer is not None
    viewer.setProperty("currentIndex", start)
    window.setProperty("viewerOpen", True)
    filmstrip = _elem(window, "viewerFilmstrip")
    assert filmstrip is not None
    assert _var(qt_app, lambda: filmstrip.property("mappaDarab") == 5)
    return window, controller, viewer, filmstrip, start


def _rgb(image: QImage, scene_point: QPointF) -> tuple[int, int, int]:
    ratio = image.devicePixelRatio()
    x = math.floor(scene_point.x() * ratio)
    y = math.floor(scene_point.y() * ratio)
    color = image.pixelColor(x, y)
    return color.red(), color.green(), color.blue()


class TestFilmszalag:
    def test_a_hossza_het_fix_ferohely(self, qml_app, qt_app):
        _window, _controller, _viewer, filmstrip, _start = _open_five_photo_folder(
            qml_app, qt_app
        )
        assert _var(qt_app, lambda: filmstrip.width() > 0)
        assert filmstrip.width() == _FILMSTRIP_WIDTH, (
            f"a filmszalag {filmstrip.width():g} px széles a rögzített "
            f"{_FILMSTRIP_WIDTH} px helyett"
        )

    def test_a_renderelt_kijeloles_merete_es_ketszinu_kerete(self, qml_app, qt_app):
        window, _controller, viewer, filmstrip, start = _open_five_photo_folder(
            qml_app, qt_app
        )
        viewer.setProperty("currentIndex", start + 2)
        assert _var(qt_app, lambda: filmstrip.property("currentIndex") == 5)

        frame = _elem(window, "viewerFilmstripCurrentFrame")
        assert frame is not None, "a kijelölt kép kétszínű kerete hiányzik"
        assert (frame.width(), frame.height()) == (_THUMB_SIZE, _THUMB_SIZE)
        frame_left = frame.mapToItem(filmstrip, QPointF(0, 0)).x()
        expected_left = (filmstrip.width() - frame.width()) / 2
        assert abs(frame_left - expected_left) <= 3, (
            f"a keret x={frame_left:.1f}, a filmszalag geometriája szerint "
            f"x={expected_left:.1f} (±3 px)"
        )

        rendered = window.grabWindow()
        assert not rendered.isNull(), "a nézőablak nem rajzolódott ki"

        outer_top = frame.mapToScene(QPointF(frame.width() / 2, 0.5))
        inner_top = frame.mapToScene(QPointF(frame.width() / 2, 1.5))
        center = frame.mapToScene(
            QPointF(frame.width() / 2, frame.height() / 2)
        )
        assert _rgb(rendered, outer_top) == _OUTER_FRAME, (
            "a renderelt külső keret nem a mért #009EFF"
        )
        assert _rgb(rendered, inner_top) == _INNER_FRAME, (
            "a renderelt belső keret nem a mért #D4D4D4"
        )
        frame_center = _rgb(rendered, center)

        # A kijelölés áthelyezése után ugyanaz a fotó keret nélkül látszik
        # egy férőhellyel balra. A két képpont egyezése bizonyítja, hogy a
        # renderelt keret közepe átlátszó maradt.
        viewer.setProperty("currentIndex", start + 3)
        assert _var(qt_app, lambda: filmstrip.property("currentIndex") == 6)
        assert _var(qt_app, lambda: frame.objectName() == "")
        thumbnail = next(
            (
                item
                for item in _walk(window.contentItem())
                if item.objectName() == "viewerFilmstripThumbnail"
                and item.parentItem().property("racsSor") == start + 2
            ),
            None,
        )
        assert thumbnail is not None, "a keret nélküli bélyegkép hiányzik"
        unselected_image = window.grabWindow()
        thumbnail_center = thumbnail.mapToScene(
            QPointF(thumbnail.width() / 2, thumbnail.height() / 2)
        )
        assert _rgb(unselected_image, thumbnail_center) == frame_center, (
            "a keret közepe takarja az alatta lévő bélyegképet"
        )

    def test_kattintott_leptetesnel_a_kijelolt_kep_kozepen_marad(
        self, qml_app, qt_app
    ):
        window, _controller, viewer, filmstrip, start = _open_five_photo_folder(
            qml_app, qt_app
        )
        original_height = window.height()
        next_button = _elem(window, "viewerNextButton")
        assert next_button is not None

        for height_delta in (-5, 0, 5):
            target_height = original_height + height_delta
            window.setHeight(target_height)
            assert _var(
                qt_app,
                lambda expected_height=target_height: window.height()
                == expected_height,
            )
            assert _var(qt_app, lambda: filmstrip.width() > 0)
            viewer.setProperty("currentIndex", start)
            assert _var(qt_app, lambda: filmstrip.property("currentIndex") >= 0)

            for step in range(5):
                current_item = _delegate_for_row(
                    filmstrip, viewer.property("currentIndex")
                )
                assert current_item is not None
                item_left = current_item.mapToItem(
                    filmstrip, QPointF(0, 0)
                ).x()
                expected_left = (filmstrip.width() - _SLOT_PITCH) / 2
                assert abs(item_left - expected_left) <= 3, (
                    f"{height_delta:+} px ablakmagasságnál, a {step}. képnél "
                    f"a kijelölt cella x={item_left:.1f}, a saját geometriája "
                    f"szerint x={expected_left:.1f} (±3 px)"
                )
                if step < 4:
                    point = next_button.mapToScene(
                        QPointF(next_button.width() / 2, next_button.height() / 2)
                    ).toPoint()
                    QTest.mouseClick(
                        window,
                        Qt.MouseButton.LeftButton,
                        Qt.KeyboardModifier.NoModifier,
                        point,
                    )
                    assert _var(
                        qt_app,
                        lambda expected=start + step + 1: viewer.property(
                            "currentIndex"
                        )
                        == expected,
                    ), "a léptetőgomb nem választotta ki a következő mappaképet"
