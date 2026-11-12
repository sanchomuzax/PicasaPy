"""A mappa-fejléc a kijelölt képekből készíti a kollázst (#6865)."""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import QPoint, Qt
from PySide6.QtQuick import QQuickItem
from PySide6.QtTest import QTest

from conftest import _build_qml_app
from support.jpeg_factory import make_jpeg
from support.varakozas import hibaturo_feltetel, var_feltetelre


@pytest.fixture
def mappa_24_keppel(qt_app, tmp_path, request):
    def kepeket_keszit(mappa: Path) -> None:
        for index in range(24):
            make_jpeg(mappa / f"kep-{index:02}.jpg", size=(96, 72))

    yield from _build_qml_app(
        qt_app,
        tmp_path,
        kepeket_keszit=kepeket_keszit,
        keep_modul=request.module,
    )


def _walk(item: QQuickItem):
    for child in item.childItems():
        yield child
        yield from _walk(child)


def _elem(window, object_name: str):
    return next(
        (
            item
            for item in _walk(window.contentItem())
            if item.objectName() == object_name
        ),
        None,
    )


def _var(qt_app, condition, seconds: float = 10.0) -> bool:
    return var_feltetelre(qt_app, hibaturo_feltetel(condition), seconds)


def _kattints(window, item, qt_app) -> None:
    assert item is not None and item.isVisible() and item.isEnabled()
    assert item.width() > 0 and item.height() > 0
    center = item.mapToScene(item.boundingRect().center())
    QTest.mouseClick(
        window,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        QPoint(round(center.x()), round(center.y())),
    )
    qt_app.processEvents()


@pytest.mark.parametrize("height_delta", (-5, 0, 5))
def test_kattintas_kijelolest_ad_at_es_kijeloles_nelkul_a_teljes_csoportot(
    mappa_24_keppel, qt_app, height_delta
):
    window, controller, _engine = mappa_24_keppel
    window.setProperty("height", window.property("height") + height_delta)
    qt_app.processEvents()
    gomb = _elem(window, "headerCollageButton")
    assert _var(qt_app, lambda: gomb is not None and gomb.isVisible())

    window.setProperty("selectedIndexes", [3, 17])
    _kattints(window, gomb, qt_app)
    assert _var(qt_app, lambda: controller.collageOpen)
    assert [Path(source.path).name for source in controller._current_sources()] == [
        "kep-03.jpg",
        "kep-17.jpg",
    ]

    controller.closeCollage()
    window.setProperty("selectedIndexes", [])
    _kattints(window, gomb, qt_app)
    assert _var(
        qt_app,
        lambda: [Path(source.path).name for source in controller._current_sources()]
        == [f"kep-{index:02}.jpg" for index in range(24)],
    )
