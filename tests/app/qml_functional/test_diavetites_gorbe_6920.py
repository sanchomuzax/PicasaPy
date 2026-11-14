"""A Dissolve az időből számolt Picasa-görbét használja (#6920)."""

from PySide6.QtCore import QObject, Qt
from PySide6.QtTest import QTest
import pytest

from support.qt_wait import varj_feltetelre


def _gyerek(gyoker, nev):
    obj = gyoker.findChild(QObject, nev)
    assert obj is not None, f"{nev} nem található"
    return obj


def test_a_dissolve_kockapontjai_a_vezerlo_gorbejet_hasznaljak(qml_app, qt_app):
    window, controller, _engine = qml_app
    controller.setSlideshowTransition("dissolve")
    controller.setSlideshowSeconds(3)
    QTest.keyClick(window, Qt.Key.Key_4, Qt.KeyboardModifier.ControlModifier)
    assert varj_feltetelre(
        qt_app,
        lambda: (
            (show := window.findChild(QObject, "slideshowView")) is not None
            and show.isVisible()
        ),
        masodperc=10.0,
    ), "a Ctrl+4 nem nyitotta meg a vetítést"

    show = _gyerek(window, "slideshowView")
    elozo = _gyerek(window, "slideshowPrevImage")
    aktualis = _gyerek(window, "slideshowImage")
    show.setProperty("playing", False)
    assert show.property("transitionMs") == 500
    assert show.property("dissolveTransitionMs") == 2000
    elozo.setProperty("opacity", 1.0)
    aktualis.setProperty("opacity", 0.0)

    show.setProperty("dissolveProgress", 0.5)
    qt_app.processEvents()
    assert aktualis.property("opacity") == pytest.approx(248 / 256, abs=1e-6)
    assert elozo.property("opacity") == pytest.approx(1.0, abs=1e-6)

    show.setProperty("dissolveProgress", 1.0)
    qt_app.processEvents()
    assert aktualis.property("opacity") == pytest.approx(1.0, abs=1e-6)

    controller.setSlideshowSeconds(6)
    assert varj_feltetelre(qt_app, lambda: show.property("seconds") == 6)
    assert show.property("dissolveTransitionMs") == 4000
    show.setProperty("dissolveProgress", 0.5)
    qt_app.processEvents()
    assert aktualis.property("opacity") == pytest.approx(248 / 256, abs=1e-6)
