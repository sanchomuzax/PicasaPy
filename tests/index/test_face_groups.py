"""#26 (2. lépcső): a lenyomat-tárolás (`faces_detected.py` bővítése) és az
inkrementális csoportosítás (`face_groups.group_unnamed_faces`) DB-rétege.

A kritikus regressziós teszt (`TestNamedFacesNeverReclustered`) az
ALAPSZABÁLYT őrzi: a `state != 'unnamed'` (már névvel ellátott) arcokat a
csoportosítás SOHA nem érinti — sem `group_id`-t nem kapnak, sem a
centroidjuk nem befolyásolja mások besorolását."""

from __future__ import annotations

import numpy as np

from picasapy.faces.detector import FaceDetection, FaceLandmarks
from picasapy.index import (
    face_embedding,
    face_groups,
    faces_missing_embedding,
    group_unnamed_faces,
    open_index,
    replace_faces,
    store_embedding,
    sync_tree,
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


def _library(tmp_path, names=("a.jpg", "b.jpg", "c.jpg")):
    root = tmp_path / "kepek"
    root.mkdir()
    for name in names:
        make_jpeg(root / name)
    with open_index(tmp_path / "index.db") as conn:
        sync_tree(conn, root)
        photo_ids = {
            row["name"]: row["id"]
            for row in conn.execute("SELECT id, name FROM photos")
        }
    return tmp_path / "index.db", photo_ids


class TestEmbeddingStorage:
    def test_faces_missing_embedding_lists_detected_faces(self, tmp_path):
        db_path, photo_ids = _library(tmp_path, names=("a.jpg",))
        with open_index(db_path) as conn:
            replace_faces(conn, photo_ids["a.jpg"], [_face()])
            conn.commit()
            pending = faces_missing_embedding(conn)
        assert len(pending) == 1
        assert pending[0].photo_path.name == "a.jpg"
        assert pending[0].detection.left == 5.0

    def test_store_embedding_round_trips(self, tmp_path):
        db_path, photo_ids = _library(tmp_path, names=("a.jpg",))
        with open_index(db_path) as conn:
            replace_faces(conn, photo_ids["a.jpg"], [_face()])
            conn.commit()
            face_id = faces_missing_embedding(conn)[0].id
            embedding = np.arange(128, dtype=np.float32)
            store_embedding(conn, face_id, embedding)
            conn.commit()
            assert faces_missing_embedding(conn) == ()
            restored = face_embedding(conn, face_id)
        np.testing.assert_array_equal(restored, embedding)

    def test_store_embedding_none_leaves_face_pending(self, tmp_path):
        db_path, photo_ids = _library(tmp_path, names=("a.jpg",))
        with open_index(db_path) as conn:
            replace_faces(conn, photo_ids["a.jpg"], [_face()])
            conn.commit()
            face_id = faces_missing_embedding(conn)[0].id
            store_embedding(conn, face_id, None)
            conn.commit()
            assert face_embedding(conn, face_id) is None
            assert len(faces_missing_embedding(conn)) == 1


def _seed_embedding(conn, photo_id, vector, score=0.9):
    replace_faces(conn, photo_id, [_face(score=score)])
    conn.commit()
    face_id = conn.execute(
        "SELECT id FROM face WHERE photo_id = ?", (photo_id,)
    ).fetchone()["id"]
    store_embedding(conn, face_id, np.array(vector, dtype=np.float32))
    conn.commit()
    return face_id


class TestGroupUnnamedFaces:
    def test_first_face_creates_a_new_group(self, tmp_path):
        db_path, photo_ids = _library(tmp_path, names=("a.jpg",))
        with open_index(db_path) as conn:
            _seed_embedding(conn, photo_ids["a.jpg"], [1.0, 0.0, 0.0])
            assigned = group_unnamed_faces(conn, cluster_threshold=0.5)
            conn.commit()
            groups = face_groups(conn)
        assert assigned == 1
        assert len(groups) == 1
        assert groups[0].face_count == 1

    def test_similar_faces_join_the_same_group(self, tmp_path):
        db_path, photo_ids = _library(tmp_path, names=("a.jpg", "b.jpg"))
        with open_index(db_path) as conn:
            _seed_embedding(conn, photo_ids["a.jpg"], [1.0, 0.0, 0.0])
            _seed_embedding(conn, photo_ids["b.jpg"], [0.99, 0.01, 0.0])
            group_unnamed_faces(conn, cluster_threshold=0.9)
            conn.commit()
            groups = face_groups(conn)
            rows = conn.execute("SELECT DISTINCT group_id FROM face").fetchall()
        assert len(groups) == 1
        assert groups[0].face_count == 2
        assert {row["group_id"] for row in rows} == {groups[0].group_id}

    def test_dissimilar_faces_form_separate_groups(self, tmp_path):
        db_path, photo_ids = _library(tmp_path, names=("a.jpg", "b.jpg"))
        with open_index(db_path) as conn:
            _seed_embedding(conn, photo_ids["a.jpg"], [1.0, 0.0, 0.0])
            _seed_embedding(conn, photo_ids["b.jpg"], [0.0, 1.0, 0.0])
            group_unnamed_faces(conn, cluster_threshold=0.9)
            conn.commit()
            groups = face_groups(conn)
        assert len(groups) == 2
        assert {g.face_count for g in groups} == {1}

    def test_idempotent_second_call_does_not_regroup(self, tmp_path):
        db_path, photo_ids = _library(tmp_path, names=("a.jpg",))
        with open_index(db_path) as conn:
            _seed_embedding(conn, photo_ids["a.jpg"], [1.0, 0.0, 0.0])
            group_unnamed_faces(conn, cluster_threshold=0.5)
            conn.commit()
            second_pass = group_unnamed_faces(conn, cluster_threshold=0.5)
            conn.commit()
            groups = face_groups(conn)
        assert second_pass == 0
        assert len(groups) == 1
        assert groups[0].face_count == 1

    def test_suggestion_above_threshold_does_not_create_or_join_a_group(self, tmp_path):
        db_path, photo_ids = _library(tmp_path, names=("a.jpg",))
        with open_index(db_path) as conn:
            face_id = _seed_embedding(conn, photo_ids["a.jpg"], [1.0, 0.0, 0.0])
            assigned = group_unnamed_faces(
                conn,
                suggest_threshold=0.5,
                cluster_threshold=0.9,
                named_centroids={"Kovács Anna": np.array([0.999, 0.001, 0.0], dtype=np.float32)},
            )
            conn.commit()
            row = conn.execute("SELECT group_id FROM face WHERE id = ?", (face_id,)).fetchone()
            groups = face_groups(conn)
        assert assigned == 0
        assert row["group_id"] is None
        assert groups == ()


class TestNamedFacesNeverReclustered:
    """Az ALAPSZABÁLY (issue #26): a már névvel ellátott arcok
    hozzárendelését a csoportosítás SOHA nem írja felül és nem is
    értékeli újra."""

    def test_named_state_face_is_never_grouped(self, tmp_path):
        db_path, photo_ids = _library(tmp_path, names=("a.jpg", "b.jpg"))
        with open_index(db_path) as conn:
            # "a.jpg": már névvel ellátott arc — SZIMULÁLVA `state='named'`-del
            # (a face táblát közvetlenül írjuk, mert a mai FaceScanController
            # ilyen fotóhoz eleve nem hoz létre sort — ez a teszt a jövőbeli,
            # bővített forgatókönyvet is lefedi, ha egyszer a névvel ellátott
            # fotókhoz is keletkezne face-sor)
            named_id = _seed_embedding(conn, photo_ids["a.jpg"], [1.0, 0.0, 0.0])
            conn.execute("UPDATE face SET state = 'named' WHERE id = ?", (named_id,))
            conn.commit()
            # "b.jpg": névtelen, majdnem AZONOS lenyomattal — csábító célpont
            # lenne, ha a csoportosítás tévedésből a névvel ellátott arcot is
            # bevonná
            unnamed_id = _seed_embedding(conn, photo_ids["b.jpg"], [0.999, 0.001, 0.0])
            group_unnamed_faces(conn, cluster_threshold=0.5)
            conn.commit()
            named_row = conn.execute(
                "SELECT state, group_id FROM face WHERE id = ?", (named_id,)
            ).fetchone()
            unnamed_row = conn.execute(
                "SELECT state, group_id FROM face WHERE id = ?", (unnamed_id,)
            ).fetchone()
            groups = face_groups(conn)
        # a névvel ellátott arc érintetlen: nincs csoportja, az állapota megmaradt
        assert named_row["state"] == "named"
        assert named_row["group_id"] is None
        # a névtelen arc viszont kapott csoportot — a névvel ellátott arc
        # centroidja NEM vett részt az összehasonlításban (csak saját magát
        # alkotja meg egy ÚJ csoportként)
        assert unnamed_row["state"] == "unnamed"
        assert unnamed_row["group_id"] is not None
        assert len(groups) == 1
        assert groups[0].face_count == 1
