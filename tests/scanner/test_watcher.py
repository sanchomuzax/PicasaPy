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
        time.sleep(0.3)  # az inotify-watchok felállása
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
        (tmp_path / "m" / ".picasa.ini").write_text("[a.jpg]\nstar=yes\n")
        collector.wait()
        assert str(tmp_path / "m") in collector.seen

    def test_irrelevant_files_ignored(self, tmp_path, watcher_factory, collector):
        (tmp_path / "m").mkdir()
        watcher_factory(tmp_path)
        (tmp_path / "m" / "jegyzet.txt").write_text("nem média")
        (tmp_path / "m" / ".picasa.ini.bak").write_text("backup")
        time.sleep(0.8)
        assert collector.batches == []

    def test_hidden_dirs_ignored(self, tmp_path, watcher_factory, collector):
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
