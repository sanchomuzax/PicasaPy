"""QML-funkcionális teszt: a felhasználói mappa-gyűjtemények (#320) végre
megjelennek a bal panelen (#476) — eddig csak a mappa-kontextusmenü
„Áthelyezés gyűjteménybe" almenüjében léteztek, a `FolderPane.qml` maga nem
sorolta fel őket.

A teszt a `test_folder_pane_collections_320.py` szerkezetét követi: egy
stub Python-controllerrel (`customCollections` property-vel) hajtjuk a
`FolderPane.qml`-t, VALÓDI AppController nélkül.

A gyűjtemény-fejlécek és mappa-sorok az outer `customCollectionsRepeater`
dinamikusan létrehozott elemei — ezek `pane.findChild`-dal közvetlenül NEM
érhetők el (MEMORY 2026-07-31: a Repeater-delegate `parentItem` elválik a
`QObject::parent()`-től). A `Repeater.itemAt(index)` viszont a delegate-
példány gyökerét adja vissza, ANNAK statikus (a QML-forrásban közvetlenül
deklarált) gyerekei — a benne lévő `CollectionHeader` és a belső `Repeater`
— már rendes `QObject`-gyerekek, tehát `findChild`-dal elérhetők."""

from __future__ import annotations

import pytest
from PySide6.QtCore import (
    Property,
    QMetaObject,
    QObject,
    QPointF,
    Q_ARG,
    Q_RETURN_ARG,
    Qt,
    QUrl,
    Signal,
    Slot,
)
from PySide6.QtQml import QQmlComponent, QQmlEngine
from PySide6.QtQuick import QQuickItem, QQuickView
from PySide6.QtTest import QTest

_KEEPALIVE = []


class _StubController(QObject):
    """A FolderPane #320/#476-os bekötésének felszíne — csak a
    `customCollections` property-t és a gyűjtemény-csukottság két slotját
    adja, memóriában."""

    customCollectionsChanged = Signal()

    def __init__(self):
        super().__init__()
        self._collections: list[dict] = []
        # #422: a gyűjtemény-menü (átnevezés/eltávolítás) bekötéséhez
        self.renamed: list[tuple[str, str]] = []
        self.deleted: list[str] = []

    @Property("QVariant", notify=customCollectionsChanged)
    def customCollections(self):
        return self._collections

    def set_collections(self, collections: list[dict]) -> None:
        self._collections = collections
        self.customCollectionsChanged.emit()

    @Slot(str, result=bool)
    def isCollectionCollapsed(self, name):
        return False

    @Slot(str, bool)
    def setCollectionCollapsed(self, name, collapsed):
        pass

    @Slot(str, str)
    def renameCollection(self, old_name, new_name):
        self.renamed.append((old_name, new_name))

    @Slot(str)
    def deleteCollection(self, name):
        self.deleted.append(name)


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
    # üres, de VALÓS modell, MÁR a létrehozáskor átadva (ld. #305 — a
    # `Connections { target: folderList.model }` undefined targetre
    # "Unable to assign" hibát dobna, ha csak utólag érkezne).
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


@pytest.fixture
def shown_view(qt_app, controller):
    """Valódi, KIRAJZOLT `QQuickView` (a `pane` fixture hasábja nem kap
    ablakot/geometriát) — csak a (c) kattintás-teszthez kell, ahol a
    `MouseArea` egy IGAZI, koordinátákkal kiváltott kattintásra reagál
    (a `QQuickView.setContent` a `pane` fixtureéhoz hasonlóan a
    `createWithInitialProperties`-szel létrehozott, foldersModel-lel már
    ellátott komponenst rögzíti — ld. #305-ös megjegyzés fent)."""
    import picasapy.app.application as app_module
    from picasapy.app.models import FolderListModel

    engine = QQmlEngine()
    engine.addImportPath(str(app_module._APP_DIR / "qml"))
    engine.rootContext().setContextProperty("controller", controller)
    url = QUrl.fromLocalFile(
        str(app_module._APP_DIR / "qml" / "PicasaPy" / "FolderPane.qml")
    )
    component = QQmlComponent(engine, url)
    folders_model = FolderListModel()
    obj = component.createWithInitialProperties({"foldersModel": folders_model})
    errors = [e.toString() for e in component.errors()]
    assert errors == [], errors
    assert obj is not None
    folders_model.setParent(obj)

    view = QQuickView(engine, None)
    view.setResizeMode(QQuickView.ResizeMode.SizeRootObjectToView)
    view.setContent(url, component, obj)
    view.resize(320, 600)
    view.show()
    QTest.qWaitForWindowExposed(view)
    qt_app.processEvents()

    _KEEPALIVE.append(engine)
    _KEEPALIVE.append(component)
    _KEEPALIVE.append(view)
    _KEEPALIVE.append(obj)
    _KEEPALIVE.append(folders_model)
    return view


