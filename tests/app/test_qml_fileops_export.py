"""QML-funkcionális tesztek: fájlműveletek (#15) és export (#16) bekötése a
Main.qml-be — kontextusmenü, átnevezés-dialógus, export-dialógus, menüsor.

Külön fájlban a test_qml_functional.py-tól, hogy a #53-as flaky (néző +
image provider GIL) kizárásakor ezek a tesztek futhassanak tovább. A néző
képbetöltését itt egyetlen teszt sem érinti.

Az átnevezés, törlés, export és effektmásolás lemezállapotot módosít, ezért
ez a fájl szándékosan funkció-szintű `qml_app` fixture-t használ.
"""

import os

import pytest
from PySide6.QtCore import (
    Q_ARG,
    Q_RETURN_ARG,
    QEventLoop,
    QMetaObject,
    QObject,
    Qt,
    QTimer,
)


# a qml_app fixture a tests/app/conftest.py-ban él (közös a funkcionális
# teszt-fájlokkal)


def _child(window, name):
    obj = window.findChild(QObject, name)
    assert obj is not None, f"{name} nem található"
    return obj


def _as_list(value):
    """QML var-lista → Python-lista (a property QJSValue-ként jön át)."""
    return value.toVariant() if hasattr(value, "toVariant") else list(value)


def _select_row(window, qt_app, row):
    window.setProperty("selectedIndexes", [row])
    window.setProperty("selectedIndex", row)
    qt_app.processEvents()


class TestContextMenuWiring:
    def test_open_selects_row_and_opens_menu(self, qml_app, qt_app):
        window, _controller, _lib, _engine = qml_app
        grid = _child(window, "photoGrid")
        QMetaObject.invokeMethod(
            window, "openPhotoContextMenu", Qt.ConnectionType.DirectConnection,
            Q_ARG("QVariant", 0), Q_ARG("QVariant", grid),
            Q_ARG("QVariant", 5), Q_ARG("QVariant", 5),
        )
        qt_app.processEvents()
        menu = _child(window, "photoContextMenu")
        assert menu.property("visible") is True
        assert _as_list(window.property("selectedIndexes")) == [0]
        assert window.property("fileOpTargetRow") == 0
        QMetaObject.invokeMethod(menu, "close", Qt.ConnectionType.DirectConnection)
        qt_app.processEvents()

    def test_open_keeps_existing_multi_selection(self, qml_app, qt_app):
        # jobbklikk a kijelölés EGYIK elemén: a többes kijelölés megmarad,
        # a műveletek (törlés/áthelyezés) a teljes kijelölésre mennek
        window, _controller, _lib, _engine = qml_app
        window.setProperty("selectedIndexes", [0, 1])
        window.setProperty("selectedIndex", 1)
        grid = _child(window, "photoGrid")
        QMetaObject.invokeMethod(
            window, "openPhotoContextMenu", Qt.ConnectionType.DirectConnection,
            Q_ARG("QVariant", 0), Q_ARG("QVariant", grid),
            Q_ARG("QVariant", 5), Q_ARG("QVariant", 5),
        )
        qt_app.processEvents()
        assert _as_list(window.property("selectedIndexes")) == [0, 1]
        menu = _child(window, "photoContextMenu")
        QMetaObject.invokeMethod(menu, "close", Qt.ConnectionType.DirectConnection)
        qt_app.processEvents()


class TestRenameDialog:
    def test_rename_end_to_end(self, qml_app, qt_app):
        # F2-út: dialógus nyitás → új név → OK → a fájl átnevezve a lemezen,
        # és a resync (wire_fileops) után a modell is az új nevet mutatja
        window, controller, lib, _engine = qml_app
        dialog = _child(window, "renameDialog")
        QMetaObject.invokeMethod(
            dialog, "openFor", Qt.ConnectionType.DirectConnection,
            Q_ARG("QVariant", 0),
        )
        qt_app.processEvents()
        field = _child(window, "renameField")
        assert field.property("text") == "a.jpg"
        field.setProperty("text", "atnevezve.jpg")
        loop = QEventLoop()
        controller.syncFinished.connect(loop.quit)
        QMetaObject.invokeMethod(dialog, "accept", Qt.ConnectionType.DirectConnection)
        qt_app.processEvents()
        # a fájl azonnal átnevezve; a rács-frissítés (#86 óta) háttérszálas
        # resyncből érkezik — arra a syncFinished-del várunk
        assert (lib / "atnevezve.jpg").exists()
        assert not (lib / "a.jpg").exists()
        QTimer.singleShot(5000, loop.quit)
        loop.exec()
        qt_app.processEvents()
        model_names = {photo.name for photo in controller.photos.photos}
        assert model_names == {"atnevezve.jpg", "b.jpg"}


