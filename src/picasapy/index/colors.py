"""Színkereső gyorsítótár az indexben (#383, #1480): `photo_colors` —
kép-azonosság (útvonal, mtime_ns, méret) → a kép Picasa-színtokenjei
(`color_tokens`) + az `avgcolor` (0xAARRGGBB) kép-metaadat.

⚠️ #1480: a színtoken NEM az átlagszínből jön. A Picasa a kép EGÉSZ
raszteréről épít telítettséggel súlyozott hue-hisztogramot, és a
legnagyobb vödör nyer (`picasapy.color.classify_image`,
`docs/specs/picasa-szinkereses.md`). Az `avgcolor` külön kép-metaadat, a
keresésnek nem bemenete — azért marad a táblában, mert ugyanabból a már
dekódolt rasztertől olcsón megvan.

Egy képhez TÖBB token is tartozhat: az akromatikus kép az eredetiben
egyszerre illeszkedik a `black`, `white` és `gray` tokenre. A tábla ezért
szóközzel elválasztott token-listát tárol (`color_tokens`).

MIÉRT nem a `schema.py`-ban él (ld. az ottani indoklást a `photo_hashes`-nél
és a `sync.py` `folder_scan_state`-jénél is): a `schema.py` FORRÓ fájl —
sémaverziót csak az integrátor oszt ki. A tábla tisztán származtatott adat
(a képből bármikor újraszámolható), ezért lustán, `CREATE TABLE IF NOT
EXISTS`-szel jön létre — nincs szükség migrációra ahhoz, hogy ez a modul
egy meglévő indexen is működjön. Ugyanezért a #1480 előtti, ÁTLAGSZÍNBŐL
számolt sorokat sem migráljuk: a régi alakú táblát eldobjuk, a
háttér-feltöltés újraszámolja.

A kulcs- és előjel-kezelés megegyezik a `hashes.py`-éval (photo_hashes):
a fájl AZONOSSÁGA a kulcs, nem az index-beli fotó-id, így a cache egy
újraindexelést (új id) is túlél."""

from __future__ import annotations

import os
import sqlite3
from collections.abc import Iterable, Sequence
from pathlib import Path

from picasapy.color import (
    ACHROMATIC_TOKENS,
    HUE_BUCKET_TOKENS,
    average_color,
    classify_image,
    rgb_to_avgcolor,
)

# Ld. hashes.py — ugyanaz a védőkorlát a paraméteres lekérdezéseknél.
_BATCH_SIZE = 300

# (útvonal, mtime_ns, méret) — a fájl azonossága, mint a photo_hashes-nél.
ColorKey = tuple[str, int, int]

# A tárolt `color_tokens` érték MINDIG e nyolc alak egyike: a hét
# hue-vödör egy-egy tokenje, vagy az akromatikus hármas. Ezért a keresés
# nem szövegrészletre illeszt, hanem a nyolc lehetséges érték közül
# válogat — így marad indexelhető egyenlőség-vizsgálat.
_STORED_VALUES: tuple[str, ...] = tuple(HUE_BUCKET_TOKENS) + (
    " ".join(ACHROMATIC_TOKENS),
)

_DDL = """
CREATE TABLE IF NOT EXISTS photo_colors (
    path TEXT PRIMARY KEY,
    mtime_ns INTEGER NOT NULL,
    size INTEGER NOT NULL,
    avgcolor INTEGER NOT NULL,
    color_tokens TEXT NOT NULL
);
"""


def ensure_color_table(conn: sqlite3.Connection) -> None:
    """A `photo_colors` tábla lusta létrehozása — hívható bármikor,
    idempotens (ld. a `folder_scan_state`-mintát a `sync.py`-ban).

    A #1480 előtti tábla `color_token` oszlopa átlagszínből számolt, MOST
    MÁR HIBÁS besorolást tárol; ilyet találva a táblát eldobjuk. Tiszta
    gyorsítótár, a háttér-feltöltés újratölti — migrálni értelmetlen
    lenne, hiszen minden sorát újra kell számolni."""
    columns = {row[1] for row in conn.execute("PRAGMA table_info(photo_colors)")}
    if columns and "color_tokens" not in columns:
        conn.execute("DROP TABLE photo_colors")
    conn.execute(_DDL)


def load_color_tokens(
    conn: sqlite3.Connection, keys: Sequence[ColorKey]
) -> dict[ColorKey, tuple[str, ...]]:
    """A megadott fájl-azonosságokhoz tárolt színtokenek.

    Csak az ÉRVÉNYES (azonos mtime_ns és méret melletti) bejegyzések
    szerepelnek a visszaadott szótárban — a hiányzó/elavult kulcsokhoz a
    hívó (a háttér-feltöltés) számol újat."""
    ensure_color_table(conn)
    wanted = {(str(path), int(mtime_ns), int(size)) for path, mtime_ns, size in keys}
    if not wanted:
        return {}
    found: dict[ColorKey, tuple[str, ...]] = {}
    paths = [key[0] for key in wanted]
    for start in range(0, len(paths), _BATCH_SIZE):
        batch = paths[start : start + _BATCH_SIZE]
        placeholders = ",".join("?" * len(batch))
        rows = conn.execute(
            "SELECT path, mtime_ns, size, color_tokens FROM photo_colors "
            f"WHERE path IN ({placeholders})",
            batch,
        )
        for row in rows:
            key = (row["path"], row["mtime_ns"], row["size"])
            if key in wanted:
                found[key] = tuple(row["color_tokens"].split())
    return found


