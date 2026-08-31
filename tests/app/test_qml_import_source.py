"""QML-funkcionális teszt: ImportSourceDialog.qml (#23/#441) — "Import
forrásból": az eszköztár "Import" gombja, a forrás-előnézet, a HÁROM
célmappa-elnevezési mód, a duplikátum-kizárás, az egyenkénti válogatás és a
háromállapotú forrás-törlés a `importSourceController` hídján keresztül,
valódi ideiglenes forrás- és cél-mappával, mock nélkül (a
`test_qml_dedup.py` mintája).

Az import fájlokat másol és a törlési ágakon forrásfájlokat távolít el,
ezért ez a fájl szándékosan funkció-szintű `qml_app` fixture-t használ."""

from datetime import date

from PySide6.QtCore import (
    QEventLoop,
    QMetaObject,
    QObject,
    Qt,
    QTimer,
)
from PySide6.QtQuick import QQuickWindow
from support.halasztott_parbeszed import nyisd_meg

from support.jpeg_factory import make_jpeg


def _child(window, name):
    # #1720: a párbeszéd HALASZTOTT — ha még nem áll, a valódi
    # menüponttal nyitjuk meg (support/halasztott_parbeszed.py).
    nyisd_meg(window, "importSourceDialog")
    obj = window.findChild(QObject, name)
    assert obj is not None, f"{name} nem található"
    return obj


def _dialog_window(window):
    # #1720: a párbeszéd HALASZTOTT — ha még nem áll, a valódi
    # menüponttal nyitjuk meg (support/halasztott_parbeszed.py).
    nyisd_meg(window, "importSourceDialog")
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
    dialog.setProperty("visible", True)
    dialog.setProperty("sourceFolder", str(source_folder))
    loop = _quit_on(_import_source_controller(engine).sourceScanFinished)
    QMetaObject.invokeMethod(
        dialog, "scanCurrentSource", Qt.ConnectionType.DirectConnection
    )
    loop.exec()
    qt_app.processEvents()


def _preview_items(dialog):
    items = dialog.property("previewItems")
    if hasattr(items, "toVariant"):
        items = items.toVariant()
    return items


class TestToolbarEntryPoint:
    def test_import_button_is_enabled(self, qml_app):
        window, _controller, _lib, _engine = qml_app
        button = _child(window, "toolbarImportButton")
        assert button.property("enabled") is True

    def test_clicking_import_opens_the_dialog(self, qml_app, qt_app):
        window, _controller, _lib, _engine = qml_app
        button = window.findChild(QObject, "toolbarImportButton")
        assert button is not None, "toolbarImportButton nem található"
        # #1720: a párbeszéd HALASZTOTT — a gomb ELŐTT létre sem jön.
        assert window.findChild(QObject, "importSourceDialog") is None, (
            "az Import ablak már a gombnyomás előtt felépült — a #1720 "
            "halasztása elromlott"
        )

        QMetaObject.invokeMethod(
            button, "clicked", Qt.ConnectionType.DirectConnection
        )
        qt_app.processEvents()

        dialog = window.findChild(QObject, "importSourceDialog")
        assert dialog is not None, "az Import gomb nem hozta létre az ablakot"
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

    def test_by_date_is_the_default_naming_mode(self, qml_app):
        window, _controller, _lib, _engine = qml_app
        dialog = _dialog_window(window)
        assert dialog.property("namingMode") == "date"

    def test_leave_card_alone_is_the_default_after_copying(self, qml_app):
        window, _controller, _lib, _engine = qml_app
        dialog = _dialog_window(window)
        assert dialog.property("afterCopying") == "leave"


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
        items = _preview_items(dialog)
        assert len(items) == 2
        for item in items:
            assert item["thumbUrl"].startswith("image://thumbs/")
            assert item["excluded"] is False

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


