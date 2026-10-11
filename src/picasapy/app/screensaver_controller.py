"""A Linuxos teljes képernyős képernyővédő forrásai és beállításai (#4259).

Az eredeti Picasa képernyővédő-kiegészítő volt; itt a már indexelt mappák,
albumok és a menüből hozzáadott képek adják a helyi forrásokat. A beállítások
QSettings-ben élnek, a vetítés pedig külön PhotoGridModelt kap, hogy ne írja
át a könyvtár aktuális kijelölését.
"""

from __future__ import annotations

import os
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from PySide6.QtCore import Property, QObject, QSettings, Signal, Slot

from picasapy.index import (
    album_photos,
    albums_in_index,
    all_photos,
    open_index,
    photos_under_folder,
)

from picasapy.index.schema import SCHEMA_VERSION

from .models import PhotoGridModel, sorted_folder_rows
from .screensaver_idle import (
    DEFAULT_MINUTES,
    MAX_MINUTES,
    MIN_MINUTES,
    IdleIntegration,
    IdleIntegrationError,
)

_SOURCES_KEY = "screensaver/sources"
_PHOTO_PATHS_KEY = "screensaver/photoPaths"
_EFFECT_KEY = "screensaver/effect"
_SECONDS_KEY = "screensaver/seconds"
_CAPTIONS_KEY = "screensaver/showCaptions"
_IDLE_MINUTES_KEY = "screensaver/idleMinutes"
_EFFECTS = {"cut", "dissolve", "dissolveblack", "dissolvewhite", "kenburns"}
_SECONDS_MIN = 1.0
_SECONDS_MAX = 30.0


def _path_key(path: str) -> str:
    return os.path.normcase(os.path.normpath(str(path)))


def _string_list(raw) -> list[str]:
    if isinstance(raw, str):
        return [raw] if raw else []
    try:
        return list(dict.fromkeys(str(item) for item in raw if str(item)))
    except TypeError:
        return []


def saved_photo_paths(settings: QSettings) -> list[str]:
    """A „Kijelölt képek” forrás menüből hozzáadott képei."""
    return _string_list(settings.value(_PHOTO_PATHS_KEY, []))


def source_catalog(conn, photo_paths: list[str], album_name=None) -> list[dict]:
    """A választható források: képet tartalmazó mappák, albumok, kijelöltek."""
    folders = sorted_folder_rows(conn)
    albums = albums_in_index(conn)
    sources = [
        {
            "key": f"folder:{path}",
            "kind": "folder",
            "name": name,
            "count": count,
        }
        for name, path, count, _date, _size, _changed, offline, _hidden, _unread
        in folders
        if count > 0 and not offline
    ]
    sources.extend(
        {
            "key": f"album:{album.token}",
            "kind": "album",
            "name": album.name or (album_name(album.token) if album_name else ""),
            "count": album.photo_count,
        }
        for album in albums
        if album.photo_count > 0
    )
    if photo_paths:
        sources.append({
            "key": "photos:selected",
            "kind": "photos",
            "name": "",
            "count": len(photo_paths),
        })
    return sources


def selected_source_keys(
    settings: QSettings, catalog: list[dict], roots
) -> list[str]:
    """A mentett forrásválasztás; mentés nélkül a figyelt gyökerek."""
    if settings.contains(_SOURCES_KEY):
        return _string_list(settings.value(_SOURCES_KEY, []))
    # Első indításkor a figyelt gyökerekből vetít; a felhasználó ezután
    # mappánként vagy albumonként szűkítheti a forrásokat.
    known = {source["key"] for source in catalog}
    defaults = [key for key in (f"folder:{root}" for root in roots) if key in known]
    return defaults or [
        source["key"] for source in catalog if source["kind"] == "folder"
    ]


def collect_slides(conn, catalog, selected, photo_paths) -> tuple:
    """A bejelölt források vetíthető (nem rejtett, nem videó) képei."""
    selected = set(selected)
    records_by_path = {}
    for source in catalog:
        key = source["key"]
        if key not in selected:
            continue
        if source["kind"] == "folder":
            records = photos_under_folder(conn, key.removeprefix("folder:"))
        elif source["kind"] == "album":
            records = album_photos(conn, key.removeprefix("album:"))
        else:
            wanted = {_path_key(path) for path in photo_paths}
            records = tuple(
                photo for photo in all_photos(conn)
                if _path_key(str(Path(photo.folder_path) / photo.name)) in wanted
            )
        for photo in records:
            if photo.hidden or photo.kind == "video":
                continue
            path = str(Path(photo.folder_path) / photo.name)
            records_by_path.setdefault(_path_key(path), photo)
    return tuple(records_by_path[key] for key in sorted(records_by_path))


