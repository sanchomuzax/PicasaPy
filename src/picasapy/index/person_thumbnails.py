"""#4536: a személy-album indexképének tartós választása."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
import sqlite3

from picasapy.ini import (
    IniDocument,
    contacts_of,
    ini_source_path,
    load_document,
    parse_faces,
)
from picasapy.scanner import PICASA_INI_NAME


@dataclass(frozen=True)
class PersonThumbnail:
    """Egy érvényes, személyhez tartozó arc-indexkép hivatkozása."""

    photo_id: int
    rect: tuple[float, float, float, float]


def person_thumbnail_face(
    conn: sqlite3.Connection, person_name: str, photo_id: int
) -> tuple[float, float, float, float] | None:
    """A fotón szereplő személy arcának kerete, vagy `None`, ha nincs ott."""
    if not person_name or photo_id <= 0:
        return None
    row = conn.execute(
        "SELECT f.path, p.name FROM photos p "
        "JOIN folders f ON f.id = p.folder_id WHERE p.id = ?",
        (photo_id,),
    ).fetchone()
    if row is None:
        return None
    document = _load_folder_ini(row["path"])
    return _face_rect(document, row["name"], person_name) if document else None


def set_person_thumbnail(
    conn: sqlite3.Connection, person_name: str, photo_id: int
) -> bool:
    """Mentse a választást, ha az indexelt fotón szerepel a személy arca.

    Nem commitol: a hívó az index többi műveletével együtt kezelheti a
    tranzakciót. Csak a fotó azonosítóját tároljuk; az arc kerete minden
    visszaolvasáskor a `.picasa.ini` aktuális adatából jön.
    """
    kulcs = person_name.strip().casefold()
    if not kulcs or person_thumbnail_face(conn, person_name, photo_id) is None:
        return False
    conn.execute(
        "INSERT INTO person_thumbnails(person_key, photo_id) VALUES (?, ?) "
        "ON CONFLICT(person_key) DO UPDATE SET photo_id = excluded.photo_id",
        (kulcs, photo_id),
    )
    return True


def person_thumbnail(
    conn: sqlite3.Connection, person_name: str
) -> PersonThumbnail | None:
    """A mentett választás, ha a fotó még a személyhez tartozó arcot mutatja."""
    return person_thumbnails(conn, (person_name,)).get(
        person_name.strip().casefold()
    )


def person_thumbnails(
    conn: sqlite3.Connection, person_names: Iterable[str] | None = None
) -> dict[str, PersonThumbnail]:
    """Az érvényes mentett választások személy-kulcs szerint.

    A kiválasztott képek mappájának ini-fájlját ugyanazon mappán belül
    legfeljebb egyszer olvassuk, akkor is, ha több személy szerepel rajtuk.
    """
    wanted = (
        {name.strip().casefold() for name in person_names if name and name.strip()}
        if person_names is not None
        else None
    )
    rows = conn.execute(
        "SELECT t.person_key, p.id AS photo_id, p.name AS photo_name, "
        "f.path AS folder_path FROM person_thumbnails t "
        "JOIN photos p ON p.id = t.photo_id "
        "JOIN folders f ON f.id = p.folder_id ORDER BY t.person_key"
    ).fetchall()
    documents: dict[str, IniDocument | None] = {}
    result: dict[str, PersonThumbnail] = {}
    for row in rows:
        key = row["person_key"]
        if wanted is not None and key not in wanted:
            continue
        folder_path = row["folder_path"]
        if folder_path not in documents:
            documents[folder_path] = _load_folder_ini(folder_path)
        document = documents[folder_path]
        if document is None:
            continue
        rect = _face_rect(document, row["photo_name"], key)
        if rect is not None:
            result[key] = PersonThumbnail(row["photo_id"], rect)
    return result


def _load_folder_ini(folder_path: str) -> IniDocument | None:
    try:
        ini_path = Path(folder_path) / PICASA_INI_NAME
        source_path = ini_source_path(ini_path) or ini_path
        return load_document(source_path)
    except (OSError, ValueError):
        return None


def _face_rect(
    document: IniDocument, photo_name: str, person_name: str
) -> tuple[float, float, float, float] | None:
    contacts = {
        contact.person_id.casefold(): contact.name.strip().casefold()
        for contact in contacts_of(document)
        if contact.name and contact.person_id
    }
    section = document.section(photo_name)
    raw_faces = section.get("faces") if section is not None else None
    if not raw_faces:
        return None
    try:
        faces = parse_faces(raw_faces)
    except ValueError:
        return None
    wanted = person_name.strip().casefold()
    for face in faces:
        if (
            face.is_identified
            and contacts.get(face.contact_id.casefold()) == wanted
        ):
            rect = face.rect
            return (rect.left, rect.top, rect.right, rect.bottom)
    return None
