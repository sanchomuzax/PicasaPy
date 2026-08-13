"""Mappa áthelyezése a KÍSÉRŐFÁJLOKKAL együtt (#457).

Az eredeti Picasa `Folder::ID_MOVEFOLDER` parancsa („Mappa áthelyezése…")
egy egész mappát vitt át egy másik mappa alá — a tartalmával együtt. A
hibaüzenetei megmondják, mire figyelt:

    CThumbUI::MoveFolderExists   „Ilyen nevű mappa már létezik a célmappában"
    CThumbUI::MoveFolderSysPath  „Rendszermappa nem helyezhető át"
    CThumbUI::MoveFolderError    „A mappa áthelyezése egy hiba miatt nem
                                  sikerült. (Hibakód: %d)"

Nálunk ehhez jön még egy fontos szempont, ami a Picasánál nem volt kérdés:
a **`.picasa.ini` az igazságforrás**. Egy mappa áthelyezésekor tehát a
kísérőfájlnak vele kell mennie — különben a képek elveszítenék a
feliratukat, a címkéiket és az arc-hozzárendeléseiket. Mivel az ini a
mappában él, a mappa mozgatása ezt magától megoldja; a modul dolga az,
hogy **ne** csak a képeket vigye át (ezért mozgatunk könyvtárat, nem
fájlonként), és hogy a mozgatás vagy TELJESEN sikerüljön, vagy sehogy.
"""

from __future__ import annotations

import shutil
from pathlib import Path

#: A rendszer-könyvtárak, amiket sosem mozgatunk. Az eredeti is külön
#: hibaüzenetet adott rá („Unable to Move a System Path") — nem hagyta,
#: hogy a felhasználó lábon lője magát.
#:
#: A lista MINDKÉT platformot fedi: a program Windowson is fut, és ott a
#: `/etc`-hez hasonló POSIX-utak nem léteznek — a `C:\Windows` viszont
#: éppúgy védendő, mint linuxon a `/usr`.
_SYSTEM_PATHS = (
    "/",
    "/bin",
    "/boot",
    "/dev",
    "/etc",
    "/home",
    "/lib",
    "/opt",
    "/proc",
    "/root",
    "/run",
    "/sbin",
    "/srv",
    "/sys",
    "/tmp",
    "/usr",
    "/var",
    # Windows
    "C:\\",
    "C:\\Windows",
    "C:\\Program Files",
    "C:\\Program Files (x86)",
    "C:\\Users",
    "C:\\ProgramData",
)


class FolderMoveError(RuntimeError):
    """A mappa áthelyezése nem sikerült — a forrás érintetlen."""


def is_system_path(folder: Path) -> bool:
    """Rendszer-könyvtár-e (az eredeti `MoveFolderSysPath` esete).

    A felhasználó saját home-ja NEM az: azt szabad mozgatni-e, arról a
    szülője dönt. A `/home` maga viszont igen."""
    resolved = Path(folder).resolve()
    # a meghajtó gyökere (linuxon "/", windowson "C:\\") sosem mozgatható
    if resolved == resolved.parent:
        return True
    known = {item.casefold() for item in _SYSTEM_PATHS}
    if str(resolved).casefold().rstrip("\\/") in {
        item.rstrip("\\/") for item in known
    }:
        return True
    # a home-könyvtár maga sem mozgatható (a benne lévő mappák igen)
    return resolved == Path.home().resolve()


def move_folder(folder: str | Path, dest_parent: str | Path) -> Path:
    """A mappa áthelyezése a `dest_parent` alá, a teljes tartalmával.

    A `.picasa.ini` és minden más kísérőfájl vele megy: könyvtárat
    mozgatunk, nem fájlokat válogatunk.

    Hibák (mind `FolderMoveError`, emberi nyelvű üzenettel — a hívó ezt
    mutatja meg, nem nyers kivételt):

    * a forrás nem létezik / nem könyvtár;
    * a forrás rendszer-könyvtár;
    * a célban már van ilyen nevű mappa;
    * a cél a forráson BELÜL van (magába nem mozgatható);
    * bármilyen egyéb fájlrendszer-hiba.
    """
    source = Path(folder)
    target_parent = Path(dest_parent)

    if not source.is_dir():
        raise FolderMoveError(f"A mappa nem található: {source}")
    if is_system_path(source):
        raise FolderMoveError("Rendszermappa nem helyezhető át.")
    if not target_parent.is_dir():
        raise FolderMoveError(f"A célmappa nem található: {target_parent}")

    resolved_source = source.resolve()
    resolved_parent = target_parent.resolve()
    if resolved_parent == resolved_source.parent:
        raise FolderMoveError("A mappa már ebben a célmappában van.")
    if resolved_source == resolved_parent or resolved_source in resolved_parent.parents:
        # magába (vagy a saját alkönyvtárába) mozgatás — a shutil ilyenkor
        # végtelen másolásba futna
        raise FolderMoveError("A mappa nem helyezhető át önmagába.")

    target = target_parent / source.name
    if target.exists():
        raise FolderMoveError(
            "Ilyen nevű mappa már létezik a célmappában."
        )

    try:
        shutil.move(str(source), str(target))
    except OSError as error:
        raise FolderMoveError(
            f"A mappa áthelyezése egy hiba miatt nem sikerült: {error}"
        ) from error
    return target


__all__ = ["FolderMoveError", "is_system_path", "move_folder"]
