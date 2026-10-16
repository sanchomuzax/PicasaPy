"""#1601/#4589: a bal hasáb ini-alapú gyűjteményei EGYETLEN söpréssel.

Az **Emberek** (#26), **Projektek** (#1029) és az **egyéni
gyűjtemények** (#4589) ugyanabból a forrásból élnek: a `has_ini=1`
mappák `.picasa.ini`-jéből. Ez a modul egyetlen `sweep_folder_inis`
menetbe fogja őket (ld. a `folder_ini.py` mérési tábláját).

A vezérlő (`app/library_controller.py`) ezt hívja, és lehetőleg
HÁTTÉRSZÁLON: az induláskori ini-söprés a felület szálán blokkolt.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass

from .custom_collection_folders import CustomCollectionFolderCollector
from .folder_ini import sweep_folder_inis
from .people import FaceDataCollector, PersonRecord, people_in_index
from .project_folders import (
    ProjectFolder,
    ProjectFolderCollector,
    project_folders_from_paths,
)


@dataclass(frozen=True)
class SidePaneCollections:
    """A hasáb ini-alapú gyűjteményei — együtt, egy söprésből.

    Fagyasztott, egyszerű adathordozó: háttérszálról a felület szálára is
    biztonságosan átadható (nincs benne se `Connection`, se QObject)."""

    people: tuple[PersonRecord, ...]
    project_folders: tuple[ProjectFolder, ...]
    custom_collection_folders: tuple[tuple[str, tuple[str, ...]], ...] = ()


def load_side_pane_collections(conn: sqlite3.Connection) -> SidePaneCollections:
    """Emberek + Projektek + egyéni gyűjtemények egyetlen söpréssel.

    Az eredménye azonos a két korábbi gyűjtemény külön lekérdezésével, és
    ugyanebből a menetből megadja az egyéni `P2category`-értékek mappáit.
    A söprés darabszámát teszt rögzíti:
    `tests/index/test_egy_ini_sopres_1601.py`."""
    faces = FaceDataCollector()
    projects = ProjectFolderCollector()
    custom_collections = CustomCollectionFolderCollector()
    sweep_folder_inis(conn, (faces, projects, custom_collections))
    return SidePaneCollections(
        people=people_in_index(conn, tuple(faces.rows)),
        project_folders=project_folders_from_paths(conn, projects.paths),
        custom_collection_folders=custom_collections.result(),
    )


__all__ = ["SidePaneCollections", "load_side_pane_collections"]
