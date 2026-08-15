"""QML-funkcionális tesztek: rejtett képek (#17).

Elrejtés a kijelölésre (menü/kontextusmenü útja: toggleHiddenSelection),
a rács alapból nem mutatja a rejtettet, a Nézet → Rejtett képek kapcsolóval
félig áttetszően igen (ThumbDelegate.isHidden → thumbFrame.opacity), és a
rács görgetése elrejtés/megjelenítés után sem ugrik el (horgony-visszaállás).
"""

import pytest
from PySide6.QtCore import (
    QEventLoop,
    QMetaObject,
    QObject,
    Qt,
    QTimer,
    QUrl,
)
from PySide6.QtQml import QQmlComponent, QQmlEngine

_KEEPALIVE = []


def _settle(qt_app, rounds=8):
    """Eseményciklus-pörgetés rövid valós várakozásokkal — a Qt.callLater
    és a Flow-relayout több körben ér célba (a nav-tesztek mintája)."""
    for _ in range(rounds):
        qt_app.processEvents()
        pause = QEventLoop()
        QTimer.singleShot(10, pause.quit)
        pause.exec()


class TestHiddenInMain:
    def test_menu_item_enabled_and_checkable(self, qml_app):
        window, controller, lib, engine = qml_app
        item = window.findChild(QObject, "menuViewHidden")
        assert item is not None
        assert item.property("enabled") is True
        assert item.property("checkable") is True
        assert item.property("checked") is False

    def test_hide_selection_removes_from_grid_and_clears_selection(
        self, qml_app, qt_app
    ):
        window, controller, lib, engine = qml_app
        window.setProperty("selectedIndexes", [0])
        window.setProperty("selectedIndex", 0)
        QMetaObject.invokeMethod(
            window, "toggleHiddenSelection", Qt.ConnectionType.DirectConnection
        )
        qt_app.processEvents()
        assert controller.photos.rowCount() == 1
        selected = window.property("selectedIndexes")
        if hasattr(selected, "toVariant"):  # a QML var lista QJSValue-ként jön
            selected = selected.toVariant()
        assert list(selected or []) == []
        assert window.property("selectedIndex") == -1
        ini_text = (lib / ".picasa.ini").read_text(encoding="utf-8")
        assert "hidden=yes" in ini_text

    def test_show_hidden_reveals_with_hidden_flag(self, qml_app, qt_app):
        window, controller, lib, engine = qml_app
        window.setProperty("selectedIndexes", [0])
        window.setProperty("selectedIndex", 0)
        QMetaObject.invokeMethod(
            window, "toggleHiddenSelection", Qt.ConnectionType.DirectConnection
        )
        controller.setShowHidden(True)
        qt_app.processEvents()
        assert controller.photos.rowCount() == 2
        hidden_flags = [
            controller.photos.itemAt(i)["hidden"] for i in range(2)
        ]
        assert hidden_flags.count(True) == 1

    def test_context_menu_has_hide_item(self, qml_app):
        """#422: az eredeti nem pipát tesz a tételre, hanem a FELIRATOT
        cseréli (Elrejtés ↔ Megjelenítés, ID_PICTURE_HIDE/UNHIDE)."""
        window, controller, lib, engine = qml_app
        item = window.findChild(QObject, "contextMenuHide")
        assert item is not None
        assert item.property("checkable") is False
        assert item.property("text")


