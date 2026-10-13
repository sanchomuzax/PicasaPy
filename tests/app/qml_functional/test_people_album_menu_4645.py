"""Az Emberek-album helyi menüje az eredeti tételsort követi (#4645)."""

from __future__ import annotations

import os
import shutil
import time
from pathlib import Path

import pytest
from PySide6.QtCore import QObject, QPoint, QPointF, QUrl, Qt
from PySide6.QtQml import QQmlComponent, QQmlEngine
from PySide6.QtQuick import QQuickItem
from PySide6.QtTest import QTest

from picasapy.index import open_index, sync_tree

_PERSON_ID = "aaaaaaaaaaaaaaaa"
_FACE_RECT = "1e00280045006e00"
_HEIGHT_OFFSETS = (-5, 0, 5)
_MENU_ORDER = (
    "peopleAlbumMenuEdit",
    "peopleAlbumMenuSeparatorAfterEdit",
    "peopleAlbumMenuSelectAll",
    "peopleAlbumMenuClearSelection",
    "peopleAlbumMenuInvertSelection",
    "peopleAlbumMenuSeparatorAfterSelection",
    "peopleAlbumMenuRefreshThumbnails",
    "peopleAlbumMenuSeparatorBeforeDelete",
    "peopleAlbumMenuDelete",
)
_MENU_TEXT = {
    "peopleAlbumMenuEdit": "&Edit People Album...",
    "peopleAlbumMenuSelectAll": "Select &All\tCtrl+A",
    "peopleAlbumMenuClearSelection": "&Clear Selection\tCtrl+D",
    "peopleAlbumMenuInvertSelection": "&Invert Selection\tCtrl+I",
    "peopleAlbumMenuRefreshThumbnails": "&Refresh Thumbnails",
    "peopleAlbumMenuDelete": "&Delete People Album",
}
_KEEPALIVE: list[object] = []


@pytest.fixture
def menu_engine(qt_app):
    import picasapy.app.application as app_module

    engine = QQmlEngine()
    engine.addImportPath(str(app_module._APP_DIR / "qml"))
    yield engine
    engine.deleteLater()


def _load_menu(engine):
    component = QQmlComponent(engine)
    component.setData(
        b"import QtQuick\nimport PicasaPy 1.0\n"
        b'PeopleAlbumContextMenu { objectName: "peopleMenuTest" }\n',
        QUrl(),
    )
    assert component.isReady(), component.errors()
    menu = component.create()
    assert menu is not None, component.errors()
    _KEEPALIVE.extend((component, menu))
    return menu


def _wait(qt_app, condition, seconds: float = 3.0) -> bool:
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        qt_app.processEvents()
        if condition():
            return True
        time.sleep(0.05)
    qt_app.processEvents()
    return bool(condition())


def _find(root, object_name):
    return root.findChild(QObject, object_name)


def _walk(item: QQuickItem):
    for child in item.childItems():
        yield child
        yield from _walk(child)


def _visible_item(root, object_name):
    return next(
        (
            item
            for item in _walk(root.contentItem())
            if item.objectName() == object_name and item.isVisible()
        ),
        None,
    )


def _click(qt_app, item, button=Qt.MouseButton.LeftButton):
    assert item is not None, "a kattintandó felületi elem hiányzik"
    assert item.property("enabled") is not False, (
        f"{item.objectName()}: a művelet le van tiltva"
    )
    assert item.width() > 0 and item.height() > 0
    point = item.mapToScene(QPointF(item.width() / 2, item.height() / 2))
    QTest.mouseClick(
        item.window(),
        button,
        Qt.KeyboardModifier.NoModifier,
        QPoint(round(point.x()), round(point.y())),
    )
    qt_app.processEvents()


