"""#7244: a hálózati fájlolvasás nem állíthatja meg a GUI eseményhurkát."""

from __future__ import annotations

import threading
import time
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest
from PySide6.QtCore import QEventLoop, QObject, QTimer, Signal

from picasapy.app import library_controller_activity as activity_module
from picasapy.app.controller_content_info_mixin import ContentInfoMixin
from picasapy.app.folder_date_controller import FolderDateMixin
from picasapy.app.geo_controller import GeoMixin
from picasapy.app.library_controller_activity import _LibraryActivityMixin
from picasapy.app.library_controller_eltunt_gyoker import _LibraryEltuntGyokerMixin
from picasapy.app.controller_sync_mixin import AppControllerSyncMixin
from picasapy.app.worker_thread import BackgroundWorkerMixin
from picasapy.index import PhotoRecord


_MAIN_THREAD = threading.get_ident()


def test_default_text_family_getter_does_not_load_font_catalogue():
    from picasapy.app.edit_controller_text_mixin import EditControllerTextMixin
    from picasapy.ini.text_overlay import DEFAULT_FAMILY

    class FontHost(EditControllerTextMixin):
        def __init__(self):
            self._text_family_value = None
            self.catalogue_loads = 0

        def _queue_text_font_families(self):
            self.catalogue_loads += 1

    host = FontHost()

    assert host._text_family == DEFAULT_FAMILY
    assert host.catalogue_loads == 0


def test_tool_state_notifications_only_emit_changed_properties(qt_app):
    from picasapy.app.edit_controller import EditController
    from picasapy.app.edit_preview import EditPreviewProvider

    controller = EditController(EditPreviewProvider())
    emitted = []
    controller.textOpacityChanged.connect(lambda: emitted.append("textOpacity"))
    controller.textFontFamilyChanged.connect(
        lambda: emitted.append("textFontFamily")
    )
    controller.toolStateChanges.connect(lambda names: emitted.append(tuple(names)))
    controller.toolsChanged.connect(lambda: emitted.append("toolsChanged"))

    before = controller._tool_property_values()
    controller._text_opacity = 0.5

    changed = controller._emit_changed_tool_properties(before)

    assert changed == ["textOpacity"]
    assert emitted == ["textOpacity", ("textOpacity",)]


def test_network_begin_edit_emits_only_changed_tool_properties(
    qt_app, tmp_path, monkeypatch
):
    from picasapy.app import edit_controller_session_mixin as session_mixin
    from picasapy.app.edit_controller import EditController
    from picasapy.app.edit_preview import EditPreviewProvider

    controller = EditController(EditPreviewProvider())
    monkeypatch.setattr(
        session_mixin, "fajlrendszer_gyoker", lambda _path: str(tmp_path)
    )
    monkeypatch.setattr(controller, "_start_network_edit_state_load", lambda *_: None)
    tools_changed = []
    sessions_started = []
    changed_properties = []
    controller.toolsChanged.connect(lambda: tools_changed.append(True))
    controller.editSessionStarted.connect(lambda: sessions_started.append(True))
    controller.toolStateChanges.connect(
        lambda names: changed_properties.extend(names)
    )

    controller.beginEdit("network-photo", str(tmp_path / "photo.jpg"))

    assert not tools_changed
    assert sessions_started == [True]
    assert len(changed_properties) == len(set(changed_properties))


def test_local_edit_session_notifies_qml_properties(qt_app, tmp_path):
    from picasapy.app.edit_controller import EditController
    from picasapy.app.edit_preview import EditPreviewProvider
    from support.jpeg_factory import make_jpeg

    photo = make_jpeg(tmp_path / "local-edit.jpg", size=(32, 24))
    controller = EditController(EditPreviewProvider())
    notified = []
    controller.chainValueChanged.connect(lambda: notified.append("chain"))
    controller.cropSuggestionsChanged.connect(lambda: notified.append("crop"))

    controller.beginEdit("local-photo", str(photo))

    assert "chain" in notified
    assert "crop" in notified
    assert controller.waitForBackgroundWorkers(10.0)


def test_revision_without_preview_change_keeps_preview_url(qt_app, tmp_path):
    from picasapy.app.edit_controller import EditController
    from picasapy.app.edit_preview import EditPreviewProvider
    from support.jpeg_factory import make_jpeg

    photo = make_jpeg(tmp_path / "no-preview-change.jpg", size=(8, 6))
    controller = EditController(EditPreviewProvider())
    controller.beginEdit("1", str(photo))
    before = controller.previewSource
    before_revision = controller.revision
    before_preview_revision = controller._preview_revision

    controller._bump_revision(preview_changed=False)

    assert controller.revision == before_revision
    assert controller.previewSource == before
    assert controller._preview_revision == before_preview_revision
    assert controller.waitForBackgroundWorkers(10.0)


