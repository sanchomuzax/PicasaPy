"""Az index-szinkron felelősségi része; a régi API a sync.py-n át él."""

from __future__ import annotations

import logging
import os
import sqlite3
from pathlib import Path


from .sync_compat import legacy

logger = logging.getLogger("picasapy.index.sync")


def _prune_folders(conn: sqlite3.Connection, root: Path, seen_paths: set[str]) -> None:
    """A gyökér alatti, de a mostani scanben nem látott mappák törlése.

    #143: a gyökér-szűrés SQL-oldalon fut (indexelhető LIKE-prefix), nem
    Pythonban az összes mappán iterálva. Explicit photos-törlés a folders
    előtt, hogy az FTS-triggerek biztosan lefussanak (az FK-cascade nem
    minden konfigurációban futtat triggert).

    #459/5: a nem látott mappa nem feltétlenül eltűnt mappa — lehet, hogy
    csak épp nem elérhető (levált NAS-mount). Az ilyen mappa a fotóival
    EGYÜTT bennmarad az indexben, `offline = 1` jelöléssel; a takarítás
    csak a bizonyítottan eltűnt mappákra fut. Ld. `folder_looks_offline`.
    """
    stale = [
        (row["id"], row["path"])
        for row in conn.execute(*_under_root_query("SELECT id, path", root))
        if row["path"] not in seen_paths
    ]
    for folder_id, path in stale:
        # Óvni csak azt érdemes, amiben van is mit veszíteni: fotó nélküli
        # sor eltávolítása nem jár adatvesztéssel, ott a takarítás mehet.
        if legacy("_has_photos")(conn, folder_id) and legacy("folder_looks_offline")(Path(path)):
            legacy("_set_folder_offline")(conn, folder_id, True)
            logger.warning("A mappa jelenleg nem elérhető, az indexben marad: %s", path)
            continue
        conn.execute("DELETE FROM photos WHERE folder_id = ?", (folder_id,))
        conn.execute("DELETE FROM folders WHERE id = ?", (folder_id,))
        conn.execute("DELETE FROM folder_scan_state WHERE path = ?", (path,))


def _under_root_query(select: str, root: Path) -> tuple[str, tuple[str, str]]:
    """SQL + paraméterek a gyökér alatti folders-sorokhoz (#143).

    A LIKE-minta escape-elt (%, _ és \\ a path-ban nem viselkedhet
    joker-ként), és elválasztóval zárt prefixet használ — a „/a/kep" gyökér
    nem foghatja meg a „/a/kepek" mappáit."""
    prefix = str(root).rstrip(os.sep) + os.sep
    escaped = prefix.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return (
        f"{select} FROM folders WHERE path = ? OR path LIKE ? ESCAPE '\\'",
        (str(root), escaped + "%"),
    )


def _is_under(path: Path, root: Path) -> bool:
    return path == root or path.is_relative_to(root)


def _has_indexed_folders(conn: sqlite3.Connection, root: Path) -> bool:
    """Van-e a gyökér alá eső mappa az indexben (a scan-eredménytől függetlenül)."""
    query, params = _under_root_query("SELECT 1", root)
    return conn.execute(f"{query} LIMIT 1", params).fetchone() is not None


# #141: fehérlista — csak ismert, biztonságos oszlopokra engedjük a célzott
# UPDATE-et (csillag/felirat/forgatás gyors-útja, teljes resync nélkül).
_TARGETED_UPDATE_COLUMNS = {
    "star",
    "hidden",
    "caption_ini",
    "caption_file",
    "keywords_ini",
    "keywords_file",
    "rotate_steps",
    # #2902/#2976: a tükrözés-jelző — a forgatás párja, ugyanígy célzottan
    # frissíthető. A #2976 óta ini-eredetű is: a mappa-resync a `flipped(N)`
    # kulcsból tölti, tehát az ini az igazságforrás, nem az index.
    "flip_flags",
    # #4332/#4693/#4885: a dátummódosítás a forrás EXIF-ét írja; ha ez nem
    # lehetséges (videó, nem-JPEG, hibás vagy írásvédett JPEG), a dátum ebbe a
    # mezőbe kerül.
    "taken_at_override",
}


