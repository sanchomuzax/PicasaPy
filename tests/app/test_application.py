"""Bootstrap-segédek: gyökér-feloldás, fordító, XDG-útvonalak."""

import pytest

from picasapy.app import application


class TestResolveRoots:
    """⚠️ A konfig-könyvtárat a PLATFORM dönti el, nem az `XDG_CONFIG_HOME`.

    Ezek a tesztek eredetileg `XDG_CONFIG_HOME`-ot állítottak, és a
    windows-lábon némán elbuktak: a #1076 óta a windowsos ág a natív
    `%APPDATA%`-ból dolgozik, tehát az XDG-változó ott nem jelent semmit.
    A TERMÉK viselkedése helyes — a teszt feltevése volt platformfüggő.

    Ezért a `_config_dir`-t közvetlenül helyettesítjük: így az állítás arról
    szól, amiről szólni akar (a `_resolve_roots` a konfig-könyvtárból
    olvas), és mind a két lábon ugyanazt jelenti."""

    @pytest.fixture
    def konfig(self, tmp_path, monkeypatch):
        mappa = tmp_path / "picasapy"
        mappa.mkdir()
        monkeypatch.setattr(application, "_config_dir", lambda *a, **k: mappa)
        return mappa

    def test_argv_wins(self):
        assert application._resolve_roots(["prog", "/a", "/b"]) == ("/a", "/b")

    def test_watched_folders_fallback(self, konfig):
        (konfig / "WatchedFolders.txt").write_text(
            "/mnt/nas/fotok\n", encoding="utf-8"
        )
        assert application._resolve_roots(["prog"]) == ("/mnt/nas/fotok",)

    def test_no_config_empty(self, konfig):
        assert application._resolve_roots(["prog"]) == ()

    def test_watched_folders_lowercase_variant(self, konfig):
        # #145: élesben a fájlnév kisbetűsen is előfordul.
        (konfig / "watchedfolders.txt").write_text(
            "/mnt/nas/fotok\n", encoding="utf-8"
        )
        assert application._resolve_roots(["prog"]) == ("/mnt/nas/fotok",)


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


#: A platform-rögzítés a linux ághoz (#1076).
LINUX = "linux"


class TestXdgDirs:
    """⚠️ Az XDG-változók csak a LINUX ágra vonatkoznak.

    A #1076 óta a windowsos ág a natív `%LOCALAPPDATA%`-ból dolgozik, a
    macOS a sajátjából — az `XDG_DATA_HOME` ott nem jelent semmit. Ezek a
    tesztek ezért a platformot KIMONDVA rögzítik; enélkül a windows-CI-lábon
    a TERMÉK helyes viselkedése buktatja el őket, és a bukás azt sugallná,
    hogy a natív útvonal a hiba.
    """

    def test_dirs_respect_xdg_env(self, tmp_path, monkeypatch):
        monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "d"))
        monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path / "c"))
        monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "cfg"))
        assert application._data_dir(LINUX) == tmp_path / "d" / "picasapy"
        assert application._cache_dir(LINUX) == tmp_path / "c" / "picasapy"

    def test_data_location_override_wins_over_xdg(self, tmp_path, monkeypatch):
        # #368: a "Move Database" dialógus sikeres áthelyezés után ide írja
        # az új, EGYESÍTETT adatgyökeret — a következő induláskor ez nyer
        # az XDG-alapértelmezés fölött, mindkét útvonalnál (index + cache).
        from picasapy.app.data_location import write_data_root

        monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "d"))
        monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path / "c"))
        monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "cfg"))
        new_root = tmp_path / "athelyezett-adatok"
        write_data_root(tmp_path / "cfg" / "picasapy", new_root)

        assert application._data_dir(LINUX) == new_root
        assert application._cache_dir(LINUX) == new_root

    def test_no_override_file_keeps_xdg_default(self, tmp_path, monkeypatch):
        monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "d"))
        monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path / "c"))
        monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "cfg"))
        assert application._data_dir(LINUX) == tmp_path / "d" / "picasapy"
        assert application._cache_dir(LINUX) == tmp_path / "c" / "picasapy"


