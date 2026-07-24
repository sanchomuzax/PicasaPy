"""QML-funkcionális teszt: DedupDialog.qml (#287) — a duplikátum-kezelő
önálló ablak, a `dedupController` hídján keresztül, valódi ideiglenes
könyvtárfán/indexen, mock nélkül (a test_qml_folder_manager.py mintája).
"""

from PySide6.QtCore import (
    Q_ARG,
    QEventLoop,
    QMetaObject,
    QObject,
    Qt,
    QTimer,
)
from PySide6.QtQuick import QQuickWindow

from picasapy.index import open_index, sync_tree

from support.jpeg_factory import make_jpeg


def _child(window, name):
    obj = window.findChild(QObject, name)
    assert obj is not None, f"{name} nem található"
    return obj


def _dialog_window(window):
    dialog = window.findChild(QQuickWindow, "dedupDialog")
    assert dialog is not None, "dedupDialog nem található Window-ként"
    return dialog


def _quit_on(signal):
    loop = QEventLoop()
    signal.connect(loop.quit)
    QTimer.singleShot(5000, loop.quit)
    return loop


def _dedup_controller(engine):
    controller = engine.rootContext().contextProperty("dedupController")
    assert controller is not None, "dedupController context property hiányzik"
    return controller


def _open_and_wait_scan(window, qt_app, engine):
    """A dialógus megnyitása — az `open()` automatikusan indítja az első
    keresést, itt bevárjuk a `scanFinished`-et."""
    dialog = _child(window, "dedupDialog")
    loop = _quit_on(_dedup_controller(engine).scanFinished)
    QMetaObject.invokeMethod(dialog, "open", Qt.ConnectionType.DirectConnection)
    loop.exec()
    qt_app.processEvents()
    return dialog


def _to_py(value):
    """A QML `var` lista/dict QJSValue-ként jöhet vissza — sima Python
    listává/dict-té alakítva egyszerűbb az assert."""
    if hasattr(value, "toVariant"):
        return value.toVariant()
    return value


class TestDedupDialogWindow:
    def test_is_a_standalone_resizable_window(self, qml_app, qt_app):
        window, _controller, _lib, engine = qml_app
        dialog = _open_and_wait_scan(window, qt_app, engine)

        assert dialog.property("visible") is True
        assert dialog.property("minimumWidth") is not None
        assert dialog.property("minimumWidth") >= 400
        assert dialog.property("minimumHeight") is not None

    def test_close_button_hides_the_window(self, qml_app, qt_app):
        window, _controller, _lib, engine = qml_app
        dialog = _open_and_wait_scan(window, qt_app, engine)
        assert dialog.property("visible") is True

        close_button = _child(window, "dedupCloseButton")
        QMetaObject.invokeMethod(
            close_button, "clicked", Qt.ConnectionType.DirectConnection
        )
        qt_app.processEvents()
        assert dialog.property("visible") is False


class TestMenuEntryPoint:
    def test_tools_menu_has_find_duplicates_item(self, qml_app):
        window, _controller, _lib, _engine = qml_app
        item = _child(window, "menuToolsDedup")
        assert item.property("enabled") is True

    def test_triggering_menu_item_opens_the_dialog(self, qml_app, qt_app):
        window, _controller, _lib, engine = qml_app
        item = _child(window, "menuToolsDedup")
        dialog = _child(window, "dedupDialog")
        assert dialog.property("visible") is False

        loop = _quit_on(_dedup_controller(engine).scanFinished)
        # a MenuItem-nek nincs hívható "trigger()" metódusa — a `triggered`
        # SIGNAL invokeMethod-dal is kiváltható (ez futtatja az onTriggered
        # kezelőt, ugyanúgy, ahogy egy valódi kattintás tenné)
        QMetaObject.invokeMethod(item, "triggered", Qt.ConnectionType.DirectConnection)
        loop.exec()
        qt_app.processEvents()

        assert dialog.property("visible") is True


