"""Történelmi mappa-duplikátumok összevonása (#507).

## Miért kell ez KÜLÖN a normalizálástól

A `picasapy.paths.normalize_path`/`path_key` bevezetése (ld.
`app/library_controller.py`, `index/sync.py`) a JÖVŐBENI duplikációt
előzi meg — a felhasználó gépén viszont a hiba MÁR bekövetkezett: a
`folders` táblában két sor élhet ugyanahhoz a valódi mappához (pl. egy
`..`-szegmenses vagy szimbolikus linken át hozzáadott gyökér miatt). A
séma önmagában ezt nem javítja — ehhez ez a modul fut, egyszer, induláskor
(`LibraryMixin.start`), az `folders.path` oszlopot `path_key`-vel
csoportosítva.

## Adatvesztés-mentesség

Csoportonként egy „megtartott" sor marad; a többi „vesztes" sor fotóit
áthelyezzük (nem töröljük!) a megtartottba:

- ha a vesztesben van egy fájlnév, ami a megtartottban NINCS: egyszerű
  áthelyezés (`folder_id` átírása) — nincs adatvesztés;
- ha ÜTKÖZIK (mindkét oldalon van azonos nevű fotó, ami majdnem mindig
  így van, hiszen a két sor UGYANAZT a valódi könyvtárat tükrözi): a
  „precíz" mezőket (csillag, feliratok, kulcsszavak, szűrők, geocímke)
  összefésüljük — ha egyik oldal üres/alapérték, a másik nem-üres értéke
  győz; ha MINDKÉT oldal nem-üres ÉS ELTÉR (valódi szerkesztés-ütközés,
  amit nem lehet automatikusan eldönteni), a teljes CSOPORT összevonását
  KIHAGYJUK — inkább marad a duplikátum, mint hogy bármelyik oldal adata
  elvesszen (felhasználói utasítás).
- az albumtagságot (`photo_albums`) és az album-definíciókat (`albums`)
  a törlés ELŐTT áthelyezzük a megtartott sorba/fotóba, hogy a
  CASCADE-törlés ne vigye el őket.

A `face` (saját arc-detektálás) és a `photo_hashes`/`photo_colors`
(fájl-útvonal-kulcsú gyorsítótárak) NEM kerülnek át — ezek dokumentáltan
tisztán származtatott, bármikor újraszámolható adatok (ld. a saját
docstringjeiket), a merge utáni első szinkron/keresés pótolja őket.
"""

from __future__ import annotations

import logging
import sqlite3
from dataclasses import dataclass

from picasapy.index.folder_spelling import rows_under
from picasapy.paths import flat_key, path_key

logger = logging.getLogger(__name__)

# Az áthelyezés ELŐTT vizsgált mezők egy ÜTKÖZŐ (azonos nevű) fotópárnál.
# Ha valamelyik mindkét oldalon nem-üres ÉS eltér, a teljes mappa-csoport
# összevonása kimarad (biztonságos, adatvesztés-mentes döntés).
_CONFLICT_FIELDS = ("star", "caption_ini", "keywords_ini", "filters", "geotag_ini")

# A megtartott fotó soron ezekre a mezőkre alkalmazzuk a „nem-üres győz"
# összefésülést, ha a vesztes oldal ad nem-üres/nem-alapértelmezett értéket
# és a megtartott oldal üres/alapértelmezett.
_MERGE_FIELDS = (
    "star",
    "hidden",
    "caption_ini",
    "keywords_ini",
    "rotate_steps",
    "filters",
    "taken_at",
    "orientation",
    "width",
    "height",
    "caption_file",
    "keywords_file",
    "geotag_ini",
    "exif_lat",
    "exif_lon",
)


@dataclass(frozen=True)
class FolderMergeReport:
    """`merged`: az összevonás után megmaradt kanonikus mappa-útvonalak.
    `skipped`: (kanonikus kulcs, indoklás) — biztonságosan NEM
    összevonható csoportok, duplikátumként meghagyva."""

    merged: tuple[str, ...] = ()
    skipped: tuple[tuple[str, str], ...] = ()


def _is_empty(value) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return value.strip() == ""
    if isinstance(value, int):
        return value == 0
    return False


def _conflicting_pair(keeper_photo: sqlite3.Row, loser_photo: sqlite3.Row) -> bool:
    for field in _CONFLICT_FIELDS:
        keeper_value, loser_value = keeper_photo[field], loser_photo[field]
        if keeper_value == loser_value:
            continue
        if not _is_empty(keeper_value) and not _is_empty(loser_value):
            return True
    return False


def _group_has_conflict(
    conn: sqlite3.Connection, keeper_id: int, loser_ids: list[int]
) -> bool:
    keeper_photos = {
        row["name"]: row
        for row in conn.execute(
            "SELECT * FROM photos WHERE folder_id = ?", (keeper_id,)
        )
    }
    for loser_id in loser_ids:
        for row in conn.execute(
            "SELECT * FROM photos WHERE folder_id = ?", (loser_id,)
        ):
            keeper_row = keeper_photos.get(row["name"])
            if keeper_row is not None and _conflicting_pair(keeper_row, row):
                return True
    return False


