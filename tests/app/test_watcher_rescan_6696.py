"""#6696: a watcher startup and periodic network rescan stay off local I/O."""

from __future__ import annotations

from pathlib import Path
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


def test_leallas_bevarja_a_felallas_szalat_es_megakadalyozza_a_keso_inditast(
    monkeypatch, tmp_path
):
    from picasapy.scanner import watcher as watcher_module
    from picasapy.scanner.watcher import LibraryWatcher

    utemezes_elindult = threading.Event()
    felallas_folytathato = threading.Event()
    observer_elindult = threading.Event()
    leallas_visszatert = threading.Event()

    class Observer:
        def schedule(self, _handler, _root, *, recursive):
            assert recursive is True
            utemezes_elindult.set()
            felallas_folytathato.wait(2)

        def start(self):
            observer_elindult.set()

        def stop(self):
            pass

        def join(self, timeout=None):
            pass

    monkeypatch.setattr(watcher_module, "Observer", Observer)
    # A bevárás határideje (30 s) jóval hosszabb a felállító szál 2 s-os
    # futásánál: a stop() addig nem térhet vissza, amíg az fut.
    watcher = LibraryWatcher((str(tmp_path),), lambda _mappak: None)
    watcher._start_background()
    assert utemezes_elindult.wait(2)

    leallito = threading.Thread(
        target=lambda: (watcher.stop(), leallas_visszatert.set()), daemon=True
    )
    leallito.start()
    try:
        assert not leallas_visszatert.wait(0.1), (
            "a stop() visszatért, miközben a watchdog felállító szála futott"
        )
    finally:
        felallas_folytathato.set()
        leallito.join(2)

    assert not leallito.is_alive(), "a stop() nem tért vissza a felállás után"
    assert not observer_elindult.is_set(), "a leállított figyelő később elindult"
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


def test_watcher_jelzes_kifejezetten_sorbaallitva_erkezik_a_vezerlohoz():
    forras = Path("src/picasapy/app/controller_initialization.py").read_text(
        encoding="utf-8"
    )

    assert "self.watcherDirty.connect(" in forras
    assert "self._on_folders_dirty, Qt.ConnectionType.QueuedConnection" in forras
    assert (
        "self._queue_watcher_start_after_reload, Qt.ConnectionType.QueuedConnection"
        in forras
    )
    assert forras.index(
        "self.syncFinished.connect(self._reload_after_sync_if_changed)"
    ) < (
        forras.index("self._queue_watcher_start_after_reload")
    )


def test_indulaskor_a_figyelo_a_gui_ujratoltes_utan_indul():
    from picasapy.app.library_controller_activity import _LibraryActivityMixin

    class Timer:
        def __init__(self):
            self.started_with = None

        def start(self, interval):
            self.started_with = interval

    class Vezerlo(_LibraryActivityMixin):
        def __init__(self):
            self._watcher_start_pending = True
            self._watcher_start_timer = Timer()
            self._sync_running = True
            self._dirty_running = False
            self.watcher_starts = 0

        def _start_watcher_background(self):
            self.watcher_starts += 1

    vezerlo = Vezerlo()
    vezerlo._queue_watcher_start_after_reload()
    assert vezerlo._watcher_start_timer.started_with == 0
    vezerlo._start_watcher_when_ready()
    assert vezerlo.watcher_starts == 0, "szinkron alatt indult el a figyelő"

    vezerlo._sync_running = False
    vezerlo._start_watcher_when_ready()
    assert vezerlo.watcher_starts == 1
    assert vezerlo._watcher_start_pending is False
