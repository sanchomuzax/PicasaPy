"""QML-funkcionális tesztek: FolderContextMenu/NewCollectionDialog/
FolderPropertiesDialog önálló komponensek (#320, #422) — a `test_qml_context_menu.py`
mintája szerint, a controllerhez kötés nélkül (azt a FolderPane.qml, nem
forró fájl végzi)."""

from __future__ import annotations

import pytest
from PySide6.QtCore import QMetaObject, QObject, Qt, QUrl
from PySide6.QtQml import QQmlComponent, QQmlEngine

# élő Python-referencia nélkül a JS-motor GC-je bármikor eltávolítaná a
# QML-ből létrehozott gyökér-objektumokat (test_qml_context_menu.py mintája)
_KEEPALIVE = []


@pytest.fixture
def qml_engine(qt_app):
    import picasapy.app.application as app_module

    engine = QQmlEngine()
    engine.addImportPath(str(app_module._APP_DIR / "qml"))
    yield engine
    engine.deleteLater()


def _load(engine, qml_source):
    component = QQmlComponent(engine)
    component.setData(qml_source.encode("utf-8"), QUrl())
    obj = component.create()
    errors = [e.toString() for e in component.errors()]
    assert errors == [], errors
    assert obj is not None, "a komponens betöltése sikertelen"
    QQmlEngine.setObjectOwnership(obj, QQmlEngine.ObjectOwnership.CppOwnership)
    _KEEPALIVE.append(component)
    _KEEPALIVE.append(obj)
    return obj


def _invoke(obj, method, *args):
    QMetaObject.invokeMethod(obj, method, Qt.ConnectionType.DirectConnection, *args)


def _load_dialog_in_window(engine, type_name):
    """Dialógus VALÓDI Window-ban (de még nem nyitva) — a Popup tartalom-
    kötései (onOpened, visible-bindingek) csak akkor értékelődnek ki, ha a
    dialógus ténylegesen egy ablak alatt nyílik meg (headless
    QQmlComponent.create() önmagában nem elég, ld. #320 kísérlet)."""
    window = _load(
        engine,
        "import QtQuick\nimport QtQuick.Controls\nimport PicasaPy 1.0\n"
        "Window {\n visible: true\n width: 400; height: 300\n"
        f'    {type_name} {{ id: dlg; objectName: "dlg" }}\n'
        "}\n",
    )
    dialog = window.findChild(QObject, "dlg")
    assert dialog is not None
    return dialog


def _open(dialog):
    QMetaObject.invokeMethod(dialog, "open", Qt.ConnectionType.DirectConnection)


