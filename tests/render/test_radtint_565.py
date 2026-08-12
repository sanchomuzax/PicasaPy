"""#565 — `radtint` (Sugaras árnyalás): radiális SZORZÓ-tint.

A jegy elfogadási feltételeit méri: a középpont változatlan, a külső terület
multiply-tintelt, a Feather min/alap/max és a nem középre tett fókuszpont is
viselkedik, és az „ismeretlen effekt" jelzés megszűnt.
"""

from __future__ import annotations

import numpy as np
import pytest

from picasapy.ini.filters import parse_filters
from picasapy.render.chain import apply_filters
from picasapy.render.tinting import apply_radtint, radtint_lut

_TINT = (255, 128, 64)


@pytest.fixture
def flat() -> np.ndarray:
    """Egyenletes szürke — így a maszk hatása tisztán mérhető."""
    return np.full((80, 120, 3), 200, dtype=np.uint8)


class TestRadtintLut:
    def test_smoothstep_shape(self):
        lut = radtint_lut()
        assert len(lut) == 1024
        assert lut[0] == pytest.approx(0.0)
        assert lut[-1] == pytest.approx(1.0)
        # köbös smoothstep: a felezőpont pontosan 0,5, és a görbe monoton
        assert lut[len(lut) // 2] == pytest.approx(0.5, abs=1e-3)
        assert np.all(np.diff(lut) >= 0)

    def test_derivative_vanishes_at_the_ends(self):
        # a smoothstep lényege: a két végén LAPOS — ettől nincs látható
        # törésvonal sem a fókuszpont körül, sem a kép szélén
        lut = radtint_lut()
        d = np.diff(lut)
        assert d[0] < d[len(d) // 2]
        assert d[-1] < d[len(d) // 2]

    def test_invalid_size_is_rejected(self):
        with pytest.raises(ValueError):
            radtint_lut(1)


class TestRadtintPixelOperation:
    def test_focus_point_is_untouched(self, flat):
        out = apply_radtint(flat, x=0.5, y=0.5, feather=0.25, color=_TINT)
        assert tuple(out[40, 60]) == (200, 200, 200)

    def test_outer_area_is_multiplied_by_the_tint(self, flat):
        # a sarok a legtávolabbi pont → teljes tint: source * tint / 256
        out = apply_radtint(flat, x=0.5, y=0.5, feather=0.25, color=_TINT)
        expected = tuple(int(round(200 * c / 256)) for c in _TINT)
        assert tuple(out[0, 0]) == expected

    def test_multiply_never_brightens(self, flat):
        # a szorzás 255/256-nál nem nagyobb tényezővel dolgozik — a kép
        # sosem világosodhat ki tőle (ez különbözteti meg a dir_tint
        # „szín FELÉ keverésétől")
        out = apply_radtint(flat, x=0.5, y=0.5, feather=1.0, color=_TINT)
        assert np.all(out <= flat)

    def test_transition_is_monotone_outward(self, flat):
        out = apply_radtint(flat, x=0.5, y=0.5, feather=1.0, color=_TINT)
        # a középső sor a középponttól a jobb szélig: a kék csatorna
        # (legerősebb tint) monoton csökken kifelé haladva
        row = out[40, 60:, 2].astype(int)
        assert np.all(np.diff(row) <= 0)

    def test_alpha_like_shape_is_preserved(self, flat):
        out = apply_radtint(flat, x=0.5, y=0.5, feather=0.25, color=_TINT)
        assert out.shape == flat.shape and out.dtype == np.uint8


class TestRadtintFeather:
    @pytest.mark.parametrize("feather", [0.0, 0.25, 1.0])
    def test_min_default_max_all_render(self, flat, feather):
        out = apply_radtint(flat, x=0.5, y=0.5, feather=feather, color=_TINT)
        assert not np.array_equal(out, flat)
        # a fókuszpont MINDEN feather-értéknél érintetlen marad
        assert tuple(out[40, 60]) == (200, 200, 200)

    def test_larger_feather_tints_a_wider_area(self, flat):
        narrow = apply_radtint(flat, x=0.5, y=0.5, feather=0.1, color=_TINT)
        wide = apply_radtint(flat, x=0.5, y=0.5, feather=0.9, color=_TINT)
        # a szélesebb átmenet több pixelt érint
        assert (wide != 200).sum() > (narrow != 200).sum()

    def test_zero_feather_is_a_hard_edge(self, flat):
        out = apply_radtint(flat, x=0.5, y=0.5, feather=0.0, color=_TINT)
        # nulla szélességű sáv: nincs átmenet — minden pixel VAGY teljesen
        # érintetlen, VAGY teljesen tintelt, köztes érték nincs
        expected = np.array(
            [int(round(200 * c / 256)) for c in _TINT], dtype=np.uint8
        )
        untouched = (out == 200).all(axis=-1)
        full = (out == expected).all(axis=-1)
        assert np.all(untouched | full)
        assert untouched.any() and full.any()


class TestRadtintOffCenterFocus:
    def test_focus_follows_the_puck(self, flat):
        out = apply_radtint(flat, x=0.2, y=0.3, feather=0.5, color=_TINT)
        focus = out[int(0.3 * 80), int(0.2 * 120)]
        assert tuple(focus) == (200, 200, 200)
        # a fókuszponttól legtávolabbi sarok viszont teljes tintet kap
        expected = tuple(int(round(200 * c / 256)) for c in _TINT)
        assert tuple(out[-1, -1]) == expected


class TestRadtintInTheChain:
    def test_full_parameter_form_round_trips(self, flat):
        result = apply_filters(
            flat, parse_filters("radtint=1,0.2,0.3,0.5,ffff8040;")
        )
        assert result.skipped == ()
        direct = apply_radtint(flat, x=0.2, y=0.3, feather=0.5, color=_TINT)
        assert np.array_equal(result.image, direct)

    def test_color_is_optional(self, flat):
        # #357: a szín elhagyható — a lánc az alapértelmezett színnel fut,
        # nem dob kivételt
        result = apply_filters(flat, parse_filters("radtint=1,0.5,0.5,0.25;"))
        assert result.skipped == ()

    def test_bare_marker_form_renders(self, flat):
        result = apply_filters(flat, parse_filters("radtint=1;"))
        assert result.skipped == ()
        assert not np.array_equal(result.image, flat)
