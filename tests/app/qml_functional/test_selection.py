"""QML-funkcionális tesztek: kijelölés — csillag, több-kijelölés,
kijelölés-stabilitás háttér-szinkron után, lasszó (#155: a korábbi
`test_qml_functional.py` egyik szelete, processzenkénti izolációhoz)."""

from PySide6.QtCore import QObject

from support.qt_wait import wait_for_photo_op

from picasapy.index import open_index, sync_tree
from support.jpeg_factory import make_jpeg


def _do_photo_op(controller, qt_app, action) -> None:
    """A csillag/felirat/forgatás háttérszálon fut — a közös segéd megvárja
    a `photoOpFinished` jelzést, és ELBUKIK, ha nem jön meg (#475)."""
    wait_for_photo_op(controller, action, qt_app=qt_app)


class TestTrayStar:
    def test_star_button_reflects_selection_state(self, qml_app, qt_app):
        window, controller, _ = qml_app
        window.setProperty("selectedIndex", 0)
        qt_app.processEvents()
        _do_photo_op(controller, qt_app, lambda: controller.toggleStar(0))
        star_label = window.findChild(QObject, "trayStarLabel")
        assert star_label is not None
        assert star_label.property("color").name() == "#f5c518"  # arany


class TestMultiSelect:
    def _click(self, qt_app, window, index, modifiers=0):
        from PySide6.QtCore import Q_ARG, QMetaObject, Qt

        QMetaObject.invokeMethod(
            window,
            "handleThumbClick",
            Qt.ConnectionType.DirectConnection,
            Q_ARG("QVariant", index),
            Q_ARG("QVariant", modifiers),
        )
        qt_app.processEvents()

    @staticmethod
    def _indexes(window):
        # a QML `property var` tömb QJSValue-ként érkezik Pythonba
        value = window.property("selectedIndexes")
        if hasattr(value, "toVariant"):
            value = value.toVariant()
        return [int(v) for v in value]

    def test_plain_click_single_selection(self, qml_app, qt_app):
        window, _, _ = qml_app
        self._click(qt_app, window, 0)
        assert self._indexes(window) == [0]
        assert window.property("selectedIndex") == 0

    def test_ctrl_click_toggles(self, qml_app, qt_app):
        from PySide6.QtCore import Qt

        window, _, _ = qml_app
        ctrl = int(Qt.KeyboardModifier.ControlModifier.value)
        self._click(qt_app, window, 0)
        self._click(qt_app, window, 1, ctrl)
        assert sorted(self._indexes(window)) == [0, 1]
        self._click(qt_app, window, 0, ctrl)
        assert self._indexes(window) == [1]

    def test_shift_click_selects_range(self, qml_app, qt_app):
        from PySide6.QtCore import Qt

        window, _, _ = qml_app
        shift = int(Qt.KeyboardModifier.ShiftModifier.value)
        self._click(qt_app, window, 0)
        self._click(qt_app, window, 1, shift)
        assert sorted(self._indexes(window)) == [0, 1]

    def test_clear_selection(self, qml_app, qt_app):
        from PySide6.QtCore import QMetaObject, Qt

        window, _, _ = qml_app
        self._click(qt_app, window, 0)
        QMetaObject.invokeMethod(
            window, "clearSelection", Qt.ConnectionType.DirectConnection
        )
        qt_app.processEvents()
        assert self._indexes(window) == []
        assert window.property("selectedIndex") == -1


