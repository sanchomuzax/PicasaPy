"""A Kép ▸ Csoportos szerkesztés eredeti sorrendje és átnevezője (#4701)."""

from __future__ import annotations

import time

import pytest
from PySide6.QtCore import QObject

from tests.app.qml_functional.test_photo_menu_commands import (
    _batch_menu_item_names,
    _click_item,
    _picture_menu_item,
)


def _varj(qt_app, feltetel, timeout=3.0):
    hatarido = time.monotonic() + timeout
    while time.monotonic() < hatarido:
        qt_app.processEvents()
        if feltetel():
            return True
        time.sleep(0.01)
    qt_app.processEvents()
    return bool(feltetel())


@pytest.mark.parametrize("magassag_eltolas", (-5, 0, 5))
def test_az_almenu_sorrendje_es_csoportjai_az_eredetit_kovetik(
    qml_app, qt_app, magassag_eltolas
):
    window, _controller, _engine = qml_app
    window.setHeight(window.height() + magassag_eltolas)
    window.setProperty("selectedIndexes", [0])
    window.setProperty("selectedIndex", 0)
    qt_app.processEvents()

    _picture_menu_item(qt_app, window, "menuBatchAutoContrast")
    assert _batch_menu_item_names(window) == [
        "menuBatchRename",
        "",
        "menuBatchRotateRight",
        "menuBatchRotateLeft",
        "",
        "menuBatchAutoContrast",
        "menuBatchAutoColor",
        "menuBatchEnhance",
        "",
        "menuBatchSepia",
        "menuBatchSharpen",
        "menuBatchWarmify",
        "menuBatchFilmGrain",
        "menuBatchBlackWhite",
        "",
        "menuBatchAutoRedeye",
        "",
        "menuPictureShowText",
        "menuPictureHideText",
    ]


@pytest.mark.parametrize("magassag_eltolas", (-5, 0, 5))
def test_az_atnevezes_a_kijelolt_kepek_atnevezo_parbeszedehez_vezet(
    qml_app, qt_app, magassag_eltolas
):
    window, _controller, _engine = qml_app
    window.setHeight(window.height() + magassag_eltolas)
    window.setProperty("selectedIndexes", [0, 1])
    window.setProperty("selectedIndex", 0)
    qt_app.processEvents()

    item = _picture_menu_item(qt_app, window, "menuBatchRename")
    assert item["qml_item"].property("text") == "&Rename...\tF2"
    _click_item(qt_app, item)

    assert _varj(
        qt_app,
        lambda: (
            (dialog := window.findChild(QObject, "renameManyDialog")) is not None
            and dialog.property("visible") is True
        ),
    ), "a kijelölt képek átnevező párbeszéde nem nyílt meg"
    dialog = window.findChild(QObject, "renameManyDialog")
    label = dialog.findChild(QObject, "renameManySelectionLabel")
    assert label is not None
    assert "2" in str(label.property("text"))
