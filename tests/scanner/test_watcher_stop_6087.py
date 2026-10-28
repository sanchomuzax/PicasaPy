"""#6087: a figyelő leállítása bevárja a már futó debounce callbacket."""

from __future__ import annotations

import threading

from picasapy.scanner import LibraryWatcher


def test_stop_megvarja_a_mar_futo_callbacket(monkeypatch):
    callback_elindult = threading.Event()
    callback_folytathato = threading.Event()
    stop_visszatert = threading.Event()
    timer_join_elindult = threading.Event()

    from picasapy.scanner import watcher as watcher_module

    timer_alaposztaly = threading.Timer

    class FigyeltTimer(timer_alaposztaly):
        def join(self, *args, **kwargs):
            timer_join_elindult.set()
            return super().join(*args, **kwargs)

    monkeypatch.setattr(watcher_module.threading, "Timer", FigyeltTimer)

    def callback(_mappak):
        callback_elindult.set()
        assert callback_folytathato.wait(5), "a teszt nem oldotta fel a callbacket"

    figyelo = LibraryWatcher(
        (), callback, debounce_seconds=0.01, max_debounce_seconds=0.01
    )
    figyelo.start()
    figyelo._mark_dirty("teszt")
    assert callback_elindult.wait(2), "a debounce callback nem indult el"

    def leallit():
        figyelo.stop()
        stop_visszatert.set()

    leallito_szal = threading.Thread(target=leallit, daemon=True)
    leallito_szal.start()
    try:
        assert timer_join_elindult.wait(2), (
            "a stop() nem joinolta a debounce Timer szálát"
        )
        assert not stop_visszatert.is_set(), (
            "a stop() visszatért, miközben a debounce callback még futott"
        )
    finally:
        callback_folytathato.set()
        leallito_szal.join(timeout=2)

    assert stop_visszatert.is_set(), "a stop() nem tért vissza a callback végén"
    assert not leallito_szal.is_alive(), "a leállító szál beragadt"
    assert figyelo.leallt()