class TestIndividualSelection:
    def test_excluding_a_single_file_updates_the_preview_via_selection_changed(
        self, qml_app, qt_app, tmp_path
    ):
        """A GridView-beli Exclude/Include érintőfelület a controller
        `excludeFile`/`includeFile` szlotjait hívja (ld. az ImportSourceDialog.qml
        MouseArea-inak `onClicked`-jét) — itt közvetlenül a controllert hívjuk,
        és azt ellenőrizzük, hogy a `selectionChanged` jelzés a dialógus
        `previewItems`-ét ténylegesen frissíti (a Connections-bekötés)."""
        window, _controller, _lib, engine = qml_app
        dialog = _dialog_window(window)
        source = tmp_path / "kartya"
        source.mkdir()
        make_jpeg(source / "a.jpg")
        make_jpeg(source / "b.jpg")
        _scan(dialog, source, engine, qt_app)

        items = _preview_items(dialog)
        assert all(not item["excluded"] for item in items)

        _import_source_controller(engine).excludeFile(str(source / "a.jpg"))
        qt_app.processEvents()

        items = _preview_items(dialog)
        assert sum(1 for item in items if item["excluded"]) == 1

    def test_exclude_all_then_include_all(self, qml_app, qt_app, tmp_path):
        window, _controller, _lib, engine = qml_app
        dialog = _dialog_window(window)
        source = tmp_path / "kartya"
        source.mkdir()
        make_jpeg(source / "a.jpg")
        make_jpeg(source / "b.jpg")
        _scan(dialog, source, engine, qt_app)

        exclude_all = _child(window, "importSourceExcludeAllButton")
        QMetaObject.invokeMethod(
            exclude_all, "clicked", Qt.ConnectionType.DirectConnection
        )
        qt_app.processEvents()
        assert all(item["excluded"] for item in _preview_items(dialog))

        start_button = _child(window, "importSourceStartButton")
        # a cél nincs beállítva, de a válogatás miatt is tiltva lenne
        assert start_button.property("enabled") is False

        include_all = _child(window, "importSourceIncludeAllButton")
        QMetaObject.invokeMethod(
            include_all, "clicked", Qt.ConnectionType.DirectConnection
        )
        qt_app.processEvents()
        assert all(not item["excluded"] for item in _preview_items(dialog))


class TestDuplicateExclusion:
    def test_a_duplicate_of_an_indexed_photo_is_flagged_in_the_preview(
        self, qml_app, qt_app, tmp_path
    ):
        window, _controller, lib, engine = qml_app
        dialog = _dialog_window(window)
        source = tmp_path / "kartya"
        source.mkdir()
        # a `qml_app` fixture "a.jpg"-t (320x160) már beszinkronizálta a
        # könyvtárba (`lib`) — pontosan ugyanezt a tartalmat visszük be
        # forrásként, hogy bitre azonos (duplikátum) legyen.
        make_jpeg(source / "a.jpg", size=(320, 160))

        _scan(dialog, source, engine, qt_app)

        items = _preview_items(dialog)
        assert items[0]["duplicate"] is True

        checkbox = _child(window, "importSourceAutoExcludeCheckBox")
        QMetaObject.invokeMethod(
            checkbox, "click", Qt.ConnectionType.DirectConnection
        )
        qt_app.processEvents()

        assert checkbox.property("checked") is True
        items = _preview_items(dialog)
        assert items[0]["excluded"] is True

        count_text = _child(window, "importSourceDuplicateCountText")
        assert count_text.property("visible") is True