class TestFolderContextMenu:
    def _make_menu(self, qml_engine, collections=None):
        menu = _load(
            qml_engine,
            'import QtQuick\nimport PicasaPy 1.0\n'
            'FolderContextMenu { objectName: "menu" }\n',
        )
        menu.setProperty("customCollections", collections or [])
        return menu

    def test_static_items_present(self, qml_engine):
        menu = self._make_menu(qml_engine)
        assert menu.findChild(QObject, "folderContextMenuMoveToCollection") is not None
        assert menu.findChild(QObject, "folderContextMenuNewCollection") is not None

    def test_all_fifteen_original_commands_are_present_in_order(self, qml_engine):
        """#422: az eredeti `Folder` menüosztály 15 tétele, a
        `docs/specs/ui-audit-context-menus.md` 1. szakaszának sorrendjében.

        A „Mappa dátumának beállítása…" tudatosan NINCS köztük: az
        eredetiben sem ebben a menüben van, hanem az `album.fen`
        („Mappaleírás szerkesztése…") dialógusban — ld.
        FolderPropertiesDialog.qml."""
        expected = [
            "folderMenuEditDescription",
            "folderMenuSelectAll",
            "folderMenuClearSelection",
            "folderMenuInvertSelection",
            "folderContextMenuMoveToCollection",
            "folderMenuRefreshThumbnails",
            "folderMenuSortBy",
            "folderMenuHideFolder",
            "folderMenuLocate",
            "folderMenuRemoveFromPicasa",
            "folderMenuMoveFolder",
            "folderMenuDeleteFolder",
            "folderMenuUploadToGooglePhotos",
            "folderMenuExportAsHtml",
            "folderMenuAddNameTags",
        ]
        menu = self._make_menu(qml_engine)
        found = [
            child.objectName()
            for child in menu.findChildren(QObject)
            if child.objectName() in expected
        ]
        assert found == expected

    def test_folder_date_item_is_gone(self, qml_engine):
        """A dátum az `album.fen` dialógusba költözött — a menüben nem
        maradhat (paritás-hiba lenne)."""
        menu = self._make_menu(qml_engine)
        assert menu.findChild(QObject, "folderContextMenuSetDate") is None

    def test_unbacked_commands_are_shown_but_disabled(self, qml_engine):
        """Az inaktív tétel is tétel: LÁTSZIK, de szürke (spec 5.1.)."""
        menu = self._make_menu(qml_engine)
        for name in (
            "folderMenuHideFolder",
            "folderMenuMoveFolder",
            "folderMenuDeleteFolder",
            "folderMenuUploadToGooglePhotos",
            "folderMenuAddNameTags",
        ):
            item = menu.findChild(QObject, name)
            assert item is not None, f"{name} hiányzik"
            assert item.property("enabled") is False, f"{name} nem szürke"

    def test_sort_submenu_checks_the_current_mode(self, qml_engine, qt_app):
        """A „Mappa rendezésének alapja ▸" almenü az `Sort` menüosztály
        négy tétele (spec A.2), a jelenlegi rendezés pipálva."""
        menu = self._make_menu(qml_engine)
        menu.setProperty("sortMode", "name")
        menu.setProperty("sortReverse", True)
        qt_app.processEvents()
        assert menu.findChild(QObject, "folderMenuSortByName").property("checked")
        assert not menu.findChild(QObject, "folderMenuSortByDate").property("checked")
        assert menu.findChild(QObject, "folderMenuSortReverse").property("checked")

    def test_new_collection_trigger_emits_signal(self, qml_engine, qt_app):
        menu = self._make_menu(qml_engine)
        events = []
        menu.newCollectionRequested.connect(lambda: events.append(True))
        item = menu.findChild(QObject, "folderContextMenuNewCollection")
        QMetaObject.invokeMethod(item, "triggered", Qt.ConnectionType.DirectConnection)
        qt_app.processEvents()
        assert events == [True]

    def test_edit_description_trigger_emits_signal(self, qml_engine, qt_app):
        menu = self._make_menu(qml_engine)
        events = []
        menu.editDescriptionRequested.connect(lambda: events.append(True))
        item = menu.findChild(QObject, "folderMenuEditDescription")
        QMetaObject.invokeMethod(item, "triggered", Qt.ConnectionType.DirectConnection)
        qt_app.processEvents()
        assert events == [True]

    def test_sort_mode_trigger_carries_the_mode(self, qml_engine, qt_app):
        menu = self._make_menu(qml_engine)
        events = []
        menu.sortModeRequested.connect(events.append)
        item = menu.findChild(QObject, "folderMenuSortBySize")
        QMetaObject.invokeMethod(item, "triggered", Qt.ConnectionType.DirectConnection)
        qt_app.processEvents()
        assert events == ["size"]

    def test_move_to_collection_repeater_reflects_model(self, qml_engine):
        menu = self._make_menu(
            qml_engine, collections=[{"name": "Nyaralások"}, {"name": "Munka"}]
        )
        repeater = menu.findChild(QObject, "folderContextMenuMoveToCollectionRepeater")
        assert repeater is not None
        assert repeater.property("count") == 2

    # #320 / MEMORY (Repeater-delegátumok): a "Move to Collection" almenü
    # sorai csak a menü TÉNYLEGES megnyitásakor realizálódnak — headless
    # QQmlComponent.create()-tel nem jönnek létre (a `Repeater.itemAt()`
    # null-t ad), ezért az egyes sorok kattintását itt nem teszteljük
    # findChild-dal; a modell-kötés helyessége a fenti `count`-teszt dolga
    # (a `test_search.py`/collections-teszt mintája, ld. MEMORY 2026-07-31).

    def test_empty_collections_show_only_new_collection_entry(self, qml_engine):
        menu = self._make_menu(qml_engine, collections=[])
        repeater = menu.findChild(QObject, "folderContextMenuMoveToCollectionRepeater")
        assert repeater.property("count") == 0
        assert menu.findChild(QObject, "folderContextMenuNewCollection") is not None


