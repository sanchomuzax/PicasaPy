"""Duplikátum-kereső mag (#31): pontos (hash) és perceptuálisan hasonló
(dHash + Hamming-távolság) képek felderítése.

Ez a csomag csak az algoritmust és az adatmodellt adja — a kezelő-felület
(UI) külön jegyre marad. Publikus belépési pont: `find_duplicates`.

#1481 — a Picasa fej+farok SZÁRMAZÁS-kulcsa (`fastkey.picasa_fast_key`) mint
olcsó előszűrő a teljes hash előtt.
"""

from __future__ import annotations

from picasapy.dedup.api import DuplicateReport, find_duplicates
from picasapy.dedup.exact import (
    ExactDuplicateGroup,
    FastKeySource,
    file_content_hash,
    group_exact_duplicates,
)
from picasapy.dedup.fastkey import (
    FAROK_KUSZOB,
    FEJ_MERET,
    picasa_fast_key,
)
from picasapy.dedup.phash import compute_dhash, hamming_distance
from picasapy.dedup.similar import (
    DEFAULT_PHASH_THRESHOLD,
    SimilarGroup,
    group_similar,
)

__all__ = [
    "DEFAULT_PHASH_THRESHOLD",
    "FAROK_KUSZOB",
    "FEJ_MERET",
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
    "picasa_fast_key",
]
