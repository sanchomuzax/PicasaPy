"""QML-funkcionális tesztek: busy-jelzés az alsó kék sávban (#70, #505).

A fény-csík (busySweep) a controller.isWorking-re köt; az animátor csak
látható (busy) állapotban fut, idle-ben a csík el sem látszik. A nézőt és
az image provider valós betöltését nem érintjük (ld. #53).

#505: az `isWorking` mostantól a KÖZÖS `AppBusyRegistry`-t
(`busy_registry.py`) olvassa — küszöbölt (rövid munkánál nem villan fel) és
minimális láthatóságú (ha megjelent, nem villog el azonnal). A tesztek ezt
a küszöböt/pufferelt láthatóságot APRÓRA (néhány ms-re) állítják, hogy
determinisztikusan, gyorsan lehessen várni rá — a valódi 300/500 ms-os
alapértékek indoklása a `busy_registry.py` modul-docstringjében van."""

import time

import pytest
from PySide6.QtCore import QObject

from picasapy.app import busy_registry as busy_registry_module
from picasapy.app.busy_registry import get_app_busy_registry, reset_app_busy_registry

# Tesztbeli küszöb/min-láthatóság — kicsi, de nem nulla, hogy a "rövid
# munka nem gyújt" eset (SHOW_DELAY_MS) is tesztelhető maradjon ÉBER
# várakozással, valódi időzítő-tüzeléssel (nem csak logikailag).
_TEST_SHOW_DELAY_MS = 40
_TEST_MIN_VISIBLE_MS = 60


@pytest.fixture(autouse=True)
def _small_busy_timings(monkeypatch):
    """A küszöb/min-láthatóság apróra állítása ELŐBB (friss regisztrátum
    kell hozzá, mert a konstansokat csak a `_on_begin`/`_on_show_timeout`
    hívások pillanatában olvassa be) + tiszta regisztrátum minden teszthez,
    hogy egyik teszt futó időzítője/számlálója ne szivárogjon át a
    következőbe (a regisztrátum modul-szintű szingleton, ld.
    `busy_registry.get_app_busy_registry`)."""
    monkeypatch.setattr(busy_registry_module, "SHOW_DELAY_MS", _TEST_SHOW_DELAY_MS)
    monkeypatch.setattr(busy_registry_module, "MIN_VISIBLE_MS", _TEST_MIN_VISIBLE_MS)
    reset_app_busy_registry()
    yield
    reset_app_busy_registry()


def _child(window, name):
    obj = window.findChild(QObject, name)
    assert obj is not None, f"{name} nem található"
    return obj


def _wait_until(qt_app, predicate, timeout_s=2.0):
    """Aktív várakozás valódi idő-előrehaladással, közben eseményeket
    dolgozva fel (a QTimer-alapú küszöb/min-láthatóság csak processEvents
    alatt tüzel) — `True`, ha a `predicate()` a határidőn belül igazzá vált."""
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        qt_app.processEvents()
        if predicate():
            return True
        time.sleep(0.005)
    return False


class TestBusySweep:
    def test_short_burst_never_lights_up(self, qml_app, qt_app):
        """A küszöb alatt kezdődő ÉS véget érő munka NE villantsa fel a
        csíkot (#505 kérés: rövid műveletnél ne villogjon)."""
        window, controller, _lib, _engine = qml_app
        sweep = _child(window, "busySweep")
        assert _wait_until(qt_app, lambda: not controller.isWorking)

        registry = get_app_busy_registry()
        registry.begin()
        registry.end()  # jóval a küszöb (40 ms) előtt lezárva

        # a teljes küszöbidőn túl várunk, és mindvégig hamisnak kell maradnia
        deadline = time.monotonic() + (_TEST_SHOW_DELAY_MS / 1000) * 3
        while time.monotonic() < deadline:
            qt_app.processEvents()
            assert controller.isWorking is False
            assert sweep.property("visible") is False
            time.sleep(0.005)

    def test_long_job_lights_up_with_minimum_visibility(self, qml_app, qt_app):
        """A küszöbön túl futó munka felgyújtja a csíkot, és a minimális
        láthatósági ablak alatt AKKOR IS látszik, ha a munka közben véget
        ér (#505 kérés: ne villogjon el azonnal)."""
        window, controller, _lib, _engine = qml_app
        sweep = _child(window, "busySweep")
        assert _wait_until(qt_app, lambda: not controller.isWorking)

        registry = get_app_busy_registry()
        registry.begin()
        assert _wait_until(qt_app, lambda: controller.isWorking is True), (
            "a küszöbön túl futó munka nem gyújtotta fel a csíkot"
        )
        assert sweep.property("visible") is True

        registry.end()  # a munka véget ér, de a min-láthatóság még tart
        assert controller.isWorking is True
        assert sweep.property("visible") is True

        assert _wait_until(qt_app, lambda: controller.isWorking is False), (
            "a csík a minimális láthatóság lejárta után sem tűnt el"
        )
        assert sweep.property("visible") is False

    def test_sweep_follows_is_working(self, qml_app, qt_app):
        window, controller, _lib, _engine = qml_app
        sweep = _child(window, "busySweep")
        assert _wait_until(qt_app, lambda: not controller.isWorking)

        controller._provider.activeCountChanged.emit(1)
        assert _wait_until(qt_app, lambda: controller.isWorking is True)
        assert sweep.property("visible") is True
        controller._provider.activeCountChanged.emit(0)
        assert _wait_until(qt_app, lambda: controller.isWorking is False)
        assert sweep.property("visible") is False

    def test_sync_job_shows_sweep(self, qml_app, qt_app):
        from PySide6.QtCore import QEventLoop, QTimer

        window, controller, _lib, _engine = qml_app
        sweep = _child(window, "busySweep")
        loop = QEventLoop()
        controller.syncFinished.connect(loop.quit)
        controller.rescan()
        QTimer.singleShot(5000, loop.quit)
        loop.exec()
        # a szinkron véget ért — a küszöb+min-láthatóság lejárta után a
        # csík mindenképp visszaáll láthatatlanra (a teszt-könyvtár
        # 2 apró képe alatt lehet, hogy a küszöb miatt fel sem villant)
        assert _wait_until(qt_app, lambda: controller.isWorking is False)
        assert sweep.property("visible") is False
