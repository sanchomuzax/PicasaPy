"""Színkereső gyorsítótár az indexben (#383): `photo_colors` — kép-azonosság
(útvonal, mtime_ns, méret) → átlagszín (`avgcolor`, 0xAARRGGBB) + a hozzá
legközelebbi Picasa-színtoken (`color_token`).

MIÉRT nem a `schema.py`-ban él (ld. az ottani indoklást a `photo_hashes`-nél
és a `sync.py` `folder_scan_state`-jénél is): a `schema.py` FORRÓ fájl —
sémaverziót csak az integrátor oszt ki. A tábla tisztán származtatott adat
(a képből bármikor újraszámolható), ezért lustán, `CREATE TABLE IF NOT
EXISTS`-szel jön létre — nincs szükség migrációra ahhoz, hogy ez a modul
egy meglévő indexen is működjön.

INTEGRÁTORI TEENDŐ (a jegy jelentésében részletezve): ha ez a tábla a
következő sémaverzió-emeléskor átköltözik a `schema.py`-ba (pl. hogy a
`photos` tábla UNIQUE(folder_id, name) kulcsával id-alapú JOIN legyen
lehetséges), a mostani útvonal-alapú kulcs és a lenti API megmarad —
csak a DDL helye változna.

A kulcs- és előjel-kezelés megegyezik a `hashes.py`-éval (photo_hashes):
a fájl AZONOSSÁGA a kulcs, nem az index-beli fotó-id, így a cache egy
újraindexelést (új id) is túlél."""

from __future__ import annotations

import os
import sqlite3
from collections.abc import Iterable, Sequence
from pathlib import Path

from picasapy.color import average_color, classify_color, rgb_to_avgcolor

# Ld. hashes.py — ugyanaz a védőkorlát a paraméteres lekérdezéseknél.
_BATCH_SIZE = 300

# (útvonal, mtime_ns, méret) — a fájl azonossága, mint a photo_hashes-nél.
ColorKey = tuple[str, int, int]

_DDL = """
CREATE TABLE IF NOT EXISTS photo_colors (
    path TEXT PRIMARY KEY,
    mtime_ns INTEGER NOT NULL,
    size INTEGER NOT NULL,
    avgcolor INTEGER NOT NULL,
    color_token TEXT NOT NULL
);
"""


def ensure_color_table(conn: sqlite3.Connection) -> None:
    """A `photo_colors` tábla lusta létrehozása — hívható bármikor,
    idempotens (ld. a `folder_scan_state`-mintát a `sync.py`-ban)."""
    conn.execute(_DDL)


def load_color_tokens(
    conn: sqlite3.Connection, keys: Sequence[ColorKey]
) -> dict[ColorKey, str]:
    """A megadott fájl-azonosságokhoz tárolt `color_token`-ek.

    Csak az ÉRVÉNYES (azonos mtime_ns és méret melletti) bejegyzések
    szerepelnek a visszaadott szótárban — a hiányzó/elavult kulcsokhoz a
    hívó (a háttér-feltöltés) számol újat."""
    ensure_color_table(conn)
    wanted = {(str(path), int(mtime_ns), int(size)) for path, mtime_ns, size in keys}
    if not wanted:
        return {}
    found: dict[ColorKey, str] = {}
    paths = [key[0] for key in wanted]
    for start in range(0, len(paths), _BATCH_SIZE):
        batch = paths[start : start + _BATCH_SIZE]
        placeholders = ",".join("?" * len(batch))
        rows = conn.execute(
            "SELECT path, mtime_ns, size, color_token FROM photo_colors "
            f"WHERE path IN ({placeholders})",
            batch,
        )
        for row in rows:
            key = (row["path"], row["mtime_ns"], row["size"])
            if key in wanted:
                found[key] = row["color_token"]
    return found


