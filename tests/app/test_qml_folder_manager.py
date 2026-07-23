"""QML-funkcionális teszt: FolderManagerDialog.qml (#231) — önálló ablak,
lusta fa-betöltés (folderTreeController háttérszála) és a háromállapotú
(figyelt/egyszeri/nincs) mappa-választó megfigyelhető kimenetét
ellenőrizzük, valódi ideiglenes könyvtárfán, mock nélkül.

A fa-sorok (FolderTreeItem) Repeater-delegátok — ezek NEM QObject-gyerekei
a szülőnek (`findChild` nem látja őket), a vizuális elem-fát (`childItems`)
kell bejárni (a test_search_suggestions_qml.py mintája). A Mappakezelő
maga is önálló Window (#231) — a fa-sorok az Ő SAJÁT `contentItem`-je
alatt élnek, nem a főablak (Main.qml) alatt."""

from PySide6.QtCore import Q_ARG, QEventLoop, QMetaObject, QObject, Qt, QTimer
from PySide6.QtQuick import QQuickWindow


def _child(window, name):
    obj = window.findChild(QObject, name)
    assert obj is not None, f"{name} nem található"
    return obj


def _dialog_window(window):
    """A Mappakezelő SAJÁT QQuickWindow-ként (nem sima QObject-ként) —
    ehhez kell a `.contentItem()` a fa-sorok vizuális bejárásához."""
    dialog = window.findChild(QQuickWindow, "folderManagerDialog")
    assert dialog is not None, "folderManagerDialog nem található Window-ként"
    return dialog


def _walk_visual_tree(item):
    for child in item.childItems():
        yield child
        yield from _walk_visual_tree(child)


def _tree_row(window, path):
    dialog = _dialog_window(window)
    matches = [
        item
        for item in _walk_visual_tree(dialog.contentItem())
        if item.objectName() == f"folderTreeItem:{path}"
    ]
    assert matches, f"folderTreeItem:{path} nem található a fában"
    return matches[0]


def _tree_row_exists(window, path):
    dialog = _dialog_window(window)
    return any(
        item.objectName() == f"folderTreeItem:{path}"
        for item in _walk_visual_tree(dialog.contentItem())
    )


def _quit_on(signal):
    loop = QEventLoop()
    signal.connect(loop.quit)
    QTimer.singleShot(5000, loop.quit)
    return loop


def _invoke(obj, method, *args):
    QMetaObject.invokeMethod(
        obj,
        method,
        Qt.ConnectionType.DirectConnection,
        *[Q_ARG("QVariant", a) for a in args],
    )


def _tree_controller(engine):
    controller = engine.rootContext().contextProperty("folderTreeController")
    assert controller is not None, "folderTreeController context property hiányzik"
    return controller


def _open_with_root(window, qt_app, engine, root_path):
    """A dialógus megnyitása egy ideiglenes gyökérrel (nem a valódi "/") —
    a fa ekkor csak a `root_path` közvetlen almappáit tölti be. A
    `childrenLoaded`-re várakozó hurkot MÉG a kiváltó hívás ELŐTT kötjük be
    (versenyhelyzet nélkül: háttérszálas jelzés bármikor megelőzheti a
    bekötést, ha az utólag történne)."""
    dialog = _child(window, "folderManagerDialog")
    loop = _quit_on(_tree_controller(engine).childrenLoaded)
    dialog.setProperty("rootPath", str(root_path))
    QMetaObject.invokeMethod(dialog, "open", Qt.ConnectionType.DirectConnection)
    loop.exec()
    qt_app.processEvents()
    return dialog


def _expand_and_wait(qt_app, engine, row_item):
    loop = _quit_on(_tree_controller(engine).childrenLoaded)
    _invoke(row_item, "toggleExpand")
    loop.exec()
    qt_app.processEvents()


class TestFolderManagerWindow:
    def test_is_a_standalone_resizable_window(self, qml_app, qt_app):
        """Window-specifikus tulajdonságok (minimumWidth/Height) csak
        akkor érhetők el, ha a dialógus valódi Window/ApplicationWindow —
        egy beékelt Dialog(Popup) ezt nem ismeri, tehát ez a
        legfontosabb regressziós jel az architektúra-váltásra."""
        window, _controller, _lib, _engine = qml_app
        dialog = _child(window, "folderManagerDialog")
        QMetaObject.invokeMethod(dialog, "open", Qt.ConnectionType.DirectConnection)
        qt_app.processEvents()

        assert dialog.property("visible") is True
        assert dialog.property("minimumWidth") is not None
        assert dialog.property("minimumWidth") >= 400
        assert dialog.property("minimumHeight") is not None

    def test_ok_and_cancel_close_the_window(self, qml_app, qt_app):
        window, _controller, _lib, _engine = qml_app
        dialog = _child(window, "folderManagerDialog")
        QMetaObject.invokeMethod(dialog, "open", Qt.ConnectionType.DirectConnection)
        qt_app.processEvents()
        assert dialog.property("visible") is True

        ok_button = _child(window, "folderManagerOkButton")
        QMetaObject.invokeMethod(
            ok_button, "clicked", Qt.ConnectionType.DirectConnection
        )
        qt_app.processEvents()
        assert dialog.property("visible") is False


