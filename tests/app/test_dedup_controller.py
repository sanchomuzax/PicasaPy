"""DedupController: a duplikátum-kezelő ablak (#287) QML-hídja a
`picasapy.dedup.find_duplicates` mag fölött — valódi ideiglenes
könyvtárfán/indexen, mock nélkül."""

from __future__ import annotations

import numpy as np
import pytest
from PIL import Image
from PySide6.QtCore import QEventLoop, QTimer

from picasapy.index import open_index, sync_tree
from picasapy.thumbs import ThumbnailCache

from support.jpeg_factory import make_jpeg


def _quit_on(signal):
    loop = QEventLoop()
    signal.connect(loop.quit)
    QTimer.singleShot(5000, loop.quit)
    return loop


def _gradient_jpeg(path, size=(64, 64)):
    """Folytonos szürkeárnyalatos színátmenet — a dHash-nek van mit
    megkülönböztetnie (a sima, egyszínű teszt-JPEG-ekkel ellentétben)."""
    width, height = size
    xs = np.linspace(0, 255, width, dtype=np.uint8)
    ys = np.linspace(0, 255, height, dtype=np.uint8)
    ramp = (xs[np.newaxis, :].astype(np.uint16) + ys[:, np.newaxis]) // 2
    rgb = np.stack([ramp] * 3, axis=-1).astype(np.uint8)
    Image.fromarray(rgb, "RGB").save(path, "JPEG", quality=90)
    return path


def _resaved_jpeg(source_path, target_path, size=(24, 24), quality=60):
    """A forrás átméretezve/újratömörítve — "hasonló, de nem bitre azonos"."""
    with Image.open(source_path) as image:
        image.resize(size, Image.BICUBIC).save(target_path, "JPEG", quality=quality)
    return target_path


@pytest.fixture
def provider(tmp_path):
    from picasapy.app.thumbnail_provider import ThumbnailProvider

    return ThumbnailProvider(ThumbnailCache(tmp_path / "thumbs", size=32))


@pytest.fixture
def controller(qt_app, tmp_path, provider):
    from picasapy.app.dedup_controller import DedupController

    return DedupController(tmp_path / "index.db", provider)


class TestScanForDuplicates:
    def test_finds_exact_duplicate_group_with_thumb_urls(
        self, qt_app, tmp_path, provider
    ):
        from picasapy.app.dedup_controller import DedupController

        lib = tmp_path / "kepek"
        lib.mkdir()
        original = make_jpeg(lib / "a.jpg", size=(40, 20))
        (lib / "b.jpg").write_bytes(original.read_bytes())
        db = tmp_path / "index.db"
        with open_index(db) as conn:
            sync_tree(conn, lib)

        dedup = DedupController(db, provider)
        results = []
        dedup.scanFinished.connect(lambda groups: results.append(groups))
        loop = _quit_on(dedup.scanFinished)
        dedup.scanForDuplicates()
        loop.exec()

        assert len(results) == 1
        groups = results[0]
        assert isinstance(groups, list)
        exact = [g for g in groups if g["kind"] == "exact"]
        assert len(exact) == 1
        paths = {item["path"] for item in exact[0]["items"]}
        assert paths == {str(lib / "a.jpg"), str(lib / "b.jpg")}
        for item in exact[0]["items"]:
            assert item["thumbUrl"].startswith("image://thumbs/")
            assert item["thumbUrl"] != "image://thumbs/"

    def test_finds_similar_group_for_resized_variant(self, qt_app, tmp_path, provider):
        from picasapy.app.dedup_controller import DedupController

        lib = tmp_path / "kepek"
        lib.mkdir()
        _gradient_jpeg(lib / "eredeti.jpg", size=(256, 256))
        _resaved_jpeg(lib / "eredeti.jpg", lib / "atmeretezett.jpg")
        db = tmp_path / "index.db"
        with open_index(db) as conn:
            sync_tree(conn, lib)

        dedup = DedupController(db, provider)
        results = []
        dedup.scanFinished.connect(lambda groups: results.append(groups))
        loop = _quit_on(dedup.scanFinished)
        dedup.scanForDuplicates()
        loop.exec()

        groups = results[0]
        similar = [g for g in groups if g["kind"] == "similar"]
        assert len(similar) == 1
        assert similar[0]["maxDistance"] >= 0
        paths = {item["path"] for item in similar[0]["items"]}
        assert paths == {str(lib / "eredeti.jpg"), str(lib / "atmeretezett.jpg")}

    def test_no_duplicates_yields_empty_list(self, qt_app, tmp_path, provider):
        from picasapy.app.dedup_controller import DedupController

        lib = tmp_path / "kepek"
        lib.mkdir()
        make_jpeg(lib / "egyedi.jpg", size=(40, 20))
        db = tmp_path / "index.db"
        with open_index(db) as conn:
            sync_tree(conn, lib)

        dedup = DedupController(db, provider)
        results = []
        dedup.scanFinished.connect(lambda groups: results.append(groups))
        loop = _quit_on(dedup.scanFinished)
        dedup.scanForDuplicates()
        loop.exec()

        assert results == [[]]

    def test_groups_and_items_are_plain_lists_not_tuples(
        self, qt_app, tmp_path, provider
    ):
        """QML-nek adott adat mindig `list` legyen, soha `tuple` (a projekt
        szabálya) — enélkül a QML-oldali `.length` undefined lenne."""
        from picasapy.app.dedup_controller import DedupController

        lib = tmp_path / "kepek"
        lib.mkdir()
        original = make_jpeg(lib / "a.jpg", size=(40, 20))
        (lib / "b.jpg").write_bytes(original.read_bytes())
        db = tmp_path / "index.db"
        with open_index(db) as conn:
            sync_tree(conn, lib)

        dedup = DedupController(db, provider)
        results = []
        dedup.scanFinished.connect(lambda groups: results.append(groups))
        loop = _quit_on(dedup.scanFinished)
        dedup.scanForDuplicates()
        loop.exec()

        groups = results[0]
        assert isinstance(groups, list)
        for group in groups:
            assert isinstance(group["items"], list)
            for item in group["items"]:
                assert isinstance(item, dict)

    def test_scan_started_emitted_before_finished(self, qt_app, tmp_path, provider):
        from picasapy.app.dedup_controller import DedupController

        lib = tmp_path / "kepek"
        lib.mkdir()
        make_jpeg(lib / "a.jpg", size=(40, 20))
        db = tmp_path / "index.db"
        with open_index(db) as conn:
            sync_tree(conn, lib)

        dedup = DedupController(db, provider)
        events = []
        dedup.scanStarted.connect(lambda: events.append("started"))
        dedup.scanFinished.connect(lambda groups: events.append("finished"))
        loop = _quit_on(dedup.scanFinished)
        dedup.scanForDuplicates()
        loop.exec()

        assert events == ["started", "finished"]


