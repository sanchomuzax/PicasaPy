"""#1029: a bal hasáb **Projektek** gyűjteménye — a `P2category=Projects
(internal)` mappák.

Nincs hozzá önálló SQL-oszlop (a `schema.py` forró fájl, séma-bővítést csak
az integrátor oszthat ki — ld. `people.py` modul-docstring): a besorolás
DIREKT ini-olvasással kerül elő, a `queries._album_suggestions` és a
`people._iter_face_data` bevált mintáját követve — a `folders` tábla
`has_ini=1` sorain végigmenve.

**Miért ez a jó választás itt, és nem csak kényelem:** a séma-oszlopot egy
migráció után a mappánkénti scan-állapot (`folder_scan_state`) miatt csak
TELJES újraindexelés töltené fel — a felhasználó addig továbbra sem látna
semmit a Projektek alatt. Az ini-olvasás a meglévő indexen is AZONNAL
helyes listát ad. A darabszám viszont az indexből jön (egy `GROUP BY`),
mert az a mappa fotóit számolja, nem az ini sorait.
"""

from __future__ import annotations

import sqlite3
from collections.abc import Iterable
from dataclasses import dataclass

from picasapy.ini import IniDocument, is_projects_category, read_folder_category

from .folder_ini import sweep_folder_inis


@dataclass(frozen=True)
class ProjectFolder:
    """Egy projekt-mappa a hasábnak: útvonal, megjelenítendő név, darabszám."""

    path: str
    name: str
    photo_count: int


class ProjectFolderCollector:
    """#1601: a `sweep_folder_inis` fogyasztója a Projektek gyűjteményhez.

    Csak az ÚTVONALAKAT gyűjti — a darabszám az indexből jön, egyetlen
    `GROUP BY`-jal (`_photo_counts`), nem ini-nként. Külön osztály, mert a
    söprést megosztjuk az Emberek gyűjteménnyel (`index/side_pane.py`)."""

    def __init__(self) -> None:
        self.paths: list[str] = []

    def __call__(self, folder_path: str, document: IniDocument) -> None:
        if is_projects_category(read_folder_category(document)):
            self.paths.append(folder_path)


def project_folders_from_paths(
    conn: sqlite3.Connection, paths: Iterable[str]
) -> tuple[ProjectFolder, ...]:
    """A begyűjtött projekt-útvonalakból a hasáb sorai, névre rendezve.

    Az ini-olvasás itt már megtörtént (`ProjectFolderCollector`); ez a
    függvény csak az index-beli darabszámot teszi mellé."""
    counts = _photo_counts(conn)
    folders = [
        ProjectFolder(
            path=path,
            name=_display_name(path),
            photo_count=counts.get(path, 0),
        )
        for path in paths
    ]
    return tuple(sorted(folders, key=lambda folder: folder.name.casefold()))


def project_folders(conn: sqlite3.Connection) -> tuple[ProjectFolder, ...]:
    """A Projektek gyűjtemény mappái — NÉV szerint rendezve (kis-nagybetű-
    tűrően), a hasáb többi gyűjteményének mintájára.

    Olvashatatlan vagy időközben eltűnt ini-t csendben kihagy: a könyvtár
    másik folyamat általi éppen-írása ne omlassza össze a listát.

    #1601: aki az Emberek gyűjteményt IS betölti, ne ezt hívja, hanem a
    `index/side_pane.load_side_pane_collections`-t — az egyetlen söpréssel
    állítja elő mindkettőt."""
    collector = ProjectFolderCollector()
    sweep_folder_inis(conn, (collector,))
    return project_folders_from_paths(conn, collector.paths)


def _photo_counts(conn: sqlite3.Connection) -> dict[str, int]:
    """Mappánkénti fotószám — a fotó nélküli (frissen mentett) projekt-mappa
    is szerepelhet a listán, ott a darabszám 0."""
    return {
        row["path"]: row["n"]
        for row in conn.execute(
            "SELECT f.path AS path, COUNT(p.id) AS n FROM folders f"
            " LEFT JOIN photos p ON p.folder_id = f.id GROUP BY f.id"
        )
    }


def _display_name(folder_path: str) -> str:
    """A mappa neve — importált WINDOWS-útvonal is előfordulhat a `folders`
    táblában, ezért mindkét elválasztóra bontunk (a `models.py` mintája)."""
    return folder_path.replace("\\", "/").rstrip("/").rpartition("/")[2] or folder_path
