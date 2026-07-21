"""histogram_helper.compute_rgb_histogram — RGB-hisztogram determinisztikus
szintetikus képekre (#25)."""

import numpy as np
import pytest

from picasapy.app.histogram_helper import (
    BUCKET_COUNT,
    EMPTY_HISTOGRAM,
    compute_rgb_histogram,
)


class TestComputeRgbHistogram:
    def test_solid_color_gives_single_peak_bucket_per_channel(self):
        array = np.zeros((4, 4, 3), dtype=np.uint8)
        array[:, :, 0] = 200
        array[:, :, 1] = 10
        array[:, :, 2] = 0
        hist = compute_rgb_histogram(array)
        assert hist["r"][200] == 1.0
        assert hist["g"][10] == 1.0
        assert hist["b"][0] == 1.0
        # minden más vödör (a csatornán belül) nulla
        assert sum(hist["r"]) == 1.0
        assert sum(hist["g"]) == 1.0
        assert sum(hist["b"]) == 1.0

    def test_normalization_is_relative_to_the_tallest_bucket(self):
        array = np.zeros((4, 1, 3), dtype=np.uint8)
        array[0:3, 0, 0] = 10  # 3 pixel a 10-es vödörben
        array[3:4, 0, 0] = 50  # 1 pixel az 50-es vödörben
        hist = compute_rgb_histogram(array)
        assert hist["r"][10] == 1.0
        assert hist["r"][50] == pytest.approx(1 / 3)

    def test_bucket_count_length_matches_requested_buckets(self):
        array = np.zeros((2, 2, 3), dtype=np.uint8)
        hist = compute_rgb_histogram(array, buckets=64)
        assert len(hist["r"]) == 64
        assert len(hist["g"]) == 64
        assert len(hist["b"]) == 64

    def test_folded_buckets_sum_the_underlying_intensities(self):
        array = np.zeros((2, 1, 3), dtype=np.uint8)
        array[0, 0, 0] = 0
        array[1, 0, 0] = 3  # ugyanabba a 4-es fold-vödörbe esik (256/64=4)
        hist = compute_rgb_histogram(array, buckets=64)
        assert hist["r"][0] == 1.0  # a két pixel együtt a csúcs

    def test_none_array_gives_empty_histogram(self):
        assert compute_rgb_histogram(None) == EMPTY_HISTOGRAM

    def test_empty_array_gives_empty_histogram(self):
        array = np.zeros((0, 0, 3), dtype=np.uint8)
        assert compute_rgb_histogram(array) == EMPTY_HISTOGRAM

    def test_invalid_shape_raises_value_error(self):
        array = np.zeros((4, 4), dtype=np.uint8)
        with pytest.raises(ValueError):
            compute_rgb_histogram(array)

    def test_invalid_bucket_count_raises_value_error(self):
        array = np.zeros((2, 2, 3), dtype=np.uint8)
        with pytest.raises(ValueError):
            compute_rgb_histogram(array, buckets=100)  # nem osztója 256-nak

    def test_default_bucket_count_is_256(self):
        array = np.zeros((2, 2, 3), dtype=np.uint8)
        hist = compute_rgb_histogram(array)
        assert len(hist["r"]) == BUCKET_COUNT

    def test_large_image_is_subsampled_but_stays_correct(self):
        # a ritkítási küszöb fölötti, egyszínű kép — a stride-mintavétel
        # után is egyetlen csúcs-vödröt kell adnia (#25 — teljesítmény)
        array = np.zeros((900, 900, 3), dtype=np.uint8)
        array[:, :, :] = 128
        hist = compute_rgb_histogram(array)
        assert hist["r"][128] == 1.0
        assert hist["g"][128] == 1.0
        assert hist["b"][128] == 1.0
