"""A db3-only adatok ismételhető kinyerése (#1, 7. rögzített döntés).

Az import CSAK OLVAS: a thumbindexből + az `imagedata` táblából fotónkénti
rekordokat állít elő, a Windows-útvonalakat a PathRemapperrel helyi
útvonalra írva. A nem leképezhető (remap nélküli) és a törölt/arc-
bejegyzések kimaradnak. Az index-be írást (mtime-ütközésnél az újabb
nyer elve, sémabővítés) az integrátor köti be — a sémaverziót csak ő
oszthatja ki (CONTRIBUTING.md).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .deferredregion import DeferredFace, parse_deferred_region
from .remap import PathRemapper
from .table import read_table
from .thumbindex import read_thumb_index, resolve_path

# az importban hasznosított imagedata-oszlopok (mind opcionális/sparse)
_COLUMNS = ("caption", "rotate", "star", "filters", "crop64", "deferredregion")


@dataclass(frozen=True)
class PhotoRecord:
    """Egy fotó db3-ból kinyert adatai, helyi útvonallal."""

    local_path: str
    windows_path: str
    row: int
    caption: str | None
    rotate: int | None
    star: bool
    filters: str | None
    crop64: int | None
    faces: tuple[DeferredFace, ...]


def iter_photo_records(
    db3_dir: Path, remapper: PathRemapper
) -> tuple[PhotoRecord, ...]:
    """A db3 könyvtár fotó-rekordjai, sorrendhelyesen.

    A thumbindex fájl-bejegyzésein megy végig (könyvtár-, arc- és törölt
    bejegyzések kihagyva); a remap nélküli útvonalak szintén kimaradnak.
    A `row` a thumbindex-index — az imagedata-oszlopok 1:1 ehhez
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

    records = []
    for entry in entries:
        if entry.is_directory or entry.name == "":
            continue
        windows_path = resolve_path(entries, entry)
        local_path = remapper.remap(windows_path)
        if local_path is None:
            continue
        deferred = table.value("deferredregion", entry.index)
        try:
            faces = parse_deferred_region(deferred)
        except ValueError:
            # hibás régió-bejegyzés nem dönti be az importot — a fotó
            # többi adata így is értékes (részleges import elve)
            faces = ()
        records.append(
            PhotoRecord(
                local_path=local_path,
                windows_path=windows_path,
                row=entry.index,
                caption=table.value("caption", entry.index) or None,
                rotate=table.value("rotate", entry.index),
                star=bool(table.value("star", entry.index)),
                filters=table.value("filters", entry.index) or None,
                crop64=table.value("crop64", entry.index),
                faces=faces,
            )
        )
    return tuple(records)


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
