"""A vetítő Timeline gombjának feltételei és belépési útja (#5653)."""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from PySide6.QtCore import Q_ARG, QMetaObject, QObject, QPoint, Qt
from PySide6.QtGui import QWindow
from PySide6.QtTest import QTest

from support.jpeg_factory import make_minta_jpeg
from support.qt_wait import varj_feltetelre
from tests.app.qml_functional.conftest import _build_qml_app


KIADASKEP_MAPPA = "PICASAPY_5653_KIADASKEP_MAPPA"


def _kepeket_keszit(mappa: Path) -> None:
    make_minta_jpeg(mappa / "a.jpg", size=(1280, 720), seed=81)
    make_minta_jpeg(mappa / "b.jpg", size=(1280, 720), seed=82)


@pytest.fixture
def qml_app_5653(qt_app, tmp_path):
    yield from _build_qml_app(
        qt_app,
        tmp_path,
        kepeket_keszit=_kepeket_keszit,
        belyegkep_meret=256,
        valodi_belyegkep=True,
    )


def _child(parent, name):
    child = parent.findChild(QObject, name)
    assert child is not None, f"{name} nem található"
    return child


def _wait(qt_app, predicate, message: str) -> None:
    assert varj_feltetelre(qt_app, predicate, 3.0), message


def _start_show(window, qt_app):
    window.show()
    window.setVisibility(QWindow.Visibility.Windowed)
    show = _child(window, "slideshowView")
    QMetaObject.invokeMethod(
        show,
        "start",
        Qt.ConnectionType.DirectConnection,
        Q_ARG("QVariant", 0),
    )
    _wait(qt_app, lambda: show.property("visible") is True, "a vetítés nem indult el")
    show.setProperty("playing", False)
    controls = _child(window, "slideshowControls")
    controls.setProperty("shown", True)
    _wait(
        qt_app,
        lambda: controls.property("opacity") >= 0.99,
        "a vezérlősáv nem jelent meg",
    )
    return show


def _set_screen_depth(show, depth: int) -> None:
    # A valódi QScreen mélységét felülírjuk, hogy mindhárom ágat mérjük.
    show.setProperty("screenDepth", depth)


def _timeline_button_and_transition(window):
    return (
        _child(window, "slideshowTimelineButton"),
        _child(window, "slideshowTransitionBox"),
    )


def _start_timeline_slideshow(window, qt_app, folder: Path) -> None:
    QMetaObject.invokeMethod(
        window, "toggleTimeline", Qt.ConnectionType.DirectConnection
    )
    _wait(
        qt_app,
        lambda: window.property("timelineOpen") is True,
        "a Nézet ▸ Időrend belépése nem nyitotta meg a bemutatót",
    )
    QMetaObject.invokeMethod(
        window,
        "startTimelineSlideshow",
        Qt.ConnectionType.DirectConnection,
        Q_ARG("QVariant", str(folder)),
    )
    _wait(
        qt_app,
        lambda: window.property("timelineSlideshowActive") is True,
        "az Időrend-kártya nem indította el a saját diavetítését",
    )
    controls = _child(window, "slideshowControls")
    controls.setProperty("shown", True)
    _wait(
        qt_app,
        lambda: controls.property("opacity") >= 0.99,
        "az Időrendből indított vetítés vezérlősávja nem jelent meg",
    )


def test_normal_slideshow_shows_timeline_instead_of_transition(
    qml_app_5653, qt_app
):
    window, controller, _engine = qml_app_5653
    assert controller._get_settings().contains("Preferences/BigSlideshow2") is False
    assert controller.bigSlideshow2 is True
    show = _start_show(window, qt_app)
    _set_screen_depth(show, 32)

    timeline, transition = _timeline_button_and_transition(window)
    assert timeline.isVisible()
    assert not transition.isVisible()


def test_big_slideshow_disabled_shows_transition_instead_of_timeline(
    qml_app_5653, qt_app
):
    window, controller, _engine = qml_app_5653
    show = _start_show(window, qt_app)
    _set_screen_depth(show, 32)
    controller._get_settings().setValue("Preferences/BigSlideshow2", False)
    controller.statusChanged.emit()

    timeline, transition = _timeline_button_and_transition(window)
    assert not timeline.isVisible()
    assert transition.isVisible()


def test_timeline_started_slideshow_shows_transition_instead_of_timeline(
    qml_app_5653, qt_app
):
    window, controller, _engine = qml_app_5653
    show = _child(window, "slideshowView")
    _set_screen_depth(show, 32)
    _start_timeline_slideshow(window, qt_app, Path(controller._roots[0]))

    timeline, transition = _timeline_button_and_transition(window)
    assert not timeline.isVisible()
    assert transition.isVisible()


def test_other_screen_depth_shows_transition_instead_of_timeline(
    qml_app_5653, qt_app
):
    window, _controller, _engine = qml_app_5653
    show = _start_show(window, qt_app)
    _set_screen_depth(show, 24)

    timeline, transition = _timeline_button_and_transition(window)
    assert not timeline.isVisible()
    assert transition.isVisible()


@pytest.mark.parametrize("height_delta", [-5, 0, 5])
def test_real_timeline_button_click_opens_the_view_menu_timeline(
    qml_app_5653, qt_app, height_delta
):
    window, _controller, _engine = qml_app_5653
    window.show()
    window.setVisibility(QWindow.Visibility.Windowed)
    target_height = window.height() + height_delta
    window.resize(window.width(), target_height)
    _wait(
        qt_app,
        lambda: window.height() == target_height,
        "a főablak magassága nem állt be",
    )
    show = _start_show(window, qt_app)
    _set_screen_depth(show, 32)
    timeline, transition = _timeline_button_and_transition(window)
    assert timeline.isVisible() and not transition.isVisible()

    if height_delta == 0 and (mappa := os.environ.get(KIADASKEP_MAPPA)):
        image = window.grabWindow()
        assert not image.isNull(), "a vetítő kiadásképe üres"
        output_dir = Path(mappa)
        output_dir.mkdir(parents=True, exist_ok=True)
        output = output_dir / "diavetites_idorend_5653.png"
        assert image.save(str(output), "PNG"), f"nem menthető a kiadáskép: {output}"

    center = timeline.mapToScene(timeline.boundingRect().center())
    QTest.mouseClick(
        window,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        QPoint(round(center.x()), round(center.y())),
    )
    _wait(
        qt_app,
        lambda: window.property("timelineOpen") is True,
        "a Timeline gomb nem hívta meg a Nézet ▸ Időrend belépését",
    )
    _wait(qt_app, lambda: not show.property("visible"), "a vetítés nem zárult be")
    view = _child(window, "timelineView")
    _wait(qt_app, view.isVisible, "az Időrend-bemutató nem jelent meg")
