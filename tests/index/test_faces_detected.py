"""#26 (1. lépcső): a SAJÁT (YuNet) arc-detektálás tárolása és a
„Névtelenek" album lekérdezése."""

from __future__ import annotations

from picasapy.faces.detector import FaceDetection, FaceLandmarks
from picasapy.index import (
    clear_faces,
    detected_face_count,
    face_ids_for_photo,
    face_photo_paths,
    ignored_faces,
    mark_faces_ignored,
    mark_faces_named,
    open_index,
    photo_ids_still_ignored,
    replace_faces,
    sync_tree,
    unignore_faces,
    unnamed_album_photos,
    unnamed_faces,
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


class TestIgnoredFaces:
    """#26: a mellőzés NEM törlés — az eredetiben a személy a „Mellőzött
    emberek" albumba került (`CAlbumLabel::Ignored`), tehát visszavehető."""

    def test_an_ignored_face_leaves_the_unnamed_album(self, tmp_path):
        db_path, photo_ids = _library(tmp_path)
        with open_index(db_path) as conn:
            replace_faces(conn, photo_ids["a.jpg"], [_face()])
            face_id = unnamed_faces(conn)[0].id

            mark_faces_ignored(conn, [face_id])

            assert unnamed_faces(conn) == ()
            assert [f.id for f in ignored_faces(conn)] == [face_id]

    def test_the_row_survives_so_it_can_come_back(self, tmp_path):
        db_path, photo_ids = _library(tmp_path)
        with open_index(db_path) as conn:
            replace_faces(conn, photo_ids["a.jpg"], [_face()])
            face_id = unnamed_faces(conn)[0].id
            mark_faces_ignored(conn, [face_id])

            unignore_faces(conn, [face_id])

            assert [f.id for f in unnamed_faces(conn)] == [face_id]
            assert ignored_faces(conn) == ()

    def test_unignoring_does_not_resurrect_a_named_face(self, tmp_path):
        """A névadás a mellőzésnél erősebb döntés — a visszavétel CSAK a
        mellőzött arcokat érinti."""
        db_path, photo_ids = _library(tmp_path)
        with open_index(db_path) as conn:
            replace_faces(conn, photo_ids["a.jpg"], [_face()])
            face_id = unnamed_faces(conn)[0].id
            mark_faces_named(conn, [face_id])

            unignore_faces(conn, [face_id])

            assert unnamed_faces(conn) == ()

    def test_an_empty_list_is_a_no_op(self, tmp_path):
        db_path, _photo_ids = _library(tmp_path)
        with open_index(db_path) as conn:
            mark_faces_ignored(conn, [])
            unignore_faces(conn, [])
            assert ignored_faces(conn) == ()


class TestFacePhotoPaths:
    """#3670: az arc → fotó-útvonal feloldás, ami a `.picasa.ini`
    `]ignoreface`-írásnak kell (melyik mappa ini-jét módosítsuk)."""

    def test_resolves_path_regardless_of_state(self, tmp_path):
        db_path, photo_ids = _library(tmp_path)
        with open_index(db_path) as conn:
            replace_faces(conn, photo_ids["a.jpg"], [_face()])
            face_id = unnamed_faces(conn)[0].id
            mark_faces_ignored(conn, [face_id])

            resolved = face_photo_paths(conn, [face_id])

        photo_id, path = resolved[face_id]
        assert photo_id == photo_ids["a.jpg"]
        assert path == tmp_path / "kepek" / "a.jpg"

    def test_empty_list_gives_empty_dict(self, tmp_path):
        db_path, _photo_ids = _library(tmp_path)
        with open_index(db_path) as conn:
            assert face_photo_paths(conn, []) == {}


class TestPhotoIdsStillIgnored:
    """#3670: kell tudni, marad-e MÉG mellőzött arc egy fotón, mielőtt a
    `.picasa.ini` `]ignoreface` jelölését levennénk róla."""

    def test_a_photo_with_a_remaining_ignored_face_is_reported(self, tmp_path):
        db_path, photo_ids = _library(tmp_path)
        with open_index(db_path) as conn:
            replace_faces(conn, photo_ids["a.jpg"], [_face(), _face(score=0.4)])
            ids = [f.id for f in unnamed_faces(conn)]
            mark_faces_ignored(conn, ids)

            still = photo_ids_still_ignored(conn, [photo_ids["a.jpg"]])

        assert still == {photo_ids["a.jpg"]}

    def test_a_fully_unignored_photo_is_not_reported(self, tmp_path):
        db_path, photo_ids = _library(tmp_path)
        with open_index(db_path) as conn:
            replace_faces(conn, photo_ids["a.jpg"], [_face()])
            face_id = unnamed_faces(conn)[0].id
            mark_faces_ignored(conn, [face_id])
            unignore_faces(conn, [face_id])

            still = photo_ids_still_ignored(conn, [photo_ids["a.jpg"]])

        assert still == set()

    def test_empty_list_gives_empty_set(self, tmp_path):
        db_path, _photo_ids = _library(tmp_path)
        with open_index(db_path) as conn:
            assert photo_ids_still_ignored(conn, []) == set()


class TestFaceIdsForPhoto:
    """#3670: a rescan után beírt friss sorok azonosítói, hogy a hívó
    azonnal `'ignored'`-ra állíthassa őket a `.picasa.ini` alapján."""

    def test_returns_all_rows_for_the_photo(self, tmp_path):
        db_path, photo_ids = _library(tmp_path)
        with open_index(db_path) as conn:
            replace_faces(conn, photo_ids["a.jpg"], [_face(), _face(score=0.4)])
            ids = face_ids_for_photo(conn, photo_ids["a.jpg"])
        assert len(ids) == 2

    def test_empty_for_a_photo_without_faces(self, tmp_path):
        db_path, photo_ids = _library(tmp_path)
        with open_index(db_path) as conn:
            assert face_ids_for_photo(conn, photo_ids["b.jpg"]) == ()
