"""#26: az „Emberek" gyűjtemény — a `faces=` + `[Contacts2]` összesítése.

Nincs önálló SQL-tábla ehhez (a `schema.py` forró fájl — séma-bővítést csak
az integrátor oszthat ki, ld. CONTRIBUTING.md): a névvel ellátott arcok
DIREKT ini-olvasással kerülnek elő, a `queries._album_suggestions` mintáját
követve — a `folders` tábla `has_ini=1` sorain megyünk végig, minden
`.picasa.ini` `[Contacts2]`-jét és a fájlbejegyzések `faces=` kulcsát
feldolgozzuk. Ez minden híváskor újraolvassa az ini-ket (NAS-on drágább,
mint egy indexelt tábla lenne) — nagy könyvtárnál ez a réteg később
séma-bővítéssel (`people`/`photo_people` tábla, az `albums`/`photo_albums`
mintájára) válthatja a mostani, olvasáskor összesítő változatot.

Az összesítés NÉV szerint történik, nem `person_id` szerint: a `[Contacts2]`
„csak lokális" (docs/specs/picasa-ini-format.md) — ugyanaz a személy
különböző mappák ini-jeiben eltérő id-t kaphat, de a nevet a Picasa
egyformán írja ki. Azonosítatlan arc (`ffffffffffffffff` contact_id) nem
számít bele.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path

from picasapy.ini import contacts_of, load_document, parse_faces
from picasapy.ini.faces import Face
from picasapy.scanner import PICASA_INI_NAME

from .queries import _SELECT, PhotoRecord, _records


@dataclass(frozen=True)
class PersonRecord:
    """Egy személy a bal hasábnak: név + a rá kitaggelt fotók száma."""

    name: str
    photo_count: int


def people_in_index(conn: sqlite3.Connection) -> tuple[PersonRecord, ...]:
    """A könyvtárban előforduló, NÉVVEL ellátott személyek — NÉV szerint
    rendezve (kis-nagybetű-tűrően), a Picasa-hasáb mintájára.

    Egy fotón belül ugyanaz a név csak egyszer számít (két arc-régió is
    tartozhatna rá, de a darabszám fotókat számol, nem arc-régiókat)."""
    counts: dict[str, int] = {}
    for _folder_path, names, faces_by_file in _iter_face_data(conn):
        for faces in faces_by_file.values():
            seen: set[str] = set()
            for face in faces:
                name = _resolve_name(face, names)
                if name is None or name in seen:
                    continue
                seen.add(name)
                counts[name] = counts.get(name, 0) + 1
    return tuple(
        PersonRecord(name=name, photo_count=count)
        for name, count in sorted(counts.items(), key=lambda kv: kv[0].casefold())
    )


def people_with(conn: sqlite3.Connection, name: str) -> tuple[PersonRecord, ...]:
    """Akik EGYÜTT szerepelnek a megadott személlyel — közös fotók száma
    szerint csökkenően, azonos darabszámnál név szerint.

    Az eredeti Picasa Emberek-panelének negyedik állapota: *„Named People
    who appear WITH the currently selected person will be listed here."*
    Ez a családi/baráti gyűjtemények természetes navigációja — „ki van még
    rajta ezeken a képeken?" —, és onnan egy kattintással át a másik
    személy albumába.

    A keresett személy MAGA nincs benne a listában. Üres/ismeretlen névre
    üres eredmény (nem hiba), a `person_photos` mintáját követve.
    """
    if not name:
        return ()
    counts: dict[str, int] = {}
    for _folder_path, names, faces_by_file in _iter_face_data(conn):
        for faces in faces_by_file.values():
            on_photo = {
                resolved
                for resolved in (_resolve_name(face, names) for face in faces)
                if resolved is not None
            }
            if name not in on_photo:
                continue
            for other in on_photo - {name}:
                counts[other] = counts.get(other, 0) + 1
    return tuple(
        PersonRecord(name=other, photo_count=count)
        for other, count in sorted(
            counts.items(), key=lambda kv: (-kv[1], kv[0].casefold())
        )
    )


def person_photos(conn: sqlite3.Connection, name: str) -> tuple[PhotoRecord, ...]:
    """Egy megnevezett személyre kitaggelt fotók — a `album_photos` mintáját
    követő szűrt nézet. Ismeretlen/üres név esetén üres eredmény (nem hiba)."""
    if not name:
        return ()
    pairs: list[tuple[str, str]] = []
    for folder_path, names, faces_by_file in _iter_face_data(conn):
        for filename, faces in faces_by_file.items():
            if any(_resolve_name(face, names) == name for face in faces):
                pairs.append((folder_path, filename))
    if not pairs:
        return ()
    clause = " OR ".join(["(f.path = ? AND p.name = ? COLLATE NOCASE)"] * len(pairs))
    params = [value for pair in pairs for value in pair]
    rows = conn.execute(
        f"{_SELECT} WHERE {clause} ORDER BY f.path, p.name", params
    )
    return _records(rows)


def _resolve_name(face: Face, names: dict[str, str]) -> str | None:
    if not face.is_identified:
        return None
    return names.get(face.contact_id.casefold())


def _iter_face_data(
    conn: sqlite3.Connection,
) -> tuple[tuple[str, dict[str, str], dict[str, tuple[Face, ...]]], ...]:
    """(mappa, {person_id.casefold(): név}, {fájlnév: arcok}) hármasok a
    `has_ini=1` mappákra — olvashatatlan/hibás ini-t csendben kihagy (a
    könyvtár másik folyamat általi éppen-írása ne omlassza össze a listát)."""
    result = []
    for row in conn.execute("SELECT path FROM folders WHERE has_ini = 1"):
        folder_path = row["path"]
        ini_path = Path(folder_path) / PICASA_INI_NAME
        try:
            document = load_document(ini_path)
        except (OSError, ValueError):
            continue
        names = {
            contact.person_id.casefold(): contact.name
            for contact in contacts_of(document)
            if contact.name
        }
        if not names:
            continue
        faces_by_file: dict[str, tuple[Face, ...]] = {}
        for section in document.file_sections():
            raw_faces = section.get("faces")
            if not raw_faces:
                continue
            try:
                faces = parse_faces(raw_faces)
            except ValueError:
                continue
            faces_by_file[section.name] = faces
        if faces_by_file:
            result.append((folder_path, names, faces_by_file))
    return tuple(result)