def test_sync_finish_skips_feed_reload_when_progress_already_loaded_index():
    class SyncHost(AppControllerSyncMixin):
        _last_sync_changed = True
        _view_mode = ("folder", r"\\server\share")
        _current_folder = r"\\server\share"
        _feed_stamp = ("db", 4, "wal", 8)
        backupFilterActive = False

        def __init__(self):
            self.reloads = 0

        def _index_stamp(self):
            return ("db", 4, "wal", 8)

        def _reload(self, **_kwargs):
            self.reloads += 1

    host = SyncHost()
    AppControllerSyncMixin._reload_after_sync_if_changed(host)
    assert host.reloads == 0

    host._index_stamp = lambda: ("db", 4, "wal", 9)
    host._sync_reload_idle_ready = True
    AppControllerSyncMixin._reload_after_sync_if_changed(host)
    assert host.reloads == 1


def test_sync_finish_yields_event_loop_before_feed_reload(monkeypatch):
    queued = []

    class SyncHost(AppControllerSyncMixin):
        _last_sync_changed = True
        _view_mode = ("folder", r"\\server\share")
        _current_folder = r"\\server\share"
        _feed_stamp = None
        backupFilterActive = False

        def __init__(self):
            self.reloads = 0

        def _index_stamp(self):
            return ("db", 1)

        def _reload(self, **_kwargs):
            self.reloads += 1

    host = SyncHost()
    monkeypatch.setattr(
        QTimer,
        "singleShot",
        lambda delay, callback: queued.append((delay, callback)),
    )

    AppControllerSyncMixin._reload_after_sync_if_changed(host)

    assert host.reloads == 0
    assert len(queued) == 1
    assert queued[0][0] == 100

    AppControllerSyncMixin._finish_sync_reload_after_idle(host)
    assert host.reloads == 1


def test_local_sync_finish_reloads_feed_without_delay(monkeypatch, tmp_path):
    queued = []
    reloads = []

    class SyncHost(AppControllerSyncMixin):
        _last_sync_changed = True
        _feed_stamp = None
        backupFilterActive = False

        def __init__(self):
            self._current_folder = str(tmp_path)
            self._view_mode = ("folder", self._current_folder)

        def _index_stamp(self):
            return ("db", 1)

        def _reload(self, **kwargs):
            reloads.append(kwargs)

    monkeypatch.setattr(
        QTimer,
        "singleShot",
        lambda delay, callback: queued.append((delay, callback)),
    )

    AppControllerSyncMixin._reload_after_sync_if_changed(SyncHost())

    assert reloads == [{"preserve_scroll": True}]
    assert queued == []


def test_sync_finish_defers_feed_reload_until_viewer_session_ends():
    class SyncHost(AppControllerSyncMixin):
        _last_sync_changed = True
        _view_mode = ("folder", r"\\server\share")
        _current_folder = r"\\server\share"
        _feed_stamp = ("db", 4, "wal", 8)
        backupFilterActive = False
        _edit_controller_for_sync = SimpleNamespace(_photo_id="network-photo")

        def __init__(self):
            self.reloads = 0

        def _index_stamp(self):
            return ("db", 4, "wal", 9)

        def _reload(self, **_kwargs):
            self.reloads += 1

    host = SyncHost()
    AppControllerSyncMixin._reload_after_sync_if_changed(host)
    assert host.reloads == 0
    assert host._deferred_sync_reload is True

    host._edit_controller_for_sync._photo_id = ""
    host._last_sync_changed = False
    host._sync_reload_idle_ready = True
    AppControllerSyncMixin._reload_after_sync_if_changed(host)
    assert host.reloads == 1
    assert host._deferred_sync_reload is False


def test_sync_progress_skips_feed_reload_for_open_photo_in_same_root():
    class SignalRecorder:
        def emit(self):
            pass

    root = "/slow-network-root"
    host = SimpleNamespace(
        _root_for_folder=lambda path: root if path.startswith(root) else None,
        _current_folder=root,
        _sync_reload_grace_until=0.0,
        _import_folder="",
        _import_done=0,
        _import_total=0,
        _import_new=0,
        _import_new_at_reload=0,
        _import_last_reload=0.0,
        _import_visible=True,
        _import_forced=False,
        _import_dismissed=False,
        _edit_controller_for_sync=SimpleNamespace(
            _photo_id="network-photo", _image_path=root + "/album/photo.jpg"
        ),
        reloads=[],
        importChanged=SignalRecorder(),
    )
    host._reload = lambda **_kwargs: host.reloads.append(True)

    _LibraryActivityMixin._on_sync_progress(host, root + "/album", 1, 40, 1)

    assert host.reloads == []
    assert host._deferred_sync_reload is True
    assert host._import_new_at_reload == 1


def test_sync_progress_refreshes_feed_without_reloading_side_pane():
    class SignalRecorder:
        def emit(self):
            pass

    root = "/slow-network-root"
    host = SimpleNamespace(
        _root_for_folder=lambda path: root if path.startswith(root) else None,
        _current_folder=root,
        _sync_reload_grace_until=0.0,
        _import_folder="",
        _import_done=0,
        _import_total=0,
        _import_new=0,
        _import_new_at_reload=0,
        _import_last_reload=0.0,
        _import_visible=True,
        _import_forced=False,
        _import_dismissed=False,
        _edit_controller_for_sync=SimpleNamespace(_photo_id=""),
        reloads=[],
        feed_refreshes=[],
        importChanged=SignalRecorder(),
    )
    host._reload = lambda **_kwargs: host.reloads.append(True)
    host._refresh_view = lambda: host.feed_refreshes.append(True)

    _LibraryActivityMixin._on_sync_progress(host, root + "/album", 1, 40, 1)

    assert host.reloads == []
    assert host.feed_refreshes == [True]


