"""A mappa Move to Collection almenüje és az azonnali besorolás (#6883)."""

from __future__ import annotations

import json
import time
from pathlib import Path

import pytest
import shiboken6
from PySide6.QtCore import Q_ARG, QMetaObject, QPoint, QPointF, QObject, Qt
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlExpression, qmlContext
from PySide6.QtQuick import QQuickItem
from PySide6.QtTest import QTest

from picasapy.ini import load_or_empty, parse_document, read_folder_category, save_document
from support.jpeg_factory import make_jpeg


_BEAVATKOZO_SORREND = (
    ("Exported Pictures", "ExportedPictures"),
    ("Folders", "Folders"),
    ("Hidden Folders", "HiddenFolders"),
    ("Other Stuff", "OtherStuff"),
    ("Projects", "Projects"),
    ("Web Albums", "WebAlbums"),
)


def _child(root, name):
    item = root.findChild(QObject, name)
    assert item is not None, f"{name} nem található"
    return item


def _wait_for(condition, qt_app, name, timeout=3):
    deadline = time.monotonic() + timeout
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


def _click(window, item, button=Qt.MouseButton.LeftButton, *, target_window=None):
    assert item.isEnabled(), f"{item.objectName()} tiltott"
    assert item.width() > 0 and item.height() > 0
    scene_point = item.mapToScene(
        QPointF(item.width() / 2, item.height() / 2)
    )
    target_window = target_window or item.window()
    assert target_window is not None
    print("CLICKDBG", item.objectName(), scene_point, item.window().title(), [(w.title(), w.geometry(), w.isVisible()) for w in QGuiApplication.allWindows()])
    QTest.mouseMove(target_window, QPoint(round(scene_point.x()), round(scene_point.y())))
    QTest.mouseClick(
        target_window,
        button,
        Qt.KeyboardModifier.NoModifier,
        QPoint(round(scene_point.x()), round(scene_point.y())),
    )


def _submenu_row(menu, submenu):
    expression = QQmlExpression(
        qmlContext(menu),
        menu,
        "(function () {"
        "  for (var i = 0; i < count; ++i) {"
        "    var item = itemAt(i);"
        f"    if (item && item.subMenu && item.subMenu.objectName === \"{submenu.objectName()}\")"
        "      return item;"
        "  }"
        "  return null;"
        "})()",
    )
    result, error = expression.evaluate()
    assert not error, expression.error()
    assert result is not None, "a Move to Collection almenüsor nem található"
    return shiboken6.wrapInstance(shiboken6.getCppPointer(result)[0], QQuickItem)


def _menu_item_names(menu):
    expression = QQmlExpression(
        qmlContext(menu),
        menu,
        "JSON.stringify((function () {"
        "  var names = [];"
        "  for (var i = 0; i < count; ++i) {"
        "    var item = itemAt(i);"
        "    names.push(item ? item.objectName : null);"
        "  }"
        "  return names;"
        "})())",
    )
    result, error = expression.evaluate()
    assert not error, expression.error()
    return json.loads(result if isinstance(result, str) else result.toString())


def _menu_item(menu, object_name):
    expression = QQmlExpression(
        qmlContext(menu),
        menu,
        "(function () {"
        "  for (var i = 0; i < count; ++i) {"
        "    var item = itemAt(i);"
        f"    if (item && item.objectName === \"{object_name}\") return item;"
        "  }"
        "  return null;"
        "})()",
    )
    result, error = expression.evaluate()
    assert not error, expression.error()
    assert result is not None, f"{object_name} menütétel nem található"
    return shiboken6.wrapInstance(shiboken6.getCppPointer(result)[0], QQuickItem)


def _open_move_to_collection(window, qt_app, folder_path):
    window.show()
    window.requestActivate()
    qt_app.processEvents()
    QMetaObject.invokeMethod(
        window,
        "openFolderContextMenu",
        Qt.ConnectionType.DirectConnection,
        Q_ARG("QVariant", str(folder_path)),
    )
    menu = _child(window, "folderContextMenu")
    _wait_for(lambda: menu.property("visible"), qt_app, "mappa helyi menü")
    submenu = _child(window, "folderContextMenuMoveToCollection")
    _click(window, _submenu_row(menu, submenu), target_window=window)
    _wait_for(lambda: submenu.property("visible"), qt_app, "gyűjtemény-almenü")
    return menu, submenu


def _make_folder(root: Path, *, category: str | None) -> Path:
    folder = root / "celmappa"
    folder.mkdir()
    make_jpeg(folder / "kep.jpg", size=(32, 24))
    if category is not None:
        document = parse_document("").with_value(
            "Picasa", "P2category", category
        )
        save_document(document, folder / ".picasa.ini")
    return folder