def _merge_photo_into(
    conn: sqlite3.Connection, keeper_photo_id: int, loser_photo: sqlite3.Row
) -> None:
    """Az ÜTKÖZŐ (azonos nevű) `loser_photo` mezőit — ahol a megtartott
    fotó üres/alapértelmezett — átveszi a megtartottba, majd az
    albumtagságát áthelyezi és a vesztes fotósort törli."""
    keeper = conn.execute(
        "SELECT * FROM photos WHERE id = ?", (keeper_photo_id,)
    ).fetchone()
    updates: dict[str, object] = {}
    for field in _MERGE_FIELDS:
        if _is_empty(keeper[field]) and not _is_empty(loser_photo[field]):
            updates[field] = loser_photo[field]
    if updates:
        set_clause = ", ".join(f"{field} = ?" for field in updates)
        conn.execute(
            f"UPDATE photos SET {set_clause} WHERE id = ?",
            (*updates.values(), keeper_photo_id),
        )
    # Album-tagság áthelyezése a CASCADE-törlés elé (#9) — az azonos
    # (photo_id, token) párt az INSERT OR IGNORE csendben kihagyja.
    conn.execute(
        "INSERT OR IGNORE INTO photo_albums(photo_id, token, place) "
        "SELECT ?, token, place FROM photo_albums WHERE photo_id = ?",
        (keeper_photo_id, loser_photo["id"]),
    )
    _move_photo_bound_rows(conn, keeper_photo_id, loser_photo["id"])
    conn.execute("DELETE FROM photos WHERE id = ?", (loser_photo["id"],))


def _move_photo_bound_rows(
    conn: sqlite3.Connection, keeper_photo_id: int, loser_photo_id: int
) -> None:
    """A vesztes fotóhoz kötött, az indexben KELETKEZETT adat (#7045) átvitele
    a törlés (és vele a CASCADE) előtt.

    A névvel ellátott arc és a felismerés nyoma nem származtatható újra az
    `.picasa.ini`-ből: ha a duplikátum másik sorában keletkezett, az
    összevonás nem viheti el. A megmaradó fotó SAJÁT arcai elsőbbséget
    élveznek (nincs kettőzés), a személy albumindexképe követi a fotót."""
    if conn.execute(
        "SELECT 1 FROM face WHERE photo_id = ? LIMIT 1", (keeper_photo_id,)
    ).fetchone() is None:
        conn.execute(
            "UPDATE face SET photo_id = ? WHERE photo_id = ?",
            (keeper_photo_id, loser_photo_id),
        )
    conn.execute(
        "INSERT OR IGNORE INTO face_scan(photo_id, mtime_ns, size, ok) "
        "SELECT ?, mtime_ns, size, ok FROM face_scan WHERE photo_id = ?",
        (keeper_photo_id, loser_photo_id),
    )
    conn.execute(
        "UPDATE person_thumbnails SET photo_id = ? WHERE photo_id = ?",
        (keeper_photo_id, loser_photo_id),
    )


def _merge_loser_into_keeper(
    conn: sqlite3.Connection, keeper_id: int, loser_id: int
) -> None:
    keeper_photos_by_name = {
        row["name"]: row["id"]
        for row in conn.execute(
            "SELECT id, name FROM photos WHERE folder_id = ?", (keeper_id,)
        )
    }
    for loser_photo in conn.execute(
        "SELECT * FROM photos WHERE folder_id = ?", (loser_id,)
    ).fetchall():
        keeper_photo_id = keeper_photos_by_name.get(loser_photo["name"])
        if keeper_photo_id is None:
            # nincs ütközés — egyszerű áthelyezés, nincs adatvesztés
            conn.execute(
                "UPDATE photos SET folder_id = ? WHERE id = ?",
                (keeper_id, loser_photo["id"]),
            )
        else:
            _merge_photo_into(conn, keeper_photo_id, loser_photo)
    # Album-DEFINÍCIÓK (nem a tagság) áthelyezése — azonos tokent az
    # INSERT OR IGNORE csendben kihagyja (a két sor úgyis ugyanabból a
    # valódi .picasa.ini-ből származik, tartalmuk azonos kell legyen).
    conn.execute(
        "INSERT OR IGNORE INTO albums(folder_id, token, name, date, "
        "description, location) "
        "SELECT ?, token, name, date, description, location "
        "FROM albums WHERE folder_id = ?",
        (keeper_id, loser_id),
    )
    loser_path = conn.execute(
        "SELECT path FROM folders WHERE id = ?", (loser_id,)
    ).fetchone()["path"]
    keeper_path = conn.execute(
        "SELECT path FROM folders WHERE id = ?", (keeper_id,)
    ).fetchone()["path"]
    # #7045: a fotó nélküli, helyi album a mappa ÚTVONALÁRA van kulcsolva
    # (nincs `folders` kapcsolata), és csak itt él: a megmaradó sor útvonalára
    # kerül, különben az egyesítés után árván maradna
    conn.execute(
        "UPDATE local_empty_albums SET folder_path = ? WHERE folder_path = ?",
        (keeper_path, loser_path),
    )
    conn.execute("DELETE FROM folder_scan_state WHERE path = ?", (loser_path,))
    conn.execute(
        "UPDATE folders SET has_ini = MAX(has_ini, (SELECT has_ini FROM "
        "folders WHERE id = ?)) WHERE id = ?",
        (loser_id, keeper_id),
    )
    # #4597: a rejtés (0/1/2) nem veszhet el összevonáskor — privát tartalom
    conn.execute(
        "UPDATE folders SET hidden = MAX(hidden, (SELECT hidden FROM "
        "folders WHERE id = ?)) WHERE id = ?",
        (loser_id, keeper_id),
    )
    conn.execute("DELETE FROM folders WHERE id = ?", (loser_id,))


