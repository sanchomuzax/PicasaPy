"""#26 (1. lépcső): a SAJÁT (YuNet) arc-detektálás tárolása az indexben, és
a „Névtelenek" album lekérdezése — csoportosítás/névfeloldás NÉLKÜL (ez a
terv 2–3. lépcsője).

Külön tábla (`face`, `schema.py`), a `photo_hashes`/`hashes.py` mintáját
követve: tisztán származtatott adat, fotónkénti töröl-és-újraír frissítéssel
(`replace_faces`) — egy fotó ismételt szkennelése nem halmoz duplikátumot.

A `.picasa.ini` `faces=`/`[Contacts2]` adatait ez a réteg NEM olvassa és
NEM írja — az a `ini/faces.py`/`index/people.py` már meglévő rétege,
változatlanul. A két réteg összefonása (pl. „ez a Picasa-arc egyezik ezzel
a saját találattal") a terv KÉSŐBBI lépcsője."""

from __future__ import annotations

import sqlite3
from collections.abc import Iterable

from picasapy.faces.detector import FaceDetection

from .queries import _SELECT, PhotoRecord, _records


def replace_faces(
    conn: sqlite3.Connection, photo_id: int, faces: Iterable[FaceDetection]
) -> None:
    """A `photo_id` fotóhoz tárolt SAJÁT arc-találatok cseréje.

    Törli a fotó korábbi sorait, majd beszúrja az újakat — idempotens
    (egy fotó ismételt szkennelése nem duplikál). A hívó felelős a
    commitért (a scan-worker kötegelve commitol, a dedup/hash-scan
    mintája szerint, ld. `app/dedup_controller.py`)."""
    conn.execute("DELETE FROM face WHERE photo_id = ?", (photo_id,))
    rows = [
        (
            photo_id,
            face.left,
            face.top,
            face.right,
            face.bottom,
            face.score,
            face.landmarks.right_eye[0],
            face.landmarks.right_eye[1],
            face.landmarks.left_eye[0],
            face.landmarks.left_eye[1],
            face.landmarks.nose[0],
            face.landmarks.nose[1],
            face.landmarks.mouth_right[0],
            face.landmarks.mouth_right[1],
            face.landmarks.mouth_left[0],
            face.landmarks.mouth_left[1],
        )
        for face in faces
    ]
    if not rows:
        return
    conn.executemany(
        "INSERT INTO face ("
        "photo_id, rect_left, rect_top, rect_right, rect_bottom, det_conf, "
        "right_eye_x, right_eye_y, left_eye_x, left_eye_y, nose_x, nose_y, "
        "mouth_right_x, mouth_right_y, mouth_left_x, mouth_left_y"
        ") VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        rows,
    )


def clear_faces(conn: sqlite3.Connection, photo_id: int) -> None:
    """A fotó SAJÁT arc-találatainak törlése (pl. ha a Picasa időközben
    névcímkét kapott a fotón — ld. `FaceScanController`: onnantól a mi
    detektorunk kihagyja, a régi találat pedig félrevezető lenne)."""
    conn.execute("DELETE FROM face WHERE photo_id = ?", (photo_id,))


def detected_face_count(conn: sqlite3.Connection, photo_id: int) -> int:
    """Hány SAJÁT arc-találat tartozik a fotóhoz (a néző overlay-jének
    később hasznos lekérdezés — 1. lépcsőben csak a teszteké)."""
    row = conn.execute(
        "SELECT COUNT(*) AS n FROM face WHERE photo_id = ?", (photo_id,)
    ).fetchone()
    return int(row["n"]) if row is not None else 0


def unnamed_album_photos(conn: sqlite3.Connection) -> tuple[PhotoRecord, ...]:
    """A „Névtelenek" album (issue #26, javasolt 1. lépcső): minden fotó,
    amelyen a SAJÁT detektorunk legalább egy arcot talált — csoportosítás
    és névfeloldás NÉLKÜL (azok a terv 2–3. lépcsője). A `state` oszlop itt
    mindig 'unnamed', mert ez a lépcső még nem ír más állapotot."""
    rows = conn.execute(
        f"{_SELECT} WHERE p.id IN ("
        "SELECT DISTINCT photo_id FROM face WHERE state = 'unnamed'"
        ") ORDER BY f.path, p.name"
    )
    return _records(rows)
