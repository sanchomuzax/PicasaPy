"""#7244: a hálózati fájlolvasás nem állíthatja meg a GUI eseményhurkát."""

from __future__ import annotations

import threading
import time
from types import SimpleNamespace

import numpy as np
from PySide6.QtCore import QEventLoop, QObject, QTimer, Signal

from picasapy.app.controller_content_info_mixin import ContentInfoMixin
from picasapy.app.folder_date_controller import FolderDateMixin
from picasapy.app.geo_controller import GeoMixin
from picasapy.app.library_controller_activity import _LibraryActivityMixin
from picasapy.app.library_controller_eltunt_gyoker import _LibraryEltuntGyokerMixin
from picasapy.app.worker_thread import BackgroundWorkerMixin
from picasapy.index import PhotoRecord


_MAIN_THREAD = threading.get_ident()


def _event_loop_max_gap_ms(qt_app, action, duration_ms=900):
    """Az action alatt a QTimer-szívverések legnagyobb kimaradása."""
    loop = QEventLoop()
    heartbeats = []
    timer = QTimer()
    timer.setInterval(10)
    timer.timeout.connect(lambda: heartbeats.append(time.monotonic()))
    timer.start()
    def run_action():
        action()

    QTimer.singleShot(50, run_action)
    QTimer.singleShot(duration_ms, loop.quit)
    loop.exec()
    timer.stop()
    assert len(heartbeats) > 2, "a szívverésmérő nem kapott elegendő eseményt"
    return max(
        (right - left) * 1000
        for left, right in zip(heartbeats, heartbeats[1:], strict=False)
    )


def _photo(path, number=0, *, geotag=None):
    return PhotoRecord(
        id=number + 1,
        folder_path=str(path),
        name=f"photo-{number}.jpg",
        kind="photo",
        size=8_000_000,
        mtime_ns=1,
        star=False,
        caption=None,
        keywords=None,
        rotate_steps=0,
        filters=None,
        taken_at=None,
        orientation=1,
        width=4928,
        height=6560,
        geotag=geotag,
    )


class _PhotoModel(QObject):
    revisionChanged = Signal()

    def __init__(self, photos):
        super().__init__()
        self.photos = photos


class _ContentHost(QObject, BackgroundWorkerMixin, ContentInfoMixin):
    statusChanged = Signal()
    feedChanged = Signal()

    def __init__(self, photos, db_path):
        super().__init__()
        self._photos = _PhotoModel(photos)
        self._db_path = db_path


class _MusicHost(QObject, BackgroundWorkerMixin, FolderDateMixin):
    statusChanged = Signal()


class _RootHost(QObject, BackgroundWorkerMixin, _LibraryEltuntGyokerMixin):
    pass


class _GeoHost(QObject, GeoMixin):
    pass


class _ActivityHost(QObject, _LibraryActivityMixin):
    importChanged = Signal()

    def _root_for_folder(self, _folder):
        return "/watched-root"

    def _reload(self, **_kwargs):
        self.reloads += 1


def test_properties_exif_read_keeps_event_loop_responsive(
    qt_app, tmp_path, monkeypatch
):
    from picasapy.app import controller_content_info_mixin as content_info
    from picasapy.app import formatting_properties
    from picasapy.metadata import EMPTY_EXIF_DETAILS

    host = _ContentHost((_photo(tmp_path),), tmp_path / "index.sqlite")
    monkeypatch.setattr(
        content_info,
        "fajlrendszer_gyoker",
        lambda _path: str(tmp_path),
        raising=False,
    )
    read_threads = []

    def slow_exif(_path):
        read_threads.append(threading.get_ident())
        time.sleep(0.5)
        return EMPTY_EXIF_DETAILS

    monkeypatch.setattr(formatting_properties, "read_exif_details", slow_exif)
    gap_ms = _event_loop_max_gap_ms(qt_app, lambda: host.propertiesOf(0))
    assert host.waitForBackgroundWorkers(3.0)
    qt_app.processEvents()

    assert read_threads and all(thread != _MAIN_THREAD for thread in read_threads)
    assert gap_ms < 200, f"az EXIF-olvasás {gap_ms:.0f} ms-re megállította a hurkot"


