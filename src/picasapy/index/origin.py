"""A SZÁRMAZÁS-kulcs öröklése (`originfast`) — #1648.

⚠️ **Ez a mező származást azonosít, nem tartalmat.** A neve az eredetiben is
„origin", nem „content". A kulcs KÉPLETE a fájl saját bájtjaiból számol
(`dedup/fastkey.py`), de a „Másolat mentése" kimenete a **forrás** értékét
ÖRÖKLI — akkor is, ha a szerkesztés bele van égetve, és a bájtok 99,9%-ban
eltérnek. Ez köti a másolatot a forrásához.

## A bizonyíték

A tulajdonos élő Picasa-adatbázisa (`research/testdata/1557-masolat-mentese/`,
egy mappa: 1 eredeti + 3 „Másolat mentése" kimenet). A négy 1600×1200-as
rekord — a méret-oszlop alapján pontosan a mi négy fájlunk — **mind ugyanazt**
az `originfast` értéket viseli (`0x08637e41c12b8eaa`), és ez az érték a
FORRÁS saját bájtjaiból jön ki a mi képletünkkel. A másolatok bájtjai
viszont eltérnek (144 796 / 228 288 / 227 898 bájt), tehát saját tartalomból
három KÜLÖNBÖZŐ érték jönne ki. Egyetlen közös érték csak átvétellel
lehetséges. Levezetés: `docs/specs/picasa-tartalomkulcs.md`.

## Miért ÖNÁLLÓ tábla, és miért nem a `photos` oszlopa

A „Másolat mentése" **előbb** írja ki a fájlt, mint ahogy a szinkron
felveszi az index `photos` táblájába — a sorrend a háttérszálak dolga, nem
garantált. Egy `photos`-oszlop írása ezért versenyhelyzetbe kerülne a
saját szinkronunkkal: vagy elveszne az érték (még nincs sor), vagy a
szinkron írná felül. Az útvonalra kulcsolt önálló tábla ettől független:
**bármikor írható**, és a sor akkor is megvan, amikor a fotó-rekord még
nem — ugyanaz a megfontolás, mint a `photo_hashes`-nél és a
`photo_colors`-nál.

⚠️ A `photo_hashes`-szel és a `photo_colors`-szal ellentétben ez az adat
**NEM származtatott**: ha elveszik, a fájlból nem számolható újra, mert épp
azt tartja nyilván, amit a fájl tartalma NEM árul el. A tábla ezért soha
nem dobható el gyorsítótárként — a `compact`/karbantartó lépések hagyják
békén.

## Mi NEM változik ettől

A `dedup/` továbbra is a **számolt** kulcsot használja előszűrőnek: ott a
kérdés a tartalmi azonosság, nem a származás. Egy másolat NEM másodpéldánya
a forrásának, tehát az öröklött érték ott félrevinne. A két fogalom
szétválasztása szándékos — az eredeti Picasa keverte őket.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

from picasapy.dedup.fastkey import picasa_fast_key

#: A kulcs ELŐJEL NÉLKÜLI 64 bites (`<Q`), az SQLite INTEGER viszont
#: előjeles 64 bites — a felső fele nem férne bele. A `photo_hashes`
#: dHash-oszlopa ugyanezt oldja meg ugyanígy (`index/hashes.py`): a
#: tárolás előjeles kettes komplemensben megy, az olvasás visszaalakít.
#: Az érintett tartomány NEM elméleti: a mért `0x8...`-nál nagyobb kulcsok
#: (pl. a #1648 mérésében szereplő rekordok fele) mind ide esnek.
_UNSIGNED_LIMIT = 1 << 64
_SIGNED_LIMIT = 1 << 63


def _elojelesre(ertek: int) -> int:
    """Előjel nélküli 64 bites kulcs → az SQLite-nak adható előjeles érték."""
    return ertek - _UNSIGNED_LIMIT if ertek >= _SIGNED_LIMIT else ertek


def _elojel_nelkulire(ertek: int) -> int:
    """Az SQLite-ból olvasott előjeles érték → előjel nélküli 64 bites kulcs."""
    return ertek + _UNSIGNED_LIMIT if ertek < 0 else ertek


_DDL = """
CREATE TABLE IF NOT EXISTS origin_keys (
    path TEXT PRIMARY KEY,
    origin_key INTEGER NOT NULL
);
"""


def ensure_origin_table(conn: sqlite3.Connection) -> None:
    """Az `origin_keys` tábla létrehozása, ha még nincs.

    Hívható bármikor és többször: a `CREATE TABLE IF NOT EXISTS` miatt
    idempotens, és egy régebbi sémájú indexen is működik migráció nélkül.
    """
    conn.executescript(_DDL)


def _kulcs(path: str | Path) -> str:
    """A tábla kulcsa: abszolút, feloldott útvonal szövegként.

    A feloldás azért kell, hogy a relatív és az abszolút alak ugyanarra a
    sorra mutasson. Nem létező fájlra a `resolve()` `strict=False`
    módban dolgozik — az öröklést be lehet írni azelőtt is, hogy a fájl a
    lemezre kerülne.
    """
    return str(Path(path).resolve())


def inherit_origin_key(
    conn: sqlite3.Connection, target: str | Path, key: int
) -> None:
    """A `target` MOSTANTÓL a megadott származás-kulcsot viseli.

    Args:
        conn: nyitott index-kapcsolat (a commit a hívóé).
        target: a keletkezett másolat útja.
        key: a FORRÁS `picasa_fast_key` értéke — nem a másolaté.

    Ugyanarra az útra ismételve felülír: egy útvonalon egyszerre csak egy
    fájl él, és ha oda ÚJ másolat készül, annak új forrása lehet.
    """
    ensure_origin_table(conn)
    conn.execute(
        "INSERT INTO origin_keys(path, origin_key) VALUES (?, ?) "
        "ON CONFLICT(path) DO UPDATE SET origin_key = excluded.origin_key",
        (_kulcs(target), _elojelesre(int(key))),
    )


def forget_origin_key(conn: sqlite3.Connection, path: str | Path) -> None:
    """Az öröklés törlése — a fájl megint a saját kulcsát kapja.

    A törölt vagy átnevezett fájl sorát ezzel kell kivenni; enélkül egy
    később ugyanoda kerülő, teljesen más fájl örökölné meg az idegen
    származást.
    """
    ensure_origin_table(conn)
    conn.execute("DELETE FROM origin_keys WHERE path = ?", (_kulcs(path),))


def origin_key(conn: sqlite3.Connection, path: str | Path) -> int | None:
    """A fájl származás-kulcsa: az ÖRÖKÖLT érték, vagy a sajátja.

    Returns:
        Az örökölt kulcs, ha van ilyen bejegyzés — ilyenkor a fájlhoz hozzá
        sem nyúlunk. Egyébként a fájl saját bájtjaiból számolt
        `picasa_fast_key`, illetve `None`, ha a fájl nem olvasható.
    """
    ensure_origin_table(conn)
    sor = conn.execute(
        "SELECT origin_key FROM origin_keys WHERE path = ?", (_kulcs(path),)
    ).fetchone()
    if sor is not None:
        return _elojel_nelkulire(int(sor[0]))
    return picasa_fast_key(path)
