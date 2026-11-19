"""#7244: a hálózati fájlolvasás nem állíthatja meg a GUI eseményhurkát."""

from __future__ import annotations

import threading
import time
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest
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


def test_teljes_nezo_utvonal_nem_olvas_lassu_gyokerbol_a_foszalon(
    qml_app, qt_app, tmp_path, monkeypatch
):
    """A teljes mappa→néző→vissza út egyetlen lassú I/O-t se végezhet a GUI-szálon."""
    import builtins
    import io
    import os
    import sys
    import traceback

    from PySide6.QtCore import QObject, QEventLoop, QTimer
    from tests.support.varakozas import var_feltetelre
    from support.jpeg_factory import make_jpeg

    window, controller, _library, _engine = qml_app
    slow_root = (tmp_path / "slow-network-root").resolve()
    slow_root.mkdir()
    for number in range(40):
        make_jpeg(slow_root / f"large-{number:02}.jpg", size=(640, 480))

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

    def monitor(name, original):
        def wrapped(path, *args, **kwargs):
            if under_slow_root(path):
                path_text = os.fsdecode(os.fspath(path))
                if threading.current_thread() is main_thread:
                    key = (name, path_text)
                    violations.append(key)
                    source_calls = tuple(
                        f"{os.path.basename(frame.filename)}:{frame.lineno}:{frame.name}"
                        for frame in traceback.extract_stack(limit=30)[:-1]
                        if "/src/picasapy/" in frame.filename.replace("\\", "/")
                    )
                    callers.setdefault(key, set()).add(source_calls[-6:])
                if Path(path_text).suffix.casefold() in {".jpg", ".jpeg"}:
                    file_key = os.path.normcase(path_text)
                    if file_key not in delayed_files:
                        delayed_files.add(file_key)
                        # A lassú megosztás olvasása fájlonként fél másodperc.
                        # A késleltetés a worker-olvasásra is érvényes, így a
                        # nézőút ténylegesen a beolvasás közben fut.
                        time.sleep(0.5)
            return original(path, *args, **kwargs)

        return wrapped

    for name in ("stat", "open", "scandir", "listdir"):
        monkeypatch.setattr(os, name, monitor(f"os.{name}", getattr(os, name)))
    monkeypatch.setattr(os, "open", monitor("os.open", os.open))
    monkeypatch.setattr(builtins, "open", monitor("open", builtins.open))
    monkeypatch.setattr(io, "open", monitor("io.open", io.open))

    loop = QEventLoop()
    state = {"done": False, "error": None, "stage": "add"}
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
                if str(slow_root) in controller._roots and any(
                    photo.folder_path == str(slow_root)
                    for photo in controller.photos.photos
                ):
                    state["stage"] = "select"
                    controller.selectFolder(str(slow_root))
                    window.show()
                    window.setProperty("viewerOpen", True)
                    state["stage"] = "viewer"
            elif state["stage"] == "viewer":
                viewer = window.findChild(QObject, "photoViewer")
                if viewer is not None and viewer.isVisible():
                    viewer.setProperty("currentIndex", 0)
                    state["stage"] = "opening"
            elif state["stage"] == "opening":
                image = window.findChild(QObject, "viewerImage")
                source = image.property("source") if image is not None else None
                if source is not None and source.toString():
                    state["stage"] = "opened"
                    beat_timer.stop()
            elif state["stage"] == "opened":
                window.setProperty("viewerOpen", False)
                state["stage"] = "return"
            elif state["stage"] == "return":
                if not window.property("viewerOpen"):
                    finish()
                    return
        except Exception as error:  # noqa: BLE001 — Qt timer callback jelentése
            finish(error)
            return
        QTimer.singleShot(20, poll)

    QTimer.singleShot(0, lambda: controller.addWatchedFolder(str(slow_root)))
    QTimer.singleShot(0, poll)
    QTimer.singleShot(30000, lambda: finish(TimeoutError("a néző-útvonal nem fejeződött be")))
    loop.exec()
    beat_timer.stop()
    watchdog_stop.set()
    watchdog.join(timeout=1)
    assert state["error"] is None, f"a teljes mappa→néző út hibázott: {state['error']}"
    assert var_feltetelre(qt_app, lambda: controller.waitForBackgroundWorkers(0.05), 30)
    assert len(delayed_files) >= 4, (
        f"a lassú fájlrendszer őre csak {len(delayed_files)} képet késleltetett"
    )

    beat_gaps = [
        ((right[0] - left[0]) * 1000, left, right)
        for left, right in zip(heartbeat, heartbeat[1:])
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
    assert max_gap_ms < 200, (
        f"a mappa- és nézőút alatt {max_gap_ms:.0f} ms-re állt meg az eseményhurok; "
        f"főszál-minták: {long_stall_stacks}; "
        f"szakasz: {gap_before} → {gap_after}"
    )