def _prepare_person(window, controller, qt_app, height_offset):
    target_height = int(window.height()) + height_offset
    window.setHeight(target_height)
    assert _wait(qt_app, lambda: int(window.height()) == target_height)

    paths = [
        Path(controller.photos.filePathAt(row))
        for row in range(controller.photos.rowCount())
    ]
    assert len(paths) >= 2, "a részleges kijelöléshez legalább két kép kell"
    library = paths[0].parent
    ini_path = library / ".picasa.ini"
    image_sections = "".join(
        f"[{path.name}]\nfaces=rect64({_FACE_RECT}),{_PERSON_ID}\n"
        for path in paths[:2]
    )
    ini_path.write_text(
        "[Contacts2]\n"
        f"{_PERSON_ID}=Anna;anna@example.test;gaia-anna\n"
        f"{image_sections}",
        encoding="utf-8",
    )
    with open_index(controller._db_path) as conn:
        sync_tree(conn, library)
    controller._reload_after_sync()
    pane = _find(window, "folderPane")
    assert pane is not None
    pane.setProperty("peopleCollapsed", False)
    assert _wait(
        qt_app,
        lambda: _visible_item(window, "personItem_Anna") is not None,
    ), "az Anna Emberek-album sora nem jelent meg"
    assert _wait(
        qt_app,
        lambda: controller.photos.rowCount() == len(paths),
    ), "a két címkézett kép nem jelent meg a látható rácsban"
    # A nézet állva marad, így a menütétel a látható rácscsoporton dolgozik.
    pane = _find(window, "folderPane")
    assert pane is not None
    return pane, library, ini_path, len(paths)


def _click_person_menu_item(window, pane, qt_app, item_name, capture=False):
    row = _visible_item(window, "personItem_Anna")
    _click(qt_app, row, Qt.MouseButton.RightButton)
    menu = _find(pane, "peopleAlbumContextMenu")
    assert _wait(
        qt_app, lambda: menu is not None and menu.property("visible") is True
    ), "az Emberek-album helyi menüje nem nyílt meg"
    if capture:
        output = Path(__file__).resolve().parents[3] / "kep-4645.png"
        assert window.grabWindow().save(str(output)), (
            f"nem sikerült a menü képét ide menteni: {output}"
        )
    item = _find(menu, item_name)
    assert item is not None, f"a menütétel hiányzik: {item_name}"
    assert item.property("enabled") is True, f"{item_name}: a tétel le van tiltva"
    _click(qt_app, item)


def _selected_rows(window) -> list[int]:
    value = window.property("selectedIndexes")
    return list(value.toVariant()) if hasattr(value, "toVariant") else list(value)


def test_emberek_menu_sorrendje_feliratai_es_gyorsbillentyui(menu_engine):
    menu = _load_menu(menu_engine)
    names = [
        child.objectName()
        for child in menu.findChildren(QObject)
        if child.objectName() in _MENU_ORDER
    ]
    assert names == list(_MENU_ORDER)
    assert _find(menu, "peopleAlbumMenuSortAlbumBy") is None, (
        "az album-rendezés almenü csak a #4599 után kerül ebbe a menübe"
    )
    for name, expected in _MENU_TEXT.items():
        item = _find(menu, name)
        assert item is not None, f"a menütétel hiányzik: {name}"
        assert item.property("text") == expected, (
            f"{name}: {item.property('text')!r} != {expected!r}"
        )
    assert _find(menu, "peopleAlbumMenuInvertSelection").property("enabled") is True


@pytest.mark.parametrize("height_offset", _HEIGHT_OFFSETS)
def test_megforditas_es_indexkep_frissites_kattintassal_mukodik(
    qml_app, qt_app, tmp_path, height_offset
):
    window, controller, _engine = qml_app
    pane, library, ini_path, initial_row_count = _prepare_person(
        window, controller, qt_app, height_offset
    )
    window.setProperty("selectedIndexes", [0])
    window.setProperty("selectedIndex", 0)
    qt_app.processEvents()
    assert _selected_rows(window) == [0]

    capture = (
        height_offset == 0
        and os.environ.get("PICASAPY_CAPTURE_MENU_4645") == "1"
    )
    _click_person_menu_item(
        window, pane, qt_app, "peopleAlbumMenuInvertSelection", capture=capture
    )
    assert _selected_rows(window) == [1], (
        "a menütétel nem a személyalbum rácsának látható két sorát fordította meg"
    )

    # Új, arc-címkézett fájl: csak a menü „Indexképek frissítése” útja
    # szinkronizálhatja a könyvtárat, majd töltheti újra a személyalbumot.
    source = Path(controller.photos.filePathAt(0))
    added = library / "c.jpg"
    shutil.copyfile(source, added)
    with ini_path.open("a", encoding="utf-8") as ini:
        ini.write(
            f"\n[{added.name}]\nfaces=rect64({_FACE_RECT}),{_PERSON_ID}\n"
        )

    _click_person_menu_item(
        window, pane, qt_app, "peopleAlbumMenuRefreshThumbnails"
    )
    assert _wait(
        qt_app,
        lambda: controller.photos.rowCount() == initial_row_count + 1,
    ), "az indexképek frissítése nem töltötte újra a rácsot"
