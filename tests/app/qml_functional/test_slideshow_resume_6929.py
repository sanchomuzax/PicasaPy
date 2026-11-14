"""#6929: normál vetítés folytatása azonnal lép, majd diaidőnként vált."""

from __future__ import annotations

import time

from PySide6.QtCore import QObject, Qt
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


def _space(window) -> None:
    QTest.keyClick(window, Qt.Key.Key_Space)


def _to_url(value) -> str:
    return value.toString() if hasattr(value, "toString") else str(value)


def _start_slideshow(
    window, qt_app, index: int, paused: bool, window_height_delta: int = 0
):
    window.resize(window.width(), window.height() + window_height_delta)
    window.show()
    window.setVisibility(QWindow.Visibility.Windowed)
    window.startSlideshow(index, paused)
    show = _child(window, "slideshowView")
    _wait(qt_app, lambda: show.property("visible"), "a vetítés nem indult el")
    return show


@pytest.mark.parametrize("window_height_delta", [-5, 0, 5])
def test_folytataskor_azonnal_lep_es_a_kovetkezo_diaido_mulva_jon(
    qml_app, qt_app, window_height_delta
):
    window, controller, _engine = qml_app
    controller.setSlideshowSeconds(1)
    controller.setSlideshowLoop(True)
    show = _start_slideshow(
        window, qt_app, 0, paused=False, window_height_delta=window_height_delta
    )

    _space(window)
    _wait(qt_app, lambda: not show.property("playing"), "a Space nem szüneteltetett")
    _wait(
        qt_app,
        lambda: bool(
            _to_url(_child(window, "slideshowImage").property("source"))
        ),
        "az első fotó forrása nem töltődött be",
    )
    _space(window)
    qt_app.processEvents()

    assert show.property("playing") is True
    assert show.property("currentIndex") == 1, (
        "a folytatás nem lépett azonnal a következő fotóra"
    )
    assert _child(window, "slideshowTransition").property("running") is True, (
        "az azonnali lépés nem indította el a beállított átmenetet"
    )

    timer = _child(window, "slideshowTimer")
    interval_ms = show.property("intervalMs")
    assert timer.property("interval") == interval_ms
    assert timer.property("running") is True
    kovetkezo_lepes_kezdete = time.monotonic()
    assert varj_feltetelre(
        qt_app, lambda: show.property("currentIndex") == 0, 3.0
    ), (
        "az időzítő nem lépett a következő fotóra "
        f"(visible={show.property('visible')}, "
        f"playing={show.property('playing')}, "
        f"running={timer.property('running')}, "
        f"interval={timer.property('interval')}, "
        f"loop={show.property('loop')})"
    )
    eltelt_ms = (time.monotonic() - kovetkezo_lepes_kezdete) * 1000
    assert interval_ms - 150 <= eltelt_ms <= interval_ms + 750, (
        f"a következő lépés {eltelt_ms:.0f} ms után jött, "
        f"az időzítő {interval_ms} ms-os üteme helyett"
    )


@pytest.mark.parametrize("window_height_delta", [-5, 0, 5])
@pytest.mark.parametrize(
    ("loop", "vart_index", "vart_lathato", "vart_playing"),
    [(True, 0, True, True), (False, 1, False, False)],
)
def test_utolso_foto_folytatasakor_megmarad_a_lista_szabaly(
    qml_app, qt_app, loop, vart_index, vart_lathato, vart_playing,
    window_height_delta
):
    window, _controller, _engine = qml_app
    show = _start_slideshow(
        window, qt_app, 1, paused=True, window_height_delta=window_height_delta
    )
    show.setProperty("loop", loop)

    _space(window)
    qt_app.processEvents()

    assert show.property("currentIndex") == vart_index
    assert show.property("visible") is vart_lathato
    assert show.property("playing") is vart_playing
