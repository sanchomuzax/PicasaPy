"""Ismételhető db3-import: a csak az adatbázisban élő adatok kinyerése.

A `.picasa.ini`-ből nem pótolható adatok (képsorrend mappákban, arcnevek a
`deferredregion` oszlopban stb.) innen jönnek. Az import bármikor
újrafuttatható (7. rögzített döntés); két futás eredménye a forrás
mtime-ja alapján fésülhető össze — ütközésnél az újabb nyer.

Csak olvasunk: a db3 könyvtárhoz nem nyúlunk. Az SQLite-indexbe írás a
bekötési (integrátor-) lépés dolga, ez a modul tiszta adatszerkezeteket ad.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from picasapy.ini import Rect64, decode_rect64

from .pmp import PmpFormatError
from .remap import PathRemapper
from .table import read_table
from .thumbindex import EntryKind, read_thumbindex

_DEFERRED_COLUMN = "deferredregion"


@dataclass(frozen=True)
class FaceRegion:
    """Nevesített arc-régió a `deferredregion` oszlopból."""

    rect: Rect64
    name: str


@dataclass(frozen=True)
class ImageRecord:
    """Egy kép importált db3-adatai, már helyi útvonallal."""

    path: str
    source_path: str
    entry_index: int
    data: dict
    faces: tuple[FaceRegion, ...]


@dataclass(frozen=True)
class PmpImport:
    """Egy importfutás eredménye; a `source_mtime` a fésülés kulcsa."""

    images: tuple[ImageRecord, ...]
    folder_orders: dict[str, tuple[str, ...]]
    unmapped: tuple[str, ...]
    source_mtime: float


def parse_deferredregion(value: str) -> tuple[FaceRegion, ...]:
    """`rect64(<hex>),<Név>;...` lista dekódolása (a hex rövidülhet)."""
    faces: list[FaceRegion] = []
    for chunk in value.split(";"):
        if not chunk:
            continue
        rect_part, separator, name = chunk.partition(",")
        if not separator or not rect_part.startswith("rect64("):
            raise ValueError(f"Érvénytelen deferredregion-elem: {chunk!r}")
        faces.append(FaceRegion(rect=decode_rect64(rect_part), name=name))
    return tuple(faces)


def load_db3(db_dir: Path, remapper: PathRemapper) -> PmpImport:
    """A db3 könyvtár beolvasása és leképezése helyi útvonalakra.

    Csak a FILE típusú thumbindex-bejegyzésekből lesz kép; a bejegyzés
    sorszáma egyben az `imagedata` tábla sorindexe (1:1 megfeleltetés).
    """
    index = read_thumbindex(_find_thumbindex(db_dir))
    table = read_table(db_dir, "imagedata")
    images: list[ImageRecord] = []
    folder_orders: dict[str, list[str]] = {}
    unmapped: list[str] = []
    for i, entry in enumerate(index.entries):
        if entry.kind is not EntryKind.FILE:
            continue
        source_path = index.path_of(i)
        local_path = remapper.remap(source_path)
        if local_path is None:
            unmapped.append(source_path)
            continue
        data = table.row(i) if i < table.row_count else {}
        faces = parse_deferredregion(data.pop(_DEFERRED_COLUMN, ""))
        images.append(
            ImageRecord(
                path=local_path,
                source_path=source_path,
                entry_index=i,
                data=data,
                faces=faces,
            )
        )
        folder = remapper.remap(index.entries[entry.parent].name)
        if folder is not None:
            folder_orders.setdefault(folder, []).append(local_path)
    return PmpImport(
        images=tuple(images),
        folder_orders={k: tuple(v) for k, v in folder_orders.items()},
        unmapped=tuple(unmapped),
        source_mtime=_source_mtime(db_dir),
    )


def merge_imports(previous: PmpImport | None, new: PmpImport) -> PmpImport:
    """Két importfutás összefésülése: útvonalütközésnél az újabb nyer."""
    if previous is None:
        return new
    older, newer = sorted((previous, new), key=lambda imp: imp.source_mtime)
    merged_images = {image.path: image for image in older.images}
    merged_images.update({image.path: image for image in newer.images})
    return PmpImport(
        images=tuple(merged_images.values()),
        folder_orders={**older.folder_orders, **newer.folder_orders},
        unmapped=tuple(dict.fromkeys(older.unmapped + newer.unmapped)),
        source_mtime=newer.source_mtime,
    )


def _find_thumbindex(db_dir: Path) -> Path:
    """thumbindex.db keresése kis-nagybetű-függetlenül (élesben kisbetűs)."""
    for path in db_dir.iterdir():
        if path.name.lower() in ("thumbindex.db", "thumbs_index.db"):
            return path
    raise PmpFormatError(f"Nincs thumbindex.db a könyvtárban: {db_dir}")


def _source_mtime(db_dir: Path) -> float:
    """A db3-készlet legfrissebb bemeneti fájljának mtime-ja."""
    inputs = [
        path
        for path in db_dir.iterdir()
        if path.suffix.lower() == ".pmp" or "thumbindex" in path.name.lower()
    ]
    return max((path.stat().st_mtime for path in inputs), default=0.0)
