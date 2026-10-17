"""A db3-only adatok ismételhető kinyerése (#1, 7. rögzített döntés).

Az import CSAK OLVAS: a thumbindexből + az `imagedata` táblából fotónkénti
rekordokat állít elő, a Windows-útvonalakat a PathRemapperrel helyi
útvonalra írva. A nem leképezhető (remap nélküli) és a törölt/arc-
bejegyzések kimaradnak. Az index-be írást (mtime-ütközésnél az újabb
nyer elve, sémabővítés) az integrátor köti be — a sémaverziót csak ő
oszthatja ki (CONTRIBUTING.md).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

from picasapy.ini.contacts_xml import load_contacts_xml

from .deferredregion import (
    DeferredFace,
    parse_deferred_face,
    parse_deferred_region,
)
from .remap import PathRemapper
from .table import read_table
from .thumbindex import (
    ThumbIndexEntry,
    read_thumb_index,
    resolve_path,
)
from .wordhash import WordHashFormatError, read_wordhash

_ALBUM_WORD_PREFIX = "]album:"
# Mért albumdata-kategóriák: 0 = album, 2 = mappa.
_ALBUM_CATEGORY = 0
_FOLDER_CATEGORY = 2

logger = logging.getLogger(__name__)

# az importban hasznosított imagedata-oszlopok (mind opcionális/sparse)
#: #2336: a `tags`, `lat` és `long` a valódi adatbázisban 342, illetve
#: 219 képet érint — eddig NÉMÁN elvesztek, mert nem szerepeltek itt.
#: Mezőtípusok mérve: `tags` = 0x06 (sztring), `lat`/`long` = 0x02 (double).
#: #2336: a `geoview` a geotag TÉNYLEGES jelzője (ld. `_koordinata`) —
#: a tartalmát nem értelmezzük, csak azt, hogy üres-e.
_COLUMNS = (
    "caption", "rotate", "star", "filters", "crop64", "deferredface",
    "deferredregion",
    "tags", "lat", "long", "geoview",
)

#: #2335: a csillagozás VALÓDI helye. A tulajdonos 2026-08-22-i
#: adatmappájában 65 `.pmp` oszlop van, és **nincs köztük**
#: `imagedata_star.pmp` — a csillagozott képeket ez a sima szöveges lista
#: sorolja fel (soronként egy windowsos abszolút útvonal, CRLF sorvégekkel;
#: ott 50 kép). Az `imagedata_star.pmp` oszlopot NEM váltja ki: a kettő
#: UNIÓJA számít, hogy a régebbi adatbázisok se sérüljenek.
_STARLIST_NAME = "starlist.txt"
_UNASSIGNED_CONTACT_ID = "ffffffffffffffff"


@dataclass(frozen=True)
class PhotoRecord:
    """Egy fotó db3-ból kinyert adatai, helyi útvonallal."""

    local_path: str
    windows_path: str
    row: int
    caption: str | None
    #: #2521: a `rotate` a valódi adatbázisban SZTRING (`0x00`, `ytString`) —
    #: a `.picasa.ini`-beli `rotate(N)` alakot tartja, nem egész számot
    #: (`docs/specs/picasa-imagedata-rekord.md`). A korábbi `int | None`
    #: annotáció a szintetikus tesztfixtúrát írta le, nem a valóságot; ma
    #: ezt a mezőt semmi nem olvassa a forrásfában.
    rotate: str | None
    star: bool
    filters: str | None
    crop64: int | None
    #: #2336: kulcsszavak. Az oszlop egyetlen sztring, vesszővel elválasztva
    #: (ugyanaz az alak, mint a `.picasa.ini` `keywords=` kulcsa).
    tags: tuple[str, ...]
    #: #2336: földrajzi hely. Hogy van-e egyáltalán geotag, azt a
    #: `geoview` oszlop üressége mondja meg (mérve: képenkénti egyezés),
    #: nem a koordináta értéke — ld. `_koordinata`.
    latitude: float | None
    longitude: float | None
    faces: tuple[DeferredFace, ...]
    #: #4591: a `thumbindex` rekord TÍPUSA (`kind`; 2 = JPEG) és a két
    #: FILETIME. Együtt döntik el, hogy a videó dátumát a felhasználó
    #: módosította-e a Picasában (`pmpimport/videodatum.py`,
    #: `docs/specs/pmp-database.md` 15.). Alapértékük a „nincs adat".
    entry_kind: int = 0
    creation_filetime: int = 0
    modified_filetime: int = 0
    #: #4889: a Picasa mappalistájából átvett priority= hely.
    manual_priority: float | None = None
    #: #4900: albumtoken és albumorder= hely páronként.
    manual_album_places: tuple[tuple[str, float], ...] = ()


@dataclass(frozen=True)
class Db3Beolvasas:
    """Egy db3 olvasásának fotóadatai és kihagyott sorrendelemei."""

    rekordok: tuple[PhotoRecord, ...]
    wordhash_kihagyott: int = 0


def iter_photo_records(
    db3_dir: Path, remapper: PathRemapper
) -> tuple[PhotoRecord, ...]:
    """A db3 könyvtár fotó-rekordjai, sorrendhelyesen.

    A wordhashből kihagyott elemek számát a beolvas_db3 adja vissza.
    """
    return beolvas_db3(db3_dir, remapper).rekordok


def beolvas_db3(db3_dir: Path, remapper: PathRemapper) -> Db3Beolvasas:
    """A fotó-rekordok és a wordhashből kihagyott elemek beolvasása.

    A thumbindex fájl-bejegyzésein megy végig (könyvtár-, arc- és törölt
    bejegyzések kihagyva); a remap nélküli útvonalak szintén kimaradnak.
    A row a thumbindex-index — az imagedata-oszlopok 1:1 ehhez
    igazodnak (éles validálás: a leghosszabb oszlop hossza == thumbindex
    bejegyzésszám).

    Raises:
        FileNotFoundError: Hiányzó thumbindex vagy imagedata-oszlopok.
        PmpFormatError / ThumbIndexFormatError: Sérült db3-fájlokra.
    """
    db3_dir = Path(db3_dir)
    index_path = _find_thumb_index(db3_dir)
    entries = read_thumb_index(index_path)
    table = read_table(db3_dir, "imagedata")
    contact_names = _contact_names(db3_dir)
    csillagos = _read_starlist(db3_dir)
    manual_priorities, manual_album_places, wordhash_kihagyott = (
        _wordhash_manual_orders(db3_dir, entries, remapper)
    )

    records = []
    for entry in entries:
        if entry.is_directory or entry.name == "":
            continue
        windows_path = resolve_path(entries, entry)
        local_path = remapper.remap(windows_path)
        if local_path is None:
            continue
        faces = _photo_faces(table, entry.index, contact_names)
        # #2336: a geotag jelzője a `geoview` üressége, nem a koordináta
        # nulla értéke. Ha az OSZLOP hiányzik (régebbi adatmappa), a jelző
        # nem kérdezhető meg — a `None` erre az esetre szól.
        geoview_jelzo = (
            bool(table.value("geoview", entry.index))
            if table.column("geoview")
            else None
        )
        records.append(
            PhotoRecord(
                local_path=local_path,
                windows_path=windows_path,
                row=entry.index,
                caption=table.value("caption", entry.index) or None,
                rotate=table.value("rotate", entry.index),
                # #2335: a két forrás UNIÓJA — a lista a valódi
                # adatbázisokban az EGYETLEN forrás, az oszlop a
                # régebbiekben.
                star=bool(table.value("star", entry.index))
                or _normalizal(windows_path) in csillagos,
                filters=table.value("filters", entry.index) or None,
                crop64=table.value("crop64", entry.index),
                tags=_split_tags(table.value("tags", entry.index)),
                latitude=_koordinata(
                    table.value("lat", entry.index), geoview_jelzo
                ),
                longitude=_koordinata(
                    table.value("long", entry.index), geoview_jelzo
                ),
                faces=faces,
                entry_kind=entry.kind,
                creation_filetime=entry.creation_filetime,
                modified_filetime=entry.modified_filetime,
                manual_priority=manual_priorities.get(entry.index),
                manual_album_places=manual_album_places.get(entry.index, ()),
            )
        )
    return Db3Beolvasas(
        rekordok=tuple(records), wordhash_kihagyott=wordhash_kihagyott
    )


def _contact_names(db3_dir: Path) -> dict[str, str]:
    """`contacts.xml` id → current name; this beats the region snapshot."""
    path = Path(db3_dir) / "contacts" / "contacts.xml"
    try:
        return {
            entry.person_id.casefold(): entry.name
            for entry in load_contacts_xml(path)
            if entry.person_id and entry.name
        }
    except (OSError, ValueError) as hiba:
        logger.warning("A db3 contacts.xml nem olvasható: %s", path, exc_info=hiba)
        return {}


def _photo_faces(
    table, row: int, contact_names: dict[str, str]
) -> tuple[DeferredFace, ...]:
    """Resolve db3 ids against contacts.xml, using deferredregion as fallback.

    `deferredface` is authoritative for the id and unknown sentinel. The
    same-rectangle `deferredregion` name is only a fallback when the contact
    list is absent or lacks an id. Snapshot-only regions remain importable.
    """
    try:
        by_id = parse_deferred_face(table.value("deferredface", row))
    except ValueError:
        logger.warning("Hibás deferredface-sor: %s", row, exc_info=True)
        by_id = ()
    try:
        snapshots = parse_deferred_region(table.value("deferredregion", row))
    except ValueError:
        logger.warning("Hibás deferredregion-sor: %s", row, exc_info=True)
        snapshots = ()

    names_by_rect: dict[object, set[str]] = {}
    for snapshot in snapshots:
        name = snapshot.name.strip()
        if name:
            names_by_rect.setdefault(snapshot.rect, set()).add(name)

    resolved: list[DeferredFace] = []
    deferred_rects = set()
    for face in by_id:
        deferred_rects.add(face.rect)
        contact_id = face.contact_id or ""
        name = ""
        if contact_id != _UNASSIGNED_CONTACT_ID:
            name = contact_names.get(contact_id, "")
            if not name:
                candidates = names_by_rect.get(face.rect, set())
                if len(candidates) == 1:
                    name = next(iter(candidates))
        resolved.append(
            DeferredFace(rect=face.rect, name=name, contact_id=contact_id)
        )

    # The two columns are sparse and overlap only partially. Keep snapshot-only
    # regions, but never let a stale snapshot rename an id-bearing row.
    resolved.extend(face for face in snapshots if face.rect not in deferred_rects)
    return tuple(resolved)


def _wordhash_manual_orders(
    db3_dir: Path,
    entries: tuple[ThumbIndexEntry, ...],
    remapper: PathRemapper,
) -> tuple[dict[int, float], dict[int, tuple[tuple[str, float], ...]], int]:
    """A mappa- és albumlisták sorait útvonalra és kézi helyre oldja fel."""
    wordhash_path = _find_wordhash(db3_dir)
    if wordhash_path is None:
        return {}, {}, 0
    try:
        word_lists = read_wordhash(wordhash_path)
    except (OSError, WordHashFormatError) as exc:
        logger.warning(
            "A wordhash.dat kézi sorrendje kimarad, a fájl hibás vagy "
            "nem olvasható: %s",
            exc,
        )
        return {}, {}, 0

    try:
        albumdata = read_table(db3_dir, "albumdata")
    except (OSError, ValueError) as exc:
        logger.warning(
            "A wordhash.dat kézi sorrendje kimarad, az albumdata nem "
            "olvasható: %s",
            exc,
        )
        return {}, {}, 0

    priorities: dict[int, float] = {}
    album_places: dict[int, list[tuple[str, float]]] = {}
    skipped_total = 0
    for album_row in range(albumdata.row_count):
        category = albumdata.value("category", album_row)
        if category not in (_ALBUM_CATEGORY, _FOLDER_CATEGORY):
            continue
        token = albumdata.value("token", album_row)
        if not isinstance(token, str) or not token.startswith(_ALBUM_WORD_PREFIX):
            continue
        rows = word_lists.get(token)
        if rows is None:
            continue

        folder_path = None
        if category == _FOLDER_CATEGORY:
            filename = albumdata.value("filename", album_row)
            if not isinstance(filename, str) or not filename:
                continue
            local_folder = remapper.remap(filename)
            if local_folder is None:
                continue
            folder_path = Path(local_folder)

        position = 0 if category == _FOLDER_CATEGORY else 1
        seen: set[int] = set()
        skipped = 0
        for row in rows:
            if row >= len(entries):
                skipped += 1
                continue
            entry = entries[row]
            if (
                entry.is_directory
                or entry.kind in {1, 5}
                or entry.is_face_record
                or not entry.name
            ):
                skipped += 1
                continue
            local_path = remapper.remap(resolve_path(entries, entry))
            if local_path is None:
                skipped += 1
                continue
            if folder_path is not None and Path(local_path).parent != folder_path:
                skipped += 1
                continue
            if row in seen:
                skipped += 1
                continue
            seen.add(row)

            if category == _FOLDER_CATEGORY:
                priorities[row] = float(position)
            else:
                album_places.setdefault(row, []).append(
                    (token.removeprefix(_ALBUM_WORD_PREFIX), float(position))
                )
            position += 1

        skipped_total += skipped
        if skipped:
            logger.warning(
                "A wordhash.dat %s listájából %d kihagyott elem nem fájl "
                "vagy nem oldható fel thumbindex-útvonalra",
                token,
                skipped,
            )

    return priorities, {
        row: tuple(places) for row, places in album_places.items()
    }, skipped_total


def _find_wordhash(db3_dir: Path) -> Path | None:
    """A wordhash.dat kis-nagybetű-tűrő feloldása."""
    for path in sorted(db3_dir.iterdir()):
        if path.name.casefold() == "wordhash.dat":
            return path
    return None


_THUMB_INDEX_NAME = "thumbindex.db"
_THUMB_CACHE_INDEX_NAME = "thumbs_index.db"


def _find_thumb_index(db3_dir: Path) -> Path:
    """`thumbindex.db` keresése kis-nagybetű-független módon (MEMORY.md:
    élesben kisbetűs fájlnevek is előfordulnak).

    ⚠️ A `thumbs_index.db` NEM alternatív név: az egy másik formátumú
    (magic `0x3FCCCCCD`) bélyegkép-gyorstár-index, amit ez a parser nem
    tud beolvasni — a kettő egyszerre is jelen lehet a db3 könyvtárban
    (#1489). Ha csak a gyorstár van jelen, a hibaüzenet ezt nevesíti,
    hogy a felhasználó ne "érvénytelen magic" hibát kapjon egy egyébként
    ép adatmappára.
    """
    found_cache_index = False
    for path in sorted(db3_dir.iterdir()):
        name = path.name.casefold()
        if name == _THUMB_INDEX_NAME:
            return path
        if name == _THUMB_CACHE_INDEX_NAME:
            found_cache_index = True
    cache_hint = (
        f" A mappában van egy {_THUMB_CACHE_INDEX_NAME} nevű fájl, de az a "
        "bélyegkép-gyorstár indexe, nem a névindex — ez nem helyettesíti "
        f"a hiányzó {_THUMB_INDEX_NAME}-t."
        if found_cache_index
        else ""
    )
    raise FileNotFoundError(
        f"Nem található {_THUMB_INDEX_NAME} névindex a db3 könyvtárban: "
        f"{db3_dir}.{cache_hint} Ellenőrizze, hogy a teljes Picasa "
        "adatbázis-mappát (db3) átmásolta-e; ha a fájl valóban hiányzik, "
        "indítsa el az eredeti Picasát azon a gépen, hogy újraépítse az "
        "adatbázist, majd próbálja meg újra az importot."
    )


def _normalizal(windows_path: str) -> str:
    """Összehasonlítható alak: a Windows az útvonalakat kis-nagybetűre
    érzéketlenül kezeli, és a `starlist.txt` sorai a `thumbindex`-beliektől
    eltérő betűzéssel is állhatnak."""
    return windows_path.replace("/", "\\").rstrip("\\").casefold()


def _read_starlist(db3_dir: Path) -> frozenset[str]:
    """A `starlist.txt` sorai normalizált alakban; üres halmaz, ha nincs.

    A hiány NEM hiba: régebbi adatmappában nincs ilyen fájl, és a
    részleges import elve szerint egy olvashatatlan lista sem dönti be az
    importot — ilyenkor a csillagozás az `imagedata_star.pmp`-ből jön (vagy
    marad üres).

    A fájl kódolása nincs deklarálva; a `latin-1` egyetlen bájtsorra sem
    dob hibát, és a normalizálás úgyis csak összehasonlításra kell.
    """
    utvonal = db3_dir / _STARLIST_NAME
    try:
        nyers = utvonal.read_bytes()
    except OSError:
        return frozenset()
    sorok = nyers.decode("latin-1").splitlines()
    return frozenset(_normalizal(sor.strip()) for sor in sorok if sor.strip())


def _split_tags(nyers: str | None) -> tuple[str, ...]:
    """A `imagedata_tags` sztringje kulcsszó-listává (#2336).

    Az alak megegyezik a `.picasa.ini` `keywords=` kulcsáéval: vesszővel
    elválasztott lista. Az üres darabokat eldobjuk, a szóközöket levágjuk —
    a Picasa nem normalizál, tehát a `"a, b"` és az `"a,b"` ugyanaz.
    """
    if not nyers:
        return ()
    return tuple(darab.strip() for darab in nyers.split(",") if darab.strip())


def _koordinata(ertek: float | None, van_geotag: bool | None) -> float | None:
    """A `lat`/`long` oszlop értéke, a hiányt `None`-ra fordítva (#2336).

    A Picasa a geotag nélküli képeknél is kitölti az oszlopot (nem hagy
    lyukat), és a hiányt nullával jelöli — nullaként átvéve minden geotag
    nélküli kép a Guineai-öbölbe (Null-sziget) kerülne a Helyek-panelen.

    **A jelző a `geoview` oszlop üressége, nem a koordináta értéke.**
    Mérve a tulajdonos adatmappáján (515 sor): ahol a `geoview` nem üres,
    ott a koordináta sem nulla (219 sor), és fordítva sem fordul elő
    kivétel (`CSAK geoview` 0 sor, `CSAK koordináta` 0 sor). A képenkénti
    egyezés tehát teljes, így a valódi 0,0-s koordináta (Egyenlítő × kezdő
    délkör, nyílt tenger) sem vész el.

    `van_geotag` = `None`, ha a `geoview` OSZLOP hiányzik a db3-ból
    (régebbi adatmappa): ott a jelző nem kérdezhető meg, ezért marad a
    „0,0 nem hely" szabály.
    """
    if ertek is None:
        return None
    try:
        szam = float(ertek)
    except (TypeError, ValueError):
        return None
    if van_geotag is None:
        return None if szam == 0.0 else szam
    return szam if van_geotag else None
