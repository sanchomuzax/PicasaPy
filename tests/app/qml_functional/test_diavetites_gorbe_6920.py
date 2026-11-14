"""A Dissolve görbéje csak az Időrend-bemutatóé (#6920, #6926)."""

from PySide6.QtCore import QElapsedTimer, QObject, Qt
from PySide6.QtTest import QTest
import pytest

from support.qt_wait import varj_feltetelre


def _gyerek(gyoker, nev):
    obj = gyoker.findChild(QObject, nev)
    assert obj is not None, f"{nev} nem található"
    return obj


def _normal_vetites(window, controller, qt_app):
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
    show.setProperty("playing", False)
    return show


def test_a_normal_vetites_dissolve_ja_nem_a_gorbet_hasznalja(qml_app, qt_app):
    """#6926: a job-683 szerint a normál vetítés áttűnése nem a 0x008001c0 görbe."""
    window, controller, _engine = qml_app
    show = _normal_vetites(window, controller, qt_app)
    aktualis = _gyerek(window, "slideshowImage")
    assert show.property("timelineSlideshow") is False
    assert show.property("_gorbesDissolve") is False
    # A transitionMs a többi átmeneté, a Dissolve saját ideje 1 s.
    assert show.property("transitionMs") == 500
    assert show.property("dissolveTransitionMs") == 1000
    aktualis.setProperty("opacity", 0.3)
    show.setProperty("dissolveProgress", 0.5)
    qt_app.processEvents()
    assert aktualis.property("opacity") == pytest.approx(0.5, abs=1 / 256)


def test_a_normal_dissolve_ideje_1000ms_a_diaidotol_fuggetlenul(
    qml_app, qt_app
):
    window, controller, _engine = qml_app
    show = _normal_vetites(window, controller, qt_app)
    animation = _gyerek(window, "slideshowTransition")

    for masodperc in (1, 3, 5):
        controller.setSlideshowSeconds(masodperc)
        assert varj_feltetelre(
            qt_app, lambda masodperc=masodperc: show.property("seconds") == masodperc,
            masodperc=10.0,
        )
        assert show.property("dissolveTransitionMs") == 1000

        meres = QElapsedTimer()
        meres.start()
        show.setProperty("currentIndex", 1 - int(show.property("currentIndex")))
        assert varj_feltetelre(
            qt_app, lambda: animation.property("running"), masodperc=10.0
        )
        assert varj_feltetelre(
            qt_app, lambda: not animation.property("running"), masodperc=10.0
        )
        eltelt_ms = meres.elapsed()
        assert 850 <= eltelt_ms <= 1200, (
            f"{masodperc} s diaidőnél a Dissolve {eltelt_ms} ms volt"
        )


def test_a_normal_dissolve_egyenes_es_a_kimeno_kep_vegig_atlatszatlan(
    qml_app, qt_app
):
    window, controller, _engine = qml_app
    show = _normal_vetites(window, controller, qt_app)
    elozo = _gyerek(window, "slideshowPrevImage")
    aktualis = _gyerek(window, "slideshowImage")
    animation = _gyerek(window, "slideshowTransition")

    show.setProperty("currentIndex", 1)
    assert varj_feltetelre(qt_app, lambda: animation.property("running"))

    for cel in (0.25, 0.5, 0.75):
        assert varj_feltetelre(
            qt_app,
            lambda cel=cel: show.property("dissolveProgress") >= cel,
            masodperc=10.0,
        )
        haladas = float(show.property("dissolveProgress"))
        varhato_alfa = int(256 * haladas + 0.5) / 256
        assert aktualis.property("opacity") == pytest.approx(
            varhato_alfa, abs=1 / 256
        )
        assert elozo.property("opacity") == pytest.approx(1.0, abs=1e-6)

    animation.stop()

    for haladas, alfa in (
        (0.0, 0.0),
        (0.25, 0.25),
        (0.5, 0.5),
        (0.75, 0.75),
        (1.0, 1.0),
    ):
        show.setProperty("dissolveProgress", haladas)
        qt_app.processEvents()
        assert aktualis.property("opacity") == pytest.approx(alfa, abs=1 / 256)
        assert elozo.property("opacity") == pytest.approx(1.0, abs=1e-6)


def test_az_idorend_dissolve_ja_a_vezerlo_gorbejet_hasznalja(qml_app, qt_app):
    window, controller, _engine = qml_app
    show = _normal_vetites(window, controller, qt_app)
    show.setProperty("timelineSlideshow", True)
    assert show.property("_gorbesDissolve") is True
    elozo = _gyerek(window, "slideshowPrevImage")
    aktualis = _gyerek(window, "slideshowImage")
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
