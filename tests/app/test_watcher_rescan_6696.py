"""#6696: a watcher startup and periodic network rescan stay off local I/O."""

from __future__ import annotations

import threading


def test_a_figyelo_inditasa_hattermunkat_hasznal(tmp_path, monkeypatch):
    from picasapy.app.library_controller_activity import _LibraryActivityMixin
    from picasapy.scanner import watcher as watcher_module
    from picasapy.scanner.watcher import LibraryWatcher

    main_thread = threading.get_ident()
    schedule_thread_ids = []
    scheduled = threading.Event()

    class Observer:
        def schedule(self, _handler, _root, *, recursive):
            assert recursive is True
            schedule_thread_ids.append(threading.get_ident())
            scheduled.set()

        def start(self):
            pass

        def stop(self):
            pass

        def join(self, timeout=None):
            pass

    class Vezerlo(_LibraryActivityMixin):
        def __init__(self):
            self._watcher = LibraryWatcher((str(tmp_path),), lambda _mappak: None)

    monkeypatch.setattr(watcher_module, "Observer", Observer)
    vezerlo = Vezerlo()
    try:
        vezerlo._start_watcher_background()
        assert scheduled.wait(2), "a watcher nem kezdte meg a rekurzív ütemezést"
        assert schedule_thread_ids and schedule_thread_ids[0] != main_thread
    finally:
        vezerlo._watcher.stop()


def test_leallas_nem_varja_meg_a_rekurziv_figyelo_felallasat(monkeypatch, tmp_path):
    from picasapy.scanner import watcher as watcher_module
    from picasapy.scanner.watcher import LibraryWatcher

    felallas_elindult = threading.Event()
    felallas_folytathato = threading.Event()
    observer_leallt = threading.Event()
    leallas_visszatert = threading.Event()

    class Observer:
        def schedule(self, _handler, _root, *, recursive):
            assert recursive is True

        def start(self):
            felallas_elindult.set()
            felallas_folytathato.wait(2)

        def stop(self):
            observer_leallt.set()

        def join(self, timeout=None):
            pass

    monkeypatch.setattr(watcher_module, "Observer", Observer)
    watcher = LibraryWatcher((str(tmp_path),), lambda _mappak: None)
    watcher._start_background()
    assert felallas_elindult.wait(2)

    leallito = threading.Thread(
        target=lambda: (watcher.stop(), leallas_visszatert.set()), daemon=True
    )
    leallito.start()
    try:
        assert leallas_visszatert.wait(0.2), (
            "a felület szála a rekurzív watchdog-felállásra vár"
        )
    finally:
        felallas_folytathato.set()
        leallito.join(2)

    assert observer_leallt.wait(2), "a félkész figyelő nem takarította el magát"
    assert watcher.leallt()


def _rescan_vezerlo(roots):
    from picasapy.app.library_controller_sync import _LibrarySyncRescanMixin

    class Vezerlo(_LibrarySyncRescanMixin):
        def __init__(self):
            self._roots = list(roots)
            self._sync_running = False
            self._dirty_running = False
            self._filetype_scan_snapshot = None
            self._projekt_kimenet_cache = ("cached",)
            self._szinkronok = []

        def _start_background(
            self, target, *, args=(), kwargs=None, name=None, cancel=None
        ):
            self._szinkronok.append((target, args, kwargs, name))
            return None

        def cancelScan(self):
            pass

    return Vezerlo()


def test_idozitett_teljes_ujraolvasas_csak_halozati_gyokeret_uzen():
    helyi = r"C:\Photos"
    halozati = r"\\photoserver\share\Pictures"
    vezerlo = _rescan_vezerlo((helyi, halozati))

    vezerlo._rescan_network_roots()

    assert len(vezerlo._szinkronok) == 1
    target, args, _kwargs, name = vezerlo._szinkronok[0]
    assert target == vezerlo._sync_worker_roots
    assert args == ((halozati,),)
    assert name == "picasapy-sync-rescan"


def test_helyi_gyokerhez_nincs_idozitett_teljes_ujraolvasas():
    vezerlo = _rescan_vezerlo((r"C:\Photos",))

    vezerlo._rescan_network_roots()

    assert vezerlo._szinkronok == []
    assert vezerlo._projekt_kimenet_cache is None
