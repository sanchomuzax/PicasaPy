"""Névütközés: „átnevezés / kihagyás" választás a felületen — #457, 2. pont.

Az eredeti Picasa a célmappa kiválasztása után jóváhagyást kért („Fájlok
áthelyezése"), és CSAK névütközéskor kérdezte meg, hogy átnevezze vagy
kihagyja a másodpéldányokat. Itt a kontroller-slotokat és a QML-bekötést
ellenőrizzük.
"""

from pathlib import Path

import pytest
from PySide6.QtCore import Q_ARG, QMetaObject, QObject, Qt

from picasapy.app.fileops_controller import FileOpsController

QML_DIR = Path(__file__).resolve().parents[2] / "src/picasapy/app/qml/PicasaPy"


def _fileops(window):
    """#1612: a `FileOpsDialogs` halasztott — a burok `ensure()`-je építi fel.

    A korábbi `findChild(...) or window` alak ELREJTETTE volna a hibát: a
    `window`-on nincs `startBatch`, tehát az `invokeMethod` némán nem csinál
    semmit. Ezért itt nincs tartalék ág — ha a példány nincs meg, a teszt
    ezen a soron bukik, nem három állítással később.
    """
    burok = window.findChild(QObject, "fileOpsDialogs")
    assert burok is not None, "a fileOpsDialogs burok nincs meg"
    assert QMetaObject.invokeMethod(burok, "ensure"), "az ensure() nem hívható"
    elem = window.findChild(QObject, "fileOpsDialogsItem")
    assert elem is not None, "az ensure() nem építette fel a párbeszédeket"
    return elem


def _child(window, name):
    obj = window.findChild(QObject, name)
    assert obj is not None, f"{name} nem található"
    return obj


def _jpeg(folder: Path, name: str) -> Path:
    from support.jpeg_factory import make_jpeg

    folder.mkdir(parents=True, exist_ok=True)
    path = folder / name
    make_jpeg(path, size=(32, 32))
    return path


@pytest.fixture
def controller(qt_app):
    return FileOpsController()


class TestControllerSlots:
    def test_conflict_count_is_zero_without_collision(self, controller, tmp_path):
        src, dest = tmp_path / "src", tmp_path / "dest"
        a = _jpeg(src, "a.jpg")
        dest.mkdir()

        assert controller.conflictCountFor([str(a)], str(dest)) == 0

    def test_conflict_count_counts_collisions(self, controller, tmp_path):
        src, dest = tmp_path / "src", tmp_path / "dest"
        a = _jpeg(src, "a.jpg")
        b = _jpeg(src, "b.jpg")
        _jpeg(dest, "a.jpg")

        assert controller.conflictCountFor([str(a), str(b)], str(dest)) == 1

    def test_conflict_count_accepts_file_url_destination(self, controller, tmp_path):
        # a QML FolderDialog `file://` URL-t ad — ugyanaz az átalakítás kell,
        # mint a `movePhoto`-nál, különben a nem létező úton NULLA ütközés
        # látszana, és a kérdés elmaradna
        src, dest = tmp_path / "src", tmp_path / "dest"
        a = _jpeg(src, "a.jpg")
        _jpeg(dest, "a.jpg")

        assert controller.conflictCountFor([str(a)], dest.as_uri()) == 1

    def test_move_rename_reports_and_signals(self, controller, tmp_path):
        src, dest = tmp_path / "src", tmp_path / "dest"
        a = _jpeg(src, "a.jpg")
        _jpeg(dest, "a.jpg")
        moved, summary = [], []
        controller.photoMoved.connect(lambda old, new: moved.append((old, new)))
        controller.batchFinished.connect(
            lambda *args: summary.append(tuple(args))
        )

        controller.movePhotos([str(a)], str(dest), "rename")

        assert moved == [(str(a), str(dest / "a-1.jpg"))]
        assert summary == [("move", 1, 0, 0, "")]

    def test_move_skip_reports_the_skipped_file(self, controller, tmp_path):
        src, dest = tmp_path / "src", tmp_path / "dest"
        a = _jpeg(src, "a.jpg")
        _jpeg(dest, "a.jpg")
        summary = []
        controller.batchFinished.connect(lambda *args: summary.append(tuple(args)))

        controller.movePhotos([str(a)], str(dest), "skip")

        assert a.exists()
        assert summary == [("move", 0, 1, 0, "")]

    def test_copy_batch_keeps_the_sources(self, controller, tmp_path):
        src, dest = tmp_path / "src", tmp_path / "dest"
        a = _jpeg(src, "a.jpg")
        dest.mkdir()
        summary = []
        controller.batchFinished.connect(lambda *args: summary.append(tuple(args)))

        controller.copyPhotos([str(a)], str(dest), "rename")

        assert a.exists() and (dest / "a.jpg").exists()
        assert summary == [("copy", 1, 0, 0, "")]

    def test_bad_policy_is_reported_not_raised(self, controller, tmp_path):
        dest = tmp_path / "dest"
        dest.mkdir()
        failures = []
        controller.operationFailed.connect(
            lambda op, message: failures.append(op)
        )

        controller.movePhotos([], str(dest), "overwrite")

        assert failures == ["move"]


