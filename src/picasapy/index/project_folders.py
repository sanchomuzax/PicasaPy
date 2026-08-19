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
from dataclasses import dataclass
from pathlib import Path

from picasapy.ini import is_projects_category, load_document, read_folder_category
from picasapy.scanner import PICASA_INI_NAME


@dataclass(frozen=True)
class ProjectFolder:
    """Egy projekt-mappa a hasábnak: útvonal, megjelenítendő név, darabszám."""

    path: str
    name: str
    photo_count: int


def project_folders(conn: sqlite3.Connection) -> tuple[ProjectFolder, ...]:
    """A Projektek gyűjtemény mappái — NÉV szerint rendezve (kis-nagybetű-
    tűrően), a hasáb többi gyűjteményének mintájára.

    Olvashatatlan vagy időközben eltűnt ini-t csendben kihagy: a könyvtár
    másik folyamat általi éppen-írása ne omlassza össze a listát."""
    counts = _photo_counts(conn)
    folders = []
    for row in conn.execute("SELECT path FROM folders WHERE has_ini = 1"):
        folder_path = row["path"]
        try:
            document = load_document(Path(folder_path) / PICASA_INI_NAME)
        except (OSError, ValueError):
            continue
        if not is_projects_category(read_folder_category(document)):
            continue
        folders.append(
            ProjectFolder(
                path=folder_path,
                name=_display_name(folder_path),
                photo_count=counts.get(folder_path, 0),
            )
        )
    return tuple(sorted(folders, key=lambda folder: folder.name.casefold()))


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