def test_network_folder_description_update_avoids_global_status_signal():
    class SignalRecorder:
        def __init__(self):
            self.calls = 0

        def emit(self):
            self.calls += 1

    host = SimpleNamespace(
        _description_read_results={"/slow-root/album": "description"},
        _description_reads_pending={"/slow-root/album"},
        _descriptions={},
        _current_folder="/slow-root/album",
        _folder_description="",
        statusChanged=SignalRecorder(),
        feedChanged=SignalRecorder(),
    )

    ContentInfoMixin._apply_network_folder_description(host)

    assert host._folder_description == "description"
    assert host.statusChanged.calls == 0
    assert host.feedChanged.calls == 1


def test_folder_music_cache_results_use_specific_signal():
    class SignalRecorder:
        def __init__(self):
            self.calls = 0

        def emit(self):
            self.calls += 1

    folder = "/slow-root/album"
    host = SimpleNamespace(
        _folder_music_read_results={folder: (True, "music.mp3")},
        _folder_music_pending={folder},
        _folder_music_cache={},
        _folder_music_url_results={folder: ("file:///music.mp3",)},
        _folder_music_urls_pending={folder},
        _folder_music_urls_cache={},
        statusChanged=SignalRecorder(),
        folderMusicChanged=SignalRecorder(),
    )

    FolderDateMixin._apply_network_folder_music_reads(host)
    FolderDateMixin._apply_network_folder_music_urls(host)

    assert host._folder_music_cache == {folder: (True, "music.mp3")}
    assert host._folder_music_urls_cache == {folder: ("file:///music.mp3",)}
    assert host.statusChanged.calls == 0
    assert host.folderMusicChanged.calls == 2


def test_folder_select_during_sync_reuses_visible_photos(monkeypatch, tmp_path):
    import picasapy.app.controller as controller_module

    class SignalRecorder:
        def __init__(self):
            self.calls = []

        def emit(self, *args):
            self.calls.append(args)

    class Host:
        def __init__(self, folder):
            self._root = folder
            self._view_mode = ("folder", "previous-folder")
            self._feed_stamp = None
            self._db_path = str(tmp_path / "index.sqlite")
            self._current_folder = "previous-folder"
            self._filter_active = False
            self._filter_status = ""
            self._import_visible = True
            self._photos = SimpleNamespace(photos=(_photo(folder),))
            self._folders = SimpleNamespace(offline_paths=lambda: ())
            self.folderActivated = SignalRecorder()
            self.statusChanged = SignalRecorder()
            self.folderUnavailable = SignalRecorder()

        def _get_settings(self):
            return SimpleNamespace(setValue=lambda *_args: None)

        def _root_for_folder(self, path):
            return self._root if path == self._root else None

        def _folder_description_for_open(self, _folder):
            return ""

        def _clear_unread(self, _folder):
            pass

        def _restore_full_folder_pane(self):
            pass

        def _feed_records(self, _conn):
            raise AssertionError("a szinkron alatti mappaváltás új feedet olvasott")

    folder = str(tmp_path / "slow-network-root")
    host = Host(folder)

    class UnexpectedIndexRead:
        def __enter__(self):
            raise AssertionError("a szinkron alatti mappaváltás indexet olvasott")

        def __exit__(self, *_args):
            return False

    monkeypatch.setattr(
        controller_module, "open_index", lambda *_args: UnexpectedIndexRead()
    )
    controller_module.AppController.selectFolder(host, folder)

    assert host._current_folder == folder
    assert host.folderActivated.calls == [(folder,)]


def test_empty_folder_select_during_sync_skips_feed_load_and_starts_grace(
    monkeypatch, tmp_path
):
    import picasapy.app.controller as controller_module

    class SignalRecorder:
        def __init__(self):
            self.calls = []

        def emit(self, *args):
            self.calls.append(args)

    folder = str(tmp_path / "slow-network-root")

    class Host:
        def __init__(self):
            self._view_mode = ("folder", "previous-folder")
            self._feed_stamp = None
            self._db_path = str(tmp_path / "index.sqlite")
            self._current_folder = "previous-folder"
            self._filter_active = False
            self._filter_status = ""
            self._import_visible = False
            self._import_forced = True
            self._photos = SimpleNamespace(photos=())
            self._folders = SimpleNamespace(offline_paths=lambda: ())
            self.folderActivated = SignalRecorder()
            self.statusChanged = SignalRecorder()
            self.folderUnavailable = SignalRecorder()

        def _root_for_folder(self, path):
            return folder if path == folder else None

        def _get_settings(self):
            return SimpleNamespace(setValue=lambda *_args: None)

        def _folder_description_for_open(self, _folder):
            return ""

        def _clear_unread(self, _folder):
            pass

        def _restore_full_folder_pane(self):
            pass

        def _feed_records(self, _conn):
            raise AssertionError("az üres, szinkronizált mappa feedet olvasott")

    class UnexpectedIndexRead:
        def __enter__(self):
            raise AssertionError("az üres, szinkronizált mappa indexet olvasott")

        def __exit__(self, *_args):
            return False

    host = Host()
    monkeypatch.setattr(
        controller_module, "open_index", lambda *_args: UnexpectedIndexRead()
    )

    controller_module.AppController.selectFolder(host, folder)

    assert host._current_folder == folder
    assert host.folderActivated.calls == [(folder,)]
    assert host._sync_reload_grace_until > time.monotonic()


