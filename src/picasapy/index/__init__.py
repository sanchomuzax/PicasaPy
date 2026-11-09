"""SQLite index: gyors lekérdezések a könyvtárra, ismételhető szinkronnal."""

from .album_collage import (
    COLLAGE_PROJECT_NAME,
    albums_with_collage,
    folder_has_collage,
)
from .albums import AlbumRecord, album_photos, albums_in_index
from .colors import (
    backfill_colors,
    color_index_progress,
    compute_photo_color,
    load_color_tokens,
    paths_with_color,
    save_colors,
)
from .database import open_index
from .hidden_scope import hidden_folders_visible, set_hidden_folders_visible
from .ignored_ini_faces import IniIgnoredFace, ignored_ini_faces
from .fast_key_source import IndexFastKeySource
from .hashes import load_dhashes, load_fast_keys, save_dhashes, save_fast_keys
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
    hidden_folders,
    is_folder_hidden,
    set_folder_hidden,
    starred_photos,
    photos_up_to_age,
    photos_with_keyword,
    video_photos,
)
from .people import (
    PersonRecord,
    people_in_index,
    photos_with_faces,
    people_with,
    person_photos,
)
from .person_thumbnails import (
    PersonThumbnail,
    person_thumbnail,
    person_thumbnail_face,
    person_thumbnails,
    set_person_thumbnail,
)
from .project_folders import ProjectFolder, project_folders
from .relocate import (
    RelocationCancelled,
    RelocationError,
    RelocationProgress,
    RelocationResult,
    relocate_data_root,
)
from .schema import SCHEMA_VERSION
from .sync import (
    add_removed_folder,
    clear_removed_folders_under,
    folder_looks_offline,
    folder_paths_under,
    folder_scan_stamps,
    move_folder_tree,
    removed_folder_paths,
    prune_foreign_folders,
    remove_folder_tree,
    remove_root,
    sync_folder,
    sync_tree,
    update_photo_fields,
    watched_root_missing,
)

__all__ = [
    "COLLAGE_PROJECT_NAME",
    "SCHEMA_VERSION",
    "AlbumRecord",
    "PendingEmbeddingFace",
    "UnnamedFace",
    "PersonRecord",
    "PersonThumbnail",
    "PhotoRecord",
    "ProjectFolder",
    "RelocationCancelled",
    "RelocationError",
    "RelocationProgress",
    "RelocationResult",
    "album_photos",
    "albums_in_index",
    "albums_with_collage",
    "all_photos",
    "backfill_colors",
    "color_index_progress",
    "clear_faces",
    "compute_photo_color",
    "detected_face_count",
    "face_embedding",
    "face_groups",
    "faces_missing_embedding",
    "folder_scan_stamps",
    "geotagged_photos",
    "hidden_folders",
    "hidden_folders_visible",
    "is_folder_hidden",
    "set_folder_hidden",
    "set_hidden_folders_visible",
    "photos_up_to_age",
    "photos_with_keyword",
    "video_photos",
    "group_unnamed_faces",
    "javaslatokat_ujraszamol",
    "lazitott_lepcso",
    "load_color_tokens",
    "IndexFastKeySource",
    "load_dhashes",
    "load_fast_keys",
    "ignored_faces",
    "named_centroids",
    "mark_faces_ignored",
    "mark_faces_named",
    "open_index",
    "paths_with_color",
    "people_in_index",
    "photos_with_faces",
    "people_with",
    "person_photos",
    "person_thumbnail",
    "person_thumbnail_face",
    "person_thumbnails",
    "photo_by_id",
    "unnamed_album_photos",
    "unnamed_photo_count",
    "unnamed_face_count",
    "photos_in_folder",
    "photos_under_folder",
    "folder_has_collage",
    "project_folders",
    "prune_foreign_folders",
    "relocate_data_root",
    "add_removed_folder",
    "clear_removed_folders_under",
    "remove_root",
    "remove_folder_tree",
    "folder_paths_under",
    "move_folder_tree",
    "removed_folder_paths",
    "delete_faces_in_folder",
    "face_scan_done",
    "faces_for_photo",
    "IniIgnoredFace",
    "ignored_ini_faces",
    "forget_face_scan",
    "mark_face_scan",
    "mark_folder_excluded",
    "replace_faces",
    "replace_imported_unnamed_faces",
    "reset_all_faces",
    "save_colors",
    "save_dhashes",
    "save_fast_keys",
    "set_person_thumbnail",
    "SearchSuggestion",
    "search_photos",
    "search_suggestions",
    "starred_photos",
    "store_embedding",
    "sync_folder",
    "sync_tree",
    "set_suggested_name",
    "suggested_faces",
    "suggested_faces_for",
    "unignore_faces",
    "unnamed_faces",
    "unnamed_faces_for_photos",
    "update_photo_fields",
    "folder_looks_offline",
    "watched_root_missing",
]

import importlib

_LAZY_FACE_EXPORTS = {
    "face_groups": ".face_groups",
    "group_unnamed_faces": ".face_groups",
    "javaslatokat_ujraszamol": ".face_groups",
    "lazitott_lepcso": ".face_groups",
    "PendingEmbeddingFace": ".faces_detected",
    "UnnamedFace": ".faces_detected",
    "clear_faces": ".faces_detected",
    "detected_face_count": ".faces_detected",
    "face_embedding": ".faces_detected",
    "faces_missing_embedding": ".faces_detected",
    "ignored_faces": ".faces_detected",
    "named_centroids": ".faces_detected",
    "mark_faces_ignored": ".faces_detected",
    "mark_faces_named": ".faces_detected",
    "delete_faces_in_folder": ".faces_detected",
    "face_scan_done": ".faces_detected",
    "faces_for_photo": ".faces_detected",
    "forget_face_scan": ".faces_detected",
    "mark_face_scan": ".faces_detected",
    "mark_folder_excluded": ".faces_detected",
    "replace_faces": ".faces_detected",
    "replace_imported_unnamed_faces": ".faces_detected",
    "reset_all_faces": ".faces_detected",
    "store_embedding": ".faces_detected",
    "unnamed_album_photos": ".faces_detected",
    "unnamed_photo_count": ".faces_detected",
    "unnamed_face_count": ".faces_detected",
    "set_suggested_name": ".faces_detected",
    "suggested_faces": ".faces_detected",
    "suggested_faces_for": ".faces_detected",
    "unignore_faces": ".faces_detected",
    "unnamed_faces": ".faces_detected",
    "unnamed_faces_for_photos": ".faces_detected",
}


def __getattr__(name: str):
    """Az arcmodulokat csak az első csomagszintű használatkor importálja."""
    module_name = _LAZY_FACE_EXPORTS.get(name)
    if module_name is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    module = importlib.import_module(module_name, __name__)
    value = getattr(module, name)
    globals()[name] = value
    return value


def __dir__():
    return sorted(set(globals()) | set(_LAZY_FACE_EXPORTS))
