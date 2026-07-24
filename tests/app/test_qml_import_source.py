"""QML-funkcionális teszt: ImportSourceDialog.qml (#23) — "Import forrásból":
az eszköztár "Import" gombja, a forrás-előnézet és a másolás/áthelyezés a
`importSourceController` hídján keresztül, valódi ideiglenes forrás- és
cél-mappával, mock nélkül (a `test_qml_dedup.py` mintája)."""

from PySide6.QtCore import (
    QEventLoop,
    QMetaObject,
    QObject,
    Qt,
    QTimer,
)
from PySide6.QtQuick import QQuickWindow

from support.jpeg_factory import make_jpeg


def _child(window, name):
    obj = window.findChild(QObject, name)
    assert obj is not None, f"{name} nem található"
    return obj


def _dialog_window(window):
    dialog = window.findChild(QQuickWindow, "importSourceDialog")
    assert dialog is not None, "importSourceDialog nem található Window-ként"
    return dialog


def _quit_on(signal):
    loop = QEventLoop()
    signal.connect(loop.quit)
    QTimer.singleShot(5000, loop.quit)
    return loop


def _import_source_controller(engine):
    controller = engine.rootContext().contextProperty("importSourceController")
    assert controller is not None, "importSourceController context property hiányzik"
    return controller


def _scan(dialog, source_folder, engine, qt_app):
    dialog.setProperty("sourceFolder", str(source_folder))
    loop = _quit_on(_import_source_controller(engine).sourceScanFinished)
    QMetaObject.invokeMethod(
        dialog, "scanCurrentSource", Qt.ConnectionType.DirectConnection
    )
    loop.exec()
    qt_app.processEvents()


class TestToolbarEntryPoint:
    def test_import_button_is_enabled(self, qml_app):
        window, _controller, _lib, _engine = qml_app
        button = _child(window, "toolbarImportButton")
        assert button.property("enabled") is True

    def test_clicking_import_opens_the_dialog(self, qml_app, qt_app):
        window, _controller, _lib, _engine = qml_app
        button = _child(window, "toolbarImportButton")
        dialog = _dialog_window(window)
        assert dialog.property("visible") is False

        QMetaObject.invokeMethod(
            button, "clicked", Qt.ConnectionType.DirectConnection
        )
        qt_app.processEvents()

        assert dialog.property("visible") is True


class TestDialogWindow:
    def test_is_a_standalone_resizable_window(self, qml_app):
        window, _controller, _lib, _engine = qml_app
        dialog = _dialog_window(window)
        assert dialog.property("minimumWidth") is not None
        assert dialog.property("minimumWidth") >= 400
        assert dialog.property("minimumHeight") is not None

    def test_close_button_hides_the_window(self, qml_app, qt_app):
        window, _controller, _lib, _engine = qml_app
        dialog = _dialog_window(window)
        dialog.setProperty("visible", True)
        qt_app.processEvents()

        close_button = _child(window, "importSourceCloseButton")
        QMetaObject.invokeMethod(
            close_button, "clicked", Qt.ConnectionType.DirectConnection
        )
        qt_app.processEvents()
        assert dialog.property("visible") is False

    def test_copy_is_the_default_mode(self, qml_app):
        window, _controller, _lib, _engine = qml_app
        dialog = _dialog_window(window)
        assert dialog.property("moveInsteadOfCopy") is False