def test_sync_progress_keeps_selected_folder_open_grace_alive(monkeypatch):
    queued = []

    monkeypatch.setattr(
        QTimer,
        "singleShot",
        lambda delay, callback: queued.append((delay, callback)),
    )
    # #7319: a valódi óra Windowson durva (~15,6 ms-os lépcső), így a teszt
    # eleji és a hívás közbeni `time.monotonic()` UGYANAZT az értéket adhatja,
    # és az időkülönbségre épülő éles egyenlőtlenség a határon elbukik. A
    # modul óráját a teszt vezérli: az idő nem telik, a szerződés pontos.
    now = 1000.0
    monkeypatch.setattr(
        activity_module, "time", SimpleNamespace(monotonic=lambda: now)
    )

    class SignalRecorder:
        def emit(self):
            pass

    folder = "/slow-network-root"
    host = SimpleNamespace(
        _root_for_folder=lambda path: folder if path.startswith(folder) else None,
        _current_folder=folder,
        _sync_reload_grace_until=now + 1,
        _deferred_sync_reload=True,
        _import_visible=True,
        _import_forced=False,
        _import_folder="",
        _import_done=0,
        _import_total=0,
        _import_new=0,
        _import_new_at_reload=0,
        _import_last_reload=now,
        _finish_sync_reload_grace=lambda: None,
        importChanged=SignalRecorder(),
    )
    previous_grace = host._sync_reload_grace_until

    _LibraryActivityMixin._on_sync_progress(host, folder + "/album", 1, 2, 0)

    # A progressz a türelmi időt a mostani időtől számított TELJES 3 s-ra
    # újítja, nem hagyja meg a megmaradt 1 s-ot.
    assert host._sync_reload_grace_until == now + 3.0
    assert host._sync_reload_grace_until - previous_grace == 2.0
    assert queued and 2500 <= queued[0][0] <= 3000


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


