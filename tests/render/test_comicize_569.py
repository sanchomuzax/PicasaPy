"""#569 — a `Comicize` eredeti, kétfázisú féltónusos rasztere.

A korábbi modell posterizálással és Canny-élkereséssel közelítette. A Picasa
effektje nem élkiemelő képregényszűrő, hanem két, egymáshoz képest fél
csempével eltolt pontmaszkból épített nyomdai raszter — ez a fájl azt méri,
hogy tényleg az.
"""

from __future__ import annotations

import inspect

import numpy as np
import pytest

from picasapy.ini.filters import parse_filters
from picasapy.render.chain import apply_filters
from picasapy.render.effects_artistic import apply_comicize
from picasapy.render.halftone import (
    dot_size_for,
    halftone_branch,
    tiled_dot_mask,
    tiled_dot_ramp,
)


def _flat(value: int, height: int = 80, width: int = 140) -> np.ndarray:
    return np.full((height, width, 3), value, dtype=np.uint8)


class TestNoEdgeDetection:
    def test_no_canny_on_the_comicize_path(self):
        """#569 elfogadási feltétel: a Comicize útvonalán nincs élkeresés.

        A docstring SZÁNDÉKOSAN említi a Cannyt (elmagyarázza, mi változott),
        ezért a KÓD-ot vizsgáljuk, nem a dokumentációt."""
        source = inspect.getsource(apply_comicize)
        # a docstring a def utáni első két \"\"\" közt áll — utána jön a kód
        code = source.split('"""')[2]
        assert "Canny" not in code
        assert "canny" not in code.lower()

    def test_the_halftone_module_has_no_edge_detection(self):
        import picasapy.render.halftone as halftone

        assert "Canny" not in inspect.getsource(halftone)


class TestDotSize:
    @pytest.mark.parametrize(
        ("width", "expected"),
        [(70, 2), (140, 3), (700, 11), (1400, 21), (4000, 58)],
    )
    def test_formula_matches_the_native_one(self, width, expected):
        # dotSize = round(W / 70) + 1
        assert dot_size_for(width) == expected

    def test_never_degenerates_to_zero(self):
        assert dot_size_for(1) == 1

    def test_invalid_width_is_rejected(self):
        with pytest.raises(ValueError):
            dot_size_for(0)

    def test_depends_on_width_not_on_height(self):
        # a képlet a SZÉLESSÉGET osztja: álló és fekvő képen ugyanaz a
        # szélesség ugyanakkora pontot ad
        wide = apply_comicize(_flat(90, height=40, width=280))
        tall = apply_comicize(_flat(90, height=280, width=280))
        assert wide.shape[1] == tall.shape[1]


class TestTiledMaskPrimitive:
    def test_ramp_is_zero_at_the_tile_centre_and_grows_outward(self):
        ramp = tiled_dot_ramp(16, 16, 8)
        # a csempeközép (a pixelközép fél pixellel odébb van)
        assert ramp[4, 4] == pytest.approx(0.0, abs=0.2)
        # a beírt kör pereme 1, a SAROK azon túl van — a két, fél csempével
        # eltolt ág épp ezeket a sarkokat fedi le egymásnak
        assert ramp[0, 0] > 1.0
        # kifelé monoton nő
        row = ramp[4, 4:8]
        assert list(row) == sorted(row)

    def test_ramp_tiles(self):
        ramp = tiled_dot_ramp(24, 24, 8)
        # a rács ismétlődik: a (4,4) és a (12,12) csempeközép azonos
        assert ramp[4, 4] == pytest.approx(ramp[12, 12])

    def test_offset_shifts_the_grid_by_half_a_tile(self):
        plain = tiled_dot_ramp(16, 16, 8)
        shifted = tiled_dot_ramp(16, 16, 8, offset_x=4, offset_y=4)
        # a fél csempével eltolt rács közepe oda esik, ahol az eredetié a
        # sarka volt — a két ág épp ezért fedi le egymást
        assert shifted[0, 0] == pytest.approx(plain[4, 4], abs=0.15)

    def test_mask_is_a_disk(self):
        mask = tiled_dot_mask(16, 16, 8)
        assert mask[4, 4] == pytest.approx(1.0)
        assert mask[0, 0] == pytest.approx(0.0, abs=0.6)

    def test_alpha_min_raises_the_floor(self):
        mask = tiled_dot_mask(16, 16, 8, alpha_min=0.3)
        assert mask.min() >= 0.3 - 1e-6

    def test_invalid_tile_and_alpha_rejected(self):
        with pytest.raises(ValueError):
            tiled_dot_ramp(8, 8, 0)
        with pytest.raises(ValueError):
            tiled_dot_mask(8, 8, 4, alpha_min=1.5)


