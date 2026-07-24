"""Import forrásból (#23): forrás-mappa beolvasása és a cél-alútvonal
számítása mappa-sablon szerint — tiszta, GUI- és Qt-mentes logika.

A GUI-hidat a `picasapy.app.import_source_controller.ImportSourceController`
adja; itt semmi nem tud QObject-ről, könnyen, elszigetelten tesztelhető.

Dátum-forrás (a `picasapy.timeline` #24 döntésével egyező): elsődlegesen a
kép EXIF `taken_at`-ja (`picasapy.metadata.reader.read_file_metadata`),
ennek hiányában (RAW/videó, vagy olvashatatlan EXIF) a fájl `mtime_ns`-ére
esik vissza — ugyanaz a `resolve_date`, amit az Időrend nézet is használ,
hogy a két funkció dátum szerinti csoportosítása KONZISZTENS legyen.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path

from picasapy.metadata.reader import read_file_metadata
from picasapy.scanner import scan_tree
from picasapy.timeline import resolve_date

# józan alapértelmezés: "év/év-hónap-nap" mappaszervezés — a Picasa
# klasszikus, dátum szerinti importjának megfelelője.
DEFAULT_TEMPLATE = "{YYYY}/{YYYY}-{MM}-{DD}"

# a gyűjtőmappa neve, ha egyetlen dátum-forrás sem állapítható meg (sem
# EXIF, sem érvényes mtime) — a fájl így sem vész el, csak nem kerül
# dátum szerinti almappába.
UNKNOWN_DATE_FOLDER_NAME = "Ismeretlen dátum"


@dataclass(frozen=True)
class ImportCandidate:
    """Egy forrásban talált médiafájl az importhoz (előnézet + másolás)."""

    path: Path
    date: date | None


def scan_source(folder: str | Path) -> tuple[ImportCandidate, ...]:
    """A forrás-mappa (és almappái — kártyák gyakori DCIM/100XXXX
    szerkezete miatt rekurzívan) médiafájljai, útvonal szerint rendezve.

    Raises:
        FileNotFoundError: Ha a forrás nem létezik vagy nem mappa.
    """
    folder = Path(folder)
    scans = scan_tree(folder)
    candidates = [
        ImportCandidate(
            path=scan.path / media.name,
            date=_resolve_file_date(scan.path / media.name, media.mtime_ns),
        )
        for scan in scans
        for media in scan.files
    ]
    return tuple(sorted(candidates, key=lambda candidate: str(candidate.path)))


def _resolve_file_date(path: Path, mtime_ns: int) -> date | None:
    """A csoportosítás/sablon dátuma: EXIF `taken_at`, ennek hiányában
    fájl-mtime (`picasapy.timeline.resolve_date`, #24 mintája)."""
    metadata = read_file_metadata(path)
    return resolve_date(metadata.taken_at, mtime_ns)


def destination_subpath(
    candidate_date: date | None, template: str = DEFAULT_TEMPLATE
) -> Path:
    """A cél-alútvonal (a választott cél-mappához KÉPEST relatív) a
    mappa-sablon szerint — a sablonban `{YYYY}`/`{MM}`/`{DD}` tokenek és
    `/` alkönyvtár-elválasztó szerepelhetnek (alapértelmezés:
    `{YYYY}/{YYYY}-{MM}-{DD}`, azaz "év/év-hónap-nap").

    Ismeretlen dátumnál (sem EXIF, sem érvényes mtime) az
    `UNKNOWN_DATE_FOLDER_NAME` gyűjtőmappa a visszaesés.
    """
    if candidate_date is None:
        return Path(UNKNOWN_DATE_FOLDER_NAME)
    rendered = (
        template.replace("{YYYY}", f"{candidate_date.year:04d}")
        .replace("{MM}", f"{candidate_date.month:02d}")
        .replace("{DD}", f"{candidate_date.day:02d}")
    )
    # a sablon "/" -szel jelöli az alkönyvtár-határt — a Path ezt
    # platformfüggetlenül (Windowson is helyesen) bontja szét
    parts = [part for part in rendered.split("/") if part]
    return Path(*parts) if parts else Path(".")
