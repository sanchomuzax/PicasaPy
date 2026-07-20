"""Olvasó lekérdezések: mappa-lista, csillagozottak, FTS5 keresés."""

from __future__ import annotations

import re
import sqlite3
from dataclasses import dataclass
from pathlib import Path

_PATH_SEP = re.compile(r"[/\\]")

# A hatásos caption/keywords: JPEG-nél az IPTC (caption_file) az elsődleges,
# egyébként a .picasa.ini értéke (Picasa-viselkedés).
_SELECT = """
SELECT p.id, f.path AS folder_path, p.name, p.kind, p.size, p.mtime_ns,
       p.star, p.hidden, COALESCE(p.caption_file, p.caption_ini) AS caption,
       COALESCE(p.keywords_file, p.keywords_ini) AS keywords,
       p.rotate_steps, p.filters, p.taken_at, p.orientation, p.width, p.height
FROM photos p JOIN folders f ON f.id = p.folder_id
"""


@dataclass(frozen=True)
class PhotoRecord:
    id: int
    folder_path: str
    name: str
    kind: str
    size: int
    mtime_ns: int
    star: bool
    caption: str | None
    keywords: str | None
    rotate_steps: int
    filters: str | None
    taken_at: str | None
    orientation: int
    width: int | None
    height: int | None
    # defaultos mező a végén: a meglévő (pozicionális) konstruálások ne
    # törjenek — az olvasó lekérdezés kulcsszóval tölti (#17)
    hidden: bool = False


def photos_in_folder(
    conn: sqlite3.Connection, folder: str | Path
) -> tuple[PhotoRecord, ...]:
    rows = conn.execute(
        f"{_SELECT} WHERE f.path = ? ORDER BY p.name", (str(folder),)
    )
    return _records(rows)


def all_photos(conn: sqlite3.Connection) -> tuple[PhotoRecord, ...]:
    """A teljes könyvtár a rács-feedhez (#64) — a mappán belüli sorrend
    névsor; a mappák feed-sorrendjét a hívó (a bal hasáb rendje szerint)
    állítja be."""
    rows = conn.execute(f"{_SELECT} ORDER BY f.path, p.name")
    return _records(rows)


def starred_photos(conn: sqlite3.Connection) -> tuple[PhotoRecord, ...]:
    rows = conn.execute(f"{_SELECT} WHERE p.star = 1 ORDER BY f.path, p.name")
    return _records(rows)


def search_photos(conn: sqlite3.Connection, query: str) -> tuple[PhotoRecord, ...]:
    """Keresés MINDENBEN (Picasa): fájlnév/felirat/kulcsszó (FTS5) ÉS
    mappanév — az egyező nevű mappák teljes tartalma is találat.

    A felhasználói inputot idézett kifejezéssé alakítjuk, hogy ne
    értelmeződjön FTS-szintaxisként (injection/szintaxishiba ellen);
    a mappanév-egyezés casefold-os (magyar ékezetekre is jó).
    """
    phrase = '"' + query.replace('"', '""') + '"'
    folded = query.casefold()
    folder_ids = [
        row["id"]
        for row in conn.execute("SELECT id, path FROM folders")
        if folded in _PATH_SEP.split(row["path"])[-1].casefold()
    ]
    placeholders = ",".join("?" * len(folder_ids))
    folder_clause = f" OR p.folder_id IN ({placeholders})" if folder_ids else ""
    rows = conn.execute(
        f"{_SELECT} WHERE p.id IN "
        "(SELECT rowid FROM photos_fts WHERE photos_fts MATCH ?)"
        f"{folder_clause} ORDER BY f.path, p.name",
        (phrase, *folder_ids),
    )
    return _records(rows)


@dataclass(frozen=True)
class SearchSuggestion:
    """Egy sor a kereső legördülőjében (#7).

    kind: "folder" | "album"; param: mappánál a teljes útvonal,
    albumnál az album-token (a kiválasztás paramétere)."""

    kind: str
    name: str
    count: int
    param: str


def search_suggestions(
    conn: sqlite3.Connection,
    text: str,
    limit: int = 8,
    *,
    include_albums: bool = False,
) -> tuple[SearchSuggestion, ...]:
    """Javaslatok gépelés közben: név-egyező mappák és virtuális albumok.

    Picasa-viselkedés (150933-as referencia): az egyezés részszó-alapú és
    casefold-os; előbb a mappák, aztán az albumok, névsorban, darabszámmal.
    Az albumok a `.picasa.ini`-kből jönnek (az index nem tárolja őket);
    ugyanaz a token több ini-ben is szerepelhet — összesítve számoljuk.

    Az album-ág opt-in (#138): az összes has_ini-s mappa ini-jének beolvasása
    (NAS-on) drága, gépelés közben leütésenként hívódna, a jelenlegi hívó
    pedig el is dobja az album-találatokat. Amíg a virtuális albumok UI-ja
    (#9) el nem készül, az alapértelmezés `include_albums=False` — ini-olvasás
    ilyenkor egyáltalán nem történik.
    """
    query = text.strip().casefold()
    if not query:
        return ()
    folders = tuple(
        SearchSuggestion(
            kind="folder",
            name=_PATH_SEP.split(row["path"])[-1],
            count=row["n"],
            param=row["path"],
        )
        for row in conn.execute(
            "SELECT f.path AS path, COUNT(p.id) AS n FROM folders f "
            "JOIN photos p ON p.folder_id = f.id GROUP BY f.id ORDER BY f.path"
        )
        if query in _PATH_SEP.split(row["path"])[-1].casefold()
    )
    albums = _album_suggestions(conn, query) if include_albums else ()
    return (folders + albums)[:limit]


def _album_suggestions(
    conn: sqlite3.Connection, folded_query: str
) -> tuple[SearchSuggestion, ...]:
    """Album-javaslatok a has_ini-s mappák `.picasa.ini`-jeiből összesítve."""
    from picasapy.ini import albums_of, load_document, parse_album_refs

    names: dict[str, str] = {}  # token -> név (az első definíció nyer)
    counts: dict[str, int] = {}  # token -> tagok száma az összes ini-ben
    ini_rows = conn.execute("SELECT path FROM folders WHERE has_ini = 1")
    for row in ini_rows:
        ini_path = Path(row["path"]) / ".picasa.ini"
        try:
            document = load_document(ini_path)
        except (OSError, ValueError):
            continue  # időközben törölt/olvashatatlan ini — kihagyjuk
        for album in albums_of(document):
            if album.name and album.token not in names:
                names[album.token] = album.name
        for section in document.sections:
            if section.is_special:
                continue
            refs = parse_album_refs(section.get("albums") or "")
            for token in refs:
                counts[token] = counts.get(token, 0) + 1
    return tuple(
        SearchSuggestion(
            kind="album", name=name, count=counts.get(token, 0), param=token
        )
        for token, name in sorted(names.items(), key=lambda kv: kv[1].casefold())
        if folded_query in name.casefold()
    )


def _records(rows: sqlite3.Cursor) -> tuple[PhotoRecord, ...]:
    return tuple(
        PhotoRecord(
            id=row["id"],
            folder_path=row["folder_path"],
            name=row["name"],
            kind=row["kind"],
            size=row["size"],
            mtime_ns=row["mtime_ns"],
            star=bool(row["star"]),
            hidden=bool(row["hidden"]),
            caption=row["caption"],
            keywords=row["keywords"],
            rotate_steps=row["rotate_steps"],
            filters=row["filters"],
            taken_at=row["taken_at"],
            orientation=row["orientation"],
            width=row["width"],
            height=row["height"],
        )
        for row in rows
    )
