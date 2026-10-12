"""#4589: az egyéni mappagyűjtemények forrása a `.picasa.ini` P2category-ja."""

# rontás-kontroll: picasapy.ini.folder_category.FOLDER_SECTION = "Broken" → 3 failed

from __future__ import annotations

import json

from PySide6.QtCore import QSettings

from picasapy.ini import load_document, read_folder_category
from picasapy.scanner import PICASA_INI_NAME
from support.jpeg_factory import make_jpeg


def _make_library(root):
    library = root / "kepek"
    for name, category in (("tech", "tech"), ("plain", "Folders on Disk")):
        folder = library / name
        folder.mkdir(parents=True)
        make_jpeg(folder / "a.jpg")
        (folder / PICASA_INI_NAME).write_bytes(
            (
                "[Picasa]\r\n"
                f"P2category={category}\r\n"
                "name=Keep this metadata\r\n"
                "[a.jpg]\r\n"
                "star=yes\r\n"
            ).encode("utf-8")
        )
    return library


def _new_controller(qt_app, tmp_path, library, settings):
    from picasapy.app.controller import AppController
    from picasapy.app.thumbnail_provider import ThumbnailProvider
    from picasapy.index import open_index, sync_tree
    from picasapy.thumbs import ThumbnailCache

    with open_index(tmp_path / "index.db") as conn:
        sync_tree(conn, library)
    controller = AppController(
        tmp_path / "index.db",
        (str(library),),
        ThumbnailProvider(ThumbnailCache(tmp_path / "thumbs", size=32)),
        settings=settings,
        watched_file=tmp_path / "WatchedFolders.txt",
    )
    controller._reload_after_sync()
    return controller


def _settings(tmp_path):
    return QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat)


def test_ini_custom_collection_is_listed(qt_app, tmp_path):
    library = _make_library(tmp_path)
    controller = _new_controller(qt_app, tmp_path, library, _settings(tmp_path))

    collections = controller.customCollections
    assert collections == [
        {"name": "tech", "folders": [str(library / "tech")], "closed": False}
    ]


def test_existing_qsettings_assignment_migrates_to_ini_and_round_trips(
    qt_app, tmp_path
):
    library = _make_library(tmp_path)
    folder = library / "plain"
    ini_path = folder / PICASA_INI_NAME
    eredeti = ini_path.read_bytes()
    settings = _settings(tmp_path)
    settings.setValue(
        "collections/custom",
        json.dumps(
            [{"name": "Régi gyűjtemény", "folders": [str(folder)], "closed": False}],
            ensure_ascii=False,
        ),
    )
    settings.sync()

    controller = _new_controller(qt_app, tmp_path, library, settings)

    assert read_folder_category(load_document(ini_path)) == "Régi gyűjtemény"
    assert ini_path.read_bytes() == eredeti.replace(
        b"P2category=Folders on Disk", "P2category=Régi gyűjtemény".encode("utf-8")
    )
    assert controller.customCollections == [
        {
            "name": "Régi gyűjtemény",
            "folders": [str(folder)],
            "closed": False,
        },
        {"name": "tech", "folders": [str(library / "tech")], "closed": False},
    ]
    migrated = json.loads(settings.value("collections/custom"))
    assert migrated == [
        {"name": "Régi gyűjtemény", "folders": [], "closed": False}
    ]


def test_moving_folder_writes_p2category_and_updates_the_collection(
    qt_app, tmp_path
):
    library = _make_library(tmp_path)
    settings = _settings(tmp_path)
    controller = _new_controller(qt_app, tmp_path, library, settings)
    ini_path = library / "plain" / PICASA_INI_NAME
    before = ini_path.read_bytes()

    controller.createCollection("Utazás")
    controller.moveFolderToCollection(str(library / "plain"), "Utazás")

    assert read_folder_category(load_document(ini_path)) == "Utazás"
    assert ini_path.read_bytes() == before.replace(
        b"P2category=Folders on Disk", "P2category=Utazás".encode("utf-8")
    )
    assert controller.customCollections == [
        {"name": "tech", "folders": [str(library / "tech")], "closed": False},
        {"name": "Utazás", "folders": [str(library / "plain")], "closed": False},
    ]
