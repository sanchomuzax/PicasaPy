"""#6518: az arcindex diagnosztikája a nyitott WAL-kapcsolat állapotát rögzíti."""

from __future__ import annotations

import re
import sqlite3

import pytest


def test_scan_database_diagnostics_capture_wal_before_connection_closes(
    tmp_path, caplog
):
    from picasapy.app.face_scan_controller_scan_mixin import (
        FaceScanControllerScanMixin,
    )

    db_path = tmp_path / "index.db"
    controller = object.__new__(FaceScanControllerScanMixin)
    controller._db_path = db_path

    with caplog.at_level(
        "ERROR", logger="picasapy.app.face_scan_controller_shared"
    ):
        with pytest.raises(sqlite3.DatabaseError, match="malformed"):
            with controller._open_index_for_scan() as conn:
                conn.execute("PRAGMA wal_autocheckpoint=0")
                conn.execute("CREATE TABLE diagnostic_probe (value INTEGER)")
                conn.execute("INSERT INTO diagnostic_probe VALUES (1)")
                conn.commit()

                wal_path = db_path.with_name(f"{db_path.name}-wal")
                assert wal_path.is_file()
                assert wal_path.stat().st_size > 0
                raise sqlite3.DatabaseError("database disk image is malformed")

    messages = "\n".join(record.getMessage() for record in caplog.records)
    assert "arc-index journal_mode: wal" in messages
    assert re.search(r"index\.db=\d+ bájt", messages)
    wal_sizes = re.findall(r"-wal=(\d+) bájt", messages)
    assert wal_sizes and any(int(size) > 0 for size in wal_sizes)
    assert re.search(r"-shm=\d+ bájt", messages)
    assert "quick_check" in messages
