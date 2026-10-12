"""A tömörítés-vezérlő — #449.

Az eredeti `compacting.fen` egyetlen gombja a **Mégse** volt: itt az a
tárgy, hogy a háttérszálas tömörítés végigfut, jelez, és megszakítható.
"""

import sqlite3

from picasapy.app import compact_controller as compact_controller_module
from picasapy.app.compact_controller import CompactController


def _wasteful_db(path, rows=4000):
    conn = sqlite3.connect(path)
    conn.execute("CREATE TABLE t (id INTEGER PRIMARY KEY, blob TEXT)")
    conn.executemany(
        "INSERT INTO t (blob) VALUES (?)", [("x" * 400,) for _ in range(rows)]
    )
    conn.commit()
    conn.execute("DELETE FROM t WHERE id > ?", (rows // 20,))
    conn.commit()
    conn.close()
    return path


def _wait(controller, qt_app, timeout=30.0):
    assert controller.waitForBackgroundWorkers(timeout), "a tömörítő szál nem állt le"
    qt_app.processEvents()


class TestCompactController:
    def test_feluleti_allapothoz_nincs_kulon_start_vagy_haladasjelzes(
        self, tmp_path
    ):
        controller = CompactController(tmp_path / "index.db")

        assert not hasattr(controller, "compactStarted")
        assert not hasattr(controller, "compactProgress")

    def test_compaction_is_submitted_to_the_shared_index_writer_queue(self, tmp_path):
        class CapturingQueue:
            def __init__(self):
                self.jobs = []

            def submit(self, worker, *, name):
                self.jobs.append((worker, name))
                return True

        queue = CapturingQueue()
        db = _wasteful_db(tmp_path / "index.db", rows=100)
        controller = CompactController(db, writer_queue=queue)

        controller.startCompact()

        assert len(queue.jobs) == 1
        assert queue.jobs[0][1] == "picasapy-compact"
        assert controller.running is True

    def test_it_finishes_and_reports_the_saved_space(self, qt_app, tmp_path):
        controller = CompactController(_wasteful_db(tmp_path / "index.db"))
        saved = []
        controller.compactFinished.connect(saved.append)

        controller.startCompact()
        _wait(controller, qt_app)

        assert saved and saved[0] > 0
        assert controller.running is False

    def test_it_can_be_cancelled_and_the_database_survives(
        self, qt_app, tmp_path, monkeypatch
    ):
        db = _wasteful_db(tmp_path / "index.db", rows=20000)
        controller = CompactController(db)
        cancelled = []
        controller.compactCancelled.connect(lambda: cancelled.append(True))
        compact = compact_controller_module.compact_database

        def compact_with_cancel_on_real_progress(
            path, *, progress=None, should_cancel=None
        ):
            assert progress is None, "a felület nem kap hasznavehetetlen pulzust"
            return compact(
                path,
                progress=lambda _tick: controller.cancelCompact(),
                should_cancel=should_cancel,
            )

        monkeypatch.setattr(
            compact_controller_module,
            "compact_database",
            compact_with_cancel_on_real_progress,
        )

        controller.startCompact()
        _wait(controller, qt_app)

        assert cancelled, "a megszakítás nem jelzett vissza"
        conn = sqlite3.connect(db)
        try:
            assert conn.execute("SELECT count(*) FROM t").fetchone()[0] == 1000
        finally:
            conn.close()

    def test_a_missing_database_fails_cleanly(self, qt_app, tmp_path):
        controller = CompactController(tmp_path / "nincs.db")
        failures = []
        controller.compactFailed.connect(failures.append)

        controller.startCompact()
        _wait(controller, qt_app)

        assert failures and failures[0]

    def test_it_tells_whether_compacting_is_worth_it(self, qt_app, tmp_path):
        assert CompactController(_wasteful_db(tmp_path / "a.db")).isWorthCompacting()

        fresh = tmp_path / "b.db"
        conn = sqlite3.connect(fresh)
        conn.execute("CREATE TABLE t (id INTEGER)")
        conn.commit()
        conn.close()
        assert CompactController(fresh).isWorthCompacting() is False
