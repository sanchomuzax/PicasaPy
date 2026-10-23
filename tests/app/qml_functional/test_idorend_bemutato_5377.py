"""Valódi bemeneti és képkocka-próbák a teljes képernyős Időrendhez."""

from pathlib import Path
from math import cos, radians, sin

from PySide6.QtCore import QObject, QPointF, Qt
from PySide6.QtGui import QColor
from PySide6.QtTest import QTest
import pytest

from support.jpeg_factory import make_minta_jpeg
from tests.app.qml_functional.conftest import _build_qml_app
from tests.support.varakozas import var_feltetelre


def _child(parent, name):
    child = parent.findChild(QObject, name)
    assert child is not None, f"{name} nem található"
    return child


def _wait(qt_app, predicate, seconds=10.0):
    return var_feltetelre(qt_app, predicate, seconds)


def _keszits_mintakepeket(mappa: Path) -> None:
    for mappa_nev, offset in (("PicasaTeszt", 0), ("Recently Updated", 10)):
        gyujtemeny = mappa / mappa_nev
        gyujtemeny.mkdir()
        for sorszam in range(1, 5):
            make_minta_jpeg(
                gyujtemeny / f"timeline-{sorszam}.jpg",
                size=(320, 240),
                seed=offset + sorszam,
            )


@pytest.fixture
def qml_app_idorend_5377(qt_app, tmp_path):
    """Mintázatos, valódi bélyegképek a kiadásképhez (#225)."""
    yield from _build_qml_app(
        qt_app,
        tmp_path,
        kepeket_keszit=_keszits_mintakepeket,
        belyegkep_meret=256,
        valodi_belyegkep=True,
    )


def _sample_collections(folder_path):
    return [
        {
            "name": "Első gyűjtemény",
            "folderPath": folder_path,
            "dateLabel": "October 2026",
            "firstDateLabel": "October 2026",
            "lastDateLabel": "October 2026",
            "sliderPosition": 0.0,
            "photos": [],
        },
        {
            "name": "Második gyűjtemény",
            "folderPath": folder_path,
            "dateLabel": "October 2026",
            "firstDateLabel": "October 2026",
            "lastDateLabel": "October 2026",
            "sliderPosition": 1.0,
            "photos": [],
        },
    ]


def _open_timeline(window, qt_app):
    window.setProperty("selectedIndexes", [])
    window.requestActivate()
    assert _wait(qt_app, window.isActive), "a főablak nem lett aktív"
    QTest.keyClick(
        window,
        Qt.Key.Key_5,
        Qt.KeyboardModifier.ControlModifier,
    )
    assert _wait(qt_app, lambda: window.property("timelineOpen") is True), (
        "a Ctrl+5 nem nyitotta meg a bemutatót kijelölés nélkül"
    )
    timeline = _child(window, "timelineView")
    assert _wait(qt_app, timeline.isVisible), "a teljes képernyős Időrend nem látszik"
    timeline.requestActivate()
    assert _wait(qt_app, timeline.isActive), "az Időrend nem kapott billentyűfókuszt"
    return timeline


def test_ctrl5_opens_fullscreen_timeline_without_selection(qml_app, qt_app):
    window, _controller, _engine = qml_app
    timeline = _open_timeline(window, qt_app)
    assert timeline.property("visibility").value == timeline.property(
        "fullscreenVisibility"
    )
    assert timeline.property("currentIndex") == 0