def _folder_row(collection_item, collection_name, index):
    """A belső (mappákat felsoroló) Repeater index. sora — ugyanaz a
    kétlépéses `itemAt` trükk, mint `_collection_item`-nél, mert ez a
    Repeater is dinamikusan hozza létre az elemeit."""
    repeater = collection_item.findChild(
        QObject, "customCollectionFoldersRepeater_" + collection_name
    )
    assert repeater is not None, "a mappákat felsoroló belső Repeater nem található"
    row = QMetaObject.invokeMethod(
        repeater, "itemAt", Qt.ConnectionType.DirectConnection,
        Q_RETURN_ARG(QQuickItem), Q_ARG(int, index),
    )
    assert row is not None, f"a(z) {index}. mappa-sor nem jött létre"
    return row


def _collection_item(pane, index):
    """A `customCollectionsRepeater` index. eleme (a gyűjtemény-Column
    gyökere) — a `Repeater.itemAt` a delegate-példány QObject-jét adja
    vissza, aminek a statikus gyerekei findChild-dal már elérhetők.

    A `Repeater.itemAt(int)` visszatérési típusa (`QQuickItem*`) miatt
    közvetlen Python-attribútumhívással nem hívható (PySide "Unknown
    return type" hibát dob) — `QMetaObject.invokeMethod`-dal, explicit
    `Q_RETURN_ARG(QQuickItem)`-mel kell hívni."""
    repeater = pane.findChild(QObject, "customCollectionsRepeater")
    assert repeater is not None, "customCollectionsRepeater nem található"
    item = QMetaObject.invokeMethod(
        repeater, "itemAt", Qt.ConnectionType.DirectConnection,
        Q_RETURN_ARG(QQuickItem), Q_ARG(int, index),
    )
    assert item is not None, f"a(z) {index}. gyűjtemény-elem nem jött létre"
    return item


class TestCustomCollectionsListedInPane:
    """(a) két gyűjteményhez két fejléc, (b) a mappáik sorként jelennek meg."""

    def test_two_collections_get_two_headers(self, pane, controller, qt_app):
        controller.set_collections(
            [
                {"name": "Nyaralások", "folders": ["/kepek/balaton"]},
                {"name": "Munka", "folders": ["/kepek/iroda", "/kepek/konferencia"]},
            ]
        )
        qt_app.processEvents()

        repeater = pane.findChild(QObject, "customCollectionsRepeater")
        assert repeater.property("count") == 2

        item0 = _collection_item(pane, 0)
        item1 = _collection_item(pane, 1)
        header0 = item0.findChild(QObject, "customCollection_Nyaralások")
        header1 = item1.findChild(QObject, "customCollection_Munka")
        assert header0 is not None, "a Nyaralások fejléc nem jött létre"
        assert header1 is not None, "a Munka fejléc nem jött létre"
        assert header0.property("text") == "Nyaralások (1)"
        assert header1.property("text") == "Munka (2)"

    def test_collection_folders_appear_as_rows(self, pane, controller, qt_app):
        controller.set_collections(
            [{"name": "Nyaralások", "folders": ["/kepek/balaton", "/kepek/tisza"]}]
        )
        qt_app.processEvents()

        item0 = _collection_item(pane, 0)
        row1 = _folder_row(item0, "Nyaralások", 0)
        row2 = _folder_row(item0, "Nyaralások", 1)
        assert row1.objectName() == "customCollectionFolder_/kepek/balaton"
        assert row2.objectName() == "customCollectionFolder_/kepek/tisza"
        assert row1.property("visible") is True
        assert row2.property("visible") is True


