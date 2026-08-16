"""A normalizált téglalapok képpontra váltása — a „Rács vastagsága" csúszka
pontos hatása (#431).

Forrás: `docs/specs/picasa-create-features.md` 1.9.3.
"""

from __future__ import annotations

import pytest

from picasapy.collage.rects import NormRect, PixelRect, to_pixel_rects


def test_terkoz_nelkul_a_teljes_lapot_kitolti():
    rects = (NormRect(0.0, 0.0, 1.0, 1.0),)
    assert to_pixel_rects(rects, 200, 100, spacing=0.0) == (
        PixelRect(0, 0, 200, 100),
    )


def test_a_hezag_keppontban_negyzetes():
    """A függőleges hézagot a lap oldalaránya (W/H) szorozza, ezért a rés
    KÉPPONTBAN ugyanakkora vízszintesen és függőlegesen — pedig a
    normalizált térben nem az."""
    rects = (NormRect(0.0, 0.0, 1.0, 1.0),)
    (box,) = to_pixel_rects(rects, 200, 100, spacing=0.2)
    assert (box.x0, box.y0, box.x1, box.y1) == (18, 18, 182, 82)
    assert box.x0 == box.y0  # a bal és a felső margó azonos képpontban
    assert 200 - box.x1 == 100 - box.y1


def test_a_lap_szelet_erinto_el_a_TELJES_hezagot_kapja():
    """A belső élek felet-felet kapnak, a külsők egészet — így a képek
    közti rés ugyanakkora, mint a lap körüli margó."""
    rects = (
        NormRect(0.0, 0.0, 0.5, 1.0),
        NormRect(0.5, 0.0, 1.0, 1.0),
    )
    left, right = to_pixel_rects(rects, 200, 200, spacing=0.4)
    outer_margin = left.x0
    inner_gap = right.x0 - left.x1
    assert outer_margin == 18
    assert inner_gap == outer_margin


def test_a_hezagot_a_LEGKISEBB_cella_oldala_meretezi():
    """`hézag = spacing * 0.45 * min(minden téglalap szélessége és
    magassága)` — egy apró cella az EGÉSZ kollázs réseit lecsökkenti."""
    wide = (NormRect(0.0, 0.0, 1.0, 1.0),)
    narrow = (
        NormRect(0.0, 0.0, 0.25, 1.0),
        NormRect(0.25, 0.0, 1.0, 1.0),
    )
    (big,) = to_pixel_rects(wide, 400, 400, spacing=0.5)
    small = to_pixel_rects(narrow, 400, 400, spacing=0.5)
    assert small[0].x0 < big.x0


def test_pixelrect_meretei():
    box = PixelRect(10, 20, 40, 60)
    assert (box.width, box.height) == (30, 40)


def test_ervenytelen_normrect():
    with pytest.raises(ValueError):
        NormRect(0.5, 0.0, 0.5, 1.0)  # nulla szélesség
    with pytest.raises(ValueError):
        NormRect(-0.1, 0.0, 1.0, 1.0)  # kilóg az egységnégyzetből


def test_ervenytelen_terkoz():
    with pytest.raises(ValueError):
        to_pixel_rects((NormRect(0.0, 0.0, 1.0, 1.0),), 100, 100, spacing=1.5)
