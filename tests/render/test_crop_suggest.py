"""#448: automatikus vágás-javaslatok.

A stratégiák NEVE a Picasa binárisából származik, a belső működésük nem —
ezért a tesztek a dokumentált saját modellt ellenőrzik: hogy a javaslat oda
esik, ahová a stratégia neve ígéri, és hogy a kért képarányt tartja.
"""

from __future__ import annotations

import numpy as np
import pytest

from picasapy.ini.rect64 import Rect64
from picasapy.render.crop_suggest import (
    SUGGESTION_COUNT,
    close_crop_to_faces,
    compose_around_faces,
    crop_by_horizon,
    crop_by_red_green,
    crop_by_variance,
    suggest_crops,
)


def _flat_image(height=240, width=320, value=110) -> np.ndarray:
    return np.full((height, width, 3), value, dtype=np.uint8)


def _aspect_of(rect: Rect64, width: int, height: int) -> float:
    return ((rect.right - rect.left) * width) / ((rect.bottom - rect.top) * height)


def _inside_unit_square(rect: Rect64) -> bool:
    return (
        0.0 <= rect.left < rect.right <= 1.0
        and 0.0 <= rect.top < rect.bottom <= 1.0
    )


class TestSuggestCrops:
    def test_three_suggestions_without_faces(self):
        result = suggest_crops(_flat_image())
        assert len(result) == SUGGESTION_COUNT
        assert [s.key for s in result] == ["variance", "horizon", "red_green"]

    def test_face_strategies_come_first_when_faces_exist(self):
        faces = (Rect64(0.4, 0.3, 0.6, 0.5),)
        result = suggest_crops(_flat_image(), faces=faces)
        assert [s.key for s in result] == [
            "faces_tight", "faces_compose", "variance"
        ]

    def test_every_suggestion_stays_inside_the_picture(self):
        faces = (Rect64(0.02, 0.02, 0.12, 0.14),)   # a bal felső sarokban
        for suggestion in suggest_crops(_flat_image(), faces=faces, aspect=1.0):
            assert _inside_unit_square(suggestion.rect), suggestion.key

    @pytest.mark.parametrize("aspect", [1.0, 16 / 9, 3 / 4])
    def test_requested_aspect_is_kept(self, aspect):
        faces = (Rect64(0.4, 0.3, 0.6, 0.5),)
        for suggestion in suggest_crops(_flat_image(), faces=faces, aspect=aspect):
            assert _aspect_of(suggestion.rect, 320, 240) == pytest.approx(
                aspect, rel=0.02
            ), suggestion.key

    def test_invalid_image_gives_no_suggestions(self):
        assert suggest_crops(np.zeros((4, 4), dtype=np.uint8)) == ()
        assert suggest_crops(np.zeros((1, 1, 3), dtype=np.uint8)) == ()


class TestFaceStrategies:
    def test_tight_crop_contains_every_face(self):
        faces = (Rect64(0.2, 0.2, 0.3, 0.35), Rect64(0.6, 0.25, 0.7, 0.4))
        rect = close_crop_to_faces(faces, 320 / 240, None)
        assert rect is not None
        for face in faces:
            assert rect.left <= face.left and rect.right >= face.right
            assert rect.top <= face.top and rect.bottom >= face.bottom

    def test_tight_crop_is_tighter_than_the_composed_one(self):
        faces = (Rect64(0.45, 0.45, 0.55, 0.55),)
        tight = close_crop_to_faces(faces, 1.0, None)
        composed = compose_around_faces(faces, 1.0, None)
        tight_area = (tight.right - tight.left) * (tight.bottom - tight.top)
        composed_area = (
            (composed.right - composed.left) * (composed.bottom - composed.top)
        )
        assert tight_area < composed_area

    def test_composed_crop_puts_faces_in_the_upper_third(self):
        faces = (Rect64(0.45, 0.45, 0.55, 0.55),)
        rect = compose_around_faces(faces, 1.0, None)
        height = rect.bottom - rect.top
        face_center = 0.5
        relative = (face_center - rect.top) / height
        assert relative == pytest.approx(1 / 3, abs=0.02)

    def test_no_faces_means_no_face_suggestion(self):
        assert close_crop_to_faces((), 1.0, None) is None
        assert compose_around_faces((), 1.0, None) is None


class TestContentStrategies:
    def test_variance_finds_the_detailed_corner(self):
        image = _flat_image()
        # zajos (részletgazdag) folt a JOBB ALSÓ negyedben
        rng = np.random.default_rng(11)
        image[150:230, 200:310] = rng.integers(0, 256, (80, 110, 3), dtype=np.uint8)
        rect = crop_by_variance(image, 320 / 240, None)
        center_x = (rect.left + rect.right) / 2
        center_y = (rect.top + rect.bottom) / 2
        assert center_x > 0.5 and center_y > 0.5

    def test_horizon_lands_on_a_third_line(self):
        image = _flat_image()
        image[:96] = 30          # sötét ég, éles határ a kép 40%-ánál
        rect = crop_by_horizon(image, 320 / 240, None)
        horizon = 96 / 240
        relative = (horizon - rect.top) / (rect.bottom - rect.top)
        # a felső harmadhoz igazít, ha a horizont a kép felső felében van
        assert relative == pytest.approx(1 / 3, abs=0.05)

    def test_red_green_follows_the_colour_blob(self):
        image = _flat_image()
        image[30:90, 20:110] = (230, 60, 60)   # piros folt a BAL FELSŐ részen
        rect = crop_by_red_green(image, 320 / 240, None)
        assert (rect.left + rect.right) / 2 < 0.5
        assert (rect.top + rect.bottom) / 2 < 0.5

    def test_content_strategies_stay_inside_the_picture(self):
        image = _flat_image()
        for rect in (
            crop_by_variance(image, 320 / 240, 16 / 9),
            crop_by_horizon(image, 320 / 240, 16 / 9),
            crop_by_red_green(image, 320 / 240, 16 / 9),
        ):
            assert _inside_unit_square(rect)
