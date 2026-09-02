"""Mappa-fa bejárás: média-fájlok és .picasa.ini felderítése.

Csak a médiát tartalmazó mappákat adja vissza (a Picasa is így listáz);
a rejtett mappákat — köztük a .picasaoriginals-t — kihagyja. A `exclude`
paraméterrel megadott mappák (és az alfáik) sem kerülnek bejárásra (#145,
FRExcludeFolders.txt — ld. `picasapy.scanner.exclude`).

#349 és #1169: a bejárás a Picasa `filters.txt`-ének megfelelő név- és
# útvonal-előtag alapú kizárólistát alkalmazza (`picasapy.scanner.name_filters`).
# A névlista például `Originals`, `thumbs` és `RECYCLER` mappákat zár ki,
# míg a Linuxos rendszer- és gyorsítótár-utak külön előtaglistában vannak.

#143: a bejárás közvetlenül `os.scandir`-ra épül, és a DirEntry cache-elt
stat-eredményét használja — fájlonként pontosan egy stat fut, külön
`(path / name).stat()` hívás nélkül. A `skip` predikátummal a hívó
(inkrementális rescan) mappánként eldöntheti, hogy a fájlok stat-olása
kihagyható-e; kihagyott mappánál csak a mappa és az esetleges ini kap statot.

#303: a bejárás — az `os.walk` alapértelmezésével (`followlinks=False`)
ellentétben — KÖVETI a symlinkelt almappákat, mert NAS-os elrendezésnél
gyakori, hogy egy fotómappa symlinkkel van behúzva a figyelt gyökér alá
(pl. `~/Kepek/Regi -> /mnt/nas/foto/regi`); követés nélkül ezek szótlanul
kimaradnának az indexből. A ciklusvédelem a bejárt mappák `(st_dev, st_ino)`
azonosítóját tartja nyilván (a teljes bejáráson át élő halmazban, ld. a
`_walk` `visited_dirs` paraméterét) — ismétlődő célra mutató mappát
(symlink-kör vagy önmagára mutató symlink) kihagyja, `logger.warning`-gal
jelezve. A törött symlink (nem létező cél) csendben kimarad, nem buktatja
el a bejárást. Ez mappánként egy plusz `os.stat` hívást jelent a korábbihoz
képest — a fájlonkénti stat-optimalizáció (fentebb) ettől független marad.
"""

from __future__ import annotations

import logging
import os
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from .filetypes import media_kind_of
from .name_filters import NameFilters, default_name_filters

logger = logging.getLogger(__name__)

PICASA_INI_NAME = ".picasa.ini"
# Korai Picasa-verziók vezető pont nélküli, nagybetűs néven írták az init
# (ld. docs/specs/picasa-ini-format.md) — a bejárás ezt is ini-jelenlétnek
# tekinti, hogy a mappa ne maradjon ki tévesen ini nélkülinek.
PICASA_INI_LEGACY_NAME = "Picasa.ini"

# Kihagyás-döntés (#143): (mappa, mappa-mtime_ns, ini-mtime_ns vagy None)
# → True, ha a mappa fájljainak stat-olása kihagyható (a mappa változatlan).
SkipPredicate = Callable[[Path, int, "int | None"], bool]


@dataclass(frozen=True)
class HibasBejegyzes:
    """Egy bejegyzés, amit a bejáró NEM tudott feldolgozni (#1998).

    Az eredeti Picasa könyvtárbejárója minden bejegyzéshez tárol egy
    `Type` mezőt, aminek **4 = hibás fájl**, **5 = hibás mappa** értéke
    van, és kérésre kilistázza őket (`badfiles.txt`, `0x004f25f0`; a két
    sorformátum `%s (badfile)` / `%s (baddirectory)`).

    Nálunk nem fájlba írunk: a hívó megkapja a listát, és minden elem
    naplóba is kerül. A `mappa` mező a `Type` 4/5 megfelelője."""

    path: Path | str
    errno: int
    mappa: bool


