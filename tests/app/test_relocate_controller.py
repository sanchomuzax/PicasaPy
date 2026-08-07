"""RelocateController (#368) — a `picasapy.index.relocate` mag QML-hídja.

Valódi ideiglenes forrás- és cél-mappával, mock nélkül (a
`test_dedup_controller.py`/`test_import_source_controller.py` mintája)."""

from __future__ import annotations

import sqlite3

import pytest
from PySide6.QtCore import QEventLoop, QTimer

from picasapy.app.data_location import read_data_root
from picasapy.app.relocate_controller import RelocateController
from picasapy.index import open_index, sync_tree


def _quit_on(signal):
    loop = QEventLoop()
    signal.connect(loop.quit)
    QTimer.singleShot(5000, loop.quit)
    return loop


def _make_source(tmp_path):
    old_data = tmp_path / "old-data"
    old_data.mkdir()
    old_cache = tmp_path / "old-cache" / "thumbs"
    old_cache.mkdir(parents=True)
    (old_cache / "x.jpg").write_bytes(b"thumb")

    photos = tmp_path / "fotok"
    photos.mkdir()
    (photos / "a.jpg").write_bytes(b"\xff\xd8\xff\xe0" + b"0" * 50)
    index_db = old_data / "index.db"
    with open_index(index_db) as conn:
        sync_tree(conn, photos)
    return index_db, old_cache


@pytest.fixture
def source(tmp_path):
    return _make_source(tmp_path)


@pytest.fixture
def config_dir(tmp_path):
    return tmp_path / "config"


@pytest.fixture
def controller(qt_app, source, config_dir):
    """#438: a teszt végén BEVÁRJA a háttérszálat (a #430 SIGSEGV-osztály
    elkerülése), amíg a controller még él."""
    index_db, cache_dir = source
    ctl = RelocateController(index_db, cache_dir, config_dir)
    yield ctl
    assert ctl.waitForBackgroundWorkers(30.0), "az áthelyezés háttérszála nem állt le"


class TestCurrentLocation:
    def test_reports_index_database_folder(self, controller, source):
        index_db, _cache_dir = source
        assert controller.currentLocation == str(index_db.parent)


class TestStartRelocate:
    def test_missing_destination_emits_failure(self, controller):
        # üres cél esetén a hiba SZINKRON (a háttérszál elindítása előtt)
        # jön — nincs mire várni, az `_quit_on`-os loop csak feleslegesen
        # kivárná a saját időtúllépését
        seen = []
        controller.relocateFailed.connect(seen.append)
        controller.startRelocate("")
        assert seen

    def test_successful_relocation_emits_finished_and_writes_override(
        self, controller, source, config_dir, tmp_path
    ):
        index_db, cache_dir = source
        new_root = tmp_path / "uj-hely"

        finished = []
        controller.relocateFinished.connect(finished.append)
        loop = _quit_on(controller.relocateFinished)
        controller.startRelocate(str(new_root))
        loop.exec()

        assert finished == [str(new_root)]
        assert not index_db.exists()
        assert not cache_dir.exists()
        assert (new_root / "index.db").exists()
        assert (new_root / "thumbs" / "x.jpg").exists()
        assert read_data_root(config_dir) == new_root

    def test_new_database_has_the_original_photo(
        self, controller, tmp_path
    ):
        new_root = tmp_path / "uj-hely"
        loop = _quit_on(controller.relocateFinished)
        controller.startRelocate(str(new_root))
        loop.exec()

        conn = sqlite3.connect(str(new_root / "index.db"))
        try:
            count = conn.execute("SELECT COUNT(*) FROM photos").fetchone()[0]
        finally:
            conn.close()
        assert count == 1

    def test_progress_signal_reports_phases(self, controller, tmp_path):
        new_root = tmp_path / "uj-hely"
        phases = []
        controller.relocateProgress.connect(
            lambda phase, done, total: phases.append(phase)
        )
        loop = _quit_on(controller.relocateFinished)
        controller.startRelocate(str(new_root))
        loop.exec()

        assert "done" in phases

    def test_invalid_destination_inside_source_emits_failure_and_keeps_source(
        self, controller, source
    ):
        index_db, _cache_dir = source
        seen = []
        controller.relocateFailed.connect(seen.append)
        loop = _quit_on(controller.relocateFailed)
        controller.startRelocate(str(index_db.parent / "sub"))
        loop.exec()

        assert seen
        assert index_db.exists()

    def test_file_url_destination_is_accepted(self, controller, tmp_path):
        new_root = tmp_path / "uj-hely"
        loop = _quit_on(controller.relocateFinished)
        controller.startRelocate(new_root.as_uri())
        loop.exec()

        assert (new_root / "index.db").exists()


class TestCancelRelocate:
    def test_cancel_before_completion_leaves_source_untouched(
        self, controller, source, tmp_path
    ):
        index_db, cache_dir = source
        new_root = tmp_path / "uj-hely"

        # a `relocateStarted` UGYANAZON a szálon, SZINKRON emit()-tel jön
        # (a `startRelocate` a háttérszál indítása ELŐTT bocsátja ki) — a
        # ide kötött `cancelRelocate` így garantáltan a worker első
        # ellenőrzési pontja ELŐTT állítja be a megszakítási jelzőt,
        # determinisztikussá téve a tesztet (nincs versenyhelyzet).
        controller.relocateStarted.connect(controller.cancelRelocate)
        cancelled = []
        controller.relocateCancelled.connect(lambda: cancelled.append(True))
        loop = _quit_on(controller.relocateCancelled)
        controller.startRelocate(str(new_root))
        loop.exec()

        assert cancelled == [True]
        assert index_db.exists()
        assert cache_dir.exists()
        assert not (new_root / "index.db").exists()

    def test_cancel_before_start_is_a_noop(self, controller):
        controller.cancelRelocate()  # nincs futó áthelyezés — nem hibázik


class TestBackgroundThreadTeardown:
    """#438 (a #430 SIGSEGV-osztály maradéka): az áthelyezés háttérszála
    bevárható legyen, mielőtt a controller megsemmisül."""

    def test_wait_without_a_run_returns_immediately(self, controller):
        assert controller.waitForBackgroundWorkers(0.0)

    def test_wait_joins_the_worker_thread(self, controller, tmp_path):
        loop = _quit_on(controller.relocateFinished)
        controller.startRelocate(str(tmp_path / "uj-hely"))
        loop.exec()
        assert controller.waitForBackgroundWorkers(30.0)
        assert not controller.backgroundWorkersRunning()
