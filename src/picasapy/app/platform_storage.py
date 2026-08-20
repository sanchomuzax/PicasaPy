"""Platformfüggő alkalmazás-adatútvonalak és Windows-migráció (#1076).

Linuxon az eddigi XDG-útvonalak jelentik a kompatibilitási szerződést.
Windowson az index és a cache a helyi, a konfiguráció a roaming AppData
alá kerül. A korábbi kiadások Windowson is XDG-helyeket számoltak;
az egyszeri migráció ezek tartalmát másolja át az új helyekre.

A migráció szándékosan nem törli a régi példányt. Az automatikus,
indulás előtti műveletnél ez adja a legerősebb adatvesztés-védelmet:
hiba vagy áramkimaradás után a forrás változatlan, a jelölőfájl
hiányában pedig a következő indítás folytatja a hiányzó fájlokat.
"""

from __future__ import annotations

import os
import shutil
import sqlite3
import tempfile
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from .data_location import read_data_root

_APP_DIR_WINDOWS = "PicasaPy"
_APP_DIR_XDG = "picasapy"
_MIGRATION_MARKER = ".legacy-xdg-migration-1076-complete"
_DATA_FILES_NOT_TO_COPY = frozenset(
    {"index.db", "index.db-wal", "index.db-shm", "picasapy.lock"}
)


@dataclass(frozen=True)
class StoragePaths:
    """Az index-, cache- és konfigurációs gyökér egy platformon."""

    data: Path
    cache: Path
    config: Path


class StorageMigrationError(RuntimeError):
    """A régi Windows XDG-adatok biztonságos átvétele nem sikerült."""


def default_storage_paths(
    platform: str,
    *,
    environ: Mapping[str, str] | None = None,
    home: Path | None = None,
) -> StoragePaths:
    """Az alkalmazás alapértelmezett tárhelyei a megadott platformon.

    A paraméterezés lehetővé teszi mindkét platformág ellenőrzését
    az aktuális operációs rendszertől függetlenül.
    """
    env = os.environ if environ is None else environ
    home_dir = Path.home() if home is None else Path(home)
    if platform == "win32":
        local = Path(env.get("LOCALAPPDATA") or home_dir / "AppData" / "Local")
        roaming = Path(env.get("APPDATA") or home_dir / "AppData" / "Roaming")
        data = local / _APP_DIR_WINDOWS
        return StoragePaths(
            data=data,
            cache=data / "cache",
            config=roaming / _APP_DIR_WINDOWS,
        )

    # Az üres XDG-változót is pontosan úgy kezeljük, mint a korábbi
    # application.py: csak a teljesen hiányzó kulcs kap fallbackot.
    data_base = env.get("XDG_DATA_HOME", str(home_dir / ".local" / "share"))
    cache_base = env.get("XDG_CACHE_HOME", str(home_dir / ".cache"))
    config_base = env.get("XDG_CONFIG_HOME", str(home_dir / ".config"))
    return StoragePaths(
        data=Path(data_base) / _APP_DIR_XDG,
        cache=Path(cache_base) / _APP_DIR_XDG,
        config=Path(config_base) / _APP_DIR_XDG,
    )


def legacy_windows_storage_paths(
    *,
    environ: Mapping[str, str] | None = None,
    home: Path | None = None,
) -> StoragePaths:
    """A #1076 előtti Windows-kiadások pontos XDG-útvonalai."""
    return default_storage_paths("legacy-xdg", environ=environ, home=home)


def _temporary_path(target: Path) -> Path:
    target.parent.mkdir(parents=True, exist_ok=True)
    descriptor, name = tempfile.mkstemp(
        prefix=f".{target.name}.", suffix=".tmp", dir=target.parent
    )
    os.close(descriptor)
    return Path(name)


def _publish_if_missing(temporary: Path, target: Path) -> None:
    """A teljes ideiglenes fájlt teszi láthatóvá, meglévőt nem ír felül."""
    try:
        # Az ideiglenes fájl ugyanabban a mappában van, ezért a hardlink
        # atomi, és az `os.replace`-szel ellentétben versenyhelyzetben sem
        # írhat felül egy közben létrejött célfájlt.
        os.link(temporary, target)
    except FileExistsError:
        return