#: A hibás bejegyzések gyűjtője — a hívó adja át, ha kéri (a `#358`
#: `excluded_names` mintája). `None` esetén csak napló keletkezik.
HibaGyujto = "list[HibasBejegyzes] | None"


def _hiba(
    gyujto: list[HibasBejegyzes] | None,
    path: Path | str,
    hiba: OSError,
    *,
    mappa: bool,
) -> None:
    """Egy elnyelt `OSError` nyilvántartásba vétele (#1998).

    Eddig mind a hét ág `return`-nel tűnt el: a felhasználó annyit
    látott, hogy egy mappa vagy egy kép „nincs ott". A napló FÜGGETLEN
    a gyűjtőtől — a jelzés akkor is kell, ha a hívó nem kért listát."""
    logger.warning(
        "A bejárás kihagyta (%s): %s — %s",
        "mappa" if mappa else "fájl",
        path,
        hiba.strerror or hiba,
    )
    if gyujto is not None:
        gyujto.append(
            HibasBejegyzes(path=path, errno=hiba.errno or 0, mappa=mappa)
        )


@dataclass(frozen=True)
class MediaFile:
    name: str
    kind: str
    size: int
    mtime_ns: int


@dataclass(frozen=True)
class FolderScan:
    path: Path
    has_ini: bool
    files: tuple[MediaFile, ...]
    # #143: a mappa saját mtime-ja és az ini mtime-ja az inkrementális
    # rescan állapotához; csak akkor töltött, ha a hívó kérte (skip vagy
    # scan_folder) — az alapértelmezett teljes scan nem stat-ol pluszban.
    mtime_ns: int = 0
    ini_mtime_ns: int | None = None
    skipped: bool = False


def scan_tree(
    root: str | Path,
    exclude: tuple[str | Path, ...] = (),
    skip: SkipPredicate | None = None,
    name_filters: NameFilters | None = None,
    excluded_names: list[Path] | None = None,
    hibas_bejegyzesek: list[HibasBejegyzes] | None = None,
) -> tuple[FolderScan, ...]:
    """A gyökér alatti összes médiatartalmú mappa, útvonal szerint rendezve.

    Az `exclude`-ban felsorolt mappák (és az alfáik) kimaradnak a bejárásból
    (#145) — sem médiafájljaik, sem a bennük lévő almappák nem kerülnek az
    eredménybe.

    A `name_filters` (#349, ld. `picasapy.scanner.name_filters`) a Picasa
    gyári `filters.txt`-jének megfelelő NÉV-alapú kizárást végzi (pl.
    `Originals`, `temp`, `windows`) — alapértelmezés `default_name_filters()`.
    A hívó saját `NameFilters`-t adhat át (jövőbeli felhasználói
    konfigurációhoz), amelyben a `directory_includes` felülírhat egy gyári
    kizárást.

    A névalapú szabályoktól független `path_prefix_filters` a teljes
    útvonalon dolgozik (pl. `~/.cache`, `/proc`, `/sys`, `/usr`); így egy
    tetszőleges helyen lévő `Cache` nevű fotómappa bejárható marad.

    A `skip` predikátum (#143) mappánként dönthet a fájl-statok kihagyásáról:
    igaz válasz esetén a mappa `skipped=True`-val, üres `files`-szal kerül az
    eredménybe — a hívó tudja, hogy az indexbeli állapot érvényes maradt.

    #358 — az `excluded_names` (ha listát kapunk) minden, a #349 NÉV-
    kizárólista miatt kihagyott mappa útvonalát felgyűjti. Ez a jel adja
    meg a hívónak (a szinkron üres-scan-heurisztikájának), hogy a gyökér
    ténylegesen elérhető volt (scandir sikerült rajta), csak a talált
    tartalom szándékosan kizárt nevű mappák alatt van — szemben a gyökér
    valódi elérhetetlenségével, amikor egyetlen mappa scandirje sem fut le."""
    root_path = Path(root)
    if not root_path.is_dir():
        raise FileNotFoundError(f"A szkennelendő gyökér nem létezik: {root_path}")
    exclude_paths = tuple(Path(item).resolve() for item in exclude)
    filters = name_filters if name_filters is not None else default_name_filters()
    folders: list[FolderScan] = []
    _walk(
        root_path, exclude_paths, skip, filters, folders, set(),
        excluded_names, hibas_bejegyzesek,
    )
    return tuple(sorted(folders, key=lambda f: f.path))


