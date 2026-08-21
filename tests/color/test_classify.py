"""Átlagszín-besorolás (#383): tiszta színminták + határesetek.

A besorolási küszöbök a MI döntésünk, nem mért Picasa-viselkedés (ld. a
`classify.py` modul-docstringjét) — a tesztek ezért a saját, dokumentált
konstansainkkal önkonzisztensek, plusz az issue-ban explicit megnevezett
3 hexa-mintát (`#ff0000` → red, `#808080` → gray, `#ffc0cb` → pink)
ellenőrzik szó szerint."""

import colorsys

import numpy as np
import pytest

from picasapy.color import (
    average_color,
    avgcolor_to_rgb,
    classify_color,
    resolve_color_alias,
    rgb_to_avgcolor,
)


def _hex(value: str) -> tuple[int, int, int]:
    value = value.lstrip("#")
    return (int(value[0:2], 16), int(value[2:4], 16), int(value[4:6], 16))


class TestIssueExamples:
    """A #383 issue szövegében szó szerint megnevezett 3 minta."""

    def test_pure_red(self):
        assert classify_color(*_hex("#ff0000")) == "red"

    def test_mid_gray(self):
        assert classify_color(*_hex("#808080")) == "gray"

    def test_pink(self):
        assert classify_color(*_hex("#ffc0cb")) == "pink"


class TestAchromatic:
    def test_black(self):
        assert classify_color(0, 0, 0) == "black"

    def test_white(self):
        assert classify_color(255, 255, 255) == "white"

    def test_near_black_below_threshold(self):
        assert classify_color(10, 10, 11) == "black"

    def test_near_white_above_threshold(self):
        assert classify_color(250, 248, 251) == "white"


class TestHueBands:
    """Szintetikus HSV-mintákat generálunk saját sávhatárainkon belülről,
    hogy a teszt a KONSTANSOKKAL legyen önkonzisztens, ne egy külső
    referenciával."""

    @pytest.mark.parametrize(
        "hue_deg,expected",
        [
            (0, "red"),
            (5, "red"),
            (350, "red"),
            (30, "orange"),
            (60, "yellow"),
            (120, "green"),
            (200, "blue"),
            (280, "purple"),
        ],
    )
    def test_band(self, hue_deg, expected):
        r, g, b = colorsys.hsv_to_rgb(hue_deg / 360.0, 0.9, 0.9)
        rgb = (round(r * 255), round(g * 255), round(b * 255))
        assert classify_color(*rgb) == expected

    def test_pink_needs_moderate_saturation_and_high_value(self):
        # Ugyanaz a hue, mint a pink-mintánál, de magas telítettséggel —
        # ez már NEM pink, hanem a hue-sáv szerinti "purple"/"red".
        r, g, b = colorsys.hsv_to_rgb(340 / 360.0, 0.95, 0.95)
        rgb = (round(r * 255), round(g * 255), round(b * 255))
        assert classify_color(*rgb) != "pink"

    def test_pink_needs_high_value(self):
        # Ugyanaz a hue/telítettség, mint a pink-mintánál, de sötét — ez
        # már NEM pink (alacsony V-nél a "pink" benyomás elvész).
        r, g, b = colorsys.hsv_to_rgb(340 / 360.0, 0.3, 0.2)
        rgb = (round(r * 255), round(g * 255), round(b * 255))
        assert classify_color(*rgb) != "pink"


class TestAverageColor:
    def test_solid_color(self):
        image = np.zeros((4, 4, 3), dtype=np.uint8)
        image[:, :] = (10, 20, 30)
        assert average_color(image) == (10, 20, 30, 255)

    def test_half_and_half_averages(self):
        image = np.zeros((2, 4, 3), dtype=np.uint8)
        image[:, :2] = (0, 0, 0)
        image[:, 2:] = (100, 200, 250)
        assert average_color(image) == (50, 100, 125, 255)

    def test_bgr_order_is_reversed(self):
        image = np.zeros((2, 2, 3), dtype=np.uint8)
        image[:, :] = (30, 20, 10)  # BGR
        assert average_color(image, order="bgr") == (10, 20, 30, 255)

    def test_picasa_truncates_and_averages_all_bgra_channels(self):
        """A 0xAARRGGBB érték szintetikus, hordozható őre (#1171).

        A valódi PMP-korpusz helyben elérhető lehet, de személyes és
        gitignore-olt, ezért azonos, 2×2 BGRA-pixelekből rögzítjük a
        Picasa utasításszinten kimért csonkolását és bájtsorrendjét.
        """
        image = np.array(
            [
                [(9, 19, 29, 254), (10, 20, 30, 255)],
                [(10, 20, 30, 255), (10, 20, 30, 255)],
            ],
            dtype=np.uint8,
        )

        assert average_color(image, order="bgr") == (29, 19, 9, 254)
        assert rgb_to_avgcolor(29, 19, 9, 254) == 0xFE1D1309

    @pytest.mark.parametrize("shape", [(1, 2, 3), (2, 1, 3), (1, 1, 4)])
    def test_picasa_does_not_calculate_under_two_by_two(self, shape):
        assert average_color(np.zeros(shape, dtype=np.uint8)) is None

    def test_rejects_wrong_shape(self):
        with pytest.raises(ValueError):
            average_color(np.zeros((4, 4), dtype=np.uint8))

    def test_rejects_empty(self):
        with pytest.raises(ValueError):
            average_color(np.zeros((0, 0, 3), dtype=np.uint8))

    def test_rejects_unknown_order(self):
        with pytest.raises(ValueError):
            average_color(np.zeros((1, 1, 3), dtype=np.uint8), order="xyz")


class TestAvgcolorPacking:
    def test_roundtrip(self):
        assert avgcolor_to_rgb(rgb_to_avgcolor(1, 2, 3)) == (1, 2, 3)

    def test_known_value(self):
        assert rgb_to_avgcolor(255, 0, 0) == 0xFFFF0000
        assert rgb_to_avgcolor(1, 2, 3, 4) == 0x04010203
        assert avgcolor_to_rgb(0x00FF00) == (0, 255, 0)


class TestResolveAlias:
    @pytest.mark.parametrize(
        "word,expected",
        [
            ("blue", "blue"),
            ("BLUE", "blue"),
            ("kék", "blue"),
            ("Kék", "blue"),
            ("piros", "red"),
            ("rózsaszín", "pink"),
            ("szürke", "gray"),
        ],
    )
    def test_known(self, word, expected):
        assert resolve_color_alias(word) == expected

    def test_unknown_is_none(self):
        assert resolve_color_alias("türkiz") is None

    def test_empty_is_none(self):
        assert resolve_color_alias("") is None
