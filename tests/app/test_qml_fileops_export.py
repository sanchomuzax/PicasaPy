"""QML-funkcionális tesztek: fájlműveletek (#15) és export (#16) bekötése a
Main.qml-be — kontextusmenü, átnevezés-dialógus, export-dialógus, menüsor.

Külön fájlban a test_qml_functional.py-tól, hogy a #53-as flaky (néző +
image provider GIL) kizárásakor ezek a tesztek futhassanak tovább. A néző
képbetöltését itt egyetlen teszt sem érinti.
"""

import pytest
from PySide6.QtCore import Q_ARG, QEventLoop, QMetaObject, QObject, Qt, QTimer

from picasapy.index import open_index, sync_tree
from picasapy.version import version_string
from support.jpeg_factory import make_jpeg


@pytest.fixture
def qml_app(qt_app, tmp_path):
    """Teljes app betöltve offscreen: (window, controller, lib, engine)."""
    import picasapy.app.application as app_module
    from picasapy.app.controller import AppController
    from picasapy.app.edit_controller import EditController
    from picasapy.app.edit_preview import EditPreviewProvider
    from picasapy.app.fileops_controller import FileOpsController
    from picasapy.app.thumbnail_provider import ThumbnailProvider
    from picasapy.thumbs import ThumbnailCache
    from PySide6.QtCore import QSettings
    from PySide6.QtQml import QQmlApplicationEngine

    lib = tmp_path / "kepek"
    lib.mkdir()
    make_jpeg(lib / "a.jpg", size=(320, 160))
    make_jpeg(lib / "b.jpg", size=(100, 100))
    db = tmp_path / "index.db"
    with open_index(db) as conn:
        sync_tree(conn, lib)

    settings = QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat)
    provider = ThumbnailProvider(ThumbnailCache(tmp_path / "thumbs", size=32))
    controller = AppController(db, (str(lib),), provider, settings=settings)
    edit_preview = EditPreviewProvider()
    edit_controller = EditController(edit_preview)
    fileops_controller = FileOpsController()
    app_module.wire_fileops(fileops_controller, controller)
    engine = QQmlApplicationEngine()
    engine.addImageProvider("thumbs", provider)
    engine.addImageProvider("editpreview", edit_preview)
    engine.addImportPath(str(app_module._APP_DIR / "qml"))
    engine.rootContext().setContextProperty("controller", controller)
    engine.rootContext().setContextProperty("editController", edit_controller)
    engine.rootContext().setContextProperty(
        "fileOpsController", fileops_controller
    )
    engine.rootContext().setContextProperty("appVersion", version_string())
    engine.load(str(app_module._APP_DIR / "qml" / "Main.qml"))
    assert engine.rootObjects(), "Main.qml betöltése sikertelen"
    window = engine.rootObjects()[0]
    controller._reload()
    controller.selectFolder(str(lib))
    qt_app.processEvents()
    yield window, controller, lib, engine
    engine.deleteLater()
    qt_app.processEvents()


def _child(window, name):
    obj = window.findChild(QObject, name)
    assert obj is not None, f"{name} nem található"
    return obj


def _as_list(value):
    """QML var-lista → Python-lista (a property QJSValue-ként jön át)."""
    return value.toVariant() if hasattr(value, "toVariant") else list(value)


def _select_row(window, qt_app, row):
    window.setProperty("selectedIndexes", [row])
    window.setProperty("selectedIndex", row)
    qt_app.processEvents()


class TestContextMenuWiring:
    def test_open_selects_row_and_opens_menu(self, qml_app, qt_app):
        window, _controller, _lib, _engine = qml_app
        grid = _child(window, "photoGrid")
        QMetaObject.invokeMethod(
            window, "openPhotoContextMenu", Qt.ConnectionType.DirectConnection,
            Q_ARG("QVariant", 0), Q_ARG("QVariant", grid),
            Q_ARG("QVariant", 5), Q_ARG("QVariant", 5),
        )
        qt_app.processEvents()
        menu = _child(window, "photoContextMenu")
        assert menu.property("visible") is True
        assert _as_list(window.property("selectedIndexes")) == [0]
        assert window.property("fileOpTargetRow") == 0
        QMetaObject.invokeMethod(menu, "close", Qt.ConnectionType.DirectConnection)
        qt_app.processEvents()

    def test_open_keeps_existing_multi_selection(self, qml_app, qt_app):
        # jobbklikk a kijelölés EGYIK elemén: a többes kijelölés megmarad,
        # a műveletek (törlés/áthelyezés) a teljes kijelölésre mennek
        window, _controller, _lib, _engine = qml_app
        window.setProperty("selectedIndexes", [0, 1])
        window.setProperty("selectedIndex", 1)
        grid = _child(window, "photoGrid")
        QMetaObject.invokeMethod(
            window, "openPhotoContextMenu", Qt.ConnectionType.DirectConnection,
            Q_ARG("QVariant", 0), Q_ARG("QVariant", grid),
            Q_ARG("QVariant", 5), Q_ARG("QVariant", 5),
        )
        qt_app.processEvents()
        assert _as_list(window.property("selectedIndexes")) == [0, 1]
        menu = _child(window, "photoContextMenu")
        QMetaObject.invokeMethod(menu, "close", Qt.ConnectionType.DirectConnection)
        qt_app.processEvents()