class TestScanResults:
    def test_exact_duplicate_group_is_listed_with_two_thumbnails(
        self, qml_app, qt_app, tmp_path
    ):
        window, controller, lib, engine = qml_app
        original = make_jpeg(lib / "eredeti.jpg", size=(40, 20))
        (lib / "masolat.jpg").write_bytes(original.read_bytes())
        with open_index(controller._db_path) as conn:
            sync_tree(conn, lib)

        dialog = _open_and_wait_scan(window, qt_app, engine)

        groups = _to_py(dialog.property("groups"))
        exact = [g for g in groups if g["kind"] == "exact"]
        assert len(exact) == 1
        paths = {item["path"] for item in exact[0]["items"]}
        assert paths == {str(lib / "eredeti.jpg"), str(lib / "masolat.jpg")}
        for item in exact[0]["items"]:
            assert item["thumbUrl"].startswith("image://thumbs/")

    def test_no_duplicates_shows_empty_message(self, qml_app, qt_app):
        """A dialógus üres-állapot szövege az adatra (nem a valódi keresésre)
        épül — a megosztott `qml_app` könyvtár két egyszínű (piros) tesztképe
        a phash-nek véletlenül HASONLÓ lenne (ez a dedup mag helyes
        viselkedése, nem a dialógusé), ezért itt közvetlenül a `groups`
        propertyt állítjuk üresre."""
        window, _controller, _lib, _engine = qml_app
        dialog = _child(window, "dedupDialog")
        dialog.setProperty("groups", [])
        dialog.setProperty("scanning", False)
        qt_app.processEvents()

        empty_text = _child(window, "dedupEmptyText")
        assert empty_text.property("visible") is True


class TestScopeSelector:
    """#294: a keresés alapból a szűk hatókörre fut, a teljes könyvtár
    tudatos választás — figyelmeztetéssel."""

    def test_default_scope_is_the_current_folder(self, qml_app, qt_app):
        window, _controller, _lib, engine = qml_app
        dialog = _open_and_wait_scan(window, qt_app, engine)
        assert dialog.property("scopeIndex") == dialog.property("scopeFolder")

    def test_scope_box_offers_three_scopes(self, qml_app, qt_app):
        window, _controller, _lib, engine = qml_app
        _open_and_wait_scan(window, qt_app, engine)
        box = _child(window, "dedupScopeBox")
        assert len(_to_py(box.property("model"))) == 3

    def test_library_scope_shows_a_duration_warning(self, qml_app, qt_app):
        window, _controller, _lib, engine = qml_app
        dialog = _open_and_wait_scan(window, qt_app, engine)
        warning = _child(window, "dedupScopeWarning")
        assert warning.property("visible") is False

        dialog.setProperty("scopeIndex", dialog.property("scopeLibrary"))
        qt_app.processEvents()
        assert warning.property("visible") is True

    def test_folder_scope_only_scans_the_current_folder_tree(
        self, qml_app, qt_app, tmp_path
    ):
        """A könyvtárban lévő, de az aktuális mappán KÍVÜLI duplikátum-pár
        nem kerülhet a találatok közé (ez a #294 hatókör-szűkítés lényege)."""
        window, controller, lib, engine = qml_app
        outside = tmp_path / "mashol"
        outside.mkdir()
        original = make_jpeg(outside / "x.jpg", size=(51, 27))
        (outside / "y.jpg").write_bytes(original.read_bytes())
        with open_index(controller._db_path) as conn:
            sync_tree(conn, outside)

        dialog = _open_and_wait_scan(window, qt_app, engine)

        groups = _to_py(dialog.property("groups"))
        found = {item["path"] for g in groups for item in g["items"]}
        assert str(outside / "x.jpg") not in found