@pytest.mark.parametrize("height", [795, 800, 805])
def test_rendered_timeline_has_centered_600_by_480_panel(
    qml_app_idorend_5377, qt_app, tmp_path, height
):
    window, _controller, engine = qml_app_idorend_5377
    timeline = _open_timeline(window, qt_app)
    timeline_controller = engine.rootContext().contextProperty("timelineController")
    reference_collections = [dict(item) for item in timeline_controller.collections]
    reference_collections[0].update(
        name="PicasaTeszt",
        dateLabel="October 2026",
        firstDateLabel="October 2026",
        lastDateLabel="October 2026",
        sliderPosition=0.3,
    )
    reference_collections[-1]["sliderPosition"] = 1.0
    timeline.setProperty("collectionsModel", reference_collections)
    name = _child(timeline, "timelineCollectionName")
    date = _child(timeline, "timelineCollectionDate")
    assert name.property("text") == "PicasaTeszt"
    assert date.property("text") == "October 2026"

    panel = _child(timeline, "timelinePanel")
    assert panel.property("width") == 600
    assert panel.property("height") == 480
    assert _wait(
        qt_app,
        lambda: timeline.property("currentCardsLoaded"),
    ), "a gyűjtemény bélyegképei nem töltődtek be"
    frame = timeline.grabWindow()
    assert not frame.isNull(), "az Időrend képkockája üres"
    assert frame.pixelColor(5, 5) == QColor("black")
    center = panel.mapToItem(timeline.contentItem(), QPointF(300, 240))
    assert abs(center.x() - timeline.width() / 2) <= 3
    assert abs(center.y() - timeline.height() / 2) <= 3
    panel_center = center.toPoint()
    assert frame.pixelColor(panel_center.x(), panel_center.y()) != QColor("black")
    panel_background = panel.mapToItem(
        timeline.contentItem(), QPointF(35, 25)
    ).toPoint()
    background_pixel = frame.pixelColor(panel_background)
    assert max(
        abs(background_pixel.red() - 138),
        abs(background_pixel.green() - 136),
        abs(background_pixel.blue() - 139),
    ) <= 3, (
        "a panel alapfelülete nem a referencia szürke mezője: "
        f"{background_pixel.name()}"
    )
    for object_name in (
        "timelineCollectionName",
        "timelineCollectionDate",
        "timelineControlBar",
        "timelineSliderTrack",
        "timelineSliderThumb",
        "timelineDateDots",
    ):
        _child(timeline, object_name)
    control_bar = _child(timeline, "timelineControlBar")
    control_top = control_bar.mapToItem(panel, QPointF(0, 0))
    assert abs(control_top.y() - 403) <= 3
    slider_area = _child(timeline, "timelineSliderArea")
    slider_top = slider_area.mapToItem(panel, QPointF(0, 0))
    assert abs(slider_top.y() - 452) <= 3
    photo_deck = _child(timeline, "timelineCurrentPhotoDeck")
    assert photo_deck.property("count") >= 3, (
        "a gyűjtemény képei nem alkotnak több, egymásra döntött bélyegből álló köteget"
    )
    next_deck = _child(timeline, "timelineNextPhotoDeck")
    assert next_deck.property("count") >= 3, (
        "a következő gyűjtemény képkötege nem látható a jelenlegi mellett"
    )
    first_photo_url = reference_collections[0]["photos"][0]["thumbUrl"]
    assert first_photo_url.startswith("image://thumbs/"), first_photo_url
    timeline.setProperty("visibility", timeline.property("windowedVisibility"))
    timeline.resize(1280, 1024)
    assert _wait(qt_app, lambda: timeline.width() == 1280)
    assert _wait(qt_app, lambda: timeline.height() == 1024)
    reference_center = panel.mapToItem(
        timeline.contentItem(), QPointF(300, 240)
    )
    assert abs(reference_center.x() - 640) <= 3
    assert abs(reference_center.y() - 512) <= 3
    if height == 800:
        reference_frame = timeline.grabWindow()
        assert not reference_frame.isNull()
        assert reference_frame.save(str(tmp_path / "timeline-frame.png"))
        card_curve = timeline_controller.bezierAt(0.94)
        card_center = panel.mapToItem(
            timeline.contentItem(),
            QPointF(
                card_curve["x"] * panel.property("width"),
                card_curve["y"] * panel.property("height"),
            ),
        ).toPoint()
        sample_colors = {
            reference_frame.pixelColor(card_center.x() + dx, card_center.y() + dy).rgba()
            for dx, dy in ((-8, -8), (0, -8), (8, -8), (-8, 0), (0, 0), (8, 0),
                           (-8, 8), (0, 8), (8, 8))
        }
        assert len(sample_colors) >= 4, (
            "a kártyán nem mintázatos valódi bélyegkép látszik: "
            f"{first_photo_url}, a mért eltérő képpontok száma {len(sample_colors)}"
        )

        card_geometry = timeline.property("currentPhotoCardGeometry").toVariant()
        assert len(card_geometry) == photo_deck.property("count")
        assert all(abs(card["rotation"]) >= 3 for card in card_geometry), (
            "a bélyegköteg valamelyik képe nincs megdöntve"
        )

        def rotated_bounds(card):
            angle = radians(abs(card["rotation"]))
            bound_width = card["width"] * cos(angle) + card["height"] * sin(angle)
            bound_height = card["height"] * cos(angle) + card["width"] * sin(angle)
            center_x = card["x"] + card["width"] / 2
            center_y = card["y"] + card["height"] / 2
            return (
                center_x - bound_width / 2,
                center_y - bound_height / 2,
                center_x + bound_width / 2,
                center_y + bound_height / 2,
            )

        card_bounds = [rotated_bounds(card) for card in card_geometry]
        assert all(
            min(first[2], second[2]) - max(first[0], second[0])
            >= min(first[2] - first[0], second[2] - second[0]) * 0.4
            and min(first[3], second[3]) > max(first[1], second[1])
            for first, second in zip(card_bounds, card_bounds[1:], strict=False)
        ), "a bélyegképek nem fednek egymásra látható kötegként"

        first_card = card_geometry[0]
        first_curve = timeline_controller.bezierAt(0.94)
        actual_card_center = QPointF(
            panel.mapToItem(timeline.contentItem(), QPointF(
                first_card["x"] + first_card["width"] / 2,
                first_card["y"] + first_card["height"] / 2,
            ))
        )
        expected_card_center = panel.mapToItem(
            timeline.contentItem(),
            QPointF(
                first_curve["x"] * panel.property("width"),
                first_curve["y"] * panel.property("height"),
            ),
        )
        assert abs(actual_card_center.x() - expected_card_center.x()) <= 3
        assert abs(actual_card_center.y() - expected_card_center.y()) <= 3

        artwork = _child(timeline, "timelineCardArtwork")
        arc_points = artwork.property("dotArcPoints").toVariant()
        dot_values = [
            float(collection.get("sliderPosition", 0))
            for collection in reference_collections
        ]
        measured_dots = timeline_controller.dotPositions(
            dot_values,
            0,
            max(0, int(panel.property("width")) - 4),
            0,
            0,
            0,
            0,
        )
        expected_arc = []
        first_card = card_geometry[0]
        start_x = name.property("x") + name.property("width") - 8
        start_y = date.property("y") + 42
        end_x = first_card["x"] + first_card["width"] * 0.38
        end_y = first_card["y"] - 48
        control_1_x, control_1_y = start_x + 3, start_y + 50
        control_2_x, control_2_y = end_x + 38, end_y - 15
        for dot in measured_dots:
            if not dot["draw"]:
                continue
            curve_parameter = 1 - dot["x"] / max(
                1, int(panel.property("width")) - 4
            )
            one_minus_t = 1 - curve_parameter
            expected_arc.append(
                (
                    one_minus_t**3 * start_x
                    + 3 * one_minus_t**2 * curve_parameter * control_1_x
                    + 3 * one_minus_t * curve_parameter**2 * control_2_x
                    + curve_parameter**3 * end_x,
                    one_minus_t**3 * start_y
                    + 3 * one_minus_t**2 * curve_parameter * control_1_y
                    + 3 * one_minus_t * curve_parameter**2 * control_2_y
                    + curve_parameter**3 * end_y
                    + dot["y"],
                )
            )
        assert len(arc_points) == len(expected_arc), (
            "a timelinedot pontok száma nem az A tömb mért elemeit követi"
        )
        for actual, (expected_x, expected_y) in zip(
            arc_points, expected_arc, strict=True
        ):
            assert abs(actual["x"] - expected_x) <= 1
            assert abs(actual["y"] - expected_y) <= 1

    timeline.resize(timeline.width(), height)
    assert _wait(qt_app, lambda: timeline.height() == height)
    resized_center = panel.mapToItem(timeline.contentItem(), QPointF(300, 240))
    assert abs(resized_center.y() - timeline.height() / 2) <= 3


