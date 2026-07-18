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
        (config / "WatchedFolders.txt").write_text("/mnt/nas/fotok\n", encoding="utf-8")
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

    def test_icon_has_taskbar_margin(self, qt_app):
        # 11-es issue: a taskbaron az ikon a teljes csempét kitöltötte.
        # Élő próba után a 66%-os kitöltés viszont túl kicsinek bizonyult:
        # a kör alakú rajzolat optikailag kisebbnek hat, mint a teli
        # négyzet-lapkás ikonok (pl. Claude), ezért 70–78% a célsáv,
        # középre igazítva.
        from PySide6.QtGui import QImage

        image = QImage(str(application._APP_DIR / "assets" / "icon.png"))
        image = image.convertToFormat(QImage.Format.Format_ARGB32)
        xs, ys = [], []
        for y in range(image.height()):
            for x in range(image.width()):
                if (image.pixel(x, y) >> 24) & 0xFF:
                    xs.append(x)
                    ys.append(y)
        assert xs, "az ikon teljesen átlátszó"
        content_w = max(xs) - min(xs) + 1
        content_h = max(ys) - min(ys) + 1
        assert image.width() * 0.70 <= content_w <= image.width() * 0.78
        assert image.height() * 0.70 <= content_h <= image.height() * 0.78
        # középre igazítás: a bal/jobb és felső/alsó margó közel azonos
        assert abs(min(xs) - (image.width() - 1 - max(xs))) <= 2
        assert abs(min(ys) - (image.height() - 1 - max(ys))) <= 2


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
        text = desktop.read_text(encoding="utf-8")
        assert "Icon=picasapy" in text
        assert "Name=PicasaPy" in text

    def test_idempotent(self, tmp_path, monkeypatch):
        monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))
        application._install_desktop_entry()
        desktop = tmp_path / "applications" / "picasapy.desktop"
        first_mtime = desktop.stat().st_mtime_ns
        application._install_desktop_entry()
        assert desktop.stat().st_mtime_ns == first_mtime  # nem írja újra

    def test_icon_change_refreshes_icon_cache(self, tmp_path, monkeypatch):
        # 35-ös issue: a panel a hicolor/icon-theme.cache-ből dolgozik;
        # ha az ikoncserét nem követi cache-frissítés, a felhasználó a
        # régi ikont látja, amíg kézzel nem fut gtk-update-icon-cache.
        monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))
        calls = []
        monkeypatch.setattr(
            application.shutil, "which", lambda name: f"/usr/bin/{name}"
        )
        monkeypatch.setattr(
            application.subprocess,
            "run",
            lambda cmd, **kwargs: calls.append(cmd),
        )
        application._install_desktop_entry()
        assert len(calls) == 1
        assert str(tmp_path / "icons" / "hicolor") in calls[0]
        calls.clear()
        application._install_desktop_entry()  # idempotens: nincs csere
        assert calls == []

    def test_missing_cache_tool_skipped_silently(self, tmp_path, monkeypatch):
        # Windowson (vagy eszköz híján) a cache-frissítés csendben kimarad.
        monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))
        monkeypatch.setattr(application.shutil, "which", lambda name: None)
        application._install_desktop_entry()  # nem dobhat
        assert (
            tmp_path / "icons" / "hicolor" / "256x256" / "apps" / "picasapy.png"
        ).exists()


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
