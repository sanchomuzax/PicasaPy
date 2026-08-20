"""Platformfüggő alkalmazás-adatútvonalak és Windows-migráció (#1076)."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from picasapy.app import application
from picasapy.app.platform_storage import (
    StorageMigrationError,
    default_storage_paths,
    legacy_windows_storage_paths,
    migrate_legacy_windows_storage,
)


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