def update_photo_fields(conn: sqlite3.Connection, photo_id: int, **fields) -> None:
    """Egy fotó indexsorának célzott, egy-soros UPDATE-je (#141).

    A csillag/felirat/forgatás gyors-útja: amikor az új érték már ismert (a
    hívó épp most írta az inibe/IPTC-be), nincs szükség a teljes mappa-
    resyncre (`sync_tree`/`sync_folder`) — egyetlen UPDATE elég, ami az
    FTS-triggert is csak az érintett sorra sütteti el."""
    if not fields:
        return
    unknown = set(fields) - _TARGETED_UPDATE_COLUMNS
    if unknown:
        raise ValueError(f"Nem célzott-frissíthető oszlop(ok): {sorted(unknown)}")
    columns = ", ".join(f"{name} = ?" for name in fields)
    conn.execute(
        f"UPDATE photos SET {columns} WHERE id = ?",
        (*fields.values(), photo_id),
    )
    conn.commit()


def remove_root(conn: sqlite3.Connection, root: str | Path) -> None:
    """Egy gyökér teljes eltávolítása az indexből (Mappakezelő:
    „Eltávolítás a Picasából"). Explicit photos-törlés a folders előtt,
    hogy az FTS-triggerek lefussanak."""
    root_path = Path(legacy("normalize_path")(root))
    legacy("_ensure_scan_state")(conn)
    legacy("_prune_folders")(conn, root_path, set())
    conn.commit()


def _resolved_protected_roots(roots: tuple[str | Path, ...]) -> tuple[Path, ...]:
    """A védett gyökerek FELOLDÁSA, kihagyva a pontosan egyező ismétlést
    (#1706).

    **Miért ez a lépés önmagában.** A `normalize_path` `Path.resolve()`-ot
    hív, ami minden útvonal-komponensre `stat`/`lstat` rendszerhívást
    jelent. MÉRVE (#1706, helyi lemezen, 21 gyökér): 20 nyilvántartott
    exportcél feloldása **83** ilyen hívást igényelt — kb. 4/gyökér —,
    miközben az utána következő SQL-összevetés (`_is_under`, tiszta Python)
    ugyanazon a gépen **mikroszekundumos**, akkor is, ha a `folders` tábla
    több száz sort tartalmaz. Hálózati megosztáson (a tulajdonos NAS-on
    tartja a könyvtárát) ez a rendszerhívásonkénti költség dominál — ez a
    #1706 mérésének fő eredménye.

    **Amit ez a függvény tesz.** A nyilvántartott exportcélok listája
    (`MAX_EXPORTED_FOLDERS = 20`) idővel PONTOSAN EGYEZŐ útvonalat is
    tartalmazhat (pl. két különböző munkamenetből ugyanarra a célra
    exportálva, mielőtt a `remember_exported_folder` dedupolt volna, vagy
    egy figyelt gyökér, ami véletlenül megegyezik egy korábbi exportcéllal)
    — az ilyen ismétlést a feloldás ELŐTT szűrjük ki, nyers
    szövegösszehasonlítással (nem érinti a lemezt). Ez BIZTOSAN biztonságos:
    ugyanaz a nyers string ugyanarra a feloldott útra vezet, tehát a
    kihagyás a végeredményt nem változtatja, csak a felesleges
    rendszerhívást takarítja meg.

    **Amit ez a függvény SZÁNDÉKOSAN NEM tesz.** Nem próbálja kitalálni
    (útvonal-előtag alapján, feloldás nélkül), hogy egy exportcél egy másik
    védett gyökér ALATT van-e — az ilyen heurisztika egy szimbolikus linkkel
    tévedhetne, és a #1667/#1560 védelme éppen az, hogy egy exportcél
    SOHA ne essen áldozatul a takarításnak. A fennmaradó, nagyobb nyereség
    (a feloldás cache-elése munkamenetek között) a #1859-ben készült el —
    ld. `_feloldas_gyorstarral`."""
    resolved: list[Path] = []
    latott: set[str] = set()
    for root in roots:
        nyers = str(root)
        if nyers in latott:
            continue
        latott.add(nyers)
        resolved.append(Path(legacy("normalize_path")(root)))
    return tuple(resolved)