class TestRenameDialog:
    def test_rename_end_to_end(self, qml_app, qt_app):
        # F2-út: dialógus nyitás → új név → OK → a fájl átnevezve a lemezen,
        # és a resync (wire_fileops) után a modell is az új nevet mutatja
        window, controller, lib, _engine = qml_app
        dialog = _child(window, "renameDialog")
        QMetaObject.invokeMethod(
            dialog, "openFor", Qt.ConnectionType.DirectConnection,
            Q_ARG("QVariant", 0),
        )
        qt_app.processEvents()
        field = _child(window, "renameField")
        assert field.property("text") == "a.jpg"
        field.setProperty("text", "atnevezve.jpg")
        QMetaObject.invokeMethod(dialog, "accept", Qt.ConnectionType.DirectConnection)
        qt_app.processEvents()
        assert (lib / "atnevezve.jpg").exists()
        assert not (lib / "a.jpg").exists()
        model_names = {photo.name for photo in controller.photos.photos}
        assert model_names == {"atnevezve.jpg", "b.jpg"}


class TestMenuBarFileActions:
    def test_items_follow_selection(self, qml_app, qt_app):
        window, _controller, _lib, _engine = qml_app
        rename_item = _child(window, "menuFileRename")
        export_item = _child(window, "menuFileExport")
        window.setProperty("selectedIndexes", [])
        qt_app.processEvents()
        assert rename_item.property("enabled") is False
        assert export_item.property("enabled") is False
        _select_row(window, qt_app, 0)
        assert rename_item.property("enabled") is True
        assert export_item.property("enabled") is True


class TestExportDialog:
    def test_export_end_to_end(self, qml_app, qt_app, tmp_path):
        window, controller, _lib, _engine = qml_app
        _select_row(window, qt_app, 0)
        target = tmp_path / "export-cel"
        dialog = _child(window, "exportDialog")
        QMetaObject.invokeMethod(
            dialog, "openForSelection", Qt.ConnectionType.DirectConnection
        )
        qt_app.processEvents()
        assert dialog.property("visible") is True
        dialog.setProperty("targetFolder", target.as_uri())
        results = []
        loop = QEventLoop()
        controller.exportFinished.connect(
            lambda done, failed: results.append((done, failed))
        )
        controller.exportFinished.connect(loop.quit)
        QMetaObject.invokeMethod(dialog, "accept", Qt.ConnectionType.DirectConnection)
        QTimer.singleShot(5000, loop.quit)
        loop.exec()
        qt_app.processEvents()
        assert results == [(1, 0)]
        assert (target / "a.jpg").exists()
        # a visszajelző dialógus is megnyílt az exportFinished-re
        result_dialog = _child(window, "exportResultDialog")
        assert result_dialog.property("visible") is True

    def test_open_requires_selection(self, qml_app, qt_app):
        window, _controller, _lib, _engine = qml_app
        window.setProperty("selectedIndexes", [])
        dialog = _child(window, "exportDialog")
        QMetaObject.invokeMethod(
            dialog, "openForSelection", Qt.ConnectionType.DirectConnection
        )
        qt_app.processEvents()
        assert dialog.property("visible") is False


class TestTrayExportButton:
    def test_enabled_follows_selection(self, qml_app, qt_app):
        window, _controller, _lib, _engine = qml_app
        button = _child(window, "trayExportButton")
        window.setProperty("selectedIndexes", [])
        qt_app.processEvents()
        assert button.property("enabled") is False
        _select_row(window, qt_app, 0)
        assert button.property("enabled") is True
