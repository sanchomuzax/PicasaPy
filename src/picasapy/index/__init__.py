"""SQLite index: gyors lekérdezések a könyvtárra, ismételhető szinkronnal."""

from .database import open_index
from .hashes import load_dhashes, save_dhashes
from .queries import (
    PhotoRecord,
    SearchSuggestion,
    all_photos,
    geotagged_photos,
    photo_by_id,
    photos_in_folder,
    photos_under_folder,
    search_photos,
    search_suggestions,
    starred_photos,
)
from .schema import SCHEMA_VERSION
from .sync import (
    prune_foreign_folders,
    remove_root,
    sync_folder,
    sync_tree,
    update_photo_fields,
)

__all__ = [
    "SCHEMA_VERSION",
    "PhotoRecord",
    "all_photos",
    "geotagged_photos",
    "load_dhashes",
    "open_index",
    "photo_by_id",
    "photos_in_folder",
    "photos_under_folder",
    "prune_foreign_folders",
    "remove_root",
    "save_dhashes",
    "SearchSuggestion",
    "search_photos",
    "search_suggestions",
    "starred_photos",
    "sync_folder",
    "sync_tree",
    "update_photo_fields",
]
