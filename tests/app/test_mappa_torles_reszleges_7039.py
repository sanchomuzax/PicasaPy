"""A részleges mappatörlés hivatalos figyelmeztetése és állapotfrissítése (#7039)."""

from __future__ import annotations

import shutil
import time
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest
from PySide6.QtCore import QSettings

from picasapy.app.application_services import wire_fileops
from picasapy.app.controller import AppController
from picasapy.app.fileops_controller import FileOpsController
from picasapy.app.i18n.dictionary import message_origin
from picasapy.app.thumbnail_provider import ThumbnailProvider
from picasapy.index import open_index, sync_tree
from picasapy.thumbs import ThumbnailCache
from support.figyelo import allitsd_le_a_figyelot
from support.jpeg_factory import make_jpeg


_HU_TS = (
    Path(__file__).resolve().parents[2]
    / "src"
    / "picasapy"
    / "app"
    / "i18n"
    / "picasapy_hu.ts"
)
_OFFICIAL_ENGLISH = (
    "The images in the folder have been deleted, but the folder itself will not\n"
    "be deleted due to the presence of additional files and/or folders."
)
_OFFICIAL_HUNGARIAN = (
    "A program a mappában lévő képeket törölte, de magát a mappát nem,\n"
    "mert más fájlok és/vagy mappák is vannak benne."
)
_I18N_DIR = _HU_TS.parent


def _wait(qt_app, predicate, timeout: float = 20.0) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return True
        qt_app.processEvents()
        time.sleep(0.02)
    return bool(predicate())


def _folder_paths(controller) -> set[str]:
    from picasapy.app.models import FolderListModel

    model = controller.folders
    return {
        model.data(model.index(row, 0), FolderListModel.PathRole)
        for row in range(model.rowCount())
        if model.data(model.index(row, 0), FolderListModel.KindRole) == "folder"
    }


@pytest.fixture
def _library(qt_app, tmp_path):
    library = tmp_path / "kepek"
    album = library / "album"
    album.mkdir(parents=True)
    make_jpeg(album / "torolt.jpg")
    leftover = album / "maradek.txt"
    leftover.write_text("a mappa ezért marad", encoding="utf-8")
    db_path = tmp_path / "index.db"
    with open_index(db_path) as conn:
        sync_tree(conn, library)

    controller = AppController(
        db_path,
        (str(library),),
        ThumbnailProvider(ThumbnailCache(tmp_path / "thumbs", size=32)),
        settings=QSettings(
            str(tmp_path / "settings.ini"), QSettings.Format.IniFormat
        ),
        watched_file=tmp_path / "WatchedFolders.txt",
    )
    try:
        controller.start()
        assert _wait(qt_app, lambda: not controller._sync_running), (
            "a kezdő szinkron nem fejeződött be"
        )
        if controller._watcher is not None:
            allitsd_le_a_figyelot(controller)
        if controller._folder_poll_timer is not None:
            controller._folder_poll_timer.stop()
        yield controller, album, db_path
    finally:
        controller.shutdown()
        assert controller.waitForBackgroundWorkers(30.0), "háttérszál nem állt le"


def test_reszleges_hiba_hivatalos_szoveget_ad_es_a_mappafa_a_lemezt_mutatja(
    qt_app, tmp_path, monkeypatch, _library
):
    import picasapy.app.fileops_controller as fileops_module
    from picasapy.index import all_photos, folder_paths_under

    controller, album, db_path = _library
    photo = album / "torolt.jpg"
    leftover = album / "maradek.txt"
    fileops = FileOpsController()
    wire_fileops(fileops, controller)
    failures: list[tuple[str, str]] = []
    deleted: list[str] = []
    fileops.operationFailed.connect(
        lambda operation, message: failures.append((operation, message))
    )
    fileops.folderDeleted.connect(deleted.append)

    def simulated_partial_trash(path: Path, *, trash_dir=None) -> Path:
        del trash_dir
        (path / photo.name).unlink()
        raise OSError("simulated Shell delete failure")

    monkeypatch.setattr(fileops_module, "delete_to_trash", simulated_partial_trash)
    fileops.deleteFolder(str(album))

    assert photo.exists() is False
    assert leftover.exists() is True
    assert album.exists() is True
    assert failures == [("delete_folder", _OFFICIAL_ENGLISH)]
    assert deleted == [], "a részlegesen megmaradt mappát nem szabad töröltként jelezni"

    def index_reflects_partial_state() -> bool:
        with open_index(db_path) as conn:
            paths = folder_paths_under(conn, str(album))
            photos = all_photos(conn)
        return (
            not paths
            and not any(
                record.folder_path == str(album) and record.name == photo.name
                for record in photos
            )
            and not any(record.folder_path == str(album) for record in photos)
            and str(album) not in _folder_paths(controller)
        )

    def current_index_state():
        with open_index(db_path) as conn:
            paths = folder_paths_under(conn, str(album))
            photos = [(record.folder_path, record.name) for record in all_photos(conn)]
        return paths, photos, _folder_paths(controller)

    assert _wait(qt_app, index_reflects_partial_state), (
        "a részleges hiba után az index/mappafa nem a lemezen maradt állapotot "
        f"mutatja (útvonalak, képek, fa: {current_index_state()!r})"
    )


def test_reszleges_hiba_a_figyelt_gyoker_eltunt_almappajat_is_kiveszi_az_indexbol(
    qt_app, monkeypatch, _library
):
    import picasapy.app.fileops_controller as fileops_module
    from picasapy.index import all_photos, folder_paths_under

    controller, album, db_path = _library
    library = album.parent
    leftover = library / "maradek.txt"
    leftover.write_text("a figyelt gyökér megmarad", encoding="utf-8")
    fileops = FileOpsController()
    wire_fileops(fileops, controller)

    def simulated_partial_root_trash(path: Path, *, trash_dir=None) -> Path:
        del trash_dir
        shutil.rmtree(path / album.name)
        raise OSError("simulated Shell delete failure")

    monkeypatch.setattr(fileops_module, "delete_to_trash", simulated_partial_root_trash)
    fileops.deleteFolder(str(library))

    assert library.is_dir() and leftover.exists()
    assert not album.exists()

    def index_reflects_deleted_child() -> bool:
        with open_index(db_path) as conn:
            paths = folder_paths_under(conn, str(album))
            photos = all_photos(conn)
        return not paths and not any(
            record.folder_path == str(album) for record in photos
        )

    assert _wait(qt_app, index_reflects_deleted_child), (
        "részleges gyökértörlés után az eltűnt almappa sora bent maradt az indexben"
    )


def test_hungarian_warning_uses_the_official_picasa_resource():
    from picasapy.app.language_controller import SUPPORTED_LANGUAGES

    for language in SUPPORTED_LANGUAGES:
        root = ET.parse(_I18N_DIR / f"picasapy_{language}.ts").getroot()
        messages = [
            message
            for message in root.iter("message")
            if message.findtext("source") == _OFFICIAL_ENGLISH
        ]
        assert len(messages) == 1, (
            f"{language}: a hivatalos figyelmeztetés hiányzik vagy többszörös"
        )
        message = messages[0]
        assert (message.findtext("translation") or "").strip(), (
            f"{language}: hiányzik a fordítás"
        )
        assert message_origin(message) == "picasa", f"{language}: hibás eredet"
        assert "picasapy-origin-key: stringres:IDS_CANT_DELETE_FOLDER" in (
            message.findtext("extracomment") or ""
        ), f"{language}: hiányzik a hivatalos erőforráskulcs"
        if language == "hu":
            assert message.findtext("translation") == _OFFICIAL_HUNGARIAN