class TestScrollAnchorOnHide:
    """#17-visszajelzés: elrejtésnél/megjelenítésnél a rács nem ugorhat el —
    a viewport a korábban látott mappacsoporton marad."""

    @pytest.fixture
    def scroll_app(self, qt_app, tmp_path):
        """Több mappás, görgethető könyvtár a Main.qml-lel.

        #718: a Main.qml időközben (a `qml_app`/conftest.py mintája szerint)
        további context property-ket vár (discoveryController,
        timelineController, folderTreeController, dedupController,
        importSourceController, facesHelper, faceScanController,
        confirmSettings, startupStatus) — ez a helyi fixture ezekkel
        korábban NEM lett szinkronban tartva, ezért a kiterjesztett
        QML-szkripthiba-őr `ReferenceError`-t fogott a hiányzó globálisokra
        (a hiba korábban is megvolt, csak néma maradt, ld. a #718 jegy)."""
        import picasapy.app.application as app_module
        from picasapy.app.controller import AppController
        from picasapy.app.dedup_controller import DedupController
        from picasapy.app.discovery_controller import DiscoveryController
        from picasapy.app.drop_import_controller import DropImportController
        from picasapy.app.edit_controller import EditController
        from picasapy.app.edit_preview import EditPreviewProvider
        from picasapy.app.effect_thumbnails import EffectThumbnailProvider
        from picasapy.app.face_scan_controller import FaceScanController
        from picasapy.app.faces_helper import FacesHelper
        from picasapy.app.fileops_controller import FileOpsController
        from picasapy.app.folder_tree_controller import FolderTreeController
        from picasapy.app.import_source_controller import ImportSourceController
        from picasapy.app.thumbnail_provider import ThumbnailProvider
        from picasapy.app.timeline_controller import TimelineController
        from picasapy.index import open_index, sync_tree
        from picasapy.thumbs import ThumbnailCache
        from picasapy.version import version_string
        from PySide6.QtCore import QSettings
        from PySide6.QtQml import QQmlApplicationEngine

        from support.jpeg_factory import make_jpeg

        lib = tmp_path / "kepek"
        for folder in ("adag1", "adag2", "adag3"):
            (lib / folder).mkdir(parents=True)
            for i in range(6):
                make_jpeg(lib / folder / f"{folder}_{i}.jpg")
        db = tmp_path / "index.db"
        with open_index(db) as conn:
            sync_tree(conn, lib)
        settings = QSettings(
            str(tmp_path / "settings.ini"), QSettings.Format.IniFormat
        )
        provider = ThumbnailProvider(
            ThumbnailCache(tmp_path / "thumbs", size=32)
        )
        controller = AppController(db, (str(lib),), provider, settings=settings)
        # #367: az általános ConfirmDialog "Ne kérdezze újra" tára — ugyanaz
        # az elszigetelt settings, mint a controlleré
        from picasapy.app.confirm_settings_bridge import ConfirmSettingsBridge

        confirm_settings = ConfirmSettingsBridge(settings=settings)
        edit_preview = EditPreviewProvider()
        edit_controller = EditController(edit_preview)
        effect_thumb_provider = EffectThumbnailProvider(provider.photo_record)
        fileops_controller = FileOpsController()
        app_module.wire_fileops(fileops_controller, controller)
        discovery_controller = DiscoveryController(
            add_folder=controller.addWatchedFolder
        )
        drop_import_controller = DropImportController(
            add_folder=controller.addWatchedFolder
        )
        folder_tree_controller = FolderTreeController()
        dedup_controller = DedupController(db, provider)
        import_source_controller = ImportSourceController(
            provider,
            add_folder=controller.addWatchedFolder,
            index_path=db,
            settings=settings,
        )
        faces_helper = FacesHelper()
        face_scan_controller = FaceScanController(db, faces_helper=faces_helper)
        timeline_controller = TimelineController(db, provider)
        controller.syncFinished.connect(timeline_controller.reload)
        engine = QQmlApplicationEngine()
        engine.addImageProvider("thumbs", provider)
        engine.addImageProvider("editpreview", edit_preview)
        engine.addImageProvider("effectthumb", effect_thumb_provider)
        engine.addImportPath(str(app_module._APP_DIR / "qml"))
        engine.rootContext().setContextProperty("controller", controller)
        engine.rootContext().setContextProperty("editController", edit_controller)
        engine.rootContext().setContextProperty(
            "fileOpsController", fileops_controller
        )
        engine.rootContext().setContextProperty(
            "discoveryController", discovery_controller
        )
        engine.rootContext().setContextProperty(
            "dropImportController", drop_import_controller
        )
        engine.rootContext().setContextProperty(
            "folderTreeController", folder_tree_controller
        )
        engine.rootContext().setContextProperty("dedupController", dedup_controller)
        engine.rootContext().setContextProperty(
            "importSourceController", import_source_controller
        )
        engine.rootContext().setContextProperty("facesHelper", faces_helper)
        engine.rootContext().setContextProperty(
            "faceScanController", face_scan_controller
        )
        engine.rootContext().setContextProperty(
            "timelineController", timeline_controller
        )
        engine.rootContext().setContextProperty("appVersion", version_string())
        engine.rootContext().setContextProperty("confirmSettings", confirm_settings)
        # #189: a splash-híd — a funkcionális tesztek kész (ready) állapotból
        # indulnak, hogy a splash-overlay ne takarjon semmit
        from picasapy.app.startup_status import StartupStatus

        startup_status = StartupStatus()
        startup_status.finish()
        engine.rootContext().setContextProperty("startupStatus", startup_status)
        engine.load(str(app_module._APP_DIR / "qml" / "Main.qml"))
        assert engine.rootObjects(), "Main.qml betöltése sikertelen"
        window = engine.rootObjects()[0]
        controller._reload()
        controller.selectFolder(controller.folders.folder_paths()[0])
        qt_app.processEvents()
        yield window, controller, engine
        engine.deleteLater()
        qt_app.processEvents()
        # #438: minden nyilvántartott daemon-szál bevárása, AMÍG a
        # controllerek még élnek — a #430 SIGSEGV-osztály elkerülése (ld.
        # picasapy.app.worker_thread.BackgroundWorkerMixin).
        for bg_controller in (
            controller,
            discovery_controller,
            dedup_controller,
            folder_tree_controller,
            import_source_controller,
        ):
            assert bg_controller.waitForBackgroundWorkers(30.0), (
                "háttérszál nem állt le a scroll_app teardownban (#430/#438)"
            )

    def _scrollable_grid(self, window, qt_app):
        grid = window.findChild(QObject, "photoGrid")
        assert grid is not None
        window.setProperty("thumbSize", 512)
        for _ in range(100):
            QMetaObject.invokeMethod(grid, "forceLayout")
            _settle(qt_app, rounds=1)
            if grid.property("contentHeight") > grid.property("height"):
                break
        assert grid.property("contentHeight") > grid.property("height")
        return grid

    @staticmethod
    def _assert_viewport_at_group_top(qt_app, grid, path):
        """A viewport a `path` mappacsoport tetején áll (horgony-eltolás 0).

        Az abszolút contentY összevetése félrevezető lenne: ha a horgony-
        mappa FELETTI tartalom nő/fogy (pl. rejtett kép megjelenítése egy
        korábbi mappában), a contentY jogosan tolódik — a lényeg, hogy a
        képernyőn ugyanaz a csoport-tető maradjon."""
        item = None
        for child in grid.property("contentItem").childItems():
            model_data = child.property("modelData")
            if hasattr(model_data, "toVariant"):
                model_data = model_data.toVariant()
            if isinstance(model_data, dict) and model_data.get("path") == path:
                item = child
                break
        assert item is not None, "a horgony-csoport delegate nincs példányosítva"
        delta = abs(item.property("y") - grid.property("contentY"))
        assert delta <= 1, f"a rács elugrott a csoport tetejéről: {delta} px"

    def test_hide_keeps_viewport_on_same_group(self, scroll_app, qt_app):
        window, controller, engine = scroll_app
        grid = self._scrollable_grid(window, qt_app)
        paths = controller.folders.folder_paths()
        from PySide6.QtCore import Q_ARG

        # görgetés a 2. mappa csoportjához
        QMetaObject.invokeMethod(
            grid, "scrollToGroup", Qt.ConnectionType.DirectConnection,
            Q_ARG("QVariant", paths[1]),
        )
        _settle(qt_app)
        assert grid.property("anchorPath") == paths[1]
        assert grid.property("contentY") > 0

        # a 2. mappa egy képének elrejtése
        row = next(
            i for i, p in enumerate(controller.photos.photos)
            if p.folder_path == paths[1]
        )
        controller.toggleHiddenRows([row])
        _settle(qt_app)

        assert grid.property("anchorPath") == paths[1]
        self._assert_viewport_at_group_top(qt_app, grid, paths[1])

    def test_show_hidden_toggle_keeps_viewport(self, scroll_app, qt_app):
        window, controller, engine = scroll_app
        # előbb rejtsünk el egy képet az 1. mappában, hogy a kapcsoló
        # tényleg átrendezze a horgony-csoport FELETTI tartalmat is
        controller.toggleHiddenRows([0])
        grid = self._scrollable_grid(window, qt_app)
        paths = controller.folders.folder_paths()
        from PySide6.QtCore import Q_ARG

        QMetaObject.invokeMethod(
            grid, "scrollToGroup", Qt.ConnectionType.DirectConnection,
            Q_ARG("QVariant", paths[2]),
        )
        _settle(qt_app)
        controller.setShowHidden(True)
        _settle(qt_app)
        assert grid.property("anchorPath") == paths[2]
        self._assert_viewport_at_group_top(qt_app, grid, paths[2])