class TestNewCollectionDialog:
    def _make_dialog(self, qml_engine):
        return _load(
            qml_engine,
            'import QtQuick\nimport PicasaPy 1.0\n'
            'NewCollectionDialog { objectName: "dlg" }\n',
        )

    def test_open_resets_and_focuses_the_name_field(self, qml_engine, qt_app):
        dialog = _load_dialog_in_window(qml_engine, "NewCollectionDialog")
        field = dialog.findChild(QObject, "newCollectionNameField")
        field.setProperty("text", "maradék szöveg")
        _open(dialog)
        qt_app.processEvents()
        assert field.property("text") == ""

    def test_accept_with_blank_name_emits_nothing(self, qml_engine, qt_app):
        dialog = self._make_dialog(qml_engine)
        events = []
        dialog.created.connect(lambda name: events.append(name))
        field = dialog.findChild(QObject, "newCollectionNameField")
        field.setProperty("text", "   ")
        _invoke(dialog, "accept")
        qt_app.processEvents()
        assert events == []

    def test_accepted_emits_created_with_trimmed_name(self, qml_engine, qt_app):
        dialog = self._make_dialog(qml_engine)
        events = []
        dialog.created.connect(lambda name: events.append(name))
        field = dialog.findChild(QObject, "newCollectionNameField")
        field.setProperty("text", "  Nyaralások  ")
        _invoke(dialog, "accept")
        qt_app.processEvents()
        assert events == ["Nyaralások"]