class TestRenameDialogFenParity:
    """#350: rename.fen paritás — gombfelirat és magyarázó feliratok."""

    def test_accept_button_says_rename_not_ok(self, qml_app, qt_app):
        window, _controller, _lib, _engine = qml_app
        dialog = _child(window, "renameDialog")
        QMetaObject.invokeMethod(
            dialog, "openFor", Qt.ConnectionType.DirectConnection,
            Q_ARG("QVariant", 0),
        )
        qt_app.processEvents()
        result = QMetaObject.invokeMethod(
            dialog, "acceptButtonText", Qt.ConnectionType.DirectConnection,
            Q_RETURN_ARG("QVariant"),
        )
        assert result == "Rename"

    def test_shows_selection_and_prompt_labels(self, qml_app, qt_app):
        window, _controller, _lib, _engine = qml_app
        dialog = _child(window, "renameDialog")
        QMetaObject.invokeMethod(
            dialog, "openFor", Qt.ConnectionType.DirectConnection,
            Q_ARG("QVariant", 0),
        )
        qt_app.processEvents()
        selection_label = _child(window, "renameSelectionLabel")
        prompt_label = _child(window, "renamePromptLabel")
        assert "1" in selection_label.property("text")
        assert prompt_label.property("text") == (
            "Please enter a new name for these files:"
        )


