"""Élő mappa-figyelés (watchdog/inotify) — debounce-olt mappa-jelzések."""

import threading
import time

import pytest

from picasapy.scanner import LibraryWatcher


@pytest.fixture
def collector():
    class Collector:
        def __init__(self):
            self.batches = []
            self.event = threading.Event()

        def __call__(self, folders):
            self.batches.append(set(folders))
            self.event.set()

        def wait(self, timeout=5.0):
            assert self.event.wait(timeout), "nem érkezett watcher-jelzés"
            self.event.clear()

        def wait_until_seen(self, folders, timeout=5.0):
            """Addig vár, amíg MINDEN mappa jelzést kapott — akár több kötegben.

            Terhelt gépen a két írás a debounce-ablak két oldalára eshet, és
            akkor két köteg jön; az első köteg utáni azonnali állítás
            ilyenkor hamisan piros (CI, 2026-09-25).
            """
            hatarido = time.monotonic() + timeout
            while not set(folders) <= self.seen:
                marad = hatarido - time.monotonic()
                assert marad > 0, f"nem jött jelzés: {set(folders) - self.seen}"
                self.event.wait(marad)
                self.event.clear()

        def wait_until(self, predicate, timeout=5.0):
            deadline = time.monotonic() + timeout
            while not predicate(self.seen):
                remaining = deadline - time.monotonic()
                assert remaining > 0, "nem érkezett meg a várt könyvtáresemény"
                self.event.wait(remaining)
                self.event.clear()

        @property
        def seen(self):
            return set().union(*self.batches) if self.batches else set()

    return Collector()


@pytest.fixture
def watcher_factory(collector):
    watchers = []

    def _make(root, debounce=0.2):
        watcher = LibraryWatcher((str(root),), collector, debounce_seconds=debounce)
        watcher.start()
        watchers.append(watcher)
        # #1463: itt korábban egy 0,3 mp-es `time.sleep()` állt „az
        # inotify-watchok felállása" indoklással. Ez fali-óra alapú
        # fogadás volt — és feleslegesen az: a watchdog a watchokat
        # SZINKRON módon adja hozzá, még mielőtt a `start()` visszatérne.
        # A lánc: `Observer.start()` → `emitter.start()` →
        # `BaseThread.start()`, ami a hívó szálán futtatja az
        # `on_thread_start()`-ot, az pedig megnyitja az `InotifyBuffer`-t
        # (`inotify_add_watch` mindegyik mappára). A `watcher.start()`
        # visszatérése tehát MAGA a szinkronpont.
        #
        # Mérve (2026-08-25, ezen a gépen): alvás nélkül 40 futásból
        # 40-szer megérkezett a közvetlenül a `start()` után írt fájl
        # jelzése — 0 elmaradás.
        return watcher

    yield _make
    for watcher in watchers:
        watcher.stop()


