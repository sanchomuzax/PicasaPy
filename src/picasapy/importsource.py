"""Import forrásból (#23/#441): forrás-mappa beolvasása, a cél-alútvonal
számítása a HÁROM elnevezési mód szerint, és a már indexelt könyvtárral
egyező (duplikátum) jelöltek kiszűrése — tiszta, GUI- és Qt-mentes logika.

A GUI-hidat a `picasapy.app.import_source_controller.ImportSourceController`
adja; itt semmi nem tud QObject-ről, könnyen, elszigetelten tesztelhető.

Dátum-forrás (a `picasapy.timeline` #24 döntésével egyező): elsődlegesen a
kép EXIF `taken_at`-ja (`picasapy.metadata.reader.read_file_metadata`),
ennek hiányában (RAW/videó, vagy olvashatatlan EXIF) a fájl `mtime_ns`-ére
esik vissza — ugyanaz a `resolve_date`, amit az Időrend nézet is használ,
hogy a két funkció dátum szerinti csoportosítása KONZISZTENS legyen.

#441 — HÁROM célmappa-elnevezési mód (a korábbi szabad szöveges sablon-mező
helyett): `NAMING_MANUAL` (egyetlen, kézzel megadott mappanév),
`NAMING_BY_DATE` (a Picasa import-munkafolyamatának lelke: felvétel dátuma
szerint KÜLÖN "ÉÉÉÉ-HH-NN" mappákba bontva), `NAMING_TODAY` (egyetlen, a mai
dátum nevű mappa). Ld. `destination_subpath_for_mode`.

A duplikátum-kizáráshoz (`duplicate_paths`) NEM új logika készült: a
meglévő `picasapy.dedup.exact.file_content_hash`-re ül rá (tartalom-hash,
méret-előszűréssel) — ugyanaz a mérce, mint a Duplikátum-kezelőé (#287)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Iterable, Sequence

from picasapy.dedup.exact import file_content_hash
from picasapy.metadata.reader import read_file_metadata
from picasapy.scanner import media_kind_of, scan_tree
from picasapy.timeline import resolve_date

# józan alapértelmezés: "év/év-hónap-nap" mappaszervezés — a Picasa
# klasszikus, dátum szerinti importjának megfelelője. A #441 UI-ja már
# közvetlenül nem ajánlja fel ezt sablonként (a NAMING_BY_DATE egyetlen
# "ÉÉÉÉ-HH-NN" szintet használ, ld. `destination_subpath_for_mode`), de a
# `destination_subpath` sablon-motorja általánosan is hasznos marad.
DEFAULT_TEMPLATE = "{YYYY}/{YYYY}-{MM}-{DD}"

# a gyűjtőmappa neve, ha egyetlen dátum-forrás sem állapítható meg (sem
# EXIF, sem érvényes mtime) — a fájl így sem vész el, csak nem kerül
# dátum szerinti almappába.
UNKNOWN_DATE_FOLDER_NAME = "Ismeretlen dátum"

# -- #441: célmappa-elnevezési módok -----------------------------------

#: Kézi név — "Enter new folder title or choose existing folder to continue".
NAMING_MANUAL = "manual"
#: Felvétel dátuma szerint, "ÉÉÉÉ-HH-NN" mappánként külön —
#: "Import into separate folders for each date taken".
NAMING_BY_DATE = "date"
#: Egyetlen, a mai dátum nevű mappa — "Import into folder with today's date".
NAMING_TODAY = "today"

# a NAMING_BY_DATE módnál használt, EGYSZINTŰ sablon (nincs "{YYYY}/" előtag
# — a jegy szerint egyenesen "ÉÉÉÉ-HH-NN" mappák, a DEFAULT_TEMPLATE
# "év/év-hónap-nap" kétszintes szervezésétől eltérően).
_DATE_ONLY_TEMPLATE = "{YYYY}-{MM}-{DD}"


@dataclass(frozen=True)
class ImportCandidate:
    """Egy forrásban talált médiafájl az importhoz (előnézet + másolás)."""

    path: Path
    date: date | None


#: A forrás-tallózó fájltípus-szűrői (#441). Az eredeti tallózó három
#: szűrőt kínált — „Picture and Movie Files" / „Picture Files" / „All
#: Files" —, nálunk a forrás mindig MAPPA, ezért ugyanez a három fokozat a
#: BEOLVASÁSRA vonatkozik: mi számítson importálandó jelöltnek.
MEDIA_FILTER_ALL = "all"
MEDIA_FILTER_PICTURES_AND_MOVIES = "pictures_and_movies"
MEDIA_FILTER_PICTURES = "pictures"

#: Az egyes fokozatokhoz tartozó média-fajták (`scanner.media_kind_of`).
#: Az „all" nálunk sem jelent tetszőleges fájlt: a beolvasás továbbra is
#: csak médiát ad vissza (a `scan_tree` eleve azt gyűjt) — a különbség a
#: NYERS (RAW) fájlok beszámítása.
_FILTER_KINDS: dict[str, frozenset[str]] = {
    MEDIA_FILTER_ALL: frozenset({"photo", "raw", "video"}),
    MEDIA_FILTER_PICTURES_AND_MOVIES: frozenset({"photo", "raw", "video"}),
    MEDIA_FILTER_PICTURES: frozenset({"photo", "raw"}),
}


def scan_source(
    folder: str | Path, media_filter: str = MEDIA_FILTER_PICTURES_AND_MOVIES
) -> tuple[ImportCandidate, ...]:
    """A forrás-mappa (és almappái — kártyák gyakori DCIM/100XXXX
    szerkezete miatt rekurzívan) médiafájljai, útvonal szerint rendezve.

    `media_filter` (#441): a tallózó fájltípus-szűrőjének megfelelője —
    ismeretlen érték esetén a „képek és filmek" fokozat (az alapértelmezés).

    Raises:
        FileNotFoundError: Ha a forrás nem létezik vagy nem mappa.
    """
    folder = Path(folder)
    kinds = _FILTER_KINDS.get(media_filter, _FILTER_KINDS[MEDIA_FILTER_PICTURES_AND_MOVIES])
    scans = scan_tree(folder)
    candidates = [
        ImportCandidate(
            path=scan.path / media.name,
            date=_resolve_file_date(scan.path / media.name, media.mtime_ns),
        )
        for scan in scans
        for media in scan.files
        if media_kind_of(media.name) in kinds
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


def destination_subpath_for_mode(
    candidate_date: date | None,
    mode: str,
    *,
    manual_name: str = "",
    today: date | None = None,
) -> Path:
    """A cél-alútvonal a HÁROM elnevezési mód (#441) egyike szerint:

    - `NAMING_MANUAL`: egyetlen, felhasználó által megadott mappanév
      (`manual_name`) — MINDEN jelölt ugyanoda kerül. Üres/csak
      szóközökből álló névnél a cél-mappa gyökere (`Path(".")`).
    - `NAMING_BY_DATE`: felvétel dátuma szerint, "ÉÉÉÉ-HH-NN" mappánként
      külön (a `candidate_date`-et a hívó a `resolve_date`/`scan_source`
      mintájával állapította meg) — ismeretlen dátumnál
      `UNKNOWN_DATE_FOLDER_NAME`.
    - `NAMING_TODAY`: EGYETLEN, a mai dátum ("ÉÉÉÉ-HH-NN") nevű mappa —
      `today` teszthez determinisztikusan átadható, alapértelmezése a
      valódi `date.today()`.

    Ismeretlen `mode`-ra `ValueError` — a hívó (controller) mindig a három
    `NAMING_*` konstans egyikét adja át."""
    if mode == NAMING_MANUAL:
        name = manual_name.strip()
        return Path(name) if name else Path(".")
    if mode == NAMING_TODAY:
        chosen = today if today is not None else date.today()
        return Path(chosen.isoformat())
    if mode == NAMING_BY_DATE:
        return destination_subpath(candidate_date, _DATE_ONLY_TEMPLATE)
    raise ValueError(f"Ismeretlen elnevezési mód: {mode!r}")


def duplicate_paths(
    candidates: Sequence[ImportCandidate],
    library_paths: Iterable[Path],
) -> frozenset[Path]:
    """A `candidates` közül azok elérési útjai, amelyek TARTALMA (SHA-256,
    méret-előszűréssel — `picasapy.dedup.exact.file_content_hash`) megegyezik
    egy `library_paths`-beli (már indexelt, azaz "már importálva a
    Picasába") fájléval (#441, "Exclude Duplicates").

    NEM önálló duplikátum-logika: a meglévő pontos-duplikátum réteget
    (#31/#287, `dedup/exact.py`) használja fel, csak a jelölt/könyvtár
    két külön halmaza között, a `dedup.find_duplicates`-től eltérően (az a
    kereső EGY halmazon belül csoportosít).

    Az olvashatatlan (törölt/elérhetetlen) fájlok szótlanul kimaradnak az
    összevetésből — sem duplikátumnak, sem egyedinek nem számítanak."""
    library_by_size: dict[int, list[Path]] = {}
    for path in library_paths:
        try:
            size = path.stat().st_size
        except OSError:
            continue
        library_by_size.setdefault(size, []).append(path)
    if not library_by_size:
        return frozenset()

    # a könyvtárbeli fájlok hash-e csak akkor számol, ha tényleg kell
    # (van jelölt AZONOS mérettel) — és utána újrafelhasználódik, ha több
    # jelölt is ugyanabba a mérethalmazba esik.
    library_hash_cache: dict[Path, str | None] = {}
    duplicates: set[Path] = set()
    for candidate in candidates:
        try:
            size = candidate.path.stat().st_size
        except OSError:
            continue
        same_size = library_by_size.get(size)
        if not same_size:
            continue
        candidate_hash = file_content_hash(candidate.path)
        if candidate_hash is None:
            continue
        for library_path in same_size:
            if library_path not in library_hash_cache:
                library_hash_cache[library_path] = file_content_hash(library_path)
            if library_hash_cache[library_path] == candidate_hash:
                duplicates.add(candidate.path)
                break
    return frozenset(duplicates)
