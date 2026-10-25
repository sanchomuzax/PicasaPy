"""#5817: a Címkék panel gyakoriság, majd fordított névsor szerint rendez."""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from PySide6.QtCore import QObject, Qt
from PySide6.QtTest import QTest

from support.jpeg_factory import make_minta_jpeg
from support.varakozas import var_feltetelre
from tests.app.qml_functional.conftest import _build_qml_app


def _kepek_keszitese(library: Path) -> None:
    make_minta_jpeg(library / "a.jpg", size=(640, 480), seed=21)
    make_minta_jpeg(library / "b.jpg", size=(640, 480), seed=22)


@pytest.fixture
def qml_app_cimke_sorrend(qt_app, tmp_path, request):
    yield from _build_qml_app(
        qt_app,
        tmp_path,
        kepeket_keszit=_kepek_keszitese,
        belyegkep_meret=256,
        valodi_belyegkep=True,
        keep_modul=request.module,
    )


def _walk(item):
    for child in item.childItems():
        yield child
        yield from _walk(child)


def _item(window, name: str):
    for item in _walk(window.contentItem()):
        if item.objectName() == name:
            return item
    found = window.findChild(QObject, name)
    assert found is not None, f"A kirajzolt felületen nincs ilyen elem: {name}"
    return found


def _thumb(window, row: int):
    for item in _walk(window.contentItem()):
        if item.objectName() != "thumbMouseArea":
            continue
        cell = item.parentItem()
        if cell is not None and int(cell.property("index")) == row:
            return item
    raise AssertionError(f"A(z) {row}. indexkép nem látható a főablakban")


def _click(window, item, qt_app, modifiers=Qt.KeyboardModifier.NoModifier):
    assert item.width() > 0 and item.height() > 0, "a kattintási cél mérete nulla"
    point = item.mapToScene(item.boundingRect().center()).toPoint()
    QTest.mouseClick(window, Qt.MouseButton.LeftButton, modifiers, point)
    qt_app.processEvents()


def _varj(qt_app, feltetel, timeout_ms: int = 10000) -> bool:
    return var_feltetelre(qt_app, feltetel, timeout_ms / 1000)


def _panel_cimkei(window) -> list[str]:
    panel = _item(window, "tagsPanel")
    value = panel.property("tags")
    return list(value) if value is not None else []


def test_valodi_kattintassal_gyakorisag_es_forditott_nevsor(qml_app_cimke_sorrend, qt_app):
    window, controller, _engine = qml_app_cimke_sorrend
    assert _varj(qt_app, lambda: controller.photos.rowCount() == 2)

    controller.addKeywordToRows([0], "AI image")
    controller.addKeywordToRows([0], "proba")
    window.setProperty("activeDrawerTab", "tags")
    window.requestActivate()
    assert _varj(qt_app, lambda: _item(window, "tagsPanel").isVisible())

    alapmagassag = int(window.height())
    for eltolás in (-5, 0, 5):
        window.setHeight(alapmagassag + eltolás)
        qt_app.processEvents()
        _click(window, _thumb(window, 0), qt_app)
        assert _varj(
            qt_app,
            lambda: window.property("selectedIndexes").toVariant() == [0]
            and len(_panel_cimkei(window)) == 2,
        )
        assert _panel_cimkei(window) == ["proba", "AI image"]

    # A két kép közös címkéje legyen az első; a maradékot a címkenév dönti el.
    controller.addKeywordToRows([0, 1], "kozos")
    for eltolás in (-5, 0, 5):
        window.setHeight(alapmagassag + eltolás)
        qt_app.processEvents()
        _click(window, _thumb(window, 0), qt_app)
        assert _varj(
            qt_app,
            lambda: window.property("selectedIndexes").toVariant() == [0],
        )
        _click(
            window,
            _thumb(window, 1),
            qt_app,
            Qt.KeyboardModifier.ControlModifier,
        )
        assert _varj(
            qt_app,
            lambda: window.property("selectedIndexes").toVariant() == [0, 1]
            and _panel_cimkei(window) == ["kozos", "proba", "AI image"],
        )

    screenshot = os.environ.get("PICASAPY_5817_SCREENSHOT")
    if screenshot:
        kep = window.grabWindow()
        assert not kep.isNull(), "a főablak nem adott kiadásképet"
        cel = Path(screenshot)
        cel.parent.mkdir(parents=True, exist_ok=True)
        assert kep.save(str(cel), "PNG"), f"a kiadáskép nem menthető: {cel}"