class TestLibraryWatcher:
    def test_new_photo_reports_folder(self, tmp_path, watcher_factory, collector):
        (tmp_path / "m").mkdir()
        watcher_factory(tmp_path)
        (tmp_path / "m" / "uj.jpg").write_bytes(b"x")
        collector.wait()
        assert str(tmp_path / "m") in collector.seen

    def test_directory_rename_reports_only_changed_subtrees(
        self, tmp_path, watcher_factory, collector
    ):
        """Az átnevezés külön törlést és új részfa-beolvasást jelez.

        Mappanév-változáskor a fájlok maguk nem változnak, ezért a fájlszintű
        eseményszűrés önmagában nem veheti ki a régi út indexsorát. A
        gyökér megjelölése viszont fölöslegesen bejárná a teljes könyvtárat.
        """
        source = tmp_path / "Eltunt"
        source.mkdir()
        watcher_factory(tmp_path)

        destination = tmp_path / "Atnevezett"
        source.rename(destination)

        collector.wait_until(
            lambda events: {
                (getattr(event, "path", None), getattr(event, "action", None))
                for event in events
            }
            >= {
                (str(source), "deleted"),
                (str(destination), "created"),
            }
        )

    def test_ini_change_reports_folder(self, tmp_path, watcher_factory, collector):
        (tmp_path / "m").mkdir()
        watcher_factory(tmp_path)
        (tmp_path / "m" / ".picasa.ini").write_text("[a.jpg]\nstar=yes\n", encoding="utf-8")
        collector.wait()
        assert str(tmp_path / "m") in collector.seen

    def test_irrelevant_files_ignored(self, tmp_path):
        """A fájlszűrő a nem képi és backup fájlokat eldobja.

        A könyvtár saját módosítása külön esemény, és azt a #6696 szerint
        a `test_modositott_mappa_is_jelzest_ad` fedi le.
        """
        from watchdog.events import FileCreatedEvent

        from picasapy.scanner.watcher import _Handler

        class Figyelo:
            _roots = (str(tmp_path),)

            def _mark_dirty(self, _mappa):
                raise AssertionError("nem releváns fájl piszkos jelzést adott")

        kezelo = _Handler(Figyelo())
        for nev in ("jegyzet.txt", ".picasa.ini.bak"):
            kezelo.on_any_event(FileCreatedEvent(str(tmp_path / nev)))

    def test_hidden_dirs_ignored(self, tmp_path, watcher_factory, collector):
        """A rejtett mappákban történt változás nem ad jelzést.

        ⚠️ #1463 — ugyanaz a fali-óra alapú távollét-állítás, mint a
        `test_irrelevant_files_ignored`-ban: a 0,8 mp a debounce
        négyszerese; terhelt gépen hamis ZÖLD a kockázat, nem hamis piros.
        """
        hidden = tmp_path / ".picasaoriginals"
        hidden.mkdir()
        watcher_factory(tmp_path)
        (hidden / "regi.jpg").write_bytes(b"x")
        time.sleep(0.8)
        assert collector.batches == []

    def test_debounce_batches_burst(self, tmp_path, watcher_factory, collector):
        (tmp_path / "a").mkdir()
        (tmp_path / "b").mkdir()
        watcher_factory(tmp_path)
        (tmp_path / "a" / "1.jpg").write_bytes(b"x")
        (tmp_path / "b" / "2.jpg").write_bytes(b"y")
        collector.wait_until_seen({str(tmp_path / "a"), str(tmp_path / "b")})

    def test_stop_stops_reporting(self, tmp_path, watcher_factory, collector):
        """A `stop()` után nem érkezik több jelzés.

        ⚠️ #1463 — fali-óra alapú távollét-állítás (0,8 mp, a 0,2 mp-es
        debounce négyszerese). Terhelt gépen hamis ZÖLD a kockázat, nem
        hamis piros.
        """
        (tmp_path / "m").mkdir()
        watcher = watcher_factory(tmp_path)
        watcher.stop()
        (tmp_path / "m" / "kesei.jpg").write_bytes(b"x")
        time.sleep(0.8)
        assert collector.batches == []

    def test_missing_root_tolerated(self, tmp_path, collector):
        watcher = LibraryWatcher(
            (str(tmp_path / "nincs"), str(tmp_path)), collector
        )
        watcher.start()  # nem dobhat a hiányzó gyökér miatt
        watcher.stop()

    def test_root_under_hidden_dir_still_reports(
        self, tmp_path, watcher_factory, collector
    ):
        # a szűrés a figyelt GYÖKÉRHEZ képesti relatív úton nézze a rejtett
        # komponenseket, ne az abszolút út minden komponensét — különben
        # egy rejtett könyvtár alatti gyökérnél (pl. ~/.photos/...) minden
        # esemény némán eldobódna
        hidden_root = tmp_path / ".photos" / "album"
        hidden_root.mkdir(parents=True)
        watcher_factory(hidden_root)
        (hidden_root / "uj.jpg").write_bytes(b"x")
        collector.wait()
        assert str(hidden_root) in collector.seen

    def test_debounce_has_maximum_window(self, tmp_path, collector):
        # hosszú másolás alatt (folyamatos, meg-nem-szakadó esemény-sorozat)
        # a callback ne halasztódjon a végtelenbe — legyen egy max. ablak.
        # A jelzés-sorozatot külön szálon, FOLYAMATOSAN generáljuk (nem áll
        # le a várakozás alatt) — enélkül a debounce sosem futna le magától.
        watcher = LibraryWatcher(
            (), collector, debounce_seconds=0.3, max_debounce_seconds=0.4
        )
        watcher.start()
        stop_marking = threading.Event()

        def _mark_loop():
            while not stop_marking.is_set():
                watcher._mark_dirty(str(tmp_path))
                time.sleep(0.05)

        marker = threading.Thread(target=_mark_loop, daemon=True)
        marker.start()
        try:
            # a max. ablaknak (0.4s) ki kell kényszerítenie a flush-t, jóval
            # a debounce (0.3s) ismételt újraindítása által sugallt
            # "végtelen halasztás" előtt
            # #1463: az időkorlát SZÁNDÉKOSAN bőkezű (korábban 0,9 mp volt).
            # Az állítás foga nem a szűk ablakon múlik: a jelölő szál
            # 0,05 mp-enként újraindítja a 0,3 mp-es debounce-t, tehát
            # `max_debounce` NÉLKÜL a flush SOHA nem futna le — akármeddig
            # várunk. A szűk határidő ezért csak hamis bukást tudott
            # termelni terhelt gépen, valódi hibát nem fogott meg többet.
            assert collector.event.wait(timeout=10.0), (
                "nem érkezett jelzés a max. ablakon belül — a folyamatos "
                "esemény-sorozat a végtelenbe halasztotta a flush-t"
            )
        finally:
            stop_marking.set()
            marker.join(timeout=2)
            watcher.stop()


