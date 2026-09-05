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


def _wait_for_row_bounds(qt_app, grid, row, timeout_ms=2000):
    """#135: determinisztikus szinkronpont a `rowBounds`-ra épülő
    tesztekhez. A #142-es virtualizált cella-ablak a `scrollToRow` utáni
    layoutot 1-2 eseményciklus késéssel köti be (delegate-inkubáció) — ez
    lassabb (pl. Windows-os CI) gépen az assert elé csúszhat, és a teszt
    flaky-vé válik. `forceLayout` + rövid valós várakozás ismételt
    lefuttatásával megvárjuk, amíg a célsor geometriája két egymást követő
    lekérdezés között már nem változik (azaz a kötés lezárult)."""
    from PySide6.QtCore import QEventLoop, QMetaObject, QTimer

    prev = None
    steps = max(1, timeout_ms // 20)
    for _ in range(steps):
        QMetaObject.invokeMethod(grid, "forceLayout")
        qt_app.processEvents()
        b = _ret(qt_app, grid, "rowBounds", row)
        if b is not None and b == prev:
            return b
        prev = b
        pause = QEventLoop()
        QTimer.singleShot(20, pause.quit)
        pause.exec()
    return prev


def _settle_content_y_at(qt_app, grid, target=0.0, timeout_ms=2000):
    """#261: a KIINDULÓ görgetés-pozíció determinisztikus beállítása.

    A `_wait_for_scroll_settled` a lépés UTÁNI állapotot várja ki, de a
    kiindulást is meg kell szilárdítani: a rács a `thumbSize` váltása utáni
    újrarendezéskor (delegate-inkubáció, mentett pozíció visszaállítása)
    egy-két eseményciklussal később felülírhatja a frissen beírt
    `contentY`-t. A Windows-CI ezért látott 898-at ott, ahol a teszt 0-t
    állított be. Itt addig ismételjük a beállítást, amíg az érték két
    egymást követő lekérdezésben is a célértéken marad.
    """
    from PySide6.QtCore import QEventLoop, QMetaObject, QTimer

    steps = max(1, timeout_ms // 20)
    stable = 0
    for _ in range(steps):
        if grid.property("contentY") != target:
            grid.setProperty("contentY", target)
            stable = 0
        else:
            stable += 1
            if stable >= 2:
                return True
        QMetaObject.invokeMethod(grid, "forceLayout")
        qt_app.processEvents()
        pause = QEventLoop()
        QTimer.singleShot(20, pause.quit)
        pause.exec()
    return grid.property("contentY") == target


def _wait_for_scroll_settled(qt_app, grid, timeout_ms=2000):
    """#261: determinisztikus szinkronpont a `contentY`-ra épülő
    tesztekhez — a `_wait_for_row_bounds` párja. A `moveSelection` utáni
    görgetés (ensureVisible) lassabb gépen (Windows-CI) 1-2 eseményciklus
    késéssel ér célba; addig várunk, amíg a `contentY` két egymást követő
    lekérdezés között már nem változik."""
    from PySide6.QtCore import QEventLoop, QMetaObject, QTimer

    prev = None
    steps = max(1, timeout_ms // 20)
    for _ in range(steps):
        QMetaObject.invokeMethod(grid, "forceLayout")
        qt_app.processEvents()
        y = grid.property("contentY")
        if prev is not None and y == prev:
            return y
        prev = y
        pause = QEventLoop()
        QTimer.singleShot(20, pause.quit)
        pause.exec()
    # #2408: időtúllépéskor NEM adjuk vissza némán az utolsó értéket. A
    # korábbi `return prev` alak azt jelentette, hogy a hívó nem tudja
    # megkülönböztetni a „beállt" és a „lejárt" esetet — a bukás így egy
    # KÉSŐBBI állításon jelentkezett, félrevezetően. A segítő maga áll meg,
    # így mind az öt csupasz hívási helye biztonságos marad.
    raise AssertionError(
        f"#2408: a görgetés {timeout_ms} ms alatt sem állt be "
        f"(utolsó contentY: {prev})"
    )


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
        # A Flow-relayout több eseményciklust igényelhet, és lassú (CI-)
        # gépen puszta processEvents-pörgetéssel nem ér oda — minden körben
        # kényszerített layout + rövid VALÓS várakozás kell.
        from PySide6.QtCore import QEventLoop, QMetaObject, QTimer

        for _ in range(100):
            QMetaObject.invokeMethod(grid, "forceLayout")
            qt_app.processEvents()
            if grid.property("contentHeight") > grid.property("height"):
                break
            pause = QEventLoop()
            QTimer.singleShot(10, pause.quit)
            pause.exec()
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
            # #261: a kiindulás is szinkronpontot kap — enélkül a rács
            # újrarendezése felülírhatja a beírt 0-t (Windows-CI)
            assert _settle_content_y_at(qt_app, grid, 0)
            # #261: a virtualizált cella-ablak kötése lassabb gépen
            # (Windows-CI) késik — a lépés ELŐTT megvárjuk a célsor
            # geometriáját, különben az ensureVisible vakon görgetne
            assert _wait_for_row_bounds(qt_app, grid, 0) is not None
            _invoke(qt_app, grid, "moveSelection", "up")
            _wait_for_scroll_settled(qt_app, grid)
            assert window.property("selectedIndex") == 0
            # #423: a mappa-fejléc magassága a tipográfiával változik (a
            # Georgia 20 pt-os cím 8 px-szel magasabb fejlécet ad), ezért a
            # korábbi fix `contentY == 0` elvárás elavult — az őr VALÓDI
            # állítása az, hogy a MÁR LÁTSZÓ célra nem görget tovább. Ezt
            # elrendezés-függetlenül az ismételt lépés méri: a legfelső sor
            # elérése után egy újabb „fel" egyáltalán nem mozdíthat.
            stabil = grid.property("contentY")
            _invoke(qt_app, grid, "moveSelection", "up")
            _wait_for_scroll_settled(qt_app, grid)
            assert window.property("selectedIndex") == 0
            assert grid.property("contentY") == stabil
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
            b = _wait_for_row_bounds(qt_app, grid, target)
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
            # #261: minden lépés után bevárjuk a görgetés lecsengését —
            # e nélkül a következő lépés menet közbeni contentY-ból számol,
            # és lassabb gépen (Windows-CI) pár pixellel mellémegy
            _invoke(qt_app, grid, "moveSelection", "down")
            _wait_for_scroll_settled(qt_app, grid)
            _invoke(qt_app, grid, "moveSelection", "down")
            _wait_for_scroll_settled(qt_app, grid)
            _invoke(qt_app, grid, "moveSelection", "up")
            _wait_for_scroll_settled(qt_app, grid)
            target = window.property("selectedIndex")
            b = _wait_for_row_bounds(qt_app, grid, target)
            assert b is not None
            # felfelé lépve a sor teteje igazodik a látótér tetejéhez
            assert abs(b["top"] - grid.property("contentY")) <= 1
        finally:
            window.setProperty("thumbSize", old_size)
            qt_app.processEvents()


class TestShiftArrowSelection:
    """#96: Shift+nyíl a mappán belül bővíti a kijelölést.

    ⚠️ #1219: a horgony a HÁROMKÉPES mappa (`adag1`) elején áll, nem a
    feed 0. során. A feed sorrendjében az `adag2` (2 kép) van elöl, így a
    0. sorról induló bővítés a 2. lépésben MAPPAHATÁRT lépett át — a
    tesztek ezt a hibás viselkedést rögzítették. A határon való megállást
    a `test_kijeloles_mappahatar_1219.py` méri; ezek itt a mappán BELÜLI
    bővítés őrei maradnak.

    ⚠️ #892/#1222: a Shift+nyíl NEM tartományt jelöl, hanem EGYESÉVEL
    bővít, és a léptetés töve is lép (`0x00717eb0`; a Shiftes ág a
    `0x0071805c`-nél kihagyja a leszedést). A „visszafelé zsugorít"
    tesztet ezért váltotta fel a megőrző párja. A teljes, irányváltásos
    viselkedést VALÓDI billentyűeseménnyel a
    `qml_functional/test_shift_nyil_bovites_892_1222.py` méri."""

    #: a második csoport (`adag1`, 3 kép) első sora a feedben
    KEZDET = 2

    @classmethod
    def _reset(cls, window, qt_app):
        window.setProperty("viewerOpen", False)
        window.setProperty("selectedIndex", cls.KEZDET)
        window.setProperty("selectedIndexes", [cls.KEZDET])
        grid = window.findChild(QObject, "photoGrid")
        assert grid is not None
        grid.setProperty("selectionAnchor", cls.KEZDET)
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
        assert self._selection(window) == [self.KEZDET, self.KEZDET + 1]
        assert window.property("selectedIndex") == self.KEZDET + 1
        _invoke(qt_app, grid, "extendSelection", "right")
        assert self._selection(window) == [
            self.KEZDET, self.KEZDET + 1, self.KEZDET + 2
        ]

    def test_extend_back_does_not_shrink(self, qml_nav_app, qt_app):
        """#892/#1222: az irányváltás nem vesz vissza — a kurzor csak
        visszasétál a már kijelölteken (a hármas mappában idáig ér)."""
        window, _, _ = qml_nav_app
        grid = self._reset(window, qt_app)
        _invoke(qt_app, grid, "extendSelection", "right")
        _invoke(qt_app, grid, "extendSelection", "right")
        _invoke(qt_app, grid, "extendSelection", "left")
        assert self._selection(window) == [
            self.KEZDET, self.KEZDET + 1, self.KEZDET + 2
        ]
        assert window.property("selectedIndex") == self.KEZDET + 1

    def test_plain_move_resets_to_single(self, qml_nav_app, qt_app):
        window, _, _ = qml_nav_app
        grid = self._reset(window, qt_app)
        _invoke(qt_app, grid, "extendSelection", "right")
        _invoke(qt_app, grid, "moveSelection", "right")
        assert self._selection(window) == [self.KEZDET + 2]
        assert grid.property("selectionAnchor") == self.KEZDET + 2


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
