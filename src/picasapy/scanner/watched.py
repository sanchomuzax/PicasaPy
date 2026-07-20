"""WatchedFolders.txt olvasás — soronként egy abszolút útvonal (Scan Always).

Az eredeti (Windows-os) Picasa fájlját is olvassuk importnál: CRLF, BOM és
backslash-útvonalak tűrése kötelező. A hiányzó fájl üres listát jelent
(nincs figyelt mappa), nem hibát.

Élesben (#145 / MEMORY 2026-07-16) a fájlnév kisbetűsen is előfordul
(`watchedfolders.txt`) — a `find_watched_folders_file` ezt kis-nagybetű-
függetlenül keresi meg egy adott könyvtárban.
"""

from __future__ import annotations

from pathlib import Path

from .config_files import find_config_file, read_path_list

WATCHED_FOLDERS_NAME = "WatchedFolders.txt"


def read_watched_folders(path: str | Path) -> tuple[str, ...]:
    return read_path_list(path)


def write_watched_folders(path: str | Path, folders: tuple[str, ...]) -> None:
    """A figyelt mappák listájának mentése (Picasa-formátum: soronként egy
    abszolút útvonal, UTF-8)."""
    file_path = Path(path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(
        "".join(f"{folder}\n" for folder in folders), encoding="utf-8"
    )


def find_watched_folders_file(directory: str | Path) -> Path | None:
    """A `WatchedFolders.txt` kis-nagybetű-független megkeresése az adott
    könyvtárban (pl. importnál a Picasa2Albums mappában)."""
    return find_config_file(directory, WATCHED_FOLDERS_NAME)
