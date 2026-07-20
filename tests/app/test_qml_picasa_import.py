"""QML-funkcionális teszt: PicasaImportDialog.qml (#146) — a discoveryController
felderítés-API-ját (scanner/discovery.py, #199) mockolva ellenőrizzük a
dialógus megjelenését, a mappák kiválasztását és az átvételt."""

from PySide6.QtCore import QEventLoop, QMetaObject, QObject, Qt, QTimer


def _child(window, name):
    obj = window.findChild(QObject, name)
    assert obj is not None, f"{name} nem található"
    return obj


def _quit_on(signal):
    loop = QEventLoop()
    signal.connect(loop.quit)
    QTimer.singleShot(5000, loop.quit)
    return loop


def _discovery_controller(engine):
    controller = engine.rootContext().contextProperty("discoveryController")
    assert controller is not None, "discoveryController context property hiányzik"
    return controller


class TestPicasaImportDialog:
    def test_open_and_discover_shows_proposed_folders(
        self, qml_app, qt_app, monkeypatch
    ):
        window, _controller, _lib, engine = qml_app
        from picasapy.scanner import PicasaInstallation

        installation = PicasaInstallation("Wine (~/.wine)", None, None, None)
        monkeypatch.setattr(
            "picasapy.app.discovery_controller.discover_installations",
            lambda: (installation,),
        )
        monkeypatch.setattr(
            "picasapy.app.discovery_controller.propose_watched_folders",
            lambda inst, remap: ("/mnt/nas/fotok",),
        )

        dialog = _child(window, "picasaImportDialog")
        discovery = _discovery_controller(engine)
        loop = _quit_on(discovery.discoveryFinished)
        QMetaObject.invokeMethod(
            dialog, "openAndDiscover", Qt.ConnectionType.DirectConnection
        )
        loop.exec()
        qt_app.processEvents()

        assert dialog.property("visible") is True
        folder_list = _child(window, "picasaImportFolderList")
        assert folder_list.property("count") == 1

    def test_adopt_adds_watched_folder(self, qml_app, qt_app, monkeypatch, tmp_path):
        window, controller, _lib, engine = qml_app
        from picasapy.scanner import PicasaInstallation

        new_folder = tmp_path / "atvett-mappa"
        new_folder.mkdir()
        installation = PicasaInstallation("Kézi mappa", None, None, None)
        monkeypatch.setattr(
            "picasapy.app.discovery_controller.discover_installations",
            lambda: (installation,),
        )
        monkeypatch.setattr(
            "picasapy.app.discovery_controller.propose_watched_folders",
            lambda inst, remap: (str(new_folder),),
        )

        dialog = _child(window, "picasaImportDialog")
        discovery = _discovery_controller(engine)
        loop = _quit_on(discovery.discoveryFinished)
        QMetaObject.invokeMethod(
            dialog, "openAndDiscover", Qt.ConnectionType.DirectConnection
        )
        loop.exec()
        qt_app.processEvents()

        adopt_button = _child(window, "picasaImportAdoptButton")
        sync_loop = _quit_on(controller.syncFinished)
        QMetaObject.invokeMethod(
            adopt_button, "clicked", Qt.ConnectionType.DirectConnection
        )
        sync_loop.exec()
        qt_app.processEvents()

        assert str(new_folder) in controller.watchedFolders
        assert dialog.property("visible") is False

    def test_no_installations_found_shows_manual_browse_hint(
        self, qml_app, qt_app, monkeypatch
    ):
        window, _controller, _lib, engine = qml_app
        monkeypatch.setattr(
            "picasapy.app.discovery_controller.discover_installations",
            lambda: (),
        )

        dialog = _child(window, "picasaImportDialog")
        discovery = _discovery_controller(engine)
        loop = _quit_on(discovery.discoveryFinished)
        QMetaObject.invokeMethod(
            dialog, "openAndDiscover", Qt.ConnectionType.DirectConnection
        )
        loop.exec()
        qt_app.processEvents()

        folder_list = _child(window, "picasaImportFolderList")
        assert folder_list.property("count") == 0
        adopt_button = _child(window, "picasaImportAdoptButton")
        assert adopt_button.property("enabled") is False

    def test_folder_manager_button_reopens_dialog(self, qml_app, qt_app, monkeypatch):
        window, _controller, _lib, engine = qml_app
        monkeypatch.setattr(
            "picasapy.app.discovery_controller.discover_installations",
            lambda: (),
        )

        folder_manager = _child(window, "folderManagerDialog")
        QMetaObject.invokeMethod(
            folder_manager, "open", Qt.ConnectionType.DirectConnection
        )
        qt_app.processEvents()

        dialog = _child(window, "picasaImportDialog")
        discovery = _discovery_controller(engine)
        loop = _quit_on(discovery.discoveryFinished)
        adopt_open_button = _child(window, "adoptPicasaFoldersButton")
        QMetaObject.invokeMethod(
            adopt_open_button, "clicked", Qt.ConnectionType.DirectConnection
        )
        loop.exec()
        qt_app.processEvents()

        assert dialog.property("visible") is True
