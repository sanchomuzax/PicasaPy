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
import sys
import tempfile
from collections.abc import Callable, Mapping
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


@dataclass(frozen=True)
class MigrationNotice:
    """Az egyszeri adatátvétel felhasználónak mutatandó forrása/célja."""

    source: Path
    target: Path


@dataclass(frozen=True)
class StorageBootstrap:
    """A bootstrap egyszer kiszámolt útvonalai és megtartandó zárai."""

    data_dir: Path
    cache_dir: Path
    config_dir: Path
    instance_lock: object
    legacy_lock: object | None
    migration_notice: MigrationNotice | None


class StorageAlreadyRunning(RuntimeError):
    """Az effektív régi vagy új adatgyökér zárja már foglalt."""


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
    _ensure_directory(target.parent)
    descriptor, name = tempfile.mkstemp(
        prefix=f".{target.name}.", suffix=".tmp", dir=target.parent
    )
    os.close(descriptor)
    return Path(name)


def _lexists(path: Path) -> bool:
    """`True` dangling symlinkre is — a `Path.exists()` azt elrejtené."""
    return os.path.lexists(path)


def _reject_symlink_components(path: Path) -> None:
    """Az útvonal egyetlen meglévő komponense sem lehet symlink.

    A migráció szándékosan nem követ sem forrás-, sem cél-symlinket:
    különben egy névleg AppData alatti művelet tetszőleges más helyre
    írhatna. A `Path.is_symlink()` dangling linkre is igaz.
    """
    for component in (path, *path.parents):
        if component.is_symlink():
            raise StorageMigrationError(
                f"Nem biztonságos symlink a migrációs útvonalban: {component}"
            )


def _ensure_directory(path: Path) -> None:
    """Biztonságos valódi könyvtárat biztosít; típusütközésnél hibázik."""
    _reject_symlink_components(path)
    if _lexists(path):
        if not path.is_dir():
            raise StorageMigrationError(
                f"Fájl–könyvtár típusütközés a migrációnál: {path}"
            )
        return
    if path.parent != path:
        _ensure_directory(path.parent)
    path.mkdir(exist_ok=False)
    _reject_symlink_components(path)
    _fsync_directory(path.parent)


def _validate_directory_or_missing(path: Path) -> None:
    _reject_symlink_components(path)
    if _lexists(path) and not path.is_dir():
        raise StorageMigrationError(
            f"Fájl–könyvtár típusütközés a migrációnál: {path}"
        )


def _validate_file_or_missing(path: Path) -> bool:
    """Igaz, ha szabályos fájl létezik; hiánynál hamis, másnál hiba."""
    _reject_symlink_components(path)
    if not _lexists(path):
        return False
    if not path.is_file():
        raise StorageMigrationError(
            f"Fájl–könyvtár típusütközés a migrációnál: {path}"
        )
    return True


def _platform() -> str:
    """A futó platform — külön függvény, hogy a teszt helyettesíthesse (#1217)."""
    return sys.platform

def _fsync_file(path: Path) -> None:
    """A teljes fájlt a stabil tárra kényszeríti publikálás előtt."""
    with path.open("rb+") as file:
        file.flush()
        os.fsync(file.fileno())


def _fsync_directory(path: Path) -> None:
    """A friss könyvtárbejegyzést tartósítja, ahol a platform engedi."""
    flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
    try:
        descriptor = os.open(path, flags)
    except OSError:
        if _platform().startswith("win"):
            # A Windows Python nem ad megnyitható directory fd-t. A fájl
            # fsync-je ott is kötelezően megtörtént; a directory flush-t
            # maga az NTFS/link művelet biztosítja.
            return
        raise
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _publish_if_missing(temporary: Path, target: Path) -> bool:
    """A teljes ideiglenes fájlt teszi láthatóvá, meglévőt nem ír felül."""
    try:
        # Az ideiglenes fájl ugyanabban a mappában van, ezért a hardlink
        # atomi, és az `os.replace`-szel ellentétben versenyhelyzetben sem
        # írhat felül egy közben létrejött célfájlt.
        os.link(temporary, target)
    except FileExistsError:
        _validate_file_or_missing(target)
        return False
    _fsync_directory(target.parent)
    return True


def _copy_file_if_missing(source: Path, target: Path) -> None:
    if not _validate_file_or_missing(source):
        return
    if _validate_file_or_missing(target):
        return
    temporary = _temporary_path(target)
    try:
        shutil.copy2(source, temporary)
        _fsync_file(temporary)
        _publish_if_missing(temporary, target)
    finally:
        temporary.unlink(missing_ok=True)


def _copy_tree_if_missing(
    source: Path, target: Path, *, skip_names: frozenset[str] = frozenset()
) -> None:
    _validate_directory_or_missing(source)
    _validate_directory_or_missing(target)
    if not _lexists(source):
        return
    _ensure_directory(target)
    for source_entry in source.iterdir():
        _reject_symlink_components(source_entry)
        if source_entry.name in skip_names:
            continue
        target_entry = target / source_entry.name
        if source_entry.is_dir():
            _copy_tree_if_missing(
                source_entry, target_entry, skip_names=skip_names
            )
        elif source_entry.is_file():
            _copy_file_if_missing(source_entry, target_entry)
        else:
            raise StorageMigrationError(
                f"Nem szabályos forrásfájl a migrációnál: {source_entry}"
            )