class TestRenameManyDialog:
    """#366: tömeges átnevezés (rename.fen paritás) — dátum-/felbontás-
    utótag jelölőnégyzetek, élő "Example:" előnézet, Picasa-mintájú
    sorszámozás (`név`, `név-1`, …). Az egyfájlos renameDialog (F2)
    változatlan (ld. fenti TestRenameDialog)."""

    def test_shows_count_and_first_file_preview(self, qml_app, qt_app):
        window, _controller, _lib, _engine = qml_app
        dialog = _child(window, "renameManyDialog")
        QMetaObject.invokeMethod(
            dialog, "openFor", Qt.ConnectionType.DirectConnection,
            Q_ARG("QVariant", [0, 1]),
        )
        qt_app.processEvents()
        assert dialog.property("visible") is True
        selection_label = _child(window, "renameManySelectionLabel")
        assert "2" in selection_label.property("text")
        field = _child(window, "renameManyField")
        field.setProperty("text", "nyaralas")
        qt_app.processEvents()
        sample_label = _child(window, "renameManySampleLabel")
        # az élő előnézet a kijelölés ELSŐ fájlját mutatja, sorszám nélkül
        assert sample_label.property("text") == "Example: nyaralas.jpg"

    def test_size_checkbox_updates_live_preview(self, qml_app, qt_app):
        window, _controller, _lib, _engine = qml_app
        dialog = _child(window, "renameManyDialog")
        QMetaObject.invokeMethod(
            dialog, "openFor", Qt.ConnectionType.DirectConnection,
            Q_ARG("QVariant", [0, 1]),
        )
        qt_app.processEvents()
        field = _child(window, "renameManyField")
        field.setProperty("text", "nyaralas")
        size_check = _child(window, "renameManySizeCheck")
        size_check.setProperty("checked", True)
        qt_app.processEvents()
        sample_label = _child(window, "renameManySampleLabel")
        # a fixture-beli a.jpg felbontása 320x160 (qml_app conftest)
        assert sample_label.property("text") == "Example: nyaralas 320x160.jpg"

    def test_accept_button_says_rename_not_ok(self, qml_app, qt_app):
        window, _controller, _lib, _engine = qml_app
        dialog = _child(window, "renameManyDialog")
        QMetaObject.invokeMethod(
            dialog, "openFor", Qt.ConnectionType.DirectConnection,
            Q_ARG("QVariant", [0, 1]),
        )
        qt_app.processEvents()
        result = QMetaObject.invokeMethod(
            dialog, "acceptButtonText", Qt.ConnectionType.DirectConnection,
            Q_RETURN_ARG("QVariant"),
        )
        assert result == "Rename"

    def test_accept_renames_both_files_with_sequence(self, qml_app, qt_app):
        window, controller, lib, _engine = qml_app
        dialog = _child(window, "renameManyDialog")
        QMetaObject.invokeMethod(
            dialog, "openFor", Qt.ConnectionType.DirectConnection,
            Q_ARG("QVariant", [0, 1]),
        )
        qt_app.processEvents()
        field = _child(window, "renameManyField")
        field.setProperty("text", "nyaralas")
        loop = QEventLoop()
        controller.photoOpFinished.connect(loop.quit)
        QMetaObject.invokeMethod(dialog, "accept", Qt.ConnectionType.DirectConnection)
        QTimer.singleShot(5000, loop.quit)
        loop.exec()
        qt_app.processEvents()
        assert (lib / "nyaralas.jpg").exists()
        assert (lib / "nyaralas-1.jpg").exists()
        assert not (lib / "a.jpg").exists()
        assert not (lib / "b.jpg").exists()
        model_names = {photo.name for photo in controller.photos.photos}
        assert model_names == {"nyaralas.jpg", "nyaralas-1.jpg"}

    def test_empty_selection_does_not_open(self, qml_app, qt_app):
        window, _controller, _lib, _engine = qml_app
        dialog = _child(window, "renameManyDialog")
        QMetaObject.invokeMethod(
            dialog, "openFor", Qt.ConnectionType.DirectConnection,
            Q_ARG("QVariant", []),
        )
        qt_app.processEvents()
        assert dialog.property("visible") is False


class TestDeleteConfirmDialog:
    """#367: a törlés-megerősítés az általános ConfirmDialog komponensre
    állítva (confirm.fen paritás) — üzenet, "Don't ask again" jelölő,
    kulcs-alapú elnyomás."""

    def _open_delete(self, window, qt_app, paths):
        dialog = _child(window, "deleteConfirmDialog")
        QMetaObject.invokeMethod(
            dialog, "openFor", Qt.ConnectionType.DirectConnection,
            Q_ARG("QVariant", paths),
        )
        qt_app.processEvents()
        return dialog

    def test_opens_with_message_and_unchecked_remember(self, qml_app, qt_app, tmp_path):
        window, _controller, _lib, _engine = qml_app
        missing = str(tmp_path / "nincs.jpg")
        dialog = self._open_delete(window, qt_app, [missing])
        assert dialog.property("visible") is True
        message_label = _child(window, "confirmMessageLabel")
        assert "1" in message_label.property("text")
        remember = _child(window, "confirmRememberCheck")
        assert remember.property("checked") is False

    def test_cancel_closes_without_deleting(self, qml_app, qt_app, tmp_path):
        window, _controller, _lib, _engine = qml_app
        missing = str(tmp_path / "nincs.jpg")
        dialog = self._open_delete(window, qt_app, [missing])
        cancel_button = _child(window, "confirmCancelButton")
        QMetaObject.invokeMethod(
            cancel_button, "clicked", Qt.ConnectionType.DirectConnection
        )
        qt_app.processEvents()
        assert dialog.property("visible") is False

    def test_remember_then_yes_suppresses_next_open(self, qml_app, qt_app, tmp_path):
        window, _controller, _lib, _engine = qml_app
        missing = str(tmp_path / "nincs.jpg")
        dialog = self._open_delete(window, qt_app, [missing])
        remember = _child(window, "confirmRememberCheck")
        remember.setProperty("checked", True)
        QMetaObject.invokeMethod(dialog, "accept", Qt.ConnectionType.DirectConnection)
        qt_app.processEvents()
        assert dialog.property("visible") is False

        # ugyanaz a kulcs ("delete") legközelebb NEM nyit dialógust — az
        # alapértelmezett (Igen) válasz automatikusan lefut
        second_missing = str(tmp_path / "meg-egy-nincs.jpg")
        dialog2 = self._open_delete(window, qt_app, [second_missing])
        assert dialog2.property("visible") is False
        assert dialog2 is dialog

    def test_no_button_denies_without_remember_side_effect(self, qml_app, qt_app, tmp_path):
        window, _controller, _lib, _engine = qml_app
        missing = str(tmp_path / "nincs.jpg")
        dialog = self._open_delete(window, qt_app, [missing])
        no_button = _child(window, "confirmNoButton")
        QMetaObject.invokeMethod(
            no_button, "clicked", Qt.ConnectionType.DirectConnection
        )
        qt_app.processEvents()
        assert dialog.property("visible") is False
        # nem lett elnyomva — a kulcs újranyitná a dialógust
        dialog2 = self._open_delete(window, qt_app, [missing])
        assert dialog2.property("visible") is True


