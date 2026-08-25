"""FileOpsController: fájlműveletek (átnevezés/áthelyezés/lomtár/fájlkezelő,
#15) QML-hídja — útvonal-alapú, az AppControllertől (forró fájl) független."""

import os
from pathlib import Path

import pytest

from picasapy.fileops import reveal


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


class TestDeletePhotoPermanently:
    """#457: NAS-on/hálózati meghajtón, ahol nincs elérhető lomtár, a
    végleges, azonnali törlésre külön slot — a `deletePhoto`-val
    ellentétben nem a lomtárba mozgat."""

    def test_emits_photo_deleted_and_removes_the_file(self, controller, tmp_path):
        photo = tmp_path / "a.jpg"
        photo.write_bytes(b"kep")
        events = []
        controller.photoDeleted.connect(lambda path: events.append(path))
        controller.deletePhotoPermanently(str(photo))
        assert events == [str(photo)]
        assert not photo.exists()

    def test_emits_operation_failed_on_missing_file(self, controller, tmp_path):
        failures = []
        controller.operationFailed.connect(
            lambda kind, msg: failures.append((kind, msg))
        )
        controller.deletePhotoPermanently(str(tmp_path / "nincs.jpg"))
        assert failures[0][0] == "delete"


@pytest.mark.skipif(
    not hasattr(os, "getuid"),
    reason="A mount-specifikus lomtár freedesktop.org (POSIX) fogalom — "
    "Windowson a #457 előtti, home-trash viselkedés marad.",
)
class TestTrashAvailableFor:
    """#457: kuka vs. végleges törlés megkülönböztetéséhez a QML-oldal ezzel
    dönti el, melyik szöveget/slotot használja."""

    def test_true_when_the_file_is_on_the_home_filesystem(
        self, controller, tmp_path, monkeypatch
    ):
        monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "xdg"))
        photo = tmp_path / "a.jpg"
        photo.write_bytes(b"kep")
        assert controller.trashAvailableFor([str(photo)]) is True

    def test_false_when_no_path_has_a_trash(self, controller, tmp_path, monkeypatch):
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
            "picasapy.fileops.trash._access", lambda path, mode: False
        )
        assert controller.trashAvailableFor([str(photo)]) is False

    def test_mixed_selection_is_false_the_stricter_branch_wins(
        self, controller, tmp_path, monkeypatch
    ):
        monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "xdg"))
        with_trash = tmp_path / "a.jpg"
        with_trash.write_bytes(b"kep")

        topdir = tmp_path / "nas"
        topdir.mkdir()
        without_trash = topdir / "b.jpg"
        without_trash.write_bytes(b"kep")

        def device_of(p):
            return 1 if str(p).startswith(str(topdir)) else 2

        monkeypatch.setattr("picasapy.fileops.trash._device_of", device_of)
        monkeypatch.setattr("picasapy.fileops.trash._mount_point", lambda p: topdir)
        monkeypatch.setattr(
            "picasapy.fileops.trash._access", lambda path, mode: False
        )

        assert (
            controller.trashAvailableFor([str(with_trash), str(without_trash)])
            is False
        )

    def test_empty_selection_is_true(self, controller):
        assert controller.trashAvailableFor([]) is True


