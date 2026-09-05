"""A duplikátum-kereső KÉT gyorsítótára az indexben, egyetlen táblában
(`photo_hashes`): a perceptuális dHash (#294) és a Picasa fej+farok
GYORSKULCSA (`originfast`, #1494), fájl-azonosság szerint eltárolva.

Miért egy tábla: mindkettő ugyanarra a hármasra kulcsol (`útvonal, mtime_ns,
méret`), és mindkettő tisztán származtatott — külön tábla ugyanazt a kulcsot
ismételné meg. Ennek AZ ÁRA, hogy mindkét oszlop írója felel a MÁSIK
érvényességéért is: ha a fájl azonossága megváltozott, a sorban maradó másik
érték már idegen fájlra vonatkozna. Mindkét mentés ezért NULL-ozza a párját,
ha az `mtime_ns`/`méret` nem egyezik a tárolttal (ld.
`_PAROSZLOP_ERVENYTELENITES`).

Miért kell a dHash-gyorstár: a dHash kiszámítása képenként egy JPEG-dekódolás
— 140 000 képnél ez percekben mérhető. A keresés viszont ismételhető művelet
(a felhasználó időnként újrafuttatja), és két futás között a képek túlnyomó
része változatlan. A cache kulcsa ezért a fájl AZONOSSÁGA: `(útvonal,
mtime_ns, méret)` — pontosan az a hármas, amivel a bélyegkép-cache is dolgozik
(`thumbs/cache.py`). Ha bármelyik eltér, a bejegyzés érvénytelen, és a hívó
újraszámol.

Miért kell a gyorskulcs-gyorstár (#1494): a kulcs képenként a fájl fej- és
farok-részéből ~33 KB beolvasás. Olcsóbb, mint egy dekódolás, de a duplikátum-
keresés (`dedup/exact.py`) és az importálás duplikátum-szűrője
(`importsource.duplicate_paths`) MINDEN azonos méretű jelöltre elvégezte,
MINDEN körben — két kör között semmi nem maradt meg.

A tábla tisztán származtatott gyorsítótár (ld. `schema.py` indoklása):
bármikor üríthető, az index többi része ettől érintetlen.

Előjel-kezelés: mindkét érték 64 bites ELŐJEL NÉLKÜLI, az SQLite INTEGER
viszont előjeles 64 bites. A 2^63 fölötti értékeket ezért kettes komplemensben
tároljuk, és olvasáskor visszaalakítjuk — enélkül az `sqlite3` a képek
nagyjából felénél OverflowError-t dobna.
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


#: A pár-oszlop (a most NEM írt érték) sorsa upsertnél: megmarad, ha a fájl
#: azonossága ugyanaz, egyébként NULL. A `CASE` a MEGLÉVŐ sorra hivatkozik
#: (`photo_hashes.…`), az `excluded.…` a most beírt értékekre — az SQLite az
#: `ON CONFLICT DO UPDATE` jobb oldalait mind a MÓDOSÍTÁS ELŐTTI soron
#: értékeli ki, tehát az értékadások sorrendje itt nem számít.
_PAROSZLOP_ERVENYTELENITES = (
    "CASE WHEN photo_hashes.mtime_ns = excluded.mtime_ns "
    "AND photo_hashes.size = excluded.size "
    "THEN photo_hashes.{oszlop} ELSE NULL END"
)


def _betolt(
    conn: sqlite3.Connection, keys: Sequence[HashKey], oszlop: str
) -> dict[HashKey, int]:
    """Egy érték-oszlop beolvasása a megadott fájl-azonosságokhoz.

    A visszaadott szótárban CSAK az érvényes (azonos mtime_ns és méret
    mellett tárolt), NEM NULL bejegyzések szerepelnek — a hiányzó kulcsokat
    a hívó számolja újra. A lekérdezés kötegelve fut, így tetszőleges méretű
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
            f"SELECT path, mtime_ns, size, {oszlop} AS ertek FROM photo_hashes "
            f"WHERE path IN ({placeholders})",
            batch,
        )
        for row in rows:
            key = (row["path"], row["mtime_ns"], row["size"])
            if key in wanted and row["ertek"] is not None:
                found[key] = _to_unsigned(row["ertek"])
    return found


def _ment(
    conn: sqlite3.Connection,
    items: Iterable[tuple[str, int, int, int]],
    oszlop: str,
    par_oszlop: str,
) -> None:
    """`(útvonal, mtime_ns, méret, érték)` négyesek eltárolása egy oszlopba.

    Upsert az útvonalra: a megváltozott fájl régi sora felülíródik (nem
    halmozódik), és a `par_oszlop` régi értéke ilyenkor NULL-ra vált — az
    már egy MÁSIK fájlra vonatkozna. A hívó dolga a commit."""
    payload = [
        (str(path), int(mtime_ns), int(size), _to_signed(int(value)))
        for path, mtime_ns, size, value in items
    ]
    if not payload:
        return
    conn.executemany(
        f"INSERT INTO photo_hashes(path, mtime_ns, size, {oszlop}) "
        "VALUES (?, ?, ?, ?) "
        "ON CONFLICT(path) DO UPDATE SET "
        "mtime_ns = excluded.mtime_ns, size = excluded.size, "
        f"{oszlop} = excluded.{oszlop}, "
        f"{par_oszlop} = {_PAROSZLOP_ERVENYTELENITES.format(oszlop=par_oszlop)}",
        payload,
    )


def load_dhashes(
    conn: sqlite3.Connection, keys: Sequence[HashKey]
) -> dict[HashKey, int]:
    """A megadott fájl-azonosságokhoz tárolt dHash-ek (#294)."""
    return _betolt(conn, keys, "dhash")


def save_dhashes(
    conn: sqlite3.Connection, items: Iterable[tuple[str, int, int, int]]
) -> None:
    """`(útvonal, mtime_ns, méret, dhash)` négyesek eltárolása (#294)."""
    _ment(conn, items, "dhash", "originfast")


def load_fast_keys(
    conn: sqlite3.Connection, keys: Sequence[HashKey]
) -> dict[HashKey, int]:
    """A megadott fájl-azonosságokhoz tárolt Picasa-gyorskulcsok (#1494).

    A migrációval érkezett (még ki nem töltött) sorok `originfast`-ja NULL
    — azok szótlanul kimaradnak, a hívó számol."""
    return _betolt(conn, keys, "originfast")


def save_fast_keys(
    conn: sqlite3.Connection, items: Iterable[tuple[str, int, int, int]]
) -> None:
    """`(útvonal, mtime_ns, méret, gyorskulcs)` négyesek eltárolása (#1494)."""
    _ment(conn, items, "originfast", "dhash")
