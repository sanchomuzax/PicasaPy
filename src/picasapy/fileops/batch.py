"""Kötegelt másolás/áthelyezés ÜTKÖZÉS-KEZELÉSSEL (#457, 2. pont).

Az eredeti Picasa névütközésnél nem döntött a felhasználó helyett: megkérdezte
(`CThumbUI::MoveFilesToAlbumFolder::2` és `::5` — a MÁSOLÁS és az ÁTHELYEZÉS
UGYANAZT a párbeszédet kapta):

    „Ez a mappa már tartalmaz azonos nevű fájlokat.
     Átnevezi vagy átugorja ezeket?"

    [Másodpéldányok átnevezése]  [Másodpéldányok kihagyása]

Ez a modul a döntés VÉGREHAJTÁSA — a kérdést a felület teszi fel. A hívó
előbb a `conflicting_names()`-szel megnézi, van-e egyáltalán ütközés (csak
akkor kérdez), majd a választott házirenddel futtatja a műveletet.

**Az átnevezés sémája (`név-1.jpg`) SAJÁT DÖNTÉS**, nem az eredetiből
átvett: a Picasa sztring-táblájában nincs rá bejegyzés (a fájlnév-utótag nem
fordítható szöveg, kódban készült). A projekt máshol — a másolás és az
exportálás magjában — már ezt a sémát használja, ezért maradunk nála: egy
programon belül kétféle séma zavaróbb lenne, mint az eredetitől való eltérés.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path

from picasapy.fileops.copy import copy_photo
from picasapy.ini import IniConflictError, IniSaveError
from picasapy.fileops.move import move_photo
from picasapy.fileops.originals import originals_slot_free
from picasapy.fileops.rename import rename_photo

#: A két házirend, ahogy az eredeti két gombja adta.
RENAME = "rename"
SKIP = "skip"


@dataclass(frozen=True)
class BatchResult:
    """Egy kötegelt művelet eredménye.

    `done` a (forrás, cél) párok a ténylegesen átvitt fájlokról, `skipped` a
    kihagyottak (a `SKIP` házirend miatt), `failed` pedig a (forrás, hiba)
    párok. A hívó ebből tud EGYETLEN összegzést mutatni — az eredeti is
    darabszámmal jelentett, nem fájlonkénti ablakkal (#459).
    """

    done: tuple[tuple[Path, Path], ...] = ()
    skipped: tuple[Path, ...] = ()
    failed: tuple[tuple[Path, str], ...] = ()


def conflicting_names(paths: Iterable[Path], dest_folder: Path) -> tuple[Path, ...]:
    """Azok a források, amelyeknek a NEVE már létezik a célmappában.

    Csak akkor kérdezünk a felhasználótól, ha ez nem üres — az eredeti sem
    kérdezett fölöslegesen.
    """
    dest = Path(dest_folder)
    return tuple(
        Path(path) for path in paths if (dest / Path(path).name).exists()
    )


def copy_photos(
    paths: Sequence[Path],
    dest_folder: Path,
    policy: str = RENAME,
    progress: Callable[[int, int], None] | None = None,
) -> BatchResult:
    """Fotók másolása a célmappába, a `policy` szerint (#457).

    `RENAME`: az ütköző nevek új nevet kapnak (`copy_photo` intézi);
    `SKIP`: az ütköző fájlok kimaradnak, a többi átmegy.

    `progress(kész, összes)`: fájlonként hívódik — az eredeti is számlálót
    mutatott (`CAcquireUI::copying` = „Copying %1$d of %2$d files"), nem
    csak egy pörgő sávot.
    """
    return _run(paths, dest_folder, policy, copy_photo, progress)


def move_photos(
    paths: Sequence[Path],
    dest_folder: Path,
    policy: str = RENAME,
    progress: Callable[[int, int], None] | None = None,
) -> BatchResult:
    """Fotók áthelyezése a célmappába, a `policy` szerint (#457).

    Az eredeti a KÉPEKRE ugyanazt a rename/skip párbeszédet adta, mint
    másolásnál (`::5`); a MAPPA áthelyezését viszont ütközéskor elutasította
    (`CThumbUI::MoveFolderExists`) — az más művelet, nem ez.
    """
    return _run(paths, dest_folder, policy, _move_with_rename, progress)


def _move_with_rename(path: Path, dest_folder: Path) -> Path:
    """`move_photo` ütközés-tűrő változata.

    A `move_photo` szándékosan `FileExistsError`-t dob (sosem ír felül
    csendben), ezért az átnevezéses ág előbb SZABAD nevet keres, a forrást a
    `rename_photo`-val nevezi át — így a `.picasa.ini` szekció is vele
    fordul —, és csak utána mozgat.
    """
    if not (dest_folder / path.name).exists():
        return move_photo(path, dest_folder)
    free_name = _free_name(path, dest_folder)
    return move_photo(rename_photo(path, free_name), dest_folder)


def _free_name(path: Path, dest_folder: Path) -> str:
    """`név-1.jpg`-séma, ami MINDKÉT mappában szabad.

    A célban azért, hogy legyen hova mozgatni; a forrásban azért, mert az
    átnevezés ott történik (a testvér fájlokat nem üthetjük el).

    #1430: a MEGŐRZÖTT EREDETI helyének is szabadnak kell lennie mindkét
    mappában. Az eredeti a képpel együtt költözik, tehát egy korábbi
    költöztetés árván maradt eredetije foglalttá teszi a pótnevet — ha ezt
    nem néznénk, a köteg egy elkerülhető hibával állna meg ennél a fájlnál.
    """
    counter = 1
    while True:
        candidate = f"{path.stem}-{counter}{path.suffix}"
        if (
            not (dest_folder / candidate).exists()
            and not (path.parent / candidate).exists()
            and originals_slot_free(dest_folder, candidate)
            and originals_slot_free(path.parent, candidate)
        ):
            return candidate
        counter += 1


def _run(paths, dest_folder, policy, operation, progress=None) -> BatchResult:
    if policy not in (RENAME, SKIP):
        raise ValueError(f"Ismeretlen ütközés-házirend: {policy!r}")
    dest = Path(dest_folder)
    done: list[tuple[Path, Path]] = []
    skipped: list[Path] = []
    failed: list[tuple[Path, str]] = []
    items = [Path(raw) for raw in paths]
    total = len(items)
    for index, path in enumerate(items, start=1):
        if policy == SKIP and (dest / path.name).exists():
            skipped.append(path)
        else:
            try:
                done.append((path, operation(path, dest)))
            except (OSError, ValueError, IniSaveError, IniConflictError) as error:
                # #301/#459: egy hibás fájl nem állíthatja meg a köteget — a
                # hívó a végén EGY összegzést mutat, nem fájlonkénti ablakot
                failed.append((path, str(error)))
        # a kihagyott és a hibás fájl is HALAD: a felhasználó a számlálóból
        # azt akarja tudni, hol tart a művelet, nem azt, hány sikerült
        if progress is not None:
            progress(index, total)
    return BatchResult(tuple(done), tuple(skipped), tuple(failed))


__all__ = [
    "RENAME",
    "SKIP",
    "BatchResult",
    "conflicting_names",
    "copy_photos",
    "move_photos",
]
