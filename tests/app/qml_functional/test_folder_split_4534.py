"""#4534 — a menüből indított mappafelosztás vége a fájlokon és az ini-n."""

from __future__ import annotations

import os
import time
from pathlib import Path

import pytest
from PySide6.QtCore import Q_ARG, QMetaObject, QObject, QPoint, QPointF, Qt
from PySide6.QtTest import QTest

from picasapy.index import open_index, sync_tree
from picasapy.ini import (
    load_or_empty,
    parse_document,
    read_folder_date_override,
    save_document,
)
from support.jpeg_factory import make_jpeg

_ALBUM_TOKEN = "604c294a68b0de9cc9222c4714f289d5"
_PERSON_ID = "b8e4117cf1d6615b"
_PERSON_RECT = "3f840000c3509f84"


def _wait(qt_app, condition, timeout_ms=10000):
    hatarido = time.monotonic() + timeout_ms / 1000
    while time.monotonic() < hatarido:
        qt_app.processEvents()
        try:
            if condition():
                return True
        except (AttributeError, RuntimeError):
            pass
        time.sleep(0.02)
    return bool(condition())


def _objektum(window, name):
    obj = window.findChild(QObject, name)
    assert obj is not None, f"{name} nem található"
    return obj


def _click(window, item, qt_app):
    assert item is not None
    assert item.property("enabled") is True, (
        f"{item.objectName()} letiltva; "
        f"dátummező={_objektum(window, 'folderPropertiesDateField').property('text')!r}; "
        f"érvényes={_objektum(window, 'folderPropertiesDialog').property('_dateValid')}; "
        f"dátum={_objektum(window, 'folderPropertiesDialog').property('currentDate')!r}"
    )
    center = item.mapToScene(
        QPointF(float(item.property("width")) / 2,
                float(item.property("height")) / 2)
    )
    target_window = item.window() or window
    QTest.mouseClick(
        target_window,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        QPoint(round(center.x()), round(center.y())),
    )
    qt_app.processEvents()


def _open_photo_menu(window, qt_app, row):
    grid = _objektum(window, "photoGrid")
    QMetaObject.invokeMethod(
        window,
        "openPhotoContextMenu",
        Qt.ConnectionType.DirectConnection,
        Q_ARG("QVariant", row),
        Q_ARG("QVariant", grid),
        Q_ARG("QVariant", 5),
        Q_ARG("QVariant", 5),
    )
    qt_app.processEvents()


def _paths(controller):
    photos = controller.photos
    return [photos.filePathAt(row) for row in range(photos.rowCount())]


def _selected_rows(window):
    value = window.property("selectedIndexes")
    return value.toVariant() if hasattr(value, "toVariant") else list(value)


def _make_split_fixture(library: Path):
    source = library / "forras"
    source.mkdir()
    names = [f"{index:02}.jpg" for index in range(1, 7)]
    document = parse_document("")
    document = document.with_value("Picasa", "description", "Régi leírás")
    document = document.with_value("Picasa", "location", "Régi hely")
    for name in names:
        make_jpeg(
            source / name,
            taken_at="2025:05:03 10:00:00",
        )
        document = document.with_value(name, "star", "1")
        document = document.with_value(name, "caption", f"Felirat {name}")
        document = document.with_value(name, "filters", "sepia=1;")
        document = document.with_value(name, "faces", "rect64(abc),Személy;")
        document = document.with_value(name, "albums", "album-token")
        document = document.with_value(name, "vendor", "megőrzendő")
    save_document(document, source / ".picasa.ini")
    (source / "jegyzet.txt").write_text("marad", encoding="utf-8")
    (source / "05.THM").write_bytes(b"video thumbnail companion")
    originals = source / ".picasaoriginals"
    originals.mkdir()
    (originals / "04.jpg").write_bytes(b"preserved original")
    collision = library / "Cut Name"
    collision.mkdir()
    (collision / "sentinel.txt").write_text("érintetlen", encoding="utf-8")
    return source, names, collision