class TestWindowsKonyvtarTorles:
    """Windowson a watchdog a törölt mappát FÁJL-törlésként jelzi (#5177).

    A `ReadDirectoryChangesW` törlésnél nem mondja meg, mappa volt-e, és a
    törölt utat már nem lehet lekérdezni, ezért `is_directory` hamis.
    """

    @pytest.fixture(autouse=True)
    def _windows(self, monkeypatch):
        monkeypatch.setattr("picasapy.scanner.watcher._platform", lambda: "win32")

    def _kezelo(self, tmp_path, jelzesek):
        from picasapy.scanner.watcher import _Handler

        class Figyelo:
            _roots = (str(tmp_path),)

            def _mark_dirty(self, valtozas):
                jelzesek.append(valtozas)

        return _Handler(Figyelo())

    def test_kiterjesztes_nelkuli_torles_mappatorles(self, tmp_path):
        from watchdog.events import FileDeletedEvent

        from picasapy.scanner import DirectoryChange

        jelzesek = []
        self._kezelo(tmp_path, jelzesek).on_any_event(
            FileDeletedEvent(str(tmp_path / "Eltunt"))
        )
        assert jelzesek == [DirectoryChange(str(tmp_path / "Eltunt"), "deleted")]

    def test_kep_torlese_marad_mappajelzes(self, tmp_path):
        from watchdog.events import FileDeletedEvent

        jelzesek = []
        self._kezelo(tmp_path, jelzesek).on_any_event(
            FileDeletedEvent(str(tmp_path / "A" / "kep.jpg"))
        )
        assert jelzesek == [str(tmp_path / "A")]

    def test_rejtett_ut_torlese_nem_jelez(self, tmp_path):
        from watchdog.events import FileDeletedEvent

        jelzesek = []
        self._kezelo(tmp_path, jelzesek).on_any_event(
            FileDeletedEvent(str(tmp_path / ".picasaoriginals"))
        )
        assert jelzesek == []


def test_fajl_olvasasa_nem_jelol_piszkosnak_de_a_valtozasok_igen(tmp_path):
    """#6696: csak írási/változási watchdog-esemény érhet piszkos jelölésig."""
    from watchdog.events import (
        FileClosedNoWriteEvent,
        FileCreatedEvent,
        FileClosedEvent,
        FileDeletedEvent,
        FileModifiedEvent,
        FileOpenedEvent,
    )

    from picasapy.scanner.watcher import _Handler

    class Figyelo:
        _roots = (str(tmp_path),)

        def __init__(self):
            self.jelzesek = []

        def _mark_dirty(self, mappa):
            self.jelzesek.append(mappa)

    figyelo = Figyelo()
    kezelo = _Handler(figyelo)
    kep = str(tmp_path / "kep.jpg")

    kezelo.on_any_event(FileOpenedEvent(kep))
    kezelo.on_any_event(FileClosedNoWriteEvent(kep))
    assert figyelo.jelzesek == [], "a saját fájlolvasás piszkosnak jelölt egy mappát"

    for esemeny in (
        FileCreatedEvent(kep),
        FileClosedEvent(kep),
        FileDeletedEvent(kep),
        FileModifiedEvent(kep),
    ):
        kezelo.on_any_event(esemeny)
    assert figyelo.jelzesek == [str(tmp_path)] * 4


def test_modositott_mappa_is_jelzest_ad(tmp_path):
    """A mappán jelzett módosítás is számít, a read-only bezárás nem."""
    from watchdog.events import DirModifiedEvent

    from picasapy.scanner import DirectoryChange
    from picasapy.scanner.watcher import _Handler

    class Figyelo:
        _roots = (str(tmp_path),)

        def __init__(self):
            self.jelzesek = []

        def _mark_dirty(self, mappa):
            self.jelzesek.append(mappa)

    figyelo = Figyelo()
    _Handler(figyelo).on_any_event(DirModifiedEvent(str(tmp_path / "album")))
    assert figyelo.jelzesek == [
        DirectoryChange(str(tmp_path / "album"), "refresh")
    ]


# rontás-kontroll: picasapy.scanner.watcher._CHANGE_EVENT_TYPES = {'created', 'deleted', 'moved', 'modified', 'closed', 'opened'} → 1 failed
def test_halozati_gyokerhez_nem_kerul_watchdog_utemezes(tmp_path, monkeypatch):
    from picasapy.scanner import watcher as watcher_module
    from picasapy.scanner.watcher import LibraryWatcher

    helyi = tmp_path / "helyi"
    tavoli = tmp_path / "megosztas"
    helyi.mkdir()
    tavoli.mkdir()
    utemezett = []

    class Observer:
        def schedule(self, _handler, path, *, recursive):
            utemezett.append((path, recursive))

        def start(self):
            pass

        def stop(self):
            pass

        def join(self, timeout=None):
            pass

    monkeypatch.setattr(watcher_module, "Observer", Observer)
    monkeypatch.setattr(
        watcher_module,
        "halozati_gyoker",
        lambda root: "\\\\photoserver\\share\\" if root == str(tavoli) else None,
    )

    figyelo = LibraryWatcher((str(helyi), str(tavoli)), lambda _mappak: None)
    figyelo.start()
    try:
        assert utemezett == [(str(helyi), True)]
    finally:
        figyelo.stop()
