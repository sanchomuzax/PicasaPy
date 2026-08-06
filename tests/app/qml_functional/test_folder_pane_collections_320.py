"""QML-funkcionális teszt: FolderPane.qml #320-as bekötése (mappasor
jobbklikk → gyűjtemény-áthelyezés / mappa-dátum) — a valódi AppController
NÉLKÜL, egy stub Python-controllerrel (a `custom_collections_controller`/
`folder_date_controller` mixinek majdani, az integrátor általi bekötését
utánozva), hogy a teszt a `controller.py` (forró fájl) módosítása nélkül
fusson (ld. issue #320 „integrátor-teendők").

A `pane.openFolderContextMenu(path)` pane-szintű függvényen át hívjuk a
jobbklikk-utat (a delegate-MouseArea Repeater/ListView-elem, findChild-dal
el nem érhető — MEMORY 2026-07-31)."""

from __future__ import annotations

import pytest
from PySide6.QtCore import (
    Property,
    QMetaObject,
    QObject,
    Qt,
    QUrl,
    Signal,
    Slot,
)
from PySide6.QtQml import QQmlComponent, QQmlEngine

_KEEPALIVE = []


class _StubController(QObject):
    """A FolderPane #320-as bekötésének felszíne — a `CustomCollectionsMixin`/
    `FolderDateMixin` slotjait tükrözi, de csak memóriában jegyzi a
    hívásokat (nincs valódi index/ini-írás)."""

    customCollectionsChanged = Signal()

    def __init__(self):
        super().__init__()
        self._collections: list[dict] = []
        self.created_names: list[str] = []
        self.moved: list[tuple[str, str]] = []
        self.date_overrides: dict[str, str] = {}
        self.set_date_calls: list[tuple[str, str]] = []
        self.clear_date_calls: list[str] = []

    @Property("QVariant", notify=customCollectionsChanged)
    def customCollections(self):
        return self._collections

    @Slot(str)
    def createCollection(self, name):
        self.created_names.append(name)
        self._collections = self._collections + [{"name": name, "folders": []}]
        self.customCollectionsChanged.emit()

    @Slot(str, str)
    def moveFolderToCollection(self, folder_path, collection_name):
        self.moved.append((folder_path, collection_name))

    @Slot(str, result=str)
    def folderDateOverride(self, folder_path):
        return self.date_overrides.get(folder_path, "")

    @Slot(str, str)
    def setFolderDate(self, folder_path, iso_date):
        self.set_date_calls.append((folder_path, iso_date))
        self.date_overrides[folder_path] = iso_date

    @Slot(str)
    def clearFolderDate(self, folder_path):
        self.clear_date_calls.append(folder_path)
        self.date_overrides.pop(folder_path, None)

    # a FolderPane induláskor a gyűjtemény-csukottságot is lekérdezi
    @Slot(str, result=bool)
    def isCollectionCollapsed(self, name):
        return False

    @Slot(str, bool)
    def setCollectionCollapsed(self, name, collapsed):
        pass


@pytest.fixture
def controller(qt_app):
    return _StubController()


@pytest.fixture
def pane(qt_app, controller):
    import picasapy.app.application as app_module
    from picasapy.app.models import FolderListModel

    engine = QQmlEngine()
    engine.addImportPath(str(app_module._APP_DIR / "qml"))
    engine.rootContext().setContextProperty("controller", controller)
    component = QQmlComponent(
        engine,
        QUrl.fromLocalFile(
            str(app_module._APP_DIR / "qml" / "PicasaPy" / "FolderPane.qml")
        ),
    )
    # üres, de VALÓS modell, MÁR a létrehozáskor átadva — a `Connections {
    # target: folderList.model }` (meglévő, #10-es kód) az induló
    # kötés-kiértékeléskor undefined targetre "Unable to assign"
    # szkripthibát dobna (#305-ös QML-figyelő), ha a modell csak utólag,
    # `setProperty`-vel érkezne.
    folders_model = FolderListModel()
    obj = component.createWithInitialProperties({"foldersModel": folders_model})
    errors = [e.toString() for e in component.errors()]
    assert errors == [], errors
    assert obj is not None
    folders_model.setParent(obj)
    QQmlEngine.setObjectOwnership(obj, QQmlEngine.ObjectOwnership.CppOwnership)
    _KEEPALIVE.append(engine)
    _KEEPALIVE.append(component)
    _KEEPALIVE.append(obj)
    _KEEPALIVE.append(folders_model)
    return obj