class TestProgressAndCancel:
    """#294: folyamatjelző és Mégse gomb — az ablak nem állhat némán."""

    def test_progress_panel_is_hidden_when_idle(self, qml_app, qt_app):
        window, _controller, _lib, engine = qml_app
        _open_and_wait_scan(window, qt_app, engine)
        assert _child(window, "dedupProgressPanel").property("visible") is False

    def test_progress_bar_reflects_the_reported_ratio(self, qml_app, qt_app):
        window, _controller, _lib, engine = qml_app
        dialog = _open_and_wait_scan(window, qt_app, engine)
        dialog.setProperty("scanning", True)
        dialog.setProperty("progressTotal", 4)
        dialog.setProperty("progressDone", 2)
        qt_app.processEvents()

        fill = _child(window, "dedupProgressBarFill")
        assert fill.property("visible") is True
        assert fill.property("width") > 0
        assert _child(window, "dedupProgressPanel").property("visible") is True
        dialog.setProperty("scanning", False)

    def test_cancel_button_stops_the_scan(self, qml_app, qt_app):
        window, _controller, _lib, engine = qml_app
        dialog = _open_and_wait_scan(window, qt_app, engine)
        dialog.setProperty("scanning", True)
        qt_app.processEvents()

        cancel = _child(window, "dedupCancelButton")
        loop = _quit_on(_dedup_controller(engine).scanCancelled)
        QMetaObject.invokeMethod(dialog, "scan", Qt.ConnectionType.DirectConnection)
        QMetaObject.invokeMethod(cancel, "clicked", Qt.ConnectionType.DirectConnection)
        loop.exec()
        qt_app.processEvents()

        assert dialog.property("scanning") is False


class TestCloseReleasesThumbnails:
    """#298: a bezárás elengedi a dedup-bélyegképeket, a fő rács
    regisztrációját viszont nem bántja."""

    def test_main_grid_registration_survives_the_open_close_cycle(
        self, qml_app, qt_app
    ):
        window, controller, lib, engine = qml_app
        provider = controller._provider
        grid_ids = [str(photo.id) for photo in controller.photos.photos]
        assert grid_ids

        dialog = _open_and_wait_scan(window, qt_app, engine)
        close_button = _child(window, "dedupCloseButton")
        QMetaObject.invokeMethod(
            close_button, "clicked", Qt.ConnectionType.DirectConnection
        )
        qt_app.processEvents()

        assert dialog.property("visible") is False
        for photo_id in grid_ids:
            assert provider._registry.get(photo_id) is not None

    def test_closing_drops_the_dedup_entries(self, qml_app, qt_app):
        from picasapy.app.dedup_controller import DEDUP_THUMB_ID_BASE

        window, controller, lib, engine = qml_app
        original = make_jpeg(lib / "eredeti.jpg", size=(40, 20))
        (lib / "masolat.jpg").write_bytes(original.read_bytes())
        with open_index(controller._db_path) as conn:
            sync_tree(conn, lib)
        provider = controller._provider

        dialog = _open_and_wait_scan(window, qt_app, engine)
        registered = [
            key
            for key in provider._registry
            if int(key) <= DEDUP_THUMB_ID_BASE
        ]
        assert registered, "a dedup nem regisztrált saját bélyegképeket"

        dialog.setProperty("visible", False)
        qt_app.processEvents()

        assert not [
            key for key in provider._registry if int(key) <= DEDUP_THUMB_ID_BASE
        ]
        assert _to_py(dialog.property("groups")) == []


class TestResolveGroup:
    def test_move_others_relocates_files_and_removes_group(
        self, qml_app, qt_app
    ):
        window, controller, lib, engine = qml_app
        original = make_jpeg(lib / "eredeti.jpg", size=(40, 20))
        copy_path = lib / "masolat.jpg"
        copy_path.write_bytes(original.read_bytes())
        with open_index(controller._db_path) as conn:
            sync_tree(conn, lib)

        dialog = _open_and_wait_scan(window, qt_app, engine)
        groups = _to_py(dialog.property("groups"))
        exact_index = next(
            i for i, g in enumerate(groups) if g["kind"] == "exact"
        )

        loop = _quit_on(_dedup_controller(engine).itemResolved)
        QMetaObject.invokeMethod(
            dialog,
            "moveGroup",
            Qt.ConnectionType.DirectConnection,
            Q_ARG("QVariant", exact_index),
        )
        loop.exec()
        qt_app.processEvents()

        # az "eredeti.jpg" marad (alapértelmezett megtartandó: az első elem),
        # a "masolat.jpg" a forrásmappa Duplikátumok alkönyvtárába kerül
        assert (lib / "eredeti.jpg").exists()
        assert not copy_path.exists()
        assert (lib / "Duplikátumok" / "masolat.jpg").exists()

        remaining = _to_py(dialog.property("groups"))
        assert all(len(g["items"]) >= 2 for g in remaining)
        assert not any(
            item["path"] == str(copy_path)
            for g in remaining
            for item in g["items"]
        )
