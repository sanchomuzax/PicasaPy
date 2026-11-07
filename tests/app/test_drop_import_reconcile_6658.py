"""Ismert mappa újbóli behúzása kényszerítse ki a lemez szerinti javítást (#6658)."""

import time
from pathlib import Path

import pytest
from PySide6.QtCore import QSettings

from support.jpeg_factory import make_jpeg


def _wait(qt_app, predicate, timeout: float = 20.0) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return True
        qt_app.processEvents()
        time.sleep(0.02)
    return bool(predicate())


@pytest.fixture
def stale_library(qt_app, tmp_path):
    from picasapy.app.controller import AppController
    from picasapy.app.thumbnail_provider import ThumbnailProvider
    from picasapy.index import open_index, sync_tree
    from picasapy.thumbs import ThumbnailCache

    library = tmp_path / "kepek"
    source = library / "202611-a"
    destination = library / "202611"
    source.mkdir(parents=True)
    destination.mkdir()
    image = source / "IMG_0001.jpg"
    make_jpeg(image)
    make_jpeg(destination / "IMG_0002.jpg")
    database = tmp_path / "index.db"
    with open_index(database) as conn:
        sync_tree(conn, library)

    controller = AppController(
        database,
        (str(library),),
        ThumbnailProvider(ThumbnailCache(tmp_path / "thumbs", size=32)),
        settings=QSettings(
            str(tmp_path / "settings.ini"), QSettings.Format.IniFormat
        ),
        watched_file=tmp_path / "WatchedFolders.txt",
    )
    controller.start()
    assert _wait(qt_app, lambda: not controller._sync_running)
    if controller._watcher is not None:
        controller._watcher.stop()
    if controller._folder_poll_timer is not None:
        controller._folder_poll_timer.stop()

    # A mozgatás után visszamaradt hibás állapot: a kép a lemezen a
    # forrásmappában van, az SQLite-sor viszont a célmappára mutat.
    with open_index(database) as conn:
        source_id = conn.execute(
            "SELECT id FROM folders WHERE path = ?", (str(source),)
        ).fetchone()[0]
        destination_id = conn.execute(
            "SELECT id FROM folders WHERE path = ?", (str(destination),)
        ).fetchone()[0]
        conn.execute(
            "UPDATE photos SET folder_id = ? WHERE folder_id = ? AND name = ?",
            (destination_id, source_id, image.name),
        )
        conn.commit()
    controller._reload()
    controller.selectFolder(str(source))
    assert not any(
        Path(record.folder_path) == source for record in controller.photos.photos
    )

    yield controller, library, source, destination, image

    controller.shutdown()
    assert controller.waitForBackgroundWorkers(30.0)


def test_dropping_a_photo_in_a_known_folder_repairs_stale_index(stale_library, qt_app):
    from picasapy.app.drop_import_controller import DropImportController
    from picasapy.app.folder_list_model import FolderListModel
    from picasapy.index import open_index, photos_in_folder

    controller, library, source, destination, image = stale_library
    drop = DropImportController(
        add_folder=controller.addWatchedFolder,
        refresh_folder=controller.refreshDroppedFolder,
    )

    drop.importDroppedUrls([image.as_uri()])

    assert _wait(
        qt_app,
        lambda: any(
            Path(record.folder_path) == source for record in controller.photos.photos
        ),
    ), (
        "az ismert forrásmappa behúzása nem olvasta újra a lemezt"
    )
    source_photos = [
        record
        for record in controller.photos.photos
        if Path(record.folder_path) == source
    ]
    assert len(source_photos) == 1

    index = controller.folders
    source_count = next(
        index.data(index.index(row, 0), FolderListModel.CountRole)
        for row in range(index.rowCount())
        if Path(index.data(index.index(row, 0), FolderListModel.PathRole)) == source
    )
    assert source_count == len(source_photos) == 1
    with open_index(controller._db_path) as conn:
        assert len(photos_in_folder(conn, source)) == 1
        assert len(photos_in_folder(conn, destination)) == 1
