"""#6443: a megmenthető régi korrekciók a láncban is működnek."""

from __future__ import annotations

import numpy as np

from picasapy.ini.filters import FilterOp, parse_filters
from picasapy.render.autocolor_matrix import (
    apply_autocolor_matrix,
    autocolor_matrix_16_16,
)
from picasapy.render.chain import apply_filters, can_offer_filter_control, can_render_filter
from picasapy.render.chain_policy import DEAD_LEGACY_OPS
from picasapy.render.chain_native_handlers import (
    apply_colorfix_op,
    apply_whitept_op,
)
from picasapy.render.legacy_effects import LEGACY_EFFECTS
from picasapy.render.native_colortemp import apply_native_colortemp


def _photo() -> np.ndarray:
    return np.array(
        [
            [[35, 90, 155], [80, 130, 205]],
            [[145, 175, 220], [215, 205, 185]],
        ],
        dtype=np.uint8,
    )


def test_whitept_neutralizes_the_selected_point_with_the_native_matrix():
    image = _photo()
    selected = (210, 120, 64)
    op = FilterOp("whitept", ("1", "ffD27840"))

    result = apply_whitept_op(image, op)

    expected = apply_autocolor_matrix(
        image, autocolor_matrix_16_16(*selected)
    )
    np.testing.assert_array_equal(result, expected)
    assert not np.array_equal(result, image)


def test_colorfix_applies_whitepoint_then_native_color_temperature():
    image = _photo()
    selected = (210, 120, 64)
    temperature = 0.125
    op = FilterOp("colorfix", ("1", "0.125", "ffD27840"))

    result = apply_colorfix_op(image, op)

    whitepoint = apply_autocolor_matrix(
        image, autocolor_matrix_16_16(*selected)
    )
    expected = apply_native_colortemp(whitepoint, temperature, 0.0)
    np.testing.assert_array_equal(result, expected)
    assert not np.array_equal(result, image)


def test_revived_filters_run_from_the_filter_chain():
    image = _photo()
    ops = (
        FilterOp("whitept", ("1", "ffd27840")),
        FilterOp("colorfix", ("1", "0.125", "ffd27840")),
    )

    report = apply_filters(image, ops)

    assert report.skipped == ()
    assert not np.array_equal(report.image, image)


def test_colorfix_keeps_legacy_numeric_parameters_without_a_picked_color():
    image = _photo()
    report = apply_filters(image, parse_filters("colorfix=1,0.500000,0.125000;"))

    assert report.skipped == ()
    np.testing.assert_array_equal(
        report.image, apply_native_colortemp(image, 0.5, 0.0)
    )


def test_revivable_legacy_effects_are_renderable_and_offer_controls():
    assert can_render_filter("colorfix")
    assert can_render_filter("whitept")
    assert can_offer_filter_control("colorfix")
    assert can_offer_filter_control("whitept")
    assert can_offer_filter_control("blur")


def test_native_dead_focalpixelate_remains_recognized_for_old_chains():
    assert "focalpixelate" in DEAD_LEGACY_OPS
    assert "focalpixelate" in {effect.key for effect in LEGACY_EFFECTS}


# rontás-kontroll: picasapy.render.chain.UI_INERT_RANGE_OPS = {"blur"} → 1 failed
