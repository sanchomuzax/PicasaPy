"""dHash-gyorsítótár az indexben (#294): a duplikátum-kereső perceptuális
lenyomatai fájl-azonosság szerint eltárolva.

Miért kell: a dHash kiszámítása képenként egy JPEG-dekódolás — 140 000
képnél ez percekben mérhető. A keresés viszont ismételhető művelet (a
felhasználó időnként újrafuttatja), és két futás között a képek túlnyomó
része változatlan. A cache kulcsa ezért a fájl AZONOSSÁGA: `(útvonal,
mtime_ns, méret)` — pontosan az a hármas, amivel a bélyegkép-cache is
dolgozik (`thumbs/cache.py`). Ha bármelyik eltér, a bejegyzés érvénytelen,
és a hívó újraszámol.

A tábla tisztán származtatott gyorsítótár (ld. `schema.py` indoklása):
bármikor üríthető, az index többi része ettől érintetlen.

Előjel-kezelés: a dHash 64 bites ELŐJEL NÉLKÜLI érték, az SQLite INTEGER
viszont előjeles 64 bites. A 2^63 fölötti hash-eket ezért kettes
komplemensben tároljuk, és olvasáskor visszaalakítjuk — enélkül az
`sqlite3` a képek nagyjából felénél OverflowError-t dobna.
"""

from __future__ import annotations

import sqlite3
from collections.abc import Iterable, Sequence

# Az SQLite alapértelmezett paraméter-korlátja (SQLITE_MAX_VARIABLE_NUMBER)
# régebbi buildeknél 999 — a kötegméret ez alatt marad, hogy egy 140k-s
# könyvtár lekérdezése se fusson bele.
_BATCH_SIZE = 300

_UNSIGNED_LIMIT = 1 << 64
_SIGNED_LIMIT = 1 << 63

# (útvonal, mtime_ns, méret) — a fájl azonossága
HashKey = tuple[str, int, int]


def _to_signed(value: int) -> int:
    """Előjel nélküli 64 bites hash → az SQLite-nak adható előjeles érték."""
    return value - _UNSIGNED_LIMIT if value >= _SIGNED_LIMIT else value


def _to_unsigned(value: int) -> int:
    """Az SQLite-ból olvasott előjeles érték → a hívónak járó, előjel
    nélküli 64 bites hash."""
    return value + _UNSIGNED_LIMIT if value < 0 else value


def load_dhashes(
    conn: sqlite3.Connection, keys: Sequence[HashKey]
) -> dict[HashKey, int]:
    """A megadott fájl-azonosságokhoz tárolt dHash-ek.

    A visszaadott szótárban CSAK az érvényes (azonos mtime_ns és méret
    mellett tárolt) bejegyzések szerepelnek — a hiányzó kulcsokat a hívó
    számolja újra. A lekérdezés kötegelve fut, így tetszőleges méretű
    bemenet biztonságos.
    """
    wanted = {(str(path), int(mtime_ns), int(size)) for path, mtime_ns, size in keys}
    if not wanted:
        return {}
    found: dict[HashKey, int] = {}
    paths = [key[0] for key in wanted]
    for start in range(0, len(paths), _BATCH_SIZE):
        batch = paths[start : start + _BATCH_SIZE]
        placeholders = ",".join("?" * len(batch))
        rows = conn.execute(
            "SELECT path, mtime_ns, size, dhash FROM photo_hashes "
            f"WHERE path IN ({placeholders})",
            batch,
        )
        for row in rows:
            key = (row["path"], row["mtime_ns"], row["size"])
            if key in wanted:
                found[key] = _to_unsigned(row["dhash"])
    return found


def save_dhashes(
    conn: sqlite3.Connection, items: Iterable[tuple[str, int, int, int]]
) -> None:
    """`(útvonal, mtime_ns, méret, dhash)` négyesek eltárolása.

    Upsert az útvonalra: a megváltozott fájl régi sora felülíródik (nem
    halmozódik). A hívó dolga a commit — így egy hosszú keresés több
    részletben, a haladás-jelzéssel összhangban menthet."""
    payload = [
        (str(path), int(mtime_ns), int(size), _to_signed(int(value)))
        for path, mtime_ns, size, value in items
    ]
    if not payload:
        return
    conn.executemany(
        "INSERT INTO photo_hashes(path, mtime_ns, size, dhash) VALUES (?, ?, ?, ?) "
        "ON CONFLICT(path) DO UPDATE SET "
        "mtime_ns = excluded.mtime_ns, size = excluded.size, dhash = excluded.dhash",
        payload,
    )
