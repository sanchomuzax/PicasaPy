"""A vetítő vezérlősávja: Timeline gomb és átmenet-választó (#5653, #7209).

#7209 (D1): az eredeti normál (`editoneup`) vetítőben a `timeline` rejtett
(`editoneup.tre:62-66`), ezért a Timeline gomb SEHOL nem látszik, az
átmenet-választó pedig mindig. A #5653 eredeti feltételei (BigSlideshow2,
16/32 bites képernyő) így megszűntek; az Időrend a Nézet menüből és a
Ctrl+5-ről nyílik.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from PySide6.QtCore import QObject, Qt
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
    QTest.keyClick(
        window, Qt.Key.Key_4, Qt.KeyboardModifier.ControlModifier
    )
    _wait(
        qt_app,
        lambda: (
            (show := window.findChild(QObject, "slideshowView")) is not None
            and show.isVisible()
        ),
        "a Ctrl+4 nem indította el a vetítést",
    )
    show = _child(window, "slideshowView")
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
    # A valódi QScreen mélységét felülírjuk (régi 16/32 bites ág): a gomb
    # akkor sem jelenhet meg. A property megszűnése esetén a próba nem hasal el.
    show.setProperty("screenDepth", depth)


def _timeline_button_and_transition(window):
    timeline = window.findChild(QObject, "slideshowTimelineButton")
    return timeline, _child(window, "slideshowTransitionBox")


def _timeline_button_hidden(timeline) -> bool:
    return timeline is None or not timeline.isVisible()


def _start_timeline_slideshow(window, qt_app):
    QTest.keyClick(
        window, Qt.Key.Key_5, Qt.KeyboardModifier.ControlModifier
    )
    _wait(
        qt_app,
        lambda: window.property("timelineOpen") is True,
        "a Nézet ▸ Időrend belépése nem nyitotta meg a bemutatót",
    )
    timeline = _child(window, "timelineView")
    _wait(qt_app, timeline.isVisible, "a Ctrl+5 nem jelenítette meg az Időrendet")
    QTest.keyClick(timeline, Qt.Key.Key_Space)
    _wait(
        qt_app,
        lambda: window.findChild(QObject, "slideshowView") is not None
        and window.property("timelineSlideshowActive") is True,
        "az Időrend Space billentyűje nem indította el a vetítést",
    )
    controls = _child(window, "slideshowControls")
    controls.setProperty("shown", True)
    _wait(
        qt_app,
        lambda: controls.property("opacity") >= 0.99,
        "az Időrendből indított vetítés vezérlősávja nem jelent meg",
    )
    return _child(window, "slideshowView")


@pytest.mark.parametrize("depth", [16, 32, 24, 0])
def test_normal_slideshow_never_shows_timeline_always_shows_transition(
    qml_app_5653, qt_app, depth
):
    window, controller, _engine = qml_app_5653
    assert controller._get_settings().contains("Preferences/BigSlideshow2") is False
    show = _start_show(window, qt_app)
    _set_screen_depth(show, depth)

    timeline, transition = _timeline_button_and_transition(window)
    assert _timeline_button_hidden(timeline), (
        f"a Timeline gomb látszik a normál vetítésben ({depth} bit)"
    )
    assert transition.isVisible()

    if depth == 32 and (mappa := os.environ.get(KIADASKEP_MAPPA)):
        image = window.grabWindow()
        assert not image.isNull(), "a vetítő kiadásképe üres"
        output_dir = Path(mappa)
        output_dir.mkdir(parents=True, exist_ok=True)
        output = output_dir / "diavetites_normal_vezerlosav_7209.png"
        assert image.save(str(output), "PNG"), f"nem menthető a kiadáskép: {output}"


@pytest.mark.parametrize("depth", [16, 32])
def test_big_slideshow_disabled_still_shows_transition_only(
    qml_app_5653, qt_app, depth
):
    window, controller, _engine = qml_app_5653
    show = _start_show(window, qt_app)
    _set_screen_depth(show, depth)
    controller._get_settings().setValue("Preferences/BigSlideshow2", False)
    controller.statusChanged.emit()

    timeline, transition = _timeline_button_and_transition(window)
    assert _timeline_button_hidden(timeline)
    assert transition.isVisible()


@pytest.mark.parametrize("depth", [16, 32])
def test_timeline_started_slideshow_keeps_transition_only(
    qml_app_5653, qt_app, depth
):
    window, _controller, _engine = qml_app_5653
    show = _start_timeline_slideshow(window, qt_app)
    _set_screen_depth(show, depth)

    timeline, transition = _timeline_button_and_transition(window)
    assert _timeline_button_hidden(timeline)
    assert transition.isVisible()
