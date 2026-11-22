"""A mappacsoport-fejlécek valódi QML-renderelése (#7364)."""

from __future__ import annotations

import os
import time
from contextlib import contextmanager
from pathlib import Path

from PySide6.QtCore import QPointF
from PySide6.QtGui import QColor
from PySide6.QtQuick import QQuickItem

from support.jpeg_factory import make_jpeg
from support.qt_wait import varj_feltetelre
from tests.app.qml_functional.conftest import _build_qml_app


_COLAB_MAPPÁK = (
    ("PicasaTeszt", "2026:11:12 12:00:00", (2026, 11, 15, 12, 0, 0)),
    (
        "2021_eltero_fajlido",
        "2021:08:12 12:00:00",
        (2021, 8, 15, 12, 0, 0),
    ),
    ("2019_marcius", "2019:03:12 12:00:00", (2019, 3, 15, 12, 0, 0)),
    ("2014_november", "2014:11:12 12:00:00", (2014, 11, 15, 12, 0, 0)),
    ("2009_majus", "2009:05:12 12:00:00", (2009, 5, 15, 12, 0, 0)),
)


def _utime(path: Path, value: tuple[int, int, int, int, int, int]) -> None:
    stamp = time.mktime((*value, 0, 0, -1))
    os.utime(path, (stamp, stamp))


def _colab_konyvtar(lib: Path) -> None:
    for name, taken_at, changed_at in _COLAB_MAPPÁK:
        folder = lib / name
        folder.mkdir()
        photo = folder / "kep.jpg"
        make_jpeg(photo, size=(64, 48), taken_at=taken_at)
        _utime(photo, changed_at)


def _150933_konyvtar(lib: Path) -> None:
    # A dátum nélküli mappa az üres, ini nélküli mappák között marad az indexben.
    (lib / "HS logo").mkdir()
    folder = lib / "2024_fotok"
    folder.mkdir()
    photo = folder / "kep.jpg"
    make_jpeg(photo, size=(64, 48), taken_at="2024:06:15 12:00:00")
    _utime(photo, (2024, 6, 15, 12, 0, 0))


@contextmanager
def _alkalmazas(qt_app, tmp_path, make_library, keep_modul):
    generator = _build_qml_app(
        qt_app,
        tmp_path,
        kepeket_keszit=make_library,
        keep_modul=keep_modul,
    )
    window, controller, engine = next(generator)
    try:
        window.resize(1280, 900)
        window.show()
        assert varj_feltetelre(qt_app, lambda: window.isVisible()), (
            "a QML-ablak nem jelent meg"
        )
        yield window, controller, engine
    finally:
        try:
            next(generator)
        except StopIteration:
            pass


def _walk(item: QQuickItem):
    for child in item.childItems():
        yield child
        yield from _walk(child)


def _latszik(item: QQuickItem) -> bool:
    if item.width() <= 0 or item.height() <= 0:
        return False
    parent = item
    while parent is not None:
        if not parent.isVisible():
            return False
        parent = parent.parentItem()
    return True


def _kirajzolt_sorok(window) -> list[tuple[str, str, QQuickItem]]:
    rows = [
        item
        for item in _walk(window.contentItem())
        if item.property("kind") in ("year", "folder")
        and item.property("isHeaderRow") is not None
        and _latszik(item)
    ]
    rows.sort(key=lambda item: item.mapToScene(QPointF(0, 0)).y())
    return [(str(item.property("kind")), str(item.property("name")), item) for item in rows]


def _sorok_idovel(window, qt_app, vart: list[tuple[str, str]]) -> None:
    assert varj_feltetelre(
        qt_app,
        lambda: [(kind, name) for kind, name, _item in _kirajzolt_sorok(window)]
        == vart,
        10.0,
    ), f"a renderelt mappasorrend eltér: {_kirajzolt_sorok(window)}"