def _azonossag(ut: str) -> tuple[int, int] | None:
    """Az útvonal fájlrendszer-AZONOSSÁGA (`dev`, `ino`), vagy `None`.

    `None` minden olyan esetben, amikor nem tudjuk megmondani: nem létezik,
    nem olvasható, lecsatolt hálózati megosztás. A hívó ilyenkor NEM
    gyorstáraz — a bizonytalanság sosem vezethet arra, hogy egy régi
    feloldást igaznak veszünk (#1859)."""
    try:
        adat = legacy("_stat")(ut)
    except OSError:
        return None
    return (_elojeles64(adat.st_dev), _elojeles64(adat.st_ino))


def _elojeles64(ertek: int) -> int:
    """Előjel nélküli 64 bites azonosító → az SQLite előjeles `INTEGER`-e (#3549).

    Windowson az `st_ino` a 64 bites ELŐJEL NÉLKÜLI fájlazonosító, és 2^63
    fölé is eshet; az SQLite ezt `OverflowError`-ral utasítja vissza. A
    leképezés bitre azonos (kettes komplemens), tehát kölcsönösen egyértelmű:
    az összevetés a tárolt és a friss érték között ugyanúgy igaz vagy hamis,
    mint a nyers értékek között.
    """
    ertek = int(ertek) & 0xFFFF_FFFF_FFFF_FFFF
    return ertek - (1 << 64) if ertek >= (1 << 63) else ertek