def save_colors(
    conn: sqlite3.Connection, items: Iterable[tuple[str, int, int, int, str]]
) -> None:
    """`(útvonal, mtime_ns, méret, avgcolor, color_token)` ötösök eltárolása.

    Upsert az útvonalra — a megváltozott fájl régi sora felülíródik. A
    hívó dolga a commit."""
    payload = [
        (str(path), int(mtime_ns), int(size), int(avgcolor), str(token))
        for path, mtime_ns, size, avgcolor, token in items
    ]
    if not payload:
        return
    ensure_color_table(conn)
    conn.executemany(
        "INSERT INTO photo_colors(path, mtime_ns, size, avgcolor, color_token) "
        "VALUES (?, ?, ?, ?, ?) "
        "ON CONFLICT(path) DO UPDATE SET "
        "mtime_ns = excluded.mtime_ns, size = excluded.size, "
        "avgcolor = excluded.avgcolor, color_token = excluded.color_token",
        payload,
    )


def paths_with_color(conn: sqlite3.Connection, tokens: Sequence[str]) -> set[str]:
    """A megadott `color_token`(ek) BÁRMELYIKÉVEL rendelkező fotók útvonalai
    (#383, a `color:`/`szín:` keresőtokenhez) — kötegelve, a paraméter-
    korlát miatt (ld. a modul tetején lévő `_BATCH_SIZE` indoklását)."""
    ensure_color_table(conn)
    wanted = tuple(dict.fromkeys(tokens))
    if not wanted:
        return set()
    found: set[str] = set()
    for start in range(0, len(wanted), _BATCH_SIZE):
        batch = wanted[start : start + _BATCH_SIZE]
        placeholders = ",".join("?" * len(batch))
        rows = conn.execute(
            f"SELECT path FROM photo_colors WHERE color_token IN ({placeholders})",
            batch,
        )
        found.update(row["path"] for row in rows)
    return found


def compute_photo_color(path: str | Path) -> tuple[int, str] | None:
    """Egy kép átlagszíne + tokenje a kis (bélyegkép-méretű) dekódolásból.

    A teljes felbontású olvasás elkerülése végett a dekódolás a
    `reduced_color_flag`-fel megegyező, redukált-méretű útvonalat használja
    (ld. `picasapy.cvimage` — ugyanezt hívja a bélyegkép-gyorsítótár és a
    dedup dHash-e is). `None`, ha a fájl nem dekódolható (törölt/sérült/nem
    kép — pl. videó)."""
    from picasapy.cvimage import read_image_bytes, reduced_color_flag

    payload = read_image_bytes(Path(path))
    if payload is None:
        return None
    import cv2

    flag = reduced_color_flag(payload, 128)
    image = cv2.imdecode(payload, flag)
    if image is None:
        return None
    average = average_color(image, order="bgr")
    if average is None:
        return None
    r, g, b, a = average
    token = classify_color(r, g, b)
    return rgb_to_avgcolor(r, g, b, a), token


def backfill_colors(conn: sqlite3.Connection, limit: int = 200) -> int:
    """Legfeljebb `limit` darab, még szín-token nélküli FÉNYKÉP (nem videó)
    feltöltése (#383, „ne blokkolja az indulást" — a hívó dolga ezt kis
    kötegekben, háttérszálon, ismételten meghívni, amíg 0-t nem ad vissza).

    A jelölt-lista SQL-oldali `LEFT JOIN ... WHERE color_token IS NULL`
    szűréssel jön, így nagy könyvtárnál sem kell Pythonban végigmenni a
    teljes `photos` táblán minden híváskor. A visszatérési érték a
    ténylegesen feldolgozott (sikeresen dekódolt VAGY véglegesen
    dekódolhatatlannak bizonyult) sorok száma — 0 jelzi, hogy nincs több
    teendő."""
    ensure_color_table(conn)
    rows = conn.execute(
        "SELECT f.path AS folder_path, p.name, p.mtime_ns, p.size "
        "FROM photos p JOIN folders f ON f.id = p.folder_id "
        "LEFT JOIN photo_colors c ON c.path = f.path || :sep || p.name "
        "WHERE p.kind = 'photo' AND c.path IS NULL "
        "LIMIT :limit",
        {"sep": os.sep, "limit": int(limit)},
    ).fetchall()
    processed = 0
    payload: list[tuple[str, int, int, int, str]] = []
    for row in rows:
        full_path = str(Path(row["folder_path"]) / row["name"])
        result = compute_photo_color(full_path)
        processed += 1
        if result is None:
            continue
        avgcolor, token = result
        payload.append((full_path, row["mtime_ns"], row["size"], avgcolor, token))
    save_colors(conn, payload)
    conn.commit()
    return processed