class TestThumbDelegateHiddenDimming:
    @pytest.fixture
    def qml_engine(self, qt_app):
        import picasapy.app.application as app_module

        engine = QQmlEngine()
        engine.addImportPath(str(app_module._APP_DIR / "qml"))
        yield engine
        engine.deleteLater()

    def _make(self, engine, is_hidden):
        component = QQmlComponent(engine)
        component.setData(
            (
                "import QtQuick\nimport PicasaPy 1.0\n"
                "ThumbDelegate { index: 0; name: \"a\"; thumbUrl: \"\";"
                " star: false; caption: \"\"; isVideo: false;"
                " keywords: \"\"; resolution: \"\"; isHidden: %s }\n"
                % ("true" if is_hidden else "false")
            ).encode("utf-8"),
            QUrl(),
        )
        obj = component.create()
        assert obj is not None, [e.toString() for e in component.errors()]
        QQmlEngine.setObjectOwnership(
            obj, QQmlEngine.ObjectOwnership.CppOwnership
        )
        _KEEPALIVE.extend([component, obj])
        return obj

    def test_hidden_thumb_semi_transparent(self, qml_engine, qt_app):
        cell = self._make(qml_engine, is_hidden=True)
        qt_app.processEvents()
        frame = cell.findChild(QObject, "thumbFrame")
        assert frame.property("opacity") < 1

    def test_visible_thumb_fully_opaque(self, qml_engine, qt_app):
        cell = self._make(qml_engine, is_hidden=False)
        qt_app.processEvents()
        frame = cell.findChild(QObject, "thumbFrame")
        assert frame.property("opacity") == 1