class TestFolderPropertiesDialog:
    """#422: „Mappaleírás szerkesztése…" — a Picasa `album.fen` dialógusa
    (docs/specs/picasa-fen-dialogs.md 3.2.). A mappa DÁTUMA az eredetiben
    itt lakik, nem a kontextusmenüben — ezért költözött ide a korábbi
    FolderDateDialog tartalma."""

    def _make_dialog(self, qml_engine):
        return _load(
            qml_engine,
            'import QtQuick\nimport PicasaPy 1.0\n'
            'FolderPropertiesDialog { objectName: "dlg" }\n',
        )

    def test_has_every_field_of_the_original_dialog(self, qml_engine):
        """Az album.fen mezősora: név · dátum + automatikus dátum · zene
        (jelölő + útvonal) · helyszín · leírás."""
        dialog = self._make_dialog(qml_engine)
        for name in (
            "folderPropertiesNameField",
            "folderPropertiesDateField",
            "folderPropertiesAutomaticDate",
            "folderPropertiesUseMusic",
            "folderPropertiesMusicPath",
            "folderPropertiesLocation",
            "folderPropertiesDescription",
        ):
            assert dialog.findChild(QObject, name) is not None, f"{name} hiányzik"

    def test_unbacked_fields_are_shown_but_disabled(self, qml_engine):
        """A név, a zene és a helyszín mögött még nincs réteg — a mezők a
        helyükön vannak, de inaktívak (az elrendezés a dizájn része)."""
        dialog = self._make_dialog(qml_engine)
        for name in (
            "folderPropertiesNameField",
            "folderPropertiesUseMusic",
            "folderPropertiesLocation",
        ):
            item = dialog.findChild(QObject, name)
            assert item.property("enabled") is False, f"{name} nem inaktív"

    def test_music_path_follows_the_music_checkbox(self, qml_engine, qt_app):
        """Az eredeti `<bind attr="enabled" source="usemusic">`."""
        dialog = self._make_dialog(qml_engine)
        check = dialog.findChild(QObject, "folderPropertiesUseMusic")
        path = dialog.findChild(QObject, "folderPropertiesMusicPath")
        assert path.property("enabled") is False
        check.setProperty("checked", True)
        qt_app.processEvents()
        assert path.property("enabled") is True

    def test_accept_emits_date_and_description(self, qml_engine, qt_app):
        dialog = _load_dialog_in_window(qml_engine, "FolderPropertiesDialog")
        dialog.setProperty("folderPath", "/mnt/fotok/balaton")
        _open(dialog)
        qt_app.processEvents()
        events = []
        dialog.folderPropertiesAccepted.connect(
            lambda path, date, desc: events.append((path, date, desc))
        )
        dialog.findChild(QObject, "folderPropertiesDateField").setProperty(
            "text", "2019-07-04")
        dialog.findChild(QObject, "folderPropertiesDescription").setProperty(
            "text", "Balatoni nyaralás")
        _invoke(dialog, "accept")
        qt_app.processEvents()
        assert events == [("/mnt/fotok/balaton", "2019-07-04", "Balatoni nyaralás")]

    def test_automatic_date_button_clears_the_date(self, qml_engine, qt_app):
        """Az eredeti „Automatic date" gombja: a mappa a legrégebbi képe
        dátumára áll vissza — a mentés üres dátumot ad tovább."""
        dialog = _load_dialog_in_window(qml_engine, "FolderPropertiesDialog")
        dialog.setProperty("folderPath", "/mnt/fotok/balaton")
        dialog.setProperty("currentDate", "2019-07-04")
        _open(dialog)
        qt_app.processEvents()
        events = []
        dialog.folderPropertiesAccepted.connect(
            lambda path, date, desc: events.append((path, date))
        )
        button = dialog.findChild(QObject, "folderPropertiesAutomaticDate")
        QMetaObject.invokeMethod(button, "clicked", Qt.ConnectionType.DirectConnection)
        qt_app.processEvents()
        _invoke(dialog, "accept")
        qt_app.processEvents()
        assert events == [("/mnt/fotok/balaton", "")]

    def test_accept_with_invalid_date_emits_nothing(self, qml_engine, qt_app):
        dialog = _load_dialog_in_window(qml_engine, "FolderPropertiesDialog")
        _open(dialog)
        qt_app.processEvents()
        events = []
        dialog.folderPropertiesAccepted.connect(
            lambda path, date, desc: events.append(date)
        )
        dialog.findChild(QObject, "folderPropertiesDateField").setProperty(
            "text", "nem-datum")
        _invoke(dialog, "accept")
        qt_app.processEvents()
        assert events == []

    def test_hint_visible_for_invalid_date_only(self, qml_engine, qt_app):
        dialog = _load_dialog_in_window(qml_engine, "FolderPropertiesDialog")
        _open(dialog)
        field = dialog.findChild(QObject, "folderPropertiesDateField")
        hint = dialog.findChild(QObject, "folderPropertiesDateHint")
        field.setProperty("text", "nem-datum")
        qt_app.processEvents()
        assert hint.property("visible") is True
        field.setProperty("text", "2019-07-04")
        qt_app.processEvents()
        assert hint.property("visible") is False

    def test_existing_values_prefill_the_fields(self, qml_engine, qt_app):
        dialog = _load_dialog_in_window(qml_engine, "FolderPropertiesDialog")
        dialog.setProperty("currentDate", "2019-07-04")
        dialog.setProperty("currentDescription", "Régi leírás")
        dialog.setProperty("folderName", "balaton")
        _open(dialog)
        qt_app.processEvents()
        assert dialog.findChild(
            QObject, "folderPropertiesDateField").property("text") == "2019-07-04"
        assert dialog.findChild(
            QObject, "folderPropertiesDescription").property("text") == "Régi leírás"
        assert dialog.findChild(
            QObject, "folderPropertiesNameField").property("text") == "balaton"
