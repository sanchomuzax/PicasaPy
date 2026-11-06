"""A kijelölt fotó szürke háttérként frissül az Időrendben (#6577)."""

from pathlib import Path

import numpy as np
from PIL import Image
from PySide6.QtCore import QObject, QPointF, Qt
from PySide6.QtTest import QTest
import pytest

from tests.app.qml_functional.conftest import _build_qml_app
from support.varakozas import var_feltetelre


def _make_timeline_photos(root: Path) -> None:
    for folder_name, color in (
        ("PicasaTeszt", (90, 38, 220)),
        ("Recently Updated", (20, 205, 80)),
    ):
        folder = root / folder_name
        folder.mkdir()
        y, x = np.indices((240, 320))
        if folder_name == "PicasaTeszt":
            pattern = 255 - (x + y * 3) // 3
        else:
            pattern = (x + y * 3) // 3
        pixels = np.empty((240, 320, 3), dtype=np.uint8)
        for channel, base, scale in (
            (0, color[0], 0.30),
            (1, color[1], 0.72),
            (2, color[2], 0.35),
        ):
            pixels[:, :, channel] = np.clip(
                base - 36 + pattern * scale, 0, 255
            ).astype(np.uint8)
        image = Image.fromarray(pixels)
        for index in range(1, 5):
            image.save(
                folder / f"timeline-{index}.jpg", "JPEG", quality=95
            )


@pytest.fixture
def qml_app_timeline_background_6577(qt_app, tmp_path):
    yield from _build_qml_app(
        qt_app,
        tmp_path,
        kepeket_keszit=_make_timeline_photos,
        belyegkep_meret=256,
        valodi_belyegkep=True,
    )


def _child(parent, name):
    child = parent.findChild(QObject, name)
    assert child is not None, f"{name} nem található"
    return child


def _wait(qt_app, predicate, message):
    assert var_feltetelre(qt_app, predicate, 10.0), message


def _panel_pixel(timeline, panel, x, y):
    frame = timeline.grabWindow()
    point = panel.mapToItem(timeline.contentItem(), QPointF(x, y)).toPoint()
    return frame.pixelColor(point)


