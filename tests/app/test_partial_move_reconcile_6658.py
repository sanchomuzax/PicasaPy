"""Sikertelen fájlmozgatás után a forrás és a cél is egyezzen a lemezzel (#6658)."""

from pathlib import Path
import time

from PySide6.QtCore import QSettings

from picasapy.app.application_services import wire_fileops
from picasapy.app.fileops_controller import FileOpsController
from picasapy.fileops import batch
from support.figyelo import allitsd_le_a_figyelot
from support.jpeg_factory import make_jpeg


def _wait(qt_app, predicate, timeout: float = 20.0) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return True
        qt_app.processEvents()
        time.sleep(0.02)
    return bool(predicate())


class _LibraryController:
    def __init__(self, root: Path) -> None:
        self.watchedFolders = [str(root)]
        self.resynced = []

    def resyncFolder(self, folder: str) -> None:
        self.resynced.append(folder)


def test_failed_move_refreshes_both_folders_and_reports_file_and_reason(
    qt_app, tmp_path, monkeypatch
):
    root = tmp_path / "kepek"
    source = root / "202611-a"
    destination = root / "202611"
    source.mkdir(parents=True)
    destination.mkdir()
    locked = source / "locked.jpg"
    locked.write_bytes(b"kep")

    def fail_due_to_lock(_path: Path, _folder: Path) -> Path:
        raise PermissionError("a fájl zárolt")

    monkeypatch.setattr(batch, "_move_with_rename", fail_due_to_lock)
    library = _LibraryController(root)
    fileops = FileOpsController()
    wire_fileops(fileops, library)
    summaries = []
    fileops.batchFinished.connect(lambda *items: summaries.append(tuple(items)))

    fileops.movePhotos([str(locked)], str(destination), "rename")

    assert locked.exists(), "a sikertelen mozgatás nem hagyhatja el a forrást"
    assert not (destination / locked.name).exists()
    assert [Path(path) for path in library.resynced] == [source, destination], (
        "a köteg hibára futott, de a lemez szerinti forrás/cél egyeztetés elmaradt"
    )
    assert summaries == [("move", 0, 0, 1, "locked.jpg: a fájl zárolt")]


def test_every_failed_file_and_reason_is_kept_in_the_batch_summary(
    qt_app, tmp_path, monkeypatch
):
    root = tmp_path / "kepek"
    source = root / "202611-a"
    destination = root / "202611"
    source.mkdir(parents=True)
    destination.mkdir()
    first = source / "first.jpg"
    second = source / "second.jpg"
    first.write_bytes(b"elso")
    second.write_bytes(b"masodik")

    def fail_due_to_lock(path: Path, _folder: Path) -> Path:
        raise PermissionError(f"{path.name} zárolt")

    monkeypatch.setattr(batch, "_move_with_rename", fail_due_to_lock)
    library = _LibraryController(root)
    fileops = FileOpsController()
    wire_fileops(fileops, library)
    summaries = []
    fileops.batchFinished.connect(lambda *items: summaries.append(tuple(items)))

    fileops.movePhotos([str(first), str(second)], str(destination), "rename")

    assert summaries[0][:4] == ("move", 0, 0, 2)
    assert "first.jpg: first.jpg zárolt" in summaries[0][4]
    assert "second.jpg: second.jpg zárolt" in summaries[0][4]
    assert first.exists() and second.exists()


def test_partial_move_keeps_failed_photo_in_grid_and_matches_folder_count(
    qt_app, tmp_path, monkeypatch
):
    from picasapy.app import application as app_module
    from picasapy.app.controller import AppController
    from picasapy.app.folder_list_model import FolderListModel
    from picasapy.app.thumbnail_provider import ThumbnailProvider
    from picasapy.index import open_index, photos_in_folder, sync_tree
    from picasapy.thumbs import ThumbnailCache

    root = tmp_path / "kepek"
    source = root / "202611-a"
    destination = root / "202611"
    source.mkdir(parents=True)
    destination.mkdir()
    moved = source / "moved.jpg"
    locked = source / "locked.jpg"
    make_jpeg(moved)
    make_jpeg(locked)
    database = tmp_path / "index.db"
    with open_index(database) as conn:
        sync_tree(conn, root)

    controller = AppController(
        database,
        (str(root),),
        ThumbnailProvider(ThumbnailCache(tmp_path / "thumbs", size=32)),
        settings=QSettings(
            str(tmp_path / "settings.ini"), QSettings.Format.IniFormat
        ),
        watched_file=tmp_path / "WatchedFolders.txt",
    )
    controller.start()
    assert _wait(qt_app, lambda: not controller._sync_running)
    if controller._watcher is not None:
        allitsd_le_a_figyelot(controller)
    if controller._folder_poll_timer is not None:
        controller._folder_poll_timer.stop()
    assert _wait(qt_app, lambda: not controller._dirty_running)
    controller.selectFolder(str(source))

    real_move = batch._move_with_rename

    def move_unless_locked(path: Path, folder: Path) -> Path:
        if path == locked:
            raise PermissionError("a fájl zárolt")
        return real_move(path, folder)

    monkeypatch.setattr(batch, "_move_with_rename", move_unless_locked)
    fileops = FileOpsController()
    app_module.wire_fileops(fileops, controller)
    failed_moves = []
    summaries = []
    fileops.photoMoveFailed.connect(
        lambda old, new: failed_moves.append((old, new))
    )
    fileops.batchFinished.connect(lambda *items: summaries.append(tuple(items)))

    fileops.movePhotos([str(moved), str(locked)], str(destination), "rename")

    assert locked.exists()
    assert not moved.exists()
    assert (destination / moved.name).exists()
    assert [tuple(Path(path) for path in pair) for pair in failed_moves] == [
        (locked, destination / locked.name)
    ]
    assert summaries[0][:4] == ("move", 1, 0, 1)
    assert summaries[0][4].startswith("locked.jpg: a fájl zárolt")

    def source_records():
        return [
            record
            for record in controller.photos.photos
            if Path(record.folder_path) == source
        ]

    def destination_records():
        return [
            record
            for record in controller.photos.photos
            if Path(record.folder_path) == destination
        ]

    assert _wait(
        qt_app,
        lambda: len(source_records()) == 1 and len(destination_records()) == 1,
    ), "a részleges mozgatás után a rács nem a lemezt követi"

    folder_model = controller.folders
    source_count = next(
        folder_model.data(folder_model.index(row, 0), FolderListModel.CountRole)
        for row in range(folder_model.rowCount())
        if folder_model.data(
            folder_model.index(row, 0), FolderListModel.PathRole
        )
        == str(source)
    )
    with open_index(database) as conn:
        assert len(photos_in_folder(conn, source)) == 1
        assert len(photos_in_folder(conn, destination)) == 1
    assert source_count == len(source_records()) == 1

    controller.shutdown()
    assert controller.waitForBackgroundWorkers(30.0)


def test_az_osszegzo_legfeljebb_tiz_hibasort_mutat_a_tobbit_szammal():
    from types import SimpleNamespace

    from picasapy.app.fileops_controller import _first_failure_reason

    hibak = tuple((Path(f"/k/kep{i:02}.jpg"), "zárolt") for i in range(12))
    sorok = _first_failure_reason(SimpleNamespace(failed=hibak)).split("\n")

    assert sorok[:2] == ["kep00.jpg: zárolt", "kep01.jpg: zárolt"]
    assert len(sorok) == 11
    assert sorok[-1] == "… (+2)"
