"""SQLite index: gyors lekérdezések a könyvtárra, ismételhető szinkronnal."""

from .database import open_index
from .queries import PhotoRecord, photos_in_folder, search_photos, starred_photos
from .schema import SCHEMA_VERSION
from .sync import remove_root, sync_tree

__all__ = [
    "SCHEMA_VERSION",
    "PhotoRecord",
    "open_index",
    "photos_in_folder",
    "remove_root",
    "search_photos",
    "starred_photos",
    "sync_tree",
]