class TestSelectionStability:
    """#135: a kijelölés sor-index helyett fotó-id-hez van kötve — a
    háttér-frissítés (5 perces rescan, watcher-jelzés) miatti sor-eltolódás
    nem viheti a kijelölést (és a rá épülő műveleteket) másik képre."""

    @staticmethod
    def _click(qt_app, window, index, modifiers=0):
        from PySide6.QtCore import Q_ARG, QMetaObject, Qt

        QMetaObject.invokeMethod(
            window,
            "handleThumbClick",
            Qt.ConnectionType.DirectConnection,
            Q_ARG("QVariant", index),
            Q_ARG("QVariant", modifiers),
        )
        qt_app.processEvents()

    @staticmethod
    def _indexes(window):
        value = window.property("selectedIndexes")
        if hasattr(value, "toVariant"):
            value = value.toVariant()
        return [int(v) for v in value]

    def test_selection_follows_photo_after_background_insert(
        self, qml_app, qt_app, tmp_path
    ):
        window, controller, _ = qml_app
        lib = tmp_path / "kepek"
        # b.jpg a névsorban a.jpg után, tehát a 2. (1-es indexű) sor
        assert controller.photos.filePathAt(1).endswith("b.jpg")
        b_id = int(controller.photos.idAt(1))
        self._click(qt_app, window, 1)
        assert window.property("selectedIndex") == 1

        # háttér-sync szimulálása: új fájl kerül a mappa elejére (névsorban
        # az a.jpg elé) — a meglévő sorok eltolódnak. A valódi 5 perces
        # rescan is így ír előbb az indexbe, majd syncFinished-en át hívja
        # az _reload_after_sync-et.
        make_jpeg(lib / "0.jpg", size=(64, 64))
        with open_index(tmp_path / "index.db") as conn:
            sync_tree(conn, lib)
        controller._reload_after_sync()
        qt_app.processEvents()

        new_row = controller.photos.rowOfId(b_id)
        assert new_row == 2  # 0.jpg, a.jpg, b.jpg sorrendben
        assert self._indexes(window) == [new_row]
        assert window.property("selectedIndex") == new_row
        assert controller.photos.filePathAt(new_row).endswith("b.jpg")

    def test_operation_after_resync_hits_correct_photo(
        self, qml_app, qt_app, tmp_path
    ):
        window, controller, _ = qml_app
        lib = tmp_path / "kepek"
        b_id = int(controller.photos.idAt(1))
        self._click(qt_app, window, 1)

        make_jpeg(lib / "0.jpg", size=(64, 64))
        with open_index(tmp_path / "index.db") as conn:
            sync_tree(conn, lib)
        controller._reload_after_sync()
        qt_app.processEvents()

        row = window.property("selectedIndex")
        assert row == controller.photos.rowOfId(b_id)
        _do_photo_op(controller, qt_app, lambda: controller.toggleStar(row))

        # a csillag a kijelölt (b.jpg) fotón landolt, a többin nem
        for r in range(controller.photos.rowCount()):
            expected = r == controller.photos.rowOfId(b_id)
            assert controller.photos.starAt(r) is expected

    def test_selection_drops_photo_removed_during_background_sync(
        self, qml_app, qt_app, tmp_path
    ):
        # ha a kijelölt fájl közben eltűnt (törölve/áthelyezve), a
        # kijelölés essen ki alóla — ne mutasson félrevezetően egy MÁSIK
        # (a helyére csúszott) képre
        window, controller, _ = qml_app
        lib = tmp_path / "kepek"
        assert controller.photos.filePathAt(0).endswith("a.jpg")
        self._click(qt_app, window, 0)
        assert window.property("selectedIndex") == 0

        (lib / "a.jpg").unlink()
        with open_index(tmp_path / "index.db") as conn:
            sync_tree(conn, lib)
        controller._reload_after_sync()
        qt_app.processEvents()

        assert self._indexes(window) == []
        assert window.property("selectedIndex") == -1


