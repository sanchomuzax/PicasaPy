"""Az Időrendből szüneteltetve indított vetítés első felúszása (#6920)."""

from urllib.parse import parse_qs, unquote, urlsplit

from PySide6.QtCore import QMetaObject, QObject, Qt
from PySide6.QtGui import QWindow
from PySide6.QtTest import QTest
import pytest

from support.qt_wait import varj_feltetelre


def _child(parent, name):
    obj = parent.findChild(QObject, name)
    assert obj is not None, f"{name} nem található"
    return obj


def _wait(qt_app, predicate, message: str) -> None:
    assert varj_feltetelre(qt_app, predicate, 3.0), message


def _to_url(value) -> str:
    return value.toString() if hasattr(value, "toString") else str(value)


def _toggle_pause(qt_app, show) -> None:
    QMetaObject.invokeMethod(show, "togglePause", Qt.ConnectionType.DirectConnection)
    qt_app.processEvents()


def _start_timeline_slideshow(window, qt_app, window_height_delta: int):
    window.resize(window.width(), window.height() + window_height_delta)
    window.show()
    window.setVisibility(QWindow.Visibility.Windowed)
    QTest.keyClick(window, Qt.Key.Key_5, Qt.KeyboardModifier.ControlModifier)
    _wait(qt_app, lambda: window.property("timelineOpen"), "az Időrend nem nyílt meg")
    timeline = _child(window, "timelineView")
    _wait(qt_app, timeline.isVisible, "az Időrend ablaka nem látható")
    QTest.keyClick(timeline, Qt.Key.Key_Space)
    _wait(
        qt_app,
        lambda: (
            (show := window.findChild(QObject, "slideshowView")) is not None
            and show.property("visible")
        ),
        "az Időrend Space billentyűje nem indította el a vetítést",
    )
    return _child(window, "slideshowView")


@pytest.mark.parametrize("window_height_delta", [-5, 0, 5])
def test_az_idorend_elso_folytatasa_a_cimkartyabol_dissolve_gorbevel(
    qml_app, qt_app, window_height_delta
):
    window, _controller, _engine = qml_app
    show = _start_timeline_slideshow(window, qt_app, window_height_delta)
    previous = _child(window, "slideshowPrevImage")
    current = _child(window, "slideshowImage")
    animation = _child(window, "slideshowTransition")

    assert show.property("playing") is False
    assert show.property("_cimkartyaFuggo") is True
    assert show.property("dissolveTransitionMs") == 2000

    _toggle_pause(qt_app, show)
    _wait(
        qt_app,
        lambda: _to_url(previous.property("source")).startswith(
            "image://slideshowlabelcard/"
        ),
        "az első folytatás nem a Python-címkártyát állította be kimenő képnek",
    )
    _wait(qt_app, lambda: animation.property("running"), "a felúszás nem indult el")
    animation.stop()
    show.setProperty("dissolveProgress", 0.0)
    qt_app.processEvents()
    assert previous.property("opacity") == pytest.approx(1.0)
    assert current.property("opacity") == pytest.approx(0.0)

    url = urlsplit(_to_url(previous.property("source")))
    query = parse_qs(url.query)
    assert query.get("name") == [show.property("_timelineCollectionName")]
    model = window.property("timelineSlideshowModel")
    assert unquote(url.path[1:]) == model.filePathAt(0)

    show.setProperty("dissolveProgress", 0.5)
    qt_app.processEvents()
    assert current.property("opacity") == pytest.approx(248 / 256, abs=1e-6)
    assert previous.property("opacity") == pytest.approx(1.0, abs=1e-6)
    show.setProperty("dissolveProgress", 1.0)
    qt_app.processEvents()
    assert current.property("opacity") == pytest.approx(1.0, abs=1e-6)


@pytest.mark.parametrize("window_height_delta", [-5, 0, 5])
def test_a_nem_idorendi_szuneteltetett_inditas_nem_kap_cimkartyat(
    qml_app, qt_app, window_height_delta
):
    window, _controller, _engine = qml_app
    window.resize(window.width(), window.height() + window_height_delta)
    window.show()
    window.setVisibility(QWindow.Visibility.Windowed)
    window.startSlideshow(0, True)
    _wait(
        qt_app,
        lambda: (
            (show := window.findChild(QObject, "slideshowView")) is not None
            and show.property("visible")
        ),
        "a normál szüneteltetett vetítés nem indult el",
    )
    show = _child(window, "slideshowView")
    assert show.property("_cimkartyaFuggo") is False

    _toggle_pause(qt_app, show)
    _wait(qt_app, lambda: show.property("playing"), "a normál vetítés nem folytatódott")
    assert not _to_url(_child(window, "slideshowPrevImage").property("source")).startswith(
        "image://slideshowlabelcard/"
    )