@pytest.mark.skipif(
    not hasattr(os, "getuid"),
    reason="A mount-specifikus lomtár freedesktop.org (POSIX) fogalom — "
    "Windowson a #457 előtti, home-trash viselkedés marad.",
)
class TestDeleteConfirmDialogNoTrashAvailable:
    """#457: NAS/hálózati meghajtón (nincs elérhető lomtár) a dialógus külön,
    hangsúlyos szöveggel figyelmeztet, hogy a törlés AZONNALI és VÉGLEGES —
    és `deletePhotoPermanently`-t hív a lomtáras `deletePhoto` helyett.

    A `trash.py` mount-határ-mockolásával szimuláljuk a NAS-esetet (nincs
    valódi másik fájlrendszer a tesztkonténerben), ugyanúgy, mint a
    `tests/fileops/test_trash.py`-ban."""

    def _open_delete(self, window, qt_app, paths):
        dialog = _child(window, "deleteConfirmDialog")
        QMetaObject.invokeMethod(
            dialog, "openFor", Qt.ConnectionType.DirectConnection,
            Q_ARG("QVariant", paths),
        )
        qt_app.processEvents()
        return dialog

    def _make_nas_unavailable(self, monkeypatch, tmp_path):
        topdir = tmp_path / "nas"
        topdir.mkdir()
        photo = topdir / "a.jpg"
        photo.write_bytes(b"kep")
        monkeypatch.setattr(
            "picasapy.fileops.trash._device_of",
            lambda p: 1 if str(p).startswith(str(topdir)) else 2,
        )
        monkeypatch.setattr("picasapy.fileops.trash._mount_point", lambda p: topdir)
        monkeypatch.setattr(
            "picasapy.fileops.trash.os.access", lambda path, mode: False
        )
        return photo

    def test_shows_the_permanent_delete_warning(
        self, qml_app, qt_app, monkeypatch, tmp_path
    ):
        window, _controller, _lib, _engine = qml_app
        photo = self._make_nas_unavailable(monkeypatch, tmp_path)
        dialog = self._open_delete(window, qt_app, [str(photo)])
        assert dialog.property("visible") is True
        message_label = _child(window, "confirmMessageLabel")
        text = message_label.property("text")
        assert "cannot be moved to the Trash" in text
        assert "cannot be undone" in text

    def test_confirming_deletes_permanently_not_via_trash(
        self, qml_app, qt_app, monkeypatch, tmp_path
    ):
        window, _controller, _lib, _engine = qml_app
        photo = self._make_nas_unavailable(monkeypatch, tmp_path)
        dialog = self._open_delete(window, qt_app, [str(photo)])
        QMetaObject.invokeMethod(dialog, "accept", Qt.ConnectionType.DirectConnection)
        qt_app.processEvents()
        assert not photo.exists()
        assert not (photo.parent / ".Trash-0" / "files" / "a.jpg").exists()
        assert not list(photo.parent.glob(".Trash*"))

    def test_normal_selection_still_shows_the_trash_message(
        self, qml_app, qt_app, tmp_path
    ):
        # kontroll: a mockolás nélküli, normál (home-fájlrendszeres)
        # kijelölésnél a lomtáras szöveg marad — a NAS-ág nem "ragad be"
        window, _controller, lib, _engine = qml_app
        photo = lib / "a.jpg"
        self._open_delete(window, qt_app, [str(photo)])
        message_label = _child(window, "confirmMessageLabel")
        assert "system trash" in message_label.property("text")


