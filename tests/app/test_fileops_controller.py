"""FileOpsController: fájlműveletek (átnevezés/áthelyezés/lomtár/fájlkezelő,
#15) QML-hídja — útvonal-alapú, az AppControllertől (forró fájl) független."""

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
        monkeypatch.setattr(
            "picasapy.fileops.reveal.subprocess.run",
            lambda args, **kwargs: calls.append(args),
        )
        photo = tmp_path / "a.jpg"
        controller.revealPhoto(str(photo))
        assert calls == [["xdg-open", str(tmp_path)]]
