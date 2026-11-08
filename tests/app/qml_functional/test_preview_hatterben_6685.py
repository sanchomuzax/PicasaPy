"""Valódi QML-kattintással ellenőrzi az élő szerkesztő-előnézetet (#6685)."""

from __future__ import annotations

import math
import threading
import time

import pytest
from PIL import Image
from PySide6.QtCore import QObject, QPointF, Qt, QTimer
from PySide6.QtTest import QTest

from tests.support.varakozas import var_feltetelre


def _item(window, name):
    item = window.findChild(QObject, name)
    assert item is not None, f"{name} nem található"
    return item


def _click(window, item, qt_app):
    center = item.mapToScene(
        QPointF(float(item.property("width")) / 2, float(item.property("height")) / 2)
    )
    QTest.mouseClick(
        window,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        center.toPoint(),
    )
    qt_app.processEvents()


def _pixel_signature(image):
    return tuple(
        image.pixelColor(x * (image.width() - 1) // 31,
                         y * (image.height() - 1) // 31).rgba()
        for y in range(32)
        for x in range(32)
    )


def _check_timer_during_render(tick_times, interval, label):
    start, end = interval
    expected = max(1, int((end - start) / 0.05))
    tick_count = sum(start <= tick <= end for tick in tick_times)
    assert tick_count >= math.ceil(expected * 0.8), (
        f"{label}: a QML 50 ms-os időzítő {tick_count}/{expected} alkalommal futott "
        f"a render ideje alatt; tickek={tuple(round(tick - start, 3) for tick in tick_times if start <= tick <= end)}"
    )


@pytest.mark.parametrize("height", (795, 800, 805), ids=("minus-5", "base", "plus-5"))
def test_valodi_kattintas_kozben_el_a_felulet_es_frissul_a_kep(
    qml_app, qt_app, tmp_path, monkeypatch, height
):
    window, _library_controller, _engine = qml_app
    window.setProperty("width", 800)
    window.setProperty("height", height)
    # A 2560 px széles minta a feladatban mért előnézeti méretet használja.
    photo_path = tmp_path / "kepek" / "a.jpg"
    image = Image.effect_noise((2560, 1600), 64).convert("RGB")
    image.save(photo_path, "JPEG", quality=92)

    window.setProperty("viewerOpen", True)
    viewer = _item(window, "photoViewer")
    viewer.setProperty("currentIndex", 0)
    panel = _item(window, "viewerEditorPanel")
    assert var_feltetelre(
        qt_app, lambda: panel.property("visible") is True, 5.0
    ), "a szerkesztőpanel nem nyílt meg"
    edit = viewer.property("editCtl")
    assert edit.waitForBackgroundWorkers(10.0)
    provider = edit._provider
    viewer_image = _item(window, "viewerImage")
    assert var_feltetelre(
        qt_app, lambda: float(viewer_image.property("implicitWidth")) > 0, 5.0
    ), "a kiinduló fotó nem töltődött be"
    before = _pixel_signature(provider.requestImage(edit._kulcs, None, None))

    timer_ticks = []
    timer = QTimer(window)
    timer.setInterval(50)
    timer.setTimerType(Qt.TimerType.PreciseTimer)
    timer.timeout.connect(lambda: timer_ticks.append(time.monotonic()))
    timer.start()
    baseline_start = time.monotonic()
    assert var_feltetelre(
        qt_app, lambda: time.monotonic() - baseline_start >= 0.5, 1.5
    ), "az időzítő alapmérése nem futott le"
    baseline_ticks = len(timer_ticks)
    timer.stop()
    timer_ticks.clear()
    assert baseline_ticks >= 8, (
        f"az időzítő alapmérése csak {baseline_ticks}/10 jelzést kapott"
    )

    panel.setProperty("activeTab", 2)
    qt_app.processEvents()
    original_register = provider.register
    render_intervals = []
    render_threads = []
    render_started = threading.Event()

    def observed_register(**request):
        start = time.monotonic()
        render_threads.append(threading.current_thread().name)
        render_started.set()
        original_register(**request)
        render_intervals.append((start, time.monotonic()))

    monkeypatch.setattr(provider, "register", observed_register)

    # A csempe megnyitása a valódi EditorPanelen át kéri a radblur előnézetét.
    # Az időzítő már az interakció előtt fut: szinkron rendernél a kattintás
    # visszatérése után nem számítjuk a késve kézbesített időzítőeseményeket.
    timer.start()
    _click(window, _item(window, "effectRadblur"), qt_app)
    assert panel.property("paramPanelActive") is True
    assert var_feltetelre(qt_app, render_started.is_set, 3.0), (
        "a kattintás nem indított előnézeti renderelést"
    )
    if not render_intervals:
        assert float(viewer_image.property("implicitWidth")) > 0, (
            "a régi előnézeti kép eltűnt az új render befejezéséig"
        )
    assert var_feltetelre(qt_app, lambda: len(render_intervals) >= 1, 30.0)
    timer.stop()
    assert render_threads[0] != threading.main_thread().name
    _check_timer_during_render(
        timer_ticks,
        (render_intervals[0][0], render_intervals[0][1]),
        "csempekattintás",
    )

    # A tényleges csúszkahúzás után is a legutolsó render képe maradjon látható.
    slider = _item(window, "effectParamSlider0")
    render_started.clear()
    render_baseline = len(render_intervals)
    worker_baseline = len(render_threads)
    timer.start()
    start = slider.mapToScene(QPointF(float(slider.property("width")) * 0.5,
                                      float(slider.property("height")) / 2)).toPoint()
    end = slider.mapToScene(QPointF(float(slider.property("width")) * 0.9,
                                    float(slider.property("height")) / 2)).toPoint()
    QTest.mousePress(window, Qt.MouseButton.LeftButton, pos=start)
    QTest.mouseMove(window, end)
    QTest.mouseRelease(window, Qt.MouseButton.LeftButton, pos=end)
    qt_app.processEvents()
    assert var_feltetelre(qt_app, render_started.is_set, 3.0), (
        "a csúszkahúzás nem indított új előnézeti rendert"
    )
    if len(render_intervals) <= render_baseline:
        assert float(viewer_image.property("implicitWidth")) > 0, (
            "a kép eltűnt a csúszkahúzás előnézetének renderelése közben"
        )
    assert var_feltetelre(qt_app, lambda: len(render_intervals) > render_baseline, 30.0), (
        "a csúszkahúzás nem kért új előnézetet"
    )
    timer.stop()
    assert render_threads[worker_baseline] != threading.main_thread().name
    _check_timer_during_render(
        timer_ticks,
        (render_intervals[-1][0], render_intervals[-1][1]),
        "csúszkahúzás",
    )
    assert var_feltetelre(
        qt_app,
        lambda: float(viewer_image.property("implicitWidth")) > 0,
        3.0,
    ), "a végső előnézeti kép nem töltődött be"
    after = _pixel_signature(provider.requestImage(edit._kulcs, None, None))
    assert before != after, "a végső előnézeti kép nem változott meg"
