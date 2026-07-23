"""Duplikátum-kereső mag (#31): pontos (hash) és perceptuálisan hasonló
(dHash + Hamming-távolság) képek felderítése.

Ez a csomag csak az algoritmust és az adatmodellt adja — a kezelő-felület
(UI) külön jegyre marad. Publikus belépési pont: `find_duplicates`.
"""

from __future__ import annotations

from picasapy.dedup.api import DuplicateReport, find_duplicates
from picasapy.dedup.exact import (
    ExactDuplicateGroup,
    file_content_hash,
    group_exact_duplicates,
)
from picasapy.dedup.phash import compute_dhash, hamming_distance
from picasapy.dedup.similar import (
    DEFAULT_PHASH_THRESHOLD,
    SimilarGroup,
    group_similar,
)

__all__ = [
    "DEFAULT_PHASH_THRESHOLD",
    "DuplicateReport",
    "ExactDuplicateGroup",
    "SimilarGroup",
    "compute_dhash",
    "file_content_hash",
    "find_duplicates",
    "group_exact_duplicates",
    "group_similar",
    "hamming_distance",
]
