"""QML-funkcionális tesztek: FolderContextMenu/NewCollectionDialog/
FolderDateDialog önálló komponensek (#320) — a `test_qml_context_menu.py`
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
        assert menu.findChild(QObject, "folderContextMenuSetDate") is not None

    def test_new_collection_trigger_emits_signal(self, qml_engine, qt_app):
        menu = self._make_menu(qml_engine)
        events = []
        menu.newCollectionRequested.connect(lambda: events.append(True))
        item = menu.findChild(QObject, "folderContextMenuNewCollection")
        QMetaObject.invokeMethod(item, "triggered", Qt.ConnectionType.DirectConnection)
        qt_app.processEvents()
        assert events == [True]

    def test_set_date_trigger_emits_signal(self, qml_engine, qt_app):
        menu = self._make_menu(qml_engine)
        events = []
        menu.setDateRequested.connect(lambda: events.append(True))
        item = menu.findChild(QObject, "folderContextMenuSetDate")
        QMetaObject.invokeMethod(item, "triggered", Qt.ConnectionType.DirectConnection)
        qt_app.processEvents()
        assert events == [True]

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


class TestFolderDateDialog:
    def _make_dialog(self, qml_engine):
        return _load(
            qml_engine,
            'import QtQuick\nimport PicasaPy 1.0\n'
            'FolderDateDialog { objectName: "dlg" }\n',
        )

    def test_accepted_emits_date_with_folder_path(self, qml_engine, qt_app):
        dialog = self._make_dialog(qml_engine)
        dialog.setProperty("folderPath", "/mnt/fotok/balaton")
        events = []
        dialog.dateAccepted.connect(lambda path, date: events.append((path, date)))
        field = dialog.findChild(QObject, "folderDateField")
        field.setProperty("text", "2019-07-04")
        _invoke(dialog, "accept")
        qt_app.processEvents()
        assert events == [("/mnt/fotok/balaton", "2019-07-04")]

    def test_clear_button_emits_date_cleared(self, qml_engine, qt_app):
        dialog = _load_dialog_in_window(qml_engine, "FolderDateDialog")
        dialog.setProperty("folderPath", "/mnt/fotok/balaton")
        dialog.setProperty("currentDate", "2019-07-04")
        _open(dialog)
        qt_app.processEvents()
        events = []
        dialog.dateCleared.connect(lambda path: events.append(path))
        button = dialog.findChild(QObject, "folderDateClearButton")
        assert button is not None
        assert button.property("visible") is True
        QMetaObject.invokeMethod(button, "clicked", Qt.ConnectionType.DirectConnection)
        qt_app.processEvents()
        assert events == ["/mnt/fotok/balaton"]

    def test_accept_with_invalid_format_emits_nothing(self, qml_engine, qt_app):
        dialog = self._make_dialog(qml_engine)
        events = []
        dialog.dateAccepted.connect(lambda path, date: events.append((path, date)))
        field = dialog.findChild(QObject, "folderDateField")
        field.setProperty("text", "nem-datum")
        _invoke(dialog, "accept")
        qt_app.processEvents()
        assert events == []

    def test_clear_button_hidden_without_existing_override(self, qml_engine):
        dialog = self._make_dialog(qml_engine)
        dialog.setProperty("currentDate", "")
        button = dialog.findChild(QObject, "folderDateClearButton")
        assert button.property("visible") is False

    def test_hint_visible_for_invalid_format(self, qml_engine, qt_app):
        dialog = _load_dialog_in_window(qml_engine, "FolderDateDialog")
        _open(dialog)
        field = dialog.findChild(QObject, "folderDateField")
        field.setProperty("text", "nem-datum")
        qt_app.processEvents()
        hint = dialog.findChild(QObject, "folderDateHint")
        assert hint.property("visible") is True

    def test_hint_hidden_for_valid_format(self, qml_engine, qt_app):
        dialog = _load_dialog_in_window(qml_engine, "FolderDateDialog")
        _open(dialog)
        field = dialog.findChild(QObject, "folderDateField")
        field.setProperty("text", "2019-07-04")
        qt_app.processEvents()
        hint = dialog.findChild(QObject, "folderDateHint")
        assert hint.property("visible") is False
