"""A mappa-fejléc film gombjának kijelölés szerinti bemenete (#6889)."""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import QMetaObject, QPoint, Qt, QUrl
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


def _zar_film(qt_app, movie_dialog) -> None:
    QMetaObject.invokeMethod(movie_dialog, "close", Qt.ConnectionType.DirectConnection)
    qt_app.processEvents()


def _klip_nevek(movie_dialog) -> list[str]:
    forrasok = movie_dialog.property("movieClipSources")
    if hasattr(forrasok, "toVariant"):
        forrasok = forrasok.toVariant()
    return [Path(QUrl(str(url)).toLocalFile()).name for url in forrasok]


@pytest.mark.parametrize("height_delta", (-5, 0, 5))
def test_fejlec_film_gomb_kijeloles_szerint_nyit(
    mappa_24_keppel, qt_app, height_delta
):
    window, controller, _engine = mappa_24_keppel
    eredeti_magassag = window.property("height")
    window.setProperty("height", eredeti_magassag + height_delta)
    qt_app.processEvents()
    gomb = _elem(window, "headerMovieButton")
    assert _var(qt_app, lambda: gomb is not None and gomb.isVisible() and gomb.isEnabled())

    # 1. Két kijelölt kép -> pontosan 2 klip a Filmkészítőben
    window.setProperty("selectedIndexes", [3, 17])
    _kattints(window, gomb, qt_app)
    movie_dialog = _elem(window, "movieDialog")
    assert movie_dialog is not None
    assert _var(qt_app, lambda: movie_dialog.property("visible") is True)
    assert _var(qt_app, lambda: len(_klip_nevek(movie_dialog)) == 2)
    assert _klip_nevek(movie_dialog) == ["kep-03.jpg", "kep-17.jpg"]
    _zar_film(qt_app, movie_dialog)
    assert _var(qt_app, lambda: movie_dialog.property("visible") is False)

    # 2. Egy kijelölt kép -> a teljes mappa (24 klip)
    window.setProperty("selectedIndexes", [5])
    _kattints(window, gomb, qt_app)
    assert _var(qt_app, lambda: movie_dialog.property("visible") is True)
    assert _var(qt_app, lambda: len(_klip_nevek(movie_dialog)) == 24)
    assert _klip_nevek(movie_dialog) == [f"kep-{i:02}.jpg" for i in range(24)]
    _zar_film(qt_app, movie_dialog)
    assert _var(qt_app, lambda: movie_dialog.property("visible") is False)

    # 3. Nulla kijelölt kép -> a teljes mappa (24 klip)
    window.setProperty("selectedIndexes", [])
    _kattints(window, gomb, qt_app)
    assert _var(qt_app, lambda: movie_dialog.property("visible") is True)
    assert _var(qt_app, lambda: len(_klip_nevek(movie_dialog)) == 24)
    assert _klip_nevek(movie_dialog) == [f"kep-{i:02}.jpg" for i in range(24)]
    _zar_film(qt_app, movie_dialog)
    assert _var(qt_app, lambda: movie_dialog.property("visible") is False)

    window.setProperty("height", eredeti_magassag)
    qt_app.processEvents()
