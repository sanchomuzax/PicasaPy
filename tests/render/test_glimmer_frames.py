"""#381: `glimmer_frames` — Border/RoundedEdges/DropShadow/MuseumMatte/
Polaroid min/alap/max határeset-tesztjei. Mind az öt effekt MEGNÖVELI a
kép méretét — a teszt a méretnövekedést és a fő paraméter-hatásokat ellenőrzi.
"""

from __future__ import annotations

import numpy as np
import pytest

from picasapy.render import glimmer_frames as f


@pytest.fixture
def image() -> np.ndarray:
    rng = np.random.default_rng(41)
    return rng.integers(20, 235, size=(48, 64, 3), dtype=np.uint8)


def _assert_valid(result):
    assert result.dtype == np.uint8
    assert result.shape[2] == 3


class TestBorder:
    @pytest.mark.parametrize(
        "outer_thickness,inner_thickness,corner_radius,caption_height",
        [(0.0, 0.0, 0.0, 0.0), (20.0, 5.0, 0.0, 0.0), (100.0, 100.0, 20.0, 8.0)],
    )
    def test_hatarok(self, image, outer_thickness, inner_thickness, corner_radius, caption_height):
        result = f.apply_border(
            image,
            outer_thickness=outer_thickness,
            inner_thickness=inner_thickness,
            corner_radius=corner_radius,
            caption_height=caption_height,
        )
        _assert_valid(result)
        assert result.shape[0] >= image.shape[0]

    def test_nulla_vastagsag_valtozatlan_meret(self, image):
        result = f.apply_border(image, outer_thickness=0.0, inner_thickness=0.0)
        assert result.shape == image.shape

    def test_kulso_szin_a_szelen(self, image):
        result = f.apply_border(image, outer_color=(9, 8, 7), outer_thickness=10.0, inner_thickness=0.0)
        assert tuple(result[0, 0]) == (9, 8, 7)


class TestRoundedEdges:
    def test_alapertelmezett_sugar(self, image):
        result = f.apply_rounded_edges(image)
        _assert_valid(result)
        assert result.shape == image.shape  # nincs vastagság, csak sarok-vágás

    def test_nulla_sugar_valtozatlan(self, image):
        np.testing.assert_array_equal(f.apply_rounded_edges(image, corner_radius=0.0), image)

    def test_max_sugar_lekerekit(self, image):
        height, width = image.shape[:2]
        result = f.apply_rounded_edges(image, corner_radius=min(height, width) / 2.0, outer_color=(1, 2, 3))
        assert tuple(result[0, 0]) == (1, 2, 3)


class TestDropShadow:
    @pytest.mark.parametrize(
        "distance,angle,blur,fade", [(0.0, 0.0, 0.0, 0.0), (4.0, 90.0, 10.0, 30.0), (30.0, 360.0, 100.0, 100.0)]
    )
    def test_hatarok(self, image, distance, angle, blur, fade):
        result = f.apply_drop_shadow(image, distance=distance, angle=angle, blur=blur, fade=fade)
        _assert_valid(result)
        assert result.shape[0] > image.shape[0]

    def test_a_kep_kozepen_marad(self, image):
        result = f.apply_drop_shadow(image, distance=4.0, angle=90.0, blur=10.0, fade=30.0)
        top = (result.shape[0] - image.shape[0]) // 2
        left = (result.shape[1] - image.shape[1]) // 2
        np.testing.assert_array_equal(result[top : top + image.shape[0], left : left + image.shape[1]], image)


class TestMuseumMatte:
    @pytest.mark.parametrize("outer_thickness,inner_thickness", [(0.0, 0.0), (25.0, 40.0), (100.0, 100.0)])
    def test_hatarok(self, image, outer_thickness, inner_thickness):
        result = f.apply_museum_matte(image, outer_thickness=outer_thickness, inner_thickness=inner_thickness)
        _assert_valid(result)
        assert result.shape[0] >= image.shape[0]


class TestPolaroid:
    @pytest.mark.parametrize("rotate", [-10.0, 5.0, 10.0])
    def test_hatarok(self, image, rotate):
        result = f.apply_polaroid(image, rotate=rotate)
        _assert_valid(result)
        assert result.shape[0] > image.shape[0]

    def test_negyzetes_kivagas_az_alapja(self, image):
        result = f.apply_polaroid(image, rotate=0.0)
        # forgatás nélkül is nagyobb, mint az eredeti (a keret miatt)
        assert result.shape[0] > image.shape[0] and result.shape[1] > image.shape[1]
