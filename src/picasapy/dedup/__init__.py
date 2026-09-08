"""Duplikátum-kereső mag (#31): pontos (hash) és perceptuálisan hasonló
(dHash + Hamming-távolság) képek felderítése.

Ez a csomag csak az algoritmust és az adatmodellt adja — a kezelő-felület
(UI) külön jegyre marad. Publikus belépési pont: `find_duplicates`.

#1481 — a Picasa fej+farok SZÁRMAZÁS-kulcsa (`fastkey.picasa_fast_key`) mint
olcsó előszűrő a teljes hash előtt. #1482 / #2733 — a lassú kulcs
(`slowkey.picasa_slow_key`) és a kettő szöveges párja, az ini `originhash`
(`originhash.origin_hash`).
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
from picasapy.dedup.originhash import (
    ORIGINHASH_HOSSZ,
    origin_hash,
    originhash_szetszed,
    originhash_szoveg,
)
from picasapy.dedup.phash import compute_dhash, hamming_distance
from picasapy.dedup.similar import (
    DEFAULT_PHASH_THRESHOLD,
    SimilarGroup,
    group_similar,
)
from picasapy.dedup.slowkey import picasa_slow_key

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