def test_rendered_background_tracks_the_selected_photo(
    qml_app_timeline_background_6577, qt_app, tmp_path
):
    window, _controller, engine = qml_app_timeline_background_6577
    window.setProperty("selectedIndexes", [])
    window.requestActivate()
    _wait(qt_app, window.isActive, "a főablak nem lett aktív")
    QTest.keyClick(window, Qt.Key.Key_5, Qt.KeyboardModifier.ControlModifier)
    _wait(
        qt_app,
        lambda: window.property("timelineOpen") is True,
        "a Ctrl+5 nem nyitotta meg az Időrendet",
    )
    timeline = _child(window, "timelineView")
    _wait(qt_app, timeline.isVisible, "az Időrend ablak nem látszik")
    timeline.requestActivate()
    _wait(qt_app, timeline.isActive, "az Időrend nem kapott fókuszt")
    timeline.setProperty("visibility", timeline.property("windowedVisibility"))
    timeline.resize(1280, 800)
    _wait(qt_app, lambda: timeline.width() == 1280, "az ablak szélessége nem állt be")
    _wait(qt_app, lambda: timeline.height() == 800, "az ablakmagasság nem állt be")

    timeline_controller = engine.rootContext().contextProperty("timelineController")
    collections = [dict(item) for item in timeline_controller.collections]
    assert len(collections) >= 2
    assert collections[0]["photos"] and collections[1]["photos"]
    collections[0]["sliderPosition"] = 0.0
    collections[1]["sliderPosition"] = 1.0
    timeline.setProperty("collectionsModel", collections)
    timeline.setProperty("currentIndex", 0)
    panel = _child(timeline, "timelinePanel")
    background_image = _child(timeline, "timelineBackgroundImage")
    previous_background_image = _child(
        timeline, "timelinePreviousBackgroundImage"
    )
    _wait(
        qt_app,
        lambda: background_image.property("source").toString().startswith(
            "image://timelinebackground/"
        ),
        "az első kijelölt fotó háttérforrása hiányzik",
    )
    _wait(
        qt_app,
        lambda: max(
            _panel_pixel(timeline, panel, 250, 200).red(),
            _panel_pixel(timeline, panel, 250, 200).green(),
            _panel_pixel(timeline, panel, 250, 200).blue(),
        ) > 40,
        "az első kijelölt fotó háttere nem töltődött be",
    )
    _wait(
        qt_app,
        lambda: timeline.property("currentCardsLoaded"),
        "a kártyák nem töltődtek be az utóképkockához",
    )

    first_source = background_image.property("source").toString()
    sample = panel.mapToItem(timeline.contentItem(), QPointF(250, 200)).toPoint()
    first_frame = {}

    def elso_hatterkesz():
        frame = timeline.grabWindow()
        pixel = frame.pixelColor(sample)
        if max(pixel.red(), pixel.green(), pixel.blue()) <= 40:
            return False
        first_frame["frame"] = frame
        first_frame["pixel"] = pixel
        return True

    _wait(qt_app, elso_hatterkesz, "a fotó nem látszik a rögzített képkockán")
    frame_before = first_frame["frame"]
    assert frame_before.save(str(tmp_path / "timeline-background-frame.png"))
    first_pixel = first_frame["pixel"]
    assert max(first_pixel.red(), first_pixel.green(), first_pixel.blue()) > 40
    assert background_image.property("source").toString().startswith(
        "image://timelinebackground/"
    )

    QTest.keyClick(timeline, Qt.Key.Key_Right)
    _wait(
        qt_app,
        lambda: timeline.property("motionMode") == "background"
        and timeline.property("currentIndex") == 1
        and background_image.property("source").toString() != first_source,
        "a körhinta megállásakor nem váltott át a háttérforrás",
    )
    _wait(
        qt_app,
        lambda: timeline.property("currentCardsLoaded"),
        "a második gyűjtemény kártyái nem töltődtek be",
    )
    mixed_frame = {}

    def atkevert_hatterkesz():
        frame = timeline.grabWindow()
        pixel = frame.pixelColor(sample)
        old_opacity = timeline.property("previousLayerOpacity")
        new_opacity = timeline.property("currentLayerOpacity")
        if not (0.05 < old_opacity < 0.95 and 0.05 < new_opacity < 0.95):
            return False
        if abs(pixel.green() - first_pixel.green()) < 2:
            return False
        mixed_frame["pixel"] = pixel
        mixed_frame["old_opacity"] = old_opacity
        mixed_frame["new_opacity"] = new_opacity
        return True

    _wait(
        qt_app,
        atkevert_hatterkesz,
        "a régi és az új háttér nem jelent meg átkevert képkockán",
    )
    assert previous_background_image.property("source").toString() == first_source
    assert 0.05 < mixed_frame["old_opacity"] < 0.95
    assert 0.05 < mixed_frame["new_opacity"] < 0.95

    _wait(
        qt_app,
        lambda: timeline.property("motionMode") == "idle"
        and timeline.property("animating") is False,
        "a háttér átúszása nem ért véget",
    )
    second_pixel = _panel_pixel(timeline, panel, 250, 200)
    assert abs(first_pixel.green() - second_pixel.green()) >= 8, (
        "a megváltozott fotó nem frissítette a szürkített háttér képpontját"
    )

    for height in (795, 800, 805):
        timeline.resize(timeline.width(), height)
        _wait(
            qt_app,
            lambda height=height: timeline.height() == height,
            "az ablakmagasság nem állt be",
        )
        panel_center = panel.mapToItem(
            timeline.contentItem(), QPointF(panel.width() / 2, panel.height() / 2)
        )
        assert abs(panel_center.x() - timeline.width() / 2) <= 3
        assert abs(panel_center.y() - timeline.height() / 2) <= 3
