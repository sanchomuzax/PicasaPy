"""Az észlelt arcok és lenyomatok tárolási műveletei."""


from __future__ import annotations


import math
import sqlite3
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from picasapy.faces.detector import FaceDetection, FaceLandmarks


def replace_faces(
    conn: sqlite3.Connection, photo_id: int, faces: Iterable[FaceDetection]
) -> None:
    """A `photo_id` fotóhoz tárolt SAJÁT arc-találatok cseréje.

    Törli a fotó korábbi sorait, majd beszúrja az újakat — idempotens
    (egy fotó ismételt szkennelése nem duplikál). A hívó felelős a
    commitért (a scan-worker kötegelve commitol, a dedup/hash-scan
    mintája szerint, ld. `app/dedup_controller.py`)."""
    conn.execute(
        "DELETE FROM face WHERE photo_id = ? AND source = 'detector'",
        (photo_id,),
    )
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


def replace_imported_unnamed_faces(
    conn: sqlite3.Connection,
    photo_id: int,
    rects: Iterable[tuple[float, float, float, float]],
) -> int:
    """Replace db3-imported unnamed regions for one indexed photo.

    Picasa stores rect64 coordinates relatively while this index uses image
    pixels. The rows are marked with their source and carry no synthetic face
    landmarks; consequently they are excluded from embedding calculation.
    Returns the number of rows inserted (zero if the photo is not indexable).
    """
    conn.execute(
        "DELETE FROM face WHERE photo_id = ? AND source = 'picasa'",
        (photo_id,),
    )
    photo = conn.execute(
        "SELECT width, height FROM photos WHERE id = ?", (photo_id,)
    ).fetchone()
    if photo is None or not photo["width"] or not photo["height"]:
        return 0
    width, height = int(photo["width"]), int(photo["height"])
    detector_rows = tuple(
        conn.execute(
            "SELECT rect_left, rect_top, rect_right, rect_bottom FROM face "
            "WHERE photo_id = ? AND source = 'detector'",
            (photo_id,),
        )
    )
    rows = []
    for rect in rects:
        if len(rect) != 4:
            continue
        left, top, right, bottom = (float(value) for value in rect)
        if (
            not all(map(math.isfinite, (left, top, right, bottom)))
            or left < 0
            or top < 0
            or right > 1
            or bottom > 1
            or right <= left
            or bottom <= top
        ):
            continue
        pixel_rect = (left * width, top * height, right * width, bottom * height)
        if any(
            all(abs(pixel_rect[index] - detected[index]) <= 1.0 for index in range(4))
            for detected in detector_rows
        ):
            continue
        rows.append(
            (
                photo_id,
                *pixel_rect,
                0.0,
                *(0.0 for _ in range(10)),
                "picasa",
            )
        )
    if rows:
        conn.executemany(
            "INSERT INTO face ("
            "photo_id, rect_left, rect_top, rect_right, rect_bottom, det_conf, "
            "right_eye_x, right_eye_y, left_eye_x, left_eye_y, nose_x, nose_y, "
            "mouth_right_x, mouth_right_y, mouth_left_x, mouth_left_y, source"
            ") VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            rows,
        )
    return len(rows)


def clear_faces(conn: sqlite3.Connection, photo_id: int) -> None:
    """A fotó SAJÁT arc-találatainak törlése (pl. ha a Picasa időközben
    névcímkét kapott a fotón — ld. `FaceScanController`: onnantól a mi
    detektorunk kihagyja, a régi találat pedig félrevezető lenne)."""
    conn.execute(
        "DELETE FROM face WHERE photo_id = ? AND source = 'detector'",
        (photo_id,),
    )


def reset_all_faces(conn: sqlite3.Connection) -> int:
    """A SAJÁT arc-találatok alaphelyzetbe állítása — az eredeti „Arcok
    alaphelyzetbe állítása" INDEX-oldali fele (#422).

    Az eredeti figyelmeztetése (`CThumbUI::ResetAllFaces`) szerint ez
    „törli az összes személyi albumot, és a Név nélküliek albumba helyezi
    át az arcokat". Nálunk pontosan ennyi történik: minden arc `'unnamed'`
    állapotba kerül, a névhez kötés és a javaslat törlődik, a csoportok
    pedig eltűnnek (a következő csoportosítás újraépíti őket).

    **Amit NEM csinál:** nem nyúl a `.picasa.ini` `faces=`/`[Contacts2]`
    tartalmához. Az eredeti ezt KÜLÖN kérdésként tette fel
    (`CThumbUI::ResetAll`: „Szeretné eltávolítani az arcokkal kapcsolatos
    összes adatot az INI fájlokból?") — az ember által adott névcímke a
    projekt alapszabálya szerint szent, azt csak külön, kifejezett kérésre
    szabad bántani.

    A visszatérési érték az érintett arcok száma.
    """
    row = conn.execute("SELECT COUNT(*) AS n FROM face").fetchone()
    affected = int(row["n"]) if row is not None else 0
    conn.execute(
        "UPDATE face SET state = 'unnamed', person_name = NULL, "
        "suggested_name = NULL, group_id = NULL"
    )
    conn.execute("DELETE FROM face_group")
    return affected


def detected_face_count(conn: sqlite3.Connection, photo_id: int) -> int:
    """Hány SAJÁT arc-találat tartozik a fotóhoz (a néző overlay-jének
    később hasznos lekérdezés — 1. lépcsőben csak a teszteké)."""
    row = conn.execute(
        "SELECT COUNT(*) AS n FROM face "
        "WHERE photo_id = ? AND source = 'detector'",
        (photo_id,),
    ).fetchone()
    return int(row["n"]) if row is not None else 0


@dataclass(frozen=True)
class PendingEmbeddingFace:
    """Egy DETEKTÁLT, de MÉG LENYOMAT NÉLKÜLI arc — pontosan annyi adattal,
    amennyi a `FaceEmbedder.compute()`-hoz kell (kép + `FaceDetection`).
    A `faces_missing_embedding` adja vissza, a lenyomat-számítás (issue
    #26, 2. lépcső, a detektálásnál alacsonyabb prioritású sor) ezen megy
    végig. A fotó teljes mérete a tárolt koordináták és a dekódolt kép
    képpont-rácsai közötti váltáshoz kell."""

    id: int
    photo_path: Path
    detection: FaceDetection
    photo_width: int | None = None
    photo_height: int | None = None


def faces_missing_embedding(conn: sqlite3.Connection) -> tuple[PendingEmbeddingFace, ...]:
    """A még lenyomat nélküli arcok — a fotó útvonalával és a tárolt
    kerettel/5 ponttal együtt, hogy a lenyomat-számítás ne kelljen újra
    detektáljon. `id` szerint rendezve (determinisztikus feldolgozási
    sorrend a csoportosításhoz, ld. `index.face_groups`)."""
    rows = conn.execute(
        "SELECT f.id, f.rect_left, f.rect_top, f.rect_right, f.rect_bottom, "
        "f.det_conf, f.right_eye_x, f.right_eye_y, f.left_eye_x, f.left_eye_y, "
        "f.nose_x, f.nose_y, f.mouth_right_x, f.mouth_right_y, "
        "f.mouth_left_x, f.mouth_left_y, fo.path AS folder_path, p.name AS name, "
        "p.width AS photo_width, p.height AS photo_height "
        "FROM face f "
        "JOIN photos p ON p.id = f.photo_id "
        "JOIN folders fo ON fo.id = p.folder_id "
        "WHERE f.embedding IS NULL AND f.source = 'detector' "
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
                photo_width=row["photo_width"],
                photo_height=row["photo_height"],
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
