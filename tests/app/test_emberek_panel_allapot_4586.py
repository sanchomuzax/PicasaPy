"""#4586: az Emberek panel állapot-forrásai a `FaceScanController`-ben.

A panel (spec `picasa-arcfelismeres.md` 9/b) a háttér-arckeresés közben
betöltés-, ellenőrizetlen-fájl- és adatrendezés-feliratot mutat. Ez a teszt
a jelek és a property-k értéksorozatát méri, a háttérszál kibocsátásának
pillanatában (`Qt.DirectConnection`, ld. a #1233 megjegyzést a
`test_face_scan_controller.py`-ban). A renderelt szöveget a
`qml_functional/test_emberek_panel_allapot_4586.py` nézi.
"""

from __future__ import annotations

import threading
from dataclasses import replace

import pytest
from PySide6.QtCore import Qt

from support.jpeg_factory import make_jpeg
from test_face_scan_controller import _make_controller, _run


def _library(tmp_path, names=("a.jpg", "b.jpg", "c.jpg")):
    root = tmp_path / "kepek"
    root.mkdir()
    for name in names:
        make_jpeg(root / name)
    return root


class TestUncheckedFiles:
    def test_idle_controller_reports_nothing_pending(self, qt_app, tmp_path):
        ctl = _make_controller(qt_app, tmp_path, _library(tmp_path))
        assert ctl.scanPercent == -1
        assert ctl.uncheckedFiles == 0
        assert ctl.sortingPercent == -1

    def test_remaining_files_count_down_to_zero(self, qt_app, tmp_path):
        ctl = _make_controller(qt_app, tmp_path, _library(tmp_path))
        seen = []
        ctl.uncheckedFilesChanged.connect(
            lambda: seen.append(ctl.uncheckedFiles), Qt.DirectConnection
        )

        _run(ctl.scanFinished, ctl.scanForFaces)
        assert ctl.waitForBackgroundWorkers(5.0)

        assert seen[0] == 3, f"a keresés indulásakor mind a 3 fájl hátra van: {seen}"
        assert seen == sorted(seen, reverse=True), f"nem csökkenő: {seen}"
        assert seen[-1] == 0, f"a végén nem 0: {seen}"
        assert ctl.uncheckedFiles == 0

    def test_running_flag_follows_the_scan(self, qt_app, tmp_path):
        ctl = _make_controller(qt_app, tmp_path, _library(tmp_path))
        seen = []
        ctl.scanPercentChanged.connect(
            lambda: seen.append(ctl.scanPercent >= 0), Qt.DirectConnection
        )

        _run(ctl.scanFinished, ctl.scanForFaces)
        assert ctl.waitForBackgroundWorkers(5.0)

        assert seen[0] is True and seen[-1] is False, seen
        assert ctl.scanPercent == -1

    def test_cancelled_scan_clears_the_pending_count(self, qt_app, tmp_path):
        root = _library(tmp_path)

        class _Stopper:
            available = True
            ctl = None

            def detect(self, _image):
                _Stopper.ctl.cancelScan()
                return ()

        ctl = _make_controller(qt_app, tmp_path, root, detector=_Stopper())
        _Stopper.ctl = ctl

        _run(ctl.scanCancelled, ctl.scanForFaces)
        assert ctl.waitForBackgroundWorkers(5.0)

        assert ctl.uncheckedFiles == 0
        assert ctl.scanPercent == -1

    def test_faces_stored_is_signalled_per_photo_with_faces(
        self, qt_app, tmp_path
    ):
        ctl = _make_controller(qt_app, tmp_path, _library(tmp_path))
        count = []
        ctl.facesStored.connect(lambda: count.append(1), Qt.DirectConnection)

        _run(ctl.scanFinished, ctl.scanForFaces)
        assert ctl.waitForBackgroundWorkers(5.0)

        assert len(count) == 3