def _invoke(obj, method, *args):
    from PySide6.QtCore import Q_ARG

    QMetaObject.invokeMethod(
        obj, method, Qt.ConnectionType.DirectConnection,
        *[Q_ARG("QVariant", a) for a in args],
    )


class TestOpenContextMenu:
    def test_sets_folder_path_and_collections_on_the_menu(self, pane, controller, qt_app):
        controller.createCollection("Nyaralások")
        qt_app.processEvents()
        _invoke(pane, "openFolderContextMenu", "/kepek/balaton")
        menu = pane.findChild(QObject, "folderContextMenu")
        assert menu.property("folderPath") == "/kepek/balaton"
        collections = menu.property("customCollections")
        assert list(collections) == [{"name": "Nyaralások", "folders": []}]


class TestMoveToCollection:
    def test_move_signal_calls_controller(self, pane, controller, qt_app):
        _invoke(pane, "openFolderContextMenu", "/kepek/balaton")
        menu = pane.findChild(QObject, "folderContextMenu")
        menu.moveToCollectionRequested.emit("Nyaralások")
        qt_app.processEvents()
        assert controller.moved == [("/kepek/balaton", "Nyaralások")]


class TestNewCollectionFlow:
    def test_new_collection_creates_and_moves_the_folder(self, pane, controller, qt_app):
        _invoke(pane, "openFolderContextMenu", "/kepek/balaton")
        menu = pane.findChild(QObject, "folderContextMenu")
        menu.newCollectionRequested.emit()
        qt_app.processEvents()

        dialog = pane.findChild(QObject, "newCollectionDialog")
        assert dialog is not None
        dialog.created.emit("Nyaralások 2024")
        qt_app.processEvents()

        assert controller.created_names == ["Nyaralások 2024"]
        assert controller.moved == [("/kepek/balaton", "Nyaralások 2024")]

    def test_refreshes_collections_model_after_create(self, pane, controller, qt_app):
        dialog = pane.findChild(QObject, "newCollectionDialog")
        dialog.created.emit("Munka")
        qt_app.processEvents()
        assert pane.property("customCollectionsModel") == [
            {"name": "Munka", "folders": []}
        ]


class TestFolderDateFlow:
    def test_set_date_requested_opens_dialog_with_current_override(
        self, pane, controller, qt_app
    ):
        controller.date_overrides["/kepek/balaton"] = "2019-07-04"
        _invoke(pane, "openFolderContextMenu", "/kepek/balaton")
        menu = pane.findChild(QObject, "folderContextMenu")
        menu.setDateRequested.emit()
        qt_app.processEvents()

        dialog = pane.findChild(QObject, "folderDateDialog")
        assert dialog.property("folderPath") == "/kepek/balaton"
        assert dialog.property("currentDate") == "2019-07-04"

    def test_date_accepted_calls_controller(self, pane, controller, qt_app):
        dialog = pane.findChild(QObject, "folderDateDialog")
        dialog.dateAccepted.emit("/kepek/balaton", "2020-01-15")
        qt_app.processEvents()
        assert controller.set_date_calls == [("/kepek/balaton", "2020-01-15")]

    def test_date_cleared_calls_controller(self, pane, controller, qt_app):
        dialog = pane.findChild(QObject, "folderDateDialog")
        dialog.dateCleared.emit("/kepek/balaton")
        qt_app.processEvents()
        assert controller.clear_date_calls == ["/kepek/balaton"]
