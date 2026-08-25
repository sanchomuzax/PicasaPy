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

    def test_ini_change_reports_folder(self, tmp_path, watcher_factory, collector):
        (tmp_path / "m").mkdir()
        watcher_factory(tmp_path)
        (tmp_path / "m" / ".picasa.ini").write_text("[a.jpg]\nstar=yes\n", encoding="utf-8")
        collector.wait()
        assert str(tmp_path / "m") in collector.seen

    def test_irrelevant_files_ignored(self, tmp_path, watcher_factory, collector):
        """A nem releváns fájlok nem adnak jelzést.

        ⚠️ #1463 — fali-óra alapú, és az is MARAD: távollétet állítunk,
        azt pedig csak várakozással lehet. A 0,8 mp a 0,2 mp-es
        debounce négyszerese, tehát ha a szűrő elromlana, a flush
        bőven beleférne az ablakba.

        Terhelt gépen ez NEM hamis bukást ad, hanem hamis ZÖLDET: ha a
        gép annyira lassú, hogy a hibásan átengedett esemény sem ér oda
        0,8 mp alatt, a teszt zöld marad. Az irány tehát biztonságos —
        de aki itt zöldet lát terhelés alatt, ne vegye erős bizonyítéknak.
        """
        (tmp_path / "m").mkdir()
        watcher_factory(tmp_path)
        (tmp_path / "m" / "jegyzet.txt").write_text("nem média", encoding="utf-8")
        (tmp_path / "m" / ".picasa.ini.bak").write_text("backup", encoding="utf-8")
        time.sleep(0.8)
        assert collector.batches == []

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
        collector.wait()
        assert {str(tmp_path / "a"), str(tmp_path / "b")} <= collector.seen

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
