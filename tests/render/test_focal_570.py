"""#570 — `FocalZoom` és `PicnikFocalPixelate`: pontos paraméterezés, közös
körmaszk, natív zoom-kernel.

A #381 az XML-csővezetéket rögzítette, de a natív
`glimmer::RadialBlurImageOperation` visszafejtése kimutatta, hogy a
paramétereket **rossz pozícióból** olvastuk (a fókuszpont után az `Impact`
jön, nem a `Radius`), és hogy a mintaszám/zoomtartomány rögzített képlet.
"""

from __future__ import annotations

import numpy as np
import pytest

from picasapy.ini.filters import parse_filters
from picasapy.render.chain import apply_filters
from picasapy.render.focal import (
    apply_focal_pixelate,
    apply_focal_zoom,
    focal_mask,
    zoom_max_offset,
    zoom_sample_count,
)


@pytest.fixture
def photo() -> np.ndarray:
    rng = np.random.default_rng(19)
    return rng.integers(0, 256, size=(90, 120, 3), dtype=np.uint8)


class TestZoomKernelFormulas:
    @pytest.mark.parametrize(
        ("impact", "expected"),
        [(0.0, 5), (1.0, 6), (24.9, 29), (25.0, 30), (50.0, 30), (100.0, 30)],
    )
    def test_sample_count(self, impact, expected):
        # N = min(trunc(Impact) + 5, 30)
        assert zoom_sample_count(impact) == expected

    @pytest.mark.parametrize(
        ("width", "impact", "expected"),
        [(1000, 50.0, 250), (1000, 0.0, 0), (800, 1.0, 4), (1999, 100.0, 999)],
    )
    def test_max_offset(self, width, impact, expected):
        # floor(width * Impact / 200)
        assert zoom_max_offset(width, impact) == expected


class TestFocalMask:
    def test_centre_is_protected_and_the_outside_is_full(self):
        mask = focal_mask(80, 120, 0.5, 0.5, radius=20.0, hardness=50.0)
        assert mask[40, 60] == pytest.approx(0.0)
        assert mask[0, 0] == pytest.approx(1.0)

    def test_hardness_zero_gives_the_widest_transition(self):
        soft = focal_mask(80, 120, 0.5, 0.5, radius=20.0, hardness=0.0)
        hard = focal_mask(80, 120, 0.5, 0.5, radius=20.0, hardness=100.0)
        # kemény peremnél a részleges (0 és 1 közötti) sáv keskenyebb
        soft_band = ((soft > 0.01) & (soft < 0.99)).mean()
        hard_band = ((hard > 0.01) & (hard < 0.99)).mean()
        assert hard_band < soft_band

    def test_hardness_100_still_leaves_a_transition(self):
        # a natív képlet 101-gyel oszt, nem 100-zal: a belső és a külső
        # sugár SOHA nem esik egybe
        mask = focal_mask(80, 120, 0.5, 0.5, radius=20.0, hardness=100.0)
        assert ((mask > 0.01) & (mask < 0.99)).any()

    def test_focus_point_follows_the_puck(self):
        mask = focal_mask(80, 120, 0.2, 0.8, radius=15.0, hardness=50.0)
        assert mask[int(0.8 * 80), int(0.2 * 120)] == pytest.approx(0.0)
        assert mask[0, -1] == pytest.approx(1.0)

    def test_scale_shrinks_the_radius(self):
        full = focal_mask(80, 120, 0.5, 0.5, radius=20.0, hardness=50.0)
        half = focal_mask(80, 120, 0.5, 0.5, radius=20.0, hardness=50.0, scale=0.5)
        # kisebb léptéken a védett zóna is kisebb → több pixel kap hatást
        assert half.mean() > full.mean()


class TestFocalZoom:
    def test_centre_stays_sharp(self, photo):
        out = apply_focal_zoom(photo, impact=80.0, radius=20.0, hardness=50.0)
        np.testing.assert_array_equal(out[45, 60], photo[45, 60])

    def test_the_edge_is_blurred(self, photo):
        out = apply_focal_zoom(photo, impact=80.0, radius=10.0, hardness=50.0)
        before = float(photo[0:8, 0:8, 0].std())
        after = float(out[0:8, 0:8, 0].std())
        assert after < before

    def test_zero_impact_is_identity(self, photo):
        np.testing.assert_array_equal(apply_focal_zoom(photo, impact=0.0), photo)

    def test_fade_100_is_identity(self, photo):
        out = apply_focal_zoom(photo, impact=80.0, radius=10.0, fade=100.0)
        np.testing.assert_array_equal(out, photo)

    def test_fade_0_is_the_full_effect(self, photo):
        assert not np.array_equal(
            apply_focal_zoom(photo, impact=80.0, radius=10.0, fade=0.0), photo
        )

    @pytest.mark.parametrize("hardness", [0.0, 50.0, 100.0])
    def test_hardness_extremes_render(self, photo, hardness):
        out = apply_focal_zoom(photo, impact=50.0, radius=15.0, hardness=hardness)
        assert out.shape == photo.shape and out.dtype == np.uint8

    def test_off_centre_focus_keeps_that_point_sharp(self, photo):
        out = apply_focal_zoom(photo, x=0.25, y=0.75, impact=90.0, radius=12.0)
        row, col = int(0.75 * 90), int(0.25 * 120)
        np.testing.assert_array_equal(out[row, col], photo[row, col])

    def test_invalid_focus_and_negative_parameters_rejected(self, photo):
        with pytest.raises(ValueError):
            apply_focal_zoom(photo, x=1.5)
        with pytest.raises(ValueError):
            apply_focal_zoom(photo, impact=-1.0)
        with pytest.raises(ValueError):
            apply_focal_zoom(photo, hardness=-1.0)

    def test_input_is_not_mutated(self, photo):
        original = photo.copy()
        apply_focal_zoom(photo, impact=60.0, radius=15.0)
        np.testing.assert_array_equal(photo, original)