@contextmanager
def open_index_readonly(db_path) -> Iterator[sqlite3.Connection]:
    """Csak olvasó kapcsolat az indexhez — nem állít WAL-t, nem migrál.

    Tétlenség-indította vetítés nem írhatja át az index fájlját (a futó
    PicasaPy mellett sem). Ha a séma nem az elvárt verzió, érthető
    `RuntimeError`-t ad, amelyet a hívó traceback nélkül jelez.
    """
    conn = sqlite3.connect(f"file:{Path(db_path).as_posix()}?mode=ro", uri=True)
    try:
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA busy_timeout=5000")
        version = conn.execute("PRAGMA user_version").fetchone()[0]
        if version != SCHEMA_VERSION:
            raise RuntimeError(
                f"Az index sémaverziója ({version}) nem az elvárt "
                f"({SCHEMA_VERSION}) — indítsd el egyszer a PicasaPy-t, hogy "
                "frissítse (vagy frissítsd a PicasaPy-t)."
            )
        yield conn
    finally:
        conn.close()


def load_screensaver_slides(db_path, settings: QSettings, roots) -> tuple:
    """A `--screensaver` belépési pont képei — főablak és vezérlő nélkül."""
    photo_paths = saved_photo_paths(settings)
    with open_index_readonly(db_path) as conn:
        catalog = source_catalog(conn, photo_paths)
        selected = selected_source_keys(settings, catalog, roots)
        return collect_slides(conn, catalog, selected, photo_paths)


def saved_effect(settings: QSettings) -> str:
    value = str(settings.value(_EFFECT_KEY, "dissolve"))
    return value if value in _EFFECTS else "dissolve"


def saved_seconds(settings: QSettings) -> int:
    try:
        seconds = int(settings.value(_SECONDS_KEY, 3))
    except (TypeError, ValueError):
        return 3
    return seconds if _SECONDS_MIN <= seconds <= _SECONDS_MAX else 3


def saved_show_captions(settings: QSettings) -> bool:
    return settings.value(_CAPTIONS_KEY, True) in (True, "true", "1", 1)


