"""Thumbnail-cache: OpenCV-alapú generálás, mtime-kulcsos gyorsítótár."""

import pytest

from picasapy.thumbs import ThumbnailCache

from support.jpeg_factory import make_jpeg


@pytest.fixture
def cache(tmp_path):
    return ThumbnailCache(tmp_path / "cache", size=64)


@pytest.fixture
def photo(tmp_path):
    return make_jpeg(tmp_path / "kep.jpg", size=(320, 160))


def _stat_key(path):
    info = path.stat()
    return info.st_mtime_ns, info.st_size


class TestGetOrCreate:
    def test_creates_thumbnail_with_max_dimension(self, cache, photo):
        thumb = cache.get_or_create(photo, *_stat_key(photo))
        assert thumb is not None and thumb.exists()
        import cv2

        image = cv2.imread(str(thumb))
        height, width = image.shape[:2]
        assert max(width, height) == 64
        assert (width, height) == (64, 32)  # képarány megőrizve

    def test_cache_hit_does_not_regenerate(self, cache, photo):
        first = cache.get_or_create(photo, *_stat_key(photo))
        first_mtime = first.stat().st_mtime_ns
        second = cache.get_or_create(photo, *_stat_key(photo))
        assert second == first
        assert second.stat().st_mtime_ns == first_mtime

    def test_changed_file_gets_new_cache_entry(self, cache, photo, tmp_path):
        old = cache.get_or_create(photo, *_stat_key(photo))
        make_jpeg(photo, size=(100, 100))
        new = cache.get_or_create(photo, *_stat_key(photo))
        assert new != old  # a kulcs mtime+méret alapú

    def test_exif_orientation_applied(self, cache, tmp_path):
        # 6-os orientáció: 90°-kal forgatva kell kicsinyíteni (32x64).
        rotated = make_jpeg(tmp_path / "forgatott.jpg", size=(320, 160), orientation=6)
        thumb = cache.get_or_create(rotated, *_stat_key(rotated))
        import cv2

        height, width = cv2.imread(str(thumb)).shape[:2]
        assert (width, height) == (32, 64)

    def test_corrupt_file_returns_none(self, cache, tmp_path):
        bad = tmp_path / "rossz.jpg"
        bad.write_bytes(b"nem kep")
        assert cache.get_or_create(bad, 1, 7) is None

    def test_upscale_avoided(self, cache, tmp_path):
        small = make_jpeg(tmp_path / "kicsi.jpg", size=(20, 10))
        thumb = cache.get_or_create(small, *_stat_key(small))
        import cv2

        height, width = cv2.imread(str(thumb)).shape[:2]
        assert (width, height) == (20, 10)  # nem nagyítunk fel

    def test_cache_dir_created_lazily(self, tmp_path, photo):
        cache = ThumbnailCache(tmp_path / "mely" / "utvonal", size=64)
        assert cache.get_or_create(photo, *_stat_key(photo)) is not None
