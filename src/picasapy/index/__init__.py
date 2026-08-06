"""SQLite index: gyors lekérdezések a könyvtárra, ismételhető szinkronnal."""

from .albums import AlbumRecord, album_photos, albums_in_index
from .colors import (
    backfill_colors,
    compute_photo_color,
    load_color_tokens,
    paths_with_color,
    save_colors,
)
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
from .people import PersonRecord, people_in_index, person_photos
from .relocate import (
    RelocationCancelled,
    RelocationError,
    RelocationProgress,
    RelocationResult,
    relocate_data_root,
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
    "AlbumRecord",
    "PersonRecord",
    "PhotoRecord",
    "RelocationCancelled",
    "RelocationError",
    "RelocationProgress",
    "RelocationResult",
    "album_photos",
    "albums_in_index",
    "all_photos",
    "backfill_colors",
    "compute_photo_color",
    "geotagged_photos",
    "load_color_tokens",
    "load_dhashes",
    "open_index",
    "paths_with_color",
    "people_in_index",
    "person_photos",
    "photo_by_id",
    "photos_in_folder",
    "photos_under_folder",
    "prune_foreign_folders",
    "relocate_data_root",
    "remove_root",
    "save_colors",
    "save_dhashes",
    "SearchSuggestion",
    "search_photos",
    "search_suggestions",
    "starred_photos",
    "sync_folder",
    "sync_tree",
    "update_photo_fields",
]
