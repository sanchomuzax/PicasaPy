"""QML-funkcionális tesztek: fájlműveletek (#15) és export (#16) bekötése a
Main.qml-be — kontextusmenü, átnevezés-dialógus, export-dialógus, menüsor.

Külön fájlban a test_qml_functional.py-tól, hogy a #53-as flaky (néző +
image provider GIL) kizárásakor ezek a tesztek futhassanak tovább. A néző
képbetöltését itt egyetlen teszt sem érinti.
"""

from PySide6.QtCore import Q_ARG, QEventLoop, QMetaObject, QObject, Qt, QTimer


# a qml_app fixture a tests/app/conftest.py-ban él (közös a funkcionális
# teszt-fájlokkal)


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
        loop = QEventLoop()
        controller.syncFinished.connect(loop.quit)
        QMetaObject.invokeMethod(dialog, "accept", Qt.ConnectionType.DirectConnection)
        qt_app.processEvents()
        # a fájl azonnal átnevezve; a rács-frissítés (#86 óta) háttérszálas
        # resyncből érkezik — arra a syncFinished-del várunk
        assert (lib / "atnevezve.jpg").exists()
        assert not (lib / "a.jpg").exists()
        QTimer.singleShot(5000, loop.quit)
        loop.exec()
        qt_app.processEvents()
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
