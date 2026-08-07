"""QML-funkcionális teszt: a #422 utolsó hiányzó menüje — a gyűjtemény
jobbklikk-menüje (a Picasa `Collection` menüosztálya).

Forrás: `docs/specs/ui-audit-context-menus.md` 4. szakasza — három tétel:
átnevezés, eltávolítás, jelszó. A komponenst önmagában töltjük be,
controllerhez kötés nélkül (a `test_stage3_context_menus_422.py` mintája)
— a bekötést a FolderPane.qml végzi (ld. a
`qml_functional/test_folder_pane_custom_collections_476.py` bővítését).
"""

from __future__ import annotations

import pytest
from PySide6.QtCore import QMetaObject, QObject, Qt, QUrl
from PySide6.QtQml import QQmlComponent, QQmlEngine

_KEEPALIVE = []


@pytest.fixture
def qml_engine(qt_app):
    import picasapy.app.application as app_module

    engine = QQmlEngine()
    engine.addImportPath(str(app_module._APP_DIR / "qml"))
    yield engine
    engine.deleteLater()


def _load(engine, type_name):
    component = QQmlComponent(engine)
    component.setData(
        f'import QtQuick\nimport PicasaPy 1.0\n{type_name} {{ objectName: "m" }}\n'
        .encode("utf-8"),
        QUrl(),
    )
    obj = component.create()
    assert [e.toString() for e in component.errors()] == []
    assert obj is not None
    QQmlEngine.setObjectOwnership(obj, QQmlEngine.ObjectOwnership.CppOwnership)
    _KEEPALIVE.extend((component, obj))
    return obj


def _trigger(menu, name):
    item = menu.findChild(QObject, name)
    assert item is not None, f"{name} nem található"
    QMetaObject.invokeMethod(item, "triggered", Qt.ConnectionType.DirectConnection)
    return item


class TestCollectionContextMenu:
    """A gyűjtemény menüje — a `Collection` osztály 3 tétele."""

    EXPECTED = [
        "collectionMenuRename",
        "collectionMenuRemove",
        "collectionMenuPassword",
    ]

    def test_all_three_commands_are_present_in_order(self, qml_engine):
        menu = _load(qml_engine, "CollectionContextMenu")
        found = [
            child.objectName()
            for child in menu.findChildren(QObject)
            if child.objectName() in self.EXPECTED
        ]
        assert found == self.EXPECTED

    def test_password_item_is_a_placeholder(self, qml_engine):
        """A jelszavas gyűjtemény mögött nincs réteg — szürkén látszik."""
        menu = _load(qml_engine, "CollectionContextMenu")
        item = menu.findChild(QObject, "collectionMenuPassword")
        assert item.property("enabled") is False

    def test_rename_and_remove_are_not_placeholders(self, qml_engine):
        menu = _load(qml_engine, "CollectionContextMenu")
        for name in ("collectionMenuRename", "collectionMenuRemove"):
            assert menu.findChild(QObject, name).property("enabled") is True

    @pytest.mark.parametrize(
        "item_name,signal_name",
        [
            ("collectionMenuRename", "renameRequested"),
            ("collectionMenuRemove", "removeRequested"),
        ],
    )
    def test_trigger_emits_matching_signal(
        self, qml_engine, qt_app, item_name, signal_name
    ):
        menu = _load(qml_engine, "CollectionContextMenu")
        events = []
        getattr(menu, signal_name).connect(lambda: events.append(True))
        _trigger(menu, item_name)
        qt_app.processEvents()
        assert events == [True]