class TestPendingAmong:
    """#4586: a kapu a KIJELÖLÉSRE vonatkozik, nem a könyvtárra."""

    @staticmethod
    def _paths(root, *names):
        return [str(root / name) for name in names]

    def test_idle_controller_has_nothing_pending(self, qt_app, tmp_path):
        root = _library(tmp_path)
        ctl = _make_controller(qt_app, tmp_path, root)
        assert ctl.pendingAmong(self._paths(root, "a.jpg")) == 0

    def test_pending_shrinks_as_photos_are_checked(self, qt_app, tmp_path):
        root = _library(tmp_path)
        everything = self._paths(root, "a.jpg", "b.jpg", "c.jpg")
        seen = []

        class _Probe:
            available = True
            ctl = None

            def detect(self, _image):
                seen.append(_Probe.ctl.pendingAmong(everything))
                return ()

        ctl = _make_controller(qt_app, tmp_path, root, detector=_Probe())
        _Probe.ctl = ctl

        _run(ctl.scanFinished, ctl.scanForFaces)
        assert ctl.waitForBackgroundWorkers(5.0)

        assert seen == [3, 2, 1], seen
        assert ctl.pendingAmong(everything) == 0

    def test_an_already_scanned_photo_is_never_pending(self, qt_app, tmp_path):
        root = _library(tmp_path, names=("a.jpg", "b.jpg"))
        ctl = _make_controller(qt_app, tmp_path, root)
        _run(ctl.scanFinished, ctl.scanForFaces)
        assert ctl.waitForBackgroundWorkers(5.0)
        make_jpeg(root / "c.jpg")
        from picasapy.index import open_index, sync_tree

        with open_index(tmp_path / "index.db") as conn:
            sync_tree(conn, root)
        seen = []
        ctl.uncheckedFilesChanged.connect(
            lambda: seen.append(ctl.uncheckedFiles), Qt.DirectConnection
        )
        probe = []

        class _Probe:
            available = True

            def detect(self, _image):
                probe.append(
                    ctl.pendingAmong(
                        [str(root / n) for n in ("a.jpg", "b.jpg", "c.jpg")]
                    )
                )
                return ()

        ctl._detector = _Probe()

        _run(ctl.scanFinished, ctl.scanForFaces)
        assert ctl.waitForBackgroundWorkers(5.0)

        # csak a friss c.jpg volt függőben; a jelzés csak érdemi változáskor szól
        assert probe == [1], probe
        assert seen == [1, 0], seen


_IDENTIFIED_INI = (
    "[Contacts2]\n1111111111111111=Anna;;\n"
    + "".join(
        f"[{name}]\nfaces=rect64(1e00280045006e00),1111111111111111\n"
        for name in ("a.jpg", "b.jpg", "c.jpg")
    )
)


