"""`AppBusyRegistry` (#505) — a közös, alkalmazás-szintű busy-nyilvántartás
egységtesztjei: számláló nullára záródása (párhuzamos munkák, hibával
végződő munka is), és a küszöb/minimális-láthatóság viselkedése.

A tesztek a `qt_app` (session-scope, `tests/app/conftest.py`) fixture-t
használják — a `QTimer`-eknek futó eseményhurokra van szükségük ahhoz,
hogy egyáltalán tüzeljenek."""

from __future__ import annotations

import threading
import time

import pytest

from picasapy.app import busy_registry as busy_registry_module
from picasapy.app.busy_registry import get_app_busy_registry, reset_app_busy_registry
from picasapy.app.worker_thread import BackgroundWorkerMixin

_TEST_SHOW_DELAY_MS = 30
_TEST_MIN_VISIBLE_MS = 50


@pytest.fixture(autouse=True)
def _small_timings(monkeypatch):
    """Apró küszöb/min-láthatóság + tiszta szingleton minden teszthez (a
    regisztrátum modul-szintű, ld. `busy_registry.get_app_busy_registry`)."""
    monkeypatch.setattr(busy_registry_module, "SHOW_DELAY_MS", _TEST_SHOW_DELAY_MS)
    monkeypatch.setattr(busy_registry_module, "MIN_VISIBLE_MS", _TEST_MIN_VISIBLE_MS)
    reset_app_busy_registry()
    yield
    reset_app_busy_registry()


class _Worker(BackgroundWorkerMixin):
    """Minimál controller-utánzat: csak a mixint gyakorolja."""


def _wait_until(qt_app, predicate, timeout_s=2.0):
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        qt_app.processEvents()
        if predicate():
            return True
        time.sleep(0.005)
    return False


class TestCounterReachesZero:
    def test_single_begin_end_returns_to_zero(self, qt_app):
        registry = get_app_busy_registry()
        registry.begin()
        assert registry.activeCount == 1
        registry.end()
        assert registry.activeCount == 0

    def test_end_without_begin_does_not_go_negative(self, qt_app):
        """Védőkorlát: egy véletlen extra `end()` ne vigye negatívba a
        számlálót (ami a `visible` logikát is elronthatná)."""
        registry = get_app_busy_registry()
        registry.end()
        assert registry.activeCount == 0

    def test_concurrent_jobs_stay_busy_until_all_done(self, qt_app):
        """Két párhuzamos munka: a csík csak akkor tűnhet el, ha
        MINDKETTŐ lezárult, nem az elsőnél."""
        registry = get_app_busy_registry()
        registry.begin()
        registry.begin()
        assert registry.activeCount == 2
        assert _wait_until(qt_app, lambda: registry.visible is True)

        registry.end()  # csak az egyik zárul le
        qt_app.processEvents()
        assert registry.activeCount == 1
        assert registry.visible is True, "a második munka még fut — nem tűnhet el"

        registry.end()  # a második is lezárul
        assert _wait_until(qt_app, lambda: registry.visible is False)
        assert registry.activeCount == 0

    @pytest.mark.filterwarnings(
        "ignore::pytest.PytestUnhandledThreadExceptionWarning"
    )
    def test_failing_worker_still_ends_its_job(self, qt_app):
        """(j)/(1): egy KIVÉTELLEL leálló háttérmunka is lezárja a
        bejegyzést — különben a csík örökre pörögne. A
        `BackgroundWorkerMixin._start_background` `try`/`finally`-vel zárja
        a regisztrátum-bejelentkezést, függetlenül attól, hogy a `target`
        kivétellel áll-e le. A `filterwarnings` a SZÁNDÉKOS teszt-kivétel
        szál-szintű figyelmeztetését némítja — maga a kivétel a teszt lényege,
        nem hibajel."""
        worker_owner = _Worker()

        def failing_target():
            raise RuntimeError("szándékos teszt-hiba")

        worker_owner._start_background(failing_target, name="test-failing")
        assert worker_owner.waitForBackgroundWorkers(5.0), "a szál nem állt le"

        registry = get_app_busy_registry()
        assert _wait_until(qt_app, lambda: registry.activeCount == 0), (
            "a hibával leálló munka NEM zárta le a busy-bejegyzést — a csík "
            "örökre pörögne"
        )
        assert _wait_until(qt_app, lambda: registry.visible is False)

    def test_multiple_background_threads_all_release(self, qt_app):
        """Több, VALÓDI háttérszálról induló begin()/end() is helyesen
        nullázódik — a `begin`/`end` szál-biztosságának (queued jelzés,
        ld. modul-docstring) gyakorlati próbája."""
        registry = get_app_busy_registry()

        def worker(barrier: threading.Barrier):
            registry.begin()
            barrier.wait(timeout=5.0)
            registry.end()

        barrier = threading.Barrier(3)
        threads = [
            threading.Thread(target=worker, args=(barrier,), daemon=True)
            for _ in range(3)
        ]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=5.0)
            assert not thread.is_alive()

        assert _wait_until(qt_app, lambda: registry.activeCount == 0)


class TestThreshold:
    def test_short_job_does_not_light_up(self, qt_app):
        """Küszöb (SHOW_DELAY_MS) alatt lezáruló munka SOSEM állítja
        `visible`-re a regisztrátumot."""
        registry = get_app_busy_registry()
        registry.begin()
        registry.end()

        # a teljes küszöbidőn túl figyeljük — mindvégig False kell maradjon
        deadline = time.monotonic() + (_TEST_SHOW_DELAY_MS / 1000) * 3
        while time.monotonic() < deadline:
            qt_app.processEvents()
            assert registry.visible is False
            time.sleep(0.005)

    def test_long_job_lights_up_after_threshold(self, qt_app):
        registry = get_app_busy_registry()
        registry.begin()
        assert registry.visible is False, "a küszöb előtt még nem szabad látszania"
        assert _wait_until(qt_app, lambda: registry.visible is True)
        registry.end()

    def test_minimum_visibility_survives_quick_finish(self, qt_app):
        """Ha a munka a küszöb UTÁN, de a minimális láthatóság ALATT
        fejeződik be, a csík akkor sem villan el azonnal."""
        registry = get_app_busy_registry()
        registry.begin()
        assert _wait_until(qt_app, lambda: registry.visible is True)
        registry.end()
        # közvetlenül a végeztetés után MÉG látszania kell (min-láthatóság)
        assert registry.visible is True
        assert _wait_until(qt_app, lambda: registry.visible is False)


class TestThreadStartFailure:
    """#550: ha a `thread.start()` elbukik, a `begin()` párja is kell."""

    def test_a_szamlalo_visszaall_ha_a_szal_nem_indul(self, qt_app, monkeypatch):
        registry = get_app_busy_registry()
        qt_app.processEvents()
        before = registry.activeCount

        def boom(self):
            raise RuntimeError("can't start new thread")

        monkeypatch.setattr(threading.Thread, "start", boom)
        worker = _Worker()
        with pytest.raises(RuntimeError):
            worker._start_background(lambda: None)

        qt_app.processEvents()
        assert registry.activeCount == before, "a csík örökre pörögne"
        assert not worker.backgroundWorkersRunning()