class TestMoveOthersToDuplicatesFolder:
    def test_moves_every_item_except_keep_into_subfolder(self, controller, tmp_path):
        lib = tmp_path / "kepek"
        lib.mkdir()
        keep = make_jpeg(lib / "keep.jpg", size=(40, 20))
        other = tmp_path / "kepek" / "masolat.jpg"
        other.write_bytes(keep.read_bytes())

        resolved = []
        controller.itemResolved.connect(lambda path: resolved.append(path))
        controller.moveOthersToDuplicatesFolder([str(keep), str(other)], str(keep))

        assert keep.exists()
        assert not other.exists()
        moved = lib / "Duplikátumok" / "masolat.jpg"
        assert moved.exists()
        assert resolved == [str(other)]

    def test_keep_path_is_never_touched(self, controller, tmp_path):
        lib = tmp_path / "kepek"
        lib.mkdir()
        keep = make_jpeg(lib / "keep.jpg", size=(40, 20))

        controller.moveOthersToDuplicatesFolder([str(keep)], str(keep))

        assert keep.exists()
        assert not (lib / "Duplikátumok").exists()

    def test_move_failure_emits_operation_failed(self, controller, tmp_path):
        lib = tmp_path / "kepek"
        lib.mkdir()
        keep = make_jpeg(lib / "keep.jpg", size=(40, 20))
        missing = lib / "nincs.jpg"

        failures = []
        controller.operationFailed.connect(
            lambda path, msg: failures.append((path, msg))
        )
        controller.moveOthersToDuplicatesFolder([str(keep), str(missing)], str(keep))

        assert failures[0][0] == str(missing)


class TestDeleteOthers:
    def test_deletes_every_item_except_keep(self, controller, tmp_path, monkeypatch):
        monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "xdg"))
        lib = tmp_path / "kepek"
        lib.mkdir()
        keep = make_jpeg(lib / "keep.jpg", size=(40, 20))
        other = lib / "masolat.jpg"
        other.write_bytes(keep.read_bytes())

        resolved = []
        controller.itemResolved.connect(lambda path: resolved.append(path))
        controller.deleteOthers([str(keep), str(other)], str(keep))

        assert keep.exists()
        assert not other.exists()
        assert resolved == [str(other)]

    def test_delete_failure_emits_operation_failed(self, controller, tmp_path):
        lib = tmp_path / "kepek"
        lib.mkdir()
        keep = make_jpeg(lib / "keep.jpg", size=(40, 20))
        missing = lib / "nincs.jpg"

        failures = []
        controller.operationFailed.connect(
            lambda path, msg: failures.append((path, msg))
        )
        controller.deleteOthers([str(keep), str(missing)], str(keep))

        assert failures[0][0] == str(missing)