class ScreensaverMixin:
    """A képernyővédő QML-hídja; a könyvtárvezérlő adatforrásait használja."""

    screensaverSettingsChanged = Signal()
    screensaverSourcesChanged = Signal()
    screensaverIdleChanged = Signal()

    def _init_screensaver(self) -> None:
        self._screensaver_photos = PhotoGridModel(self)
        self.albumsChanged.connect(self.screensaverSourcesChanged.emit)
        self._folders.folderCountChanged.connect(self.screensaverSourcesChanged.emit)
        self.syncFinished.connect(self._screensaver_catalog_reloaded)

    def _screensaver_catalog_reloaded(self, *_args) -> None:
        self.screensaverSourcesChanged.emit()

    def _get_settings(self) -> QSettings:  # supplied by AppController
        raise NotImplementedError

    def _source_catalog(self) -> list[dict]:
        with open_index(self._db_path) as conn:
            return source_catalog(
                conn, self._screensaver_photo_paths(), self._album_placeholder_name
            )

    def _screensaver_photo_paths(self) -> list[str]:
        return saved_photo_paths(self._get_settings())

    def _selected_source_keys(self) -> list[str]:
        return selected_source_keys(
            self._get_settings(), self._source_catalog(), self._roots
        )

    @Property("QVariantList", notify=screensaverSourcesChanged)
    def screensaverSources(self) -> list[dict]:  # noqa: N802
        selected = set(self._selected_source_keys())
        return [
            {**source, "selected": source["key"] in selected}
            for source in self._source_catalog()
        ]

    def setScreensaverSources(self, keys) -> None:  # noqa: N802
        known = {source["key"] for source in self._source_catalog()}
        selected = list(dict.fromkeys(str(key) for key in keys if str(key) in known))
        self._get_settings().setValue(_SOURCES_KEY, selected)
        self.screensaverSettingsChanged.emit()
        self.screensaverSourcesChanged.emit()

    @Slot(str, bool)
    def setScreensaverSource(self, key: str, selected: bool) -> None:  # noqa: N802
        current = self._selected_source_keys()
        if selected and key not in current:
            current.append(key)
        elif not selected:
            current = [item for item in current if item != key]
        self.setScreensaverSources(current)

    @Property(str, notify=screensaverSettingsChanged)
    def screensaverEffect(self) -> str:  # noqa: N802
        return saved_effect(self._get_settings())

    @Slot(str)
    def setScreensaverEffect(self, value: str) -> None:  # noqa: N802
        if value not in _EFFECTS:
            return
        self._get_settings().setValue(_EFFECT_KEY, value)
        self.screensaverSettingsChanged.emit()

    @Property(int, notify=screensaverSettingsChanged)
    def screensaverSeconds(self) -> int:  # noqa: N802
        return saved_seconds(self._get_settings())

    @Slot(int)
    def setScreensaverSeconds(self, seconds: int) -> None:  # noqa: N802
        try:
            seconds = int(seconds)
        except (TypeError, ValueError):
            return
        if not _SECONDS_MIN <= seconds <= _SECONDS_MAX:
            return
        self._get_settings().setValue(_SECONDS_KEY, seconds)
        self.screensaverSettingsChanged.emit()

    @Property(bool, notify=screensaverSettingsChanged)
    def screensaverShowCaptions(self) -> bool:  # noqa: N802
        return saved_show_captions(self._get_settings())

    @Slot(bool)
    def setScreensaverShowCaptions(self, enabled: bool) -> None:  # noqa: N802
        self._get_settings().setValue(_CAPTIONS_KEY, bool(enabled))
        self.screensaverSettingsChanged.emit()

    @Slot("QVariantList", result=int)
    def addScreensaverPhotos(self, paths) -> int:  # noqa: N802
        existing = self._screensaver_photo_paths()
        by_key = {_path_key(path): path for path in existing}
        old_count = len(by_key)
        for path in paths:
            value = str(path)
            if value:
                by_key.setdefault(_path_key(value), value)
        result = list(by_key.values())
        self._get_settings().setValue(_PHOTO_PATHS_KEY, result)
        selected = self._selected_source_keys()
        if result and "photos:selected" not in selected:
            selected.append("photos:selected")
            self._get_settings().setValue(_SOURCES_KEY, selected)
        self.screensaverSettingsChanged.emit()
        self.screensaverSourcesChanged.emit()
        return len(result) - old_count

    @Property(QObject, constant=True)
    def screensaverPhotos(self):  # noqa: N802
        return self._screensaver_photos

    @Slot(result=int)
    def prepareScreensaverPreview(self) -> int:  # noqa: N802
        photo_paths = self._screensaver_photo_paths()
        with open_index(self._db_path) as conn:
            catalog = source_catalog(conn, photo_paths, self._album_placeholder_name)
            selected = selected_source_keys(self._get_settings(), catalog, self._roots)
            records = collect_slides(conn, catalog, selected, photo_paths)
        self._provider.register_photos(records)
        self._screensaver_photos.set_display_mode(self.displayMode)
        self._screensaver_photos.set_photos(records)
        self.screensaverSettingsChanged.emit()
        return len(records)

    # --- indítás a gép tétlenségekor (#4613) -------------------------------

    def _screensaver_idle_integration(self) -> IdleIntegration:
        integration = getattr(self, "_screensaver_idle", None)
        if integration is None:
            integration = IdleIntegration.for_session()
            self._screensaver_idle = integration
        return integration

    @Property(bool, notify=screensaverIdleChanged)
    def screensaverIdleSupported(self) -> bool:  # noqa: N802
        return self._screensaver_idle_integration().support().supported

    @Property(str, notify=screensaverIdleChanged)
    def screensaverIdleReason(self) -> str:  # noqa: N802
        """Üres, ha támogatott; különben `not-linux` / `desktop` / `no-swayidle`."""
        return self._screensaver_idle_integration().support().reason

    @Property(str, notify=screensaverIdleChanged)
    def screensaverIdleDesktop(self) -> str:  # noqa: N802
        return self._screensaver_idle_integration().support().desktop

    @Property(bool, notify=screensaverIdleChanged)
    def screensaverIdleEnabled(self) -> bool:  # noqa: N802
        return self._screensaver_idle_integration().is_enabled()

    @Property(bool, notify=screensaverIdleChanged)
    def screensaverIdleAutostart(self) -> bool:  # noqa: N802
        """Az asztal újrabejelentkezéskor magától elindítja a bejegyzést?"""
        return self._screensaver_idle_integration().support().autostart

    @Slot()
    def refreshScreensaverIdle(self) -> None:  # noqa: N802
        """Újraolvastatja az állapotot (a bejegyzést kívülről törölhették)."""
        self.screensaverIdleChanged.emit()

    @Property(int, notify=screensaverIdleChanged)
    def screensaverIdleMinutes(self) -> int:  # noqa: N802
        integration = self._screensaver_idle_integration()
        if integration.is_enabled():
            configured = integration.configured_minutes()
            if configured is not None and MIN_MINUTES <= configured <= MAX_MINUTES:
                return configured
        try:
            minutes = int(self._get_settings().value(_IDLE_MINUTES_KEY, DEFAULT_MINUTES))
        except (TypeError, ValueError):
            return DEFAULT_MINUTES
        return minutes if MIN_MINUTES <= minutes <= MAX_MINUTES else DEFAULT_MINUTES

    @Slot(bool, result=bool)
    def setScreensaverIdleEnabled(self, enabled: bool) -> bool:  # noqa: N802
        """Be-/kikapcsolja a saját tétlenségi bejegyzést; hibánál `False`."""
        integration = self._screensaver_idle_integration()
        try:
            if enabled:
                integration.enable(self.screensaverIdleMinutes)
            else:
                integration.disable()
        except (IdleIntegrationError, OSError, ValueError):
            return False
        finally:
            self.screensaverIdleChanged.emit()
        return True

    @Slot(int, result=bool)
    def setScreensaverIdleMinutes(self, minutes: int) -> bool:  # noqa: N802
        try:
            minutes = int(minutes)
        except (TypeError, ValueError):
            return False
        if not MIN_MINUTES <= minutes <= MAX_MINUTES:
            return False
        self._get_settings().setValue(_IDLE_MINUTES_KEY, minutes)
        integration = self._screensaver_idle_integration()
        result = True
        if integration.is_enabled():
            try:
                integration.enable(minutes)
            except (IdleIntegrationError, OSError, ValueError):
                result = False
        self.screensaverIdleChanged.emit()
        return result
