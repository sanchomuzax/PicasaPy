"""A kikapcsolt Gyorscímke-előzmény valódi kattintás után is megmarad (#5665)."""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from PySide6.QtCore import QPoint, QPointF, Qt
from PySide6.QtQuick import QQuickItem
from PySide6.QtTest import QTest

from tests.app.qml_functional.conftest import _build_qml_app
from tests.support.jpeg_factory import make_minta_jpeg
from tests.support.qt_wait import varj_ablakon_belulre
from tests.support.varakozas import var_feltetelre

#: a kiadáskép csak kérésre készül, a hívó adja a mappát
KIADASKEP_MAPPA = "PICASAPY_5665_KIADASKEP_MAPPA"


@pytest.fixture
def qml_app(qt_app, tmp_path):
    """Mintázatos képekkel: a kiadásképen valódi bélyegkép látszik (agent #225)."""

    def kepek(lib):
        make_minta_jpeg(lib / "a.jpg", size=(320, 240), seed=21)
        make_minta_jpeg(lib / "b.jpg", size=(320, 240), seed=22)

    yield from _build_qml_app(
        qt_app,
        tmp_path,
        kepeket_keszit=kepek,
        belyegkep_meret=256,
        valodi_belyegkep=True,
    )


@pytest.mark.parametrize("magassag_eltolas", (-5, 0, 5))
def test_kikapcsolt_legutobbiak_valodi_kattintas_utan_megmaradnak(
    qml_app, qt_app, magassag_eltolas
):
    window, controller, _engine = qml_app
    settings = controller._get_settings()
    settings.setValue(
        "quickTags/recentKeywords", ["korábbi első", "korábbi második"]
    )
    controller.setQuickTagsReserveRecent(False)
    controller.setQuickTagLabel(0, "új címke")

    window.setProperty("activeDrawerTab", "tags")
    window.setProperty("selectedIndexes", [0])
    window.setProperty("selectedIndex", 0)
    window.setHeight(window.height() + magassag_eltolas)
    assert var_feltetelre(
        qt_app,
        lambda: (
            (button := window.findChild(QQuickItem, "quickTagButton0"))
            is not None
            and button.width() > 0
            and button.height() > 0
            and button.property("text") == "új címke"
        ),
        3.0,
    ), "a gyorscímke gomb nem épült fel"

    button = window.findChild(QQuickItem, "quickTagButton0")
    varj_ablakon_belulre(window, button)
    center = button.mapToScene(QPointF(button.width() / 2, button.height() / 2))
    QTest.mouseClick(
        window,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        QPoint(round(center.x()), round(center.y())),
    )

    assert var_feltetelre(
        qt_app,
        lambda: "új címke" in controller.keywordsOfRows([0]),
        3.0,
    ), "a valódi gyorscímke-kattintás nem címkézte meg a kijelölt képet"

    controller.setQuickTagsReserveRecent(True)

    def felso_gombok_regiek():
        buttons = [
            window.findChild(QQuickItem, f"quickTagButton{i}")
            for i in range(2)
        ]
        return all(button is not None for button in buttons) and [
            button.property("text") for button in buttons
        ] == ["korábbi első", "korábbi második"]

    assert var_feltetelre(
        qt_app,
        felso_gombok_regiek,
        3.0,
    ), "a felső két gomb nem a kattintás előtti előzményeket mutatja"

    mappa = os.environ.get(KIADASKEP_MAPPA)
    if magassag_eltolas == 0 and mappa:
        qt_app.processEvents()
        kep = window.grabWindow()
        assert not kep.isNull(), "a kiadáskép üres"
        cel = Path(mappa) / "gyorscimke_5665.png"
        assert kep.save(str(cel), "PNG"), f"nem menthető a kiadáskép: {cel}"
