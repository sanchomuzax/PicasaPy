r"""Első indítás: mit olvassunk be (#449).

A Picasa az első indításkor **egyetlen kérdést** tett fel, mielőtt bármit
csinált volna (`CInitialScanDialog`):

- „Search my whole computer for pictures", vagy
- **„Keresés csak a Dokumentumok és a Képek mappában, valamint az
  asztalon"** (Mac-en az iPhoto-könyvtárral kiegészülve).

Két dolog látszik a párbeszéd felépítéséből (#449, 2026-08-12): **csak két
választás volt** — nem kért mappalistát, nem nyitott fát —, és **egyetlen
`ok` gomb**, Mégse nélkül: az első indításból nem lehetett kilépni anélkül,
hogy eldöntötted volna, hiszen enélkül a program üres. A finomhangolás
utána, a Mappakezelőben történik.

**A leképezés (#1167).** Az eredeti „teljes gép" ága a meghajtó-
gyökereket veszi (`0x004fdd10`, `GetLogicalDrives` — a valódi mintában
`+C:\ +L:\ +E:\ +D:\`). Nálunk: Windowson a meghajtók; Linuxon a
home + a /media és /run/media alatti FELHASZNÁLÓI csatolások. A /mnt
szándékosan kimarad: ott ül a tulajdonos élő családi NAS-a (csak-olvasás,
napló-korláttal) — azt első indításkor beolvasni veszélyes volna. A szűk
választás az XDG szerinti Dokumentumok/Képek/Asztal (az eredeti
`WinSystemPaths::MyDocuments`/`::MyPictures`/`::Desktop` megfelelője).

A varázsló kihagyható (`skipinitialscan`) — a Picasában is volt erre kulcs.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

#: A két választás azonosítója (a QML és a beállítás is ezt használja).
SCAN_NARROW = "narrow"
SCAN_WIDE = "wide"

#: A varázsló kihagyása — az eredeti `skipinitialscan` kulcs megfelelője.
SKIP_INITIAL_SCAN_KEY = "startup/skipinitialscan"

#: A szűk halmaz XDG-változói és a visszaesés-nevek. A sorrend a Picasa
#: felsorolását követi (Dokumentumok · Képek · Asztal); a beolvasásnál a
#: sorrend nem számít, a felületi szövegben viszont igen.
_NARROW_DIRS: tuple[tuple[str, str], ...] = (
    ("XDG_DOCUMENTS_DIR", "Documents"),
    ("XDG_PICTURES_DIR", "Pictures"),
    ("XDG_DESKTOP_DIR", "Desktop"),
)


def _resolve(home: Path, variable: str, fallback: str) -> Path:
    """Az XDG-változó értéke, vagy a szokásos angol nevű mappa a home-ban.

    Az XDG-változó abszolút útvonalat ad; ha relatív (elvben nem fordul
    elő, de sérült konfigurációban igen), a home-hoz mérjük.
    """
    value = os.environ.get(variable, "").strip()
    if not value:
        return home / fallback
    path = Path(value).expanduser()
    return path if path.is_absolute() else home / path


def narrow_folders(home: Path | None = None) -> tuple[str, ...]:
    """A szűk halmaz LÉTEZŐ mappái (Dokumentumok · Képek · Asztal).

    A nem létező mappákat kihagyjuk: egy üres, sosem használt `~/Desktop`
    felvétele csak zajt vinne a bal hasábba.
    """
    base = Path(home) if home is not None else Path.home()
    found = []
    for variable, fallback in _NARROW_DIRS:
        candidate = _resolve(base, variable, fallback)
        if candidate.is_dir():
            found.append(str(candidate))
    return tuple(found)


#: a Linux-csatolások szülői — a `folder_tree_controller` gyökereinek mintája
_MEDIA_PARENTS = (Path("/media"), Path("/run/media"))


def _platform() -> str:
    """A futó platform — külön függvény, hogy a teszt helyettesíthesse."""
    return sys.platform


def wide_folders(home: Path | None = None) -> tuple[str, ...]:
    """A tág választás kötetei (#1167) — ld. a modul-docstring leképezését."""
    if _platform() == "win32":
        from .folder_tree_controller import _windows_meghajtok

        return tuple(str(utvonal) for _nev, utvonal in _windows_meghajtok())
    base = Path(home) if home is not None else Path.home()
    kotetek = [str(base)] if base.is_dir() else []
    felhasznalo = base.name
    for szulo in _MEDIA_PARENTS:
        try:
            for csatolas in (szulo / felhasznalo).iterdir():
                if csatolas.is_dir() and str(csatolas) not in kotetek:
                    kotetek.append(str(csatolas))
        except OSError:
            continue
    return tuple(kotetek)


def _installation_count() -> int:
    """A felderített korábbi telepítések száma — külön függvény, hogy a
    teszt helyettesíthesse (a valódi felderítő a `scanner.discovery`, #146)."""
    from picasapy.scanner import discover_installations

    return len(discover_installations())


def migration_detected() -> bool:
    """A MIGRÁCIÓS szövegkészlet kell-e (`Text1`) — az eredetiben
    `migrációs jelző = találtunk korábbi telepítést` (`0x0040d450`).

    Hibatűrő: a felderítés bukása nem akadályozhatja az indulást — tiszta
    telepítésként megy tovább."""
    try:
        return _installation_count() > 0
    except Exception:
        return False


def folders_for_choice(choice: str, home: Path | None = None) -> tuple[str, ...]:
    """A választáshoz tartozó mappák; ismeretlen értéknél a SZŰK halmaz.

    A szűk a „biztonságos" út — ismeretlen bemenetre nem a teljes
    home-könyvtárat kezdjük el beolvasni.
    """
    if choice == SCAN_WIDE:
        return wide_folders(home)
    return narrow_folders(home)


def needs_initial_scan(watched: tuple[str, ...], skip: bool) -> bool:
    """Fel kell-e tenni a kérdést indításkor?

    Csak akkor, ha MÉG NINCS figyelt mappa (tehát a program üres lenne), és
    a felhasználó nem kérte a varázsló kihagyását.
    """
    return not skip and not watched


__all__ = [
    "SCAN_NARROW",
    "SCAN_WIDE",
    "SKIP_INITIAL_SCAN_KEY",
    "folders_for_choice",
    "migration_detected",
    "narrow_folders",
    "needs_initial_scan",
    "wide_folders",
]
