"""Duplikátum-kereső mag (#31): pontos és perceptuálisan hasonló képek.

A csomag algoritmust és adatmodellt ad; a kezelőfelület külön rétegben él.
Publikus belépési pontja a `find_duplicates`. A Picasa fej+farok származás-
kulcsa (`fastkey.picasa_fast_key`), a lassú kulcs (`slowkey.picasa_slow_key`)
és az ini `originhash` párja külön exportként érhető el.

A publikus neveket csak kéréskor importáljuk, így az index gyorskulcsai nem
húzzák be a teljes deduplikációs algoritmuscsomagot.
"""

from __future__ import annotations

from importlib import import_module

_EXPORT_MODULES = {
    "api": ("DuplicateReport", "find_duplicates"),
    "exact": (
        "ExactDuplicateGroup",
        "FastKeySource",
        "file_content_hash",
        "group_exact_duplicates",
    ),
    "fastkey": ("FAROK_KUSZOB", "FEJ_MERET", "picasa_fast_key"),
    "originhash": (
        "ORIGINHASH_HOSSZ",
        "origin_hash",
        "originhash_szetszed",
        "originhash_szoveg",
    ),
    "phash": ("compute_dhash", "hamming_distance"),
    "similar": ("DEFAULT_PHASH_THRESHOLD", "SimilarGroup", "group_similar"),
    "slowkey": ("picasa_slow_key",),
}

_NAME_TO_MODULE = {
    name: module_name
    for module_name, names in _EXPORT_MODULES.items()
    for name in names
}
__all__ = [
    "DEFAULT_PHASH_THRESHOLD",
    "FAROK_KUSZOB",
    "FEJ_MERET",
    "ORIGINHASH_HOSSZ",
    "DuplicateReport",
    "ExactDuplicateGroup",
    "FastKeySource",
    "SimilarGroup",
    "compute_dhash",
    "file_content_hash",
    "find_duplicates",
    "group_exact_duplicates",
    "group_similar",
    "hamming_distance",
    "origin_hash",
    "originhash_szetszed",
    "originhash_szoveg",
    "picasa_fast_key",
    "picasa_slow_key",
]


def __getattr__(name: str):
    """A publikus API-t csak a kért duplikátumművelet tölti be."""
    module_name = _NAME_TO_MODULE.get(name)
    if module_name is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    value = getattr(import_module(f".{module_name}", __name__), name)
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    return sorted(set(globals()) | set(__all__))
