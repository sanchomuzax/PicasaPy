"""`picasapy.printing.layout` — determinisztikus, Qt-független nyomtatás-
elrendezés-geometria (#32, RÉSZLEGES kör: egyszerű FIT/FILL elrendezés)."""

from __future__ import annotations

import pytest

from picasapy.printing.layout import (
    PageGeometry,
    PrintFitMode,
    PrintOrientation,
    compute_print_layout,
    resolve_orientation,
)


class TestPageGeometry:
    def test_printable_area_subtracts_margin_both_sides(self):
        page = PageGeometry(width=200, height=100, margin=10)
        assert page.printable_width == 180
        assert page.printable_height == 80

    def test_zero_margin_is_full_page(self):
        page = PageGeometry(width=200, height=100)
        assert page.printable_width == 200
        assert page.printable_height == 100

    @pytest.mark.parametrize("width,height", [(0, 100), (-1, 100), (100, 0), (100, -1)])
    def test_rejects_non_positive_size(self, width, height):
        with pytest.raises(ValueError):
            PageGeometry(width=width, height=height)

    def test_rejects_negative_margin(self):
        with pytest.raises(ValueError):
            PageGeometry(width=100, height=100, margin=-1)

    def test_rejects_margin_at_least_half_the_page(self):
        with pytest.raises(ValueError):
            PageGeometry(width=100, height=100, margin=50)


class TestResolveOrientation:
    def test_auto_picks_landscape_for_wide_image(self):
        assert (
            resolve_orientation(2000, 1000, PrintOrientation.AUTO)
            == PrintOrientation.LANDSCAPE
        )

    def test_auto_picks_portrait_for_tall_image(self):
        assert (
            resolve_orientation(1000, 2000, PrintOrientation.AUTO)
            == PrintOrientation.PORTRAIT
        )

    def test_auto_picks_portrait_for_square_image(self):
        assert (
            resolve_orientation(1000, 1000, PrintOrientation.AUTO)
            == PrintOrientation.PORTRAIT
        )

    @pytest.mark.parametrize(
        "requested", [PrintOrientation.PORTRAIT, PrintOrientation.LANDSCAPE]
    )
    def test_explicit_orientation_ignores_image_shape(self, requested):
        # egy fekvő (2000x1000) kép is portrét kap, ha azt kérték
        assert resolve_orientation(2000, 1000, requested) == requested

    def test_rejects_non_positive_image_size(self):
        with pytest.raises(ValueError):
            resolve_orientation(0, 100, PrintOrientation.AUTO)


class TestComputePrintLayoutFit:
    def test_wide_image_on_square_area_is_letterboxed_vertically(self):
        page = PageGeometry(width=100, height=100)
        placement = compute_print_layout(page, 2000, 1000, PrintFitMode.FIT)
        assert placement.width == pytest.approx(100)
        assert placement.height == pytest.approx(50)
        assert placement.x == pytest.approx(0)
        assert placement.y == pytest.approx(25)  # függőlegesen középre

    def test_tall_image_on_square_area_is_letterboxed_horizontally(self):
        page = PageGeometry(width=100, height=100)
        placement = compute_print_layout(page, 1000, 2000, PrintFitMode.FIT)
        assert placement.width == pytest.approx(50)
        assert placement.height == pytest.approx(100)
        assert placement.x == pytest.approx(25)
        assert placement.y == pytest.approx(0)

    def test_placement_stays_within_page_bounds(self):
        page = PageGeometry(width=210, height=297, margin=10)
        placement = compute_print_layout(page, 3000, 2000, PrintFitMode.FIT)
        assert placement.x >= 0
        assert placement.y >= 0
        assert placement.x + placement.width <= page.width + 1e-6
        assert placement.y + placement.height <= page.height + 1e-6

    def test_matching_aspect_fills_printable_area_exactly(self):
        page = PageGeometry(width=200, height=100, margin=0)
        placement = compute_print_layout(page, 400, 200, PrintFitMode.FIT)
        assert placement.width == pytest.approx(200)
        assert placement.height == pytest.approx(100)


class TestComputePrintLayoutFill:
    def test_wide_image_on_square_area_overflows_horizontally(self):
        page = PageGeometry(width=100, height=100)
        placement = compute_print_layout(page, 2000, 1000, PrintFitMode.FILL)
        # a terület teljesen kitöltve (magasság == oldal), a szélesség túllóg
        assert placement.height == pytest.approx(100)
        assert placement.width == pytest.approx(200)
        assert placement.x == pytest.approx(-50)
        assert placement.y == pytest.approx(0)

    def test_fill_always_covers_the_printable_area(self):
        page = PageGeometry(width=210, height=297, margin=10)
        placement = compute_print_layout(page, 640, 480, PrintFitMode.FILL)
        assert placement.width >= page.printable_width - 1e-6
        assert placement.height >= page.printable_height - 1e-6


class TestComputePrintLayoutValidation:
    @pytest.mark.parametrize("width,height", [(0, 100), (100, 0), (-5, 100)])
    def test_rejects_non_positive_image_size(self, width, height):
        page = PageGeometry(width=100, height=100)
        with pytest.raises(ValueError):
            compute_print_layout(page, width, height)
