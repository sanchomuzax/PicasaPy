"""#26 (2. lépcső): a csoportosítás TISZTA matematikája — a lenyomatokat
paraméterként adva, modell NÉLKÜL is tesztelhető (egyetlen teszt sem
importál `cv2.FaceRecognizerSF`-et vagy modellfájlt)."""

from __future__ import annotations

import numpy as np

from picasapy.faces.clustering import (
    DEFAULT_CLUSTER_THRESHOLD,
    DEFAULT_SUGGEST_THRESHOLD,
    PICASA_STEPS,
    FaceGroupCentroid,
    assign_face,
    cosine_similarity,
    step_to_threshold,
)


def _vec(*values: float) -> np.ndarray:
    return np.array(values, dtype=np.float32)


class TestCosineSimilarity:
    def test_identical_vectors_are_similarity_one(self):
        v = _vec(1.0, 2.0, 3.0)
        assert cosine_similarity(v, v) == 1.0

    def test_orthogonal_vectors_are_zero(self):
        assert cosine_similarity(_vec(1.0, 0.0), _vec(0.0, 1.0)) == 0.0

    def test_opposite_vectors_are_minus_one(self):
        assert cosine_similarity(_vec(1.0, 0.0), _vec(-1.0, 0.0)) == -1.0

    def test_zero_vector_is_zero_not_error(self):
        assert cosine_similarity(_vec(0.0, 0.0), _vec(1.0, 1.0)) == 0.0


class TestStepToThreshold:
    def test_endpoints_map_to_scale_bounds(self):
        assert step_to_threshold(PICASA_STEPS[0]) == 0.20
        assert abs(step_to_threshold(PICASA_STEPS[-1]) - 0.55) < 1e-9

    def test_monotonic_across_steps(self):
        thresholds = [step_to_threshold(step) for step in PICASA_STEPS]
        assert thresholds == sorted(thresholds)

    def test_suggest_default_is_stricter_than_cluster_default(self):
        # a javaslat (elnevezett személyhez társítás) tévedése látványosabb,
        # mint egy névtelen csoport téves összevonása — ezért szigorúbb
        assert DEFAULT_SUGGEST_THRESHOLD > DEFAULT_CLUSTER_THRESHOLD


class TestAssignFace:
    def test_no_groups_no_names_creates_new_group(self):
        embedding = _vec(1.0, 0.0, 0.0)
        result = assign_face(embedding, {}, [])
        assert result.kind == "new_group"
        assert np.array_equal(result.new_centroid, embedding.astype(np.float32))

    def test_close_to_existing_group_joins_it(self):
        embedding = _vec(1.0, 0.0, 0.0)
        group = FaceGroupCentroid(group_id=7, centroid=_vec(0.99, 0.01, 0.0), face_count=3)
        result = assign_face(embedding, {}, [group], cluster_threshold=0.9)
        assert result.kind == "grouped"
        assert result.group_id == 7
        assert result.new_centroid is not None

    def test_centroid_update_is_weighted_by_group_size(self):
        embedding = _vec(0.0, 1.0, 0.0)
        group = FaceGroupCentroid(group_id=1, centroid=_vec(1.0, 0.0, 0.0), face_count=3)
        result = assign_face(embedding, {}, [group], cluster_threshold=-1.0)
        # súlyozott átlag: (3*[1,0,0] + [0,1,0]) / 4 = [0.75, 0.25, 0]
        assert result.new_centroid is not None
        np.testing.assert_allclose(result.new_centroid, [0.75, 0.25, 0.0], atol=1e-6)

    def test_far_from_every_group_creates_new_group(self):
        embedding = _vec(0.0, 1.0, 0.0)
        group = FaceGroupCentroid(group_id=1, centroid=_vec(1.0, 0.0, 0.0), face_count=5)
        result = assign_face(embedding, {}, [group], cluster_threshold=0.99)
        assert result.kind == "new_group"

    def test_close_to_named_person_is_suggested_not_grouped(self):
        embedding = _vec(1.0, 0.0, 0.0)
        named = {"Kovács Anna": _vec(0.999, 0.001, 0.0)}
        group = FaceGroupCentroid(group_id=1, centroid=_vec(0.0, 1.0, 0.0), face_count=2)
        result = assign_face(
            embedding, named, [group], suggest_threshold=0.9, cluster_threshold=0.9
        )
        assert result.kind == "suggestion"
        assert result.suggested_name == "Kovács Anna"
        # a javaslat NEM ír csoportot/centroidot
        assert result.group_id is None

    def test_named_suggestion_only_above_threshold_else_falls_back_to_grouping(self):
        embedding = _vec(1.0, 0.0, 0.0)
        # a legjobb névegyezés csak gyengén hasonlít — nem éri el a küszöböt
        named = {"Kovács Anna": _vec(0.5, 0.5, 0.0)}
        group = FaceGroupCentroid(group_id=9, centroid=_vec(0.99, 0.01, 0.0), face_count=1)
        result = assign_face(
            embedding, named, [group], suggest_threshold=0.95, cluster_threshold=0.9
        )
        assert result.kind == "grouped"
        assert result.group_id == 9

    def test_best_matching_group_chosen_among_several(self):
        embedding = _vec(1.0, 0.0, 0.0)
        far = FaceGroupCentroid(group_id=1, centroid=_vec(0.0, 1.0, 0.0), face_count=1)
        near = FaceGroupCentroid(group_id=2, centroid=_vec(0.98, 0.02, 0.0), face_count=1)
        result = assign_face(embedding, {}, [far, near], cluster_threshold=0.5)
        assert result.kind == "grouped"
        assert result.group_id == 2
