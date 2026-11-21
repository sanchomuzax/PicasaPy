"""Az Időrend dátumsávja a Picasa hónapra kerekített logaritmikus képletét követi (#7323)."""

from datetime import datetime
from math import isclose, log
from pathlib import Path

from PySide6.QtCore import QLocale

from picasapy.app.timeline_controller import TimelineController
from picasapy.index import PhotoRecord


def _record(identifier: int, folder: str, taken_at: str) -> PhotoRecord:
    return PhotoRecord(
        id=identifier,
        folder_path=f"/library/{folder}",
        name=f"{folder}.jpg",
        kind="photo",
        size=0,
        mtime_ns=0,
        star=False,
        caption=None,
        keywords=None,
        rotate_steps=0,
        filters=None,
        taken_at=taken_at,
        orientation=1,
        width=None,
        height=None,
        geotag=None,
        exif_lat=None,
        exif_lon=None,
    )


def _dot_positions(controller: TimelineController, values: list[float]) -> list:
    return controller.dotPositions(values, 0, 100, 7, 28, 0, 10)


def test_slider_positions_match_month_rounded_logarithmic_cumulative_values(qt_app):
    controller = TimelineController(Path("unused-index.db"), provider=None)
    records = (
        _record(1, "januar", "2020-01-25T12:00:00"),
        _record(2, "februar", "2020-02-11T12:00:00"),
        _record(3, "majus", "2020-05-20T12:00:00"),
    )

    collections = controller._collections_to_qml(records, QLocale("en_US"))

    first_month = datetime(2020, 1, 1)
    second_month = datetime(2020, 2, 1)
    third_month = datetime(2020, 5, 1)
    cumulative = [
        0.0,
        log(1 + (second_month - first_month).days),
        log(1 + (second_month - first_month).days)
        + log(1 + (third_month - second_month).days),
    ]
    denominator = cumulative[-1]
    expected = [value / denominator for value in cumulative]

    assert [item["name"] for item in collections] == ["januar", "februar", "majus"]
    assert len(collections) == len(expected)
    for item, position in zip(collections, expected, strict=True):
        assert isclose(item["sliderPosition"], position, rel_tol=0, abs_tol=1e-12)


def test_same_month_cards_share_a_position_and_zero_denominator_draws_no_dots(qt_app):
    controller = TimelineController(Path("unused-index.db"), provider=None)
    records = (
        _record(1, "jan eleje", "2020-01-03T12:00:00"),
        _record(2, "jan vege", "2020-01-29T12:00:00"),
    )

    collections = controller._collections_to_qml(records, QLocale("en_US"))
    positions = [item["sliderPosition"] for item in collections]

    assert positions == [0.0, 0.0]
    assert _dot_positions(controller, positions) == []
