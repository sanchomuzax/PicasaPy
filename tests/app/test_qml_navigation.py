"""#77: kurzorgombos és egérgörgős navigáció — QML-funkcionális tesztek.

A nézet-komponensek (PhotoViewer, FolderPane) görgő- és léptető-függvényeit
a betöltött Main.qml-en át ellenőrizzük, kétmappás könyvtárral (a mappa-
léptetéshez legalább két mappa kell).
"""

import pytest
from PySide6.QtCore import Q_ARG, QMetaObject, QObject, Qt

from picasapy.index import open_index, sync_tree
from support.jpeg_factory import make_jpeg


@pytest.fixture(scope="module")
def qml_nav_app(qt_app, tmp_path_factory):
    """Teljes app offscreen, két mappával: (window, controller, engine).

    Modul-szintű fixture: a Main.qml-t EGYSZER töltjük be — a tesztenkénti
    újratöltés sok engine-t halmoz fel, ami az offscreen QQmlThread-del
    ritkán deadlockba fut (a teljes tesztkészletben reprodukálódott).
    """
    import picasapy.app.application as app_module
    from picasapy.app.controller import AppController
    from picasapy.app.edit_controller import EditController
    from picasapy.app.edit_preview import EditPreviewProvider
    from picasapy.app.thumbnail_provider import ThumbnailProvider
    from picasapy.thumbs import ThumbnailCache
    from PySide6.QtCore import QSettings
    from PySide6.QtQml import QQmlApplicationEngine

    tmp_path = tmp_path_factory.mktemp("navlib")
    lib = tmp_path / "kepek"
    (lib / "adag1").mkdir(parents=True)
    (lib / "adag2").mkdir()
    for i in range(3):
        make_jpeg(lib / "adag1" / f"a{i}.jpg")
    for i in range(2):
        make_jpeg(lib / "adag2" / f"b{i}.jpg")
    db = tmp_path / "index.db"
    with open_index(db) as conn:
        sync_tree(conn, lib)

    settings = QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat)
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
    engine.load(str(app_module._APP_DIR / "qml" / "Main.qml"))
    assert engine.rootObjects(), "Main.qml betöltése sikertelen"
    window = engine.rootObjects()[0]
    controller._reload()
    controller.selectFolder(controller.folders.folder_paths()[0])
    qt_app.processEvents()
    yield window, controller, engine
    engine.deleteLater()
    qt_app.processEvents()


def _invoke(qt_app, obj, name, *args):
    QMetaObject.invokeMethod(
        obj,
        name,
        Qt.ConnectionType.DirectConnection,
        *[Q_ARG("QVariant", a) for a in args],
    )
    qt_app.processEvents()


def _open_viewer(window, qt_app, index=0):
    window.setProperty("viewerOpen", True)
    viewer = window.findChild(QObject, "photoViewer")
    assert viewer is not None, "photoViewer nem található"
    viewer.setProperty("currentIndex", index)
    qt_app.processEvents()
    return viewer


class TestViewerWheelPaging:
    """A nagy nézőben a görgő lapozza a képeket (DoD: néző + görgő)."""

    def test_wheel_down_advances_wheel_up_goes_back(self, qml_nav_app, qt_app):
        window, _, _ = qml_nav_app
        viewer = _open_viewer(window, qt_app)
        _invoke(qt_app, viewer, "wheelStep", -120)  # görgő lefelé
        assert viewer.property("currentIndex") == 1
        _invoke(qt_app, viewer, "wheelStep", 120)   # görgő felfelé
        assert viewer.property("currentIndex") == 0

    def test_wheel_stops_at_ends(self, qml_nav_app, qt_app):
        window, _, _ = qml_nav_app
        viewer = _open_viewer(window, qt_app)
        _invoke(qt_app, viewer, "wheelStep", 120)
        assert viewer.property("currentIndex") == 0
        last = viewer.property("photoCount") - 1
        viewer.setProperty("currentIndex", last)
        qt_app.processEvents()
        _invoke(qt_app, viewer, "wheelStep", -120)
        assert viewer.property("currentIndex") == last

    def test_touchpad_deltas_accumulate_to_one_step(self, qml_nav_app, qt_app):
        # Touchpad: több kis delta összegyűlve ad EGY lépést — nem ugrál.
        window, _, _ = qml_nav_app
        viewer = _open_viewer(window, qt_app)
        _invoke(qt_app, viewer, "wheelStep", -40)
        _invoke(qt_app, viewer, "wheelStep", -40)
        assert viewer.property("currentIndex") == 0
        _invoke(qt_app, viewer, "wheelStep", -40)
        assert viewer.property("currentIndex") == 1


