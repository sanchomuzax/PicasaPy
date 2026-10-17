"""A könyvtárfigyelő csak az érintett részfát dolgozza fel (#5177)."""

from __future__ import annotations

import shutil
import time
from pathlib import Path

import pytest

from support.jpeg_factory import make_jpeg
from picasapy.scanner import DirectoryChange


def _wait(qt_app, predicate, timeout: float = 15.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        qt_app.processEvents()
        if predicate():
            return
        time.sleep(0.05)
    pytest.fail("A háttér-szinkron nem fejeződött be határidőn belül")


@pytest.fixture
def library_controller(qt_app, tmp_path):
    from PySide6.QtCore import QSettings

    from picasapy.app.controller import AppController
    from picasapy.app.thumbnail_provider import ThumbnailProvider
    from picasapy.index import open_index, sync_tree
    from picasapy.thumbs import ThumbnailCache

    root = tmp_path / "kepek"
    old = root / "regi"
    old.mkdir(parents=True)
    make_jpeg(old / "kep.jpg", size=(32, 32))
    database = tmp_path / "index.db"
    with open_index(database) as conn:
        sync_tree(conn, root)

    provider = ThumbnailProvider(ThumbnailCache(tmp_path / "thumbs", size=32))
    settings = QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat)
    controller = AppController(
        database,
        (str(root),),
        provider,
        settings=settings,
        watched_file=tmp_path / "WatchedFolders.txt",
    )
    controller._reload()
    yield controller, root, database
    assert controller.waitForBackgroundWorkers(30.0), "háttérszál nem állt le"


def _sync_finished(qt_app, controller, emit):
    finished = []
    controller.syncFinished.connect(lambda: finished.append(True))
    emit()
    _wait(qt_app, lambda: bool(finished))


def test_torolt_mappanal_nincs_lemezolvasas_es_az_indexbol_is_torli(
    library_controller, qt_app, monkeypatch
):
    controller, root, database = library_controller
    removed = root / "regi"
    shutil.rmtree(removed)

    import picasapy.app.library_controller as library_module

    disk_reads = []
    monkeypatch.setattr(
        library_module,
        "sync_folder",
        lambda *args, **kwargs: disk_reads.append(("folder", args, kwargs)),
    )
    monkeypatch.setattr(
        controller,
        "_sync_tree",
        lambda *args, **kwargs: disk_reads.append(("tree", args, kwargs)),
    )

    _sync_finished(
        qt_app,
        controller,
        lambda: controller._on_folders_dirty(
            [DirectoryChange(str(removed), "deleted"), str(removed)]
        ),
    )

    assert disk_reads == [], "törlés után a watcher bejárta a lemezt"
    from picasapy.index import open_index

    with open_index(database) as conn:
        assert conn.execute(
            "SELECT 1 FROM folders WHERE path = ?", (str(removed),)
        ).fetchone() is None
        assert conn.execute(
            "SELECT 1 FROM photos p JOIN folders f ON f.id = p.folder_id "
            "WHERE f.path = ? LIMIT 1",
            (str(removed),),
        ).fetchone() is None


def test_uj_mappanal_csak_az_uj_reszfa_szinkronizalodik(
    library_controller, qt_app, monkeypatch
):
    controller, root, database = library_controller
    created = root / "uj"
    nested = created / "belso"
    excluded = created / "kihagyott"
    nested.mkdir(parents=True)
    excluded.mkdir()
    make_jpeg(created / "gyoker.jpg", size=(32, 32))
    make_jpeg(nested / "uj.jpg", size=(32, 32))
    make_jpeg(excluded / "ne-indexeld.jpg", size=(32, 32))
    controller.setFolderManagerState(str(excluded), "none")

    from picasapy.app import controller as controller_module
    from picasapy.index import sync_tree as real_sync_tree

    tree_calls = []

    def record_tree(conn, scan_root, **kwargs):
        tree_calls.append(
            (Path(scan_root), tuple(Path(path) for path in kwargs.get("exclude", ())))
        )
        return real_sync_tree(conn, scan_root, **kwargs)

    monkeypatch.setattr(controller_module, "sync_tree", record_tree)
    import picasapy.app.library_controller as library_module

    monkeypatch.setattr(
        library_module,
        "sync_folder",
        lambda *args, **kwargs: pytest.fail("új mappánál sync_folder futott"),
    )

    _sync_finished(
        qt_app,
        controller,
        lambda: controller._on_folders_dirty(
            [DirectoryChange(str(created), "created"), str(created)]
        ),
    )

    assert tree_calls == [(created, (excluded,))]
    from picasapy.index import open_index

    with open_index(database) as conn:
        indexed = {
            Path(row[0])
            for row in conn.execute("SELECT path FROM folders")
            if Path(row[0]).is_relative_to(created)
        }
    assert indexed == {created, nested}
