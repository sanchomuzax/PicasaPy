"""Lassú SMB/GVFS útvonalak ne tartsák fel a felületet (#7048)."""

from __future__ import annotations

import posixpath
import threading
import time

import pytest
from support.qt_wait import varj_feltetelre

from picasapy import halozati_ut, paths


def _mountok(monkeypatch, *mounts):
    """Helyi, szintetikus mount-tábla; NAS-hoz nem nyúl."""
    monkeypatch.setattr(
        halozati_ut,
        "_mount_records",
        lambda: tuple(mounts),
        raising=False,
    )


@pytest.fixture(autouse=True)
def _halozati_allapot_tisztitasa():
    halozati_ut._alaphelyzet()
    yield
    halozati_ut._alaphelyzet()


@pytest.mark.parametrize(
    ("mountpoint", "fstype", "path"),
    [
        (
            "/mnt/picasapy-slow",
            "cifs",
            "/mnt/picasapy-slow/kepek/2026/../2026/a.jpg",
        ),
        (
            "/run/user/1000/gvfs",
            "fuse.gvfsd-fuse",
            "/run/user/1000/gvfs/smb-share:server=nas,share=photos/2026/a.jpg",
        ),
    ],
)
def test_linuxos_halozati_utvonal_lexikalis_normalizalasa_nem_resolve_oz(
    monkeypatch, mountpoint, fstype, path
):
    monkeypatch.setattr(paths, "_platform", lambda: "linux")
    _mountok(monkeypatch, (mountpoint, fstype))
    main_thread = threading.get_ident()
    calls = []
    original = paths._feloldas

    def slow_resolve(value):
        calls.append(threading.get_ident())
        threading.Event().wait(0.25)
        return original(value)

    monkeypatch.setattr(paths, "_feloldas", slow_resolve)
    started = time.monotonic()
    result = paths.normalize_path(path)
    elapsed = time.monotonic() - started

    assert result == posixpath.normpath(path)
    assert calls == [], "a hálózati csatolást Path.resolve() érte"
    assert elapsed < 0.15, f"az útvonal-normalizálás {elapsed:.3f} s-ig várt"
    assert main_thread == threading.get_ident()


def test_mapped_windows_meghajto_lexikalis_normalizalasa_nem_resolve_oz(
    monkeypatch,
):
    monkeypatch.setattr(paths, "_platform", lambda: "win32")
    monkeypatch.setattr(
        halozati_ut,
        "_query_dos_device",
        lambda drive: r"\Device\Mup\;Z:000000000000\server\photos"
        if drive == "Z:"
        else None,
        raising=False,
    )
    calls = []
    original = paths._feloldas

    def slow_resolve(value):
        calls.append(value)
        threading.Event().wait(0.25)
        return original(value)

    monkeypatch.setattr(paths, "_feloldas", slow_resolve)
    started = time.monotonic()
    result = paths.normalize_path(r"Z:\Photo\2026\..\a.jpg")
    elapsed = time.monotonic() - started

    assert result == r"Z:\Photo\a.jpg"
    assert calls == [], "a leképezett hálózati meghajtót Path.resolve() érte"
    assert elapsed < 0.15, f"a meghajtó normalizálása {elapsed:.3f} s-ig várt"


def test_linuxos_halozati_mount_elerehetosege_idokorlatos(monkeypatch):
    monkeypatch.setattr(halozati_ut, "_platform", lambda: "linux", raising=False)
    _mountok(monkeypatch, ("/mnt/picasapy-slow", "cifs"))
    main_thread = threading.get_ident()
    started_io = threading.Event()
    release_io = threading.Event()
    finished_io = threading.Event()
    io_threads = []

    def slow_probe(root):
        assert root == "/mnt/picasapy-slow"
        io_threads.append(threading.get_ident())
        started_io.set()
        release_io.wait(1.0)
        finished_io.set()
        return True

    monkeypatch.setattr(halozati_ut, "_letezik", slow_probe)
    started = time.monotonic()
    available = halozati_ut.elerheto(
        "/mnt/picasapy-slow/kepek/a.jpg", idokorlat_s=0.05
    )
    elapsed = time.monotonic() - started

    assert available is False, "a lassú SMB-próba nem futott le az időkorláton"
    assert elapsed < 0.2, f"az elérhetőség {elapsed:.3f} s-ig fogta a hívót"
    assert started_io.wait(0.2), "a hálózati próba nem indult el"
    assert main_thread not in io_threads, "a mount ellenőrzése a fő szálon futott"
    release_io.set()
    assert finished_io.wait(1.0), "a szimulált mount-ellenőrzés beragadt"