class TestPendingSet:
    @pytest.mark.parametrize("kind", ["identified", "video", "excluded"])
    def test_skipped_photos_never_enter_the_pending_set(
        self, qt_app, tmp_path, kind
    ):
        from picasapy.index import all_photos, open_index

        root = _library(tmp_path, names=("a.jpg",))
        enabled = (lambda _folder: False) if kind == "excluded" else None
        ctl = _make_controller(
            qt_app, tmp_path, root, face_detection_enabled=enabled
        )
        with open_index(tmp_path / "index.db") as conn:
            photos = all_photos(conn)
            if kind == "identified":
                (root / ".picasa.ini").write_text(
                    _IDENTIFIED_INI, encoding="utf-8")
            if kind == "video":
                photos = [replace(photos[0], name="film.mp4")]
            pending = ctl._build_pending(conn, photos)

        assert pending == set()

    def test_an_ordinary_photo_is_pending(self, qt_app, tmp_path):
        from picasapy.index import all_photos, open_index

        root = _library(tmp_path, names=("a.jpg",))
        ctl = _make_controller(qt_app, tmp_path, root)
        with open_index(tmp_path / "index.db") as conn:
            assert len(ctl._build_pending(conn, all_photos(conn))) == 1

    def test_the_ini_is_read_once_per_folder(self, qt_app, tmp_path, monkeypatch):
        from picasapy.app import face_ignore_ini
        from picasapy.index import all_photos, open_index

        root = _library(tmp_path)
        (root / ".picasa.ini").write_text("[a.jpg]\nstar=yes\n", encoding="utf-8")
        ctl = _make_controller(qt_app, tmp_path, root)
        reads = []
        original = face_ignore_ini.load_existing
        monkeypatch.setattr(
            face_ignore_ini, "load_existing",
            lambda path: reads.append(path) or original(path),
        )
        with open_index(tmp_path / "index.db") as conn:
            ctl._build_pending(conn, all_photos(conn))

        assert len(reads) == 1, reads

    def test_a_photo_identified_during_the_run_leaves_the_pending_set(
        self, qt_app, tmp_path
    ):
        root = _library(tmp_path)
        everything = [str(root / n) for n in ("a.jpg", "b.jpg", "c.jpg")]
        calls = []

        class _Detector:
            available = True

            def detect(self, _image):
                (root / ".picasa.ini").write_text(
                    _IDENTIFIED_INI, encoding="utf-8")
                return ()

        def enabled(_folder):
            calls.append(ctl.pendingAmong(everything))
            return True

        ctl = _make_controller(
            qt_app, tmp_path, root, detector=_Detector(),
            face_detection_enabled=enabled,
        )

        _run(ctl.scanFinished, ctl.scanForFaces)
        assert ctl.waitForBackgroundWorkers(5.0)

        # 3 előzetes hívás (a függő-halmaz felépítése), majd fotónként 1.
        # A 3. fotó indulásakor az 1. detektálva, a 2. azonosított → csak 1 függő.
        assert calls[3:] == [3, 2, 1], calls


class TestOverlappingScans:
    def test_the_old_scan_does_not_clear_the_new_scans_state(
        self, qt_app, tmp_path
    ):
        root = _library(tmp_path)
        everything = [str(root / n) for n in ("a.jpg", "b.jpg", "c.jpg")]
        gates = [threading.Event(), threading.Event()]
        entered = [threading.Event(), threading.Event()]
        calls = []

        class _Detector:
            available = True

            def detect(self, _image):
                index = min(len(calls), 1)
                calls.append(index)
                entered[index].set()
                if len(calls) <= 2:
                    assert gates[index].wait(10)
                return ()

        ctl = _make_controller(qt_app, tmp_path, root, detector=_Detector())
        ctl.scanForFaces()
        assert entered[0].wait(10)
        ctl.scanForFaces()  # megszakítja az elsőt, újat indít
        assert entered[1].wait(10)

        # az első szál most fejezi be: a `finally`-je nem nyúlhat a másodikhoz
        _run(ctl._scanWorkerStopped, gates[0].set)

        assert ctl.pendingAmong(everything) > 0
        assert ctl.scanPercent >= 0

        gates[1].set()
        assert ctl.waitForBackgroundWorkers(10.0)
        assert ctl.pendingAmong(everything) == 0
        assert ctl.scanPercent == -1


class TestSortingPercent:
    def test_embedding_progress_is_a_real_percentage(self, qt_app, tmp_path):
        ctl = _make_controller(qt_app, tmp_path, _library(tmp_path))
        seen = []
        ctl.sortingPercentChanged.connect(
            lambda: seen.append(ctl.sortingPercent), Qt.DirectConnection
        )

        # a sikeres keresés után a lenyomat-számítás magától indul (#4619)
        _run(ctl.embeddingFinished, ctl.scanForFaces)
        assert ctl.waitForBackgroundWorkers(5.0)

        assert 100 in seen, seen
        assert seen == sorted(seen[: seen.index(100) + 1]) + seen[seen.index(100) + 1 :]
        assert seen[-1] == -1, f"a lezáró −1 hiányzik: {seen}"
        assert ctl.sortingPercent == -1
