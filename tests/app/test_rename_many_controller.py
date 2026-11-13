"""AppController (PhotoOpsMixin): tömeges átnevezés (#366) — a tényleges
`renamePreview` célnevétől különálló, rögzített `renameSamplePreview` minta,
és a háttérszálon + resync végzett `renamePhotosMany`."""

import dataclasses

import pytest
from PySide6.QtCore import QLocale

from picasapy.fileops.rename import format_taken_at

from support.jpeg_factory import make_jpeg
from support.qt_wait import wait_for_photo_op


@pytest.fixture
def library(tmp_path):
    root = tmp_path / "kepek"
    root.mkdir()
    make_jpeg(
        root / "a.jpg", size=(800, 600), taken_at="2025:05:01 07:00:00",
    )
    make_jpeg(
        root / "b.jpg", size=(1024, 768), taken_at="2025:06:02 08:00:00",
    )
    make_jpeg(
        root / "c.jpg", size=(640, 480), taken_at="2025:07:03 09:00:00",
    )
    (root / ".picasa.ini").write_text(
        "[a.jpg]\nstar=yes\n[b.jpg]\ncaption=nyar\n[c.jpg]\nstar=no\n",
        encoding="utf-8",
    )
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
        tmp_path / "index.db",
        (str(library),),
        provider,
        settings=settings,
        watched_file=tmp_path / "WatchedFolders.txt",
    )
    ctl._reload()
    ctl.selectFolder(str(library))
    yield ctl
    assert ctl._wait_for_rename_workers(30.0), "az átnevező szál nem állt le"
    assert ctl.waitForBackgroundWorkers(30.0), "az átnevezés háttérszála nem állt le"


def _rows_by_name(controller, *names) -> list:
    photos = controller.photos.photos
    by_name = {p.name: i for i, p in enumerate(photos)}
    return [by_name[name] for name in names]


def _stamp(controller, name) -> str:
    """A fájl felvételi dátum-idő utótagja, a rendszer területi beállításával."""
    photo = next(p for p in controller.photos.photos if p.name == name)
    assert photo.taken_at, "a próbakép dátuma hiányzik"
    return format_taken_at(photo.taken_at, QLocale.system())


def _do_rename(controller, action) -> None:
    wait_for_photo_op(controller, action)


def test_rename_worker_does_not_capture_qt_controller(
    controller, monkeypatch
):
    """A fájlműveleti worker bemenetei ne tartsanak életben Qt-wrappert."""
    from PySide6.QtCore import QLocale, QObject

    targets = []

    class InertThread:
        def is_alive(self):
            return False

        def join(self, timeout=None):
            return None

    def capture_worker(target, **kwargs):
        targets.append(target)
        return InertThread()

    monkeypatch.setattr(controller, "_start_background", capture_worker)
    monkeypatch.setattr(controller, "_start_rename_result_dispatch", lambda: None)
    rows = _rows_by_name(controller, "a.jpg", "b.jpg")
    controller.renamePhotosMany(rows, "nyaralas", True, False)

    assert len(targets) == 1
    target = targets[0]
    freevars = dict(zip(
        target.__code__.co_freevars,
        (cell.cell_contents for cell in target.__closure__ or ()),
        strict=True,
    ))
    assert all(value is not controller for value in freevars.values())
    assert not any(
        isinstance(value, (QObject, QLocale)) for value in freevars.values()
    )


def test_rename_worker_formats_dates_before_starting(
    controller, monkeypatch
):
    """A QLocale-alapú dátumformázás a controller GUI-szálán történjen."""
    import threading

    import picasapy.fileops.rename as rename_module

    formatter_threads = []
    original_format_taken_at = rename_module.format_taken_at

    def track_formatter_thread(*args, **kwargs):
        formatter_threads.append(threading.get_ident())
        return original_format_taken_at(*args, **kwargs)

    monkeypatch.setattr(rename_module, "format_taken_at", track_formatter_thread)
    main_thread_id = threading.get_ident()
    dispatch_threads = []
    on_rename_done = controller._on_rename_batch_done

    def track_dispatch_thread(folders):
        dispatch_threads.append(threading.get_ident())
        on_rename_done(folders)

    monkeypatch.setattr(controller, "_on_rename_batch_done", track_dispatch_thread)
    rows = _rows_by_name(controller, "a.jpg", "b.jpg")
    _do_rename(
        controller,
        lambda: controller.renamePhotosMany(rows, "nyaralas", True, False),
    )

    assert formatter_threads
    assert set(formatter_threads) == {main_thread_id}
    assert dispatch_threads == [main_thread_id]


