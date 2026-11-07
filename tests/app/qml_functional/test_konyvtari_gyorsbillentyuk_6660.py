"""#6660: a meglevő könyvtári műveletek valódi billentyűpróbái."""

from __future__ import annotations

import pytest
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest

from tests.app.qml_functional._mappa_kep_menu_5150_helpers import (
    app_epitese,
    elokeszit,
    varj,
)


def _eltolja_az_ablakmagassagot(window, qt_app, elteres: int) -> None:
    eredeti = window.height()
    cel = eredeti + elteres
    window.setHeight(cel)
    assert varj(qt_app, lambda: window.height() == cel), (
        f"az ablak magassága nem állt át {cel} px-re"
    )


@pytest.mark.parametrize("magassag_eltolas", [-5, 0, 5])
def test_ctrl8_valodi_billentyuvel_billenti_a_kijelolt_kep_csillagat(
    qt_app, tmp_path, magassag_eltolas
):
    app = app_epitese(qt_app, tmp_path)
    window, controller, _engine = next(app)
    try:
        elokeszit(window, qt_app, controller)
        _eltolja_az_ablakmagassagot(window, qt_app, magassag_eltolas)
        assert controller.photos.starAt(0) is False, "a kijelölt kép már csillagos"

        QTest.keyClick(
            window, Qt.Key.Key_8, Qt.KeyboardModifier.ControlModifier
        )
        assert varj(qt_app, lambda: controller.photos.starAt(0) is True), (
            "a Ctrl+8 nem csillagozta a kijelölt képet"
        )

        QTest.keyClick(
            window, Qt.Key.Key_8, Qt.KeyboardModifier.ControlModifier
        )
        assert varj(qt_app, lambda: controller.photos.starAt(0) is False), (
            "a második Ctrl+8 nem vette le a kijelölt kép csillagát"
        )
    finally:
        next(app, None)


@pytest.mark.parametrize("magassag_eltolas", [-5, 0, 5])
def test_ctrl_shift_g_valodi_billentyuvel_megnyitja_a_helyek_panelt(
    qt_app, tmp_path, magassag_eltolas
):
    app = app_epitese(qt_app, tmp_path)
    window, controller, _engine = next(app)
    try:
        elokeszit(window, qt_app, controller)
        _eltolja_az_ablakmagassagot(window, qt_app, magassag_eltolas)
        window.setProperty("activeDrawerTab", "")
        qt_app.processEvents()

        QTest.keyClick(
            window,
            Qt.Key.Key_G,
            Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.ShiftModifier,
        )
        assert varj(
            qt_app, lambda: window.property("activeDrawerTab") == "places"
        ), "a Ctrl+Shift+G nem nyitotta meg a meglévő Helyek panelt"
    finally:
        next(app, None)
