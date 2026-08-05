"""`picasapy.render.text_overlay.apply_text_overlay` — determinisztikus
pixel-tesztek. A pozíció-konvenció (relatív [0..1], PicasaPy-saját) és a
Hershey-betűkészlet közelítés — ld. a modul docsztringjét: a Picasa
tényleges betűtípus-renderelésével NEM hasonlítottuk össze (nincs golden)."""

from __future__ import annotations

import numpy as np
import pytest

from picasapy.render.text_overlay import apply_text_overlay


def _blank_image(width: int = 100, height: int = 60) -> np.ndarray:
    return np.zeros((height, width, 3), dtype=np.uint8)


class TestApplyTextOverlay:
    def test_ures_tartalom_no_op(self) -> None:
        image = _blank_image()
        result = apply_text_overlay(image, "", x=0.5, y=0.5)
        np.testing.assert_array_equal(result, image)

    def test_szoveg_pixeleket_valtoztat(self) -> None:
        image = _blank_image()
        result = apply_text_overlay(
            image, "A", x=0.3, y=0.6, font_scale=2.0, color=(255, 255, 255)
        )
        assert not np.array_equal(result, image)

    def test_nem_mutalja_a_bemenetet(self) -> None:
        image = _blank_image()
        original = image.copy()
        apply_text_overlay(image, "Szia", x=0.1, y=0.5)
        np.testing.assert_array_equal(image, original)

    def test_kimenet_merete_megegyezik(self) -> None:
        image = _blank_image()
        result = apply_text_overlay(image, "Szia", x=0.1, y=0.5)
        assert result.shape == image.shape

    def test_ervenytelen_pozicio_value_error(self) -> None:
        image = _blank_image()
        with pytest.raises(ValueError):
            apply_text_overlay(image, "Szia", x=1.5, y=0.5)

    def test_nem_pozitiv_font_scale_value_error(self) -> None:
        image = _blank_image()
        with pytest.raises(ValueError):
            apply_text_overlay(image, "Szia", x=0.5, y=0.5, font_scale=0.0)