class TestRenamePreview:
    def test_first_file_no_suffix_by_default(self, controller):
        rows = _rows_by_name(controller, "a.jpg", "b.jpg")
        preview = controller.renamePreview(rows, "nyaralas", False, False)
        assert preview == "nyaralas.jpg"

    def test_date_and_size_suffix(self, controller):
        rows = _rows_by_name(controller, "a.jpg", "b.jpg")
        preview = controller.renamePreview(rows, "nyaralas", True, True)
        assert preview == f"nyaralas {_stamp(controller, 'a.jpg')} 800x600.jpg"

    def test_fixed_sample_ignores_selected_file_metadata(self, controller):
        # rontás-kontroll: picasapy.app.photo_ops_controller.RENAME_SAMPLE_DATE = "" → 1 failed
        photos = controller.photos.photos
        controller.photos.set_photos((
            dataclasses.replace(
                photos[0],
                name="a.webp",
                taken_at="2031-11-12T13:14:15",
                width=4032,
                height=3024,
            ),
        ) + photos[1:])

        rows = [0]
        assert controller.renameSamplePreview(rows, "  nyaralas  ", False, False) == (
            "nyaralas.jpg"
        )
        assert controller.renameSamplePreview(rows, "nyaralas", True, False) == (
            "nyaralas 08-01-2004 2-30-45 PM.jpg"
        )
        assert controller.renameSamplePreview(rows, "nyaralas", False, True) == (
            "nyaralas 640x480.jpg"
        )
        assert controller.renameSamplePreview(rows, "nyaralas", True, True) == (
            "nyaralas 08-01-2004 2-30-45 PM 640x480.jpg"
        )

    def test_flags_default_off_and_persist(self, controller):
        assert controller.renameUseDate() is False
        assert controller.renameUseSize() is False
        controller.setRenameUseFlags(True, False)
        assert controller.renameUseDate() is True
        assert controller.renameUseSize() is False
        controller.setRenameUseFlags(False, True)
        assert controller.renameUseDate() is False
        assert controller.renameUseSize() is True

    def test_empty_base_name_gives_empty_preview(self, controller):
        rows = _rows_by_name(controller, "a.jpg")
        assert controller.renamePreview(rows, "  ", False, False) == ""

    def test_empty_selection_gives_empty_preview(self, controller):
        assert controller.renamePreview([], "nev", False, False) == ""


class TestRenamePhotosMany:
    def test_renames_with_sequence_and_syncs_grid(self, controller, library):
        rows = _rows_by_name(controller, "a.jpg", "b.jpg")
        _do_rename(
            controller,
            lambda: controller.renamePhotosMany(rows, "nyaralas", False, False),
        )
        assert (library / "nyaralas.jpg").exists()
        assert (library / "nyaralas-001.jpg").exists()
        assert not (library / "a.jpg").exists()
        assert not (library / "b.jpg").exists()
        names = {p.name for p in controller.photos.photos}
        assert names == {"nyaralas.jpg", "nyaralas-001.jpg", "c.jpg"}

    def test_ini_sections_follow_the_rename(self, controller, library):
        rows = _rows_by_name(controller, "a.jpg", "b.jpg")
        _do_rename(
            controller,
            lambda: controller.renamePhotosMany(rows, "nyaralas", False, False),
        )
        from picasapy.ini import load_document

        document = load_document(library / ".picasa.ini")
        assert document.section("nyaralas.jpg").get("star") == "yes"
        assert document.section("nyaralas-001.jpg").get("caption") == "nyar"

    def test_date_and_size_suffix_end_to_end(self, controller, library):
        stamp_a = _stamp(controller, "a.jpg")
        stamp_b = _stamp(controller, "b.jpg")
        rows = _rows_by_name(controller, "a.jpg", "b.jpg")
        _do_rename(
            controller,
            lambda: controller.renamePhotosMany(rows, "nyar", True, True),
        )
        assert (library / f"nyar {stamp_a} 800x600.jpg").exists()
        assert (library / f"nyar {stamp_b} 1024x768.jpg").exists()

    def test_occupied_batch_target_uses_suffix_and_keeps_the_occupant(
        self, controller, library
    ):
        # az első fájl célneve "b.jpg" lenne, de ezt a köteg másik eleme
        # jelenleg foglalja, ezért a feloldás a következő szabad nevet adja.
        rows = _rows_by_name(controller, "a.jpg", "b.jpg")
        failures = []
        controller.syncFailed.connect(lambda msg: failures.append(msg))
        _do_rename(
            controller,
            lambda: controller.renamePhotosMany(rows, "b", False, False),
        )
        assert not failures
        assert (library / "b-001.jpg").exists()
        assert not (library / "a.jpg").exists()
        assert (library / "b.jpg").exists()

    def test_runtime_failure_reports_and_refreshes_partial_renames(
        self, controller, library, monkeypatch
    ):
        import picasapy.fileops.rename as rename_module

        rows = _rows_by_name(controller, "a.jpg", "b.jpg", "c.jpg")
        real_rename = rename_module._rename
        calls = 0

        def fail_on_third(source, target):
            nonlocal calls
            calls += 1
            if calls == 3:
                raise PermissionError("injected third-file failure")
            real_rename(source, target)

        monkeypatch.setattr(rename_module, "_rename", fail_on_third)
        failures = []
        controller.syncFailed.connect(failures.append)
        _do_rename(
            controller,
            lambda: controller.renamePhotosMany(rows, "trip", False, False),
        )

        assert failures
        assert "trip.jpg" in failures[-1]
        assert "trip-001.jpg" in failures[-1]
        assert "c.jpg" in failures[-1]
        assert (library / "trip.jpg").exists()
        assert (library / "trip-001.jpg").exists()
        assert not (library / "a.jpg").exists()
        assert not (library / "b.jpg").exists()
        assert (library / "c.jpg").exists()
        assert {photo.name for photo in controller.photos.photos} == {
            "trip.jpg", "trip-001.jpg", "c.jpg",
        }

    def test_empty_base_name_is_a_no_op(self, controller, library):
        rows = _rows_by_name(controller, "a.jpg", "b.jpg")
        controller.renamePhotosMany(rows, "   ", False, False)
        assert (library / "a.jpg").exists()
        assert (library / "b.jpg").exists()


