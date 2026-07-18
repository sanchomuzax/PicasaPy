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
