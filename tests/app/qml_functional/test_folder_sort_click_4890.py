"""#4890: a mappa almenüjének valódi kattintása csak a célmappát rendezi."""

from __future__ import annotations

import time

import pytest
from PySide6.QtCore import Q_ARG, QMetaObject, QPoint, QPointF, QObject, Qt
from PySide6.QtTest import QTest

from picasapy.index import open_index, sync_tree
from support.jpeg_factory import make_jpeg


def _child(root, name):
    obj = root.findChild(QObject, name)
    assert obj is not None, f"{name} nem található"
    return obj


def _wait_for(condition, qt_app, name):
    deadline = time.monotonic() + 3
    while time.monotonic() < deadline:
        qt_app.processEvents()
        if condition():
            return
        time.sleep(0.05)
    raise AssertionError(f"határidőn belül nem teljesült: {name}")


def _visual_item(root, name):
    pending = [root.contentItem()]
    while pending:
        item = pending.pop()
        if item.objectName() == name:
            return item
        pending.extend(item.childItems())
    raise AssertionError(f"{name} nem található a vizuális fában")


def _click(window, item, button=Qt.LeftButton):
    scene_point = item.mapToScene(QPointF(item.width() / 2, item.height() / 2))
    QTest.mouseClick(
        window, button, Qt.NoModifier, QPoint(round(scene_point.x()), round(scene_point.y()))
    )


def _submenu_row(menu, submenu):
    title = submenu.property("title")
    pending = [menu.property("contentItem")]
    while pending:
        item = pending.pop()
        if (
            "MenuItem" in item.metaObject().className()
            and item.property("text") == title
            and not item.objectName()
        ):
            return item
        pending.extend(item.childItems())
    raise AssertionError(f"{title!r} almenüsora nem található")


@pytest.mark.parametrize("height_delta", (-5, 0, 5))
def test_kattintasra_termeszetesen_rendez_csak_egy_mappat(
    qml_app, qt_app, tmp_path, height_delta
):
    window, controller, _engine = qml_app
    root = tmp_path / "kepek"
    target = root / "cel"
    other = root / "masik"
    target.mkdir()
    other.mkdir()
    make_jpeg(target / "kep10.jpg", size=(8, 6))
    make_jpeg(target / "kep2.jpg", size=(8, 6))
    make_jpeg(other / "masik10.jpg", size=(8, 6))
    make_jpeg(other / "masik2.jpg", size=(8, 6))
    with open_index(tmp_path / "index.db") as conn:
        sync_tree(conn, root)
    controller._reload_after_sync()
    controller.selectFolder(str(target))
    qt_app.processEvents()

    original_height = window.height()
    window.setHeight(original_height + height_delta)
    qt_app.processEvents()

    QMetaObject.invokeMethod(
        window,
        "openFolderContextMenu",
        Qt.ConnectionType.DirectConnection,
        Q_ARG("QVariant", str(target)),
    )
    menu = _child(window, "folderContextMenu")
    _wait_for(lambda: menu.property("visible"), qt_app, "mappa helyi menü")
    submenu = _child(window, "folderMenuSortBy")
    _click(window, _submenu_row(menu, submenu))
    _wait_for(lambda: submenu.property("visible"), qt_app, "rendezési almenü")
    _click(window, _visual_item(window, "folderMenuSortByName"))
    _wait_for(lambda: not menu.property("visible"), qt_app, "menü bezárása")

    assert [photo.name for photo in controller.photos.photos if photo.folder_path == str(target)] == [
        "kep2.jpg",
        "kep10.jpg",
    ]
    controller.selectFolder(str(other))
    assert [photo.name for photo in controller.photos.photos if photo.folder_path == str(other)] == [
        "masik10.jpg",
        "masik2.jpg",
    ]