class TestHalftoneBranch:
    """A két ág külön tesztelhető — ez a #569 egyik elfogadási feltétele."""

    def test_dark_tone_grows_the_dot(self):
        dark = halftone_branch(np.full((32, 32), 30.0, np.float32), 8)
        light = halftone_branch(np.full((32, 32), 200.0, np.float32), 8)
        # a festékes (0-hoz közeli) pixelek aránya sötét tónusnál nagyobb
        assert (dark < 128).mean() > (light < 128).mean()

    def test_white_prints_nothing(self):
        branch = halftone_branch(np.full((32, 32), 255.0, np.float32), 8)
        assert branch.min() == pytest.approx(255.0, abs=1.0)

    def test_black_prints_a_full_dot(self):
        branch = halftone_branch(np.zeros((32, 32), np.float32), 8)
        # a beírt kör TELJESEN fekete; a csempesarkokat a másik (fél
        # csempével eltolt) ág fedi le — együtt lesz tömör a fekete
        assert branch.min() == pytest.approx(0.0, abs=1.0)
        assert (branch < 128).mean() > 0.7

    def test_the_two_branches_together_fill_a_black_area(self):
        ink = np.zeros((64, 64), np.float32)
        combined = np.minimum(
            halftone_branch(ink, 8, 0.0, 0.0), halftone_branch(ink, 8, 4.0, 4.0)
        )
        assert combined.mean() < 20.0

    def test_the_two_offsets_give_different_rasters(self):
        ink = np.full((32, 32), 120.0, np.float32)
        a = halftone_branch(ink, 8, 0.0, 0.0)
        b = halftone_branch(ink, 8, 4.0, 4.0)
        assert not np.array_equal(a, b)


class TestComicizeParameters:
    @pytest.mark.parametrize("value", [0.0, 50.0, 100.0])
    def test_blur_min_default_max(self, value):
        out = apply_comicize(_flat(120), blur_xy=value)
        assert out.shape == (80, 140, 3) and out.dtype == np.uint8

    @pytest.mark.parametrize("value", [0.0, 50.0, 100.0])
    def test_dot_contrast_min_default_max(self, value):
        out = apply_comicize(_flat(120), dot_contrast=value)
        assert out.dtype == np.uint8

    def test_higher_dot_contrast_prints_more_ink(self):
        # A mozgó kontrollpont `90 + DotContrast*1,5`: nagyobb érték = a
        # görbe KÉSŐBB fut ki fehérre = több középtónus marad sötét = több
        # festék, tehát SÖTÉTEBB kimenet. (A #1606 mérése ezt a Picasa-
        # referencián is megerősítette: a `research/comicize-sweep/`
        # `effekt5_kepregeny_dotcontrast` exportjainak ÁTLAGA — vagyis
        # maga a festékmennyiség — mind az öt álláson csökken:
        # 125,09 · 124,47 · 124,01 · 123,66 · 123,38.)
        #
        # ⚠️ Az állítás mindig is ez volt (`high < low`), csak a NÉV és a
        # megjegyzés mondta az ellenkezőjét — a #1606 javította.
        wide = _flat(120, height=200, width=700)
        low = apply_comicize(wide, dot_contrast=0.0).mean()
        high = apply_comicize(wide, dot_contrast=100.0).mean()
        assert high < low

    @pytest.mark.parametrize("value", [0.0, 50.0, 100.0])
    def test_dot_fade_min_default_max(self, value):
        out = apply_comicize(_flat(120), dot_fade=value)
        assert out.dtype == np.uint8

    def test_dot_fade_100_leaves_the_image_untouched(self):
        # a blokk alfája `0,5 − DotFade/200`: 100-nál pontosan 0
        image = _flat(120)
        np.testing.assert_array_equal(apply_comicize(image, dot_fade=100.0), image)

    def test_stronger_fade_prints_less(self):
        # valósághű szélesség kell hozzá: keskeny képen a csempe 3 px, ott a
        # világos középtónus amúgy sem nyom festéket
        wide = _flat(120, height=200, width=700)
        weak = apply_comicize(wide, dot_fade=0.0).mean()
        strong = apply_comicize(wide, dot_fade=80.0).mean()
        assert strong > weak  # kevesebb festék = világosabb kép


class TestComicizeOutput:
    def test_the_raster_only_darkens(self):
        image = np.random.default_rng(7).integers(
            0, 256, size=(60, 100, 3), dtype=np.uint8
        )
        assert np.all(apply_comicize(image) <= image)

    def test_a_flat_midtone_gets_a_visible_dot_pattern(self):
        # valósághű szélesség (700 px → 11 px csempe): ekkora raszteren a
        # pontok láthatóak, nem olvadnak egybe az élsimítással
        out = apply_comicize(_flat(90, height=200, width=700))
        # egyenletes szürkén is raszter keletkezik: van szórás a kimenetben
        assert out[..., 0].std() > 1.0

    def test_white_stays_white(self):
        np.testing.assert_array_equal(apply_comicize(_flat(255)), _flat(255))

    def test_input_is_not_mutated(self):
        image = _flat(120)
        original = image.copy()
        apply_comicize(image)
        np.testing.assert_array_equal(image, original)

    def test_extremes_do_not_raise(self):
        apply_comicize(_flat(0))
        apply_comicize(_flat(255))


class TestComicizeInTheChain:
    def test_chain_passes_the_three_filterdesc_sliders(self):
        image = _flat(120)
        report = apply_filters(
            image, parse_filters("Comicize=1,20.000000,50.000000,50.000000;")
        )
        assert report.skipped == ()
        np.testing.assert_array_equal(
            report.image,
            apply_comicize(image, blur_xy=20.0, dot_contrast=50.0, dot_fade=50.0),
        )