def scan_folder(
    folder: str | Path,
    name_filters: NameFilters | None = None,
    skip: SkipPredicate | None = None,
    hibas_bejegyzesek: list[HibasBejegyzes] | None = None,
) -> FolderScan | None:
    """Egyetlen mappa nem-rekurzív scanje (watcher-ág, #143).

    None, ha a mappa nem létezik / nem mappa / rejtett / a neve gyári
    kizárólistán van (#349) / nincs benne média — a hívó ilyenkor az
    indexből is eltávolíthatja."""
    path = Path(folder)
    if path.name.startswith("."):
        return None
    filters = name_filters if name_filters is not None else default_name_filters()
    if filters.is_path_excluded(path):
        return None
    if filters.is_directory_excluded(path.name):
        return None
    try:
        with os.scandir(path) as it:
            entries = list(it)
    except OSError as hiba:
        _hiba(hibas_bejegyzesek, path, hiba, mappa=True)
        return None
    file_entries = [e for e in entries if not _entry_is_dir(e)]
    # #1674: a watcher-ág is kaphat kihagyás-predikátumot. Enélkül a
    # `_scan_folder` MINDEN médiafájlt statolt akkor is, ha a mappa
    # bizonyíthatóan változatlan — a #139 gépezete létezett, csak ez az út
    # nem használta.
    return _scan_folder(
        path, file_entries, skip=skip, with_state=True,
        hibas=hibas_bejegyzesek,
    )


def _walk(
    current: Path,
    exclude_paths: tuple[Path, ...],
    skip: SkipPredicate | None,
    name_filters: NameFilters,
    out: list[FolderScan],
    visited_dirs: set[tuple[int, int]],
    excluded_names: list[Path] | None = None,
    hibas: list[HibasBejegyzes] | None = None,
) -> None:
    """Rekurzív scandir-bejárás; olvashatatlan mappát csendben kihagy
    (élő NAS-on a mappa el is tűnhet menet közben).

    #303: symlinket követ, ezért a `visited_dirs` (a teljes bejáráson át
    közös, hívónként átadott állapot — NEM mappánként újul) tartja nyilván
    a már bejárt mappák `(st_dev, st_ino)` azonosítóját. Ismétlődésnél
    (symlink-kör, önmagára mutató symlink) a mappa kihagyásra kerül,
    figyelmeztetéssel."""
    if _is_under_any(current, exclude_paths):
        return
    if name_filters.is_path_excluded(current):
        return
    try:
        stat = os.stat(current)
    except OSError as hiba:
        # törött symlink vagy időközben eltűnt/elérhetetlen mappa (#1998:
        # eddig nyomtalanul tűnt el)
        _hiba(hibas, current, hiba, mappa=True)
        return
    identity = (stat.st_dev, stat.st_ino)
    if identity in visited_dirs:
        logger.warning(
            "Symlink-kör kihagyva: %s (a cél már egy korábban bejárt mappa)",
            current,
        )
        return
    visited_dirs.add(identity)
    try:
        with os.scandir(current) as it:
            entries = list(it)
    except OSError as hiba:
        _hiba(hibas, current, hiba, mappa=True)
        return
    dir_entries = []
    file_entries = []
    for entry in entries:
        if _entry_is_dir(entry):
            dir_entries.append(entry)
        else:
            file_entries.append(entry)
    scan = _scan_folder(
        current, file_entries, skip, with_state=skip is not None, hibas=hibas
    )
    if scan is not None:
        out.append(scan)
    for entry in sorted(dir_entries, key=lambda e: e.name):
        # A rejtett (pont-előtagú) mappák — köztük a .picasaoriginals —
        # mindig kimaradnak; a #349 gyári NÉV-kizárólista (Originals, temp,
        # windows, winnt, Program Files) ugyanitt, ugyanígy zárja ki a
        # nem rejtett, de kizárt nevű mappákat.
        if entry.name.startswith("."):
            continue
        if name_filters.is_directory_excluded(entry.name):
            # #358: a NÉV-kizárás jelzése — ez bizonyítja, hogy a szülő
            # mappa scandirje lefutott (a gyökér tehát elérhető), csak a
            # tartalma szándékosan marad ki az indexből.
            if excluded_names is not None:
                excluded_names.append(current / entry.name)
            continue
        if name_filters.is_path_excluded(current / entry.name):
            continue
        _walk(
            current / entry.name,
            exclude_paths,
            skip,
            name_filters,
            out,
            visited_dirs,
            excluded_names,
            hibas,
        )


