"""Platformfüggő alkalmazás-adatútvonalak és Windows-migráció (#1076)."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from picasapy.app import application
from picasapy.app.data_location import write_data_root
from picasapy.app.platform_storage import (
    StorageMigrationError,
    default_storage_paths,
    legacy_windows_storage_paths,
    migrate_legacy_windows_storage,
)
from picasapy.app.startup_status import StartupStatus


def _windows_env(tmp_path: Path) -> dict[str, str]:
    return {
        "LOCALAPPDATA": str(tmp_path / "AppData" / "Local"),
        "APPDATA": str(tmp_path / "AppData" / "Roaming"),
        # A régi PicasaPy pontosan ezeket az XDG-helyeket használta
        # Windowson is; az új alapértelmezésnek ezeket figyelmen kívül
        # kell hagynia, a migrációnak viszont innen kell átvennie.
        "XDG_DATA_HOME": str(tmp_path / "legacy" / "data"),
        "XDG_CACHE_HOME": str(tmp_path / "legacy" / "cache"),
        "XDG_CONFIG_HOME": str(tmp_path / "legacy" / "config"),
    }


def _create_index(path: Path, value: str = "meglevő-index") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as connection:
        connection.execute("CREATE TABLE marker (value TEXT NOT NULL)")
        connection.execute("INSERT INTO marker VALUES (?)", (value,))


def _index_value(path: Path) -> str:
    with sqlite3.connect(path) as connection:
        return str(connection.execute("SELECT value FROM marker").fetchone()[0])


class TestDefaultStoragePaths:
    def test_linux_xdg_viselkedes_bitre_valtozatlan(self, tmp_path):
        env = {
            "XDG_DATA_HOME": str(tmp_path / "d"),
            "XDG_CACHE_HOME": str(tmp_path / "c"),
            "XDG_CONFIG_HOME": str(tmp_path / "cfg"),
        }

        paths = default_storage_paths("linux", environ=env, home=tmp_path / "home")

        assert paths.data == tmp_path / "d" / "picasapy"
        assert paths.cache == tmp_path / "c" / "picasapy"
        assert paths.config == tmp_path / "cfg" / "picasapy"

    def test_linux_fallbackok_is_valtozatlanok(self, tmp_path):
        home = tmp_path / "home"

        paths = default_storage_paths("darwin", environ={}, home=home)

        assert paths.data == home / ".local" / "share" / "picasapy"
        assert paths.cache == home / ".cache" / "picasapy"
        assert paths.config == home / ".config" / "picasapy"

    def test_windows_a_szokasos_appdata_helyeket_hasznalja(self, tmp_path):
        env = _windows_env(tmp_path)

        paths = default_storage_paths("win32", environ=env, home=tmp_path / "home")

        assert paths.data == tmp_path / "AppData" / "Local" / "PicasaPy"
        assert paths.cache == paths.data / "cache"
        assert paths.config == tmp_path / "AppData" / "Roaming" / "PicasaPy"

    def test_windows_kornyezeti_valtozo_hianyaban_stabil_fallbackot_ad(
        self, tmp_path
    ):
        home = tmp_path / "Felhasználó"

        paths = default_storage_paths("win32", environ={}, home=home)

        assert paths.data == home / "AppData" / "Local" / "PicasaPy"
        assert paths.cache == paths.data / "cache"
        assert paths.config == home / "AppData" / "Roaming" / "PicasaPy"

    def test_application_segedek_a_befecskendezett_platformot_hasznaljak(
        self, tmp_path, monkeypatch
    ):
        env = _windows_env(tmp_path)
        for name, value in env.items():
            monkeypatch.setenv(name, value)

        assert application._data_dir(platform="win32") == (
            tmp_path / "AppData" / "Local" / "PicasaPy"
        )
        assert application._cache_dir(platform="win32") == (
            tmp_path / "AppData" / "Local" / "PicasaPy" / "cache"
        )
        assert application._config_dir(platform="win32") == (
            tmp_path / "AppData" / "Roaming" / "PicasaPy"
        )

    def test_ekezetes_windows_profil_bitpontosan_mukodik(self, tmp_path):
        profile = tmp_path / "Users" / "Sáncho"
        env = {
            "LOCALAPPDATA": str(profile / "AppData" / "Local"),
            "APPDATA": str(profile / "AppData" / "Roaming"),
            "XDG_DATA_HOME": str(profile / ".local" / "share"),
            "XDG_CACHE_HOME": str(profile / ".cache"),
            "XDG_CONFIG_HOME": str(profile / ".config"),
        }
        legacy = legacy_windows_storage_paths(environ=env, home=profile)
        target = default_storage_paths("win32", environ=env, home=profile)
        _create_index(legacy.data / "index.db", "Sáncho indexe")
        legacy.config.mkdir(parents=True)
        (legacy.config / "WatchedFolders.txt").write_text(
            "C:\\Users\\Sáncho\\Képek\n", encoding="utf-8"
        )

        outcome = migrate_legacy_windows_storage(target, legacy)

        assert outcome is not None
        assert target.data == profile / "AppData" / "Local" / "PicasaPy"
        assert target.config == profile / "AppData" / "Roaming" / "PicasaPy"
        assert _index_value(target.data / "index.db") == "Sáncho indexe"
        assert (target.config / "WatchedFolders.txt").read_text(
            encoding="utf-8"
        ) == "C:\\Users\\Sáncho\\Képek\n"


class TestLegacyWindowsMigration:
    def test_atveszi_az_indexet_cache_t_es_konfiguraciot(self, tmp_path):
        env = _windows_env(tmp_path)
        legacy = legacy_windows_storage_paths(environ=env, home=tmp_path / "home")
        target = default_storage_paths("win32", environ=env, home=tmp_path / "home")
        _create_index(legacy.data / "index.db")
        (legacy.data / "errorlog.txt").write_text("régi napló", encoding="utf-8")
        (legacy.cache / "thumbs" / "ab").mkdir(parents=True)
        (legacy.cache / "thumbs" / "ab" / "kep.jpg").write_bytes(b"thumbnail")
        legacy.config.mkdir(parents=True)
        (legacy.config / "WatchedFolders.txt").write_text(
            "C:\\Fotók\n", encoding="utf-8"
        )

        migrated = migrate_legacy_windows_storage(target, legacy)

        assert migrated is True
        assert _index_value(target.data / "index.db") == "meglevő-index"
        assert (target.data / "errorlog.txt").read_text(encoding="utf-8") == (
            "régi napló"
        )
        assert (target.cache / "thumbs" / "ab" / "kep.jpg").read_bytes() == (
            b"thumbnail"
        )
        assert (target.config / "WatchedFolders.txt").read_text(
            encoding="utf-8"
        ) == "C:\\Fotók\n"
        # Automatikus migrációnál a régi példány biztonsági
        # másolatként megmarad: megszakítás sem okozhat adatvesztést.
        assert (legacy.data / "index.db").exists()
        assert (legacy.cache / "thumbs" / "ab" / "kep.jpg").exists()

    def test_masodik_futas_idempotens_es_nem_irja_felul_az_uj_adatot(
        self, tmp_path
    ):
        env = _windows_env(tmp_path)
        legacy = legacy_windows_storage_paths(environ=env, home=tmp_path / "home")
        target = default_storage_paths("win32", environ=env, home=tmp_path / "home")
        _create_index(legacy.data / "index.db", "régi")

        assert migrate_legacy_windows_storage(target, legacy) is True
        with sqlite3.connect(target.data / "index.db") as connection:
            connection.execute("UPDATE marker SET value = 'új'")

        assert migrate_legacy_windows_storage(target, legacy) is False
        assert _index_value(target.data / "index.db") == "új"

    def test_elso_futaskor_sem_ir_felul_meglevo_celfajlt(self, tmp_path):
        env = _windows_env(tmp_path)
        legacy = legacy_windows_storage_paths(environ=env, home=tmp_path / "home")
        target = default_storage_paths("win32", environ=env, home=tmp_path / "home")
        _create_index(legacy.data / "index.db", "régi")
        _create_index(target.data / "index.db", "már használt új")
        legacy.config.mkdir(parents=True)
        (legacy.config / "WatchedFolders.txt").write_text(
            "C:\\Régi\n", encoding="utf-8"
        )
        target.config.mkdir(parents=True)
        (target.config / "WatchedFolders.txt").write_text(
            "C:\\Új\n", encoding="utf-8"
        )

        migrate_legacy_windows_storage(target, legacy)

        assert _index_value(target.data / "index.db") == "már használt új"
        assert (target.config / "WatchedFolders.txt").read_text(
            encoding="utf-8"
        ) == "C:\\Új\n"
        assert _index_value(legacy.data / "index.db") == "régi"

    def test_explicit_adatgyoker_felulbiralasat_megorizve_nem_masol_feleslegesen(
        self, tmp_path
    ):
        env = _windows_env(tmp_path)
        legacy = legacy_windows_storage_paths(environ=env, home=tmp_path / "home")
        target = default_storage_paths("win32", environ=env, home=tmp_path / "home")
        custom = tmp_path / "kulon-adatgyoker"
        legacy.config.mkdir(parents=True)
        (legacy.config / "data-location.txt").write_text(
            str(custom), encoding="utf-8"
        )
        _create_index(legacy.data / "index.db")

        migrate_legacy_windows_storage(target, legacy)

        assert (target.config / "data-location.txt").read_text(
            encoding="utf-8"
        ) == str(custom)
        assert not (target.data / "index.db").exists()

    def test_masolasi_hibanal_a_regi_adat_ep_es_a_felkesz_cel_nem_aktiv(
        self, tmp_path, monkeypatch
    ):
        import picasapy.app.platform_storage as storage

        env = _windows_env(tmp_path)
        legacy = legacy_windows_storage_paths(environ=env, home=tmp_path / "home")
        target = default_storage_paths("win32", environ=env, home=tmp_path / "home")
        _create_index(legacy.data / "index.db")

        def _boom(*_args, **_kwargs):
            raise sqlite3.OperationalError("próbahiba")

        monkeypatch.setattr(storage, "_copy_sqlite_database", _boom)

        with pytest.raises(StorageMigrationError, match="index.db"):
            migrate_legacy_windows_storage(target, legacy)

        assert _index_value(legacy.data / "index.db") == "meglevő-index"
        assert not (target.data / "index.db").exists()


def _symlink_or_skip(link: Path, target: Path, *, directory: bool = True) -> None:
    try:
        link.parent.mkdir(parents=True, exist_ok=True)
        link.symlink_to(target, target_is_directory=directory)
    except OSError as error:
        pytest.skip(f"A tesztkörnyezet nem enged symlinket: {error}")


class TestMigrationPathSafety:
    def _paths(self, tmp_path):
        env = _windows_env(tmp_path)
        return (
            legacy_windows_storage_paths(environ=env, home=tmp_path / "home"),
            default_storage_paths("win32", environ=env, home=tmp_path / "home"),
        )

    @pytest.mark.parametrize("dangling", [False, True])
    def test_source_root_symlink_hangosan_megall(self, tmp_path, dangling):
        import picasapy.app.platform_storage as storage

        legacy, target = self._paths(tmp_path)
        real_source = tmp_path / "valodi-forras"
        if not dangling:
            _create_index(real_source / "index.db")
        _symlink_or_skip(legacy.data, real_source)

        with pytest.raises(StorageMigrationError, match="symlink"):
            migrate_legacy_windows_storage(target, legacy)

        assert not (target.config / storage._MIGRATION_MARKER).exists()
        assert not (target.data / "index.db").exists()

    @pytest.mark.parametrize("dangling", [False, True])
    def test_target_root_symlink_hangosan_megall(self, tmp_path, dangling):
        import picasapy.app.platform_storage as storage

        legacy, target = self._paths(tmp_path)
        _create_index(legacy.data / "index.db")
        real_target = tmp_path / "valodi-cel"
        if not dangling:
            real_target.mkdir()
        _symlink_or_skip(target.data, real_target)

        with pytest.raises(StorageMigrationError, match="symlink"):
            migrate_legacy_windows_storage(target, legacy)

        assert not (target.config / storage._MIGRATION_MARKER).exists()
        assert not (real_target / "index.db").exists()

    @pytest.mark.parametrize("side", ["source", "target"])
    def test_storage_root_fajl_konyvtar_tipusutkozes_hangosan_megall(
        self, tmp_path, side
    ):
        import picasapy.app.platform_storage as storage

        legacy, target = self._paths(tmp_path)
        if side == "source":
            legacy.data.parent.mkdir(parents=True)
            legacy.data.write_text("nem könyvtár", encoding="utf-8")
        else:
            _create_index(legacy.data / "index.db")
            target.data.parent.mkdir(parents=True)
            target.data.write_text("nem könyvtár", encoding="utf-8")

        with pytest.raises(StorageMigrationError, match="típusütközés"):
            migrate_legacy_windows_storage(target, legacy)

        assert not (target.config / storage._MIGRATION_MARKER).exists()

    def test_celfajl_helyen_konyvtar_tipusutkozes_hangosan_megall(self, tmp_path):
        import picasapy.app.platform_storage as storage

        legacy, target = self._paths(tmp_path)
        legacy.data.mkdir(parents=True)
        (legacy.data / "errorlog.txt").write_text("napló", encoding="utf-8")
        (target.data / "errorlog.txt").mkdir(parents=True)

        with pytest.raises(StorageMigrationError, match="típusütközés"):
            migrate_legacy_windows_storage(target, legacy)

        assert not (target.config / storage._MIGRATION_MARKER).exists()


class TestMigrationDurability:
    def test_minden_publikacio_fsync_et_kap_es_a_marker_az_utolso(
        self, tmp_path, monkeypatch
    ):
        import picasapy.app.platform_storage as storage

        env = _windows_env(tmp_path)
        legacy = legacy_windows_storage_paths(environ=env, home=tmp_path / "home")
        target = default_storage_paths("win32", environ=env, home=tmp_path / "home")
        _create_index(legacy.data / "index.db")
        (legacy.data / "errorlog.txt").write_text("napló", encoding="utf-8")
        legacy.config.mkdir(parents=True)
        (legacy.config / "WatchedFolders.txt").write_text("C:\\Fotók\n")

        events: list[tuple[str, Path]] = []
        original_fsync_file = storage._fsync_file
        original_fsync_directory = storage._fsync_directory
        original_publish = storage._publish_if_missing

        def record_fsync_file(path):
            original_fsync_file(path)
            events.append(("fsync_file", Path(path)))

        def record_fsync_directory(path):
            original_fsync_directory(path)
            events.append(("fsync_directory", Path(path)))

        def record_publish(temporary, destination):
            events.append(("publish", Path(destination)))
            return original_publish(temporary, destination)

        monkeypatch.setattr(storage, "_fsync_file", record_fsync_file)
        monkeypatch.setattr(storage, "_fsync_directory", record_fsync_directory)
        monkeypatch.setattr(storage, "_publish_if_missing", record_publish)

        migrate_legacy_windows_storage(target, legacy)

        publications = [event for event in events if event[0] == "publish"]
        marker = target.config / storage._MIGRATION_MARKER
        assert publications[-1] == ("publish", marker)
        marker_index = events.index(("publish", marker))
        earlier_publications = publications[:-1]
        assert earlier_publications
        for _, published in earlier_publications:
            publish_index = events.index(("publish", published))
            assert events[publish_index - 1][0] == "fsync_file"
            assert ("fsync_directory", published.parent) in events[
                publish_index + 1 : marker_index
            ]
        assert events[marker_index - 1][0] == "fsync_file"


class TestStorageBootstrap:
    def test_futo_regi_explicit_adatgyokernel_migracio_elott_megall(
        self, tmp_path
    ):
        env = _windows_env(tmp_path)
        legacy = legacy_windows_storage_paths(environ=env, home=tmp_path / "home")
        explicit_root = tmp_path / "régi-explicit-adat"
        explicit_root.mkdir()
        write_data_root(legacy.config, explicit_root)
        held_lock = application._acquire_instance_lock(explicit_root)
        assert held_lock is not None
        migration_calls = []
        try:
            with pytest.raises(application.StorageAlreadyRunning):
                application._bootstrap_storage(
                    platform="win32",
                    environ=env,
                    home=tmp_path / "home",
                    migrate=lambda *_args: migration_calls.append(True),
                )
        finally:
            held_lock.unlock()

        assert migration_calls == []

    def test_explicit_legacy_adatgyoker_symlinkjet_sem_koveti(self, tmp_path):
        env = _windows_env(tmp_path)
        legacy = legacy_windows_storage_paths(environ=env, home=tmp_path / "home")
        real_root = tmp_path / "valodi-explicit-adat"
        real_root.mkdir()
        linked_root = tmp_path / "linkelt-explicit-adat"
        _symlink_or_skip(linked_root, real_root)
        write_data_root(legacy.config, linked_root)
        migration_calls = []

        with pytest.raises(StorageMigrationError, match="symlink"):
            application._bootstrap_storage(
                platform="win32",
                environ=env,
                home=tmp_path / "home",
                migrate=lambda *_args: migration_calls.append(True),
            )

        assert migration_calls == []

    def test_azonos_effektiv_rootnal_ugyanazt_a_zarat_tartja_meg_es_a_sorrend_jo(
        self, tmp_path
    ):
        env = _windows_env(tmp_path)
        legacy = legacy_windows_storage_paths(environ=env, home=tmp_path / "home")
        explicit_root = tmp_path / "közös-explicit-adat"
        explicit_root.mkdir()
        write_data_root(legacy.config, explicit_root)
        events = []
        lock = object()

        def acquire(path):
            events.append(("lock", Path(path)))
            return lock

        def migrate(target_paths, legacy_paths):
            events.append(("migrate", legacy_paths.data))
            target_paths.config.mkdir(parents=True, exist_ok=True)
            write_data_root(target_paths.config, explicit_root)
            return True

        bootstrap = application._bootstrap_storage(
            platform="win32",
            environ=env,
            home=tmp_path / "home",
            acquire_lock=acquire,
            migrate=migrate,
        )

        assert events == [("lock", explicit_root), ("migrate", legacy.data)]
        assert bootstrap.data_dir == explicit_root
        assert bootstrap.instance_lock is lock
        assert bootstrap.legacy_lock is lock

    def test_windows_migracio_utan_az_uj_rootot_zarja(self, tmp_path):
        env = _windows_env(tmp_path)
        legacy = legacy_windows_storage_paths(environ=env, home=tmp_path / "home")
        legacy.data.mkdir(parents=True)
        events = []

        def acquire(path):
            events.append(("lock", Path(path)))
            return object()

        def migrate(_target, _legacy):
            events.append(("migrate", _legacy.data))
            return True

        bootstrap = application._bootstrap_storage(
            platform="win32",
            environ=env,
            home=tmp_path / "home",
            acquire_lock=acquire,
            migrate=migrate,
        )

        target = default_storage_paths("win32", environ=env, home=tmp_path / "home")
        assert events == [
            ("lock", legacy.data),
            ("migrate", legacy.data),
            ("lock", target.data),
        ]
        assert bootstrap.data_dir == target.data
        assert bootstrap.instance_lock is not bootstrap.legacy_lock

    def test_linuxon_nincs_migracio_es_az_xdg_root_zarodik(self, tmp_path):
        env = {
            "XDG_DATA_HOME": str(tmp_path / "data"),
            "XDG_CACHE_HOME": str(tmp_path / "cache"),
            "XDG_CONFIG_HOME": str(tmp_path / "config"),
        }
        events = []
        lock = object()

        bootstrap = application._bootstrap_storage(
            platform="linux",
            environ=env,
            home=tmp_path / "home",
            acquire_lock=lambda path: events.append(("lock", Path(path))) or lock,
            migrate=lambda *_args: events.append(("migrate", Path("hiba"))),
        )

        target = default_storage_paths("linux", environ=env, home=tmp_path / "home")
        assert events == [("lock", target.data)]
        assert bootstrap.instance_lock is lock
        assert bootstrap.legacy_lock is None

    def test_run_a_bootstrapot_a_gyokerfeloldas_elott_hivja(self):
        source = Path(application.__file__).read_text(encoding="utf-8")
        run_source = source[source.index("def run(") :]

        assert run_source.index("_bootstrap_storage()") < run_source.index(
            "roots = _resolve_roots(argv)"
        )


class TestMigrationNotice:
    def test_sikeres_migracio_a_splashen_forras_es_celuttal_latszik(self, tmp_path):
        profile = tmp_path / "Users" / "Sáncho"
        env = {
            "LOCALAPPDATA": str(profile / "AppData" / "Local"),
            "APPDATA": str(profile / "AppData" / "Roaming"),
            "XDG_DATA_HOME": str(profile / ".local" / "share"),
            "XDG_CACHE_HOME": str(profile / ".cache"),
            "XDG_CONFIG_HOME": str(profile / ".config"),
        }
        legacy = legacy_windows_storage_paths(environ=env, home=profile)
        _create_index(legacy.data / "index.db")
        bootstrap = application._bootstrap_storage(
            platform="win32",
            environ=env,
            home=profile,
            acquire_lock=lambda _path: object(),
        )
        notice = bootstrap.migration_notice
        assert notice is not None
        status = StartupStatus("Indulás…")

        class Controller:
            started = False

            def start(self):
                self.started = True

        controller = Controller()

        application._start_initial_scan(status, controller, notice)

        assert controller.started is True
        assert str(notice.source) in status.statusText
        assert str(notice.target) in status.statusText
        assert "migr" in status.statusText.lower()
