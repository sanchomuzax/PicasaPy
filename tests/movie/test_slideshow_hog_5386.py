"""A Mozgófilm alap sorrendje és HOG-jellemzői (#5386)."""

from datetime import datetime, timedelta

import numpy as np
import pytest
from PIL import Image

from picasapy.movie import burst, slideshow


def _photos(tmp_path, count=6, offsets=None):
    start = datetime(2026, 10, 19, 12, 0, 0)
    if offsets is None:
        offsets = range(count)
    photos = []
    for index, offset in enumerate(offsets):
        path = tmp_path / f"kep-{index}.jpg"
        exif = Image.Exif()
        exif[36867] = (start + timedelta(seconds=offset)).strftime(
            "%Y:%m:%d %H:%M:%S"
        )
        Image.new("RGB", (16, 16), (index * 20, 0, 0)).save(path, exif=exif)
        photos.append(path)
    return photos


def _writer(monkeypatch):
    class Writer:
        def __init__(self):
            self.frames = []

        def isOpened(self):
            return True

        def write(self, frame):
            self.frames.append(frame.copy())

        def release(self):
            pass

    writer = Writer()
    monkeypatch.setattr(slideshow.cv2, "VideoWriter", lambda *_args: writer)
    return writer


def _settings(**changes):
    values = {
        "width": 16,
        "height": 16,
        "fps": 1,
        "seconds_per_photo": 1,
        "transition_seconds": 0,
    }
    values.update(changes)
    return slideshow.MovieSettings(**values)


def _descriptor():
    descriptor = getattr(burst, "hog_descriptor", None)
    assert callable(descriptor), "A G/11 HOG-leíró még nincs megvalósítva."
    return descriptor


def _wraparound_gradient():
    image = np.zeros((480, 640, 3), dtype=np.uint8)

    # A piros csatorna gradiensére dx=4 és dy=-1 adódik a vizsgált ablakban.
    x_values = np.full(640, 40, dtype=np.int16)
    for x in range(72, 138):
        if x % 2 == 0:
            x_values[x] = 40 + 4 * (x // 2 - 36)
        else:
            x_values[x] = 42 + 4 * ((x - 1) // 2 - 36)

    y_values = np.full(480, 120, dtype=np.int16)
    for y in range(168, 210):
        if y % 2 == 0:
            y_values[y] = 120 - (y // 2 - 84)
        else:
            y_values[y] = 120 - ((y - 1) // 2 - 84)

    image[:, :, 2] = np.clip(
        y_values[:, None] + x_values[None, :] - 100, 0, 255
    ).astype(np.uint8)
    # A kisebb zöld gradiensnek nem szabad felülírnia a piros csatornát.
    for x in range(72, 138):
        image[168:210, x, 1] = 80 + (x - 72)
    return image


def test_zero_threshold_keeps_the_six_photo_capture_order(tmp_path, monkeypatch):
    photos = _photos(tmp_path)
    frames = {
        path: np.full((16, 16, 3), index + 1, dtype=np.uint8)
        for index, path in enumerate(photos)
    }
    writer = _writer(monkeypatch)
    monkeypatch.setattr(
        slideshow,
        "prepare_photo_frame",
        lambda path, *_args, **_kwargs: frames[path],
    )

    def unexpected_selection(*_args, **_kwargs):
        pytest.fail("T=0 esetén a kiválasztólánc nem futhat le.")

    monkeypatch.setattr(slideshow, "select_chain", unexpected_selection)

    report = slideshow.export_movie(
        photos, tmp_path / "alap.mp4", _settings(burstmodethresh=0)
    )

    assert report.used == tuple(photos)
    assert [int(frame[0, 0, 0]) for frame in writer.frames] == list(range(1, 7))


def test_hog_descriptor_has_2016_values():
    descriptor = _descriptor()(np.zeros((480, 640, 3), dtype=np.uint8))

    assert descriptor.shape == (2016,)


def test_hog_wraps_the_nineteenth_bin_into_bin_zero():
    feature = _descriptor()(_wraparound_gradient())
    angle = np.arctan2(-1.0, 4.0) + 2 * np.pi
    scaled_bin = angle * (9 / np.pi)
    expected_ratio = (scaled_bin - 17) / (18 - scaled_bin)

    assert feature.shape == (2016,)
    assert feature[0] > 0
    assert feature[17] > 0
    assert feature[0] / feature[17] == pytest.approx(expected_ratio, rel=1e-5)
    assert feature[18] == pytest.approx(feature[0], rel=1e-6)


def test_nonzero_threshold_selection_receives_hog_features(tmp_path, monkeypatch):
    photos = _photos(tmp_path, count=3, offsets=(0, 1, 4600))
    frames = {
        path: np.full((16, 16, 3), (index + 1) * 10, dtype=np.uint8)
        for index, path in enumerate(photos)
    }
    writer = _writer(monkeypatch)
    feature_frames = []
    monkeypatch.setattr(
        slideshow,
        "prepare_photo_frame",
        lambda path, *_args, **_kwargs: frames[path],
    )

    def hog_feature(frame):
        feature_frames.append(frame)
        return np.asarray([float(frame[0, 0, 0])])

    assert hasattr(slideshow, "hog_descriptor"), "Az export nem használ HOG-leírót."
    monkeypatch.setattr(slideshow, "hog_descriptor", hog_feature)

    report = slideshow.export_movie(
        photos,
        tmp_path / "sorozat.mp4",
        _settings(burstmodethresh=3600),
    )

    assert report.used == (photos[0], photos[2], photos[1])
    assert {int(frame[0, 0, 0]) for frame in feature_frames} == {10, 20, 30}
    assert [int(frame[0, 0, 0]) for frame in writer.frames] == [10, 30, 20]


def test_zero_threshold_orders_by_capture_time_like_the_owner_export(tmp_path, monkeypatch):
    """A tulajdonos 2026-10-19-i exportja: a hat kép ábécérendben adva, a film a
    `DateTimeOriginal` szerinti sorrendet követi (16:29:43, :59, 16:30:05, :26, :31, :48)."""
    # ábécérendben: Andy, JonasBen, Peet56, ShelbyLore, TimothyLGreen, Werbyu
    offsets = [0, 22, 65, 48, 16, 43]
    photos = _photos(tmp_path, offsets=offsets)
    frames = {
        path: np.full((16, 16, 3), index + 1, dtype=np.uint8)
        for index, path in enumerate(photos)
    }
    writer = _writer(monkeypatch)
    monkeypatch.setattr(
        slideshow,
        "prepare_photo_frame",
        lambda path, *_args, **_kwargs: frames[path],
    )

    slideshow.export_movie(photos, tmp_path / "alap.mp4", _settings(burstmodethresh=0))

    # Andy, Timothy, JonasBen, Werbyu, ShelbyLore, Peet56
    assert [int(frame[0, 0, 0]) for frame in writer.frames] == [1, 5, 2, 6, 4, 3]
