"""#5180: a Picasából átvett névtelen arc az index saját találataitól elkülönül."""

from __future__ import annotations

import pytest

from picasapy.faces.detector import FaceDetection, FaceLandmarks
from picasapy.index import (
    clear_faces,
    detected_face_count,
    faces_missing_embedding,
    open_index,
    replace_faces,
    replace_imported_unnamed_faces,
    sync_tree,
    unnamed_faces,
)
from support.jpeg_factory import make_jpeg


_LANDMARKS = FaceLandmarks(
    right_eye=(8.0, 10.0),
    left_eye=(18.0, 10.0),
    nose=(13.0, 16.0),
    mouth_right=(10.0, 22.0),
    mouth_left=(16.0, 22.0),
)


def test_importalt_arc_idempotens_es_nem_kerul_embedding_sorba(tmp_path):
    library = tmp_path / "kepek"
    library.mkdir()
    make_jpeg(library / "a.jpg")
    index_path = tmp_path / "index.db"
    with open_index(index_path) as conn:
        sync_tree(conn, library)
        photo_id = conn.execute(
            "SELECT id FROM photos WHERE name = 'a.jpg'"
        ).fetchone()[0]
        count = replace_imported_unnamed_faces(
            conn, photo_id, ((0.25, 0.2, 0.5, 0.6),)
        )
        again = replace_imported_unnamed_faces(
            conn, photo_id, ((0.25, 0.2, 0.5, 0.6),)
        )
        imported = [face for face in unnamed_faces(conn) if face.photo_id == photo_id]
        pending = faces_missing_embedding(conn)

    assert count == again == 1
    assert len(imported) == 1
    assert imported[0].rect == pytest.approx((0.25, 0.2, 0.5, 0.6))
    assert imported[0].state == "unnamed"
    assert pending == ()


def test_detector_csere_es_torles_megtartja_a_db3_arcot(tmp_path):
    library = tmp_path / "kepek"
    library.mkdir()
    make_jpeg(library / "a.jpg")
    index_path = tmp_path / "index.db"
    with open_index(index_path) as conn:
        sync_tree(conn, library)
        photo_id = conn.execute(
            "SELECT id FROM photos WHERE name = 'a.jpg'"
        ).fetchone()[0]
        replace_imported_unnamed_faces(
            conn, photo_id, ((0.25, 0.2, 0.5, 0.6),)
        )
        replace_faces(
            conn,
            photo_id,
            [
                FaceDetection(
                    left=4.0,
                    top=6.0,
                    right=20.0,
                    bottom=28.0,
                    score=0.9,
                    landmarks=_LANDMARKS,
                )
            ],
        )
        assert detected_face_count(conn, photo_id) == 1
        assert len([f for f in unnamed_faces(conn) if f.photo_id == photo_id]) == 2
        clear_faces(conn, photo_id)
        remaining = [f for f in unnamed_faces(conn) if f.photo_id == photo_id]

    assert len(remaining) == 1
    assert remaining[0].rect == pytest.approx((0.25, 0.2, 0.5, 0.6))
