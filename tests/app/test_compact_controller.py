"""A tömörítés-vezérlő — #449.

Az eredeti `compacting.fen` egyetlen gombja a **Mégse** volt: itt az a
tárgy, hogy a háttérszálas tömörítés végigfut, jelez, és megszakítható.
"""

import sqlite3

from PySide6.QtCore import Qt

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
    def test_it_finishes_and_reports_the_saved_space(self, qt_app, tmp_path):
        controller = CompactController(_wasteful_db(tmp_path / "index.db"))
        saved = []
        controller.compactFinished.connect(saved.append)

        controller.startCompact()
        _wait(controller, qt_app)

        assert saved and saved[0] > 0
        assert controller.running is False

    def test_it_can_be_cancelled_and_the_database_survives(self, qt_app, tmp_path):
        db = _wasteful_db(tmp_path / "index.db", rows=20000)
        controller = CompactController(db)
        cancelled = []
        controller.compactCancelled.connect(lambda: cancelled.append(True))
        # a megszakítás a haladás-jelzés első jelére megy ki — így biztos,
        # hogy a `VACUUM` közben ér oda, nem előtte vagy utána
        # DirectConnection: a jelzés a HÁTTÉRSZÁLON születik, sorba állítva
        # csak a `VACUUM` után futna le — akkor pedig már nincs mit
        # megszakítani
        controller.compactProgress.connect(
            lambda _tick: controller.cancelCompact(),
            Qt.ConnectionType.DirectConnection,
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