def save_colors(
    conn: sqlite3.Connection, items: Iterable[tuple[str, int, int, int, Sequence[str]]]
) -> None:
    """`(útvonal, mtime_ns, méret, avgcolor, tokenek)` ötösök eltárolása.

    Upsert az útvonalra — a megváltozott fájl régi sora felülíródik. A
    hívó dolga a commit."""
    payload = [
        (str(path), int(mtime_ns), int(size), int(avgcolor), " ".join(tokens))
        for path, mtime_ns, size, avgcolor, tokens in items
    ]
    if not payload:
        return
    ensure_color_table(conn)
    conn.executemany(
        "INSERT INTO photo_colors(path, mtime_ns, size, avgcolor, color_tokens) "
        "VALUES (?, ?, ?, ?, ?) "
        "ON CONFLICT(path) DO UPDATE SET "
        "mtime_ns = excluded.mtime_ns, size = excluded.size, "
        "avgcolor = excluded.avgcolor, color_tokens = excluded.color_tokens",
        payload,
    )


def paths_with_color(conn: sqlite3.Connection, tokens: Sequence[str]) -> set[str]:
    """A megadott színtoken(ek) BÁRMELYIKÉVEL rendelkező fotók útvonalai
    (#383, a `color:`/`szín:` keresőtokenhez).

    A `black`/`white`/`gray` bármelyike ugyanazt a képhalmazt adja: az
    eredeti a három akromatikus token között nem tesz különbséget
    (#1480). Ismeretlen token egyszerűen nem illeszkedik semmire."""
    ensure_color_table(conn)
    wanted = set(tokens)
    candidates = [
        value for value in _STORED_VALUES if wanted.intersection(value.split())
    ]
    if not candidates:
        return set()
    placeholders = ",".join("?" * len(candidates))
    rows = conn.execute(
        f"SELECT path FROM photo_colors WHERE color_tokens IN ({placeholders})",
        candidates,
    )
    return {row["path"] for row in rows}


def compute_photo_color(path: str | Path) -> tuple[int, tuple[str, ...]] | None:
    """Egy kép színtokenjei + `avgcolor`-a a kis (bélyegkép-méretű)
    dekódolásból.

    A teljes felbontású olvasás elkerülése végett a dekódolás a
    `reduced_color_flag`-fel megegyező, redukált-méretű útvonalat használja
    (ld. `picasapy.cvimage` — ugyanezt hívja a bélyegkép-gyorsítótár és a
    dedup dHash-e is). Az eredeti is a bélyegkép-gyorstárból dolgozott
    (erős, de nem bizonyított lelet; golden anyag híján a raszter MÉRETE
    nem is ellenőrizhető — ld. a spec „nyitott kérdések" táblázatát).

    `None`, ha a fájl nem dekódolható (törölt/sérült/nem kép — pl. videó).
    A 2×2-nél kisebb képnek nincs `avgcolor`-a (a Picasa sem számol
    ilyet) — ott a `0` sentinel áll, a színtokenek viszont a rasztertől
    függetlenül megvannak."""
    from picasapy.cvimage import read_image_bytes, reduced_color_flag

    payload = read_image_bytes(Path(path))
    if payload is None:
        return None
    import cv2

    flag = reduced_color_flag(payload, 128)
    image = cv2.imdecode(payload, flag)
    if image is None:
        return None
    tokens = classify_image(image, order="bgr")
    average = average_color(image, order="bgr")
    if average is None:
        return 0, tokens
    r, g, b, a = average
    return rgb_to_avgcolor(r, g, b, a), tokens


def backfill_colors(conn: sqlite3.Connection, limit: int = 200) -> int:
    """Legfeljebb `limit` darab, még szín-token nélküli FÉNYKÉP (nem videó)
    feltöltése (#383, „ne blokkolja az indulást" — a hívó dolga ezt kis
    kötegekben, háttérszálon, ismételten meghívni, amíg 0-t nem ad vissza).

    A jelölt-lista SQL-oldali `LEFT JOIN ... WHERE color_tokens IS NULL`
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
    payload: list[tuple[str, int, int, int, Sequence[str]]] = []
    for row in rows:
        full_path = str(Path(row["folder_path"]) / row["name"])
        result = compute_photo_color(full_path)
        processed += 1
        if result is None:
            continue
        avgcolor, tokens = result
        payload.append((full_path, row["mtime_ns"], row["size"], avgcolor, tokens))
    save_colors(conn, payload)
    conn.commit()
    return processed
