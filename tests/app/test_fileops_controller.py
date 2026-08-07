"""FileOpsController: fájlműveletek (átnevezés/áthelyezés/lomtár/fájlkezelő,
#15) QML-hídja — útvonal-alapú, az AppControllertől (forró fájl) független."""

from pathlib import Path

import pytest


@pytest.fixture
def controller(qt_app):
    from picasapy.app.fileops_controller import FileOpsController

    return FileOpsController()


class TestRenamePhoto:
    def test_emits_photo_renamed_on_success(self, controller, tmp_path):
        photo = tmp_path / "a.jpg"
        photo.write_bytes(b"kep")
        events = []
        controller.photoRenamed.connect(lambda old, new: events.append((old, new)))
        controller.renamePhoto(str(photo), "b.jpg")
        assert events == [(str(photo), str(tmp_path / "b.jpg"))]
        assert (tmp_path / "b.jpg").exists()

    def test_emits_operation_failed_on_collision(self, controller, tmp_path):
        photo = tmp_path / "a.jpg"
        photo.write_bytes(b"kep")
        (tmp_path / "b.jpg").write_bytes(b"mar-van")
        failures = []
        controller.operationFailed.connect(
            lambda kind, msg: failures.append((kind, msg))
        )
        controller.renamePhoto(str(photo), "b.jpg")
        assert failures[0][0] == "rename"
        assert photo.exists()  # nem történt semmi

    def test_emits_operation_failed_on_invalid_name(self, controller, tmp_path):
        photo = tmp_path / "a.jpg"
        photo.write_bytes(b"kep")
        failures = []
        controller.operationFailed.connect(
            lambda kind, msg: failures.append((kind, msg))
        )
        controller.renamePhoto(str(photo), "al/könyvtár.jpg")
        assert failures[0][0] == "rename"


class TestMovePhoto:
    def test_emits_photo_moved_on_success(self, controller, tmp_path):
        src = tmp_path / "forras"
        dest = tmp_path / "cel"
        src.mkdir()
        dest.mkdir()
        photo = src / "a.jpg"
        photo.write_bytes(b"kep")
        events = []
        controller.photoMoved.connect(lambda old, new: events.append((old, new)))
        controller.movePhoto(str(photo), str(dest))
        assert events == [(str(photo), str(dest / "a.jpg"))]

    def test_emits_operation_failed_on_missing_dest(self, controller, tmp_path):
        photo = tmp_path / "a.jpg"
        photo.write_bytes(b"kep")
        failures = []
        controller.operationFailed.connect(
            lambda kind, msg: failures.append((kind, msg))
        )
        controller.movePhoto(str(photo), str(tmp_path / "nincs-mappa"))
        assert failures[0][0] == "move"


class TestDeletePhoto:
    def test_emits_photo_deleted_on_success(self, controller, tmp_path, monkeypatch):
        monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "xdg"))
        photo = tmp_path / "a.jpg"
        photo.write_bytes(b"kep")
        events = []
        controller.photoDeleted.connect(lambda path: events.append(path))
        controller.deletePhoto(str(photo))
        assert events == [str(photo)]
        assert not photo.exists()

    def test_emits_operation_failed_on_missing_file(self, controller, tmp_path):
        failures = []
        controller.operationFailed.connect(
            lambda kind, msg: failures.append((kind, msg))
        )
        controller.deletePhoto(str(tmp_path / "nincs.jpg"))
        assert failures[0][0] == "delete"


class TestRevealPhoto:
    def test_calls_xdg_open_on_parent_folder(self, controller, tmp_path, monkeypatch):
        calls = []

        class _CompletedProcess:
            returncode = 0

        monkeypatch.setattr(
            "picasapy.fileops.reveal.subprocess.run",
            lambda args, **kwargs: calls.append(args) or _CompletedProcess(),
        )
        photo = tmp_path / "a.jpg"
        controller.revealPhoto(str(photo))
        assert calls == [["xdg-open", str(tmp_path)]]

    def test_emits_operation_failed_on_missing_xdg_open(
        self, controller, tmp_path, monkeypatch
    ):
        def _raise(*_args, **_kwargs):
            raise FileNotFoundError("xdg-open nincs telepítve")

        monkeypatch.setattr("picasapy.fileops.reveal.subprocess.run", _raise)
        failures = []
        controller.operationFailed.connect(
            lambda kind, msg: failures.append((kind, msg))
        )
        controller.revealPhoto(str(tmp_path / "a.jpg"))
        assert failures[0][0] == "reveal"

    def test_emits_operation_failed_on_nonzero_exit(
        self, controller, tmp_path, monkeypatch
    ):
        class _CompletedProcess:
            returncode = 1

        monkeypatch.setattr(
            "picasapy.fileops.reveal.subprocess.run",
            lambda args, **kwargs: _CompletedProcess(),
        )
        failures = []
        controller.operationFailed.connect(
            lambda kind, msg: failures.append((kind, msg))
        )
        controller.revealPhoto(str(tmp_path / "a.jpg"))
        assert failures[0][0] == "reveal"