class TestAssets:
    def test_icon_and_logo_exist_and_load(self, qt_app):
        from PySide6.QtGui import QImage

        assets = application._APP_DIR / "assets"
        assert not QImage(str(assets / "icon.png")).isNull()
        assert (assets / "logo.svg").exists()

    def test_icon_has_taskbar_margin(self, qt_app):
        # 11-es issue + 37-es issue: a kör logó fehér háttér-korongon ül,
        # amely kicsit túllóg a logó szélén (tálca-méretben ~1–2 px).
        # A korong középen van, a sarkok átlátszók maradnak (kerek forma),
        # a perem pedig fehér.
        # 267-es issue: a Windows Start menüben/Asztalon a korábbi 82–90%-os
        # kitöltés még mindig láthatóan kisebbnek tűnt az eredeti Picasa 3
        # ikonnál, ezért a kitöltést tovább növeltük (~92–95%-ra) — ez a
        # #11/#37 óta tartó "ne tűnjön kicsinek" trend folytatása, csak
        # magasabb küszöbbel.
        # 325-ös issue: a bbox-kitöltés (ez a teszt) még a #267 utáni
        # ~92%-nál is zöld maradt, miközben a rajzolat KÖR alakja miatt a
        # ténylegesen kirajzolt (nem-átlátszó) pixel-terület csak a vászon
        # ~67%-át fedte — ez volt az igazi ok, amiért a felhasználó szerint
        # a logó "nem javult". A bbox felső korlátját ezért feloldottuk
        # ~99%-ra (a FILL_RATIO 0.94 → 0.98 emelésével, ld.
        # `tools/regenerate_icon.py`); a tényleges pixel-terület kitöltését
        # a `tests/support/test_icon.py` teszt méri és őrzi.
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
        assert image.width() * 0.90 <= content_w <= image.width() * 0.99
        assert image.height() * 0.90 <= content_h <= image.height() * 0.99
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
        monkeypatch.setattr(application, "_which", lambda name: f"/usr/bin/{name}")
        monkeypatch.setattr(
            application, "_run", lambda cmd, **kwargs: calls.append(cmd)
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
        monkeypatch.setattr(application, "_which", lambda name: None)
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


class TestWindowsAppId:
    """#67: Windows taskbar-ikon — explicit AppUserModelID-beállítás."""

    def test_sets_app_id_on_windows_win32(self, monkeypatch):
        # A SetCurrentProcessExplicitAppUserModelID hívása Win32 platformon
        calls = []

        def mock_set_app_id(app_id):
            calls.append(app_id)

        class MockShell32:
            SetCurrentProcessExplicitAppUserModelID = staticmethod(
                mock_set_app_id
            )

        class MockWindll:
            shell32 = MockShell32()

        # ⚠️ #1217: a platformot a modul `_platform` FOGANTYÚJÁN mondjuk ki.
        # Korábban a globális `sys` modul `platform`-ját írtuk át — az
        # `application` modulon KERESZTÜL, de ugyanazt az egy `sys`
        # objektumot, tehát a csere minden más modulra is hatott.
        monkeypatch.setattr(application, "_platform", lambda: "win32")
        monkeypatch.setattr(application, "ctypes", type("MockCtypes", (), {
            "windll": MockWindll()
        })())

        application._set_windows_app_id()

        assert calls == ["PicasaPy.PicasaPy"]

    def test_skips_non_windows_platforms(self, monkeypatch):
        # Linuxon/macOS-en nem csinál semmit
        calls = []

        def mock_set_app_id(app_id):
            calls.append(app_id)

        class MockShell32:
            SetCurrentProcessExplicitAppUserModelID = staticmethod(
                mock_set_app_id
            )

        class MockWindll:
            shell32 = MockShell32()

        monkeypatch.setattr(application, "_platform", lambda: "linux")
        monkeypatch.setattr(application, "ctypes", type("MockCtypes", (), {
            "windll": MockWindll()
        })())

        application._set_windows_app_id()

        assert calls == []

    def test_handles_attribute_error_gracefully(self, monkeypatch):
        # Régi Windows-verzió vagy hiányzó API — csendben kimarad
        monkeypatch.setattr(application, "_platform", lambda: "win32")

        class MockShell32:
            pass

        class MockWindll:
            shell32 = MockShell32()

        monkeypatch.setattr(application, "ctypes", type("MockCtypes", (), {
            "windll": MockWindll()
        })())

        # Nem dobjuk, csak csendben megálljunk
        application._set_windows_app_id()  # nem dobhat

    def test_handles_os_error_gracefully(self, monkeypatch):
        # Nem admin-felhasználó vagy rendszer-hiba — csendben kimarad
        calls = []

        def mock_set_app_id(app_id):
            calls.append(app_id)
            raise OSError("Access denied")

        class MockShell32:
            SetCurrentProcessExplicitAppUserModelID = staticmethod(
                mock_set_app_id
            )

        class MockWindll:
            shell32 = MockShell32()

        monkeypatch.setattr(application, "_platform", lambda: "win32")
        monkeypatch.setattr(application, "ctypes", type("MockCtypes", (), {
            "windll": MockWindll()
        })())

        application._set_windows_app_id()  # nem dobhat


class TestWireFileops:
    """#15: a fájlműveletek utáni célzott resync bekötése."""

    class _StubController:
        def __init__(self, roots):
            self.watchedFolders = list(roots)
            self.resynced = []
            self.removed = []  # #1227

        def resyncFolder(self, folder):
            self.resynced.append(folder)

        def removeDeletedRow(self, path):  # noqa: N802
            """#1227: a törölt sor azonnali kivétele a rácsból.

            A stubnak ismernie kell, különben a `photoDeleted` kezelője
            `AttributeError`-ral elszáll, és a resync SEM fut le — pont ezt
            fogta meg ez a teszt, amikor a lánc bekötése elkészült.
            """
            self.removed.append(path)
            return True

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

    def test_delete_removes_the_row_FIRST(self, wired):
        """#1227: a látható hatás előbb, az egyeztetés utána.

        Fordítva a felhasználó a szinkron végéig nézné a törölt képet —
        nagy könyvtárnál percekig.
        """
        fileops, stub, root = wired
        fileops.photoDeleted.emit(str(root / "banan" / "kep.jpg"))
        assert stub.removed == [str(root / "banan" / "kep.jpg")]
        assert stub.resynced == [str(root / "banan")]

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


class TestWindowIconPath:
    """#67: Windowson több méretű .ico a taskbar-ikonhoz — a futásidejű PNG
    kis méretre skálázása a taskbaron megbízhatatlan/késleltetett."""

    def test_windows_prefers_ico(self):
        path = application._window_icon_path(platform="win32")
        assert path.suffix == ".ico"
        assert path.exists()

    def test_linux_uses_png(self):
        path = application._window_icon_path(platform="linux")
        assert path.suffix == ".png"
        assert path.exists()


class TestRemainingSplashMs:
    """#240: a splash minimum-megjelenítési idejének számítása."""

    def test_fast_startup_waits_out_the_minimum(self):
        assert application._remaining_splash_ms(200, minimum_ms=1500) == 1300

    def test_slow_startup_finishes_immediately(self):
        assert application._remaining_splash_ms(4000, minimum_ms=1500) == 0

    def test_exact_boundary(self):
        assert application._remaining_splash_ms(1500, minimum_ms=1500) == 0


class TestEditControllerShutdownOnExit:
    """#547/#430: kilépéskor a szerkesztő háttér-renderét ÉRVÉNYTELENÍTENI
    kell, majd rövid ideig bevárni — különben a daemon-szál az interpreter
    leépítése közben emitálna egy már megsemmisült QObject-nek (SIGSEGV).

    A teljes kilépési út tesztből nem futtatható (valódi `app.exec()` kell
    hozzá), ezért a forrást ellenőrizzük: a két hívásnak az `app.exec()`
    UTÁN, a `return` ELŐTT kell állnia, ebben a sorrendben."""

    def _source(self) -> str:
        from pathlib import Path

        import picasapy.app.application as app_module

        return Path(app_module.__file__).read_text(encoding="utf-8")

    def test_invalidate_then_wait_after_exec(self):
        source = self._source()
        exec_at = source.index("exit_code = app.exec()")
        cancel_at = source.index("edit_controller.cancelPendingPreview()")
        wait_at = source.index("edit_controller.waitForBackgroundWorkers(")
        return_at = source.index("return exit_code")
        assert exec_at < cancel_at < wait_at < return_at, (
            "a szerkesztő háttér-renderének érvénytelenítése/bevárása nem a "
            "kilépési úton, helyes sorrendben áll"
        )

    def test_wait_has_a_bounded_timeout(self):
        """A perces rendert NEM várjuk végig — az emit-ág már érvénytelen,
        elég egy rövid, KORLÁTOS várakozás."""
        import re

        match = re.search(
            r"edit_controller\.waitForBackgroundWorkers\(([^)]*)\)", self._source()
        )
        assert match is not None
        timeout = match.group(1).strip()
        assert timeout not in ("", "None"), "korlátlan várakozás a kilépési úton"
        assert 0 < float(timeout) <= 5.0, f"eltúlzott kilépési várakozás: {timeout}"
