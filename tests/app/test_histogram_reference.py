"""A hisztogram-referencia készlet ellenőrzése (#236).

A `tests/support/histogram_reference` determinisztikus képeire lefuttatja a
`compute_rgb_histogram`-ot, és igazolja, hogy a kapott hisztogram a
generátorban DOKUMENTÁLT alakot adja (csúcs-pozíciók, illetve laposság). Ez
a Picasa-összevetés (golden) automatizált, gép-oldali sarokköve: ha a
normalizálási logika (#232) megváltozik, ezek a tesztek azonnal jeleznek.
"""

from __future__ import annotations

import numpy as np
import pytest

from picasapy.app.histogram_helper import BUCKET_COUNT, compute_rgb_histogram
from tests.support.histogram_reference import (
    REFERENCES,
    reference_by_name,
    reference_images,
    write_reference_pngs,
)

_CHANNELS = ("r", "g", "b")


class TestReferenceSet:
    def test_has_expected_reference_count(self):
        # a feladat ~9-10 képet kér; jelenleg pontosan 9
        assert len(REFERENCES) == 9

    def test_names_are_unique(self):
        names = [ref.name for ref in REFERENCES]
        assert len(names) == len(set(names))

    def test_all_arrays_are_uint8_rgb(self):
        for ref in REFERENCES:
            assert ref.array.dtype == np.uint8, ref.name
            assert ref.array.ndim == 3 and ref.array.shape[2] == 3, ref.name

    def test_reference_by_name_round_trips(self):
        for ref in REFERENCES:
            assert reference_by_name(ref.name) is ref

    def test_reference_by_name_unknown_raises(self):
        with pytest.raises(KeyError):
            reference_by_name("nincs_ilyen")

    def test_reference_images_is_deterministic(self):
        # kétszeri generálás bitre azonos képeket ad
        first = reference_images()
        second = reference_images()
        for a, b in zip(first, second):
            assert a.name == b.name
            assert np.array_equal(a.array, b.array), a.name


class TestExpectedPeaks:
    """A dokumentált csúcs-binek tényleg 1.0 értéket kapnak, a többi 0."""

    @pytest.mark.parametrize(
        "name",
        [r.name for r in REFERENCES if r.expected_peaks],
    )
    def test_peaks_match_documented_bins(self, name):
        ref = reference_by_name(name)
        hist = compute_rgb_histogram(ref.array)
        for channel in _CHANNELS:
            peaks = ref.expected_peaks[channel]
            values = hist[channel]
            assert len(values) == BUCKET_COUNT
            for bin_index in peaks:
                assert values[bin_index] == pytest.approx(1.0), (
                    f"{name}/{channel}: a(z) {bin_index}. bin nem csúcs"
                )
            # a csúcsokon kívül minden bin nulla
            nonzero = {i for i, v in enumerate(values) if v > 0}
            assert nonzero == set(peaks), (
                f"{name}/{channel}: váratlan nem-nulla binek: "
                f"{sorted(nonzero - set(peaks))}"
            )


class TestPureColours:
    """Kiemelt, kézzel is ellenőrzött esetek a feladatleírásból."""

    def test_pure_red_only_r_channel_top_bin(self):
        hist = compute_rgb_histogram(reference_by_name("pure_red").array)
        assert hist["r"][255] == 1.0
        assert sum(hist["r"]) == 1.0  # egyetlen nem-nulla bin
        assert hist["g"][0] == 1.0 and sum(hist["g"]) == 1.0
        assert hist["b"][0] == 1.0 and sum(hist["b"]) == 1.0

    def test_mid_gray_peak_in_middle_bin_all_channels(self):
        hist = compute_rgb_histogram(reference_by_name("mid_gray").array)
        for channel in _CHANNELS:
            assert hist[channel][128] == 1.0
            assert sum(hist[channel]) == 1.0

    def test_white_top_bin_all_channels(self):
        hist = compute_rgb_histogram(reference_by_name("white").array)
        for channel in _CHANNELS:
            assert hist[channel][255] == 1.0

    def test_two_tone_has_two_equal_peaks(self):
        hist = compute_rgb_histogram(
            reference_by_name("two_tone_64_192").array
        )
        for channel in _CHANNELS:
            assert hist[channel][64] == 1.0
            assert hist[channel][192] == 1.0
            # csak ez a két bin nem-nulla
            assert sum(1 for v in hist[channel] if v > 0) == 2


class TestFlatChannels:
    """A rámpa lapos, egyenletes eloszlású — nincs kiugró egyetlen csúcs."""

    def test_gray_ramp_is_uniform(self):
        hist = compute_rgb_histogram(reference_by_name("gray_ramp").array)
        for channel in _CHANNELS:
            values = np.asarray(hist[channel])
            # minden bin ~1.0 (minden intenzitás azonos gyakoriságú)
            assert np.all(values > 0.99), channel
            assert values.min() == pytest.approx(values.max())

    def test_ramp_channels_are_flagged_flat(self):
        ref = reference_by_name("gray_ramp")
        assert ref.flat_channels == ("r", "g", "b")

    def test_rgb_gradient_spans_full_range(self):
        # minden csatorna a teljes tartományt lefedi: a 0-s és a felső bin
        # környéke is kap értéket, tehát nem egyetlen csúcsba tömörül
        hist = compute_rgb_histogram(reference_by_name("rgb_gradient").array)
        for channel in _CHANNELS:
            values = np.asarray(hist[channel])
            populated = np.count_nonzero(values)
            assert populated > 50, f"{channel}: túl kevés bin ({populated})"


class TestPngExport:
    def test_write_reference_pngs_creates_all_files(self, tmp_path):
        cv2 = pytest.importorskip("cv2")
        paths = write_reference_pngs(tmp_path)
        assert len(paths) == len(REFERENCES)
        for ref, path in zip(REFERENCES, paths):
            assert path.exists() and path.name == f"{ref.name}.png"
            # visszaolvasva a méret és a csatornaszám egyezik
            back = cv2.imread(str(path))
            assert back is not None
            assert back.shape == ref.array.shape
