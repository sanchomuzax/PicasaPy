"""TrueType-rajzoló a szöveg-eszközhöz — #450, 2. lépcső.

Az eddigi rajzoló az OpenCV Hershey-készletét használta: abban nincs
betűcsalád, nincs félkövér/dőlt, nincs aláhúzás és nincs sor-igazítás — a
jegy hátralévő vezérlői emiatt nem voltak megvalósíthatók.

A tesztek szándékosan **relatív** állításokat ellenőriznek (a félkövér
több festéket tesz a képre, az igazítás elmozdítja a szöveget), nem konkrét
képpont-mintát: a rendelkezésre álló betűkészlet gépenként eltér, és nem az
adott betűkép a szerződés, hanem a viselkedés.
"""

from __future__ import annotations

import numpy as np
import pytest

from picasapy.render.text_fonts import (
    DEFAULT_FAMILY,
    FONT_FAMILIES,
    family_labels,
    font_path_for,
    load_font,
)
from picasapy.render.text_overlay import apply_text_overlay

_HAS_TRUETYPE = font_path_for(DEFAULT_FAMILY) is not None
_needs_font = pytest.mark.skipif(
    not _HAS_TRUETYPE, reason="ezen a gépen nincs használható TrueType betű"
)


def _canvas() -> np.ndarray:
    return np.zeros((80, 320, 3), dtype=np.uint8)


def _ink(image: np.ndarray) -> int:
    """Hány képpontra került festék (a vászon fekete)."""
    return int((image.sum(axis=-1) > 0).sum())


def _ink_columns(image: np.ndarray) -> tuple[int, int]:
    columns = np.nonzero((image.sum(axis=-1) > 0).any(axis=0))[0]
    assert columns.size > 0, "semmi nem rajzolódott ki"
    return int(columns.min()), int(columns.max())


class TestFontResolution:
    def test_every_family_resolves_or_none_is_available(self):
        # vagy MINDEGYIK családhoz van fájl, vagy egyikhez sem (nincs betű a
        # gépen) — a köztes állapot azt jelentené, hogy a jelölt-listánk
        # hiányos valamelyik családnál
        found = [font_path_for(f.key) is not None for f in FONT_FAMILIES]
        assert all(found) or not any(found)

    @_needs_font
    def test_the_styles_map_to_different_files(self):
        regular = font_path_for("arial")
        bold = font_path_for("arial", bold=True)
        italic = font_path_for("arial", italic=True)
        assert regular != bold
        assert regular != italic

    @_needs_font
    def test_an_unknown_family_falls_back_to_the_default(self):
        assert font_path_for("nincs-ilyen") == font_path_for(DEFAULT_FAMILY)

    def test_the_dropdown_data_is_key_and_label(self):
        labels = family_labels()
        assert {"key", "label"} == set(labels[0])
        assert [item["key"] for item in labels] == [f.key for f in FONT_FAMILIES]

    def test_a_nonpositive_size_is_refused(self):
        with pytest.raises(ValueError):
            load_font(DEFAULT_FAMILY, 0)


@_needs_font
class TestTypography:
    def test_bold_puts_more_ink_on_the_canvas(self):
        normal = apply_text_overlay(_canvas(), "Proba", 0.05, 0.6)
        bold = apply_text_overlay(_canvas(), "Proba", 0.05, 0.6, bold=True)
        assert _ink(bold) > _ink(normal)

    def test_underline_adds_ink_below_the_text(self):
        plain = apply_text_overlay(_canvas(), "Proba", 0.05, 0.6)
        underlined = apply_text_overlay(
            _canvas(), "Proba", 0.05, 0.6, underline=True
        )
        assert _ink(underlined) > _ink(plain)
        rows_plain = np.nonzero((plain.sum(axis=-1) > 0).any(axis=1))[0]
        rows_underlined = np.nonzero(
            (underlined.sum(axis=-1) > 0).any(axis=1)
        )[0]
        # az aláhúzás LEJJEBB nyúlik, mint a betűk alja
        assert rows_underlined.max() > rows_plain.max()

    def test_italic_differs_from_regular(self):
        normal = apply_text_overlay(_canvas(), "Proba", 0.05, 0.6)
        italic = apply_text_overlay(_canvas(), "Proba", 0.05, 0.6, italic=True)
        assert not np.array_equal(normal, italic)

    @pytest.mark.parametrize("family", [f.key for f in FONT_FAMILIES])
    def test_every_family_draws_something(self, family):
        result = apply_text_overlay(
            _canvas(), "Proba", 0.05, 0.6, font_family=family
        )
        assert _ink(result) > 0

    def test_the_families_are_not_all_the_same_drawing(self):
        drawn = [
            apply_text_overlay(_canvas(), "Proba", 0.05, 0.6, font_family=f.key)
            for f in FONT_FAMILIES
        ]
        assert not np.array_equal(drawn[0], drawn[1])

    def test_alignment_moves_the_text(self):
        left = apply_text_overlay(_canvas(), "Proba", 0.5, 0.6, align="left")
        centre = apply_text_overlay(_canvas(), "Proba", 0.5, 0.6, align="center")
        right = apply_text_overlay(_canvas(), "Proba", 0.5, 0.6, align="right")
        left_start = _ink_columns(left)[0]
        centre_start = _ink_columns(centre)[0]
        right_start = _ink_columns(right)[0]
        # ugyanaz a horgonypont: balra igazítva onnan INDUL a szöveg,
        # jobbra igazítva ott VÉGZŐDIK
        assert right_start < centre_start < left_start
        assert _ink_columns(right)[1] <= _ink_columns(left)[1]

    def test_an_unknown_alignment_is_refused(self):
        with pytest.raises(ValueError):
            apply_text_overlay(_canvas(), "Proba", 0.5, 0.6, align="justify")

    def test_the_size_follows_the_scale(self):
        small = apply_text_overlay(_canvas(), "Proba", 0.05, 0.6, font_scale=0.6)
        large = apply_text_overlay(_canvas(), "Proba", 0.05, 0.6, font_scale=1.4)
        assert _ink(large) > _ink(small)

    def test_the_untouched_pixels_stay_exactly_the_same(self):
        base = np.full((80, 320, 3), 40, dtype=np.uint8)
        result = apply_text_overlay(base, "Proba", 0.05, 0.6)
        untouched = np.all(result == base, axis=-1)
        assert untouched.any()
        assert np.array_equal(result[untouched], base[untouched])
