"""#4482: a mappa átnevezése frissítse a listát, a képeket és az indexet."""

from __future__ import annotations

import sqlite3
import time
from pathlib import Path

import pytest

from PySide6.QtCore import QSettings

import picasapy.app.library_controller as library_module
from picasapy.app.controller import AppController
from picasapy.app.models import FolderListModel
from picasapy.app.thumbnail_provider import ThumbnailProvider
from picasapy.index import open_index, sync_tree
from picasapy.ini import (
    parse_document,
    save_document,
    with_folder_date_override,
    with_folder_music,
)
from picasapy.thumbs import ThumbnailCache

from support.jpeg_factory import make_jpeg


def _var(qt_app, condition, seconds=8.0):
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        try:
            if condition():
                return True
        except (AttributeError, RuntimeError, sqlite3.Error):
            pass
        qt_app.processEvents()
        time.sleep(0.02)
    return bool(condition())


@pytest.fixture
def indexed_library(qt_app, tmp_path):
    root = tmp_path / "library"
    folder = root / "old-name"
    (folder / "child").mkdir(parents=True)
    make_jpeg(folder / "photo.jpg")
    make_jpeg(folder / "child" / "nested.jpg")
    music = tmp_path / "background.mp3"
    music.write_bytes(b"zene")
    ini = parse_document("").with_value(
        "Picasa", "description", "Megőrzött leírás"
    )
    ini = with_folder_date_override(ini, "2024-02-03")
    ini = with_folder_music(ini, True, str(music))
    save_document(ini, folder / ".picasa.ini")

    db_path = tmp_path / "index.db"
    with open_index(db_path) as conn:
        sync_tree(conn, root)
    provider = ThumbnailProvider(ThumbnailCache(tmp_path / "thumbs", size=32))
    settings = QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat)
    controller = AppController(db_path, (str(root),), provider, settings=settings)
    controller._reload()
    controller.selectFolder(str(folder))
    yield controller, root, folder, db_path, music
    controller.shutdown()
    assert controller.waitForBackgroundWorkers(30.0), "háttérmunka nem állt le"


def _folder_paths(controller):
    model = controller.folders
    return {
        model.data(model.index(row, 0), FolderListModel.PathRole)
        for row in range(model.rowCount())
        if model.data(model.index(row, 0), FolderListModel.KindRole) == "folder"
    }


def test_atnevezes_utan_a_mappalista_a_kepek_es_az_index_is_koveti(
    indexed_library,
):
    controller, root, source, db_path, music = indexed_library
    target = root / "new-name"

    result = controller.renameFolder(str(source), "new-name")

    assert result["ok"] is True
    assert result["path"] == str(target)
    assert not source.exists()
    assert target.is_dir()
    assert controller._current_folder == str(target)
    assert str(target) in _folder_paths(controller)
    assert str(target / "child") in _folder_paths(controller)
    assert str(source) not in _folder_paths(controller)
    assert [
        photo.name
        for photo in controller.photos.photos
        if photo.folder_path == str(target)
    ] == ["photo.jpg"]
    assert controller.folderDescriptionOf(str(target)) == "Megőrzött leírás"
    assert controller.folderDateOverride(str(target)) == "2024-02-03"
    assert controller.folderMusicEnabled(str(target)) is True
    assert controller.folderMusicFile(str(target)) == str(music)
    with open_index(db_path) as conn:
        paths = {
            row[0] for row in conn.execute("SELECT path FROM folders")
        }
    assert str(target) in paths and str(target / "child") in paths
    assert str(source) not in paths


def test_indexhiba_utan_a_lemezes_atnevezes_visszagordul(
    indexed_library, monkeypatch
):
    controller, root, source, db_path, _music = indexed_library
    target = root / "new-name"

    def fail(*_args, **_kwargs):
        raise sqlite3.OperationalError("teszt indexhiba")

    monkeypatch.setattr(library_module, "move_folder_tree", fail)
    result = controller.renameFolder(str(source), "new-name")

    assert result["ok"] is False
    assert "index" in result["error"].lower()
    assert source.is_dir()
    assert not target.exists()
    with open_index(db_path) as conn:
        paths = {row[0] for row in conn.execute("SELECT path FROM folders")}
    assert str(source) in paths
    assert str(target) not in paths


def test_csak_kis_nagybetu_elteresnel_a_mappat_es_az_indexet_is_atirja(
    indexed_library,
):
    controller, root, _source, db_path, _music = indexed_library
    source = root / "Foo"
    (source / "child").mkdir(parents=True)
    make_jpeg(source / "photo.jpg")
    make_jpeg(source / "child" / "nested.jpg")
    with open_index(db_path) as conn:
        sync_tree(conn, root)
    controller._reload(preserve_scroll=True)

    result = controller.renameFolder(str(source), "foo")

    target = root / "foo"
    assert result == {"ok": True, "path": str(target), "name": "foo"}
    assert target.is_dir() and not source.exists()
    assert (target / "photo.jpg").is_file()
    assert (target / "child" / "nested.jpg").is_file()
    with open_index(db_path) as conn:
        paths = {row[0] for row in conn.execute("SELECT path FROM folders")}
    assert str(target) in paths
    assert str(target / "child") in paths
    assert str(source) not in paths
    assert any(photo.folder_path == str(target) for photo in controller.photos.photos)


