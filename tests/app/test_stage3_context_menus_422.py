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

import json

import pytest
from PySide6.QtCore import QMetaObject, QObject, Qt, QUrl
from PySide6.QtQml import QQmlComponent, QQmlEngine, QQmlExpression, qmlContext

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
    """A bal panel saját menüje - rendezés, emberek, Shortcuts és nézetkapcsolók.

    #757: a spec kétszer is „11 tétel"-t írt, a `Picasa3i18n.dll`
    string-táblájában viszont TIZENKÉT `AlbumList::` sor van — a
    `Shortcuts` kimaradt a számolásból."""

    EXPECTED = [
        "folderListMenuSortByDate",
        "folderListMenuSortByChanged",
        "folderListMenuSortBySize",
        "folderListMenuSortByName",
        "folderListMenuSortReverse",
        "folderListMenuSortPeopleByName",
        "folderListMenuSortPeopleByCount",
        "folderListMenuSortPeopleByTopList",
        "folderListMenuShortcuts",
        "folderListMenuDesktop",
        "folderListMenuMyDocuments",
        "folderListMenuMyPictures",
        "folderListMenuMyComputer",
        "folderListMenuShowThumbnails",
        "folderListMenuSimplifiedTree",
    ]

    def test_all_commands_are_present_in_order(self, qml_engine):
        menu = _load(qml_engine, "FolderListContextMenu")
        found = [
            child.objectName()
            for child in menu.findChildren(QObject)
            if child.objectName() in self.EXPECTED
        ]
        assert found == self.EXPECTED

    #: Amik mögé MÁR megjött a réteg — ezek nem helykitöltők.
    #:
    #: ⚠️ Ez a lista csak NŐHET: minden új tétel egy megszüntetett néma
    #: vezérlő. Ha valamelyik visszakerülne a szürkék közé, az regresszió.
    ELO_KIVETELEK = {
        # #1454: a bal hasáb fa-vezérlőjének kapcsolója
        "folderListMenuSimplifiedTree",
        # #1767: a Személyek lista három rendezési módja — név,
        # darabszám, Top 10; a választást a `view/peopleSort` őrzi
        "folderListMenuSortPeopleByName",
        "folderListMenuSortPeopleByCount",
        "folderListMenuSortPeopleByTopList",
        # #4462: a nézetkapcsoló és az Asztal gyorsugrás meglévő
        # FolderHierarchyController-műveletre van bekötve.
        "folderListMenuShowThumbnails",
        "folderListMenuShortcuts",
        "folderListMenuDesktop",
        "folderListMenuMyDocuments",
        "folderListMenuMyPictures",
        "folderListMenuMyComputer",
    }

    def test_unbacked_commands_are_shown_but_disabled(self, qml_engine):
        menu = _load(qml_engine, "FolderListContextMenu")
        for name in self.EXPECTED[5:]:  # a személy-rendezéstől lefelé
            if name in self.ELO_KIVETELEK:
                continue
            item = menu.findChild(QObject, name)
            assert item.property("enabled") is False, f"{name} nem szürke"

    def test_the_simplified_tree_item_is_live(self, qml_engine, qt_app):
        """#1454: a tétel `placeholder: true` volt — most jelzést ad."""
        menu = _load(qml_engine, "FolderListContextMenu")
        events = []
        menu.simplifiedTreeRequested.connect(lambda: events.append(True))
        item = _trigger(menu, "folderListMenuSimplifiedTree")
        qt_app.processEvents()
        assert item.property("enabled") is True
        assert events == [True]

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


def _menu_sorok(menu) -> list[dict]:
    """A menü sorai építési sorrendben: objectName, osztály, felirat.

    Az `itemAt(i)` a menü TÉNYLEGES sorait adja, az elválasztót is: a
    `findChildren` az elválasztót nem különböztetné meg a tételektől."""
    kifejezes = QQmlExpression(
        qmlContext(menu),
        menu,
        "JSON.stringify((function () {"
        "  var sorok = [];"
        "  for (var i = 0; i < count; ++i) {"
        "    var sor = itemAt(i);"
        "    sorok.push({"
        "      nev: sor ? sor.objectName : null,"
        "      szeparator: sor ? sor.toString().indexOf('MenuSeparator') >= 0 : false,"
        "      felirat: sor && sor.text !== undefined ? sor.text : null"
        "    });"
        "  }"
        "  return sorok;"
        "})())",
    )
    eredmeny, hiba = kifejezes.evaluate()
    assert not hiba, kifejezes.error()
    return json.loads(eredmeny if isinstance(eredmeny, str) else eredmeny.toString())


class TestTagContextMenu:
    """A címke menüje — a `Tags` osztály 3 tétele, mind bekötve."""

    # #7025: az eredeti sorrend: kijelölésre adás, keresés, eltávolítás.
    EXPECTED = ["tagMenuAddToSelection", "tagMenuFindTagged", "tagMenuRemove"]

    def test_the_menu_order_has_a_separator_between_search_and_remove(
        self, qml_engine
    ):
        """#7136: az eredeti `0x00735480` négy rekordot ad át a
        `0x00a6aee0`-nak: Add, Search, csupa nulla rekord (elválasztó),
        Remove. Nálunk a sorok: Add, Search, MenuSeparator, Remove."""
        menu = _load(qml_engine, "TagContextMenu")
        sorok = _menu_sorok(menu)
        assert [sor["nev"] for sor in sorok] == [
            "tagMenuAddToSelection",
            "tagMenuFindTagged",
            "tagMenuSeparator",
            "tagMenuRemove",
        ]
        assert [sor["szeparator"] for sor in sorok] == [False, False, True, False]

    def test_the_menu_has_exactly_one_separator_and_four_rows(self, qml_engine):
        """Nem szabad: több elválasztó vagy további sor (az eredeti rekordtáblája
        négy sor). A szélső sor sem lehet elválasztó."""
        menu = _load(qml_engine, "TagContextMenu")
        sorok = _menu_sorok(menu)
        assert len(sorok) == 4
        assert sum(1 for sor in sorok if sor["szeparator"]) == 1
        assert not sorok[0]["szeparator"] and not sorok[-1]["szeparator"]

    def test_the_labels_are_unchanged(self, qml_engine):
        """Nem szabad: a három tétel hivatalos felirata nem változik."""
        menu = _load(qml_engine, "TagContextMenu")
        feliratok = {
            sor["nev"]: sor["felirat"] for sor in _menu_sorok(menu) if not sor["szeparator"]
        }
        assert feliratok == {
            "tagMenuAddToSelection": "Add this tag to entire selection",
            "tagMenuFindTagged": "Search for items with this tag",
            "tagMenuRemove": "Remove this tag",
        }

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