class TestSourcePreview:
    def test_scanning_populates_preview_grid_with_thumb_urls(
        self, qml_app, qt_app, tmp_path
    ):
        window, _controller, _lib, engine = qml_app
        dialog = _dialog_window(window)
        source = tmp_path / "kartya"
        source.mkdir()
        make_jpeg(source / "a.jpg")
        make_jpeg(source / "b.jpg")

        _scan(dialog, source, engine, qt_app)

        assert dialog.property("previewCount") == 2
        items = dialog.property("previewItems")
        if hasattr(items, "toVariant"):
            items = items.toVariant()
        assert len(items) == 2
        for item in items:
            assert item["thumbUrl"].startswith("image://thumbs/")

        start_button = _child(window, "importSourceStartButton")
        # a cél-mappa még nincs kiválasztva — a gomb nem engedélyezett
        assert start_button.property("enabled") is False

    def test_empty_source_shows_empty_text(self, qml_app, qt_app, tmp_path):
        window, _controller, _lib, engine = qml_app
        dialog = _dialog_window(window)
        source = tmp_path / "ures-kartya"
        source.mkdir()

        _scan(dialog, source, engine, qt_app)

        assert dialog.property("previewCount") == 0
        empty_text = _child(window, "importSourceEmptyText")
        assert empty_text.property("visible") is True

    def test_missing_source_shows_error(self, qml_app, qt_app, tmp_path):
        window, _controller, _lib, engine = qml_app
        dialog = _dialog_window(window)

        _scan(dialog, tmp_path / "nincs-ilyen", engine, qt_app)

        error_text = _child(window, "importSourceErrorText")
        assert error_text.property("visible") is True


class TestRunImport:
    def test_copy_leaves_source_untouched_and_watches_destination(
        self, qml_app, qt_app, tmp_path
    ):
        window, controller, _lib, engine = qml_app
        dialog = _dialog_window(window)
        source = tmp_path / "kartya"
        source.mkdir()
        make_jpeg(source / "a.jpg", taken_at="2024:03:05 10:00:00")
        dest = tmp_path / "cel-konyvtar"
        dest.mkdir()

        _scan(dialog, source, engine, qt_app)
        dialog.setProperty("destFolder", str(dest))

        start_button = _child(window, "importSourceStartButton")
        assert start_button.property("enabled") is True

        loop = _quit_on(_import_source_controller(engine).importFinished)
        QMetaObject.invokeMethod(
            start_button, "clicked", Qt.ConnectionType.DirectConnection
        )
        loop.exec()
        qt_app.processEvents()

        target = dest / "2024" / "2024-03-05" / "a.jpg"
        assert target.exists()
        assert (source / "a.jpg").exists()  # másolás — a forrás megmarad
        assert str(dest) in controller.watchedFolders

        result_text = _child(window, "importSourceResultText")
        assert result_text.property("visible") is True

    def test_move_mode_removes_the_source_file(self, qml_app, qt_app, tmp_path):
        window, _controller, _lib, engine = qml_app
        dialog = _dialog_window(window)
        source = tmp_path / "kartya"
        source.mkdir()
        make_jpeg(source / "a.jpg", taken_at="2024:03:05 10:00:00")
        dest = tmp_path / "cel-konyvtar"
        dest.mkdir()

        _scan(dialog, source, engine, qt_app)
        dialog.setProperty("destFolder", str(dest))
        dialog.setProperty("moveInsteadOfCopy", True)

        start_button = _child(window, "importSourceStartButton")
        loop = _quit_on(_import_source_controller(engine).importFinished)
        QMetaObject.invokeMethod(
            start_button, "clicked", Qt.ConnectionType.DirectConnection
        )
        loop.exec()
        qt_app.processEvents()

        assert (dest / "2024" / "2024-03-05" / "a.jpg").exists()
        assert not (source / "a.jpg").exists()

    def test_custom_template_is_applied(self, qml_app, qt_app, tmp_path):
        window, _controller, _lib, engine = qml_app
        dialog = _dialog_window(window)
        source = tmp_path / "kartya"
        source.mkdir()
        make_jpeg(source / "a.jpg", taken_at="2024:03:05 10:00:00")
        dest = tmp_path / "cel-konyvtar"
        dest.mkdir()

        _scan(dialog, source, engine, qt_app)
        dialog.setProperty("destFolder", str(dest))
        dialog.setProperty("template", "{YYYY}/{MM}")

        start_button = _child(window, "importSourceStartButton")
        loop = _quit_on(_import_source_controller(engine).importFinished)
        QMetaObject.invokeMethod(
            start_button, "clicked", Qt.ConnectionType.DirectConnection
        )
        loop.exec()
        qt_app.processEvents()

        assert (dest / "2024" / "03" / "a.jpg").exists()
