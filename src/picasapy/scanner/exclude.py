"""FRExcludeFolders.txt olvasás és mappa-kizárás (#145).

Eredeti Picasa-jelentés: `%LocalAppData%\\Google\\Picasa2Albums\\
FRExcludeFolders.txt` — soronként egy abszolút útvonal, azok a mappák,
amelyeket a Picasa az **arcfelismerésből** zár ki (ld.
`docs/specs/pmp-database.md`). Az 1. fázisban (MVP: kezelő + néző) még nincs
arcfelismerés, ezért a PicasaPy egyelőre a teljes indexelésből zárja ki
ezeket a mappákat és az alfáikat — ez szándékos, ideiglenes egyszerűsítés;
ha megérkezik az arcfelismerés-fázis (3. fázis), érdemes újragondolni, hogy
a kizárás csak az arcfelismerést érintse, a fájlok/album-tartalom
indexelését ne.

Élesben (MEMORY 2026-07-16) a fájlnév kisbetűsen is előfordul
(`frexcludefolders.txt`) — a keresés kis-nagybetű-független.
"""

from __future__ import annotations

from pathlib import Path

from .config_files import find_config_file, read_path_list

EXCLUDE_FOLDERS_NAME = "FRExcludeFolders.txt"


def read_exclude_folders(path: str | Path) -> tuple[str, ...]:
    """A kizárt mappák listájának olvasása (soronként egy abszolút útvonal).
    A hiányzó fájl üres listát jelent — nincs kizárt mappa."""
    return read_path_list(path)


def find_exclude_folders_file(directory: str | Path) -> Path | None:
    """A `FRExcludeFolders.txt` kis-nagybetű-független megkeresése az adott
    könyvtárban."""
    return find_config_file(directory, EXCLUDE_FOLDERS_NAME)


def is_excluded(folder: str | Path, exclude_roots: tuple[str | Path, ...]) -> bool:
    """Igaz, ha a `folder` maga vagy bármely őse szerepel a kizárt
    gyökerek között (a kizárás az alfákra is érvényes)."""
    if not exclude_roots:
        return False
    resolved = Path(folder).resolve()
    for root in exclude_roots:
        resolved_root = Path(root).resolve()
        if resolved == resolved_root or resolved_root in resolved.parents:
            return True
    return False