class TestMenuBarFileActions:
    def test_items_follow_selection(self, qml_app, qt_app):
        window, _controller, _lib, _engine = qml_app
        rename_item = _child(window, "menuFileRename")
        export_item = _child(window, "menuFileExport")
        window.setProperty("selectedIndexes", [])
        qt_app.processEvents()
        assert rename_item.property("enabled") is False
        assert export_item.property("enabled") is False
        _select_row(window, qt_app, 0)
        assert rename_item.property("enabled") is True
        assert export_item.property("enabled") is True


class TestExportDialog:
    def test_export_end_to_end(self, qml_app, qt_app, tmp_path):
        window, controller, _lib, _engine = qml_app
        _select_row(window, qt_app, 0)
        target = tmp_path / "export-cel"
        dialog = _child(window, "exportDialog")
        QMetaObject.invokeMethod(
            dialog, "openForSelection", Qt.ConnectionType.DirectConnection
        )
        qt_app.processEvents()
        assert dialog.property("visible") is True
        dialog.setProperty("targetFolder", target.as_uri())
        results = []
        loop = QEventLoop()
        controller.exportFinished.connect(
            lambda done, failed: results.append((done, failed))
        )
        controller.exportFinished.connect(loop.quit)
        QMetaObject.invokeMethod(dialog, "accept", Qt.ConnectionType.DirectConnection)
        QTimer.singleShot(5000, loop.quit)
        loop.exec()
        qt_app.processEvents()
        assert results == [(1, 0)]
        # #1166: az eredetiben a végleges útvonal `<hely>\<név>\` — a
        # névmező alapértéke a FORRÁSMAPPA neve (spec 12.1, `0x0073b500`),
        # ezért a kép a hely alatti, azonos nevű almappába kerül. Korábban
        # a mező üresen állt, és a kép közvetlenül a helyre került.
        nev = dialog.findChild(QObject, "exportFolderNameField").property("text")
        assert nev, "a névmező alapértéke üres maradt"
        assert (target / nev / "a.jpg").exists()
        # a visszajelző dialógus is megnyílt az exportFinished-re
        result_dialog = _child(window, "exportResultDialog")
        assert result_dialog.property("visible") is True

    def test_open_requires_selection(self, qml_app, qt_app):
        window, _controller, _lib, _engine = qml_app
        window.setProperty("selectedIndexes", [])
        dialog = _child(window, "exportDialog")
        QMetaObject.invokeMethod(
            dialog, "openForSelection", Qt.ConnectionType.DirectConnection
        )
        qt_app.processEvents()
        assert dialog.property("visible") is False


class TestExportDialogFenParity:
    """#350: export.fen paritás — cím és gombfelirat."""

    def test_title_matches_fen_wording(self, qml_app, qt_app):
        window, _controller, _lib, _engine = qml_app
        dialog = _child(window, "exportDialog")
        assert dialog.property("title") == "Export to Folder..."

    def test_accept_button_says_export_not_ok(self, qml_app, qt_app):
        window, _controller, _lib, _engine = qml_app
        _select_row(window, qt_app, 0)
        dialog = _child(window, "exportDialog")
        QMetaObject.invokeMethod(
            dialog, "openForSelection", Qt.ConnectionType.DirectConnection
        )
        qt_app.processEvents()
        result = QMetaObject.invokeMethod(
            dialog, "acceptButtonText", Qt.ConnectionType.DirectConnection,
            Q_RETURN_ARG("QVariant"),
        )
        assert result == "Export"


