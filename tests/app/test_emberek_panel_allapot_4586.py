"""#4586: az Emberek panel állapot-forrásai a `FaceScanController`-ben.

A panel (spec `picasa-arcfelismeres.md` 9/b) a háttér-arckeresés közben
betöltés-, ellenőrizetlen-fájl- és adatrendezés-feliratot mutat. Ez a teszt
a jelek és a property-k értéksorozatát méri, a háttérszál kibocsátásának
pillanatában (`Qt.DirectConnection`, ld. a #1233 megjegyzést a
`test_face_scan_controller.py`-ban). A renderelt szöveget a
`qml_functional/test_emberek_panel_allapot_4586.py` nézi.
"""

from __future__ import annotations

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
        assert ctl.scanRunning is False
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
            lambda: seen.append(ctl.scanRunning), Qt.DirectConnection
        )

        _run(ctl.scanFinished, ctl.scanForFaces)
        assert ctl.waitForBackgroundWorkers(5.0)

        assert seen[0] is True and seen[-1] is False, seen
        assert ctl.scanRunning is False

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
        assert ctl.scanRunning is False

    def test_faces_stored_is_signalled_per_photo_with_faces(
        self, qt_app, tmp_path
    ):
        ctl = _make_controller(qt_app, tmp_path, _library(tmp_path))
        count = []
        ctl.facesStored.connect(lambda: count.append(1), Qt.DirectConnection)

        _run(ctl.scanFinished, ctl.scanForFaces)
        assert ctl.waitForBackgroundWorkers(5.0)

        assert len(count) == 3


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
