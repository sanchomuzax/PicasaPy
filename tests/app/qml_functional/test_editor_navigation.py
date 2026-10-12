"""A néző mappahatáron belüli lapozásának funkcionális próbái."""

import pytest
from PySide6.QtCore import QObject

from picasapy.index import open_index, sync_tree
from support.jpeg_factory import make_jpeg


class TestViewerFolderBoundedNavigation:
    """#84: a nagy nézőben (PhotoViewer) a lapozás CSAK az aktuális mappa
    képei között mozogjon — a rács (feed) nézet szűrői (pl. csillag-szűrő)
    több mappa fotóit is felsorolhatják egymás után, de a néző ne lépjen
    át a szomszéd mappába."""

    @pytest.fixture
    def qml_app_multi_folder(self, qt_app, tmp_path):
        """Két mappa csillagozott képekkel, egyetlen (mappaátlépő) rács-
        listában betöltve — ahogy a csillag-szűrő is összefésüli őket."""
        import picasapy.app.application as app_module
        from picasapy.app.controller import AppController
        from picasapy.app.discovery_controller import DiscoveryController
        from picasapy.app.edit_controller import EditController
        from picasapy.app.edit_preview import EditPreviewProvider
        from picasapy.app.face_scan_controller import FaceScanController
        from picasapy.app.faces_helper import FacesHelper
        from picasapy.app.fileops_controller import FileOpsController
        from picasapy.app.folder_tree_controller import FolderTreeController
        from picasapy.app.import_source_controller import ImportSourceController
        from picasapy.app.thumbnail_provider import ThumbnailProvider
        from picasapy.app.timeline_controller import TimelineController
        from picasapy.thumbs import ThumbnailCache
        from picasapy.version import version_string
        from PySide6.QtCore import QSettings
        from PySide6.QtQml import QQmlApplicationEngine

        lib = tmp_path / "kepek"
        folder_a = lib / "nyaralas"
        folder_b = lib / "telek"
        folder_a.mkdir(parents=True)
        folder_b.mkdir()
        make_jpeg(folder_a / "a1.jpg")
        make_jpeg(folder_a / "a2.jpg")
        make_jpeg(folder_b / "b1.jpg")
        make_jpeg(folder_b / "b2.jpg")
        (folder_a / ".picasa.ini").write_text(
            "[a1.jpg]\nstar=yes\n\n[a2.jpg]\nstar=yes\n", encoding="utf-8"
        )
        (folder_b / ".picasa.ini").write_text(
            "[b1.jpg]\nstar=yes\n\n[b2.jpg]\nstar=yes\n", encoding="utf-8"
        )
        db = tmp_path / "index.db"
        with open_index(db) as conn:
            sync_tree(conn, lib)

        settings = QSettings(
            str(tmp_path / "settings.ini"), QSettings.Format.IniFormat
        )
        provider = ThumbnailProvider(ThumbnailCache(tmp_path / "thumbs", size=32))
        controller = AppController(db, (str(lib),), provider, settings=settings)
        edit_preview = EditPreviewProvider()
        edit_controller = EditController(edit_preview)
        engine = QQmlApplicationEngine()
        engine.addImageProvider("thumbs", provider)
        engine.addImageProvider("editpreview", edit_preview)
        engine.addImportPath(str(app_module._APP_DIR / "qml"))
        engine.rootContext().setContextProperty("controller", controller)
        engine.rootContext().setContextProperty("editController", edit_controller)
        # #305: a Main.qml és a benne élő komponensek (MainToolbar,
        # PicasaImportDialog, FileOpsDialogs, AboutDialog, TimelineView…)
        # az application.py bekötésének megfelelően MINDIG várják ezeket a
        # context property-ket — hiányukban nem null-t, hanem "X is not
        # defined" ReferenceError-t dobnak. A fixture ezért a közös
        # qml_app-hoz hasonlóan mindegyiket regisztrálja (a teszt maga csak
        # a controller/editController-t használja, a többi csak a
        # figyelmeztetés-mentességhez kell).
        fileops_controller = FileOpsController()
        app_module.wire_fileops(fileops_controller, controller)
        engine.rootContext().setContextProperty(
            "fileOpsController", fileops_controller
        )
        discovery_controller = DiscoveryController(
            add_folder=controller.addWatchedFolder
        )
        engine.rootContext().setContextProperty(
            "discoveryController", discovery_controller
        )
        folder_tree_controller = FolderTreeController()
        engine.rootContext().setContextProperty(
            "folderTreeController", folder_tree_controller
        )
        faces_helper = FacesHelper()
        engine.rootContext().setContextProperty("facesHelper", faces_helper)
        face_scan_controller = FaceScanController(db, faces_helper=faces_helper)
        engine.rootContext().setContextProperty(
            "faceScanController", face_scan_controller
        )
        timeline_controller = TimelineController(db, provider)
        controller.syncFinished.connect(timeline_controller.reload)
        engine.rootContext().setContextProperty(
            "timelineController", timeline_controller
        )
        import_source_controller = ImportSourceController(
            provider, add_folder=controller.addWatchedFolder
        )
        engine.rootContext().setContextProperty(
            "importSourceController", import_source_controller
        )
        engine.rootContext().setContextProperty("appVersion", version_string())
        engine.load(str(app_module._APP_DIR / "qml" / "Main.qml"))
        assert engine.rootObjects(), "Main.qml betöltése sikertelen"
        window = engine.rootObjects()[0]
        controller._reload()
        # a rács (feed) nézet: mindkét mappa csillagozott képei, folytonosan
        # (f.path, p.name szerint: nyaralas/a1, a2, telek/b1, b2)
        controller.showStarred()
        qt_app.processEvents()
        yield window, controller, engine
        engine.deleteLater()
        qt_app.processEvents()

    def _open_viewer(self, window, qt_app, index):
        window.setProperty("viewerOpen", True)
        viewer = window.findChild(QObject, "photoViewer")
        viewer.setProperty("currentIndex", index)
        qt_app.processEvents()
        return viewer

    def test_next_stops_at_folder_end(self, qml_app_multi_folder, qt_app):
        from PySide6.QtCore import QMetaObject, Qt

        window, controller, _ = qml_app_multi_folder
        assert controller.photos.rowCount() == 4  # a rács nem szűkül mappára
        viewer = self._open_viewer(window, qt_app, index=1)  # a2.jpg — nyaralas utolsó képe
        QMetaObject.invokeMethod(viewer, "next", Qt.ConnectionType.DirectConnection)
        qt_app.processEvents()
        assert viewer.property("currentIndex") == 1, (
            "a mappahatárnál a néző nem léphet át a szomszéd mappába"
        )

    def test_previous_stops_at_folder_start(self, qml_app_multi_folder, qt_app):
        from PySide6.QtCore import QMetaObject, Qt

        window, controller, _ = qml_app_multi_folder
        viewer = self._open_viewer(window, qt_app, index=2)  # b1.jpg — telek első képe
        QMetaObject.invokeMethod(
            viewer, "previous", Qt.ConnectionType.DirectConnection
        )
        qt_app.processEvents()
        assert viewer.property("currentIndex") == 2

    def test_next_moves_within_folder(self, qml_app_multi_folder, qt_app):
        from PySide6.QtCore import QMetaObject, Qt

        window, controller, _ = qml_app_multi_folder
        viewer = self._open_viewer(window, qt_app, index=0)  # a1.jpg
        QMetaObject.invokeMethod(viewer, "next", Qt.ConnectionType.DirectConnection)
        qt_app.processEvents()
        assert viewer.property("currentIndex") == 1  # a2.jpg — még a nyaralas mappa

    def test_nav_buttons_disabled_at_folder_boundaries(
        self, qml_app_multi_folder, qt_app
    ):
        window, controller, _ = qml_app_multi_folder
        viewer = self._open_viewer(window, qt_app, index=1)  # a2.jpg — nyaralas utolsó
        next_button = window.findChild(QObject, "viewerNextButton")
        assert next_button is not None, "viewerNextButton nem található"
        assert next_button.property("enabled") is False
        # ugyanezen a nézőn (egyetlen engine) a telek mappa első képénél a
        # ◀ gomb is letiltva — egy fixture-példányban ellenőrizve, hogy az
        # offscreen tesztkörnyezetben ne kelljen két QQmlApplicationEngine-t
        # egymás után létrehozni (ismert instabilitás a tesztfuttatóban)
        viewer.setProperty("currentIndex", 2)  # b1.jpg — telek első képe
        qt_app.processEvents()
        prev_button = window.findChild(QObject, "viewerPrevButton")
        assert prev_button is not None, "viewerPrevButton nem található"
        assert prev_button.property("enabled") is False
