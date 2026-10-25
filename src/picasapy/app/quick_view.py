"""Közvetlen fájlmegnyitás a gyorsnézegetőben (#5762)."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path

from PySide6.QtCore import QUrl
from PySide6.QtGui import QImageReader

from picasapy.ini import INI_NAME, load_or_empty
from picasapy.index.queries import PhotoRecord
from picasapy.scanner.filetypes import PHOTO_EXTENSIONS


# A desktop társítások a PicasaPy által képformátumként kezelt kiterjesztések
# MIME-típusai. A RAW külön médiaosztály, ezért nem kerül ide.
_EXTENSION_MIME_OVERRIDES = {
    ".bmp": "image/bmp",
    ".gif": "image/gif",
    ".jpe": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".jpg": "image/jpeg",
    ".png": "image/png",
    ".psd": "image/vnd.adobe.photoshop",
    ".tga": "image/x-tga",
    ".tif": "image/tiff",
    ".tiff": "image/tiff",
    ".webp": "image/webp",
}

IMAGE_MIME_TYPES_BY_EXTENSION = {
    extension: _EXTENSION_MIME_OVERRIDES[extension]
    for extension in sorted(PHOTO_EXTENSIONS)
}
SUPPORTED_IMAGE_MIME_TYPES = tuple(sorted(set(IMAGE_MIME_TYPES_BY_EXTENSION.values())))

# A thumbnail-provider más további rekordjai -1…-999 999, illetve
# -1 000 000-től lefelé használják az azonosítótartományt.
# A nagy, de JavaScriptben még pontos egész számként ábrázolható ideiglenes
# tartomány külön marad a provider többi negatív azonosítójától.
QUICK_VIEW_ID_BASE = -8_000_000_000_000_000


@dataclass(frozen=True)
class LaunchArguments:
    """A parancssori képútvonalak és könyvtárgyökerek külön listája."""

    photo_paths: tuple[str, ...] = ()
    directory_roots: tuple[str, ...] = ()


def _local_path(argument: str) -> Path | None:
    value = str(argument or "").strip()
    if not value:
        return None

    # A raw Windows drive path is parsed by QUrl as a one-letter URL scheme.
    # Keep it as a path; file:// URLs are handled by the next branch.
    windows_drive_path = re.match(r"^[A-Za-z]:[\\/]", value) is not None
    if not windows_drive_path:
        url = QUrl(value)
        if url.isLocalFile():
            value = url.toLocalFile()
        elif url.scheme():
            return None

    return Path(os.path.abspath(os.path.expanduser(value)))


def parse_launch_arguments(argv: list[str]) -> LaunchArguments:
    """Szétválasztja a létező támogatott képeket és a létező könyvtárakat.

    A fájlkezelők a desktop `%U` mezőjén át `file://` URL-eket is adhatnak.
    Nem helyi URL és nem létező cél nem indít könyvtár- vagy fájlbetöltést.
    """
    photos: list[str] = []
    roots: list[str] = []
    seen_photos: set[str] = set()
    seen_roots: set[str] = set()

    for argument in argv[1:]:
        path = _local_path(argument)
        if path is None:
            continue
        normalized = str(path)
        key = os.path.normcase(normalized)
        if path.is_dir():
            if key not in seen_roots:
                seen_roots.add(key)
                roots.append(normalized)
        elif path.is_file() and path.suffix.lower() in PHOTO_EXTENSIONS:
            if key not in seen_photos:
                seen_photos.add(key)
                photos.append(normalized)

    return LaunchArguments(tuple(photos), tuple(roots))


def quick_view_records(photo_paths: tuple[str, ...]) -> tuple[PhotoRecord, ...]:
    """Könnyű, csak a kifejezetten kért fájlokat leíró viewer-rekordok."""
    records = []
    folder_documents = {}
    for index, raw_path in enumerate(photo_paths):
        path = Path(raw_path)
        stat = path.stat()
        image_size = QImageReader(str(path)).size()
        width = image_size.width() if image_size.isValid() else None
        height = image_size.height() if image_size.isValid() else None
        if path.parent not in folder_documents:
            folder_documents[path.parent] = load_or_empty(
                path.parent / INI_NAME
            )
        section = folder_documents[path.parent].section(path.name)
        records.append(
            PhotoRecord(
                id=QUICK_VIEW_ID_BASE - index - 1,
                folder_path=str(path.parent),
                name=path.name,
                kind="photo",
                size=stat.st_size,
                mtime_ns=stat.st_mtime_ns,
                star=bool(section and section.get("star") == "yes"),
                caption=None,
                keywords=None,
                rotate_steps=0,
                filters=None,
                taken_at=None,
                orientation=1,
                width=width,
                height=height,
            )
        )
    return tuple(records)