def test_timeline_slider_dates_have_reference_contrast(qml_app, qt_app):
    window, _controller, _engine = qml_app
    timeline = _open_timeline(window, qt_app)
    background = QColor("#8a888b")

    def luminance(color):
        channels = [color.red(), color.green(), color.blue()]
        linear = [
            channel / 3294.6 if channel <= 10 else ((channel / 255 + 0.055) / 1.055) ** 2.4
            for channel in channels
        ]
        return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]

    background_luminance = luminance(background)
    for object_name in ("timelineFirstDate", "timelineLastDate"):
        date_label = _child(timeline, object_name)
        label_color = QColor(date_label.property("color"))
        label_luminance = luminance(label_color)
        contrast = (background_luminance + 0.05) / (label_luminance + 0.05)
        assert contrast >= 3.0, (
            f"a {object_name} felirata halvány a panel hátterén: {contrast:.2f}:1"
        )


@pytest.mark.parametrize("height", [795, 800, 805])
def test_keys_buttons_and_slider_animate_between_collection_cards(
    qml_app, qt_app, height
):
    window, controller, _engine = qml_app
    window.resize(window.width(), height)
    timeline = _open_timeline(window, qt_app)
    timeline.setProperty("collectionsModel", _sample_collections(controller.currentFolder))

    QTest.keyClick(timeline, Qt.Key.Key_Right)
    assert _wait(qt_app, lambda: timeline.property("currentIndex") == 1)
    assert timeline.property("animationDurationMs") == 2000

    QTest.keyClick(timeline, Qt.Key.Key_Left)
    assert _wait(qt_app, lambda: timeline.property("currentIndex") == 0)
    assert timeline.property("animationDurationMs") == 2000

    right_button = _child(timeline, "timelineRightButton")
    right_point = right_button.mapToItem(
        timeline.contentItem(),
        QPointF(right_button.width() / 2, right_button.height() / 2),
    ).toPoint()
    QTest.mouseClick(timeline, Qt.MouseButton.LeftButton, pos=right_point)
    assert _wait(qt_app, lambda: timeline.property("currentIndex") == 1)
    assert timeline.property("animationDurationMs") == 2000

    slider = _child(timeline, "timelineSliderMouseArea")
    slider_point = slider.mapToItem(
        timeline.contentItem(), QPointF(1, slider.height() / 2)
    ).toPoint()
    QTest.mouseClick(timeline, Qt.MouseButton.LeftButton, pos=slider_point)
    assert _wait(qt_app, lambda: timeline.property("currentIndex") == 0)
    assert timeline.property("animationDurationMs") == 4000

    play_button = _child(timeline, "timelinePlayButton")
    play_point = play_button.mapToItem(
        timeline.contentItem(),
        QPointF(play_button.width() / 2, play_button.height() / 2),
    ).toPoint()
    QTest.mouseClick(timeline, Qt.MouseButton.LeftButton, pos=play_point)
    slideshow = _child(window, "slideshowView")
    assert _wait(qt_app, slideshow.isVisible)