def test_folder_music_ini_read_keeps_event_loop_responsive(
    qt_app, tmp_path, monkeypatch
):
    from picasapy.app import folder_date_controller
    from picasapy.ini import parse_document

    host = _MusicHost()
    folder = tmp_path / "nas" / "album"
    read_threads = []

    monkeypatch.setattr(
        folder_date_controller,
        "fajlrendszer_gyoker",
        lambda _path: str(tmp_path / "nas"),
        raising=False,
    )

    def slow_ini(_path):
        read_threads.append(threading.get_ident())
        time.sleep(0.5)
        return parse_document("")

    monkeypatch.setattr(folder_date_controller, "load_or_empty", slow_ini)
    gap_ms = _event_loop_max_gap_ms(qt_app, lambda: host.folderMusicEnabled(str(folder)))
    assert host.waitForBackgroundWorkers(3.0)
    qt_app.processEvents()

    assert read_threads and all(thread != _MAIN_THREAD for thread in read_threads)
    assert gap_ms < 200, f"az ini-olvasás {gap_ms:.0f} ms-re megállította a hurkot"


def test_watched_root_check_keeps_event_loop_responsive(
    qt_app, tmp_path, monkeypatch
):
    from picasapy.app import library_controller_eltunt_gyoker as missing_root

    host = _RootHost()
    host._roots = (str(tmp_path / "nas-root"),)
    host._db_path = tmp_path / "index.sqlite"
    check_threads = []

    def slow_missing(_root):
        check_threads.append(threading.get_ident())
        time.sleep(0.5)
        return False

    monkeypatch.setattr(missing_root, "watched_root_missing", slow_missing)
    gap_ms = _event_loop_max_gap_ms(
        qt_app, lambda: missing_root._LibraryEltuntGyokerMixin._eltunt_gyokerek_rendezese(host)
    )
    assert host.waitForBackgroundWorkers(3.0)
    qt_app.processEvents()

    assert check_threads and all(thread != _MAIN_THREAD for thread in check_threads)
    assert gap_ms < 200, f"a gyökér-ellenőrzés {gap_ms:.0f} ms-re megállította a hurkot"


def test_network_begin_edit_reads_file_in_background(qt_app, tmp_path, monkeypatch):
    from support.jpeg_factory import make_jpeg
    from picasapy.app import edit_controller_preview_mixin as preview_mixin
    from picasapy.app import edit_controller_session_mixin as session_mixin
    from picasapy.app.edit_controller import EditController
    from picasapy.app.edit_preview import EditPreviewProvider

    image = make_jpeg(tmp_path / "large.jpg", size=(64, 48))
    controller = EditController(EditPreviewProvider())
    monkeypatch.setattr(
        session_mixin,
        "fajlrendszer_gyoker",
        lambda _path: str(tmp_path),
        raising=False,
    )
    read_threads = []

    def slow_size(_path):
        read_threads.append(threading.get_ident())
        time.sleep(0.5)
        return 4928, 6560

    monkeypatch.setattr(preview_mixin.EditControllerPreviewMixin,
                        "_read_image_size", staticmethod(slow_size))
    gap_ms = _event_loop_max_gap_ms(
        qt_app, lambda: controller.beginEdit("nas-photo", str(image))
    )
    assert controller.waitForBackgroundWorkers(5.0)
    qt_app.processEvents()

    assert read_threads and all(thread != _MAIN_THREAD for thread in read_threads)
    assert gap_ms < 200, (
        f"a képolvasás {gap_ms:.0f} ms-re megállította a hurkot"
    )