class TestTrayExportButton:
    def test_enabled_follows_selection(self, qml_app, qt_app):
        window, _controller, _lib, _engine = qml_app
        button = _child(window, "trayExportButton")
        window.setProperty("selectedIndexes", [])
        qt_app.processEvents()
        assert button.property("enabled") is False
        _select_row(window, qt_app, 0)
        assert button.property("enabled") is True


class TestCopyPasteEffectsMenu:
    """#426: „Az összes effektus másolása/beillesztése" — a Szerkesztés menü
    két tétele a `photo_ops_controller` kötegelt vágólap-motorját hívja
    (NEM a #152-es `effects_controller`-t, amely a kép-specifikus
    `crop64`-et is átvinné — ld. `docs/specs/filterdesc-registry.md`)."""

    def test_paste_disabled_until_copied_then_applies_to_selection(
        self, qml_app, qt_app
    ):
        window, controller, lib, _engine = qml_app
        # a.jpg-nek van effektlánca, b.jpg-nek nincs
        (lib / ".picasa.ini").write_text(
            "[a.jpg]\nfilters=BRIT=1,e50,0.20;\n", encoding="utf-8"
        )
        controller.resyncFolder(str(lib))
        loop = QEventLoop()
        controller.syncFinished.connect(loop.quit)
        QTimer.singleShot(5000, loop.quit)
        loop.exec()
        qt_app.processEvents()

        copy_item = _child(window, "menuEditCopyEffects")
        paste_item = _child(window, "menuEditPasteEffects")

        _select_row(window, qt_app, 0)  # a.jpg — a forrás
        assert paste_item.property("enabled") is False  # még nincs vágólap

        QMetaObject.invokeMethod(
            copy_item, "triggered", Qt.ConnectionType.DirectConnection
        )
        qt_app.processEvents()
        assert controller.hasAllEffectsClipboard is True

        _select_row(window, qt_app, 1)  # b.jpg — a cél
        assert paste_item.property("enabled") is True

        QMetaObject.invokeMethod(
            paste_item, "triggered", Qt.ConnectionType.DirectConnection
        )
        qt_app.processEvents()

        ini_text = (lib / ".picasa.ini").read_text(encoding="utf-8")
        assert "[b.jpg]" in ini_text
        assert "filters=BRIT=1,e50,0.20;" in ini_text.split("[b.jpg]")[1]

    def test_crop_and_redeye_are_not_transferred(self, qml_app, qt_app):
        """#426 elfogadási kritérium: a kivágás/vörösszem/retus régióhoz/
        képhez kötött, ezért az „Az összes effektus beillesztése" ezeket
        NEM viheti át — ellentétben a #152-es (Kép menü) korábbi
        motorjával, amely a crop64-et is átvinné."""
        window, controller, lib, _engine = qml_app
        (lib / ".picasa.ini").write_text(
            "[a.jpg]\n"
            "filters=enhance=1;crop64=1,45930000ba03defe;redeye=1;\n",
            encoding="utf-8",
        )
        controller.resyncFolder(str(lib))
        loop = QEventLoop()
        controller.syncFinished.connect(loop.quit)
        QTimer.singleShot(5000, loop.quit)
        loop.exec()
        qt_app.processEvents()

        copy_item = _child(window, "menuEditCopyEffects")
        paste_item = _child(window, "menuEditPasteEffects")

        _select_row(window, qt_app, 0)  # a.jpg — a forrás
        QMetaObject.invokeMethod(
            copy_item, "triggered", Qt.ConnectionType.DirectConnection
        )
        qt_app.processEvents()

        _select_row(window, qt_app, 1)  # b.jpg — a cél
        QMetaObject.invokeMethod(
            paste_item, "triggered", Qt.ConnectionType.DirectConnection
        )
        qt_app.processEvents()

        ini_text = (lib / ".picasa.ini").read_text(encoding="utf-8")
        b_block = ini_text.split("[b.jpg]")[1]
        assert "enhance=1" in b_block
        assert "crop64" not in b_block
        assert "redeye" not in b_block