def _copy_file_if_missing(source: Path, target: Path) -> None:
    if target.exists():
        return
    temporary = _temporary_path(target)
    try:
        shutil.copy2(source, temporary)
        _publish_if_missing(temporary, target)
    finally:
        temporary.unlink(missing_ok=True)


def _copy_tree_if_missing(
    source: Path, target: Path, *, skip_names: frozenset[str] = frozenset()
) -> None:
    if not source.is_dir():
        return
    for source_file in source.rglob("*"):
        if not source_file.is_file() or source_file.name in skip_names:
            continue
        relative = source_file.relative_to(source)
        _copy_file_if_missing(source_file, target / relative)


def _copy_sqlite_database(source: Path, target: Path) -> None:
    """Konzisztens SQLite-pillanatképet másol és ellenőriz, atomikusan."""
    if not source.is_file() or target.exists():
        return
    temporary = _temporary_path(target)
    try:
        source_connection = sqlite3.connect(str(source))
        try:
            target_connection = sqlite3.connect(str(temporary))
            try:
                source_connection.backup(target_connection)
            finally:
                target_connection.close()
        finally:
            source_connection.close()

        with sqlite3.connect(str(temporary)) as copied:
            result = [str(row[0]) for row in copied.execute("PRAGMA integrity_check")]
        if result != ["ok"]:
            raise sqlite3.DatabaseError("; ".join(result))
        _publish_if_missing(temporary, target)
    finally:
        temporary.unlink(missing_ok=True)


def _write_marker(config_dir: Path) -> None:
    marker = config_dir / _MIGRATION_MARKER
    if marker.exists():
        return
    temporary = _temporary_path(marker)
    try:
        temporary.write_text("ok\n", encoding="ascii")
        _publish_if_missing(temporary, marker)
    finally:
        temporary.unlink(missing_ok=True)


def migrate_legacy_windows_storage(
    target: StoragePaths, legacy: StoragePaths
) -> bool:
    """Egyszer, adatvesztésmentesen átveszi a régi Windows XDG-adatokat.

    `True`, ha volt migrálandó forrás és a művelet befejeződött;
    `False`, ha nem volt mit tenni vagy egy korábbi futás már elkészült.
    Meglévő célfájlt soha nem ír felül, a forrást soha nem törli.
    """
    marker = target.config / _MIGRATION_MARKER
    if marker.is_file():
        return False
    sources = (legacy.data, legacy.cache, legacy.config)
    if not any(path.exists() for path in sources):
        return False

    current_source: Path = legacy.config
    current_target: Path = target.config
    try:
        # A konfiguráció az első: ebben élhet a #368 explicit
        # adatgyökér-felülbírálása. Ha van ilyen, az továbbra is
        # nyer az alapértelmezés fölött; a régi default index/cache
        # másolása ilyenkor felesleges és félrevezető volna.
        _copy_tree_if_missing(legacy.config, target.config)
        if read_data_root(target.config) is None:
            current_source = legacy.data / "index.db"
            current_target = target.data / "index.db"
            _copy_sqlite_database(current_source, current_target)

            current_source = legacy.data
            current_target = target.data
            _copy_tree_if_missing(
                legacy.data, target.data, skip_names=_DATA_FILES_NOT_TO_COPY
            )

            current_source = legacy.cache
            current_target = target.cache
            _copy_tree_if_missing(legacy.cache, target.cache)

        current_source = legacy.config
        current_target = marker
        _write_marker(target.config)
    except (OSError, sqlite3.Error) as error:
        raise StorageMigrationError(
            "A régi Windows-adatok átvétele nem sikerült "
            f"({current_source} → {current_target}): {error}"
        ) from error
    return True


__all__ = [
    "StorageMigrationError",
    "StoragePaths",
    "default_storage_paths",
    "legacy_windows_storage_paths",
    "migrate_legacy_windows_storage",
]