def test_folder_open_unread_index_write_runs_in_background(
    qml_app, qt_app, tmp_path, monkeypatch
):
    from types import SimpleNamespace

    from picasapy.app import controller_navigation_mixin as navigation

    _window, controller, _library, _engine = qml_app
    read_threads = []

    class SlowIndex:
        def __enter__(self):
            read_threads.append(threading.get_ident())
            time.sleep(0.5)
            return self

        def __exit__(self, *_args):
            return False

        def execute(self, *_args):
            return SimpleNamespace(rowcount=1)

        def commit(self):
            pass

    monkeypatch.setattr(navigation, "open_index", lambda _path: SlowIndex())
    monkeypatch.setattr(controller, "_reload_folders", lambda: None)
    gap_ms = _event_loop_max_gap_ms(
        qt_app, lambda: controller._clear_unread(str(tmp_path / "album"))
    )
    assert controller.waitForBackgroundWorkers(3.0)
    qt_app.processEvents()

    assert read_threads and all(thread != _MAIN_THREAD for thread in read_threads)
    assert gap_ms < 200, f"a mappanyitás indexírása {gap_ms:.0f} ms-re állította meg a hurkot"


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
    assert len(reads) == 1, (
        "csak az egyetlen helycímkézett képnél kell koordinátát feldolgozni; "
        f"a {len(photos)} képes feed {len(reads)} helyolvasást végzett"
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


def test_nezo_kepolvasasa_aszinkron_es_a_rejtett_fak_lustak(qt_app):
    """A hálózati kép forrása nem fogja meg az eseményhurkot; rejtett fák nem épülnek fel."""
    import json

    from PySide6.QtCore import QUrl
    from PySide6.QtGui import QColor, QImage
    from PySide6.QtQml import QQmlComponent, QQmlEngine, QQmlExpression, qmlContext
    from PySide6.QtQuick import QQuickImageProvider, QQuickWindow
    from tests.support.varakozas import var_feltetelre

    qml_dir = Path(__file__).parents[2] / "src/picasapy/app/qml/PicasaPy"
    grid_qml = (qml_dir / "PhotoViewerStraightenGrid.qml").read_text(encoding="utf-8")
    photo_area_qml = (qml_dir / "PhotoViewerPhotoArea.qml").read_text(encoding="utf-8")
    foto_image_qml = (qml_dir / "PhotoViewerFotoImage.qml").read_text(encoding="utf-8")
    before_image_qml = (qml_dir / "PhotoViewerElotteImage.qml").read_text(
        encoding="utf-8"
    )
    right_panels_qml = (qml_dir / "PhotoViewerRightPanels.qml").read_text(
        encoding="utf-8"
    )
    async_binding = 'asynchronous: Qt.platform.pluginName !== "offscreen"'
    assert async_binding in grid_qml, "a kiegyenesítő rács képei szinkron forrásbetöltők"
    assert async_binding in foto_image_qml
    assert async_binding in before_image_qml
    assert photo_area_qml.count(async_binding) == 2, (
        "a PhotoViewerPhotoArea valamelyik fájlforrású képe szinkron maradt"
    )
    assert "id: straightenGridLoader" in photo_area_qml
    assert "active: photoArea.hostViewer.visible" in photo_area_qml
    assert "PhotoViewerStraightenGrid {" in photo_area_qml
    assert "objectName: \"viewerPropertiesPanelLoader\"" in right_panels_qml
    assert "active: viewer.propertiesOpen && viewer.visible" in right_panels_qml
    assert "sourceComponent: PropertiesPanel {" in right_panels_qml

    provider_threads = []

    class SlowImageProvider(QQuickImageProvider):
        def __init__(self):
            super().__init__(QQuickImageProvider.ImageType.Image)

        def requestImage(self, _image_id, size, _requested_size):  # noqa: N802 (Qt API)
            provider_threads.append(threading.current_thread())
            time.sleep(0.5)
            image = QImage(32, 24, QImage.Format.Format_ARGB32)
            image.fill(QColor("red"))
            size.setWidth(image.width())
            size.setHeight(image.height())
            return image

    provider = SlowImageProvider()
    engine = QQmlEngine()
    engine.addImageProvider("slowNas", provider)
    component = QQmlComponent(engine)
    component.setData(
        b"import QtQuick\n"
        b'Item { width: 32; height: 24; Image { objectName: "viewerImage"; '
        b"anchors.fill: parent; asynchronous: true } }",
        QUrl(),
    )
    assert var_feltetelre(
        qt_app,
        lambda: component.status() != QQmlComponent.Status.Loading,
        5.0,
    ), "a minimális Image-komponens nem készült el"
    root = component.create()
    assert root is not None, "\n".join(error.toString() for error in component.errors())
    window = QQuickWindow()
    window.setWidth(32)
    window.setHeight(24)
    root.setParentItem(window.contentItem())
    window.show()
    image = root.findChild(QObject, "viewerImage")
    assert image is not None
    image_ready = QQmlExpression(qmlContext(image), image, "status === Image.Ready")
    image_ready.setSourceLocation(str(qml_dir / "PhotoViewerFotoImage.qml"), 1, 1)
    previous_source = image.property("source")
    queued_source_expressions = []

    def queue_source_change(source: str) -> None:
        # A Qt képbetöltő a Python szolgáltatót munkaszálon hívja. A forrás
        # Pythonból állítása közben a GIL-t tartó tesztszál és a képbetöltő
        # egymásra várhat, ezért maga az értékadás QML-oldalon, a következő
        # eseménykörben történjen.
        expression = QQmlExpression(
            qmlContext(image),
            image,
            "Qt.callLater(function() { source = "
            f"{json.dumps(source)}; }})",
        )
        expression.evaluate()
        queued_source_expressions.append(expression)

    heartbeat = [time.monotonic()]
    beat_timer = QTimer()
    beat_timer.setInterval(10)
    beat_timer.timeout.connect(lambda: heartbeat.append(time.monotonic()))
    beat_timer.start()
    queue_source_change("image://slowNas/large-network-image")
    assert var_feltetelre(
        qt_app,
        lambda: bool(image_ready.evaluate()[0]) and bool(provider_threads),
        5.0,
    ), "a lassú Image-forrás nem készült el"
    heartbeat.append(time.monotonic())
    beat_timer.stop()
    previous_source_text = (
        previous_source.toString()
        if hasattr(previous_source, "toString")
        else str(previous_source or "")
    )
    queue_source_change(previous_source_text)

    def current_source_text() -> str:
        source = image.property("source")
        return source.toString() if hasattr(source, "toString") else str(source or "")

    assert var_feltetelre(
        qt_app,
        lambda: current_source_text() == previous_source_text,
        5.0,
    ), "a QML-oldali forrás-visszaállítás nem fejeződött be"

    max_gap_ms = max(
        ((right - left) * 1000 for left, right in zip(heartbeat, heartbeat[1:], strict=False)),
        default=0,
    )
    assert provider_threads and all(
        thread is not threading.main_thread() for thread in provider_threads
    ), "az Image szolgáltató a GUI-szálon futott"
    assert max_gap_ms < 200, (
        f"a lassú hálózati Image-forrás {max_gap_ms:.0f} ms-re állította meg "
        "az eseményhurkot"
    )


def test_teljes_nezo_utvonal_nem_olvas_lassu_gyokerbol_a_foszalon(
    qml_app, qt_app, tmp_path, monkeypatch, request
):
    """A lassú gyökér I/O-ja maradjon háttérben, az eseményhurok rése pedig 500 ms alatt.

    Az 500 ms CI-n is stabil általános határ; ez alatt nem jelentkezik a
    fagyásérzet, és jóval rövidebb a Windows 5 s-os „Nem válaszol” határánál.
    A lassú gyökérből végzett GUI-szálas fájlműveletek megengedett száma továbbra is nulla.
    A célzott fájlművelet-próbák szigorú, 200 ms-os küszöbe változatlan.
    """
    import os
    import sys
    import traceback

    from PySide6.QtCore import QObject, QEventLoop, QTimer
    from PySide6.QtQml import QQmlExpression, qmlContext
    from tests.support.varakozas import var_feltetelre
    from support.jpeg_factory import make_jpeg

    window, controller, _library, _engine = qml_app
    edit_controller = _engine.rootContext().contextProperty("editController")
    controller._edit_controller_for_sync = edit_controller
    window.setProperty("placesPanelOpen", False)
    places_panel = window.findChild(QObject, "placesPanel")
    assert places_panel is not None
    assert places_panel.property("visible") is False
    from picasapy.index.queries import PhotoRecord as IndexedPhoto

    geo_location_reads = []
    original_location = IndexedPhoto.location.fget

    def counted_location(photo):
        geo_location_reads.append(photo.id)
        return original_location(photo)

    monkeypatch.setattr(IndexedPhoto, "location", property(counted_location))
    reload_observations = []
    slow_callbacks = []

    def observe_method(name, original):
        def wrapped(*args, **kwargs):
            started = time.monotonic()
            try:
                return original(*args, **kwargs)
            finally:
                elapsed_ms = (time.monotonic() - started) * 1000
                if elapsed_ms >= 50:
                    edit_controller = controller._edit_controller_for_sync
                    observation = {
                        "method": name,
                        "stage": state.get("stage"),
                        "elapsed_ms": round(elapsed_ms),
                        "photo_id": getattr(edit_controller, "_photo_id", ""),
                        "import_visible": controller._import_visible,
                        "grace_until": getattr(controller, "_sync_reload_grace_until", 0.0),
                    }
                    slow_callbacks.append(observation)
                    if name == "_reload":
                        observation["caller"] = traceback.extract_stack(limit=3)[-2].name
                        reload_observations.append(observation)

        return wrapped

    for method_name in (
        "_reload",
        "_refresh_view",
        "_show",
        "_update_feed_groups",
        "_update_status",
        "_emit_network_properties_changed",
        "_on_sync_progress",
    ):
        monkeypatch.setattr(
            controller,
            method_name,
            observe_method(method_name, getattr(controller, method_name)),
        )

    def observe_edit_method(name, original):
        def wrapped(*args, **kwargs):
            started = time.monotonic()
            try:
                return original(*args, **kwargs)
            finally:
                elapsed_ms = (time.monotonic() - started) * 1000
                if elapsed_ms >= 50:
                    slow_callbacks.append(
                        {
                            "method": f"edit.{name}",
                            "stage": state.get("stage"),
                            "elapsed_ms": round(elapsed_ms),
                            "photo_id": edit_controller._photo_id,
                        }
                    )

        return wrapped

    for method_name in (
        "_apply_network_edit_state",
        "_tool_property_values",
        "_emit_changed_tool_properties",
        "_preview_request",
        "_start_preview_worker",
        "_bump_revision",
        "_register_preview",
        "_restore_text_overlay_state",
    ):
        monkeypatch.setattr(
            edit_controller,
            method_name,
            observe_edit_method(method_name, getattr(edit_controller, method_name)),
        )
    viewer_image = window.findChild(QObject, "viewerImage")
    assert viewer_image is not None
    image_ready = QQmlExpression(
        qmlContext(viewer_image), viewer_image, "status === Image.Ready"
    )
    # Az éles platformokon a néző képe aszinkron töltődik. Az offscreen Qt
    # alapból szinkronra vált a #53-as GIL-holtpont elkerülésére; ennél a
    # fájlútvonalas méréstesztnél visszaállítjuk az éles út viselkedését.
    viewer_image.setProperty("asynchronous", True)
    slow_root = (tmp_path / "slow-network-root").resolve()
    slow_root.mkdir()
    for number in range(40):
        album = slow_root / f"album-{number:02}"
        album.mkdir()
        make_jpeg(album / "large.jpg", size=(3000, 4000))

    def under_slow_root(path) -> bool:
        try:
            value = os.path.normcase(os.path.abspath(os.fsdecode(os.fspath(path))))
        except (TypeError, ValueError):
            return False
        root = os.path.normcase(str(slow_root))
        return value == root or value.startswith(root + os.sep)

    def remote_root(path, *_args, **_kwargs):
        return str(slow_root) if under_slow_root(path) else None

    # A helyi tmp_path-ot csak a tesztben tekintjük hálózati meghajtónak;
    # a termékkód hálózati ágainak így valódi útvonalai futnak.
    import picasapy.halozati_ut as network_paths
    import picasapy.paths as path_helpers

    monkeypatch.setattr(network_paths, "fajlrendszer_gyoker", remote_root)
    monkeypatch.setattr(path_helpers, "is_network_path", lambda path: bool(remote_root(path)))
    for module in tuple(sys.modules.values()):
        if module is None or not getattr(module, "__name__", "").startswith("picasapy.app"):
            continue
        for name in ("fajlrendszer_gyoker", "halozati_gyoker", "is_network_path"):
            if name in vars(module):
                original = vars(module)[name]
                if callable(original):
                    monkeypatch.setattr(
                        module,
                        name,
                        lambda path, _name=name, _original=original: (
                            remote_root(path)
                            if _name != "is_network_path"
                            else bool(remote_root(path))
                        ) or (_original(path) if not remote_root(path) else None),
                    )

    main_thread = threading.main_thread()
    violations = []
    delayed_files = set()
    callers = {}
    text_layer_calls = []
    text_layer_call_starts = {}

    def record_slow_access(name, path, frame=None):
        if not under_slow_root(path):
            return
        path_text = os.fsdecode(os.fspath(path))
        if threading.current_thread() is main_thread:
            key = (name, path_text)
            violations.append(key)
            source_calls = tuple(
                f"{os.path.basename(item.filename)}:{item.lineno}:{item.name}"
                for item in traceback.extract_stack(frame, limit=30)
                if frame is not None
                and "/src/picasapy/" in item.filename.replace("\\", "/")
            ) if frame is not None else ()
            callers.setdefault(key, set()).add(source_calls[-6:])
        if name == "open" and Path(path_text).suffix.casefold() in {".jpg", ".jpeg"}:
            file_key = os.path.normcase(path_text)
            if file_key not in delayed_files:
                delayed_files.add(file_key)
                # Fájlonként fél másodpercet késleltetünk; a QTimer-őr közben
                # a GUI-szál bármely lassú hálózati hívását hibaként veszi.
                time.sleep(0.5)

    audit_active = {"enabled": True}

    def monitor_audit(event, args):
        if not audit_active["enabled"] or not args:
            return
        if event == "open":
            record_slow_access("open", args[0])
        elif event in {"os.scandir", "os.listdir"}:
            record_slow_access(event, args[0])

    def monitor_stat(frame, event, called):
        code = frame.f_code
        if (
            code.co_name == "hasTextLayerInSelection"
            and code.co_filename.replace("\\", "/").endswith(
                "/photo_ops_write_mixin.py"
            )
        ):
            frame_id = id(frame)
            if event == "call":
                text_layer_call_starts[frame_id] = time.monotonic()
            elif event == "return":
                started = text_layer_call_starts.pop(frame_id, None)
                if started is not None:
                    elapsed_ms = round((time.monotonic() - started) * 1000)
                    if elapsed_ms >= 10:
                        text_layer_calls.append(elapsed_ms)
        if event != "c_call" or called is not os.stat:
            return
        if threading.current_thread() is not main_thread:
            return
        for value in frame.f_locals.values():
            if isinstance(value, (str, bytes, os.PathLike)) and under_slow_root(value):
                record_slow_access("os.stat", value, frame)
                break

    sys.addaudithook(monitor_audit)
    request.addfinalizer(lambda: audit_active.__setitem__("enabled", False))
    previous_profile = sys.getprofile()
    sys.setprofile(monitor_stat)
    request.addfinalizer(lambda: sys.setprofile(previous_profile))

    # Az appablak már nyitva van, mielőtt a teljes útvonal mérését elkezdjük;
    # a startup első kirajzolása nem része a beolvasás alatti használatnak.
    window.show()
    assert var_feltetelre(
        qt_app,
        lambda: window.findChild(QObject, "photoGrid") is not None
        and window.findChild(QObject, "photoGrid").height() > 0,
        5,
    )

    loop = QEventLoop()
    state = {
        "done": False,
        "error": None,
        "stage": "add",
        "photo_revision": -1,
        "slow_row": None,
    }
    heartbeat = []
    beat_timer = QTimer()
    beat_timer.setInterval(10)
    beat_timer.timeout.connect(
        lambda: heartbeat.append((time.monotonic(), state["stage"]))
    )
    beat_timer.start()
    long_stall_stacks = []
    watchdog_stop = threading.Event()

    def sample_main_stack() -> None:
        while not watchdog_stop.wait(0.05):
            if heartbeat and time.monotonic() - heartbeat[-1][0] > 0.2:
                frame = sys._current_frames().get(main_thread.ident)
                if frame is not None and len(long_stall_stacks) < 8:
                    long_stall_stacks.append(
                        " ← ".join(
                            f"{os.path.basename(item.filename)}:{item.lineno}:{item.name}"
                            for item in traceback.extract_stack(frame, limit=18)
                        )
                    )

    watchdog = threading.Thread(target=sample_main_stack, daemon=True)
    watchdog.start()
    def finish(error=None):
        state["error"] = error
        state["done"] = True
        loop.quit()

    def poll():
        try:
            if state["stage"] == "add":
                if str(slow_root) in controller._roots:
                    # A NAS-on a felhasználó a hozzáadás után rögtön belép;
                    # nem várja meg, míg az egész könyvtár felkerül a feedbe.
                    controller.selectFolder(str(slow_root))
                    window.setProperty("viewerOpen", True)
                    state["stage"] = "viewer"
            elif state["stage"] == "viewer":
                viewer = window.findChild(QObject, "photoViewer")
                slow_group = next(
                    (
                        group
                        for group in controller._feed_groups
                        if under_slow_root(group["path"])
                    ),
                    None,
                )
                if slow_group is not None:
                    state["slow_row"] = int(slow_group["start"])
                else:
                    revision = controller.photos.revision
                    if revision != state["photo_revision"]:
                        state["photo_revision"] = revision
                        state["slow_row"] = next(
                            (
                                row
                                for row, photo in enumerate(controller.photos.photos)
                                if under_slow_root(photo.folder_path)
                            ),
                            None,
                        )
                slow_row = state["slow_row"]
                if viewer is not None and viewer.isVisible() and slow_row is not None:
                    viewer.setProperty("currentIndex", slow_row)
                    state["stage"] = "opening"
            elif state["stage"] == "opening":
                photo_grid = window.findChild(QObject, "photoGrid")
                assert photo_grid is not None
                assert photo_grid.property("count") == 0, (
                    "a néző mögötti könyvtárfeed modellje aktív maradt"
                )
                image = window.findChild(QObject, "viewerImage")
                source = image.property("source") if image is not None else None
                image_is_ready, image_ready_error = image_ready.evaluate()
                if (
                    source is not None
                    and source.toString()
                    and not image_ready_error
                    and image_is_ready
                    and not edit_controller._network_edit_load_pending
                ):
                    assert under_slow_root(edit_controller._image_path)
                    state["stage"] = "opened"
            elif state["stage"] == "opened":
                if not controller._sync_running and not controller._import_visible:
                    window.setProperty("viewerOpen", False)
                    state["stage"] = "return"
            elif state["stage"] == "return":
                photo_grid = window.findChild(QObject, "photoGrid")
                slow_root_visible = any(
                    under_slow_root(group["path"])
                    for group in controller._feed_groups
                )
                if (
                    not window.property("viewerOpen")
                    and photo_grid is not None
                    and photo_grid.property("count") > 0
                    and slow_root_visible
                ):
                    beat_timer.stop()
                    finish()
                    return
        except Exception as error:  # noqa: BLE001 — Qt timer callback jelentése
            finish(error)
            return
        QTimer.singleShot(20, poll)

    QTimer.singleShot(0, lambda: controller.addWatchedFolder(str(slow_root)))
    QTimer.singleShot(0, poll)
    QTimer.singleShot(
        30000,
        lambda: finish(
            TimeoutError(
                "a néző-útvonal nem fejeződött be "
                f"(szakasz: {state['stage']}, "
                f"sync: {controller._sync_running}, "
                f"import: {controller._import_visible}, "
                f"rows: {sum(group['count'] for group in controller._feed_groups if under_slow_root(group['path']))}, "
                f"photo_count: {controller.photos.rowCount()}, "
                f"photo_paths: {[photo.folder_path for photo in controller.photos.photos[:3]]}, "
                f"current: {controller._current_folder!r}/{controller._view_mode!r}, "
                f"import_count: {controller._import_new}/{controller._import_new_at_reload}, "
                f"changed: {getattr(controller, '_last_sync_changed', None)!r}, "
                f"photo_id: {edit_controller._photo_id!r}, "
                f"grace: {getattr(controller, '_sync_reload_grace_until', 0.0):.1f}, "
                f"deferred: {getattr(controller, '_deferred_sync_reload', False)})"
            )
        ),
    )
    loop.exec()
    beat_timer.stop()
    watchdog_stop.set()
    watchdog.join(timeout=10)
    assert state["error"] is None, f"a teljes mappa→néző út hibázott: {state['error']}"
    assert var_feltetelre(qt_app, lambda: controller.waitForBackgroundWorkers(0.05), 30)
    assert len(delayed_files) >= 4, (
        f"a lassú fájlrendszer őre csak {len(delayed_files)} képet késleltetett"
    )

    beat_gaps = [
        ((right[0] - left[0]) * 1000, left, right)
        for left, right in zip(heartbeat, heartbeat[1:], strict=False)
    ]
    max_gap_ms, gap_before, gap_after = max(beat_gaps, default=(0.0, (), ()))
    if violations:
        details = []
        for operation, path in dict.fromkeys(violations):
            call_sites = sorted(callers[(operation, path)])
            details.append(f"{operation}({os.path.relpath(path, slow_root)})")
            details.extend("  ← " + " ← ".join(site) for site in call_sites[:8])
        pytest.fail(
            f"a GUI-szál {len(violations)} lassú fájlműveletet végzett "
            f"({len(details)} egyedi út): " + "; ".join(details[:24])
        )
    visible_photo_ids = {photo.id for photo in controller.photos.photos}
    unshown_geo_reads = set(geo_location_reads) - visible_photo_ids
    assert not unshown_geo_reads, (
        "a rejtett térképes kötés a látható feeden kívüli képek GPS-adatait is "
        f"lekérdezte ({sorted(unshown_geo_reads)}; {len(visible_photo_ids)} látható kép)"
    )
    assert max_gap_ms < 500, (
        f"a mappa- és nézőút alatt {max_gap_ms:.0f} ms-re állt meg az eseményhurok; "
        f"főszál-minták: {long_stall_stacks}; "
        f"hasTextLayerInSelection hívások (≥10 ms): {text_layer_calls}; "
        f"szakasz: {gap_before} → {gap_after}; újratöltések: {reload_observations}; "
        f"lassú visszahívások: {slow_callbacks}"
    )
