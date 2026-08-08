"""#26 (1. lépcső): a szemvonalra igazított arc-indexkép geometriája —
MODELL NÉLKÜL tesztelhető (a szemkoordináták paraméterként jönnek, ld.
`picasapy/faces/align.py` modul-docstringje)."""

from __future__ import annotations

import numpy as np
import pytest

from picasapy.faces.align import (
    compute_alignment_geometry,
    alignment_matrix,
    eye_aligned_face_crop,
)


class TestAlignmentGeometry:
    def test_horizontal_eyes_have_zero_angle(self):
        geometry = compute_alignment_geometry((30, 50), (70, 50), output_size=200)
        assert geometry.angle_deg == pytest.approx(0.0)
        assert geometry.center == pytest.approx((50.0, 50.0))

    def test_vertically_offset_eyes_rotate_90_degrees(self):
        # jobb szem fent, bal szem lent — a szemvonal függőleges
        geometry = compute_alignment_geometry((50, 30), (50, 70), output_size=200)
        assert abs(geometry.angle_deg) == pytest.approx(90.0)

    def test_scale_matches_target_eye_distance(self):
        geometry = compute_alignment_geometry(
            (0, 0), (40, 0), output_size=100, eye_distance_fraction=0.5
        )
        # a cél szemtávolság 100*0.5=50, az eredeti távolság 40 → skála 1.25
        assert geometry.scale == pytest.approx(1.25)

    def test_degenerate_identical_points_do_not_crash(self):
        geometry = compute_alignment_geometry((10, 10), (10, 10), output_size=100)
        assert geometry.scale == pytest.approx(1.0)


class TestAlignmentMatrix:
    def test_eyes_land_symmetrically_around_output_center(self):
        right_eye = (30.0, 50.0)
        left_eye = (70.0, 50.0)
        output_size = 200
        geometry = compute_alignment_geometry(right_eye, left_eye, output_size=output_size)
        matrix = alignment_matrix(geometry)
        transformed = matrix @ np.array([[right_eye[0], left_eye[0]], [right_eye[1], left_eye[1]], [1, 1]])
        right_x, left_x = transformed[0]
        right_y, left_y = transformed[1]
        # a szemvonal a kívánt magasságban, és a kép közepére szimmetrikusan ül
        assert right_y == pytest.approx(output_size * geometry.eye_line_fraction, abs=1e-6)
        assert left_y == pytest.approx(right_y, abs=1e-6)
        assert (right_x + left_x) / 2 == pytest.approx(output_size / 2, abs=1e-6)
        assert (left_x - right_x) == pytest.approx(output_size * 0.35, abs=1e-6)


class TestEyeAlignedFaceCrop:
    def test_output_shape_is_square_of_requested_size(self):
        image = np.zeros((300, 300, 3), dtype=np.uint8)
        crop = eye_aligned_face_crop(image, (120.0, 140.0), (180.0, 140.0), output_size=96)
        assert crop.shape == (96, 96, 3)

    def test_rotated_eyes_still_produce_requested_shape(self):
        image = np.zeros((300, 300, 3), dtype=np.uint8)
        crop = eye_aligned_face_crop(image, (140.0, 100.0), (140.0, 200.0), output_size=64)
        assert crop.shape == (64, 64, 3)

    def test_content_is_preserved_at_eye_positions(self):
        # egy fehér pötty a jobb szem helyén — a kimeneten a geometria
        # által számolt pozíció környékén kell megjelennie (a warpAffine
        # mintavétele miatt kis tűréssel, nem pixel-pontosan)
        image = np.zeros((200, 200, 3), dtype=np.uint8)
        right_eye = (80.0, 100.0)
        left_eye = (120.0, 100.0)
        image[95:106, 75:86] = 255
        output_size = 200
        crop = eye_aligned_face_crop(image, right_eye, left_eye, output_size=output_size)
        geometry = compute_alignment_geometry(right_eye, left_eye, output_size=output_size)
        matrix = alignment_matrix(geometry)
        mapped = matrix @ np.array([right_eye[0], right_eye[1], 1.0])
        target_x, target_y = int(round(mapped[0])), int(round(mapped[1]))
        patch = crop[target_y - 5 : target_y + 5, target_x - 5 : target_x + 5]
        assert patch.mean() > 100  # a fehér folt visszaköszön a várt helyen