class TestRevealPhoto:
    """#1104: ez az osztály a LINUX ágat írja le.

    ⚠️ A rögzítés SZŰK: modul-szinten `autouse`-ként a windows-CI-lábon
    mást tört el (a `sys.platform` linuxra állítása miatt egy másik teszt
    `os.uname()`-et hívott, ami Windowson nincs). A tanulság: a
    platform-hamisítás akkora hatókörű legyen, amekkorát tényleg állít.

    ⚠️ #1217: a fenti szivárgás OKA az volt, hogy a rögzítés a GLOBÁLIS
    `sys.platform`-ot írta át — a `picasapy.fileops.reveal.sys` maga a
    `sys` modul, tehát a csere minden más modulra is hatott. Most a
    `reveal` modul `_platform` fogantyúját cseréljük: a hatókör így már a
    MECHANIZMUSBÓL adódóan egyetlen modul, nem a fixture ügyességéből."""

    @pytest.fixture(autouse=True)
    def _linux(self, monkeypatch):
        monkeypatch.setattr(reveal, "_platform", lambda: "linux")

    def test_calls_xdg_open_on_parent_folder(self, controller, tmp_path, monkeypatch):
        calls = []

        class _CompletedProcess:
            returncode = 0

        monkeypatch.setattr(
            "picasapy.fileops.reveal._run",
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

        monkeypatch.setattr("picasapy.fileops.reveal._run", _raise)
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
            "picasapy.fileops.reveal._run",
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


class TestMegorzottEredeti1430:
    """#1430: a megőrzött eredeti a képpel költözik, és ha ez nem megy, a
    felhasználó ÉRTHETŐ üzenetet kap — nem néma elutasítást.

    **Melyik út melyik felületi gombhoz tartozik.** A `renamePhoto` az F2-es
    átnevezés valódi útja, és a hibája az `operationFailed`-en át a
    `fileOpsErrorDialog`-ba kerül szó szerint. A `movePhoto` viszont
    NEM felületi út: a „Move to Folder…" mindig a kötegelt `movePhotos`-t
    hívja (`Main.qml` → `openMove` → `startBatch("move")`), egyetlen kijelölt
    képnél is. Az egyfájlos slotot csak tesztek hívják — az áthelyezés
    felhasználói üzenetét ezért a KÖTEGELT úton kell mérni (lent), és a
    végső megjelenést a
    `tests/app/qml_functional/test_koteg_hibaok_1430.py` őrzi.
    """

    def test_atnevezes_viszi_az_eredetit(self, controller, tmp_path):
        photo = tmp_path / "a.jpg"
        photo.write_bytes(b"szerkesztett")
        originals = tmp_path / ".picasaoriginals"
        originals.mkdir()
        (originals / "a.jpg").write_bytes(b"eredeti")
        controller.renamePhoto(str(photo), "b.jpg")
        assert (originals / "b.jpg").read_bytes() == b"eredeti"

    def test_kotegelt_mozgatas_viszi_az_eredetit(self, controller, tmp_path):
        """A felület valódi áthelyezési útja (`movePhotos`)."""
        src = tmp_path / "forras"
        dest = tmp_path / "cel"
        src.mkdir()
        dest.mkdir()
        photo = src / "a.jpg"
        photo.write_bytes(b"szerkesztett")
        originals = src / ".picasaoriginals"
        originals.mkdir()
        (originals / "a.jpg").write_bytes(b"eredeti")
        controller.movePhotos([str(photo)], str(dest), "rename")
        assert (dest / ".picasaoriginals" / "a.jpg").read_bytes() == b"eredeti"

    def test_egyfajlos_slot_is_viszi_az_eredetit(self, controller, tmp_path):
        """A `movePhoto` slotnak ma nincs QML-hívója, de programozói felület
        (és a `dedup_controller` is a magját hívja) — maradjon helyes."""
        src = tmp_path / "forras"
        dest = tmp_path / "cel"
        src.mkdir()
        dest.mkdir()
        photo = src / "a.jpg"
        photo.write_bytes(b"szerkesztett")
        originals = src / ".picasaoriginals"
        originals.mkdir()
        (originals / "a.jpg").write_bytes(b"eredeti")
        controller.movePhoto(str(photo), str(dest))
        assert (dest / ".picasaoriginals" / "a.jpg").read_bytes() == b"eredeti"

    def test_atnevezesnel_az_ok_az_operation_failedre_megy(
        self, controller, tmp_path
    ):
        photo = tmp_path / "a.jpg"
        photo.write_bytes(b"szerkesztett")
        originals = tmp_path / ".picasaoriginals"
        originals.mkdir()
        (originals / "a.1.jpg").write_bytes(b"pillanatkep")
        (originals / "b.1.jpg").write_bytes(b"utban-van")

        failures = []
        controller.operationFailed.connect(
            lambda kind, msg: failures.append((kind, msg))
        )
        controller.renamePhoto(str(photo), "b.jpg")

        assert failures, "a felhasználó semmilyen visszajelzést nem kapott"
        kind, message = failures[0]
        assert kind == "rename"
        assert "eredeti" in message.lower()
        assert str(originals / "b.1.jpg") in message
        assert "Semmi nem változott" in message
        assert photo.exists()

    def test_kotegelt_mozgatasnal_az_ok_a_batch_osszegzesbe_megy(
        self, controller, tmp_path
    ):
        """#1430 kódszemle, 1. blokkoló: a kötegelt út eddig csak a
        DARABSZÁMOT jelentette, az okot eldobta — így az áthelyezés
        magyarázó üzenete sosem jutott el a felhasználóhoz."""
        src = tmp_path / "forras"
        dest = tmp_path / "cel"
        src.mkdir()
        dest.mkdir()
        photo = src / "a.jpg"
        photo.write_bytes(b"szerkesztett")
        (src / ".picasaoriginals").mkdir()
        (src / ".picasaoriginals" / "a.1.jpg").write_bytes(b"pillanatkep")
        # a célban egy ÉLŐ kép birtokolja ugyanazt a helyet
        (dest / "a.1.jpg").write_bytes(b"masik-elo-kep")
        (dest / ".picasaoriginals").mkdir()
        (dest / ".picasaoriginals" / "a.1.jpg").write_bytes(b"masik-kep-eredetije")

        summary = []
        controller.batchFinished.connect(lambda *args: summary.append(tuple(args)))
        controller.movePhotos([str(photo)], str(dest), "rename")

        assert summary, "a köteg nem jelentett semmit"
        operation, done, skipped, failed, reason = summary[0]
        assert (operation, done, failed) == ("move", 0, 1)
        assert reason.startswith("a.jpg: "), "a bukott fájl neve hiányzik"
        assert "eredeti" in reason.lower(), "a bukás OKA nem megy ki"
        assert "NE törölje" in reason, (
            "a másik kép eredetijének törlését nem szabad tanácsolni"
        )
        assert photo.exists()
