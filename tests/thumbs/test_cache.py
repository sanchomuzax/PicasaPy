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

    def test_no_temp_leftovers_on_success(self, cache, photo, tmp_path):
        cache.get_or_create(photo, *_stat_key(photo))
        leftovers = [
            p for p in (tmp_path / "cache").rglob("*") if p.suffix != ".jpg" and p.is_file()
        ]
        assert leftovers == []

    def test_no_temp_leftovers_on_encode_failure(self, cache, photo, tmp_path, monkeypatch):
        import cv2

        monkeypatch.setattr(cv2, "imencode", lambda *a, **k: (False, None))
        assert cache.get_or_create(photo, *_stat_key(photo)) is None
        cache_dir = tmp_path / "cache"
        leftovers = list(cache_dir.rglob("*.tmp")) if cache_dir.exists() else []
        assert leftovers == []

    def test_cache_dir_created_lazily(self, tmp_path, photo):
        cache = ThumbnailCache(tmp_path / "mely" / "utvonal", size=64)
        assert cache.get_or_create(photo, *_stat_key(photo)) is not None

    def test_accented_path_decoded(self, cache, tmp_path):
        # #65: Windows-on a cv2.imread nem tud nem-ASCII útvonalat megnyitni
        # (ANSI fájl-API) — a bájt-alapú dekódolás (fromfile+imdecode)
        # minden platformon unicode-biztos. A teszt útvonala a hibát adó
        # valós mappára rímel: "Képek".
        folder = tmp_path / "Képek árvíztűrő"
        folder.mkdir()
        photo = make_jpeg(folder / "kép_őúű.jpg", size=(320, 160))
        thumb = cache.get_or_create(photo, *_stat_key(photo))
        assert thumb is not None and thumb.exists()

    def test_missing_source_returns_none(self, cache, tmp_path):
        # Időközben törölt/elérhetetlen forrás (NAS): None, nem kivétel.
        assert cache.get_or_create(tmp_path / "nincs.jpg", 1, 7) is None

    def test_replace_race_lost_still_returns_target(
        self, cache, photo, monkeypatch
    ):
        # #66: Windows-on az os.replace PermissionError-t dob, ha a célt épp
        # olvassa egy másik szál. Ha a cél közben (a párhuzamos író révén)
        # létrejött, a vesztes fél is a kész thumbnailt adja vissza.
        import os as os_module
        from pathlib import Path

        def losing_replace(temp_name, target):
            Path(target).parent.mkdir(parents=True, exist_ok=True)
            Path(target).write_bytes(b"\xff\xd8gyoztes")  # a másik író műve
            raise PermissionError("sharing violation")

        monkeypatch.setattr(os_module, "replace", losing_replace)
        thumb = cache.get_or_create(photo, *_stat_key(photo))
        assert thumb is not None and thumb.exists()

    def test_video_thumbnail_from_first_frame(self, cache, tmp_path):
        # Videóból (mp4) az első képkockából készül thumbnail.
        from support.video_factory import make_mp4

        video = make_mp4(tmp_path / "VID_20250516.mp4", size=(320, 160))
        thumb = cache.get_or_create(video, *_stat_key(video))
        assert thumb is not None and thumb.exists()
        import cv2

        height, width = cv2.imread(str(thumb)).shape[:2]
        assert (width, height) == (64, 32)  # képarány megőrizve

    def test_video_not_read_fully_into_memory(self, cache, tmp_path, monkeypatch):
        # NAS-teljesítmény: a videót TILOS np.fromfile-lal teljesen
        # beolvasni (egy mp4 több száz MB is lehet hálózaton át) — a
        # VideoCapture streamelve csak a szükséges képkockát olvassa.
        from support.video_factory import make_mp4

        import picasapy.thumbs.cache as cache_module

        def forbidden_fromfile(*args, **kwargs):
            raise AssertionError("np.fromfile tiltott videó-forrásra")

        monkeypatch.setattr(cache_module.np, "fromfile", forbidden_fromfile)
        video = make_mp4(tmp_path / "VID_20250503.mp4", size=(320, 160))
        assert cache.get_or_create(video, *_stat_key(video)) is not None

    def test_corrupt_video_returns_none(self, cache, tmp_path):
        bad = tmp_path / "rossz.mp4"
        bad.write_bytes(b"nem video")
        assert cache.get_or_create(bad, 1, 9) is None

    def test_missing_video_returns_none(self, cache, tmp_path):
        assert cache.get_or_create(tmp_path / "nincs.mp4", 1, 9) is None

    def test_write_failure_returns_none(self, cache, photo, monkeypatch):
        # Ha az írás végleg meghiúsul (tele lemez, NAS-hiba), None jár —
        # a hívó placeholder-re eshet vissza, kivétel nem szökhet ki.
        monkeypatch.setattr(
            ThumbnailCache,
            "_write_atomic",
            lambda self, target, payload: (_ for _ in ()).throw(OSError("nincs hely")),
        )
        assert cache.get_or_create(photo, *_stat_key(photo)) is None
