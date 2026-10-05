"""#4289: görgetés egy teljes képernyőnyi bélyegképet ír a cache-be."""

from __future__ import annotations

import math
import time
from pathlib import Path

import pytest
from PySide6.QtCore import QPointF, QObject
from PySide6.QtTest import QTest

from picasapy.index import open_index, sync_tree
from support.jpeg_factory import make_jpeg


def _feed_cell_rows(grid) -> set[int]:
    """A ténylegesen a nézőtérben álló `feedCell`-ek sorindexei."""
    rows: set[int] = set()

    def visit(item) -> None:
        if item.objectName() == "feedCell":
            top_left = item.mapToItem(grid, QPointF(0, 0))
            top = float(top_left.y())
            bottom = top + float(item.height())
            if bottom > 0 and top < float(grid.height()):
                rows.add(int(item.property("row")))
        for child in item.childItems():
            visit(child)

    visit(grid.property("contentItem"))
    return rows


def _cache_contains(provider, photo) -> bool:
    cache = provider._cache
    source = Path(photo.folder_path) / photo.name
    return any(
        cache.thumbnail_path(
            source, photo.mtime_ns, photo.size, level
        ).is_file()
        for level in (None, *cache.levels)
    )


def _wait_for(qt_app, predicate, timeout: float = 8.0) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        qt_app.processEvents()
        if predicate():
            return True
        QTest.qWait(20)
    qt_app.processEvents()
    return bool(predicate())


@pytest.mark.parametrize("height_delta", (-5, 0, 5))
def test_scroll_prefetches_a_full_viewport_before_it_is_visible(
    qml_app, qt_app, height_delta
):
    window, controller, _engine = qml_app
    library = Path(controller._roots[0])
    for index in range(2, 182):
        make_jpeg(library / f"prefetch-{index:03}.jpg", size=(80, 60))
    with open_index(controller._db_path) as connection:
        sync_tree(connection, library)
    controller._reload()

    original_height = int(window.height())
    window.setProperty("height", original_height + height_delta)
    qt_app.processEvents()
    grid = window.findChild(QObject, "photoGrid")
    assert grid is not None, "photoGrid nem található"

    assert _wait_for(
        qt_app,
        lambda: len(controller.photos.photos) >= 180
        and float(grid.height()) > 0
        and float(grid.property("contentHeight")) > float(grid.height()),
    ), "a próbarács nem vált görgethetővé"

    provider = controller._provider
    provider.clear_cache()
    visible_before = _feed_cell_rows(grid)
    assert visible_before, "a rácsban nincs ténylegesen látható próbacella"

    cell_height = float(grid.property("cellHeight"))
    grid.setProperty(
        "contentY",
        min(
            float(grid.property("contentY")) + cell_height * 3,
            float(grid.property("contentHeight")) - float(grid.height()),
        ),
    )
    qt_app.processEvents()

    expected_row: int | None = None

    def future_thumbnail_is_cached() -> bool:
        nonlocal expected_row
        visible = _feed_cell_rows(grid)
        if not visible:
            return False
        viewport_rows = math.ceil(float(grid.height()) / cell_height)
        screen_cells = viewport_rows * int(grid.property("columns"))
        expected_row = max(visible) + screen_cells
        if expected_row >= len(controller.photos.photos):
            return False
        if expected_row in visible:
            return False
        return _cache_contains(provider, controller.photos.photos[expected_row])

    assert _wait_for(qt_app, future_thumbnail_is_cached), (
        "a görgetés irányában egy teljes képernyőnyi távolságban lévő "
        f"{expected_row}. sor bélyegképe nem került a cache-be, mielőtt "
        "láthatóvá vált volna"
    )