def merge_duplicate_folders(conn: sqlite3.Connection) -> FolderMergeReport:
    """Egyszeri, adatvesztés-mentes takarítás: a `folders` táblában
    `path_key`-re nézve azonos (tehát ugyanahhoz a valódi mappához
    tartozó) sorok összevonása. Idempotens — duplikátum hiányában
    nincs teendő, üres jelentést ad."""
    return _merge_rows(conn, conn.execute("SELECT id, path, has_ini FROM folders").fetchall())


def merge_duplicate_folders_under(conn: sqlite3.Connection, root: str) -> FolderMergeReport:
    """Ugyanaz, mint `merge_duplicate_folders`, de csak a (hálózati) `root`
    alatti sorokra (#7045): a szinkron a bejárás ELŐTT egyesíti a gyökér
    kis-nagybetűs duplikátumait, hogy a bejárás ismert alakon írjon."""
    return _merge_rows(conn, rows_under(conn, root))


def _case_only_group(group_rows: list[sqlite3.Row]) -> bool:
    """Csak a kis-nagybetűben (és az elválasztóban) eltérő sorok csoportja.
    POSIX-on a `flat_key` identitás, ott ilyen csoport nem létezik."""
    return len({flat_key(row["path"]) for row in group_rows}) == 1


def _merge_rows(conn: sqlite3.Connection, rows: list[sqlite3.Row]) -> FolderMergeReport:
    if conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='folder_scan_state'"
    ).fetchone() is None:
        conn.execute(
            "CREATE TABLE IF NOT EXISTS folder_scan_state ("
            "path TEXT PRIMARY KEY, mtime_ns INTEGER NOT NULL, "
            "ini_mtime_ns INTEGER)"
        )
    groups: dict[str, list[sqlite3.Row]] = {}
    for row in rows:
        groups.setdefault(path_key(row["path"]), []).append(row)

    merged: list[str] = []
    skipped: list[tuple[str, str]] = []
    for key, group_rows in groups.items():
        if len(group_rows) < 2:
            continue
        if _case_only_group(group_rows):
            # #7045: a csak kis-nagybetűben eltérő sorok közül az ELSŐ
            # (legrégebbi) marad, hogy a tárolt és megjelenített alak az
            # eredeti legyen, és a szinkron (amely az indexben látott alakon
            # ír) ne hozzon létre újra másikat
            keeper = min(group_rows, key=lambda r: r["id"])
        else:
            # a megtartott: a legtöbb fotót tartalmazó sor (a leggazdagabb
            # adat), egyenlőségnél a legkisebb id (a legrégebbi, legstabilabb)
            counts = {
                row["id"]: conn.execute(
                    "SELECT COUNT(*) AS n FROM photos WHERE folder_id = ?",
                    (row["id"],),
                ).fetchone()["n"]
                for row in group_rows
            }
            keeper = max(group_rows, key=lambda r: (counts[r["id"]], -r["id"]))
        loser_ids = [r["id"] for r in group_rows if r["id"] != keeper["id"]]
        if _group_has_conflict(conn, keeper["id"], loser_ids):
            skipped.append(
                (
                    key,
                    "ütköző (mindkét oldalon eltérő, nem-üres) fotó-mező — "
                    "kihagyva, hogy ne vesszen adat",
                )
            )
            logger.warning(
                "#507: mappa-duplikátum ütköző szerkesztéssel, összevonás "
                "kihagyva: %s (%d sor)",
                key,
                len(group_rows),
            )
            continue
        for loser_id in loser_ids:
            _merge_loser_into_keeper(conn, keeper["id"], loser_id)
        canonical = path_key(keeper["path"])
        merged.append(canonical)
        logger.info(
            "#507: %d mappa-duplikátum sor összevonva: %s", len(group_rows), canonical
        )
    if merged or skipped:
        conn.commit()
    return FolderMergeReport(merged=tuple(merged), skipped=tuple(skipped))
