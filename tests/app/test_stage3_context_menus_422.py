"""QML-funkcionális tesztek: a #422 3. lépcsőjének kontextusmenüi —
bal panel (`AlbumList`), címke (`Tags`) és képtálca (`Tray`).

Mindhárom menü a `Picasa3i18n.dll` string-táblájából derült ki (a
felhasználó képernyőképein nem szerepeltek), a tételsoruk forrása a
`docs/specs/ui-audit-context-menus.md` A.2 szakasza. Nálunk eddig
mindhárom teljesen hiányzott.

A komponenseket önmagukban töltjük be, controllerhez kötés nélkül (a
`test_folder_context_menu_320.py` mintája) — a bekötést a FolderPane /
TagsPanel / TrayBar végzi.
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


class TestFolderListContextMenu:
    """A bal panel saját menüje — az `AlbumList` osztály 11 tétele."""

    EXPECTED = [
        "folderListMenuSortByDate",
        "folderListMenuSortByName",
        "folderListMenuSortBySize",
        "folderListMenuSortByChanged",
        "folderListMenuSortReverse",
        "folderListMenuSortPeopleByName",
        "folderListMenuSortPeopleByCount",
        "folderListMenuSortPeopleByTopList",
        "folderListMenuFlatView",
        "folderListMenuShowThumbnails",
        "folderListMenuDesktop",
    ]

    def test_all_eleven_commands_are_present_in_order(self, qml_engine):
        menu = _load(qml_engine, "FolderListContextMenu")
        found = [
            child.objectName()
            for child in menu.findChildren(QObject)
            if child.objectName() in self.EXPECTED
        ]
        assert found == self.EXPECTED

    def test_unbacked_commands_are_shown_but_disabled(self, qml_engine):
        menu = _load(qml_engine, "FolderListContextMenu")
        for name in self.EXPECTED[5:]:  # a személy-rendezéstől lefelé
            item = menu.findChild(QObject, name)
            assert item.property("enabled") is False, f"{name} nem szürke"

    def test_sort_checkmarks_follow_the_current_state(self, qml_engine, qt_app):
        menu = _load(qml_engine, "FolderListContextMenu")
        menu.setProperty("sortMode", "changed")
        menu.setProperty("sortReverse", True)
        qt_app.processEvents()
        assert menu.findChild(
            QObject, "folderListMenuSortByChanged").property("checked")
        assert not menu.findChild(
            QObject, "folderListMenuSortByDate").property("checked")
        assert menu.findChild(
            QObject, "folderListMenuSortReverse").property("checked")

    def test_sort_mode_trigger_carries_the_mode(self, qml_engine, qt_app):
        menu = _load(qml_engine, "FolderListContextMenu")
        events = []
        menu.sortModeRequested.connect(events.append)
        _trigger(menu, "folderListMenuSortBySize")
        qt_app.processEvents()
        assert events == ["size"]

    def test_reverse_trigger_emits_signal(self, qml_engine, qt_app):
        menu = _load(qml_engine, "FolderListContextMenu")
        events = []
        menu.sortReverseRequested.connect(lambda: events.append(True))
        _trigger(menu, "folderListMenuSortReverse")
        qt_app.processEvents()
        assert events == [True]


class TestTagContextMenu:
    """A címke menüje — a `Tags` osztály 3 tétele, mind bekötve."""

    EXPECTED = ["tagMenuAddToSelection", "tagMenuFindTagged", "tagMenuRemove"]

    def test_all_three_commands_are_present_in_order(self, qml_engine):
        menu = _load(qml_engine, "TagContextMenu")
        found = [
            child.objectName()
            for child in menu.findChildren(QObject)
            if child.objectName() in self.EXPECTED
        ]
        assert found == self.EXPECTED

    def test_no_command_is_a_placeholder(self, qml_engine):
        """Mindhárom mögött van réteg — egyik sem lehet szürke."""
        menu = _load(qml_engine, "TagContextMenu")
        for name in self.EXPECTED:
            assert menu.findChild(QObject, name).property("enabled") is True

    @pytest.mark.parametrize(
        "item_name,signal_name",
        [
            ("tagMenuAddToSelection", "addToSelectionRequested"),
            ("tagMenuFindTagged", "findTaggedRequested"),
            ("tagMenuRemove", "removeRequested"),
        ],
    )
    def test_trigger_emits_matching_signal(
        self, qml_engine, qt_app, item_name, signal_name
    ):
        menu = _load(qml_engine, "TagContextMenu")
        events = []
        getattr(menu, signal_name).connect(lambda: events.append(True))
        _trigger(menu, item_name)
        qt_app.processEvents()
        assert events == [True]


class TestTrayContextMenu:
    """A képtálca menüje — a `Tray` osztály 2 tétele."""

    def test_both_commands_are_present(self, qml_engine):
        menu = _load(qml_engine, "TrayContextMenu")
        for name in ("trayMenuKeepSelection", "trayMenuRemoveSelection"):
            assert menu.findChild(QObject, name) is not None

    @pytest.mark.parametrize(
        "item_name,signal_name",
        [
            ("trayMenuKeepSelection", "keepSelectionRequested"),
            ("trayMenuRemoveSelection", "removeSelectionRequested"),
        ],
    )
    def test_trigger_emits_matching_signal(
        self, qml_engine, qt_app, item_name, signal_name
    ):
        menu = _load(qml_engine, "TrayContextMenu")
        events = []
        getattr(menu, signal_name).connect(lambda: events.append(True))
        _trigger(menu, item_name)
        qt_app.processEvents()
        assert events == [True]
