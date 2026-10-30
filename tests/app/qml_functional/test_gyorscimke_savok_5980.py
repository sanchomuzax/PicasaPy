"""A gyorscímkesáv két recent és nyolc kézi helye kattintással (#5980)."""

from __future__ import annotations

import pytest
from PySide6.QtCore import QPoint, QPointF, Qt
from PySide6.QtQuick import QQuickItem
from PySide6.QtTest import QTest

from tests.app.qml_functional.conftest import _build_qml_app
from tests.support.qt_wait import varj_kattinthatora
from tests.support.varakozas import var_feltetelre


@pytest.fixture
def qml_app(qt_app, tmp_path):
    yield from _build_qml_app(qt_app, tmp_path)


@pytest.mark.parametrize("magassag_eltolas", (-5, 0, 5))
def test_recent_es_kezi_helyek_a_savban_es_valodi_kattintas(
    qml_app, qt_app, magassag_eltolas
):
    window, controller, _engine = qml_app
    settings = controller._get_settings()
    settings.setValue("quickTags/recentKeywords", ["recent0", "recent1"])
    for slot in range(10):
        controller.setQuickTagLabel(slot, f"tag{slot}")

    window.setProperty("activeDrawerTab", "tags")
    window.setProperty("selectedIndexes", [0])
    window.setProperty("selectedIndex", 0)
    window.setHeight(window.height() + magassag_eltolas)

    vart = ["recent0", "recent1", *(f"tag{i}" for i in range(2, 10))]

    def sav_felepult():
        buttons = [
            window.findChild(QQuickItem, f"quickTagButton{i}")
            for i in range(10)
        ]
        return all(
            button is not None and button.width() > 0 and button.height() > 0
            for button in buttons
        ) and [button.property("text") for button in buttons] == vart

    assert var_feltetelre(qt_app, sav_felepult, 3.0), (
        "a gyorscímkesáv nem a két recent és a tag2..tag9 kézi helyeket mutatja"
    )

    button = window.findChild(QQuickItem, "quickTagButton2")
    varj_kattinthatora(window, button)
    center = button.mapToScene(QPointF(button.width() / 2, button.height() / 2))
    QTest.mouseClick(
        window,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        QPoint(round(center.x()), round(center.y())),
    )

    assert var_feltetelre(
        qt_app, lambda: "tag2" in controller.keywordsOfRows([0]), 3.0
    ), "a valódi gyorscímke-kattintás nem adta hozzá a kézi tag2 címkét"
    assert controller._quick_tag_recent() == ["tag2", "recent0"]