class TestCustomCollectionFolderClick:
    """(c) a mappa-sorra kattintás folderChosen-t ad a helyes útvonallal.

    Valódi, koordinátákkal kiváltott egérkattintással teszteljük (nem a
    C++ `clicked(QQuickMouseEvent*)` jel közvetlen emittálásával — az
    Python felől nem konstruálható meg típushelyesen), ezért itt a
    `shown_view` fixture-t használjuk a könnyű `pane` helyett."""

    def test_clicking_a_folder_row_emits_folder_chosen(
        self, shown_view, controller, qt_app
    ):
        controller.set_collections(
            [{"name": "Nyaralások", "folders": ["/kepek/balaton"]}]
        )
        qt_app.processEvents()
        # a `ColumnLayout` a modell-frissítés utáni újratördelést csak a
        # következő polish-körben végzi el — enélkül a sor szélessége/
        # pozíciója még 0 maradna, és a kattintás mellétrafálna.
        QTest.qWait(50)
        qt_app.processEvents()

        pane = shown_view.rootObject()
        item0 = _collection_item(pane, 0)
        row = _folder_row(item0, "Nyaralások", 0)
        assert row.objectName() == "customCollectionFolder_/kepek/balaton"

        received: list[str] = []
        pane.folderChosen.connect(lambda path: received.append(path))

        center = row.mapToScene(QPointF(row.width() / 2, row.height() / 2))
        QTest.mouseClick(
            shown_view, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier,
            center.toPoint(),
        )
        qt_app.processEvents()

        assert received == ["/kepek/balaton"]


class TestCustomCollectionCollapse:
    """(d) a fejléc csukása elrejti a hozzá tartozó mappasorokat."""

    def test_toggling_the_header_hides_the_rows(self, pane, controller, qt_app):
        controller.set_collections(
            [{"name": "Nyaralások", "folders": ["/kepek/balaton"]}]
        )
        qt_app.processEvents()

        item0 = _collection_item(pane, 0)
        row = _folder_row(item0, "Nyaralások", 0)
        assert row.property("visible") is True

        header_row = item0.findChild(QObject, "customCollection_NyaralásokRow")
        assert header_row is not None, "a fejléc-sor (Row) nem található"
        header_row.toggled.emit()
        qt_app.processEvents()

        row = _folder_row(item0, "Nyaralások", 0)
        assert row.property("visible") is False

        # a csukott állapot a pane collapsedCollections térképében is látszik
        collapsed = pane.property("collapsedCollections")
        if hasattr(collapsed, "toVariant"):
            collapsed = collapsed.toVariant()
        assert collapsed["Nyaralások"] is True

        # újranyitáskor a sor ismét látszik
        header_row.toggled.emit()
        qt_app.processEvents()
        row = _folder_row(item0, "Nyaralások", 0)
        assert row.property("visible") is True


class TestCustomCollectionContextMenu:
    """#422 (utolsó menü): a gyűjtemény-fejléc jobbklikk-menüje —
    `pane.openCollectionContextMenu(name)`-en át (a delegate-MouseArea/
    TapHandler Repeater-elemből findChild-dal el nem érhető,
    MEMORY 2026-07-31), az `openAlbumContextMenu` mintája."""

    def test_open_sets_the_collection_name_on_the_menu(self, pane, controller, qt_app):
        controller.set_collections([{"name": "Nyaralások", "folders": []}])
        qt_app.processEvents()

        QMetaObject.invokeMethod(
            pane, "openCollectionContextMenu", Qt.ConnectionType.DirectConnection,
            Q_ARG("QVariant", "Nyaralások"),
        )
        menu = pane.findChild(QObject, "collectionContextMenu")
        assert menu is not None
        assert menu.property("collectionName") == "Nyaralások"

    def test_remove_requested_asks_before_deleting(self, pane, controller, qt_app):
        controller.set_collections([{"name": "Nyaralások", "folders": []}])
        qt_app.processEvents()
        QMetaObject.invokeMethod(
            pane, "openCollectionContextMenu", Qt.ConnectionType.DirectConnection,
            Q_ARG("QVariant", "Nyaralások"),
        )
        menu = pane.findChild(QObject, "collectionContextMenu")
        menu.removeRequested.emit()
        qt_app.processEvents()
        assert controller.deleted == []

        confirm = pane.findChild(QObject, "removeCollectionConfirmDialog")
        assert confirm is not None
        confirm.confirmed.emit()
        qt_app.processEvents()
        assert controller.deleted == ["Nyaralások"]

    def test_rename_requested_opens_dialog_with_current_name_then_renames(
        self, pane, controller, qt_app
    ):
        controller.set_collections([{"name": "Nyaralások", "folders": []}])
        qt_app.processEvents()
        QMetaObject.invokeMethod(
            pane, "openCollectionContextMenu", Qt.ConnectionType.DirectConnection,
            Q_ARG("QVariant", "Nyaralások"),
        )
        menu = pane.findChild(QObject, "collectionContextMenu")
        menu.renameRequested.emit()
        qt_app.processEvents()

        dialog = pane.findChild(QObject, "newCollectionDialog")
        assert dialog is not None
        assert dialog.property("initialName") == "Nyaralások"

        dialog.created.emit("Nyaralások 2024")
        qt_app.processEvents()

        assert controller.renamed == [("Nyaralások", "Nyaralások 2024")]