class TestRunImport:
    def test_by_date_mode_copies_into_a_single_level_date_folder(
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

        target = dest / "2024-03-05" / "a.jpg"
        assert target.exists()
        assert (source / "a.jpg").exists()  # "Leave card alone" — a forrás megmarad
        assert str(dest) in controller.watchedFolders

        result_text = _child(window, "importSourceResultText")
        assert result_text.property("visible") is True

    def test_manual_mode_uses_the_typed_folder_name(self, qml_app, qt_app, tmp_path):
        window, _controller, _lib, engine = qml_app
        dialog = _dialog_window(window)
        source = tmp_path / "kartya"
        source.mkdir()
        make_jpeg(source / "a.jpg", taken_at="2024:03:05 10:00:00")
        dest = tmp_path / "cel-konyvtar"
        dest.mkdir()

        _scan(dialog, source, engine, qt_app)
        dialog.setProperty("destFolder", str(dest))
        dialog.setProperty("namingMode", "manual")
        dialog.setProperty("manualFolderName", "Nyaralás")

        start_button = _child(window, "importSourceStartButton")
        loop = _quit_on(_import_source_controller(engine).importFinished)
        QMetaObject.invokeMethod(
            start_button, "clicked", Qt.ConnectionType.DirectConnection
        )
        loop.exec()
        qt_app.processEvents()

        assert (dest / "Nyaralás" / "a.jpg").exists()

    def test_today_mode_uses_todays_date_folder(self, qml_app, qt_app, tmp_path):
        window, _controller, _lib, engine = qml_app
        dialog = _dialog_window(window)
        source = tmp_path / "kartya"
        source.mkdir()
        make_jpeg(source / "a.jpg", taken_at="2024:03:05 10:00:00")
        dest = tmp_path / "cel-konyvtar"
        dest.mkdir()

        _scan(dialog, source, engine, qt_app)
        dialog.setProperty("destFolder", str(dest))
        dialog.setProperty("namingMode", "today")

        start_button = _child(window, "importSourceStartButton")
        loop = _quit_on(_import_source_controller(engine).importFinished)
        QMetaObject.invokeMethod(
            start_button, "clicked", Qt.ConnectionType.DirectConnection
        )
        loop.exec()
        qt_app.processEvents()

        assert (dest / date.today().isoformat() / "a.jpg").exists()


class TestAfterCopyingConfirmation:
    def test_delete_copied_asks_for_confirmation_before_deleting(
        self, qml_app, qt_app, tmp_path
    ):
        window, _controller, _lib, engine = qml_app
        dialog = _dialog_window(window)
        source = tmp_path / "kartya"
        source.mkdir()
        make_jpeg(source / "a.jpg", taken_at="2024:03:05 10:00:00")
        dest = tmp_path / "cel-konyvtar"
        dest.mkdir()

        _scan(dialog, source, engine, qt_app)
        dialog.setProperty("destFolder", str(dest))
        dialog.setProperty("afterCopying", "delete_copied")

        confirm = window.findChild(
            QObject, "importSourceRemoveImportedConfirmDialog"
        )
        assert confirm is not None
        assert confirm.property("visible") is False

        start_button = _child(window, "importSourceStartButton")
        QMetaObject.invokeMethod(
            start_button, "clicked", Qt.ConnectionType.DirectConnection
        )
        qt_app.processEvents()

        # a megerősítő dialógus nyitva, az import MÉG nem futott le
        assert confirm.property("visible") is True
        assert (source / "a.jpg").exists()

        loop = _quit_on(_import_source_controller(engine).importFinished)
        yes_button = _child(window, "importSourceRemoveImportedConfirmYesButton")
        QMetaObject.invokeMethod(
            yes_button, "clicked", Qt.ConnectionType.DirectConnection
        )
        loop.exec()
        qt_app.processEvents()

        assert (dest / "2024-03-05" / "a.jpg").exists()
        assert not (source / "a.jpg").exists()

    def test_delete_all_asks_a_second_stronger_warning(
        self, qml_app, qt_app, tmp_path
    ):
        window, _controller, _lib, engine = qml_app
        dialog = _dialog_window(window)
        source = tmp_path / "kartya"
        source.mkdir()
        make_jpeg(source / "a.jpg", taken_at="2024:03:05 10:00:00")
        make_jpeg(source / "b.jpg", taken_at="2024:03:06 10:00:00")
        dest = tmp_path / "cel-konyvtar"
        dest.mkdir()

        _scan(dialog, source, engine, qt_app)
        dialog.setProperty("destFolder", str(dest))
        dialog.setProperty("afterCopying", "delete_all")

        _import_source_controller(engine).excludeFile(str(source / "b.jpg"))
        qt_app.processEvents()

        start_button = _child(window, "importSourceStartButton")
        QMetaObject.invokeMethod(
            start_button, "clicked", Qt.ConnectionType.DirectConnection
        )
        qt_app.processEvents()

        first_confirm = window.findChild(
            QObject, "importSourceRemoveImportedConfirmDialog"
        )
        assert first_confirm.property("visible") is True
        yes_button = _child(window, "importSourceRemoveImportedConfirmYesButton")
        QMetaObject.invokeMethod(
            yes_button, "clicked", Qt.ConnectionType.DirectConnection
        )
        qt_app.processEvents()

        second_confirm = window.findChild(
            QObject, "importSourceDeleteAllWarningConfirmDialog"
        )
        assert second_confirm is not None
        assert second_confirm.property("visible") is True
        # az import addig nem futott le
        assert (source / "a.jpg").exists()

        loop = _quit_on(_import_source_controller(engine).importFinished)
        second_yes = _child(window, "importSourceDeleteAllWarningConfirmYesButton")
        QMetaObject.invokeMethod(
            second_yes, "clicked", Qt.ConnectionType.DirectConnection
        )
        loop.exec()
        qt_app.processEvents()

        # "Delete everything on card": a kizárt b.jpg is törlődik
        assert not (source / "a.jpg").exists()
        assert not (source / "b.jpg").exists()

    def test_leave_card_alone_skips_confirmation(self, qml_app, qt_app, tmp_path):
        window, _controller, _lib, engine = qml_app
        dialog = _dialog_window(window)
        source = tmp_path / "kartya"
        source.mkdir()
        make_jpeg(source / "a.jpg", taken_at="2024:03:05 10:00:00")
        dest = tmp_path / "cel-konyvtar"
        dest.mkdir()

        _scan(dialog, source, engine, qt_app)
        dialog.setProperty("destFolder", str(dest))
        # afterCopying alapértelmezetten "leave"

        loop = _quit_on(_import_source_controller(engine).importFinished)
        start_button = _child(window, "importSourceStartButton")
        QMetaObject.invokeMethod(
            start_button, "clicked", Qt.ConnectionType.DirectConnection
        )
        loop.exec()
        qt_app.processEvents()

        assert (source / "a.jpg").exists()
        assert (dest / "2024-03-05" / "a.jpg").exists()


class TestRotateAndStarInThePreview:
    """#441: az előnézeten forgatni és csillagozni lehet MÁR az import
    előtt — az eredeti import-képernyőjén ugyanígy ott volt a két forgató
    gomb és a csillagozás."""

    def test_the_preview_reflects_the_marks(self, qml_app, qt_app, tmp_path):
        window, _controller, _lib, engine = qml_app
        dialog = _dialog_window(window)
        source = tmp_path / "kartya"
        source.mkdir()
        make_jpeg(source / "a.jpg")
        _scan(dialog, source, engine, qt_app)

        items = _preview_items(dialog)
        assert items[0]["rotation"] == 0
        assert items[0]["starred"] is False

        controller = _import_source_controller(engine)
        controller.rotateFile(str(source / "a.jpg"), 1)
        controller.toggleStar(str(source / "a.jpg"))
        qt_app.processEvents()

        items = _preview_items(dialog)
        assert items[0]["rotation"] == 1
        assert items[0]["starred"] is True

    # A gombok MEGLÉTÉT nem findChild-dal ellenőrizzük: a GridView
    # delegáltjai onnan nem érhetők el (MEMORY 2026-07-31) — a fájl többi
    # tesztje is a controller-úton méri a delegált viselkedését.


class TestInitialScanDialog:
    """#449: az első indítás EGYETLEN kérdése — a Mappakezelő fája helyett."""

    def test_the_dialog_exists_with_both_choices(self, qml_app, qt_app):
        window, _controller, _lib, _engine = qml_app
        dialog = _child(window, "initialScanDialog")

        assert dialog is not None
        assert _child(window, "initialScanNarrow") is not None
        assert _child(window, "initialScanWide") is not None

    def test_it_stays_closed_when_a_folder_is_already_watched(
        self, qml_app, qt_app
    ):
        # a fixture könyvtára már figyelt — ilyenkor nincs mit kérdezni
        window, controller, _lib, _engine = qml_app
        assert controller.needsInitialScan is False
        assert _child(window, "initialScanDialog").property("visible") is False

    def test_the_scope_is_shown_in_advance(self, qml_app, qt_app):
        window, _controller, _lib, _engine = qml_app
        dialog = _child(window, "initialScanDialog")

        dialog.setProperty("choice", "wide")
        qt_app.processEvents()

        assert _child(window, "initialScanScopeText").property("text") != ""

    def test_the_reassurance_is_on_the_screen(self, qml_app, qt_app):
        window, _controller, _lib, _engine = qml_app

        text = _child(window, "initialScanReassuranceText").property("text")

        # az eredeti mindkét képernyőjén ott volt: a keresés SOHA nem mozgat
        assert "never moves" in text or "nem mozgat" in text
