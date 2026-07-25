"""Kollázs-elrendezések (#29) — tiszta geometria, kép nélkül."""

import pytest

from picasapy.collage import (
    COLLAGE_KINDS,
    CONTACT_SHEET,
    GRID,
    MOSAIC,
    PILE,
    Placement,
    contact_sheet_layout,
    grid_layout,
    grid_shape,
    layout_for,
    mosaic_layout,
    pile_layout,
)


class TestGridShape:
    @pytest.mark.parametrize(
        ("count", "expected"),
        [(1, (1, 1)), (2, (2, 1)), (4, (2, 2)), (5, (3, 2)), (9, (3, 3)), (10, (4, 3))],
    )
    def test_shape_is_as_square_as_possible(self, count, expected):
        assert grid_shape(count) == expected

    def test_zero_is_error(self):
        with pytest.raises(ValueError):
            grid_shape(0)


class TestGridLayout:
    def test_one_placement_per_image(self):
        places = grid_layout(7, 800, 600)
        assert len(places) == 7

    def test_cells_stay_inside_canvas(self):
        for place in grid_layout(9, 800, 600, spacing=10):
            assert place.x >= 0 and place.y >= 0
            assert place.x + place.width <= 800
            assert place.y + place.height <= 600

    def test_cells_do_not_overlap(self):
        places = grid_layout(6, 900, 600, spacing=6)
        for first in range(len(places)):
            for second in range(first + 1, len(places)):
                a, b = places[first], places[second]
                separated = (
                    a.x + a.width <= b.x
                    or b.x + b.width <= a.x
                    or a.y + a.height <= b.y
                    or b.y + b.height <= a.y
                )
                assert separated, f"átfedés: {a} és {b}"

    def test_cells_fill_the_frame(self):
        assert all(place.fill for place in grid_layout(4, 400, 400))

    def test_tiny_canvas_is_error(self):
        with pytest.raises(ValueError):
            grid_layout(9, 20, 20, spacing=8)


class TestContactSheet:
    def test_fixed_column_count(self):
        places = contact_sheet_layout(8, 800, 600, columns=4)
        # az első négy kép egy sorban áll
        assert len({p.y for p in places[:4]}) == 1
        assert len({p.y for p in places}) == 2

    def test_whole_image_is_visible(self):
        assert all(not place.fill for place in contact_sheet_layout(4, 400, 400))

    def test_columns_capped_at_image_count(self):
        places = contact_sheet_layout(2, 800, 600, columns=6)
        assert len({p.y for p in places}) == 1

    def test_invalid_columns(self):
        with pytest.raises(ValueError):
            contact_sheet_layout(4, 400, 400, columns=0)


class TestMosaic:
    def test_single_image_fills_canvas(self):
        (place,) = mosaic_layout(1, 800, 600, spacing=10)
        assert place.width == 780 and place.height == 580

    def test_hero_is_the_largest(self):
        places = mosaic_layout(6, 1200, 900)
        hero = places[0]
        assert all(hero.width * hero.height > p.width * p.height for p in places[1:])

    def test_all_inside_canvas(self):
        for place in mosaic_layout(7, 1200, 900):
            assert place.x >= 0 and place.y >= 0
            assert place.x + place.width <= 1200
            assert place.y + place.height <= 900


class TestPile:
    def test_same_seed_same_layout(self):
        assert pile_layout(5, 800, 600, seed=7) == pile_layout(5, 800, 600, seed=7)

    def test_different_seed_differs(self):
        assert pile_layout(5, 800, 600, seed=1) != pile_layout(5, 800, 600, seed=2)

    def test_cards_are_rotated(self):
        assert any(place.angle for place in pile_layout(6, 800, 600, seed=3))

    def test_cards_are_square_and_sized_to_canvas(self):
        places = pile_layout(4, 800, 600, seed=0)
        assert all(p.width == p.height for p in places)
        assert all(p.width < 600 for p in places)


class TestLayoutFor:
    @pytest.mark.parametrize("kind", COLLAGE_KINDS)
    def test_every_kind_produces_placements(self, kind):
        places = layout_for(kind, 5, 1000, 800)
        assert len(places) == 5
        assert all(isinstance(p, Placement) for p in places)

    def test_unknown_kind_is_error(self):
        with pytest.raises(ValueError, match="Ismeretlen kollázs-típus"):
            layout_for("mandala", 3, 800, 600)

    def test_kinds_differ_from_each_other(self):
        rendered = {
            kind: layout_for(kind, 5, 1000, 800)
            for kind in (GRID, CONTACT_SHEET, MOSAIC, PILE)
        }
        assert len({tuple(v) for v in rendered.values()}) == 4


class TestPlacementValidation:
    def test_zero_size_is_error(self):
        with pytest.raises(ValueError):
            Placement(x=0, y=0, width=0, height=10)
