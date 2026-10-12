"""#4890: a mappamenü egyszer rendez, a kézi lista mappánként megmarad."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QSettings

from picasapy.index import open_index, sync_tree
from picasapy.ini.document import parse_document
from picasapy.ini.priority import olvasd_a_prioritasokat
from support.jpeg_factory import make_jpeg


def _photos(controller, folder: Path) -> list[str]:
    return [
        photo.name
        for photo in controller.photos.photos
        if Path(photo.folder_path) == folder
    ]


def test_nev_szerint_termeszetes_mappankenti_sorrend_tarolodik(
    qt_app, tmp_path
):
    from picasapy.app.controller import AppController
    from picasapy.app.thumbnail_provider import ThumbnailProvider
    from picasapy.thumbs import ThumbnailCache

    root = tmp_path / "kepek"
    target = root / "cel"
    other = root / "masik"
    target.mkdir(parents=True)
    other.mkdir(parents=True)
    # A fájlnév szerinti kezdő sorrend eltér a természetes összevetéstől.
    make_jpeg(target / "kep1.jpg", size=(8, 6), taken_at="2024:01:01 10:00:00")
    make_jpeg(target / "kep10.jpg", size=(8, 6), taken_at="2020:01:01 10:00:00")
    make_jpeg(target / "kep2.jpg", size=(8, 6), taken_at="2022:01:01 10:00:00")
    make_jpeg(other / "masik10.jpg", size=(8, 6))
    make_jpeg(other / "masik2.jpg", size=(8, 6))

    db = tmp_path / "index.db"
    with open_index(db) as conn:
        sync_tree(conn, root)
    settings = QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat)
    # Egy régi globális nézetmód induláskor sem rendezheti át az összes mappát.
    settings.setValue("view/folderPhotoSort", "date")
    settings.setValue("view/folderPhotoSortReverse", True)
    controller = AppController(
        db,
        (str(root),),
        ThumbnailProvider(ThumbnailCache(tmp_path / "thumbs", size=32)),
        settings=settings,
        watched_file=tmp_path / "WatchedFolders.txt",
    )
    controller._reload()
    controller.selectFolder(str(target))

    assert _photos(controller, target) == ["kep1.jpg", "kep10.jpg", "kep2.jpg"]
    untouched_ini = other / ".picasa.ini"
    untouched_before = untouched_ini.read_bytes() if untouched_ini.exists() else None

    assert controller.sortFolderBy(str(target), "name") is True

    assert _photos(controller, target) == ["kep1.jpg", "kep2.jpg", "kep10.jpg"]
    sorted_ini = parse_document((target / ".picasa.ini").read_text(encoding="utf-8"))
    assert olvasd_a_prioritasokat(sorted_ini) == {
        "kep1.jpg": 1.0,
        "kep2.jpg": 2.0,
        "kep10.jpg": 3.0,
    }
    assert (untouched_ini.read_bytes() if untouched_ini.exists() else None) == untouched_before

    # Újratöltés ugyanabból az igazságforrásból az újraindítás utáni sorrendet méri.
    controller._reload()
    controller.selectFolder(str(target))
    assert _photos(controller, target) == ["kep1.jpg", "kep2.jpg", "kep10.jpg"]
    controller.selectFolder(str(other))
    assert _photos(controller, other) == ["masik10.jpg", "masik2.jpg"]