def test_space_starts_collection_slideshow_and_escape_returns_to_main(qml_app, qt_app):
    window, controller, _engine = qml_app
    timeline = _open_timeline(window, qt_app)
    timeline.setProperty("collectionsModel", _sample_collections(controller.currentFolder))

    QTest.keyClick(timeline, Qt.Key.Key_Right)
    assert _wait(qt_app, lambda: timeline.property("currentIndex") == 1)
    QTest.keyClick(timeline, Qt.Key.Key_Space)
    slideshow = _child(window, "slideshowView")
    assert _wait(qt_app, slideshow.isVisible), (
        "a szóköz nem indította a gyűjtemény diavetítését"
    )
    slideshow_model = slideshow.property("photosModel")
    assert slideshow_model.rowCount() == 2
    assert slideshow_model.filePathAt(0).startswith(controller.currentFolder)
    assert window.property("timelineOpen") is False

    QTest.keyClick(window, Qt.Key.Key_Escape)
    assert _wait(qt_app, lambda: slideshow.isVisible() is False)
    assert window.property("timelineOpen") is False


def test_escape_key_closes_timeline_to_main_window(qml_app, qt_app):
    window, _controller, _engine = qml_app
    timeline = _open_timeline(window, qt_app)
    QTest.keyClick(timeline, Qt.Key.Key_Escape)
    assert _wait(qt_app, lambda: window.property("timelineOpen") is False)
    assert _wait(qt_app, lambda: timeline.isVisible() is False)
