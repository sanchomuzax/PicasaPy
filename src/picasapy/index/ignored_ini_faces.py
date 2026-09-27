"""#3670: az eredeti Picasa által mellőzött arcok a `.picasa.ini`-kből.

Élőben mérve (`docs/specs/picasa-arcfelismeres.md` 15.3/b.1): a mellőzött
arc jele a `faces=` sor személy-mezőjében a `ffffffffffffffff`. Ezek az
arcok akkor is a „Mellőzött emberek" albumba tartoznak, ha a saját
detektorunk a képet még nem nézte át, vagy nem talált a helyen arcot.

Séma-bővítés nélkül, a `has_ini=1` mappák közös söprésén át
(`folder_ini.sweep_folder_inis`) — ahogy az Emberek-gyűjtemény is
(`people.py`). Csak olvas; a `.picasa.ini` írása az `ini/` csomagé.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path

from picasapy.ini import UNIDENTIFIED_CONTACT, IniDocument, parse_faces

from .folder_ini import sweep_folder_inis


@dataclass(frozen=True)
class IniIgnoredFace:
    """Egy `faces=…,ffffffffffffffff` bejegyzés, az index fotójához kötve.
    `rect` a `.picasa.ini`-ben tárolt (rect64-rácsú) relatív keret."""

    photo_id: int
    photo_path: Path
    rect: tuple[float, float, float, float]


class _Collector:
    """A söprés fogyasztója: mappa → {fájlnév: [keret, …]}."""

    def __init__(self) -> None:
        self.by_folder: dict[str, dict[str, list[tuple[float, float, float, float]]]] = {}

    def __call__(self, folder_path: str, document: IniDocument) -> None:
        for section in document.file_sections():
            raw_faces = section.get("faces")
            if not raw_faces:
                continue
            try:
                faces = parse_faces(raw_faces)
            except ValueError:
                continue
            rects = [
                (face.rect.left, face.rect.top, face.rect.right, face.rect.bottom)
                for face in faces
                if face.contact_id.casefold() == UNIDENTIFIED_CONTACT
            ]
            if rects:
                self.by_folder.setdefault(folder_path, {})[section.name.casefold()] = rects


def ignored_ini_faces(conn: sqlite3.Connection) -> tuple[IniIgnoredFace, ...]:
    """Minden mellőzött (`ffffffffffffffff`) ini-arc, amelynek a fotója az
    indexben van — mappa, fájlnév, majd az ini-beli sorrend szerint."""
    collector = _Collector()
    sweep_folder_inis(conn, (collector,))
    result: list[IniIgnoredFace] = []
    for folder_path in sorted(collector.by_folder):
        rects_by_name = collector.by_folder[folder_path]
        rows = conn.execute(
            "SELECT p.id, p.name FROM photos p JOIN folders f ON f.id = p.folder_id "
            "WHERE f.path = ? ORDER BY p.name",
            (folder_path,),
        )
        for row in rows:
            for rect in rects_by_name.get(row["name"].casefold(), ()):
                result.append(
                    IniIgnoredFace(
                        photo_id=int(row["id"]),
                        photo_path=Path(folder_path) / row["name"],
                        rect=rect,
                    )
                )
    return tuple(result)
