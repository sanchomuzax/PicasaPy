"""A `picasapy.render.chain` lánc-alkalmazó tesztjei."""

from __future__ import annotations

import math

import numpy as np
import pytest

from picasapy.ini.filters import FilterOp
from picasapy.render.chain import apply_filters, tilt_cover_scale
from picasapy.render.ops import apply_autocolor, apply_autolight, apply_crop


def _gradient_image(width: int = 20, height: int = 10) -> np.ndarray:
    row = np.linspace(80, 180, width, dtype=np.uint8)
    image = np.tile(row, (height, 1))
    return np.stack([image, image, image], axis=-1).astype(np.uint8)


class TestTiltCoverScale:
    def test_nulla_szognel_egy(self) -> None:
        assert tilt_cover_scale(100, 50, 0.0) == pytest.approx(1.0)

    def test_pozitiv_szognel_nagyobb_mint_egy(self) -> None:
        assert tilt_cover_scale(100, 50, math.radians(10)) > 1.0

    def test_negativ_szog_ugyanaz_mint_pozitiv(self) -> None:
        pos = tilt_cover_scale(100, 60, math.radians(15))
        neg = tilt_cover_scale(100, 60, math.radians(-15))
        assert pos == pytest.approx(neg)


class TestApplyFilters:
    def test_tamogatott_crop64_alkalmazasa(self) -> None:
        image = _gradient_image()
        ops = (FilterOp("crop64", ("1", "20001000c000e000")),)
        result, skipped = apply_filters(image, ops)
        expected = apply_crop(
            image,
            __import__(
                "picasapy.ini.rect64", fromlist=["decode_rect64"]
            ).decode_rect64("20001000c000e000"),
        )
        assert result.shape == expected.shape
        assert skipped == ()

    def test_nem_tamogatott_szurot_nemán_kihagyja(self) -> None:
        image = _gradient_image()
        ops = (FilterOp("Vignette", ("1", "0.5")),)
        result, skipped = apply_filters(image, ops)
        np.testing.assert_array_equal(result, image)
        assert skipped == ("Vignette",)

    def test_vegyes_lanc_sorrend_es_kihagyottak(self) -> None:
        image = _gradient_image()
        ops = (
            FilterOp("autolight", ("1",)),
            FilterOp("finetune2", ("1", "0.3", "0.1", "0.2", "00000000", "0.0")),
            FilterOp("autocolor", ("1",)),
        )
        result, skipped = apply_filters(image, ops)
        expected = apply_autocolor(apply_autolight(image))
        np.testing.assert_array_equal(result, expected)
        assert skipped == ("finetune2",)

    def test_enhance_alkalmazasa(self) -> None:
        image = _gradient_image()
        ops = (FilterOp("enhance", ("1",)),)
        result, skipped = apply_filters(image, ops)
        assert result.shape == image.shape
        assert skipped == ()

    def test_ures_lanc_valtozatlan_kepet_ad(self) -> None:
        image = _gradient_image()
        result, skipped = apply_filters(image, ())
        np.testing.assert_array_equal(result, image)
        assert skipped == ()

    def test_tilt_azonossag_nulla_szognel(self) -> None:
        image = _gradient_image()
        ops = (FilterOp("tilt", ("1", "0.0")),)
        result, skipped = apply_filters(image, ops)
        assert result.shape == image.shape
        assert skipped == ()

    def test_nem_mutalja_a_bemenetet(self) -> None:
        image = _gradient_image()
        original = image.copy()
        ops = (FilterOp("autolight", ("1",)),)
        apply_filters(image, ops)
        np.testing.assert_array_equal(image, original)