@pytest.fixture
def app_controller(qt_app, tmp_path):
    from PySide6.QtCore import QSettings

    from picasapy.app.controller import AppController
    from picasapy.app.thumbnail_provider import ThumbnailProvider
    from picasapy.index import open_index
    from picasapy.thumbs import ThumbnailCache

    db_path = tmp_path / "index.db"
    with open_index(db_path):
        pass
    settings = QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat)
    settings.setValue("view/showOnlyBigImages", False)
    provider = ThumbnailProvider(ThumbnailCache(tmp_path / "thumbs", size=32))
    controller = AppController(
        db_path,
        (),
        provider,
        settings=settings,
        watched_file=tmp_path / "WatchedFolders.txt",
    )
    yield controller
    assert controller.waitForBackgroundWorkers(5.0)
    controller.shutdown()


def test_linuxos_halozati_mappaleiras_hatterben_olvasodik(
    qt_app, app_controller, monkeypatch
):
    from picasapy.app import controller_content_info_mixin as content_module

    path = "/mnt/picasapy-slow/album"
    _mountok(monkeypatch, ("/mnt/picasapy-slow", "cifs"))
    main_thread = threading.get_ident()
    read_threads = []
    release_io = threading.Event()

    def slow_description(_path):
        read_threads.append(threading.get_ident())
        release_io.wait(0.5)
        return "NAS leírás"

    monkeypatch.setattr(
        content_module.ContentInfoMixin,
        "_read_folder_description",
        staticmethod(slow_description),
    )
    started = time.monotonic()
    assert app_controller.folderDescriptionOf(path) == ""
    elapsed = time.monotonic() - started

    assert elapsed < 0.15, f"a leíráskérés {elapsed:.3f} s-ig blokkolt"
    assert main_thread not in read_threads, "a .picasa.ini olvasása a fő szálon futott"
    qt_app.processEvents()
    release_io.set()
    assert app_controller.waitForBackgroundWorkers(2.0)
    assert varj_feltetelre(
        qt_app, lambda: app_controller._descriptions.get(path) == "NAS leírás"
    )
    assert app_controller.folderDescriptionOf(path) == "NAS leírás"


def test_halozati_mappak_felvetele_es_egyszeri_keresese_hatterben_validalodik(
    qt_app, app_controller, monkeypatch
):
    from picasapy.app import library_controller_folders as folders_module

    mountpoint = "/mnt/picasapy-slow"
    watch_path = mountpoint + "/figyelt"
    once_path = mountpoint + "/egyszeri"
    _mountok(monkeypatch, (mountpoint, "cifs"))
    main_thread = threading.get_ident()
    started_io = threading.Event()
    release_io = threading.Event()
    io_threads = []
    original_is_dir = folders_module._is_directory

    def slow_is_dir(path):
        if str(path) in {watch_path, once_path}:
            io_threads.append(threading.get_ident())
            started_io.set()
            release_io.wait(0.5)
            return True
        return original_is_dir(path)

    monkeypatch.setattr(folders_module, "_is_directory", slow_is_dir)
    submitted = []

    class Queue:
        def submit(self, worker, *, name):
            submitted.append((worker, name))

    app_controller._iro_sor = Queue()
    app_controller._persist_roots = lambda: None
    app_controller._restart_watcher = lambda: None
    app_controller._make_progress_emitter = lambda **_kwargs: None
    app_controller._make_should_stop = lambda _path: None
    app_controller._cancel_event = lambda _path: threading.Event()

    started = time.monotonic()
    app_controller.addWatchedFolder(watch_path)
    app_controller.scanFolderOnce(once_path)
    elapsed = time.monotonic() - started

    assert elapsed < 0.15, f"a hálózati mappaművelet {elapsed:.3f} s-ig blokkolt"
    assert started_io.wait(0.2), "a mappaellenőrzés nem indult el"
    qt_app.processEvents()
    assert main_thread not in io_threads, "a Path.is_dir a fő szálon futott"
    release_io.set()
    assert varj_feltetelre(
        qt_app,
        lambda: watch_path in app_controller._roots and len(submitted) == 2,
    )
    assert len(io_threads) == 2
