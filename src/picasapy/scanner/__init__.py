"""Mappa-szkenner: médiafelderítés Picasa-kompatibilis szabályokkal."""

from .discovery import (
    PicasaInstallation,
    discover_installations,
    propose_watched_folders,
)
from .exclude import (
    EXCLUDE_FOLDERS_NAME,
    find_exclude_folders_file,
    is_excluded,
    read_exclude_folders,
)
from .filetypes import (
    PHOTO_EXTENSIONS,
    RAW_EXTENSIONS,
    VIDEO_EXTENSIONS,
    media_kind_of,
)
from .walker import (
    PICASA_INI_LEGACY_NAME,
    PICASA_INI_NAME,
    FolderScan,
    MediaFile,
    SkipPredicate,
    scan_folder,
    scan_tree,
)
from .watched import (
    WATCHED_FOLDERS_NAME,
    find_watched_folders_file,
    read_watched_folders,
    write_watched_folders,
)
from .watcher import LibraryWatcher

__all__ = [
    "EXCLUDE_FOLDERS_NAME",
    "PHOTO_EXTENSIONS",
    "PICASA_INI_LEGACY_NAME",
    "PICASA_INI_NAME",
    "RAW_EXTENSIONS",
    "VIDEO_EXTENSIONS",
    "WATCHED_FOLDERS_NAME",
    "FolderScan",
    "LibraryWatcher",
    "MediaFile",
    "PicasaInstallation",
    "discover_installations",
    "find_exclude_folders_file",
    "find_watched_folders_file",
    "is_excluded",
    "media_kind_of",
    "propose_watched_folders",
    "read_exclude_folders",
    "read_watched_folders",
    "SkipPredicate",
    "scan_folder",
    "scan_tree",
    "write_watched_folders",
]
