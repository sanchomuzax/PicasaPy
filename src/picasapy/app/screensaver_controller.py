"""A Linuxos teljes képernyős képernyővédő forrásai és beállításai (#4259).

Az eredeti Picasa képernyővédő-kiegészítő volt; itt a már indexelt mappák,
albumok és a menüből hozzáadott képek adják a helyi forrásokat. A beállítások
QSettings-ben élnek, a vetítés pedig külön PhotoGridModelt kap, hogy ne írja
át a könyvtár aktuális kijelölését.
"""

from __future__ import annotations

import os
from pathlib import Path

from PySide6.QtCore import Property, QObject, QSettings, Signal, Slot

from picasapy.index import (
    album_photos,
    albums_in_index,
    all_photos,
    open_index,
    photos_under_folder,
)

from .models import PhotoGridModel, sorted_folder_rows

_SOURCES_KEY = "screensaver/sources"
_PHOTO_PATHS_KEY = "screensaver/photoPaths"
_EFFECT_KEY = "screensaver/effect"
_SECONDS_KEY = "screensaver/seconds"
_CAPTIONS_KEY = "screensaver/showCaptions"
_EFFECTS = {"cut", "dissolve", "dissolveblack", "dissolvewhite", "kenburns"}
_SECONDS_MIN = 1.0
_SECONDS_MAX = 30.0


def _path_key(path: str) -> str:
    return os.path.normcase(os.path.normpath(str(path)))


class ScreensaverMixin:
    """A képernyővédő QML-hídja; a könyvtárvezérlő adatforrásait használja."""

    screensaverSettingsChanged = Signal()
    screensaverSourcesChanged = Signal()

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
                "name": album.name or self._album_placeholder_name(album.token),
                "count": album.photo_count,
            }
            for album in albums
            if album.photo_count > 0
        )
        if self._screensaver_photo_paths():
            sources.append({
                "key": "photos:selected",
                "kind": "photos",
                "name": "",
                "count": len(self._screensaver_photo_paths()),
            })
        return sources

    def _screensaver_photo_paths(self) -> list[str]:
        raw = self._get_settings().value(_PHOTO_PATHS_KEY, [])
        if isinstance(raw, str):
            return [raw] if raw else []
        try:
            return list(dict.fromkeys(str(path) for path in raw if str(path)))
        except TypeError:
            return []

    def _selected_source_keys(self) -> list[str]:
        settings = self._get_settings()
        if settings.contains(_SOURCES_KEY):
            raw = settings.value(_SOURCES_KEY, [])
            if isinstance(raw, str):
                return [raw] if raw else []
            try:
                return list(dict.fromkeys(str(key) for key in raw if str(key)))
            except TypeError:
                return []

        # Első indításkor a figyelt gyökerekből vetít; a felhasználó ezután
        # mappánként vagy albumonként szűkítheti a forrásokat.
        known = {source["key"] for source in self._source_catalog()}
        roots = [f"folder:{root}" for root in self._roots]
        defaults = [key for key in roots if key in known]
        return defaults or [
            source["key"]
            for source in self._source_catalog()
            if source["kind"] == "folder"
        ]

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
        value = str(self._get_settings().value(_EFFECT_KEY, "dissolve"))
        return value if value in _EFFECTS else "dissolve"

    @Slot(str)
    def setScreensaverEffect(self, value: str) -> None:  # noqa: N802
        if value not in _EFFECTS:
            return
        self._get_settings().setValue(_EFFECT_KEY, value)
        self.screensaverSettingsChanged.emit()

    @Property(int, notify=screensaverSettingsChanged)
    def screensaverSeconds(self) -> int:  # noqa: N802
        try:
            seconds = int(self._get_settings().value(_SECONDS_KEY, 3))
        except (TypeError, ValueError):
            return 3
        return seconds if _SECONDS_MIN <= seconds <= _SECONDS_MAX else 3

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
        value = self._get_settings().value(_CAPTIONS_KEY, True)
        return value in (True, "true", "1", 1)

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
        selected = set(self._selected_source_keys())
        records_by_path = {}
        with open_index(self._db_path) as conn:
            for source in self._source_catalog():
                key = source["key"]
                if key not in selected:
                    continue
                if source["kind"] == "folder":
                    records = photos_under_folder(conn, key.removeprefix("folder:"))
                elif source["kind"] == "album":
                    records = album_photos(conn, key.removeprefix("album:"))
                else:
                    wanted = {_path_key(path) for path in self._screensaver_photo_paths()}
                    records = tuple(
                        photo for photo in all_photos(conn)
                        if _path_key(str(Path(photo.folder_path) / photo.name)) in wanted
                    )
                for photo in records:
                    if photo.hidden or photo.kind == "video":
                        continue
                    path = str(Path(photo.folder_path) / photo.name)
                    records_by_path.setdefault(_path_key(path), photo)

        records = tuple(
            records_by_path[key] for key in sorted(records_by_path)
        )
        self._provider.register_photos(records)
        self._screensaver_photos.set_display_mode(self.displayMode)
        self._screensaver_photos.set_photos(records)
        self.screensaverSettingsChanged.emit()
        return len(records)
