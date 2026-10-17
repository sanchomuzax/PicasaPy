"""A film időcsoportjai és ordering=0 láncválasztója (#4194)."""

import numpy as np
import pytest
from datetime import datetime, timedelta
from PIL import Image

from picasapy.movie.burst import capture_groups, d_hog, select_chain


_FEATURES = np.asarray(
    [
        [0.10, 0.20, 0.30, 0.40, 0.50, 0.60, 0.70, 0.80],
        [0.12, 0.22, 0.28, 0.41, 0.52, 0.58, 0.72, 0.79],
        [0.90, 0.10, 0.05, 0.80, 0.10, 0.70, 0.20, 0.60],
        [0.15, 0.25, 0.35, 0.45, 0.55, 0.65, 0.75, 0.85],
        [0.50, 0.50, 0.50, 0.50, 0.10, 0.10, 0.10, 0.10],
        [0.48, 0.52, 0.49, 0.51, 0.12, 0.09, 0.11, 0.10],
    ],
    dtype=np.float64,
)


def test_capture_groups_follow_rounded_adjacent_threshold_etalon():
    assert capture_groups([0, 3240, 6480], 3600) == [0, 0, 0]
    assert capture_groups([0, 3600, 7200], 3600) == [0, 1, 2]
    assert capture_groups([0, 3240, 7200], 3600) == [0, 0, 1]
    assert capture_groups([0, 3240, 6480], 0) == [0, 1, 2]


def test_new_movie_defaults_to_best_transitions():
    from picasapy.movie import MovieSettings

    assert MovieSettings().ordering == 0


def test_d_hog_matches_the_three_native_fixtures():
    pairs = (
        (
            [1, 2, 3, 4, 5, 6, 7, 8],
            [2, 2, 1, 4, 6, 6, 9, 8],
            1.6742424964904785,
        ),
        (
            [0.5, 1.5, 2.5, 3.5, 4.5],
            [1, 0, 2, 4, 3],
            2.055555582046509,
        ),
        ([0] * 6, [1e-8] * 6, 2.999999892949745e-8),
    )
    for first, second, expected in pairs:
        assert d_hog(first, second) == pytest.approx(expected, rel=1e-6)


@pytest.mark.parametrize(
    ("groups", "count", "anchor", "expected"),
    [
        ([0, 0, 0, 1, 1, 2], 4, 0, [0, 3, 1, 5]),
        ([0, 0, 0, 1, 1, 2], 4, 3, [3, 1, 5, 4]),
        ([0, 0, 0, 0, 0, 0], 3, 0, [0]),
    ],
    ids=["V1", "V2", "V3"],
)
def test_chain_selection_matches_native_vectors(groups, count, anchor, expected):
    assert select_chain(
        groups,
        count,
        feature_for_index=lambda index: _FEATURES[index],
        anchor=anchor,
    ) == expected


def test_export_movie_uses_burst_threshold_for_best_transitions(
    tmp_path, monkeypatch
):
    from picasapy.movie import slideshow

    class Writer:
        def isOpened(self):
            return True

        def write(self, _frame):
            pass

        def release(self):
            pass

    photos = [tmp_path / f"{index}.jpg" for index in range(3)]
    start = datetime(2020, 1, 1)
    for photo, offset in zip(photos, (0, 1000, 4600), strict=True):
        exif = Image.Exif()
        exif[36867] = (start + timedelta(seconds=offset)).strftime(
            "%Y:%m:%d %H:%M:%S"
        )
        Image.new("RGB", (16, 16)).save(photo, exif=exif)
    monkeypatch.setattr(
        slideshow,
        "prepare_photo_frame",
        lambda *_args, **_kwargs: np.zeros((16, 16, 3), dtype=np.uint8),
    )
    monkeypatch.setattr(slideshow.cv2, "VideoWriter", lambda *_args: Writer())

    no_filter = slideshow.export_movie(
        photos,
        tmp_path / "no-filter.mp4",
        slideshow.MovieSettings(
            width=16,
            height=16,
            fps=1,
            seconds_per_photo=1,
            transition_seconds=0,
            ordering=0,
            burstmodethresh=0,
        ),
    )
    filtered = slideshow.export_movie(
        photos,
        tmp_path / "filtered.mp4",
        slideshow.MovieSettings(
            width=16,
            height=16,
            fps=1,
            seconds_per_photo=1,
            transition_seconds=0,
            ordering=0,
            burstmodethresh=3600,
        ),
    )

    assert no_filter.used == tuple(photos)
    assert filtered.used == (photos[0], photos[2], photos[1])
