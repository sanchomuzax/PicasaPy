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

    def test_negativ_outline_thickness_value_error(self) -> None:
        image = _blank_image()
        with pytest.raises(ValueError):
            apply_text_overlay(image, "Szia", x=0.5, y=0.5, outline_thickness=-1)

    def test_ervenytelen_opacity_value_error(self) -> None:
        image = _blank_image()
        with pytest.raises(ValueError):
            apply_text_overlay(image, "Szia", x=0.5, y=0.5, opacity=1.5)


class TestOutlineAndFill:
    """#450: kétszínű szöveg (kitöltés + körvonal) + opacity + fill_enabled."""

    def test_korvonal_nelkul_ugyanaz_mint_eddig(self) -> None:
        """outline_thickness=0 (alapérték) → a régi hívók kimenete változatlan."""
        image = _blank_image()
        old = apply_text_overlay(
            image, "A", x=0.3, y=0.6, font_scale=2.0, color=(255, 255, 255)
        )
        new = apply_text_overlay(
            image,
            "A",
            x=0.3,
            y=0.6,
            font_scale=2.0,
            color=(255, 255, 255),
            outline_color=(0, 0, 0),
            outline_thickness=0,
        )
        np.testing.assert_array_equal(old, new)

    def test_korvonal_szine_megjelenik(self) -> None:
        image = _blank_image()
        result = apply_text_overlay(
            image,
            "A",
            x=0.3,
            y=0.6,
            font_scale=3.0,
            thickness=1,
            color=(255, 255, 255),
            outline_color=(10, 20, 30),
            outline_thickness=3,
        )
        assert np.any(np.all(result == (10, 20, 30), axis=-1))

    def test_fill_enabled_false_csak_korvonal(self) -> None:
        image = _blank_image()
        result = apply_text_overlay(
            image,
            "A",
            x=0.3,
            y=0.6,
            font_scale=3.0,
            color=(255, 255, 255),
            outline_color=(10, 20, 30),
            outline_thickness=3,
            fill_enabled=False,
        )
        # a tiszta kitöltő szín (255,255,255) sehol nem jelenik meg
        assert not np.any(np.all(result == (255, 255, 255), axis=-1))
        assert np.any(np.all(result == (10, 20, 30), axis=-1))

    def test_fill_enabled_false_korvonal_nelkul_no_op(self) -> None:
        image = _blank_image()
        result = apply_text_overlay(
            image, "A", x=0.3, y=0.6, fill_enabled=False,
        )
        np.testing.assert_array_equal(result, image)

    def test_opacity_csak_a_szoveg_pixeleit_erinti(self) -> None:
        image = np.full((60, 100, 3), 40, dtype=np.uint8)
        result = apply_text_overlay(
            image, "A", x=0.3, y=0.6, font_scale=2.0, color=(255, 255, 255),
            opacity=0.5,
        )
        unchanged_mask = np.all(result == image, axis=-1)
        # a kép nagy része (a szöveg nem érinti) bitre pontosan változatlan
        assert unchanged_mask.mean() > 0.8
        # de VAN eltérő (rajzolt, félig áttetsző) képpont
        assert not unchanged_mask.all()
        changed = result[~unchanged_mask]
        # a félig áttetsző fehér szöveg a 40-es háttéren se nem 40 (eredeti
        # hátér), se nem tiszta 255 (teljesen átlátszatlan rajzolás)
        assert np.any((changed != 40) & (changed != 255))

    def test_opacity_1_megegyezik_a_default_rajzolassal(self) -> None:
        image = _blank_image()
        opaque = apply_text_overlay(
            image, "A", x=0.3, y=0.6, font_scale=2.0, color=(255, 255, 255)
        )
        explicit = apply_text_overlay(
            image, "A", x=0.3, y=0.6, font_scale=2.0, color=(255, 255, 255),
            opacity=1.0,
        )
        np.testing.assert_array_equal(opaque, explicit)

    def test_nem_mutalja_a_bemenetet_korvonallal_es_opacityvel(self) -> None:
        image = _blank_image()
        original = image.copy()
        apply_text_overlay(
            image, "Szia", x=0.1, y=0.5,
            outline_color=(0, 0, 0), outline_thickness=2, opacity=0.4,
        )
        np.testing.assert_array_equal(image, original)
