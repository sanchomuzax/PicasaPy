"""Első indítás: mit olvassunk be (#449).

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

**A linuxos leképezés.** A „teljes számítógép" itt NEM a teljes
fájlrendszer: csatolt hálózati meghajtók, konténerek és rendszermappák
miatt az kifejezetten rossz ötlet. A tág választás nálunk a
**home-könyvtár**; a szűk pedig az XDG szerinti Képek/Dokumentumok/Asztal.

A varázsló kihagyható (`skipinitialscan`) — a Picasában is volt erre kulcs.
"""

from __future__ import annotations

import os
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


def wide_folders(home: Path | None = None) -> tuple[str, ...]:
    """A tág választás: a home-könyvtár (a „teljes gép" linuxos megfelelője)."""
    base = Path(home) if home is not None else Path.home()
    return (str(base),) if base.is_dir() else ()


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
    "narrow_folders",
    "needs_initial_scan",
    "wide_folders",
]
