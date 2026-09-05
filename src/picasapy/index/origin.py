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
from collections.abc import Iterable
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


_DDL = """CREATE TABLE IF NOT EXISTS origin_keys (
    path TEXT PRIMARY KEY,
    origin_key INTEGER NOT NULL,
    anchor_size INTEGER,
    anchor_mtime_ns INTEGER
);
"""

#: A HORGONY (#2099): melyik fájlra vonatkozik az öröklés. Mindkét oszlop
#: felvehet NULL-t, mert az öröklés a fájl kiírása ELŐTT is beírható (ld. a
#: modul fejlécét) — ilyenkor az első szinkron horgonyoz le, amikor a fájlt
#: először látja. Utána minden szinkron összeveti: ha a méret VAGY az mtime
#: eltér, a fájl kicserélődött, és az öröklés törlődik.
#:
#: ⚠️ „vagy", nem „és": a lecserélt fájl mérete véletlenül egyezhet. A
#: szigorúbb feltétel itt biztonságos, mert a PicasaPy NEM destruktív — a
#: szerkesztéseket a `.picasa.ini` tartja, a képfájlhoz nem nyúlunk, tehát
#: normál használatban az mtime nem változik.
_HORGONY_OSZLOPOK = ("anchor_size", "anchor_mtime_ns")


def _horgonyoszlopokat_potol(conn: sqlite3.Connection) -> None:
    """A #2099 előtti indexek táblája még kétoszlopos — pótoljuk.

    A `CREATE TABLE IF NOT EXISTS` egy MEGLÉVŐ táblát nem bővít, tehát a
    régi index némán a régi sémával futna tovább, és a csere-felismerés
    csendben hatástalan lenne.
    """
    meglevo = {
        sor[1] for sor in conn.execute("PRAGMA table_info(origin_keys)")
    }
    for oszlop in _HORGONY_OSZLOPOK:
        if oszlop not in meglevo:
            conn.execute(f"ALTER TABLE origin_keys ADD COLUMN {oszlop} INTEGER")


def ensure_origin_table(conn: sqlite3.Connection) -> None:
    """Az `origin_keys` tábla létrehozása, ha még nincs.

    Hívható bármikor és többször: a `CREATE TABLE IF NOT EXISTS` miatt
    idempotens, és egy régebbi sémájú indexen is működik — a #2099 horgony-
    oszlopait `ALTER TABLE`-lel pótolja.

    ⚠️ **`execute`, nem `executescript`.** Az `executescript` a futtatás előtt
    IMPLICIT COMMITOT csinál — a szinkron közben hívva ezzel véglegesítené a
    félbehagyott mappát, és a megszakítás visszagörgetése elveszne (#2038;
    a `tests/index/test_sync_cancel.py` őre ezt fogta meg).
    """
    conn.execute(_DDL)
    _horgonyoszlopokat_potol(conn)


def _kulcs(path: str | Path) -> str:
    """A tábla kulcsa: abszolút, feloldott útvonal szövegként.

    A feloldás azért kell, hogy a relatív és az abszolút alak ugyanarra a
    sorra mutasson. Nem létező fájlra a `resolve()` `strict=False`
    módban dolgozik — az öröklést be lehet írni azelőtt is, hogy a fájl a
    lemezre kerülne.
    """
    return str(Path(path).resolve())