class TestFocalPixelate:
    def test_uses_nearest_neighbour_blocks(self, photo):
        """`smoothing = false` → a blokkok élesek: a kép szélén egy
        blokkon belül minden pixel azonos."""
        out = apply_focal_pixelate(photo, impact=10.0, radius=1.0, hardness=100.0)
        block = out[0:6, 0:6]
        # a sarok teljesen a maszkon kívül van (radius=1) → tiszta blokkosítás
        assert np.all(block == block[0, 0])

    def test_centre_stays_sharp(self, photo):
        out = apply_focal_pixelate(photo, impact=20.0, radius=20.0, hardness=50.0)
        np.testing.assert_array_equal(out[45, 60], photo[45, 60])

    def test_fade_100_is_identity(self, photo):
        out = apply_focal_pixelate(photo, impact=20.0, radius=10.0, fade=100.0)
        np.testing.assert_array_equal(out, photo)

    @pytest.mark.parametrize("hardness", [0.0, 50.0, 100.0])
    def test_hardness_extremes_render(self, photo, hardness):
        out = apply_focal_pixelate(photo, impact=20.0, radius=15.0, hardness=hardness)
        assert out.shape == photo.shape and out.dtype == np.uint8

    def test_input_is_not_mutated(self, photo):
        original = photo.copy()
        apply_focal_pixelate(photo, impact=20.0, radius=15.0)
        np.testing.assert_array_equal(photo, original)


class TestParameterPositionsInTheChain:
    """A #570 fő hibája: a paramétereket rossz pozícióból olvastuk. A helyes
    sorrend `x, y, Impact, Radius, Hardness, Fade`."""

    def test_focal_zoom_reads_all_six_parameters(self, photo):
        report = apply_filters(
            photo,
            parse_filters(
                "FocalZoom=1,0.250000,0.750000,80.000000,12.000000,"
                "30.000000,10.000000;"
            ),
        )
        assert report.skipped == ()
        np.testing.assert_array_equal(
            report.image,
            apply_focal_zoom(
                photo,
                x=0.25,
                y=0.75,
                impact=80.0,
                radius=12.0,
                hardness=30.0,
                fade=10.0,
            ),
        )

    def test_focal_pixelate_mind_a_hat_parametert_olvassa(self, photo):
        """#1142: a LÁNCBÓL már nem hívjuk (az eredeti sem futtatja), de a
        #570-ben visszafejtett csővezeték maga változatlanul él — a hat
        paraméter olvasása itt a függvényen marad ellenőrizve."""
        kicsi = apply_focal_pixelate(
            photo, x=0.25, y=0.75, impact=20.0, radius=12.0, hardness=30.0, fade=10.0
        )
        assert not np.array_equal(kicsi, photo)
        for eltero in (
            dict(x=0.75), dict(y=0.25), dict(impact=60.0),
            dict(radius=40.0), dict(hardness=90.0), dict(fade=90.0),
        ):
            alap = dict(
                x=0.25, y=0.75, impact=20.0, radius=12.0, hardness=30.0, fade=10.0
            )
            assert not np.array_equal(
                kicsi, apply_focal_pixelate(photo, **{**alap, **eltero})
            ), f"a {list(eltero)[0]} paraméter nem hat"

    def test_focal_pixelate_a_lancbol_kimarad(self, photo):
        """A `merokit-2` mérése szerint az eredeti Picasa nem futtatja."""
        report = apply_filters(
            photo,
            parse_filters(
                "PicnikFocalPixelate=1,0.250000,0.750000,20.000000,12.000000,"
                "30.000000,10.000000;"
            ),
        )
        assert report.skipped == ("PicnikFocalPixelate",)
        np.testing.assert_array_equal(report.image, photo)

    def test_impact_is_the_third_field_not_the_radius(self, photo):
        """Ha a harmadik mezőt Radius-ként olvasnánk (a régi hiba), a két
        alábbi lánc UGYANAZT adná — a helyes olvasásnál nem."""
        small_impact = apply_filters(
            photo, parse_filters("FocalZoom=1,0.5,0.5,5.000000,10.000000,50.0,0.0;")
        ).image
        big_impact = apply_filters(
            photo, parse_filters("FocalZoom=1,0.5,0.5,90.000000,10.000000,50.0,0.0;")
        ).image
        assert not np.array_equal(small_impact, big_impact)