@pytest.mark.parametrize("height_delta", [-5, 0, 5])
def test_split_menu_click_selects_tail_then_moves_it_to_sibling(
    qml_app, qt_app, tmp_path, height_delta
):
    window, controller, _engine = qml_app
    library = tmp_path / "kepek"
    source, _names, collision = _make_split_fixture(library)
    with open_index(tmp_path / "index.db") as conn:
        sync_tree(conn, library)
    controller._reload_after_sync()
    controller.selectFolder(str(source))
    assert _wait(qt_app, lambda: controller.currentFolder == str(source))
    assert _wait(qt_app, lambda: len(_paths(controller)) >= 6)

    original_height = window.height()
    window.resize(window.width(), original_height + height_delta)
    assert _wait(qt_app, lambda: window.height() == original_height + height_delta)

    grid_paths = _paths(controller)
    source_rows = [
        row for row, path in enumerate(grid_paths) if Path(path).parent == source
    ]
    source_paths = [grid_paths[row] for row in source_rows]
    assert len(source_paths) == 6
    assert source_rows == list(range(source_rows[0], source_rows[0] + 6))
    cut_index = source_rows[2]
    split_rows = source_rows[2:]
    keep_paths = source_paths[:2]
    moved_paths = source_paths[2:]
    cut_date = controller.photos.itemAt(cut_index)["takenAt"][:10]
    assert cut_date == "2025-05-03"
    window.setProperty("selectedIndexes", [cut_index])
    window.setProperty("selectedIndex", cut_index)

    _open_photo_menu(window, qt_app, cut_index)
    menu_item = _objektum(window, "contextMenuSplitFolder")
    assert menu_item.property("visible") is True
    assert menu_item.property("enabled") is True
    _click(window, menu_item, qt_app)

    dialog = _objektum(window, "folderPropertiesDialog")
    assert _wait(qt_app, lambda: dialog.property("opened"))
    # A szinkron megnyitás utáni állapot a párbeszéd előtt kijelölt
    # tartományt őrzi.
    assert _selected_rows(window) == split_rows
    assert dialog.property("currentDate") == "2025-05-03"
    name_field = _objektum(window, "folderPropertiesNameField")
    assert name_field.property("text") in {"Névtelen", "Untitled"}

    capture = os.environ.get("PICASAPY_CAPTURE_MENU_4534")
    if height_delta == 0 and capture:
        screenshot = window.grabWindow()
        assert not screenshot.isNull()
        assert screenshot.save(capture)

    # Mégse után sem mappa, sem ini-módosítás, sem képmozgatás nem történik.
    cancel = _objektum(window, "folderPropertiesCancelButton")
    _click(window, cancel, qt_app)
    assert _wait(qt_app, lambda: not dialog.property("opened"))
    assert all(Path(path).is_file() for path in grid_paths)
    assert not (library / "Cut Name_1").exists()
    assert (source / ".picasa.ini").read_text(encoding="utf-8").count("[Picasa]") == 1

    # Üres kijelölésnél a kattintás csendes; nem nyit tulajdonságablakot.
    _open_photo_menu(window, qt_app, cut_index)
    window.setProperty("selectedIndexes", [])
    window.setProperty("selectedIndex", -1)
    _click(window, menu_item, qt_app)
    qt_app.processEvents()
    assert not dialog.property("opened")
    assert all(Path(path).is_file() for path in grid_paths)

    # Újra megnyitjuk a menüt és ténylegesen a menüpontot kattintjuk.
    _open_photo_menu(window, qt_app, cut_index)
    _click(window, menu_item, qt_app)
    assert _wait(qt_app, lambda: dialog.property("opened"))
    assert _selected_rows(window) == split_rows
    name_field = _objektum(window, "folderPropertiesNameField")
    name_field.setProperty("text", "Cut? Name")
    _objektum(window, "folderPropertiesLocation").setProperty("text", "Lake")
    _objektum(window, "folderPropertiesDescription").setProperty(
        "text", "Új leírás"
    )
    assert _objektum(window, "folderPropertiesLocation").property("enabled") is True
    _click(window, _objektum(window, "folderPropertiesOkButton"), qt_app)

    target = library / "Cut Name_1"
    expected_names = [Path(path).name for path in moved_paths]
    assert _wait(qt_app, lambda: all((target / name).is_file() for name in expected_names))
    assert source.is_dir()
    assert (source / "jegyzet.txt").read_text(encoding="utf-8") == "marad"
    assert (collision / "sentinel.txt").read_text(encoding="utf-8") == "érintetlen"
    assert sorted(path.name for path in source.glob("*.jpg")) == sorted(
        Path(path).name for path in keep_paths
    )
    assert sorted(path.name for path in target.glob("*.jpg")) == sorted(expected_names)
    assert (target / "05.THM").read_bytes() == b"video thumbnail companion"
    assert not (source / "05.THM").exists()
    assert (target / ".picasaoriginals" / "04.jpg").read_bytes() == b"preserved original"
    assert not (source / ".picasaoriginals" / "04.jpg").exists()

    source_doc = load_or_empty(source / ".picasa.ini")
    target_doc = load_or_empty(target / ".picasa.ini")
    assert sorted(section.name for section in source_doc.file_sections()) == sorted(
        Path(path).name for path in keep_paths
    )
    assert sorted(section.name for section in target_doc.file_sections()) == sorted(
        expected_names
    )
    for name in expected_names:
        section = target_doc.section(name)
        assert section.get("star") == "1"
        assert section.get("caption") == f"Felirat {name}"
        assert section.get("filters") == "sepia=1;"
        assert section.get("faces") == "rect64(abc),Személy;"
        assert section.get("albums") == "album-token"
        assert section.get("vendor") == "megőrzendő"
    assert source_doc.section("Picasa").get("description") == "Régi leírás"
    assert source_doc.section("Picasa").get("location") == "Régi hely"
    assert target_doc.section("Picasa").get("description") == "Új leírás"
    assert target_doc.section("Picasa").get("location") == "Lake"
    assert read_folder_date_override(target_doc) == "2025-05-03"


@pytest.mark.parametrize("view", ["album", "person"])
def test_split_menu_is_hidden_in_album_and_people_views(qml_app, qt_app, tmp_path, view):
    window, controller, _engine = qml_app
    library = tmp_path / "kepek"
    ini = parse_document("")
    if view == "album":
        ini = ini.with_value(f".album:{_ALBUM_TOKEN}", "name", "Nyaralás")
        ini = ini.with_value(f".album:{_ALBUM_TOKEN}", "token", _ALBUM_TOKEN)
        ini = ini.with_value("a.jpg", "albums", _ALBUM_TOKEN)
    else:
        ini = ini.with_value("Contacts2", _PERSON_ID, "Roy Avery;;")
        ini = ini.with_value(
            "a.jpg", "faces", f"rect64({_PERSON_RECT}),{_PERSON_ID};"
        )
    save_document(ini, library / ".picasa.ini")
    with open_index(tmp_path / "index.db") as conn:
        sync_tree(conn, library)
    controller._reload_after_sync()
    if view == "album":
        controller.showAlbum(_ALBUM_TOKEN)
    else:
        controller.showPerson("Roy Avery")
    qt_app.processEvents()

    _open_photo_menu(window, qt_app, 0)
    menu_item = _objektum(window, "contextMenuSplitFolder")
    assert menu_item.property("visible") is False