class TestSelectStarred:
    """#426: „Csillagozottak kijelölése" (Picasa `ID_SELECTSTAR`, Szerkesztés
    menü) — a JELENLEGI nézet csillagos képeit jelöli ki, NEM a Mappák panel
    „Csillagozott" nézet-szűrőjét váltja (az utóbbi külön, meglévő út,
    `controller.showStarred()`, a bal oldali fa „Starred" bejegyzésén)."""

    @staticmethod
    def _indexes(window):
        value = window.property("selectedIndexes")
        if hasattr(value, "toVariant"):
            value = value.toVariant()
        return [int(v) for v in value]

    def test_selects_only_starred_rows_in_current_view(self, qml_app, qt_app):
        window, controller, _engine = qml_app
        wait_for_photo_op(controller, lambda: controller.toggleStar(1), qt_app=qt_app)

        window.setProperty("selectedIndexes", [])
        window.setProperty("selectedIndex", -1)
        qt_app.processEvents()

        from PySide6.QtCore import QMetaObject, Qt

        QMetaObject.invokeMethod(
            window, "selectStarred", Qt.ConnectionType.DirectConnection
        )
        qt_app.processEvents()

        assert self._indexes(window) == [1]
        assert window.property("selectedIndex") == 1

    def test_view_filter_stays_untouched(self, qml_app, qt_app):
        """A kijelölés NEM változtatja meg az aktuális nézetet/szűrést."""
        window, controller, _engine = qml_app
        wait_for_photo_op(controller, lambda: controller.toggleStar(0), qt_app=qt_app)
        before = controller.filterActive

        from PySide6.QtCore import QMetaObject, Qt

        QMetaObject.invokeMethod(
            window, "selectStarred", Qt.ConnectionType.DirectConnection
        )
        qt_app.processEvents()

        assert controller.filterActive == before


class TestLasso:
    @staticmethod
    def _apply(qt_app, grid, start, count, flow_w, x1, y1, x2, y2, mods=0):
        # #64: a lasszó a húzás kezdő-csoportján belül jelöl ki — a hívás
        # a csoport (start, count) és a képfolyam szélessége szerint számol.
        from PySide6.QtCore import Q_ARG, QMetaObject, Qt

        QMetaObject.invokeMethod(
            grid, "applyLasso", Qt.ConnectionType.DirectConnection,
            Q_ARG("QVariant", start), Q_ARG("QVariant", count),
            Q_ARG("QVariant", flow_w),
            Q_ARG("QVariant", x1), Q_ARG("QVariant", y1),
            Q_ARG("QVariant", x2), Q_ARG("QVariant", y2),
            Q_ARG("QVariant", mods),
        )
        qt_app.processEvents()

    def test_lasso_selects_geometry_range(self, qml_app, qt_app):
        # A (0,0)-tól két cellányira húzott keret a csoport mindkét képét
        # kijelöli.
        from PySide6.QtCore import QObject

        window, controller, _ = qml_app
        grid = window.findChild(QObject, "photoGrid")
        assert grid is not None, "photoGrid nem található"
        cell_w = grid.property("cellWidth")
        self._apply(qt_app, grid, 0, 2, cell_w * 4, 0, 0, cell_w * 2 + 1, 1)
        value = window.property("selectedIndexes")
        if hasattr(value, "toVariant"):
            value = value.toVariant()
        assert sorted(int(v) for v in value) == [0, 1]

    def test_lasso_ctrl_merges(self, qml_app, qt_app):
        from PySide6.QtCore import QObject, Qt

        window, controller, _ = qml_app
        window.setProperty("selectedIndexes", [1])
        grid = window.findChild(QObject, "photoGrid")
        cell_w = grid.property("cellWidth")
        ctrl = int(Qt.KeyboardModifier.ControlModifier.value)
        self._apply(qt_app, grid, 0, 2, cell_w * 4, 0, 0, 1, 1, ctrl)
        value = window.property("selectedIndexes")
        if hasattr(value, "toVariant"):
            value = value.toVariant()
        assert sorted(int(v) for v in value) == [0, 1]

    def test_lasso_respects_group_offset(self, qml_app, qt_app):
        # Egy második csoportban (start=5) húzott lasszó globális sorokat ad.
        from PySide6.QtCore import QObject

        window, _, _ = qml_app
        grid = window.findChild(QObject, "photoGrid")
        cell_w = grid.property("cellWidth")
        self._apply(qt_app, grid, 5, 3, cell_w * 4, 0, 0, cell_w * 2 + 1, 1)
        value = window.property("selectedIndexes")
        if hasattr(value, "toVariant"):
            value = value.toVariant()
        assert sorted(int(v) for v in value) == [5, 6, 7]
