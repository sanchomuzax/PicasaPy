"""#459 — 2. pont (sérült/betölthetetlen kép: elrejtés felajánlása a
MEGLÉVŐ elrejtés-úton) és 4. pont (lemezhely-ellenőrzés export/webexport/
import előtt) controller-szintű tesztjei."""

import pytest
from PySide6.QtCore import QEventLoop, QTimer

from support.jpeg_factory import make_jpeg


@pytest.fixture
def library(tmp_path):
    root = tmp_path / "kepek"
    root.mkdir()
    make_jpeg(root / "IMG_0001.jpg")
    make_jpeg(root / "IMG_0002.jpg")
    return root


@pytest.fixture
def controller(qt_app, tmp_path, library):
    from picasapy.app.controller import AppController
    from picasapy.app.thumbnail_provider import ThumbnailProvider
    from picasapy.index import open_index, sync_tree
    from picasapy.thumbs import ThumbnailCache
    from PySide6.QtCore import QSettings

    with open_index(tmp_path / "index.db") as conn:
        sync_tree(conn, library)
    provider = ThumbnailProvider(ThumbnailCache(tmp_path / "thumbs", size=32))
    settings = QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat)
    ctl = AppController(
        tmp_path / "index.db", (str(library),), provider, settings=settings,
        watched_file=tmp_path / "WatchedFolders.txt",
    )
    ctl._reload()
    ctl.selectFolder(str(library))
    yield ctl
    assert ctl.waitForBackgroundWorkers(30.0), "háttérszál nem állt le a teardownban"


class TestBrokenPhotoDetection:
    """A ThumbnailProvider `brokenImageDetected`-je → a controller
    `brokenPhotosDetected`-en át jelzi a QML-nek, fotónként EGYSZER."""

    def test_broken_image_signal_reaches_controller(self, controller, qt_app):
        photo = controller.photos.photos[0]
        events = []
        controller.brokenPhotosDetected.connect(events.append)
        controller._provider.brokenImageDetected.emit(str(photo.id))
        qt_app.processEvents()
        assert events == [[{"id": photo.id, "name": photo.name}]]

    def test_broken_image_signal_deduplicated(self, controller, qt_app):
        photo = controller.photos.photos[0]
        events = []
        controller.brokenPhotosDetected.connect(events.append)
        controller._provider.brokenImageDetected.emit(str(photo.id))
        controller._provider.brokenImageDetected.emit(str(photo.id))
        qt_app.processEvents()
        assert len(events) == 1

    def test_unknown_photo_id_ignored(self, controller, qt_app):
        events = []
        controller.brokenPhotosDetected.connect(events.append)
        controller._provider.brokenImageDetected.emit("999999")
        qt_app.processEvents()
        assert events == []


class TestHidePhotosByIds:
    """`hidePhotosByIds` — a sérült-kép ajánlat "Hide Files" válasza a
    MEGLÉVŐ `toggleHiddenRows`/`_apply_batch` elrejtés-utat futtatja, csak
    id-alapon (nem sorindexen)."""

    def test_hides_photo_by_id(self, controller, library):
        photo = controller.photos.photos[0]
        controller.hidePhotosByIds([photo.id])
        ini_text = (library / ".picasa.ini").read_text(encoding="utf-8")
        assert "hidden=yes" in ini_text.split(f"[{photo.name}]")[1]
        remaining = [p.name for p in controller.photos.photos]
        assert photo.name not in remaining

    def test_unknown_id_is_noop(self, controller, library):
        controller.hidePhotosByIds([999999])
        assert not (library / ".picasa.ini").exists()

    def test_empty_list_is_noop(self, controller, library):
        controller.hidePhotosByIds([])
        assert not (library / ".picasa.ini").exists()


class TestExportDiskSpaceCheck:
    @staticmethod
    def _run_export(controller, qt_app, rows, target):
        results = []
        loop = QEventLoop()
        controller.exportFinished.connect(
            lambda done, failed: results.append((done, failed))
        )
        controller.exportFinished.connect(loop.quit)
        controller.exportRows(rows, target, 0, 85)
        if not results:
            QTimer.singleShot(5000, loop.quit)
            loop.exec()
        return results

    def test_insufficient_space_blocks_export_and_reports(
        self, controller, library, tmp_path, qt_app, monkeypatch
    ):
        from picasapy.app import export_controller

        monkeypatch.setattr(
            export_controller, "has_enough_free_space", lambda *a, **k: False
        )
        details = []
        controller.exportFailedDetails.connect(details.append)
        target = tmp_path / "export-cel"
        results = self._run_export(controller, qt_app, [0, 1], str(target))
        assert results == [(0, 2)]
        assert details and "disk space" in details[0][0]
        # a művelet NEM indult el félbehagyva — semmi nem másolódott
        assert not target.exists() or not list(target.glob("*.jpg"))

    def test_sufficient_space_exports_normally(self, controller, library, tmp_path, qt_app):
        target = tmp_path / "export-cel-ok"
        results = self._run_export(controller, qt_app, [0, 1], str(target))
        assert results == [(2, 0)]


class TestImportDiskSpaceCheck:
    def test_insufficient_space_blocks_import_and_reports(
        self, qt_app, tmp_path, monkeypatch
    ):
        from PySide6.QtCore import QSettings

        from picasapy.app.import_source_controller import ImportSourceController
        from picasapy.app import import_source_controller as mod
        from picasapy.app.thumbnail_provider import ThumbnailProvider
        from picasapy.thumbs import ThumbnailCache

        source = tmp_path / "kartya"
        source.mkdir()
        make_jpeg(source / "DSC_0001.jpg")
        dest = tmp_path / "cel"
        dest.mkdir()

        added = []
        provider = ThumbnailProvider(ThumbnailCache(tmp_path / "thumbs", size=32))
        settings = QSettings(
            str(tmp_path / "importsettings.ini"), QSettings.Format.IniFormat
        )
        ctl = ImportSourceController(
            provider, add_folder=added.append,
            index_path=tmp_path / "index.db", settings=settings,
        )
        monkeypatch.setattr(mod, "has_enough_free_space", lambda *a, **k: False)

        scan_results = []
        scan_loop = QEventLoop()
        ctl.sourceScanFinished.connect(lambda items, count: scan_results.append(count))
        ctl.sourceScanFinished.connect(scan_loop.quit)
        ctl.scanSource(str(source))
        if not scan_results:
            QTimer.singleShot(5000, scan_loop.quit)
            scan_loop.exec()
        assert scan_results == [1]

        finished = []
        details = []
        loop = QEventLoop()
        ctl.importFinished.connect(lambda done, failed: finished.append((done, failed)))
        ctl.importFinished.connect(loop.quit)
        ctl.importFailedDetails.connect(details.append)
        ctl.runImport(str(dest), "manual", "importalt", "leave")
        if not finished:
            QTimer.singleShot(5000, loop.quit)
            loop.exec()
        assert finished == [(0, 1)]
        assert details and "disk space" in details[0][0]
        assert list(dest.glob("*.jpg")) == []
        assert ctl.waitForBackgroundWorkers(30.0)
