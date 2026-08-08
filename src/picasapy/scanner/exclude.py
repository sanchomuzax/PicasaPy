"""FRExcludeFolders.txt olvasás/írás — mappa-kizárás az ARCFELISMERÉSBŐL
(#145, pontosítva #449-ben).

Eredeti Picasa-jelentés: `%LocalAppData%\\Google\\Picasa2Albums\\
FRExcludeFolders.txt` — soronként egy abszolút útvonal, azok a mappák
(és alfáik), amelyeket a Picasa Mappakezelőjében a felhasználó a három
scan-állapottól (Scan Always / Scan Once / Remove from Picasa) FÜGGETLEN,
NEGYEDIK kapcsolóval kizárt az arcfelismerésből — ld.
`docs/specs/feature-map.md`.

**FONTOS — ezt korábban tévesen dokumentáltuk itt**: a kulcs KIZÁRÓLAG
az arcfelismerést érinti, az általános indexelést (fotók/albumok
beolvasását) NEM — a Picasában a kizárt mappa fotói továbbra is
megjelennek a könyvtárban, csak arc-régiót/névcímkét nem kapnak. A
PicasaPy ezt a fájlt korábban egyáltalán nem használta (csak olvasó
függvények léteztek, hívó nélkül); a #449-es jegy vezette be az írás-
oldalt és a tényleges (bár egyelőre csak SZÁNDÉKOT rögzítő, ld.
`app/library_controller.py`) bekötést, mert arcfelismerés-motor még
nincs a projektben.

Élesben (MEMORY 2026-07-16) a fájlnév kisbetűsen is előfordul
(`frexcludefolders.txt`) — a keresés kis-nagybetű-független.
"""

from __future__ import annotations

from pathlib import Path

from .config_files import find_config_file, read_path_list

EXCLUDE_FOLDERS_NAME = "FRExcludeFolders.txt"


def read_exclude_folders(path: str | Path) -> tuple[str, ...]:
    """Az arcfelismerésből kizárt mappák listája (soronként egy abszolút
    útvonal). A hiányzó fájl üres listát jelent — nincs kizárt mappa."""
    return read_path_list(path)


def write_exclude_folders(path: str | Path, folders: tuple[str, ...]) -> None:
    """Az arcfelismerésből kizárt mappák listájának mentése (Picasa-
    formátum: soronként egy abszolút útvonal, UTF-8) — a
    `write_watched_folders` mintájára (`scanner/watched.py`)."""
    file_path = Path(path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(
        "".join(f"{folder}\n" for folder in folders), encoding="utf-8"
    )


def find_exclude_folders_file(directory: str | Path) -> Path | None:
    """A `FRExcludeFolders.txt` kis-nagybetű-független megkeresése az adott
    könyvtárban."""
    return find_config_file(directory, EXCLUDE_FOLDERS_NAME)


def is_excluded(folder: str | Path, exclude_roots: tuple[str | Path, ...]) -> bool:
    """Igaz, ha a `folder` maga vagy bármely őse szerepel a kizárt
    gyökerek között (a kizárás az alfákra is érvényes). Ez a függvény csak
    az arcfelismerés-kapcsoló állapotát dönti el (#449) — az általános
    indexelésre NINCS hatással."""
    if not exclude_roots:
        return False
    resolved = Path(folder).resolve()
    for root in exclude_roots:
        resolved_root = Path(root).resolve()
        if resolved == resolved_root or resolved_root in resolved.parents:
            return True
    return False