class TestGridCursorWiring:
    """Rács: kurzor/görgő bekötés a Main.qml-ben (DoD: fotórács)."""

    def test_move_selection_steps_and_selects(self, qml_nav_app, qt_app):
        window, controller, _ = qml_nav_app
        window.setProperty("viewerOpen", False)
        window.setProperty("selectedIndex", -1)
        window.setProperty("selectedIndexes", [])
        grid = window.findChild(QObject, "photoGrid")
        assert grid is not None, "photoGrid nem található"
        _invoke(qt_app, grid, "moveSelection", "right")
        assert window.property("selectedIndex") == 0  # üresből az elsőre
        _invoke(qt_app, grid, "moveSelection", "right")
        assert window.property("selectedIndex") == 1
        _invoke(qt_app, grid, "moveSelection", "left")
        assert window.property("selectedIndex") == 0

    def test_grid_wheel_steps_rows(self, qml_nav_app, qt_app):
        window, controller, _ = qml_nav_app
        window.setProperty("viewerOpen", False)
        window.setProperty("selectedIndex", 0)
        window.setProperty("selectedIndexes", [0])
        grid = window.findChild(QObject, "photoGrid")
        cols = grid.property("feedColumns")
        total = controller.photos.rowCount()
        expected = controller.photos.navigate(0, "down", cols)
        _invoke(qt_app, grid, "wheelStep", -120)
        assert window.property("selectedIndex") == expected
        _invoke(qt_app, grid, "wheelStep", 120)
        assert window.property("selectedIndex") == 0
        assert total >= 2  # az adat tényleg léptethető


class TestFolderPaneStepping:
    """Mappalista: kurzor/görgő a könyvtárelemek között (DoD: mappalista)."""

    @staticmethod
    def _pane_and_folders(window, controller):
        pane = window.findChild(QObject, "folderPane")
        assert pane is not None, "folderPane nem található"
        folders = list(controller.folders.folder_paths())
        assert len(folders) == 2
        return pane, folders

    def test_step_folder_moves_selection(self, qml_nav_app, qt_app):
        window, controller, _ = qml_nav_app
        pane, folders = self._pane_and_folders(window, controller)
        controller.selectFolder(folders[0])
        qt_app.processEvents()
        _invoke(qt_app, pane, "stepFolder", 1)
        assert controller.currentFolder == folders[1]
        _invoke(qt_app, pane, "stepFolder", -1)
        assert controller.currentFolder == folders[0]

    def test_step_folder_clamps_at_edges(self, qml_nav_app, qt_app):
        window, controller, _ = qml_nav_app
        pane, folders = self._pane_and_folders(window, controller)
        controller.selectFolder(folders[0])
        qt_app.processEvents()
        _invoke(qt_app, pane, "stepFolder", -1)
        assert controller.currentFolder == folders[0]
        controller.selectFolder(folders[-1])
        qt_app.processEvents()
        _invoke(qt_app, pane, "stepFolder", 1)
        assert controller.currentFolder == folders[-1]

    def test_wheel_steps_between_folders(self, qml_nav_app, qt_app):
        # Görgő lefelé → következő mappa; kis (touchpad) delták gyűlnek.
        window, controller, _ = qml_nav_app
        pane, folders = self._pane_and_folders(window, controller)
        controller.selectFolder(folders[0])
        qt_app.processEvents()
        _invoke(qt_app, pane, "wheelStep", -60)
        assert controller.currentFolder == folders[0]
        _invoke(qt_app, pane, "wheelStep", -60)
        assert controller.currentFolder == folders[1]
        _invoke(qt_app, pane, "wheelStep", 120)
        assert controller.currentFolder == folders[0]