def _entry_is_dir(entry: os.DirEntry) -> bool:
    """Mappa-e a bejegyzés — symlinket is KÖVETVE (#303, ld. a modul-
    docstring indoklását). Törött symlinkre a `DirEntry.is_dir()` nem dob
    kivételt, hanem `False`-t ad — az ilyen bejegyzés fájlként landol a
    szűrőben, ahol (jellemzően kiterjesztés hiányában) kiesik."""
    try:
        return entry.is_dir(follow_symlinks=True)
    except OSError:
        return False


def _scan_folder(
    path: Path,
    entries: list[os.DirEntry],
    skip: SkipPredicate | None,
    with_state: bool,
    hibas: list[HibasBejegyzes] | None = None,
) -> FolderScan | None:
    by_name = {entry.name: entry for entry in entries}
    media = [
        (name, kind)
        for name in sorted(by_name)
        if (kind := media_kind_of(name)) is not None
    ]
    if not media:
        return None
    has_ini = PICASA_INI_NAME in by_name or PICASA_INI_LEGACY_NAME in by_name
    mtime_ns = 0
    ini_mtime_ns: int | None = None
    if with_state:
        try:
            mtime_ns = os.stat(path).st_mtime_ns
        except OSError:
            mtime_ns = 0
        ini_mtime_ns = _ini_mtime(by_name)
        if skip is not None and mtime_ns and skip(path, mtime_ns, ini_mtime_ns):
            return FolderScan(
                path=path,
                has_ini=has_ini,
                files=(),
                mtime_ns=mtime_ns,
                ini_mtime_ns=ini_mtime_ns,
                skipped=True,
            )
    files = []
    for name, kind in media:
        try:
            # DirEntry.stat(): az első hívás statol, az eredmény cache-elt —
            # nincs külön (path / name).stat() kör (NAS-on plusz RTT / fájl).
            info = by_name[name].stat()
        except OSError as hiba:
            # Élő könyvtárban (NAS, futó Picasa) a fájl eltűnhet a listázás
            # és a stat között — egy fájl kihagyása nem buktathat scant.
            # #1998: de nem is tűnhet el NYOMTALANUL — ez a `Type = 4`
            # (hibás fájl) megfelelője.
            _hiba(hibas, path / name, hiba, mappa=False)
            continue
        files.append(
            MediaFile(name=name, kind=kind, size=info.st_size, mtime_ns=info.st_mtime_ns)
        )
    if not files:
        return None
    return FolderScan(
        path=path,
        has_ini=has_ini,
        files=tuple(files),
        mtime_ns=mtime_ns,
        ini_mtime_ns=ini_mtime_ns,
    )


def _ini_mtime(by_name: dict[str, os.DirEntry]) -> int | None:
    """A mappa ini-fájljának mtime-ja (elsőbbség: .picasa.ini), ha van."""
    entry = by_name.get(PICASA_INI_NAME) or by_name.get(PICASA_INI_LEGACY_NAME)
    if entry is None:
        return None
    try:
        return entry.stat().st_mtime_ns
    except OSError:
        return None


def _is_under_any(path: Path, roots: tuple[Path, ...]) -> bool:
    if not roots:
        return False
    resolved = path.resolve()
    return any(resolved == root or root in resolved.parents for root in roots)
