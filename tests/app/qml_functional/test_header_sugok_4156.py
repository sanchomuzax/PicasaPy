"""A fejléc két, már megépült művelete az eredeti súgót mutatja (#4156)."""

from __future__ import annotations

import time
from pathlib import Path

from PySide6.QtCore import QObject, QPoint, QPointF, QUrl
from PySide6.QtQml import QQmlComponent
from PySide6.QtQuick import QQuickItem
from PySide6.QtTest import QTest

from tests.support.qml_blokk import blokk_horgonyra

_QML = Path(__file__).resolve().parents[3] / "src/picasapy/app/qml/PicasaPy"
_HEADER = (_QML / "LightboxHeader.qml").read_text(encoding="utf-8")
_TRAY = (_QML / "TrayBar.qml").read_text(encoding="utf-8")
_KEEP_ALIVE: list[QObject] = []


def _keres(item: QQuickItem, nev: str):
    for child in item.childItems():
        if child.objectName() == nev:
            return child
        talalat = _keres(child, nev)
        if talalat is not None:
            return talalat
    return None


def _tooltip_probe(engine, target):
    component = QQmlComponent(engine)
    component.setData(
        b"""import QtQuick\nimport QtQuick.Controls\nItem {
            property var targetItem
            readonly property bool tooltipVisible:
                targetItem.ToolTip.toolTip.visible
            readonly property string tooltipText:
                targetItem.ToolTip.toolTip.text
        }""",
        QUrl(),
    )
    assert component.isReady(), component.errors()
    probe = component.createWithInitialProperties({"targetItem": target})
    assert probe is not None, component.errors()
    _KEEP_ALIVE.extend((component, probe))
    return probe


def test_a_diavetites_gombja_az_eredeti_sugot_adja():
    blokk = blokk_horgonyra(_HEADER, "headerPlayButton")
    assert 'ToolTip.text: qsTr("Play Fullscreen Slideshow")' in blokk


def test_a_mozgofilm_gombja_az_eredeti_sugot_adja():
    blokk = blokk_horgonyra(_TRAY, "trayMovieButton")
    assert 'ToolTip.text: qsTr("Create Movie Presentation")' in blokk


def _ellenoriz_hover_kimenet(window, qt_app, button, text, probe):
    window.requestActivate()
    assert QTest.qWaitForWindowActive(window, 3000)
    height = window.height()
    try:
        for delta in (-5, 0, 5):
            window.resize(window.width(), height + delta)
            qt_app.processEvents()
            assert button.isVisible() and button.width() > 0
            center = button.mapToScene(
                QPointF(button.width() / 2, button.height() / 2)
            ).toPoint()
            QTest.mouseMove(window, center)
            deadline = time.monotonic() + 3.0
            while time.monotonic() < deadline:
                qt_app.processEvents()
                if probe.property("tooltipVisible"):
                    break
                time.sleep(0.01)
            assert probe.property("tooltipVisible"), (
                f"{text}: a ToolTip rejtve maradt; "
                f"enabled={button.isEnabled()}, scene={center}, "
                f"hovered={button.property('hovered')!r}, "
                f"tooltipText={probe.property('tooltipText')!r}"
            )
            assert probe.property("tooltipText") == text
            QTest.mouseMove(window, QPoint(1, 1))
            qt_app.processEvents()
    finally:
        window.resize(window.width(), height)


def test_a_diavetites_sugo_a_foablakban_megjelenik(qml_app, qt_app):
    window, _controller, engine = qml_app
    qt_app.processEvents()
    feed = window.findChild(QObject, "photoGrid")
    assert feed is not None
    button = _keres(feed, "headerPlayButton")
    assert button is not None
    _ellenoriz_hover_kimenet(
        window, qt_app, button, "Play Fullscreen Slideshow",
        _tooltip_probe(engine, button),
    )


def test_a_film_gomb_sugoja_a_foablakban_megjelenik(qml_app, qt_app):
    window, _controller, engine = qml_app
    window.setProperty("selectedIndexes", [0])
    qt_app.processEvents()
    button = _keres(window.contentItem(), "trayMovieButton")
    assert button is not None and button.isEnabled()
    _ellenoriz_hover_kimenet(
        window, qt_app, button, "Create Movie Presentation",
        _tooltip_probe(engine, button),
    )
