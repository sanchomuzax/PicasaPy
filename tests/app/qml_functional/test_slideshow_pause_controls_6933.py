"""A Space-szünet a vezérlősávot azonnal előhozza és rögzíti (#6933)."""

from PySide6.QtCore import QEventLoop, QObject, QPoint, QTimer, Qt
from PySide6.QtGui import QWindow
from PySide6.QtTest import QTest
import pytest

from support.qt_wait import varj_feltetelre


def _child(parent, name):
    obj = parent.findChild(QObject, name)
    assert obj is not None, f"{name} nem található"
    return obj


def _wait_elapsed(qt_app, milliseconds: int) -> None:
    """Eseményhurkot futtat határidőig, rövid QTimer-szakaszokban."""
    deadline = QTimer()
    deadline.setSingleShot(True)
    loop = QEventLoop()
    deadline.timeout.connect(loop.quit)
    deadline.start(milliseconds)
    loop.exec()
    qt_app.processEvents()


@pytest.mark.parametrize("window_height_delta", (-5, 0, 5))
def test_space_szunet_azonnal_megjeleniti_es_a_folytatas_azonnal_elrejti(
    qml_app, qt_app, window_height_delta
):
    window, _controller, _engine = qml_app
    window.show()
    window.requestActivate()
    window.setVisibility(QWindow.Visibility.Windowed)
    target_height = window.height() + window_height_delta
    window.resize(window.width(), target_height)
    assert varj_feltetelre(
        qt_app, lambda: window.height() == target_height, 3.0
    ), f"az ablak magassága nem lett {target_height}: {window.height()}"

    window.startSlideshow(0, False)
    show = _child(window, "slideshowView")
    controls = _child(window, "slideshowControls")
    hide_timer = _child(window, "slideshowHideTimer")
    hover = _child(window, "slideshowControlsHover")
    assert varj_feltetelre(
        qt_app,
        lambda: show.property("visible") and show.property("playing"),
        3.0,
    ), "a normál vetítés nem indult el"

    QTest.keyClick(window, Qt.Key.Key_Space)
    assert show.property("playing") is False
    assert controls.property("shown") is True
    assert float(controls.property("opacity")) == pytest.approx(1.0, abs=1e-6)
    assert hide_timer.property("running") is False

    # A szünet alatti mozgás és a sáv fölötti lebegés nem indít elrejtést.
    window_center = QPoint(window.width() // 3, window.height() // 3)
    QTest.mouseMove(window, window_center)
    qt_app.processEvents()
    assert controls.property("shown") is True
    assert float(controls.property("opacity")) == pytest.approx(1.0, abs=1e-6)
    assert hide_timer.property("running") is False

    controls_center = controls.mapToScene(
        controls.boundingRect().center()
    ).toPoint()
    QTest.mouseMove(window, controls_center)
    assert varj_feltetelre(
        qt_app, lambda: hover.property("hovered") is True, 2.0
    ), "a mutató nem került a vezérlősáv fölé"
    assert controls.property("shown") is True
    assert hide_timer.property("running") is False

    QTest.mouseMove(window, window_center)
    qt_app.processEvents()
    assert controls.property("shown") is True
    assert hide_timer.property("running") is False
    _wait_elapsed(qt_app, 3000)
    assert controls.property("shown") is True
    assert float(controls.property("opacity")) == pytest.approx(1.0, abs=1e-6)
    assert hide_timer.property("running") is False

    paused_index = show.property("currentIndex")
    QTest.keyClick(window, Qt.Key.Key_Space)
    assert show.property("playing") is True
    assert show.property("currentIndex") == paused_index + 1
    assert controls.property("shown") is False
    assert float(controls.property("opacity")) == pytest.approx(
        1 / 256, abs=1e-6
    )
    assert hide_timer.property("running") is False
