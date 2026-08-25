"""Fájl átnevezése a lemezen — a .picasa.ini szekció követi (#15).

Round-trip elv: a szekció tartalma (star/caption/rotate/filters/… és minden
ismeretlen sor) bitre pontosan megmarad, csak a `[fájlnév]` fejléc változik.

Az ini-írás az ütközésbiztos `update_document`-en megy (#295): a NAS-mappát
a párhuzamosan futó eredeti Picasa is írhatja, a sima `load → save` pedig
némán felülírná, amit közben írt (lost update).

#366: `rename_photos_many` a `rename.fen` tömeges módja — alapnév +
opcionális dátum-/felbontás-utótag, Picasa-mintájú sorszámozás (`név`,
`név-1`, `név-2`…). Fájlonként az EGYFÁJLOS `rename_photo`-t hívja, így az
ini-átvitel (és annak ütközés-/hibakezelése) ugyanazon az úton megy, mint
az F2-átnevezésnél — nincs duplikált logika."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from picasapy.fileops.originals import originals_follow
from picasapy.ini import load_or_empty, update_document
from picasapy.scanner import PICASA_INI_NAME


def rename_photo(path: Path, new_name: str) -> Path:
    """A `path` fájl átnevezése `new_name`-re, ugyanabban a mappában.

    Args:
        path: Az átnevezendő fájl jelenlegi elérési útja.
        new_name: Az új fájlnév (csak név, elérési út elem nélkül).

    Returns:
        Az új elérési út.

    Raises:
        ValueError: Ha `new_name` üres vagy elérési út elemet tartalmaz.
        FileNotFoundError: Ha `path` nem létezik.
        FileExistsError: Ha a célnév (fájl, ini-szekció vagy a megőrzött
            eredeti helye) már foglalt — akkor is, ha az ini-szekciót csak az
            átnevezés közben foglalta el egy párhuzamos író.
        OSError: Ha a megőrzött eredeti költöztetése bukott el (#1430) —
            ilyenkor sem a kép, sem az eredetije nem mozdult el.
        IniConflictError: Ha az ini-t egy párhuzamos író miatt tartósan nem
            sikerült ütközésmentesen menteni (a fájl ekkor már át van
            nevezve; az üzenet megmondja, hol maradt a metaadat).
    """
    path = Path(path)
    _validate_name(new_name)
    if not path.exists():
        raise FileNotFoundError(f"A fájl nem létezik: {path}")
    target = path.with_name(new_name)
    if target.exists():
        raise FileExistsError(f"A célnév már foglalt: {target}")

    ini_path = path.parent / PICASA_INI_NAME
    has_ini = ini_path.exists()
    if has_ini and load_or_empty(ini_path).section(new_name) is not None:
        raise FileExistsError(f"A célnév ini-szekciója már foglalt: {new_name}")

    # #1430: a megőrzött eredeti (és a sorszámozott pillanatképek) a képpel
    # együtt mennek. Előbb ők költöznek, utána a kép — ha a kísérők
    # költöztetése bukik, a kép el sem indul; ha a kép átnevezése bukik, a
    # `originals_follow` visszateszi őket.
    with originals_follow(path, target):
        path.rename(target)

    if has_ini:
        try:
            update_document(
                ini_path,
                lambda document: document.with_renamed_section(path.name, new_name),
                backup=True,
            )
        except ValueError as error:
            # A `with_renamed_section` ütközést jelez: a célnév szekcióját a
            # fenti előellenőrzés óta (az újrajátszás friss dokumentumában)
            # elfoglalta valaki. Kifelé a szerződés szerinti FileExistsError
            # marad, de a fájl EKKOR MÁR át van nevezve — ezt az üzenetnek
            # meg kell mondania, különben a felhasználó nem tudja, mit tegyen.
            raise FileExistsError(
                f"A fájl átnevezése megtörtént ({target}), de a .picasa.ini "
                f"bejegyzése nem követte: a(z) {new_name!r} szekciónevet egy "
                f"párhuzamos író (pl. a futó Picasa) időközben elfoglalta itt: "
                f"{ini_path}. A kép beállításai a(z) {path.name!r} szekcióban "
                f"maradtak — onnan kézzel átmásolhatók."
            ) from error

    return target


def _validate_name(name: str) -> None:
    if not name or name in (".", "..") or "/" in name or "\\" in name:
        raise ValueError(f"Érvénytelen fájlnév: {name!r}")


@dataclass(frozen=True)
class RenameItem:
    """Egy tömegesen átnevezendő fájl bemenete (#366): az útvonal mellett a
    dátum-/felbontás-utótaghoz szükséges, MÁR ISMERT (indexelt) metaadat —
    a hívó (a controller) tölti a `PhotoRecord`-ból, nincs újra lemez-/
    EXIF-olvasás itt."""

    path: Path
    date: str | None = None  # ISO dátum eleje (pl. a `taken_at` első 10 karaktere)
    width: int | None = None
    height: int | None = None


def _build_stem(
    base_name: str, item: RenameItem, *, include_date: bool, include_size: bool
) -> str:
    """Az alapnév + opcionális dátum-/felbontás-utótag — a `rename.fen`
    "Include in filename: Date / Image resolution" jelölőnégyzetei.
    Sorszám NÉLKÜL (azt a `preview_name` teszi hozzá) — hiányzó metaadatnál
    (nincs dátum/felbontás) a megfelelő utótag néma kihagyással marad el."""
    parts = [base_name]
    if include_date and item.date:
        parts.append(item.date[:10])
    if include_size and item.width and item.height:
        parts.append(f"{item.width}x{item.height}")
    return " ".join(parts)


def preview_name(
    base_name: str,
    item: RenameItem,
    *,
    include_date: bool = False,
    include_size: bool = False,
    sequence: int = 0,
    ext: str | None = None,
) -> str:
    """A végleges fájlnév — élő előnézethez és a tényleges átnevezéshez is
    ez számolja ki. `sequence=0` az első fájl (nincs sorszám-utótag), `1`,
    `2`, … a Picasa-mintájú `név-1`, `név-2`, … folytatás. `ext` hiányában
    (élő előnévet-híváskor) `item.path.suffix`-ot használ."""
    stem = _build_stem(base_name, item, include_date=include_date, include_size=include_size)
    if sequence > 0:
        stem = f"{stem}-{sequence}"
    extension = ext if ext is not None else item.path.suffix
    return f"{stem}{extension}"


def _check_batch_collisions(items: Sequence[RenameItem], names: Sequence[str]) -> None:
    """Előellenőrzés a teljes köteg célneveire — MIELŐTT bármelyik fájl
    átnevezése elindulna: sem egymással, sem a mappa meglévő tartalmával
    (a saját jelenlegi nevét kivéve) nem ütközhetnek. Szándékosan a köteg
    tagjainak JELENLEGI nevével való ütközést is elutasítja (nem csak a
    lemezen lévő, kötegen kívüli fájlokét) — enélkül a végrehajtás
    sorrendjétől függne, hogy egy köztes állapotban a cél még foglalt-e."""
    if len(set(names)) != len(names):
        raise FileExistsError(
            "A tömeges átnevezés ütköző célneveket eredményezne — "
            "semmi sem lett átnevezve."
        )
    folder_originals: dict[Path, set[str]] = defaultdict(set)
    for item in items:
        folder_originals[item.path.parent].add(item.path.name)

    for item, name in zip(items, names, strict=True):
        if name == item.path.name:
            continue  # nincs tényleges változás — nem ütközés önmagával
        if name in folder_originals[item.path.parent]:
            raise FileExistsError(
                f"A(z) {name!r} célnév ütközik egy másik, a kötegben lévő "
                "fájl jelenlegi nevével — semmi sem lett átnevezve."
            )
        target = item.path.parent / name
        if target.exists():
            raise FileExistsError(f"A célnév már foglalt: {target}")


def rename_photos_many(
    items: Sequence[RenameItem],
    base_name: str,
    *,
    include_date: bool = False,
    include_size: bool = False,
) -> list[Path]:
    """Tömeges átnevezés a `rename.fen` szerint (#366): a kijelölt fájlok
    egyetlen alapnevet kapnak (+ opcionális dátum-/felbontás-utótag),
    Picasa-mintájú sorszámozással (`név`, `név-1`, `név-2`…). A teljes köteg
    célneveit ELŐRE ellenőrizzük ütközésre — vagy az egész köteg átnevezhető,
    vagy egyik fájl sem mozdul. Fájlonként az egyfájlos `rename_photo`-t
    hívja (ini-átvitel ugyanazon az úton).

    Raises:
        ValueError: érvénytelen alapnév.
        FileExistsError: ütköző célnevek (a kötegen belül vagy a mappa
            meglévő tartalmával).
        FileNotFoundError, IniConflictError: ld. `rename_photo`.
    """
    if not items:
        return []
    _validate_name(base_name)
    names = [
        preview_name(
            base_name, item, include_date=include_date, include_size=include_size,
            sequence=i,
        )
        for i, item in enumerate(items)
    ]
    _check_batch_collisions(items, names)

    results: list[Path] = []
    for item, name in zip(items, names, strict=True):
        if name == item.path.name:
            results.append(item.path)  # no-op: a név ténylegesen nem változik
        else:
            results.append(rename_photo(item.path, name))
    return results