def _add_folder(controller, tmp_path, qt_app, *, category):
    folder = _make_folder(tmp_path / "kepek", category=category)
    from picasapy.index import open_index, sync_tree

    with open_index(tmp_path / "index.db") as conn:
        sync_tree(conn, tmp_path / "kepek")
    controller._reload_after_sync()
    qt_app.processEvents()
    return folder


@pytest.mark.parametrize("height_delta", (-5, 0, 5))
def test_other_stuffba_es_vissza_a_mappakba_kattintassal(
    qml_app, qt_app, tmp_path, height_delta
):
    window, controller, _engine = qml_app
    folder = _add_folder(
        controller, tmp_path, qt_app, category="Other Stuff"
    )
    pane = _child(window, "folderPane")
    folders_model = pane.property("foldersModel")
    other_header = _child(window, "otherHeader")
    assert folders_model.rowOfPath(str(folder)) == -1
    assert other_header.property("text").endswith("(1)")

    window.setHeight(window.height() + height_delta)
    qt_app.processEvents()
    visible_windows_before = sum(
        1 for item in QGuiApplication.allWindows() if item.isVisible()
    )
    _menu, _submenu = _open_move_to_collection(window, qt_app, folder)
    _click(
        window,
        _menu_item(_submenu, "folderContextMenuMoveToCollectionBuiltin_Folders"),
    )
    _wait_for(
        lambda: read_folder_category(load_or_empty(folder / ".picasa.ini")) is None,
        qt_app,
        "Folders kategóriaírás",
    )

    ini = load_or_empty(folder / ".picasa.ini")
    assert read_folder_category(ini) is None
    assert folders_model.rowOfPath(str(folder)) >= 0
    assert other_header.property("text").endswith("(0)")
    visible_windows_after = sum(
        1 for item in QGuiApplication.allWindows() if item.isVisible()
    )
    assert visible_windows_after == visible_windows_before


@pytest.mark.parametrize("height_delta", (-5, 0, 5))
def test_foldersbol_other_stuffba_kattintassal(
    qml_app, qt_app, tmp_path, height_delta
):
    window, controller, _engine = qml_app
    folder = _add_folder(controller, tmp_path, qt_app, category=None)
    pane = _child(window, "folderPane")
    folders_model = pane.property("foldersModel")
    other_header = _child(window, "otherHeader")
    assert folders_model.rowOfPath(str(folder)) >= 0
    assert other_header.property("text").endswith("(0)")

    window.setHeight(window.height() + height_delta)
    qt_app.processEvents()
    visible_windows_before = sum(
        1 for item in QGuiApplication.allWindows() if item.isVisible()
    )
    _menu, _submenu = _open_move_to_collection(window, qt_app, folder)
    target = _menu_item(
        _submenu,
        "folderContextMenuMoveToCollectionBuiltin_OtherStuff",
    )
    _click(window, target)
    _wait_for(
        lambda: read_folder_category(load_or_empty(folder / ".picasa.ini"))
        == "Other Stuff",
        qt_app,
        "Other Stuff kategóriaírás",
    )

    ini = load_or_empty(folder / ".picasa.ini")
    assert read_folder_category(ini) == "Other Stuff"
    assert folders_model.rowOfPath(str(folder)) == -1
    assert other_header.property("text").endswith("(1)")
    other_row = _child(window, f"otherStuffFolder_{folder}")
    assert other_row.property("visible") is True
    visible_windows_after = sum(
        1 for item in QGuiApplication.allWindows() if item.isVisible()
    )
    assert visible_windows_after == visible_windows_before


def test_beepitett_menuk_sorrendje_es_aktualis_gyujtemeny(
    qml_app, qt_app, tmp_path
):
    window, controller, _engine = qml_app
    folder = _add_folder(controller, tmp_path, qt_app, category=None)
    controller.createCollection("Saját")
    qt_app.processEvents()
    menu, _submenu = _open_move_to_collection(
        window, qt_app, folder
    )

    builtin_items = [
        _menu_item(
            _submenu,
            f"folderContextMenuMoveToCollectionBuiltin_{slug}",
        )
        for _label, slug in _BEAVATKOZO_SORREND
    ]
    assert [item.property("text") for item in builtin_items] == [
        label for label, _slug in _BEAVATKOZO_SORREND
    ]
    assert _menu_item_names(_submenu) == [
        *(
            f"folderContextMenuMoveToCollectionBuiltin_{slug}"
            for _label, slug in _BEAVATKOZO_SORREND
        ),
        "folderContextMenuMoveToCollectionItem_Saját",
        "folderContextMenuMoveToCollectionSeparator",
        "folderContextMenuNewCollection",
    ]

    folders_item = builtin_items[1]
    assert folders_item.property("checkable") is True
    assert folders_item.property("checked") is True
    assert folders_item.property("enabled") is False
    assert menu.property("visible") is True
