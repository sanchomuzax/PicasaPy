"""#459/5 — a nem elérhető mappa JELÖLÉSE a bal hasábon és a tájékoztató
üzenet a mappára lépéskor.

A sor-delegate a `ListView` terméke — a `findChild` NEM látja (MEMORY
2026-07-31), ezért a vizuális fát járjuk be, ahogy a #384-es teszt teszi.
"""

from __future__ import annotations

import pytest
from PySide6.QtCore import QMetaObject, QObject, QUrl
from PySide6.QtQml import QQmlComponent, QQmlEngine

from picasapy.index import open_index, sync_tree

from support.jpeg_factory import make_jpeg

_KEEPALIVE = []


@pytest.fixture
def library(tmp_path):
    root = tmp_path / "kepek"
    (root / "helyi").mkdir(parents=True)
    (root / "nas").mkdir()
    make_jpeg(root / "helyi" / "a.jpg")
    make_jpeg(root / "nas" / "b.jpg")
    return root


@pytest.fixture
def conn(tmp_path, library):
    with open_index(tmp_path / "index.db") as connection:
        sync_tree(connection, library)
        connection.execute("UPDATE folders SET offline = 1 WHERE path LIKE '%nas'")
        connection.commit()
        yield connection


@pytest.fixture
def pane(qt_app, conn):
    import picasapy.app.application as app_module
    from picasapy.app.models import FolderListModel

    engine = QQmlEngine()
    engine.addImportPath(str(app_module._APP_DIR / "qml"))
    engine.rootContext().setContextProperty("controller", None)
    component = QQmlComponent(
        engine,
        QUrl.fromLocalFile(
            str(app_module._APP_DIR / "qml" / "PicasaPy" / "FolderPane.qml")
        ),
    )
    folders_model = FolderListModel()
    folders_model.load(conn)
    obj = component.createWithInitialProperties({"foldersModel": folders_model})
    errors = [e.toString() for e in component.errors()]
    assert errors == [], errors
    assert obj is not None
    folders_model.setParent(obj)
    obj.setProperty("width", 300)
    obj.setProperty("height", 1600)
    QQmlEngine.setObjectOwnership(obj, QQmlEngine.ObjectOwnership.CppOwnership)
    _KEEPALIVE.extend([engine, component, obj, folders_model])
    return obj


def _walk(item):
    for child in item.childItems():
        yield child
        yield from _walk(child)


def _folder_rows(pane_obj):
    folder_list = pane_obj.findChild(QObject, "folderListView")
    # a ListView a delegate-eket inkubálva hozza létre — enélkül headless
    # futásban csak az ELSŐ sor létezik a bejáráskor
    QMetaObject.invokeMethod(folder_list, "forceLayout")
    content = folder_list.property("contentItem")
    return {
        item.property("path"): item
        for item in _walk(content)
        if item.property("kind") == "folder"
    }


def _label_of(row):
    labels = [
        item
        for item in _walk(row)
        if item.objectName() == "folderRowLabel"
    ]
    assert labels, "nincs mappa-címke a soron"
    return labels[0]


class TestOfflineFolderRow:
    def test_offline_row_is_italic_and_dimmed(self, pane, qt_app):
        rows = _folder_rows(pane)
        for _ in range(3):
            qt_app.processEvents()
        rows = _folder_rows(pane)
        offline = [path for path in rows if path.endswith("nas")]
        assert offline, f"nincs nas sor: {list(rows)}"
        label = _label_of(rows[offline[0]])
        assert label.property("font").italic() is True
        assert label.property("opacity") < 1.0

    def test_available_row_is_normal(self, pane, qt_app):
        rows = _folder_rows(pane)
        for _ in range(3):
            qt_app.processEvents()
        rows = _folder_rows(pane)
        online = [path for path in rows if path.endswith("helyi")]
        assert online, f"nincs helyi sor: {list(rows)}"
        label = _label_of(rows[online[0]])
        assert label.property("font").italic() is False
        assert label.property("opacity") == 1.0
