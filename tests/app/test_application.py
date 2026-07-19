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


class TestDialogPolicy:
    def test_windows_uses_native_dialogs(self):
        # #58: Windowson a natív mappaválasztó kell — meghajtók, hálózati
        # helyek és ékezetes mappák csak abból érhetők el rendesen.
        assert application._force_qml_dialogs("win32") is False

    def test_other_platforms_use_qml_dialogs(self):
        # Linuxon/macOS-en marad a saját világos QML-dialógus (a rendszer
        # sötét témájú választója helyett — rögzített dizájn-döntés).
        assert application._force_qml_dialogs("linux") is True
        assert application._force_qml_dialogs("darwin") is True


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
        # 11-es issue + 37-es issue: a kör logó fehér háttér-korongon ül,
        # amely kicsit túllóg a logó szélén (tálca-méretben ~1–2 px).
        # A korong a vászon 82–90%-a, középen; a sarkok átlátszók
        # maradnak (kerek forma), a perem pedig fehér.
        from PySide6.QtGui import QImage, qAlpha, qBlue, qGreen, qRed

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
        assert image.width() * 0.82 <= content_w <= image.width() * 0.90
        assert image.height() * 0.82 <= content_h <= image.height() * 0.90
        # középre igazítás: a bal/jobb és felső/alsó margó közel azonos
        assert abs(min(xs) - (image.width() - 1 - max(xs))) <= 2
        assert abs(min(ys) - (image.height() - 1 - max(ys))) <= 2
        # kerek forma: a sarkok átlátszók
        for cx, cy in ((0, 0), (image.width() - 1, 0), (0, image.height() - 1),
                       (image.width() - 1, image.height() - 1)):
            assert qAlpha(image.pixel(cx, cy)) == 0
        # a perem fehér: a korong tetejének közepe (pár px-szel beljebb)
        top = image.pixel(image.width() // 2, min(ys) + 3)
        assert min(qRed(top), qGreen(top), qBlue(top)) >= 240


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


class TestThumbnailCacheSize:
    """#83: a rács legnagyobb fokozatában is élesen jelenjen meg a
    bélyegkép — a cache-cél sose legyen kisebb a legnagyobb rács-
    megjelenítésnél (a devicePixelRatio-t is figyelembe véve)."""

    def test_standard_dpr_matches_max_grid_size(self):
        assert (
            application._thumbnail_cache_size(1.0)
            == application._GRID_MAX_THUMB_PX
        )

    def test_hidpi_scales_up_the_cache_target(self):
        assert (
            application._thumbnail_cache_size(2.0)
            == application._GRID_MAX_THUMB_PX * 2
        )

    def test_fractional_dpr_rounds_up_never_down(self):
        # 1.5x DPR-nél felfelé kerekítünk — a cél sose essen a küszöb alá,
        # a ThumbnailCache úgyis csak kicsinyít, sosem nagyít.
        assert application._thumbnail_cache_size(1.5) == 384

    def test_sub_unity_dpr_is_clamped_to_one(self):
        assert (
            application._thumbnail_cache_size(0.5)
            == application._GRID_MAX_THUMB_PX
        )


class TestScreenDevicePixelRatio:
    def test_primary_screen_ratio_is_used(self, qt_app):
        ratio = application._screen_device_pixel_ratio(qt_app)
        assert ratio == qt_app.primaryScreen().devicePixelRatio()

    def test_missing_screen_falls_back_to_one(self, qt_app, monkeypatch):
        monkeypatch.setattr(qt_app, "primaryScreen", lambda: None)
        assert application._screen_device_pixel_ratio(qt_app) == 1.0


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


class TestWireFileops:
    """#15: a fájlműveletek utáni célzott resync bekötése."""

    class _StubController:
        def __init__(self, roots):
            self.watchedFolders = list(roots)
            self.resynced = []

        def resyncFolder(self, folder):
            self.resynced.append(folder)

    @pytest.fixture
    def wired(self, qt_app, tmp_path):
        from picasapy.app.fileops_controller import FileOpsController

        root = tmp_path / "kepek"
        (root / "alma").mkdir(parents=True)
        (root / "banan").mkdir()
        stub = self._StubController([str(root)])
        fileops = FileOpsController()
        application.wire_fileops(fileops, stub)
        return fileops, stub, root

    def test_rename_resyncs_parent_folder(self, wired):
        fileops, stub, root = wired
        fileops.photoRenamed.emit(
            str(root / "alma" / "a.jpg"), str(root / "alma" / "b.jpg")
        )
        assert stub.resynced == [str(root / "alma")]

    def test_move_resyncs_both_folders(self, wired):
        fileops, stub, root = wired
        fileops.photoMoved.emit(
            str(root / "alma" / "a.jpg"), str(root / "banan" / "a.jpg")
        )
        assert sorted(stub.resynced) == [str(root / "alma"), str(root / "banan")]

    def test_delete_resyncs_parent_folder(self, wired):
        fileops, stub, root = wired
        fileops.photoDeleted.emit(str(root / "banan" / "c.jpg"))
        assert stub.resynced == [str(root / "banan")]

    def test_paths_outside_watched_roots_are_skipped(self, wired, tmp_path):
        # figyelt körön kívüli mappát (pl. export-cél) nem szinkronizálunk
        # az indexbe — az ottragadt idegen gyökér a #58 tanulsága
        fileops, stub, root = wired
        outside = tmp_path / "kivul" / "a.jpg"
        fileops.photoMoved.emit(str(root / "alma" / "a.jpg"), str(outside))
        assert stub.resynced == [str(root / "alma")]
