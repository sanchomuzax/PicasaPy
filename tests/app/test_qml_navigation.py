"""#77: kurzorgombos és egérgörgős navigáció — QML-funkcionális tesztek.

A nézet-komponensek (PhotoViewer, FolderPane) görgő- és léptető-függvényeit
a betöltött Main.qml-en át ellenőrizzük, kétmappás könyvtárral (a mappa-
léptetéshez legalább két mappa kell).
"""

import pytest
from PySide6.QtCore import Q_ARG, Q_RETURN_ARG, QMetaObject, QObject, Qt

from picasapy.index import open_index, sync_tree
from picasapy.version import version_string
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
    engine.rootContext().setContextProperty("appVersion", version_string())
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


def _ret(qt_app, obj, name, *args):
    result = QMetaObject.invokeMethod(
        obj,
        name,
        Qt.ConnectionType.DirectConnection,
        Q_RETURN_ARG("QVariant"),
        *[Q_ARG("QVariant", a) for a in args],
    )
    qt_app.processEvents()
    if hasattr(result, "toVariant"):
        result = result.toVariant()
    return result


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


class TestGridWheelScrollsPage:
    """#89: a feed-rácson a görgő a LAPOT görgeti, nem a kijelölést lépteti.

    A #77-es rácssor-léptető görgő-viselkedést váltja: görgetéskor a
    contentY mozog (mint egy dokumentumban), a selectedIndex változatlan;
    a rácssor-léptetés kizárólag a nyilak (moveSelection) dolga marad.
    """

    @staticmethod
    def _scrollable_grid(window, qt_app):
        """Nagy bélyegméretet állít, hogy a feed ténylegesen görgethető
        legyen az offscreen ablakban; visszaállítandó értéket ad vissza."""
        window.setProperty("viewerOpen", False)
        grid = window.findChild(QObject, "photoGrid")
        assert grid is not None, "photoGrid nem található"
        old_size = window.property("thumbSize")
        window.setProperty("thumbSize", 512)
        # a Flow-relayout több eseményciklust is igényelhet
        for _ in range(50):
            qt_app.processEvents()
            if grid.property("contentHeight") > grid.property("height"):
                break
        assert grid.property("contentHeight") > grid.property("height"), (
            "a fixture-nek görgethető tartalmat kell adnia"
        )
        return grid, old_size

    def test_wheel_scrolls_content_selection_stays(self, qml_nav_app, qt_app):
        window, _, _ = qml_nav_app
        window.setProperty("selectedIndex", 0)
        window.setProperty("selectedIndexes", [0])
        grid, old_size = self._scrollable_grid(window, qt_app)
        try:
            grid.setProperty("contentY", 0)
            qt_app.processEvents()
            _invoke(qt_app, grid, "wheelStep", -120)  # görgő lefelé
            assert grid.property("contentY") > 0, "a lapnak görgetődnie kell"
            assert window.property("selectedIndex") == 0, (
                "a kijelölés görgetéskor nem mozdulhat"
            )
            scrolled = grid.property("contentY")
            _invoke(qt_app, grid, "wheelStep", 120)   # görgő felfelé
            assert grid.property("contentY") < scrolled
            assert window.property("selectedIndex") == 0
        finally:
            window.setProperty("thumbSize", old_size)
            qt_app.processEvents()

    def test_wheel_clamps_at_top(self, qml_nav_app, qt_app):
        window, _, _ = qml_nav_app
        grid, old_size = self._scrollable_grid(window, qt_app)
        try:
            grid.setProperty("contentY", 0)
            qt_app.processEvents()
            _invoke(qt_app, grid, "wheelStep", 120)   # felfelé a tetején
            assert grid.property("contentY") == 0
        finally:
            window.setProperty("thumbSize", old_size)
            qt_app.processEvents()

    def test_arrows_start_from_selected_after_scroll(self, qml_nav_app, qt_app):
        # Görgetés után a nyíl a KIJELÖLT képtől lép (nem a látott
        # területtől), és a nézet visszaugrik hozzá (scrollToRow).
        window, controller, _ = qml_nav_app
        window.setProperty("selectedIndex", 0)
        window.setProperty("selectedIndexes", [0])
        grid, old_size = self._scrollable_grid(window, qt_app)
        try:
            for _ in range(4):
                _invoke(qt_app, grid, "wheelStep", -120)
            assert window.property("selectedIndex") == 0
            cols = grid.property("feedColumns")
            expected = controller.photos.navigate(0, "down", cols)
            _invoke(qt_app, grid, "moveSelection", "down")
            assert window.property("selectedIndex") == expected
        finally:
            window.setProperty("thumbSize", old_size)
            qt_app.processEvents()


class TestWheelEndStop:
    """#95: a görgő az utolsó képsornál megáll, üres lapra nem fut."""

    def test_wheel_stops_at_last_row(self, qml_nav_app, qt_app):
        window, _, _ = qml_nav_app
        window.setProperty("selectedIndex", 0)
        window.setProperty("selectedIndexes", [0])
        grid, old_size = TestGridWheelScrollsPage._scrollable_grid(
            window, qt_app)
        try:
            grid.setProperty("contentY", 0)
            qt_app.processEvents()
            for _ in range(40):  # bőven a tartalom-végen túl
                _invoke(qt_app, grid, "wheelStep", -120)
            gap = _ret(qt_app, grid, "feedEndGap")
            assert gap is not None, "az utolsó csoport nem látszik (üres lap)"
            height = grid.property("height")
            assert 0 < gap <= height + 1, (
                f"az utolsó csoport alja a látótérben kell maradjon (gap={gap})"
            )
            assert window.property("selectedIndex") == 0
            end_y = grid.property("contentY")
            _invoke(qt_app, grid, "wheelStep", 120)  # onnan vissza is lehet
            assert grid.property("contentY") < end_y
        finally:
            window.setProperty("thumbSize", old_size)
            qt_app.processEvents()


