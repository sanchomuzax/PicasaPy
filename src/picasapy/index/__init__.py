"""SQLite index: gyors lekérdezések a könyvtárra, ismételhető szinkronnal."""

from .database import open_index
from .queries import (
    PhotoRecord,
    SearchSuggestion,
    all_photos,
    photos_in_folder,
    search_photos,
    search_suggestions,
    starred_photos,
)
from .schema import SCHEMA_VERSION
from .sync import prune_foreign_folders, remove_root, sync_tree

__all__ = [
    "SCHEMA_VERSION",
    "PhotoRecord",
    "all_photos",
    "open_index",
    "photos_in_folder",
    "prune_foreign_folders",
    "remove_root",
    "SearchSuggestion",
    "search_photos",
    "search_suggestions",
    "starred_photos",
    "sync_tree",
]
