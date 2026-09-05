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
meglévő pontos-duplikátum rétegre ül rá (méret → Picasa gyors kulcs →
teljes SHA-256) — ugyanaz a mérce, mint a Duplikátum-kezelőé (#287)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Iterable, Sequence

from picasapy.dedup.exact import FastKeySource, file_content_hash
from picasapy.dedup.fastkey import picasa_fast_key
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


#: #1555: az importálás öt ÁTMÉRETEZÉSI opciója, a HOSSZABBIK oldal
#: képpontértékében. A mért parancsazonosítók és feltételek
#: (`0x00518b40`, `acquirepanel/sync_options_button`):
#:
#: | azonosító | feltétel        | jelentés        |
#: |-----------|-----------------|-----------------|
#: | `0x9dfe`  | `[+0x74c] == 0` | eredeti méret   |
#: | `0x9e14`  | `== 0x800`      | 2048 képpont    |
#: | `0x9dfd`  | `== 0x640`      | 1600 képpont    |
#: | `0x9e0a`  | `== 0x400`      | 1024 képpont    |
#: | `0x9e13`  | `== 0x320`      | 800 képpont     |
#:
#: ⚠️ A tárolt érték KÉPPONT, nem sorszám — az eredeti is így tárolja
#: (egyetlen egész mező). Ettől egy új méret felvétele nem töri el a
#: meglévő beállításokat, és a `0` jelentése „EREDETI MÉRET", nem „nincs
#: beállítva".
ATMERETEZES_EREDETI = 0
ATMERETEZES_OPCIOK: tuple[int, ...] = (ATMERETEZES_EREDETI, 2048, 1600, 1024, 800)


def atmeretezendo(szelesseg: int, magassag: int, hatar: int) -> bool:
    """Kell-e átméretezni ezt a képet a megadott határra.

    `hatar = 0` (eredeti méret) esetén soha. A már kisebb képet sem
    nagyítjuk FEL: az importálás nem javíthat a felbontáson, csak
    ronthatna a fájlmérettel."""
    if hatar <= 0:
        return False
    return max(int(szelesseg), int(magassag)) > int(hatar)


def atmeretez_masolatot(target: Path, hatar: int) -> bool:
    """A MÁR ÁTMÁSOLT fájl leskálázása a helyén; volt-e tényleges munka.

    A leskálázás matematikáját SZÁNDÉKOSAN nem írjuk le újra: a
    `cvimage.scale_down` a projekt egyetlen „hosszabbik oldal korlátozása,
    felskálázás soha" megvalósítása (INTER_AREA-val), és a kiírás is a
    bevált, bájt-alapú úton megy — a `cv2.imwrite` Windowson ékezetes
    útvonalon némán nem ír (#190).

    A CÉLPÉLDÁNYT írja át, sosem a forrást: az importálás a kártyán lévő
    eredetihez nem nyúlhat. Nem dekódolható fájlra (videó, RAW, sérült)
    `False`-szal tér vissza — a másolat érintetlen marad."""
    if hatar <= 0:
        return False
    import cv2

    from picasapy.collage.render import write_collage
    from picasapy.cvimage import read_image_bytes, scale_down

    target = Path(target)
    # ⚠️ A `read_image_bytes` a NYERS BÁJTOKAT adja (nem dekódolt képet) —
    # a dekódolás a hívóé, `imdecode`-dal (a `thumbs/cache.py` mintája).
    # A bájt-alapú út azért kell, mert a `cv2.imread` Windowson ékezetes
    # útvonalon némán elhasal (#65).
    bajtok = read_image_bytes(target)
    if bajtok is None:
        return False
    kep = cv2.imdecode(bajtok, cv2.IMREAD_COLOR)
    if kep is None or kep.ndim < 2:
        return False
    magassag, szelesseg = kep.shape[:2]
    if not atmeretezendo(szelesseg, magassag, hatar):
        return False
    write_collage(target, scale_down(kep, hatar))
    return True


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
    library_key_source: FastKeySource | None = None,
) -> frozenset[Path]:
    """A `candidates` közül azok elérési útjai, amelyek TARTALMA megegyezik
    egy `library_paths`-beli (már indexelt, azaz "már importálva a
    Picasába") fájléval (#441, "Exclude Duplicates").

    NEM önálló duplikátum-logika: a meglévő pontos-duplikátum réteget
    (#31/#287, `dedup/exact.py`) használja fel, csak a jelölt/könyvtár
    két külön halmaza között, a `dedup.find_duplicates`-től eltérően (az a
    kereső EGY halmazon belül csoportosít). Ugyanaz a három lépcső is:
    méret → Picasa gyors kulcs (#1481, ~33 KB/fájl) → teljes SHA-256. A
    kimondó mérce a SHA-256 marad: egy téves egyezés itt azt jelentené,
    hogy egy fénykép szótlanul kimarad az importálásból.

    `library_key_source` (#1494): a KÖNYVTÁRBELI fájlok gyorskulcsának
    forrása; alapértelmezésben a lemezről számoló `picasa_fast_key`.
    Index-hátterű forrással (`index.IndexFastKeySource`) a MÁSODIK
    importálási kör a könyvtár változatlan képeinek fájlvégeit sem olvassa
    be újra.

    ⚠️ A JELÖLTEK kulcsa szándékosan MARAD számolt: azok kártyáról/kamerából
    jönnek, a következő körben már nem lesznek ott, tehát az indexben csak
    idegen útvonalú szemétsorokat hagynának — a nyereség nulla volna.

    Az olvashatatlan (törölt/elérhetetlen) fájlok szótlanul kimaradnak az
    összevetésből — sem duplikátumnak, sem egyedinek nem számítanak."""
    kulcsforras = picasa_fast_key if library_key_source is None else library_key_source
    library_by_size: dict[int, list[Path]] = {}
    for path in library_paths:
        try:
            size = path.stat().st_size
        except OSError:
            continue
        library_by_size.setdefault(size, []).append(path)
    if not library_by_size:
        return frozenset()

    # a könyvtárbeli fájlok kulcsa/hash-e csak akkor számol, ha tényleg kell
    # (van jelölt AZONOS mérettel) — és utána újrafelhasználódik, ha több
    # jelölt is ugyanabba a mérethalmazba esik.
    library_key_cache: dict[Path, int | None] = {}
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
        # 2. lépcső: a gyors kulcs a jelöltre és a könyvtárbeli társaira.
        # Kulcs nélküli (üres vagy olvashatatlan) fájlnál nem szűrünk elő —
        # döntsön a teljes hash, az adja a helyes választ üres fájlokra is.
        candidate_key = picasa_fast_key(candidate.path)
        kulcs_egyezok = []
        for library_path in same_size:
            if library_path not in library_key_cache:
                library_key_cache[library_path] = kulcsforras(library_path)
            if library_key_cache[library_path] == candidate_key:
                kulcs_egyezok.append(library_path)
        if not kulcs_egyezok:
            continue
        # 3. lépcső: csak a kulcs-egyezőkre megy el a teljes olvasás.
        candidate_hash = file_content_hash(candidate.path)
        if candidate_hash is None:
            continue
        for library_path in kulcs_egyezok:
            if library_path not in library_hash_cache:
                library_hash_cache[library_path] = file_content_hash(library_path)
            if library_hash_cache[library_path] == candidate_hash:
                duplicates.add(candidate.path)
                break
    return frozenset(duplicates)