def _copy_sqlite_database(source: Path, target: Path) -> None:
    """Konzisztens SQLite-pillanatképet másol és ellenőriz, atomikusan."""
    if not _validate_file_or_missing(source):
        return
    if _validate_file_or_missing(target):
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

        # ⚠️ A `with sqlite3.connect(...)` NEM zárja be a kapcsolatot — csak
        # a tranzakciót kezeli. Windowson a nyitva maradt másolat miatt a
        # rákövetkező publikálás `WinError 32`-vel bukik, és az EGÉSZ
        # migráció hibára fut: a felhasználó indexe nem kerül át. Linuxon
        # ez láthatatlan, ott a nyitott fájl is linkelhető és törölhető.
        copied = sqlite3.connect(str(temporary))
        try:
            result = [str(row[0]) for row in copied.execute("PRAGMA integrity_check")]
        finally:
            copied.close()
        if result != ["ok"]:
            raise sqlite3.DatabaseError("; ".join(result))
        _fsync_file(temporary)
        _publish_if_missing(temporary, target)
    finally:
        temporary.unlink(missing_ok=True)


def _write_marker(config_dir: Path) -> None:
    marker = config_dir / _MIGRATION_MARKER
    if _validate_file_or_missing(marker):
        return
    temporary = _temporary_path(marker)
    try:
        temporary.write_text("ok\n", encoding="ascii")
        _fsync_file(temporary)
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
    # A célakat marker mellett is ellenőrizzük: egy később odatett
    # symlinket a késznek jelölt migráció sem tehet elfogadottá.
    for root in (target.data, target.cache, target.config):
        _validate_directory_or_missing(root)
    marker = target.config / _MIGRATION_MARKER
    if _validate_file_or_missing(marker):
        return False
    sources = (legacy.data, legacy.cache, legacy.config)
    if not any(_lexists(path) for path in sources):
        return False

    # Minden gyökér ellenőrzése MÉG AZ ELSŐ ÍRÁS ELŐTT: egy
    # cél-symlink vagy gyökér-típusütközés így részleges config-
    # másolatot sem hagy maga után.
    for root in sources:
        _validate_directory_or_missing(root)

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


def _same_storage_location(first: Path, second: Path) -> bool:
    """Két, esetleg még nem létező útvonal ugyanoda mutat-e."""
    try:
        return first.resolve(strict=False) == second.resolve(strict=False)
    except OSError:
        return first.absolute() == second.absolute()


def _effective_storage_paths(defaults: StoragePaths) -> tuple[Path, Path]:
    override = read_data_root(defaults.config)
    if override is not None:
        return override, override
    return defaults.data, defaults.cache


def bootstrap_storage(
    platform: str,
    *,
    acquire_lock: Callable[[Path], object | None],
    environ: Mapping[str, str] | None = None,
    home: Path | None = None,
    migrate: Callable[[StoragePaths, StoragePaths], object] | None = None,
) -> StorageBootstrap:
    """Feloldja/migrálja az utakat, és még előtte lefoglalja a régi zárat.

    A befecskendezhető platform, környezet, zároló és migráló tesztből
    bizonyíthatóvá teszi a kritikus sorrendet. A visszaadott objektum a
    teljes alkalmazás-élettartam alatt megtartja mindkét QLockFile-t.
    """
    env = os.environ if environ is None else environ
    migrate_fn = migrate_legacy_windows_storage if migrate is None else migrate
    target = default_storage_paths(platform, environ=env, home=home)
    legacy_lock = None
    legacy_effective_data: Path | None = None
    legacy_override: Path | None = None
    migration_performed = False

    if platform == "win32":
        legacy = legacy_windows_storage_paths(environ=env, home=home)
        # KÖTELEZŐ sorrend: legacy config olvasása → effektív régi zár
        # → migráció. Így explicit #368 gyökérből sem másolunk futó DB-t.
        _validate_directory_or_missing(legacy.config)
        legacy_override = read_data_root(legacy.config)
        legacy_effective_data = legacy_override or legacy.data
        _validate_directory_or_missing(legacy_effective_data)
        if legacy_effective_data.is_dir():
            legacy_lock = acquire_lock(legacy_effective_data)
            if legacy_lock is None:
                raise StorageAlreadyRunning
        migration_performed = bool(migrate_fn(target, legacy))

    target_override = read_data_root(target.config)
    data_dir, cache_dir = _effective_storage_paths(target)
    if platform == "win32":
        _validate_directory_or_missing(data_dir)
        _validate_directory_or_missing(cache_dir)
    if (
        legacy_lock is not None
        and legacy_effective_data is not None
        and _same_storage_location(legacy_effective_data, data_dir)
    ):
        instance_lock = legacy_lock
    else:
        instance_lock = acquire_lock(data_dir)
        if instance_lock is None:
            raise StorageAlreadyRunning

    notice = None
    if (
        migration_performed
        and legacy_override is None
        and target_override is None
        and legacy_effective_data is not None
        and legacy_effective_data.is_dir()
        and not _same_storage_location(legacy_effective_data, data_dir)
    ):
        notice = MigrationNotice(legacy_effective_data, data_dir)
    return StorageBootstrap(
        data_dir=data_dir,
        cache_dir=cache_dir,
        config_dir=target.config,
        instance_lock=instance_lock,
        legacy_lock=legacy_lock,
        migration_notice=notice,
    )


__all__ = [
    "MigrationNotice",
    "StorageAlreadyRunning",
    "StorageBootstrap",
    "StorageMigrationError",
    "StoragePaths",
    "bootstrap_storage",
    "default_storage_paths",
    "legacy_windows_storage_paths",
    "migrate_legacy_windows_storage",
]
