"""QML-funkcionális tesztek: szerkesztő — EditorPanel/CropOverlay ↔
EditController ↔ ini bekötés, és a néző mappahatáron belüli lapozása
(#155: a korábbi `test_qml_functional.py` egyik szelete, processzenkénti
izolációhoz)."""

import pytest
from PySide6.QtCore import QObject

from picasapy.index import open_index, sync_tree
from support.jpeg_factory import make_jpeg


class TestEditorWiring:
    """A #19-es bekötés: EditorPanel/CropOverlay ↔ EditController ↔ ini."""

    def _open_viewer(self, window, qt_app, index=0):
        window.setProperty("viewerOpen", True)
        viewer = window.findChild(QObject, "photoViewer")
        viewer.setProperty("currentIndex", index)
        qt_app.processEvents()
        return viewer

    def _edit_controller(self, engine):
        return engine.rootContext().contextProperty("editController")

    def test_viewer_open_starts_edit_session(self, qml_app, qt_app):
        window, _, engine = qml_app
        self._open_viewer(window, qt_app)
        edit = self._edit_controller(engine)
        assert edit.property("previewSource").startswith("image://editpreview/")
        image = window.findChild(QObject, "viewerImage")
        assert image.property("source").toString().startswith("image://editpreview/")

    def test_viewer_close_ends_edit_session(self, qml_app, qt_app):
        window, _, engine = qml_app
        self._open_viewer(window, qt_app)
        window.setProperty("viewerOpen", False)
        qt_app.processEvents()
        assert self._edit_controller(engine).property("previewSource") == ""

    def test_panel_toggle_writes_ini_and_syncs_state(self, qml_app, qt_app, tmp_path):
        from PySide6.QtCore import Q_ARG, QMetaObject, Qt

        window, _, engine = qml_app
        self._open_viewer(window, qt_app)
        panel = window.findChild(QObject, "viewerEditorPanel")
        assert panel is not None, "viewerEditorPanel nem található"
        QMetaObject.invokeMethod(
            panel,
            "handleToolClick",
            Qt.ConnectionType.DirectConnection,
            Q_ARG("QVariant", "autolight"),
        )
        qt_app.processEvents()
        ini_text = (tmp_path / "kepek" / ".picasa.ini").read_text(encoding="utf-8")
        assert "[a.jpg]" in ini_text
        assert "autolight=1" in ini_text
        # a panel állapota az EditController igazságforrásából szinkronizált:
        # az egygombos javítás gombja tiltott, amíg ő a lánc utolsó eleme (#116)
        assert panel.property("autolightEnabled") is False
        # a kép forrása új ?rev=-et kap → az előnézet frissül
        image = window.findChild(QObject, "viewerImage")
        assert "?rev=" in image.property("source").toString()

    def test_crop_accept_persists_and_advances(self, qml_app, qt_app, tmp_path):
        from PySide6.QtCore import QMetaObject, QRectF, Qt

        window, _, engine = qml_app
        viewer = self._open_viewer(window, qt_app)
        panel = window.findChild(QObject, "viewerEditorPanel")
        panel.setProperty("cropActive", True)
        qt_app.processEvents()
        overlay = window.findChild(QObject, "cropOverlay")
        assert overlay is not None, "cropOverlay nem található"
        assert overlay.property("visible") is True
        overlay.setProperty("cropRect", QRectF(0.25, 0.25, 0.5, 0.5))
        overlay.setProperty("hasSelection", True)
        QMetaObject.invokeMethod(
            overlay, "acceptCrop", Qt.ConnectionType.DirectConnection
        )
        qt_app.processEvents()
        ini_text = (tmp_path / "kepek" / ".picasa.ini").read_text(encoding="utf-8")
        assert "crop64=1," in ini_text
        # Enter-flow: elfogadás után a néző a következő képre lép, a
        # vágó-mód megmarad (sorozat-vágás)
        assert viewer.property("currentIndex") == 1
        assert panel.property("cropActive") is True

    def test_tilt_drag_previews_live_then_commits_on_release(
        self, qml_app, qt_app, tmp_path
    ):
        """#72: húzás közben élő előnézet, ini-mentés nélkül; elengedéskor ír."""
        window, _, _ = qml_app
        self._open_viewer(window, qt_app)
        panel = window.findChild(QObject, "viewerEditorPanel")
        panel.setProperty("tiltActive", True)
        qt_app.processEvents()
        slider = window.findChild(QObject, "tiltSlider")
        assert slider is not None, "tiltSlider nem található"
        image = window.findChild(QObject, "viewerImage")
        before_source = image.property("source").toString()
        ini_path = tmp_path / "kepek" / ".picasa.ini"

        slider.setProperty("value", 0.3)
        qt_app.processEvents()
        assert not ini_path.exists(), "húzás közben nem szabadna ini-be írni"
        assert image.property("source").toString() != before_source

        slider.setProperty("pressed", True)
        slider.setProperty("pressed", False)
        qt_app.processEvents()
        ini_text = ini_path.read_text(encoding="utf-8")
        assert "filters=tilt=1,0.300000,0.000000;" in ini_text

    def test_tilt_tool_opens_with_saved_value_not_zero(
        self, qml_app, qt_app, tmp_path
    ):
        """#131: a döntés-csúszka a MENTETT tilt-értékről induljon, ne néma
        0-ról — különben az első érintés kinullázza a mentett döntést."""
        from PySide6.QtCore import Q_ARG, QMetaObject, Qt

        window, _, _ = qml_app
        ini_path = tmp_path / "kepek" / ".picasa.ini"
        ini_path.write_text(
            "[a.jpg]\nfilters=tilt=1,0.400000,0.000000;\n", encoding="utf-8"
        )
        self._open_viewer(window, qt_app)
        panel = window.findChild(QObject, "viewerEditorPanel")
        QMetaObject.invokeMethod(
            panel,
            "handleToolClick",
            Qt.ConnectionType.DirectConnection,
            Q_ARG("QVariant", "tilt"),
        )
        qt_app.processEvents()
        slider = window.findChild(QObject, "tiltSlider")
        assert slider is not None, "tiltSlider nem található"
        assert slider.property("value") == pytest.approx(0.4)

    def test_navigation_with_tilt_tool_active_preserves_next_photo_preview(
        self, qml_app, qt_app, tmp_path
    ):
        """#131: aktív döntés-eszköz melletti lapozás NEM nullázza a
        következő kép előnézetét — a csúszka a mentett tilt-értékére áll,
        a 0-ra állás nem vált ki previewTilt(0)-t."""
        window, _, _ = qml_app
        ini_path = tmp_path / "kepek" / ".picasa.ini"
        ini_path.write_text(
            "[a.jpg]\nfilters=tilt=1,0.400000,0.000000;\n"
            "[b.jpg]\nfilters=tilt=1,-0.200000,0.000000;\n",
            encoding="utf-8",
        )
        viewer = self._open_viewer(window, qt_app, index=0)
        panel = window.findChild(QObject, "viewerEditorPanel")
        panel.setProperty("tiltActive", True)
        qt_app.processEvents()
        slider = window.findChild(QObject, "tiltSlider")
        assert slider is not None, "tiltSlider nem található"

        viewer.setProperty("currentIndex", 1)
        qt_app.processEvents()

        # a csúszka a b.jpg mentett tilt-értékére állt, NEM 0-ra
        assert slider.property("value") == pytest.approx(-0.2)
        # a b.jpg mentett tilt-je az ini-ben érintetlen maradt
        ini_text = ini_path.read_text(encoding="utf-8")
        assert "filters=tilt=1,-0.200000,0.000000;" in ini_text

    def test_reopen_crop_tool_shows_uncropped_image_and_existing_selection(
        self, qml_app, qt_app, tmp_path
    ):
        """#71: a Vágás eszköz újranyitásakor a teljes (vágatlan) kép +
        a meglévő kijelölés látszik, a vágás folytatható marad."""
        from PySide6.QtCore import QMetaObject, QRectF, Qt

        window, _, engine = qml_app
        viewer = self._open_viewer(window, qt_app)
        panel = window.findChild(QObject, "viewerEditorPanel")
        panel.setProperty("cropActive", True)
        qt_app.processEvents()
        overlay = window.findChild(QObject, "cropOverlay")
        overlay.setProperty("cropRect", QRectF(0.25, 0.25, 0.5, 0.5))
        overlay.setProperty("hasSelection", True)
        QMetaObject.invokeMethod(
            overlay, "acceptCrop", Qt.ConnectionType.DirectConnection
        )
        qt_app.processEvents()
        # Enter-flow: elfogadás után a vágó-mód megmarad, de a kijelölés
        # üresre áll vissza a következő képre lépéskor
        assert panel.property("cropActive") is True
        assert overlay.property("hasSelection") is False

        # visszalépés az imént megvágott képre: a teljes kép + a mentett
        # kijelölés (nem a levágott eredmény) jelenjen meg
        viewer.setProperty("currentIndex", 0)
        qt_app.processEvents()
        edit = self._edit_controller(engine)
        assert edit.property("previewSource").startswith("image://editpreview/")
        assert overlay.property("hasSelection") is True
        crop_rect = overlay.property("cropRect")
        assert crop_rect.x() == pytest.approx(0.25, abs=1e-3)
        assert crop_rect.width() == pytest.approx(0.5, abs=1e-3)

    def test_crop_cancel_leaves_crop_mode(self, qml_app, qt_app):
        from PySide6.QtCore import QMetaObject, Qt

        window, _, _ = qml_app
        self._open_viewer(window, qt_app)
        panel = window.findChild(QObject, "viewerEditorPanel")
        panel.setProperty("cropActive", True)
        qt_app.processEvents()
        overlay = window.findChild(QObject, "cropOverlay")
        QMetaObject.invokeMethod(
            overlay, "cancelCrop", Qt.ConnectionType.DirectConnection
        )
        qt_app.processEvents()
        assert panel.property("cropActive") is False


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