class TestOpenPhoto:
    """#422: „Fájl megnyitása" a néző kontextusmenüjéből — a `revealPhoto`
    párja: az a fájlkezelőt nyitja, ez a társított alkalmazást."""

    def test_opens_the_file_itself_with_the_associated_app(
        self, controller, tmp_path, monkeypatch
    ):
        opened = []
        monkeypatch.setattr(
            "picasapy.app.fileops_controller.QDesktopServices.openUrl",
            lambda url: opened.append(url.toLocalFile()) or True,
        )
        photo = tmp_path / "a.jpg"
        photo.write_bytes(b"\xff\xd8\xff\xe0" + b"0" * 50)
        controller.openPhoto(str(photo))
        # `QUrl.toLocalFile()` Windowson per-jeles utat ad (C:/…), a
        # `str(Path)` viszont visszaperjeleset — a két alak ugyanaz a fájl,
        # ezért Path-ként hasonlítunk (ld. formatting.to_local_path)
        assert [Path(p) for p in opened] == [photo]

    def test_emits_operation_failed_for_a_missing_file(self, controller, tmp_path):
        failures = []
        controller.operationFailed.connect(
            lambda kind, msg: failures.append((kind, msg))
        )
        controller.openPhoto(str(tmp_path / "nincs.jpg"))
        assert failures[0][0] == "open"

    def test_emits_operation_failed_when_the_desktop_refuses(
        self, controller, tmp_path, monkeypatch
    ):
        monkeypatch.setattr(
            "picasapy.app.fileops_controller.QDesktopServices.openUrl",
            lambda url: False,
        )
        photo = tmp_path / "a.jpg"
        photo.write_bytes(b"\xff\xd8\xff\xe0" + b"0" * 50)
        failures = []
        controller.operationFailed.connect(
            lambda kind, msg: failures.append((kind, msg))
        )
        controller.openPhoto(str(photo))
        assert failures[0][0] == "open"


class TestCopyFullPath:
    """#422: „Teljes elérési út másolása" — a vágólapra kerül a helyi út."""

    def test_puts_the_local_path_on_the_clipboard(self, controller, tmp_path, qt_app):
        from PySide6.QtGui import QGuiApplication

        photo = tmp_path / "a.jpg"
        controller.copyFullPath(str(photo))
        clipboard = QGuiApplication.clipboard()
        if clipboard is None:  # fej nélküli környezet — nincs mit ellenőrizni
            return
        assert clipboard.text() == str(photo)

    def test_accepts_a_file_url_too(self, controller, tmp_path, qt_app):
        """A QML `filePathAt` `file://` URL-t is adhat — a helyi útra
        fordítás a `_to_local_path` dolga, ahogy a többi slotnál."""
        from PySide6.QtGui import QGuiApplication

        photo = tmp_path / "a.jpg"
        controller.copyFullPath(photo.as_uri())
        clipboard = QGuiApplication.clipboard()
        if clipboard is None:
            return
        assert clipboard.text() == str(photo)

    def test_empty_path_is_a_no_op(self, controller):
        controller.copyFullPath("")  # nem dobhat


class TestIniConflictReachesUser:
    """#295: az ini-ütközés (párhuzamosan futó eredeti Picasa) nem `OSError` —
    a korábbi szűrő mellett kezeletlen kivételként, néma bukásként tűnt volna
    el a QML felé. A felhasználó a megszokott `operationFailed` csatornán
    kapjon jelzést."""

    @pytest.fixture
    def failing_ini_write(self, monkeypatch):
        from picasapy.fileops import move as move_module
        from picasapy.fileops import rename as rename_module
        from picasapy.ini import IniConflictError

        def raise_conflict(path, mutate, **kwargs):
            raise IniConflictError("teszt: tartós ütközés")

        monkeypatch.setattr(move_module, "update_document", raise_conflict)
        monkeypatch.setattr(rename_module, "update_document", raise_conflict)

    def test_rename_reports_ini_conflict(
        self, controller, tmp_path, failing_ini_write
    ):
        photo = tmp_path / "a.jpg"
        photo.write_bytes(b"kep")
        (tmp_path / ".picasa.ini").write_text("[a.jpg]\nstar=yes\n", encoding="utf-8")
        failures = []
        controller.operationFailed.connect(
            lambda kind, msg: failures.append((kind, msg))
        )
        controller.renamePhoto(str(photo), "b.jpg")
        assert failures[0][0] == "rename"
        assert "ütközés" in failures[0][1]

    def test_move_reports_ini_conflict(self, controller, tmp_path, failing_ini_write):
        src = tmp_path / "forras"
        dest = tmp_path / "cel"
        src.mkdir()
        dest.mkdir()
        photo = src / "a.jpg"
        photo.write_bytes(b"kep")
        (src / ".picasa.ini").write_text("[a.jpg]\nstar=yes\n", encoding="utf-8")
        failures = []
        controller.operationFailed.connect(
            lambda kind, msg: failures.append((kind, msg))
        )
        controller.movePhoto(str(photo), str(dest))
        assert failures[0][0] == "move"
        assert str(src / ".picasa.ini") in failures[0][1]