class TestArrowMinimalScroll:
    """#96: a nyíl-navigáció csak a szükséges mértékben görget."""

    def test_no_scroll_when_target_visible(self, qml_nav_app, qt_app):
        window, _, _ = qml_nav_app
        window.setProperty("selectedIndex", 1)
        window.setProperty("selectedIndexes", [1])
        grid, old_size = TestGridWheelScrollsPage._scrollable_grid(
            window, qt_app)
        try:
            grid.setProperty("selectionAnchor", 1)
            grid.setProperty("contentY", 0)
            qt_app.processEvents()
            _invoke(qt_app, grid, "moveSelection", "up")
            assert window.property("selectedIndex") == 0
            assert grid.property("contentY") == 0  # látszott, nem mozdult
        finally:
            window.setProperty("thumbSize", old_size)
            qt_app.processEvents()

    def test_down_scrolls_just_enough(self, qml_nav_app, qt_app):
        window, _, _ = qml_nav_app
        window.setProperty("selectedIndex", 0)
        window.setProperty("selectedIndexes", [0])
        grid, old_size = TestGridWheelScrollsPage._scrollable_grid(
            window, qt_app)
        try:
            grid.setProperty("selectionAnchor", 0)
            grid.setProperty("contentY", 0)
            qt_app.processEvents()
            _invoke(qt_app, grid, "moveSelection", "down")
            target = window.property("selectedIndex")
            assert target > 0
            b = _ret(qt_app, grid, "rowBounds", target)
            assert b is not None
            content_y = grid.property("contentY")
            height = grid.property("height")
            # a cél-sor alja pont belóg: pontosan annyi görgetés, amennyi kell
            assert abs(b["bottom"] - (content_y + height)) <= 1
        finally:
            window.setProperty("thumbSize", old_size)
            qt_app.processEvents()

    def test_up_scrolls_back_minimally(self, qml_nav_app, qt_app):
        window, _, _ = qml_nav_app
        window.setProperty("selectedIndex", 0)
        window.setProperty("selectedIndexes", [0])
        grid, old_size = TestGridWheelScrollsPage._scrollable_grid(
            window, qt_app)
        try:
            grid.setProperty("selectionAnchor", 0)
            grid.setProperty("contentY", 0)
            qt_app.processEvents()
            _invoke(qt_app, grid, "moveSelection", "down")
            _invoke(qt_app, grid, "moveSelection", "down")
            _invoke(qt_app, grid, "moveSelection", "up")
            target = window.property("selectedIndex")
            b = _ret(qt_app, grid, "rowBounds", target)
            assert b is not None
            # felfelé lépve a sor teteje igazodik a látótér tetejéhez
            assert abs(b["top"] - grid.property("contentY")) <= 1
        finally:
            window.setProperty("thumbSize", old_size)
            qt_app.processEvents()


class TestShiftArrowSelection:
    """#96: Shift+nyíl a horgonytól tartományt jelöl ki / von vissza."""

    @staticmethod
    def _reset(window, qt_app):
        window.setProperty("viewerOpen", False)
        window.setProperty("selectedIndex", 0)
        window.setProperty("selectedIndexes", [0])
        grid = window.findChild(QObject, "photoGrid")
        assert grid is not None
        grid.setProperty("selectionAnchor", 0)
        qt_app.processEvents()
        return grid

    @staticmethod
    def _selection(window):
        raw = window.property("selectedIndexes")
        if hasattr(raw, "toVariant"):
            raw = raw.toVariant()
        return sorted(int(i) for i in raw)

    def test_extend_right_grows_range(self, qml_nav_app, qt_app):
        window, _, _ = qml_nav_app
        grid = self._reset(window, qt_app)
        _invoke(qt_app, grid, "extendSelection", "right")
        assert self._selection(window) == [0, 1]
        assert window.property("selectedIndex") == 1
        _invoke(qt_app, grid, "extendSelection", "right")
        assert self._selection(window) == [0, 1, 2]

    def test_extend_back_shrinks_range(self, qml_nav_app, qt_app):
        window, _, _ = qml_nav_app
        grid = self._reset(window, qt_app)
        _invoke(qt_app, grid, "extendSelection", "right")
        _invoke(qt_app, grid, "extendSelection", "right")
        _invoke(qt_app, grid, "extendSelection", "left")
        assert self._selection(window) == [0, 1]

    def test_plain_move_resets_to_single(self, qml_nav_app, qt_app):
        window, _, _ = qml_nav_app
        grid = self._reset(window, qt_app)
        _invoke(qt_app, grid, "extendSelection", "right")
        _invoke(qt_app, grid, "moveSelection", "right")
        assert self._selection(window) == [2]
        assert grid.property("selectionAnchor") == 2


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