class TestBackgroundThreadTeardown:
    """#438 (a #430 SIGSEGV-osztály maradéka): a tömeges átnevezés
    háttérszála bevárható legyen, mielőtt a controller megsemmisül."""

    def test_wait_without_a_run_returns_immediately(self, controller):
        assert controller.waitForBackgroundWorkers(0.0)

    def test_wait_joins_the_worker_thread(self, controller, library):
        rows = _rows_by_name(controller, "a.jpg", "b.jpg")
        _do_rename(
            controller,
            lambda: controller.renamePhotosMany(rows, "nyaralas", False, False),
        )
        assert controller.waitForBackgroundWorkers(30.0)
        assert not controller.backgroundWorkersRunning()

    def test_wait_joins_until_the_thread_itself_exits(
        self, controller, library, qt_app, monkeypatch
    ):
        """A worker a feladat vége után is élhet a szál kilépéséig (#6858)."""
        import threading

        import picasapy.app.worker_thread as worker_thread

        entered_tail = threading.Event()
        release_tail = threading.Event()
        threads = []
        original_thread = worker_thread._Thread

        class TailHeldThread(original_thread):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                threads.append(self)

            def run(self):
                super().run()
                if self.name == "picasapy-rename":
                    entered_tail.set()
                    release_tail.wait(30.0)

        monkeypatch.setattr(worker_thread, "_Thread", TailHeldThread)
        rows = _rows_by_name(controller, "a.jpg", "b.jpg")
        controller.renamePhotosMany(rows, "nyaralas", False, False)

        assert entered_tail.wait(30.0), "az átnevező worker nem ért a szál végéhez"
        rename_thread = next(t for t in threads if t.name == "picasapy-rename")
        wait_started = threading.Event()
        original_wait = controller._wait_for_rename_workers
        releaser = None

        def observed_wait(timeout_s=None):
            wait_started.set()
            return original_wait(timeout_s)

        monkeypatch.setattr(controller, "_wait_for_rename_workers", observed_wait)
        try:
            assert rename_thread.is_alive()
            assert not original_wait(0.0), (
                "a bevárás késznek jelezte a még élő átnevező szálat"
            )
            releaser = threading.Thread(
                target=lambda: (wait_started.wait(30.0), release_tail.set())
            )
            releaser.start()
            assert controller._wait_for_rename_workers(None)
            assert not rename_thread.is_alive(), "a bevárás után a szál még fut"
        finally:
            wait_started.set()
            release_tail.set()
            if releaser is not None:
                releaser.join(30.0)

        qt_app.processEvents()
