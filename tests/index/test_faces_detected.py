"""#26 (1. lépcső): a SAJÁT (YuNet) arc-detektálás tárolása és a
„Névtelenek" album lekérdezése."""

from __future__ import annotations

from picasapy.faces.detector import FaceDetection, FaceLandmarks
from picasapy.index import (
    clear_faces,
    detected_face_count,
    open_index,
    replace_faces,
    sync_tree,
    unnamed_album_photos,
)
from support.jpeg_factory import make_jpeg

_LANDMARKS = FaceLandmarks(
    right_eye=(10.0, 20.0),
    left_eye=(30.0, 20.0),
    nose=(20.0, 30.0),
    mouth_right=(15.0, 40.0),
    mouth_left=(25.0, 40.0),
)


def _face(score=0.9) -> FaceDetection:
    return FaceDetection(left=5.0, top=10.0, right=40.0, bottom=50.0, score=score, landmarks=_LANDMARKS)


def _library(tmp_path):
    root = tmp_path / "kepek"
    root.mkdir()
    make_jpeg(root / "a.jpg")
    make_jpeg(root / "b.jpg")
    with open_index(tmp_path / "index.db") as conn:
        sync_tree(conn, root)
        photo_ids = {
            row["name"]: row["id"]
            for row in conn.execute("SELECT id, name FROM photos")
        }
    return tmp_path / "index.db", photo_ids


class TestReplaceFaces:
    def test_round_trip(self, tmp_path):
        db_path, photo_ids = _library(tmp_path)
        with open_index(db_path) as conn:
            replace_faces(conn, photo_ids["a.jpg"], [_face()])
            conn.commit()
            row = conn.execute(
                "SELECT * FROM face WHERE photo_id = ?", (photo_ids["a.jpg"],)
            ).fetchone()
        assert row["rect_left"] == 5.0
        assert row["rect_bottom"] == 50.0
        assert row["right_eye_x"] == 10.0
        assert row["left_eye_x"] == 30.0
        assert row["state"] == "unnamed"

    def test_replace_does_not_duplicate(self, tmp_path):
        db_path, photo_ids = _library(tmp_path)
        with open_index(db_path) as conn:
            replace_faces(conn, photo_ids["a.jpg"], [_face(), _face(score=0.5)])
            replace_faces(conn, photo_ids["a.jpg"], [_face()])
            conn.commit()
            assert detected_face_count(conn, photo_ids["a.jpg"]) == 1

    def test_empty_list_clears_previous_faces(self, tmp_path):
        db_path, photo_ids = _library(tmp_path)
        with open_index(db_path) as conn:
            replace_faces(conn, photo_ids["a.jpg"], [_face()])
            replace_faces(conn, photo_ids["a.jpg"], [])
            conn.commit()
            assert detected_face_count(conn, photo_ids["a.jpg"]) == 0

    def test_clear_faces(self, tmp_path):
        db_path, photo_ids = _library(tmp_path)
        with open_index(db_path) as conn:
            replace_faces(conn, photo_ids["a.jpg"], [_face()])
            conn.commit()
            clear_faces(conn, photo_ids["a.jpg"])
            conn.commit()
            assert detected_face_count(conn, photo_ids["a.jpg"]) == 0


class TestUnnamedAlbum:
    def test_only_photos_with_detected_faces_appear(self, tmp_path):
        db_path, photo_ids = _library(tmp_path)
        with open_index(db_path) as conn:
            replace_faces(conn, photo_ids["a.jpg"], [_face()])
            conn.commit()
            album = unnamed_album_photos(conn)
        assert [record.name for record in album] == ["a.jpg"]

    def test_empty_without_any_detection(self, tmp_path):
        db_path, _photo_ids = _library(tmp_path)
        with open_index(db_path) as conn:
            assert unnamed_album_photos(conn) == ()

    def test_multiple_faces_on_one_photo_count_once(self, tmp_path):
        db_path, photo_ids = _library(tmp_path)
        with open_index(db_path) as conn:
            replace_faces(conn, photo_ids["a.jpg"], [_face(), _face(score=0.4)])
            conn.commit()
            album = unnamed_album_photos(conn)
        assert len(album) == 1
