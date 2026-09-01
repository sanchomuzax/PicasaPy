"""Olvasó lekérdezések: mappa-lista, csillagozottak, FTS5 keresés."""

from __future__ import annotations

import re
import sqlite3
from dataclasses import dataclass
from pathlib import Path

from .colors import paths_with_color
from .search_color import parse_color_terms

_PATH_SEP = re.compile(r"[/\\]")

# A hatásos caption/keywords: JPEG-nél az IPTC (caption_file) az elsődleges,
# egyébként a .picasa.ini értéke (Picasa-viselkedés).
_SELECT = """
SELECT p.id, f.path AS folder_path, p.name, p.kind, p.size, p.mtime_ns,
       p.star, p.hidden, COALESCE(p.caption_file, p.caption_ini) AS caption,
       COALESCE(p.keywords_file, p.keywords_ini) AS keywords,
       p.rotate_steps, p.filters, p.taken_at, p.orientation, p.width, p.height,
       p.geotag_ini, p.exif_lat, p.exif_lon,
       -- #463: a bélyegkép arc-jelvényeihez — hány felismert arc van a
       -- képen, és hány vár még névadásra. A `face` tábla származtatott
       -- adat (index/faces_detected.py); LEFT JOIN, hogy az arc-szkennelés
       -- előtti (üres táblás) állapot is működjön.
       (SELECT COUNT(*) FROM face WHERE face.photo_id = p.id) AS face_count,
       (SELECT COUNT(*) FROM face
         WHERE face.photo_id = p.id AND face.state = 'unnamed'
       ) AS unnamed_face_count
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
    # #30: geocímke — az ini nyers `geotag=` értéke és a fájlból olvasott
    # EXIF GPS. A feloldás (melyik nyer) a `location` tulajdonságé.
    geotag: str | None = None
    exif_lat: float | None = None
    exif_lon: float | None = None
    # #463: arc-jelvények a bélyegképen — a saját (YuNet) felismerés
    # eredménye (`face` tábla). A `face_count` az összes találat, az
    # `unnamed_face_count` a még névre váró (jóváhagyandó) arcoké.
    face_count: int = 0
    unnamed_face_count: int = 0

    @property
    def location(self):
        """A kép helye `GeoPoint`-ként; ini `geotag=` > EXIF GPS > None.

        Fájlolvasás NINCS: az EXIF-koordináta az indexelésnél már eltárolva."""
        from picasapy.metadata.gps import GeoPoint, parse_geotag

        point = parse_geotag(self.geotag)
        if point is not None:
            return point
        if self.exif_lat is None or self.exif_lon is None:
            return None
        try:
            return GeoPoint(self.exif_lat, self.exif_lon)
        except ValueError:
            return None


def photos_in_folder(
    conn: sqlite3.Connection, folder: str | Path
) -> tuple[PhotoRecord, ...]:
    rows = conn.execute(
        f"{_SELECT} WHERE f.path = ? ORDER BY p.name", (str(folder),)
    )
    return _records(rows)


def photos_under_folder(
    conn: sqlite3.Connection, folder: str | Path
) -> tuple[PhotoRecord, ...]:
    """A mappa ÉS az összes almappája fotói (#294) — a duplikátum-kereső
    „aktuális mappa (+almappák)" hatóköre.

    Az illesztés a mappa saját sorára, illetve az elválasztóval kezdődő
    részfájára megy: a `kepek/a` így NEM fogja meg a `kepek/alma` mappát.
    A LIKE-mintában a `%` és `_` jokerek escape-elve vannak, hogy egy ilyen
    karaktert tartalmazó mappanév se viselkedjen mintaként.
    """
    prefix = str(folder).rstrip("/\\")
    escaped = (
        prefix.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    )
    rows = conn.execute(
        f"{_SELECT} WHERE f.path = ? "
        "OR f.path LIKE ? ESCAPE '\\' OR f.path LIKE ? ESCAPE '\\' "
        "ORDER BY f.path, p.name",
        (prefix, f"{escaped}/%", f"{escaped}\\\\%"),
    )
    return _records(rows)


def photo_by_id(conn: sqlite3.Connection, photo_id: int) -> PhotoRecord | None:
    """Egy fotó friss rekordja azonosító alapján (#141): a célzott
    index-UPDATE után ez adja vissza a rács-sor frissítéséhez szükséges
    állapotot — nincs szükség teljes mappa-resyncre/lekérdezésre."""
    row = conn.execute(f"{_SELECT} WHERE p.id = ?", (photo_id,)).fetchone()
    return _records([row])[0] if row is not None else None


def all_photos(conn: sqlite3.Connection) -> tuple[PhotoRecord, ...]:
    """A teljes könyvtár a rács-feedhez (#64) — a mappán belüli sorrend
    névsor; a mappák feed-sorrendjét a hívó (a bal hasáb rendje szerint)
    állítja be."""
    rows = conn.execute(f"{_SELECT} ORDER BY f.path, p.name")
    return _records(rows)


def starred_photos(conn: sqlite3.Connection) -> tuple[PhotoRecord, ...]:
    rows = conn.execute(f"{_SELECT} WHERE p.star = 1 ORDER BY f.path, p.name")
    return _records(rows)


def video_photos(conn: sqlite3.Connection) -> tuple[PhotoRecord, ...]:
    """Csak a videók (#1830) — az eredeti `moviesearch` szűrője.

    A MÁR MEGLÉVŐ `kind` mezőre épül, tehát nem igényel sem sémaváltozást,
    sem újraindexelést. A rendezés a csillag-szűrőét követi (mappa, majd
    név), hogy a szűrt nézet ugyanúgy viselkedjen, mint a testvérei."""
    rows = conn.execute(
        f"{_SELECT} WHERE p.kind = 'video' ORDER BY f.path, p.name"
    )
    return _records(rows)


def geotagged_photos(conn: sqlite3.Connection) -> tuple[PhotoRecord, ...]:
    """Minden hellyel rendelkező fotó (#30) — a geo-szűrő és a térkép-nézet
    forrása.

    Az SQL csak előszűr (van-e egyáltalán adat); az ÉRVÉNYESSÉGET a
    `PhotoRecord.location` dönti el, hogy a hibás `geotag=` ne kerüljön a
    térképre. Rendezés: legfrissebb felvétel elöl (mint a csillagozottaknál
    a mappa-sorrend) — a nem datált képek a végére."""
    rows = conn.execute(
        f"{_SELECT} WHERE p.geotag_ini IS NOT NULL AND p.geotag_ini <> ''"
        " OR (p.exif_lat IS NOT NULL AND p.exif_lon IS NOT NULL)"
        " ORDER BY p.taken_at IS NULL, p.taken_at DESC, f.path, p.name"
    )
    return tuple(
        record for record in _records(rows) if record.location is not None
    )


def search_photos(
    conn: sqlite3.Connection, query: str, *, only_id: int | None = None
) -> tuple[PhotoRecord, ...]:
    """Keresés MINDENBEN (Picasa): fájlnév/felirat/kulcsszó (FTS5) ÉS
    mappanév — az egyező nevű mappák teljes tartalma is találat.

    #383: a `color:`/`szín:` tokenek (pl. `color:blue nyaralás`) a
    szabadszavas résztől ELVÁLNAK — a színszűrés a maradék szöveges
    kereséssel ÉS kapcsolatban van, több színtoken egymással VAGY
    kapcsolatban (ld. `search_color.parse_color_terms`). Ha egy képre még
    nincs kiszámolt színtoken (a háttér-feltöltés még nem érte el), a kép
    egyszerűen kimarad a találatokból — nem hiba, csak hiányzó adat.

    `only_id` (#1515): a találati halmazt EGYETLEN képre szűkíti, tehát a
    visszatérés vagy üres, vagy egyelemű. Így lehet TAGSÁG-kérdést feltenni
    („találat-e még ez a kép?") anélkül, hogy a teljes listát felépítenénk.
    Mért különbség valósághű indexen (140 755 kép / 3 000 mappa): a teljes
    lekérdezés medián **597 ms** (27 179 találatnál), az egy képre szűkített
    **6–11 ms**.

    A szűkítés SZÁNDÉKOSAN ugyanennek a függvénynek a paramétere, nem külön
    „egyezik-e ez a kép" segéd: két külön implementációban a mappanév-ág, a
    színtokenek és az idézőjel-védés is duplikálódna, és ha elcsúsznának, a
    nézet NÉMÁN hibás tagságot mutatna.
    """
    remainder, color_tokens = parse_color_terms(query)
    remainder = remainder.strip()
    if not remainder and not color_tokens:
        return ()
    if remainder:
        records = _text_search(conn, remainder, only_id=only_id)
    elif only_id is None:
        records = all_photos(conn)
    else:
        found = photo_by_id(conn, only_id)
        records = (found,) if found is not None else ()
    if color_tokens:
        wanted_paths = paths_with_color(conn, color_tokens)
        records = tuple(
            record for record in records if _full_path(record) in wanted_paths
        )
    return records


def _text_search(
    conn: sqlite3.Connection, query: str, *, only_id: int | None = None
) -> tuple[PhotoRecord, ...]:
    """A korábbi (#383 előtti) szöveges keresés-logika, változatlanul —
    idézett FTS-kifejezés + casefold-os mappanév-egyezés.

    #1515: az `only_id` egyetlen képre szűkít. A meglévő feltétel emiatt
    ZÁRÓJELBE került: az FTS-egyezés és a mappanév-egyezés VAGY-a továbbra
    is EGY egységként áll, a szűkítés pedig ÉS-sel jön rá. Zárójel nélkül a
    mappanév-ág kibújna a szűkítés alól.
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
    scope_clause = " AND p.id = ?" if only_id is not None else ""
    scope_params = () if only_id is None else (only_id,)
    rows = conn.execute(
        f"{_SELECT} WHERE (p.id IN "
        "(SELECT rowid FROM photos_fts WHERE photos_fts MATCH ?)"
        f"{folder_clause}){scope_clause} ORDER BY f.path, p.name",
        (phrase, *folder_ids, *scope_params),
    )
    return _records(rows)


def full_path(record: PhotoRecord) -> str:
    """A fotó teljes útvonala — ugyanaz a képzési szabály, mint a
    `photo_colors`/`photo_hashes` kulcsánál (`str(Path(folder) / name)`).

    #699: PUBLIKUS, mert a szerkesztés-napló (`app/edit_journal_controller`)
    is ezt hívja. A napló írás/olvasás kulcsának bájtra egyeznie kell —
    harmadik útvonal-szabályt írni tilos: ha a két oldal másképp képezné,
    a `detect_lost_edits` némán soha nem találna egyezést, és a #644
    védelme CSENDBEN hatástalan maradna.
    """
    return str(Path(record.folder_path) / record.name)


#: A régi, modulon belüli név — a meglévő hívások miatt marad.
_full_path = full_path


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


def _optional_count(row: sqlite3.Row, key: str) -> int:
    """Számláló-oszlop, ha a lekérdezés adta — különben 0.

    Nem minden hívó a `_SELECT`-et használja (pl. a duplikátum-kereső saját,
    szűkebb oszloplistával dolgozik), ezért a hiányzó oszlop nem hiba.
    """
    try:
        value = row[key]
    except (IndexError, KeyError):
        return 0
    return int(value or 0)


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
            geotag=row["geotag_ini"],
            exif_lat=row["exif_lat"],
            exif_lon=row["exif_lon"],
            face_count=_optional_count(row, "face_count"),
            unnamed_face_count=_optional_count(row, "unnamed_face_count"),
        )
        for row in rows
    )