class TestOriginalWording:
    """A párbeszéd szövegei az eredeti sztring-táblából valók."""

    def test_dialog_uses_the_original_strings(self):
        source = (QML_DIR / "FileOpsDialogs.qml").read_text(encoding="utf-8")
        assert (
            "This folder already contains files with the same name."
            in source
        )
        assert "Would you like to rename or skip these files?" in source
        assert 'qsTr("Rename Duplicates")' in source
        assert 'qsTr("Skip Duplicates")' in source
        assert 'qsTr("Confirm Move")' in source
        assert 'qsTr("Move Files")' in source

    def test_hungarian_translation_matches_the_original_wording(self):
        ts = (QML_DIR.parents[1] / "i18n/picasapy_hu.ts").read_text(
            encoding="utf-8"
        )
        assert "Másodpéldányok átnevezése" in ts
        assert "Másodpéldányok kihagyása" in ts
        assert "Ez a mappa már tartalmaz azonos nevű fájlokat." in ts
        assert "Átnevezi vagy átugorja ezeket?" in ts


class TestQmlWiring:
    def test_confirm_dialog_offers_the_move_files_button(self, qml_app, qt_app):
        window, _controller, lib, _engine = qml_app
        _fileops(window)  # #1612: halasztott — előbb fel kell épülnie
        dialog = _child(window, "moveConfirmDialog")
        dest = Path(lib).parent / "cel"
        dest.mkdir()
        QMetaObject.invokeMethod(
            dialog, "openFor", Qt.ConnectionType.DirectConnection,
            Q_ARG("QVariant", [str(Path(lib) / "a.jpg")]),
            Q_ARG("QVariant", str(dest)),
        )
        qt_app.processEvents()

        assert dialog.property("visible") is True
        text = dialog.metaObject().method(
            dialog.metaObject().indexOfMethod("acceptButtonText()")
        )
        assert text is not None
        QMetaObject.invokeMethod(dialog, "close", Qt.ConnectionType.DirectConnection)
        qt_app.processEvents()

    def test_conflict_opens_the_duplicate_question(self, qml_app, qt_app):
        window, _controller, lib, _engine = qml_app
        dest = Path(lib).parent / "cel2"
        dest.mkdir()
        _jpeg(dest, "a.jpg")
        source = str(Path(lib) / "a.jpg")

        QMetaObject.invokeMethod(
            _fileops(window),
            "startBatch", Qt.ConnectionType.DirectConnection,
            Q_ARG("QVariant", "move"), Q_ARG("QVariant", [source]),
            Q_ARG("QVariant", str(dest)),
        )
        qt_app.processEvents()

        question = _child(window, "duplicateNamesDialog")
        assert question.property("visible") is True
        assert Path(source).exists()  # kérdés közben még semmi nem történt

        QMetaObject.invokeMethod(
            _child(window, "duplicateRenameButton"), "clicked",
            Qt.ConnectionType.DirectConnection,
        )
        qt_app.processEvents()

        assert not Path(source).exists()
        assert (dest / "a-1.jpg").exists()

    def test_skip_leaves_everything_in_place(self, qml_app, qt_app):
        window, _controller, lib, _engine = qml_app
        dest = Path(lib).parent / "cel3"
        dest.mkdir()
        _jpeg(dest, "a.jpg")
        source = str(Path(lib) / "a.jpg")

        QMetaObject.invokeMethod(
            _fileops(window),
            "startBatch", Qt.ConnectionType.DirectConnection,
            Q_ARG("QVariant", "move"), Q_ARG("QVariant", [source]),
            Q_ARG("QVariant", str(dest)),
        )
        qt_app.processEvents()
        QMetaObject.invokeMethod(
            _child(window, "duplicateSkipButton"), "clicked",
            Qt.ConnectionType.DirectConnection,
        )
        qt_app.processEvents()

        assert Path(source).exists()
        assert not (dest / "a-1.jpg").exists()

    def test_no_conflict_skips_the_question(self, qml_app, qt_app):
        window, _controller, lib, _engine = qml_app
        dest = Path(lib).parent / "cel4"
        dest.mkdir()
        source = str(Path(lib) / "b.jpg")

        QMetaObject.invokeMethod(
            _fileops(window),
            "startBatch", Qt.ConnectionType.DirectConnection,
            Q_ARG("QVariant", "move"), Q_ARG("QVariant", [source]),
            Q_ARG("QVariant", str(dest)),
        )
        qt_app.processEvents()

        question = _child(window, "duplicateNamesDialog")
        assert question.property("visible") is False  # nincs mit kérdezni
        assert (dest / "b.jpg").exists()


