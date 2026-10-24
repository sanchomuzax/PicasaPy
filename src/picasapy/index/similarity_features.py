"""A hasonlóságkeresés képszármaztatott jellemzőinek SQLite-cache-e (#5744)."""

from __future__ import annotations

import sqlite3
from collections.abc import Iterable, Sequence

from picasapy.dedup.similarity import (
    SimilarityFeatures,
    pack_similarity_features,
    unpack_similarity_features,
)

from .hashes import HashKey

_BATCH_SIZE = 300


def load_similarity_features(
    conn: sqlite3.Connection, keys: Sequence[HashKey]
) -> dict[HashKey, SimilarityFeatures]:
    """Csak az útvonal, mtime és méret szerint érvényes jellemzőket adja."""
    wanted = {(str(path), int(mtime_ns), int(size)) for path, mtime_ns, size in keys}
    if not wanted:
        return {}
    found: dict[HashKey, SimilarityFeatures] = {}
    paths = list({key[0] for key in wanted})
    for start in range(0, len(paths), _BATCH_SIZE):
        batch = paths[start : start + _BATCH_SIZE]
        placeholders = ",".join("?" * len(batch))
        rows = conn.execute(
            "SELECT path, mtime_ns, size, rgb565, histogram, edges "
            "FROM photo_similarity "
            f"WHERE path IN ({placeholders})",
            batch,
        )
        for row in rows:
            key = (row["path"], row["mtime_ns"], row["size"])
            if key not in wanted:
                continue
            found[key] = unpack_similarity_features(
                row["rgb565"], row["histogram"], row["edges"]
            )
    return found


def save_similarity_features(
    conn: sqlite3.Connection,
    items: Iterable[tuple[str, int, int, SimilarityFeatures]],
) -> None:
    """`(útvonal, mtime_ns, méret, jellemzők)` upsert; a hívó commitol."""
    payload = []
    for path, mtime_ns, size, features in items:
        rgb565, histogram, edges = pack_similarity_features(features)
        payload.append((str(path), int(mtime_ns), int(size), rgb565, histogram, edges))
    if not payload:
        return
    conn.executemany(
        "INSERT INTO photo_similarity"
        "(path, mtime_ns, size, rgb565, histogram, edges) "
        "VALUES (?, ?, ?, ?, ?, ?) "
        "ON CONFLICT(path) DO UPDATE SET "
        "mtime_ns = excluded.mtime_ns, size = excluded.size, "
        "rgb565 = excluded.rgb565, histogram = excluded.histogram, "
        "edges = excluded.edges",
        payload,
    )