def _horgony(path: str | Path) -> tuple[int | None, int | None]:
    """A fájl mai horgonya: (méret, mtime_ns), vagy (None, None).

    A hiányzó fájl nem hiba: az öröklés a kiírás előtt is beírható, és a
    szinkron a fájl eltűnését amúgy is külön kezeli.
    """
    try:
        adat = Path(path).stat()
    except OSError:
        return (None, None)
    return (adat.st_size, adat.st_mtime_ns)


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

    A horgonyt (#2099) MINDJÁRT rögzíti, ha a fájl a hívás pillanatában már
    a lemezen van — ezzel a legszűkebbre húzza azt az ablakot, amelyben egy
    csere észrevétlen maradhat. Ha a fájl még nincs kiírva, a horgony NULL
    marad, és a szinkron horgonyoz le.
    """
    ensure_origin_table(conn)
    meret, mtime_ns = _horgony(target)
    conn.execute(
        "INSERT INTO origin_keys(path, origin_key, anchor_size, "
        "anchor_mtime_ns) VALUES (?, ?, ?, ?) "
        "ON CONFLICT(path) DO UPDATE SET "
        "origin_key = excluded.origin_key, "
        "anchor_size = excluded.anchor_size, "
        "anchor_mtime_ns = excluded.anchor_mtime_ns",
        (_kulcs(target), _elojelesre(int(key)), meret, mtime_ns),
    )


def forget_origin_key(conn: sqlite3.Connection, path: str | Path) -> None:
    """Az öröklés törlése — a fájl megint a saját kulcsát kapja.

    A törölt vagy átnevezett fájl sorát ezzel kell kivenni; enélkül egy
    később ugyanoda kerülő, teljesen más fájl örökölné meg az idegen
    származást.
    """
    ensure_origin_table(conn)
    conn.execute("DELETE FROM origin_keys WHERE path = ?", (_kulcs(path),))


def _sorok(conn: sqlite3.Connection) -> list[tuple[str, int | None, int | None]]:
    """A tábla ÖSSZES sora: (útvonal, horgony-méret, horgony-mtime).

    A szűrés szándékosan Pythonban történik, nem SQL `LIKE`-kal: az
    útvonalban előforduló `%` és `_` a `LIKE` joker-karakterei, tehát egy
    „100%_nyar" nevű mappa takarítása IDEGEN sorokat is elvinne. Az
    `origin_keys` csak a „Másolat mentése" kimeneteit tartalmazza — pár
    száz sor nagyságrend —, ezért a teljes olvasás ára elhanyagolható.
    """
    ensure_origin_table(conn)
    return list(
        conn.execute(
            "SELECT path, anchor_size, anchor_mtime_ns FROM origin_keys"
        )
    )


def forget_origin_keys_outside(
    conn: sqlite3.Connection, folder: str | Path, kept_names: Iterable[str]
) -> None:
    """A `folder` KÖZVETLEN gyerekei közül kiveszi azokat, amik eltűntek.

    Ezt hívja a mappa-szinkron: `kept_names` a mappában MOST látott fájlok
    neve. Ami a táblában szerepel, de a listában nem, az eltűnt — kukába
    került, átnevezték, vagy a felhasználó törölte a fájlkezelőből.

    Az almappák sorait NEM bántja: azokat a saját mappájuk szinkronja
    kezeli, és egy előtag-alapú törlés némán elvinné őket.

    ⚠️ A törlés feltétele KETTŐS: a név hiányozzon a listából **és** a fájl
    tényleg ne legyen a lemezen. Az `origin_keys` ugyanis — a
    `photo_hashes`-szel ellentétben — **nem újraszámolható** adat (ld. a
    modul fejlécét): ha egy scan átmeneti hiba miatt üres listát adna, a
    puszta névlista alapján visszavonhatatlanul elveszne az öröklés.

    A CSERÉT is ez a lépés veszi észre (#2099): a HORGONY (méret + mtime)
    mondja meg, melyik fájlra szólt az öröklés. Ha a helyben maradt névhez
    ma más méretű vagy más mtime-ú fájl tartozik, akkor a régi eltűnt és új
    került a helyére — az öröklés tehát törlendő, különben az új kép idegen
    származást viselne. A még lehorgonyzatlan (NULL) sorokat ez a lépés
    horgonyozza le.

    ⚠️ **Megmaradó rés, kimondva:** ha a csere még az ELSŐ lehorgonyzás
    előtt történik (öröklés → csere → első szinkron), a horgony a
    betolakodóra áll rá. Ez nem szüntethető meg, amíg az öröklés a kiírás
    előtt is beírható; a rés a „két szinkron közti bármikor"-ról a legelső
    szinkron előtti pillanatra szűkült.

    Args:
        conn: nyitott index-kapcsolat (a commit a hívóé).
        folder: a most szinkronizált mappa.
        kept_names: a mappában látott fájlnevek.
    """
    mappa = Path(folder).resolve()
    maradok = set(kept_names)
    torlendo: list[str] = []
    horgonyozando: list[tuple[int, int, str]] = []
    for ut, horgony_meret, horgony_mtime in _sorok(conn):
        eleres = Path(ut)
        if eleres.parent != mappa:
            continue          # az almappák sorai a saját szinkronjukéi
        mai_meret, mai_mtime = _horgony(eleres)
        if eleres.name not in maradok and mai_meret is None:
            torlendo.append(ut)          # #2038: eltűnt és nincs a lemezen
        elif mai_meret is None:
            continue          # átmenetileg olvashatatlan — nem következtetünk
        elif horgony_meret is None or horgony_mtime is None:
            horgonyozando.append((mai_meret, mai_mtime, ut))
        elif (mai_meret, mai_mtime) != (horgony_meret, horgony_mtime):
            torlendo.append(ut)          # #2099: kicserélt fájl
    if horgonyozando:
        conn.executemany(
            "UPDATE origin_keys SET anchor_size = ?, anchor_mtime_ns = ? "
            "WHERE path = ?",
            horgonyozando,
        )
    if torlendo:
        conn.executemany(
            "DELETE FROM origin_keys WHERE path = ?", [(ut,) for ut in torlendo]
        )


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
