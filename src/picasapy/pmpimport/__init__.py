"""PMP/db3-import (#1): Windowsos Picasa-adatbázis ismételhető olvasása.

A publikus nevek lusták: a Picasa telepítésének felderítése nem tölti be a
teljes adatbázis-importot.
"""

from __future__ import annotations

from importlib import import_module

_EXPORT_MODULES = {
    "cacheblob": ("CACHE_NEVEK", "FACETEMPLATE_HOSSZ", "CacheStore", "open_cache_store"),
    "deferredregion": (
        "DeferredFace",
        "parse_deferred_face",
        "parse_deferred_region",
    ),
    "importer": (
        "Db3Beolvasas",
        "PhotoRecord",
        "beolvas_db3",
        "iter_photo_records",
    ),
    "pmp_column": ("PmpColumn", "PmpFormatError", "read_pmp_column"),
    "remap": ("PathRemapper",),
    "table": ("PmpTable", "read_table"),
    "thumbindex": (
        "ThumbIndexEntry",
        "ThumbIndexFormatError",
        "read_thumb_index",
        "resolve_path",
    ),
}

_NAME_TO_MODULE = {
    name: module_name
    for module_name, names in _EXPORT_MODULES.items()
    for name in names
}
__all__ = [
    "CACHE_NEVEK",
    "FACETEMPLATE_HOSSZ",
    "CacheStore",
    "DeferredFace",
    "Db3Beolvasas",
    "PathRemapper",
    "PhotoRecord",
    "PmpColumn",
    "PmpFormatError",
    "PmpTable",
    "ThumbIndexEntry",
    "ThumbIndexFormatError",
    "beolvas_db3",
    "iter_photo_records",
    "open_cache_store",
    "parse_deferred_region",
    "parse_deferred_face",
    "read_pmp_column",
    "read_table",
    "read_thumb_index",
    "resolve_path",
]


def __getattr__(name: str):
    """A db3-import publikus API-ját csak az adott importfunkció tölti be."""
    module_name = _NAME_TO_MODULE.get(name)
    if module_name is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    value = getattr(import_module(f".{module_name}", __name__), name)
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    return sorted(set(globals()) | set(__all__))
