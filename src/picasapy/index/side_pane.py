"""#1601: a bal hasáb két ini-alapú gyűjteménye EGYETLEN söpréssel.

Az **Emberek** (#26) és a **Projektek** (#1029) gyűjtemény ugyanabból a
forrásból él: a `has_ini=1` mappák `.picasa.ini`-jéből. Külön hívva
mindkettő végigolvasta az EGÉSZ halmazt — a lemezmunka tehát kétszeres
volt. Ez a modul a kettőt egyetlen `sweep_folder_inis` menetbe fogja
(ld. a `folder_ini.py` mérési tábláját).

A vezérlő (`app/library_controller.py`) ezt hívja, és lehetőleg
HÁTTÉRSZÁLON: az induláskori ini-söprés a felület szálán blokkolt.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass

from .folder_ini import sweep_folder_inis
from .people import FaceDataCollector, PersonRecord, people_in_index
from .project_folders import (
    ProjectFolder,
    ProjectFolderCollector,
    project_folders_from_paths,
)


@dataclass(frozen=True)
class SidePaneCollections:
    """A hasáb két ini-alapú gyűjteménye — együtt, egy söprésből.

    Fagyasztott, egyszerű adathordozó: háttérszálról a felület szálára is
    biztonságosan átadható (nincs benne se `Connection`, se QObject)."""

    people: tuple[PersonRecord, ...]
    project_folders: tuple[ProjectFolder, ...]


def load_side_pane_collections(conn: sqlite3.Connection) -> SidePaneCollections:
    """Emberek + Projektek egyetlen `.picasa.ini`-söpréssel.

    Az eredménye elemről elemre AZONOS a `people_in_index(conn)` és a
    `project_folders(conn)` külön hívásáéval — csak feleannyi lemezmunkával
    (ezt teszt rögzíti: `tests/index/test_egy_ini_sopres_1601.py`)."""
    faces = FaceDataCollector()
    projects = ProjectFolderCollector()
    sweep_folder_inis(conn, (faces, projects))
    return SidePaneCollections(
        people=people_in_index(conn, tuple(faces.rows)),
        project_folders=project_folders_from_paths(conn, projects.paths),
    )


__all__ = ["SidePaneCollections", "load_side_pane_collections"]