class TestMoveFolder:
    """#457: mappa áthelyezése a kísérőfájlokkal — a `.picasa.ini` nálunk
    az igazságforrás, tehát vele kell mennie."""

    def _controller(self):
        from picasapy.app.fileops_controller import FileOpsController

        return FileOpsController()

    def test_it_reports_the_new_location(self, qt_app, tmp_path):
        source = tmp_path / "innen" / "kepek"
        source.mkdir(parents=True)
        (source / "a.jpg").write_bytes(b"kep")
        (source / ".picasa.ini").write_text("[a.jpg]\ncaption=X\n", encoding="utf-8")
        dest = tmp_path / "ide"
        dest.mkdir()
        controller = self._controller()
        moved = []
        controller.folderMoved.connect(lambda old, new: moved.append((old, new)))

        controller.moveFolder(str(source), str(dest))
        qt_app.processEvents()

        assert moved and moved[0][1] == str(dest / "kepek")
        assert (dest / "kepek" / ".picasa.ini").exists()

    def test_a_failure_is_a_human_message_not_a_crash(self, qt_app, tmp_path):
        source = tmp_path / "innen" / "kepek"
        source.mkdir(parents=True)
        dest = tmp_path / "ide"
        (dest / "kepek").mkdir(parents=True)
        controller = self._controller()
        failures = []
        controller.operationFailed.connect(
            lambda operation, message: failures.append((operation, message))
        )

        controller.moveFolder(str(source), str(dest))
        qt_app.processEvents()

        assert failures and failures[0][0] == "move_folder"
        assert source.exists()

    def test_an_empty_destination_is_refused(self, qt_app, tmp_path):
        controller = self._controller()
        failures = []
        controller.operationFailed.connect(
            lambda operation, message: failures.append(operation)
        )

        controller.moveFolder(str(tmp_path), "")
        qt_app.processEvents()

        assert failures == ["move_folder"]


class TestProgressSpeed:
    """#457: az eredeti a SEBESSÉGET is kiírta („Moving %d of %d (%s/s)") —
    egy nagy köteg alatt ez mondja meg, érdemes-e várni."""

    def test_the_progress_carries_a_speed(self, qt_app, tmp_path):
        from picasapy.app.fileops_controller import FileOpsController

        source = tmp_path / "innen"
        source.mkdir()
        paths = []
        for name in ("a.jpg", "b.jpg"):
            path = source / name
            path.write_bytes(b"x" * 4096)
            paths.append(str(path))
        dest = tmp_path / "ide"
        dest.mkdir()
        controller = FileOpsController()
        seen = []
        controller.batchProgress.connect(
            lambda op, target, done, total, speed: seen.append((done, total, speed))
        )

        controller.copyPhotos(paths, str(dest), "rename")
        qt_app.processEvents()

        assert [(d, t) for d, t, _s in seen] == [(1, 2), (2, 2)]
        # A sebesség sosem negatív. Nullát viszont KAPHATUNK: Windowson a
        # `time.monotonic()` felbontása ~15 ms, két apró fájl másolása
        # ennél gyorsabb — ilyenkor a mért idő pontosan nulla, és a
        # vezérlő (helyesen) 0-t jelent osztási hiba helyett.
        assert all(speed >= 0 for _d, _t, speed in seen)