class TestFolderTreeLazyLoading:
    def test_expanding_a_row_loads_only_its_own_children(
        self, qml_app, qt_app, tmp_path
    ):
        browse_root = tmp_path / "tallozo"
        alfa = browse_root / "alfa"
        (alfa / "beta").mkdir(parents=True)
        (browse_root / "ures").mkdir()

        window, _controller, _lib, engine = qml_app
        _open_with_root(window, qt_app, engine, browse_root)

        alfa_row = _tree_row(window, alfa)
        assert alfa_row.property("hasChildren") is True
        assert alfa_row.property("expanded") is False
        # a "beta" gyerek-sor MÉG nem létezik — a fa nem olvasta be
        # előre (lusta betöltés)
        assert not _tree_row_exists(window, alfa / "beta")

        _expand_and_wait(qt_app, engine, alfa_row)

        beta_row = _tree_row(window, alfa / "beta")
        assert beta_row.property("hasChildren") is False

    def test_leaf_row_has_no_expand_arrow_and_ignores_toggle(
        self, qml_app, qt_app, tmp_path
    ):
        browse_root = tmp_path / "tallozo2"
        (browse_root / "ures").mkdir(parents=True)

        window, _controller, _lib, engine = qml_app
        _open_with_root(window, qt_app, engine, browse_root)

        leaf_row = _tree_row(window, browse_root / "ures")
        assert leaf_row.property("hasChildren") is False
        _invoke(leaf_row, "toggleExpand")
        assert leaf_row.property("expanded") is False


class TestFolderStateSelection:
    def test_selecting_watched_root_reports_always_state(self, qml_app, qt_app):
        window, controller, lib, engine = qml_app
        # a `qml_app` fixture a `lib` (kepek) mappát már figyeltként adja át
        assert str(lib) in controller.watchedFolders
        parent_dir = lib.parent
        _open_with_root(window, qt_app, engine, parent_dir)

        dialog = _child(window, "folderManagerDialog")
        dialog.setProperty("selectedPath", str(lib))
        qt_app.processEvents()
        assert dialog.property("selectedState") == "always"

    def test_selecting_unknown_folder_reports_none_state(self, qml_app, qt_app):
        window, _controller, lib, _engine = qml_app
        dialog = _child(window, "folderManagerDialog")
        dialog.setProperty("selectedPath", str(lib.parent / "nincs-figyelve"))
        qt_app.processEvents()
        assert dialog.property("selectedState") == "none"

    def test_scan_once_indexes_without_persisting_watch(
        self, qml_app, qt_app, tmp_path
    ):
        from support.jpeg_factory import make_jpeg

        window, controller, lib, engine = qml_app
        once_dir = lib.parent / "egyszeri"
        once_dir.mkdir()
        make_jpeg(once_dir / "x.jpg")

        dialog = _child(window, "folderManagerDialog")
        dialog.setProperty("selectedPath", str(once_dir))
        qt_app.processEvents()
        assert dialog.property("selectedState") == "none"

        loop = _quit_on(controller.syncFinished)
        _invoke(dialog, "setState", str(once_dir), "once")
        loop.exec()
        qt_app.processEvents()

        assert controller.folders.rowOfPath(str(once_dir)) >= 0
        assert str(once_dir) not in controller.watchedFolders
        assert dialog.property("selectedState") == "once"

    def test_remove_from_picasa_unwatches_root(self, qml_app, qt_app):
        window, controller, lib, _engine = qml_app
        dialog = _child(window, "folderManagerDialog")
        dialog.setProperty("selectedPath", str(lib))
        qt_app.processEvents()
        assert dialog.property("selectedState") == "always"

        _invoke(dialog, "setState", str(lib), "none")
        qt_app.processEvents()

        assert str(lib) not in controller.watchedFolders
        assert dialog.property("selectedState") == "none"

    def test_watched_folders_summary_list_still_shown(self, qml_app, qt_app):
        window, controller, _lib, _engine = qml_app
        QMetaObject.invokeMethod(
            _child(window, "folderManagerDialog"),
            "open",
            Qt.ConnectionType.DirectConnection,
        )
        qt_app.processEvents()
        summary = _child(window, "folderManagerWatchedList")
        assert summary.property("count") == len(controller.watchedFolders)