def test_valodi_indexelt_celutkozesnel_nem_nevez_at(indexed_library):
    controller, root, _source, db_path, _music = indexed_library
    source = root / "Foo"
    target = root / "bar"
    source.mkdir()
    target.mkdir()
    make_jpeg(source / "photo.jpg")
    (target / "sentinel.txt").write_text("marad", encoding="utf-8")
    with open_index(db_path) as conn:
        sync_tree(conn, root)
    controller._reload(preserve_scroll=True)

    result = controller.renameFolder(str(source), "bar")

    assert result["ok"] is False
    assert "már létezik" in result["error"]
    assert source.is_dir() and target.is_dir()
    assert (source / "photo.jpg").is_file()
    assert (target / "sentinel.txt").read_text(encoding="utf-8") == "marad"


def test_atnevezeskor_a_kis_nagybetuvel_eltero_testver_indexe_erintetlen(
    indexed_library,
):
    controller, root, _source, db_path, _music = indexed_library
    source = root / "Foo"
    sibling = root / "foo"
    if source == sibling:
        pytest.skip("ez a fájlrendszer nem tárol különböző betűzésű testvéreket")
    (source / "child").mkdir(parents=True)
    (sibling / "child").mkdir(parents=True)
    make_jpeg(source / "child" / "source.jpg")
    make_jpeg(sibling / "child" / "sibling.jpg")
    with open_index(db_path) as conn:
        sync_tree(conn, root)
    controller._reload(preserve_scroll=True)

    result = controller.renameFolder(str(source), "Bar")

    target = root / "Bar"
    assert result == {"ok": True, "path": str(target), "name": "Bar"}
    assert (target / "child" / "source.jpg").is_file()
    assert (sibling / "child" / "sibling.jpg").is_file()
    with open_index(db_path) as conn:
        paths = {row[0] for row in conn.execute("SELECT path FROM folders")}
        photos = {
            row[0]
            for row in conn.execute(
                "SELECT f.path || '/' || p.name "
                "FROM photos p JOIN folders f ON f.id = p.folder_id"
            )
        }
    assert str(target / "child") in paths
    assert str(sibling / "child") in paths
    assert str(target / "child" / "source.jpg") in photos
    assert str(sibling / "child" / "sibling.jpg") in photos


def test_nem_nevez_at_amig_a_mappa_kepe_szerkesztes_alatt_all(
    indexed_library,
):
    controller, _root, source, _db_path, _music = indexed_library

    class ActiveEditor:
        _image_path = source / "photo.jpg"

    controller.set_edit_controllers(ActiveEditor())

    result = controller.renameFolder(str(source), "new-name")

    assert result["ok"] is False
    assert "szerkesztés alatt" in result["error"]
    assert source.is_dir()
    assert not source.with_name("new-name").exists()


def test_az_utoellenorzo_figyelo_futas_utan_is_megmaradnak_a_mappaadatok(
    indexed_library, qt_app
):
    controller, _root, source, _db_path, music = indexed_library
    controller.start()
    assert _var(qt_app, lambda: not controller._sync_running), (
        "az induló indexszinkron nem fejeződött be"
    )
    controller.selectFolder(str(source))
    befejezesek = []
    controller.syncFinished.connect(lambda: befejezesek.append(True))

    result = controller.renameFolder(str(source), "after-watch")
    target = source.with_name("after-watch")

    assert result["ok"] is True
    assert _var(qt_app, lambda: bool(befejezesek)), (
        "az átnevezés watcher-eseménye nem futott le"
    )
    assert controller.folderDescriptionOf(str(target)) == "Megőrzött leírás"
    assert controller.folderDateOverride(str(target)) == "2024-02-03"
    assert controller.folderMusicEnabled(str(target)) is True
    assert controller.folderMusicFile(str(target)) == str(music)
    assert str(target) in _folder_paths(controller)
    assert str(source) not in _folder_paths(controller)


def test_a_nev_mezo_mappanal_is_szerkesztheto_es_megnyitaskor_kijelolt():
    qml = (
        Path(__file__).resolve().parents[2]
        / "src/picasapy/app/qml/PicasaPy/FolderPropertiesDialog.qml"
    ).read_text(encoding="utf-8")
    name_field = qml.split(
        'objectName: "folderPropertiesNameField"', 1
    )[1].split("}", 1)[0]
    opened = qml.split("onOpened:", 1)[1].split("onAccepted:", 1)[0]

    assert "enabled: root.albumMode" not in name_field
    assert "selectAll()" in opened