def _feloldas_gyorstarral(
    conn: sqlite3.Connection, roots: tuple[str | Path, ...]
) -> tuple[Path, ...]:
    """A védett gyökerek feloldása, MUNKAMENETEK KÖZÖTT megőrzött
    gyorstárral (#1859).

    **Miért kell.** A `Path.resolve()` minden útvonal-komponensre
    rendszerhívást tesz (mérve: gyökerenként 5, pontosan lineárisan), és ez
    minden induláskor újrafut ugyanazokra az útvonalakra. Helyi lemezen
    ingyen van; hálózati megosztáson minden hívás körülfordulás — a
    tulajdonos a könyvtárát NAS-on tartja, és a #1706 mérése szerint épp ez
    magyarázza a takarítás 125 → 969 ms-os romlását.

    **Miért nem elég egy egyszerű szótár.** A feloldás eredménye KÍVÜLRŐL
    változhat: átirányított szimbolikus link, le-/felcsatolt NAS,
    átnevezett vagy megszűnt exportcél. Egy elavult bejegyzés a #1667/#1560
    védelmét lyukasztaná ki — egy védett mappa „idegennek" minősülne, és a
    takarítás TÖRÖLNÉ az indexből.

    **Ezért a bejegyzés MINDKÉT végét azonosítjuk.** A nyers útvonalét és a
    feloldottét is (`dev`/`ino`). A gyorstárazott feloldást csak akkor
    fogadjuk el, ha
      * a nyers útvonal ma is ugyanarra az objektumra mutat, ÉS
      * a feloldott útvonal ma is ugyanaz az objektum, ÉS
      * a kettő UGYANAZ az objektum.
    Ez két `stat` hívás gyökerenként az öt helyett; bármelyik feltétel
    sérülésekor (vagy bármilyen hibánál) a feloldás teljesen újrafut, és a
    bejegyzés frissül. Az eredmény tehát SOHA nem lehet más, mint
    gyorstár nélkül — csak gyorsabban áll elő.
    """
    try:
        conn.execute("SELECT 1 FROM resolved_root_cache LIMIT 1")
    except sqlite3.Error:
        # A tábla hiánya (régi index, félbemaradt migráció) NEM hiba: a
        # gyorstár származtatott adat, nélküle a régi út működik.
        return _resolved_protected_roots(roots)

    tarolt: dict[str, sqlite3.Row] = {
        sor["raw"]: sor
        for sor in conn.execute(
            "SELECT raw, resolved, raw_dev, raw_ino, resolved_dev, resolved_ino"
            " FROM resolved_root_cache"
        )
    }

    eredmeny: list[Path] = []
    latott: set[str] = set()
    frissitendo: list[tuple] = []
    for root in roots:
        nyers = str(root)
        if nyers in latott:
            continue
        latott.add(nyers)

        sor = tarolt.get(nyers)
        talalat = None
        if sor is not None:
            nyers_id = _azonossag(nyers)
            if nyers_id is not None and nyers_id == (sor["raw_dev"], sor["raw_ino"]):
                feloldott_id = _azonossag(sor["resolved"])
                if feloldott_id is not None and feloldott_id == nyers_id:
                    talalat = str(sor["resolved"])
        if talalat is not None:
            eredmeny.append(Path(talalat))
            continue

        feloldott = legacy("normalize_path")(root)
        eredmeny.append(Path(feloldott))
        azonossag = _azonossag(nyers)
        feloldott_azonossag = _azonossag(feloldott)
        # Csak azt tesszük el, aminek MINDKÉT vége azonosítható — egy
        # nem létező vagy elérhetetlen útvonalra a gyorstár nem tudna
        # érvényességet állítani.
        if azonossag is not None and feloldott_azonossag is not None:
            frissitendo.append(
                (
                    nyers,
                    feloldott,
                    azonossag[0],
                    azonossag[1],
                    feloldott_azonossag[0],
                    feloldott_azonossag[1],
                )
            )

    if frissitendo:
        conn.executemany(
            "INSERT INTO resolved_root_cache"
            " (raw, resolved, raw_dev, raw_ino, resolved_dev, resolved_ino)"
            " VALUES (?, ?, ?, ?, ?, ?)"
            " ON CONFLICT(raw) DO UPDATE SET"
            "  resolved = excluded.resolved,"
            "  raw_dev = excluded.raw_dev, raw_ino = excluded.raw_ino,"
            "  resolved_dev = excluded.resolved_dev,"
            "  resolved_ino = excluded.resolved_ino",
            frissitendo,
        )
        conn.commit()
    return tuple(eredmeny)


def prune_foreign_folders(conn: sqlite3.Connection, roots: tuple[str | Path, ...]) -> None:
    """A figyelt gyökerek egyikéhez sem tartozó mappák törlése az indexből.

    Induláskor fut (#58): a korábbi futásokból ottragadt gyökerek (pl. régi
    parancssori argumentum) mappái ne jelenjenek meg a bal hasábban. Üres
    gyökérlistával nem csinál semmit — védekezés, nehogy egy hiányzó
    WatchedFolders.txt csendben kiürítse az egész indexet. Explicit
    photos-törlés a folders előtt, hogy az FTS-triggerek lefussanak.

    A gyökerek feloldása (`_resolved_protected_roots`, #1706) kihagyja a
    pontosan egyező ismétlést — ld. ott a mérést és az indoklást."""
    if not roots:
        return
    legacy("_ensure_scan_state")(conn)
    root_paths = _feloldas_gyorstarral(conn, roots)
    stale = [
        (row["id"], row["path"])
        for row in conn.execute("SELECT id, path FROM folders")
        if not any(_is_under(Path(row["path"]), root) for root in root_paths)
    ]
    for folder_id, path in stale:
        conn.execute("DELETE FROM photos WHERE folder_id = ?", (folder_id,))
        conn.execute("DELETE FROM folders WHERE id = ?", (folder_id,))
        conn.execute("DELETE FROM folder_scan_state WHERE path = ?", (path,))
    conn.commit()
