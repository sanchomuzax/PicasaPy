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
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from picasapy.faces.detector import FaceDetection, FaceLandmarks

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


@dataclass(frozen=True)
class PendingEmbeddingFace:
    """Egy DETEKTÁLT, de MÉG LENYOMAT NÉLKÜLI arc — pontosan annyi adattal,
    amennyi a `FaceEmbedder.compute()`-hoz kell (kép + `FaceDetection`).
    A `faces_missing_embedding` adja vissza, a lenyomat-számítás (issue
    #26, 2. lépcső, a detektálásnál alacsonyabb prioritású sor) ezen megy
    végig."""

    id: int
    photo_path: Path
    detection: FaceDetection


def faces_missing_embedding(conn: sqlite3.Connection) -> tuple[PendingEmbeddingFace, ...]:
    """A még lenyomat nélküli arcok — a fotó útvonalával és a tárolt
    kerettel/5 ponttal együtt, hogy a lenyomat-számítás ne kelljen újra
    detektáljon. `id` szerint rendezve (determinisztikus feldolgozási
    sorrend a csoportosításhoz, ld. `index.face_groups`)."""
    rows = conn.execute(
        "SELECT f.id, f.rect_left, f.rect_top, f.rect_right, f.rect_bottom, "
        "f.det_conf, f.right_eye_x, f.right_eye_y, f.left_eye_x, f.left_eye_y, "
        "f.nose_x, f.nose_y, f.mouth_right_x, f.mouth_right_y, "
        "f.mouth_left_x, f.mouth_left_y, fo.path AS folder_path, p.name AS name "
        "FROM face f "
        "JOIN photos p ON p.id = f.photo_id "
        "JOIN folders fo ON fo.id = p.folder_id "
        "WHERE f.embedding IS NULL "
        "ORDER BY f.id"
    )
    result = []
    for row in rows:
        detection = FaceDetection(
            left=row["rect_left"],
            top=row["rect_top"],
            right=row["rect_right"],
            bottom=row["rect_bottom"],
            score=row["det_conf"],
            landmarks=FaceLandmarks(
                right_eye=(row["right_eye_x"], row["right_eye_y"]),
                left_eye=(row["left_eye_x"], row["left_eye_y"]),
                nose=(row["nose_x"], row["nose_y"]),
                mouth_right=(row["mouth_right_x"], row["mouth_right_y"]),
                mouth_left=(row["mouth_left_x"], row["mouth_left_y"]),
            ),
        )
        result.append(
            PendingEmbeddingFace(
                id=row["id"],
                photo_path=Path(row["folder_path"]) / row["name"],
                detection=detection,
            )
        )
    return tuple(result)


def store_embedding(
    conn: sqlite3.Connection, face_id: int, embedding: np.ndarray | None
) -> None:
    """A `face_id` sor lenyomatának mentése — `None` esetén NULL marad
    (modell nélküli/sikertelen számítás, ld. `FaceEmbedder.compute`), nem
    hiba. `float32` bájtsorként tárolva (`numpy.frombuffer` olvassa
    vissza, ld. `face_embedding`)."""
    blob = np.asarray(embedding, dtype=np.float32).tobytes() if embedding is not None else None
    conn.execute("UPDATE face SET embedding = ? WHERE id = ?", (blob, face_id))


def face_embedding(conn: sqlite3.Connection, face_id: int) -> np.ndarray | None:
    """A `face_id` sor lenyomata, vagy `None`, ha még nincs kiszámolva."""
    row = conn.execute("SELECT embedding FROM face WHERE id = ?", (face_id,)).fetchone()
    if row is None or row["embedding"] is None:
        return None
    return np.frombuffer(row["embedding"], dtype=np.float32)


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
