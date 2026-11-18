"""#7190: a kézi léptetés lista-széli viselkedése független az ismétléstől.

A mérce a docs/specs/paritas-ellenorzes.md #7060/D7 része: a valódi Picasa
kézi előre lépéskor az utolsó képről az elsőre fordul, hátra pedig az első
képen marad. A teszt a teljes alkalmazásban, valódi egérkattintással méri a
két vezérlőgombot, ismétlés be- és kikapcsolt állapotában.

# rontás-kontroll: a régi hurokfüggő kézi ág → a javítás nélküli futás piros (FF)
"""

from __future__ import annotations

import pytest
from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QWindow
from PySide6.QtQuick import QQuickItem
from PySide6.QtTest import QTest

from support.qt_wait import varj_feltetelre


def _child(parent, name):
    obj = parent.findChild(QQuickItem, name)
    assert obj is not None, f"{name} nem található"
    return obj


def _kattint(window, qt_app, button):
    assert button.isVisible(), f"a(z) {button.objectName()} gomb nem látható"
    center = button.mapToScene(button.boundingRect().center())
    QTest.mouseClick(
        window,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        QPoint(round(center.x()), round(center.y())),
    )
    qt_app.processEvents()


@pytest.mark.parametrize(
    "loop_enabled", [False, True], ids=["ismetles-ki", "ismetles-be"]
)
@pytest.mark.parametrize(
    "window_height_delta", [-5, 0, 5], ids=["alacsonyabb", "alap", "magasabb"]
)
def test_kezzel_elore_az_utolso_keprol_korbe_hatra_az_elson_marad(
    qml_app, qt_app, loop_enabled, window_height_delta
):
    window, controller, _engine = qml_app
    window.show()
    window.requestActivate()
    window.setVisibility(QWindow.Visibility.Windowed)

    target_height = window.height() + window_height_delta
    window.resize(window.width(), target_height)
    assert varj_feltetelre(
        qt_app, lambda: window.height() == target_height, 3.0
    ), f"az ablak magassága nem lett {target_height}: {window.height()}"

    controller.setSlideshowLoop(loop_enabled)
    controller.setSlideshowSeconds(30)
    window.startSlideshow(1, True)
    show = _child(window, "slideshowView")
    controls = _child(window, "slideshowControls")
    previous = _child(window, "slideshowPrevButton")
    next_button = _child(window, "slideshowNextButton")
    clicked_buttons = []
    previous.clicked.connect(lambda: clicked_buttons.append("previous"))
    next_button.clicked.connect(lambda: clicked_buttons.append("next"))

    assert varj_feltetelre(
        qt_app,
        lambda: show.property("visible")
        and show.property("currentIndex") == 1
        and controls.property("opacity") > 0.99,
        3.0,
    ), "a vetítés nem állt készen a kézi léptetésre"
    assert show.property("loop") is loop_enabled

    try:
        _kattint(window, qt_app, next_button)
        assert clicked_buttons == ["next"], "az előre gomb nem kapott valódi kattintást"
        assert varj_feltetelre(
            qt_app, lambda: show.property("currentIndex") == 0, 3.0
        ), "kézi előrelépéskor az utolsó képről nem fordult az elsőre"
        assert show.property("visible") is True, "a kézi léptetés bezárta a vetítést"

        _kattint(window, qt_app, previous)
        assert clicked_buttons == ["next", "previous"], (
            "a hátra gomb nem kapott valódi kattintást"
        )
        assert show.property("currentIndex") == 0, (
            "kézi hátralépéskor az első képről elmozdult, pedig ott kell maradnia"
        )
        assert show.property("visible") is True
    finally:
        if show.property("visible"):
            show.stop()
