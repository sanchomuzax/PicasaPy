"""#4646: a fájlidő-visszaállítás a mappa újraszkennelése UTÁN történik.

Relatime fájlrendszeren az indexelő olvasás frissíti az atime-ot, ezért a
visszaállításnak az olvasás után kell lefutnia. A teszt GUI nélkül, valódi
indexszel méri ezt, így a sorrend nem függ a nézet utólagos képbetöltésétől.
"""

from __future__ import annotations

import logging
import os
from datetime import datetime
from pathlib import Path

import pytest

from picasapy.app import timestamp_controller
from picasapy.app.timestamp_controller import TimestampAdjustmentMixin
from support.jpeg_factory import make_jpeg


CEL_DATUM = datetime(2020, 2, 3, 4, 5, 6)
# Régi időbélyeg: relatime alatt az olvasás ilyenkor frissíti az atime-ot.
REGI_NS = round(datetime(2018, 1, 2, 3, 4, 5).timestamp() * 1_000_000_000)


class _Controller(TimestampAdjustmentMixin):
    def __init__(self, db_path: Path) -> None:
        self._db_path = db_path
        self._filetype_scan_snapshot = None


@pytest.fixture
def mappa(tmp_path):
    folder = tmp_path / "kepek"
    folder.mkdir()
    paths = [
        make_jpeg(
            folder / nev,
            taken_at="2019:02:03 04:05:06",
            datetime_0th="2019:02:03 04:05:06",
        )
        for nev in ("a.jpg", "b.jpg")
    ]
    for path in paths:
        os.utime(path, ns=(REGI_NS, REGI_NS))
    return folder, paths


def _irasok(paths: list[Path]) -> dict[Path, os.stat_result]:
    """Az EXIF-írás a mappa minden képére, a visszaállításhoz szükséges régi időkkel."""
    befores = {}
    for path in paths:
        before = timestamp_controller._write_photo_exif_date(path, CEL_DATUM)
        assert before is not None
        befores[path] = before
    return befores


def test_ujraszkenneles_utan_is_megmaradnak_a_fajlidok(tmp_path, mappa):
    folder, paths = mappa
    regi = {path: path.stat() for path in paths}
    befores = _irasok(paths)

    _Controller(tmp_path / "index.sqlite")._reindex_folder_keeping_times(
        str(folder), befores
    )

    for path in paths:
        most = path.stat()
        assert most.st_atime_ns == regi[path].st_atime_ns
        assert most.st_mtime_ns == regi[path].st_mtime_ns


def test_os_utime_hibaja_naplozodik_es_a_koteg_folytatodik(
    tmp_path, mappa, monkeypatch, caplog
):
    folder, paths = mappa
    befores = _irasok(paths)

    def utime_hiba(*_args, **_kwargs):
        raise OSError("nincs jogosultság")

    monkeypatch.setattr(timestamp_controller.os, "utime", utime_hiba)
    caplog.set_level(logging.WARNING, logger=timestamp_controller.__name__)

    _Controller(tmp_path / "index.sqlite")._reindex_folder_keeping_times(
        str(folder), befores
    )

    assert sum("fájlidők visszaállítása" in r.getMessage() for r in caplog.records) == 2


def test_indexhiba_utan_is_visszaall_a_fajlido(tmp_path, mappa, monkeypatch):
    folder, paths = mappa
    regi = {path: path.stat() for path in paths}
    befores = _irasok(paths)

    def szinkron_hiba(*_args, **_kwargs):
        raise RuntimeError("index nem elérhető")

    monkeypatch.setattr(timestamp_controller, "sync_tree", szinkron_hiba)

    with pytest.raises(RuntimeError, match="index nem elérhető"):
        _Controller(tmp_path / "index.sqlite")._reindex_folder_keeping_times(
            str(folder), befores
        )

    for path in paths:
        assert path.stat().st_atime_ns == regi[path].st_atime_ns