def _ellenoriz_renderelt_fejlec(window, row: QQuickItem, expected: str) -> None:
    label = next(
        (
            child
            for child in row.childItems()
            if child.property("text") == expected and _latszik(child)
        ),
        None,
    )
    assert label is not None, f"a fejléc szövege nem látható: {expected!r}"

    divider = next(
        (
            child
            for child in row.childItems()
            if child.metaObject().className().endswith("Rectangle")
            and child.height() > 0
            and child.width() > row.width() / 3
            and _latszik(child)
        ),
        None,
    )
    assert divider is not None, f"a fejléc elválasztóvonala nem látható: {expected!r}"

    image = window.grabWindow()
    assert not image.isNull(), "a QML-ablakról nem készült renderelt kép"
    # A fejléc szövege középen fekszik; a vonal szöveg nélküli jobb szélét mérjük.
    sample = divider.mapToScene(QPointF(divider.width() * 0.8, divider.height() / 2))
    scale = image.devicePixelRatio()
    x, y = round(sample.x() * scale), round(sample.y() * scale)
    assert 0 <= x < image.width() and 0 <= y < image.height()
    expected_color = QColor(divider.property("color"))
    matching_pixels = [
        image.pixelColor(px, py)
        for px in range(max(0, x - 1), min(image.width(), x + 2))
        for py in range(max(0, y - 3), min(image.height(), y + 4))
    ]
    assert any(
        all(
            abs(actual - target) <= 3
            for actual, target in zip(
                (pixel.red(), pixel.green(), pixel.blue()),
                (expected_color.red(), expected_color.green(), expected_color.blue()),
                strict=True,
            )
        )
        for pixel in matching_pixels
    ), (
        f"a fejléc vonala nem a QML színével renderelődött: "
        f"várt={expected_color.name()}, line={divider.x()},{divider.y()} "
        f"{divider.width()}x{divider.height()}, sample={sample.x()},{sample.y()}, "
        f"dpr={scale}"
    )


def test_colab_date_lista_elso_sora_fejlec_nelkul_renderelodik(
    qt_app, tmp_path, request
):
    with _alkalmazas(qt_app, tmp_path, _colab_konyvtar, request.module) as (
        window,
        controller,
        _engine,
    ):
        vart = [
            ("folder", "PicasaTeszt"),
            ("year", "2021"),
            ("folder", "2021_eltero_fajlido"),
            ("year", "2019"),
            ("folder", "2019_marcius"),
            ("year", "2014"),
            ("folder", "2014_november"),
            ("year", "2009"),
            ("folder", "2009_majus"),
        ]
        for height_delta in (-5, 0, 5):
            window.resize(window.width(), 900 + height_delta)
            assert varj_feltetelre(
                qt_app, lambda d=height_delta: window.height() == 900 + d
            )
            _sorok_idovel(window, qt_app, vart)
            header = _kirajzolt_sorok(window)[1][2]
            _ellenoriz_renderelt_fejlec(window, header, "2021")


def test_hs_logo_utan_renderelodik_a_2024_fejlec(qt_app, tmp_path, request):
    with _alkalmazas(qt_app, tmp_path, _150933_konyvtar, request.module) as (
        window,
        controller,
        _engine,
    ):
        from picasapy.index import open_index

        with open_index(tmp_path / "index.db") as conn:
            conn.execute(
                "INSERT INTO folders(path, date) VALUES (?, NULL)",
                (str(tmp_path / "kepek" / "HS logo"),),
            )
            controller.folders.load(conn, sort_mode="date", reverse=True)
        vart = [("folder", "HS logo"), ("year", "2024"), ("folder", "2024_fotok")]
        for height_delta in (-5, 0, 5):
            window.resize(window.width(), 900 + height_delta)
            assert varj_feltetelre(
                qt_app, lambda d=height_delta: window.height() == 900 + d
            )
            _sorok_idovel(window, qt_app, vart)
            _ellenoriz_renderelt_fejlec(
                window, _kirajzolt_sorok(window)[1][2], "2024"
            )


def test_recent_changes_rendereli_a_job_802_havi_fejleceit(
    qt_app, tmp_path, request
):
    with _alkalmazas(qt_app, tmp_path, _colab_konyvtar, request.module) as (
        window,
        controller,
        _engine,
    ):
        controller.setPaneSort("changed")
        controller.togglePaneSortReverse()
        vart = [
            ("folder", "2009_majus"),
            ("year", "Updated November 2014"),
            ("folder", "2014_november"),
            ("year", "Updated March 2019"),
            ("folder", "2019_marcius"),
            ("year", "Updated August 2021"),
            ("folder", "2021_eltero_fajlido"),
            ("year", "Updated November 2026"),
            ("folder", "PicasaTeszt"),
        ]
        for height_delta in (-5, 0, 5):
            window.resize(window.width(), 900 + height_delta)
            assert varj_feltetelre(
                qt_app, lambda d=height_delta: window.height() == 900 + d
            )
            _sorok_idovel(window, qt_app, vart)
            _ellenoriz_renderelt_fejlec(
                window,
                _kirajzolt_sorok(window)[1][2],
                "Updated November 2014",
            )
            image = window.grabWindow()
            target = Path(".tmp") / f"7364-recent-changes-{height_delta:+d}.png"
            target.parent.mkdir(exist_ok=True)
            assert image.save(str(target)), f"a próbakép nem menthető: {target}"
