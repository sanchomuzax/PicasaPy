"""Bootstrap-segédek: gyökér-feloldás, fordító, XDG-útvonalak."""

import pytest

from picasapy.app import application


class TestResolveRoots:
    def test_argv_wins(self):
        assert application._resolve_roots(["prog", "/a", "/b"]) == ("/a", "/b")

    def test_watched_folders_fallback(self, tmp_path, monkeypatch):
        monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
        config = tmp_path / "picasapy"
        config.mkdir()
        (config / "WatchedFolders.txt").write_text("/mnt/nas/fotok\n")
        assert application._resolve_roots(["prog"]) == ("/mnt/nas/fotok",)

    def test_no_config_empty(self, tmp_path, monkeypatch):
        monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
        assert application._resolve_roots(["prog"]) == ()


class TestXdgDirs:
    def test_dirs_respect_xdg_env(self, tmp_path, monkeypatch):
        monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "d"))
        monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path / "c"))
        assert application._data_dir() == tmp_path / "d" / "picasapy"
        assert application._cache_dir() == tmp_path / "c" / "picasapy"


class TestAssets:
    def test_icon_and_logo_exist_and_load(self, qt_app):
        from PySide6.QtGui import QImage

        assets = application._APP_DIR / "assets"
        assert not QImage(str(assets / "icon.png")).isNull()
        assert (assets / "logo.svg").exists()


class TestSingleInstance:
    def test_second_lock_fails_while_held(self, tmp_path):
        lock = application._acquire_instance_lock(tmp_path)
        assert lock is not None
        assert application._acquire_instance_lock(tmp_path) is None
        lock.unlock()
        assert application._acquire_instance_lock(tmp_path) is not None


class TestDesktopEntry:
    def test_installs_desktop_file_and_icon(self, tmp_path, monkeypatch):
        monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))
        application._install_desktop_entry()
        desktop = tmp_path / "applications" / "picasapy.desktop"
        icon = tmp_path / "icons" / "hicolor" / "256x256" / "apps" / "picasapy.png"
        assert desktop.exists() and icon.exists()
        text = desktop.read_text()
        assert "Icon=picasapy" in text
        assert "Name=PicasaPy" in text

    def test_idempotent(self, tmp_path, monkeypatch):
        monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))
        application._install_desktop_entry()
        desktop = tmp_path / "applications" / "picasapy.desktop"
        first_mtime = desktop.stat().st_mtime_ns
        application._install_desktop_entry()
        assert desktop.stat().st_mtime_ns == first_mtime  # nem írja újra


class TestTranslator:
    def test_hungarian_loads_and_translates(self, qt_app, monkeypatch):
        monkeypatch.setenv("PICASAPY_LANG", "hu_HU")
        translator = application._install_translator(qt_app)
        assert translator is not None
        from PySide6.QtCore import QCoreApplication

        assert (
            QCoreApplication.translate("AppController", "0 pictures") == "0 kép"
        )
        qt_app.removeTranslator(translator)

    def test_unknown_language_falls_back(self, qt_app, monkeypatch):
        monkeypatch.setenv("PICASAPY_LANG", "zz_ZZ")
        assert application._install_translator(qt_app) is None
