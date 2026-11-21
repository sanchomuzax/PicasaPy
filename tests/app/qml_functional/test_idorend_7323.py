"""Az üres Időrend-elutasítás és az eredeti nyitó/záró áttűnés (#7323)."""

from __future__ import annotations

import time

import pytest
from PySide6.QtCore import QMetaObject, QObject, Qt
from PySide6.QtTest import QTest

from picasapy.index import open_index
from tests.app.qml_functional._nezet_menu_5150_helpers import (
    elokeszit,
    nezet_app_epitese,
    tetel_kattintasa,
    varj,
)


_EMPTY_MESSAGE = "You must have images in the Picture Tray to do this."
_EMPTY_MESSAGE_HU = "A művelet elvégzéséhez a képtálcán elemeknek kell lenniük."


@pytest.fixture
def timeline_app(qt_app, tmp_path):
    yield from nezet_app_epitese(qt_app, tmp_path)


def _child(parent: QObject, name: str) -> QObject:
    child = parent.findChild(QObject, name)
    assert child is not None, f"{name} nem található"
    return child


def _set_window_height(window, qt_app, delta: int) -> None:
    original_height = window.height()
    target_height = original_height + delta
    window.resize(window.width(), target_height)
    assert varj(
        qt_app,
        lambda: window.height() == target_height,
        3.0,
    ), "a főablak magassága nem állt be"


def _animation_times(animation: QObject) -> dict[str, float]:
    stamps: dict[str, float] = {}
    animation.started.connect(lambda: stamps.__setitem__("started", time.monotonic()))
    animation.finished.connect(lambda: stamps.__setitem__("finished", time.monotonic()))
    return stamps


@pytest.mark.parametrize("height_delta", (-5, 0, 5))
def test_real_view_menu_rejects_an_empty_timeline_and_shows_the_message(
    timeline_app, qt_app, tmp_path, height_delta
):
    window, controller, engine = timeline_app
    _set_window_height(window, qt_app, height_delta)
    elokeszit(window, qt_app, controller)

    empty_index = tmp_path / "empty_timeline.db"
    with open_index(empty_index):
        pass
    timeline_controller = engine.rootContext().contextProperty("timelineController")
    timeline_controller._db_path = empty_index

    tetel_kattintasa(window, qt_app, "menuViewTimeline")

    message = _child(window, "errorBannerText")
    timeline = _child(window, "timelineView")
    assert varj(
        qt_app,
        lambda: message.property("text") in {_EMPTY_MESSAGE, _EMPTY_MESSAGE_HU},
        3.0,
    ), "az üres Időrend nem jelenítette meg az eredeti üzenetet"
    assert window.property("timelineOpen") is False
    assert timeline.isVisible() is False


def test_open_and_escape_fades_take_about_one_second(timeline_app, qt_app):
    window, controller, _engine = timeline_app
    elokeszit(window, qt_app, controller)
    assert QMetaObject.invokeMethod(
        window,
        "ensureTimelineView",
        Qt.ConnectionType.DirectConnection,
    )
    timeline = _child(window, "timelineView")
    opening_fade = _child(timeline, "timelineOpeningFade")
    closing_fade = _child(timeline, "timelineClosingFade")
    open_times = _animation_times(opening_fade)
    close_times = _animation_times(closing_fade)

    tetel_kattintasa(window, qt_app, "menuViewTimeline")
    fade_cover = _child(timeline, "timelineFadeCover")
    assert opening_fade.property("duration") == 1000
    assert varj(qt_app, lambda: "finished" in open_times, 3.0), (
        "a nyitási áttűnés nem érte el a teljes fedettséget"
    )
    opening_elapsed = open_times["finished"] - open_times["started"]
    assert 0.8 <= opening_elapsed <= 3.0, opening_elapsed
    assert fade_cover.property("opacity") <= 0.001

    assert closing_fade.property("duration") == 1000
    QTest.keyClick(timeline, Qt.Key.Key_Escape)
    assert timeline.isVisible() is True
    assert varj(
        qt_app,
        lambda: fade_cover.property("opacity") > 0.0,
        1.0,
    ), "a zárási áttűnés nem sötétítette a nézetet"
    assert varj(qt_app, lambda: "finished" in close_times, 3.0), (
        "az Escape nem zárta be az Időrendet az áttűnés után"
    )
    assert varj(qt_app, lambda: timeline.isVisible() is False, 1.0), (
        "az Escape nem zárta be az Időrendet az áttűnés után"
    )
    closing_elapsed = close_times["finished"] - close_times["started"]
    assert 0.8 <= closing_elapsed <= 3.0, closing_elapsed
    assert fade_cover.property("opacity") >= 0.999