def test_network_crop_suggestion_analysis_runs_in_background(
    qt_app, tmp_path, monkeypatch
):
    from picasapy.app import edit_controller_crop_mixin as crop_mixin
    from picasapy.app.edit_controller import EditController
    from picasapy.app.edit_preview import EditPreviewProvider

    path = tmp_path / "large.jpg"
    controller = EditController(EditPreviewProvider())
    controller._photo_id = "nas-photo"
    controller._image_path = path
    controller._ini_path = None
    controller._network_edit_load_pending = False
    controller._network_edit_load_failed = False
    monkeypatch.setattr(
        crop_mixin, "fajlrendszer_gyoker", lambda _path: str(tmp_path), raising=False
    )
    monkeypatch.setattr(
        crop_mixin,
        "_decode_source",
        lambda *_args, **_kwargs: np.zeros((4000, 3000, 3), dtype=np.uint8),
    )
    controller._provider.source_image = lambda *_args: np.zeros(
        (4000, 3000, 3), dtype=np.uint8
    )
    analysis_threads = []

    def slow_analysis(_image, **_kwargs):
        analysis_threads.append(threading.get_ident())
        time.sleep(0.5)
        return ()

    monkeypatch.setattr(crop_mixin, "suggest_crops", slow_analysis)
    gap_ms = _event_loop_max_gap_ms(qt_app, lambda: controller.cropSuggestions)
    assert controller.waitForBackgroundWorkers(3.0)
    qt_app.processEvents()

    assert analysis_threads and all(thread != _MAIN_THREAD for thread in analysis_threads)
    assert gap_ms < 200, f"a vágásanalízis {gap_ms:.0f} ms-re megállította a hurkot"


def test_font_catalogue_first_read_keeps_event_loop_responsive(
    qt_app, monkeypatch
):
    from picasapy.app import edit_controller
    from picasapy.app.edit_controller import EditController
    from picasapy.app.edit_preview import EditPreviewProvider

    controller = EditController(EditPreviewProvider())
    read_threads = []

    def slow_catalogue():
        read_threads.append(threading.get_ident())
        time.sleep(0.5)
        return [{"key": "Arial", "label": "Arial"}]

    monkeypatch.setattr(edit_controller, "family_labels", slow_catalogue)
    gap_ms = _event_loop_max_gap_ms(
        qt_app, lambda: (controller.textFontFamilies, controller.textFontFamily)
    )
    assert controller.waitForBackgroundWorkers(3.0)
    qt_app.processEvents()

    assert read_threads and all(thread != _MAIN_THREAD for thread in read_threads)
    assert gap_ms < 200, f"a betűlista {gap_ms:.0f} ms-re megállította a hurkot"


def test_geo_markers_are_materialized_once_for_large_feed(qt_app, tmp_path, monkeypatch):
    from picasapy.index.queries import PhotoRecord as Record

    photos = tuple(
        _photo(tmp_path, number, geotag="47.5,19.0" if number == 0 else None)
        for number in range(1145)
    )
    host = _GeoHost()
    host._photos = SimpleNamespace(photos=photos, thumbUrlAt=lambda _row: "file:///thumb")
    original = Record.location.fget
    reads = []

    def counted_location(photo):
        reads.append(photo.id)
        return original(photo)

    monkeypatch.setattr(Record, "location", property(counted_location))
    first = host.geoMarkers
    second = host.geoMarkers

    assert first == second and len(first) == 1
    assert len(reads) == len(photos), (
        f"a {len(photos)} képes feed helyadatait {len(reads)} alkalommal olvasta"
    )


def test_final_sync_progress_does_not_repeat_the_final_feed_reload(qt_app):
    host = _ActivityHost()
    host.reloads = 0
    host._import_new_at_reload = 0
    host._import_last_reload = 0.0
    host._import_visible = True
    host._import_forced = False
    host._import_dismissed = False

    host._on_sync_progress("/watched-root/album", 1145, 1145, 1145)

    assert host.reloads == 0, "a végső progressz egy második teljes feed-újratöltést kért"
