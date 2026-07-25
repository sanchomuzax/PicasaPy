"""Mozgófilm-export (#29): letterbox, kockaszám, hibatűrés, kodek-hiány."""

import cv2
import numpy as np
import pytest

from picasapy.movie import MovieSettings, export_movie, letterbox


def _write_photo(path, size=(200, 120), color=(20, 60, 220)):
    image = np.full((size[1], size[0], 3), np.array(color, dtype=np.uint8), np.uint8)
    ok, encoded = cv2.imencode(".jpg", image, [int(cv2.IMWRITE_JPEG_QUALITY), 95])
    assert ok
    path.write_bytes(encoded.tobytes())
    return path


def _skip_without_codec(target):
    """MP4-kodek nélküli rendszeren (pl. csupasz konténer) a teszt kimarad —
    a kodek megléte környezeti kérdés, nem a kódé."""
    writer = cv2.VideoWriter(
        str(target), cv2.VideoWriter_fourcc(*"mp4v"), 24.0, (64, 64)
    )
    opened = writer.isOpened()
    writer.release()
    if not opened:
        pytest.skip("Nincs elérhető MP4-kodek ezen a rendszeren.")


class TestLetterbox:
    def test_result_has_canvas_size(self):
        image = np.zeros((100, 400, 3), np.uint8)
        assert letterbox(image, 320, 240).shape == (240, 320, 3)

    def test_aspect_ratio_is_kept(self):
        image = np.full((100, 400, 3), 255, np.uint8)
        result = letterbox(image, 400, 400, background=(0, 0, 0))
        # a fehér sáv magassága a 4:1 arányból jön (400 széles → 100 magas)
        white_rows = np.where(result.any(axis=(1, 2)))[0]
        assert len(white_rows) == 100

    def test_background_fills_the_rest(self):
        image = np.full((10, 10, 3), 255, np.uint8)
        result = letterbox(image, 100, 50, background=(0, 255, 0))
        assert np.all(result[0, 0] == (0, 255, 0))

    def test_invalid_canvas(self):
        with pytest.raises(ValueError):
            letterbox(np.zeros((10, 10, 3), np.uint8), 0, 10)


class TestMovieSettings:
    def test_frame_counts(self):
        settings = MovieSettings(fps=10, seconds_per_photo=2.0, transition_seconds=0.5)
        assert settings.frames_per_photo == 20
        assert settings.transition_frames == 5

    @pytest.mark.parametrize(
        "kwargs",
        [
            {"width": 8, "height": 8},
            {"width": 641, "height": 480},
            {"fps": 0},
            {"seconds_per_photo": 0},
            {"transition_seconds": -1},
            {"seconds_per_photo": 1.0, "transition_seconds": 1.0},
        ],
    )
    def test_invalid_settings(self, kwargs):
        with pytest.raises(ValueError):
            MovieSettings(**kwargs)


class TestExportMovie:
    def test_writes_playable_file(self, tmp_path):
        _skip_without_codec(tmp_path / "proba.mp4")
        photos = [_write_photo(tmp_path / f"{i}.jpg") for i in range(3)]
        target = tmp_path / "film.mp4"
        report = export_movie(
            photos,
            target,
            MovieSettings(
                width=320, height=240, fps=10, seconds_per_photo=0.5,
                transition_seconds=0.2,
            ),
        )
        assert target.exists() and target.stat().st_size > 0
        assert len(report.used) == 3
        assert report.frames > 0

        capture = cv2.VideoCapture(str(target))
        try:
            assert capture.isOpened()
            assert int(capture.get(cv2.CAP_PROP_FRAME_WIDTH)) == 320
        finally:
            capture.release()

    def test_frame_count_matches_settings(self, tmp_path):
        _skip_without_codec(tmp_path / "proba.mp4")
        photos = [_write_photo(tmp_path / f"{i}.jpg") for i in range(2)]
        settings = MovieSettings(
            width=160, height=120, fps=10, seconds_per_photo=1.0,
            transition_seconds=0.3,
        )
        report = export_movie(photos, tmp_path / "film.mp4", settings)
        hold = settings.frames_per_photo - settings.transition_frames
        expected = 2 * hold + settings.transition_frames
        assert report.frames == expected

    def test_progress_is_reported_per_photo(self, tmp_path):
        _skip_without_codec(tmp_path / "proba.mp4")
        photos = [_write_photo(tmp_path / f"{i}.jpg") for i in range(3)]
        seen = []
        export_movie(
            photos,
            tmp_path / "film.mp4",
            MovieSettings(width=160, height=120, fps=5, seconds_per_photo=0.4,
                          transition_seconds=0.0),
            progress=lambda done, total: seen.append((done, total)),
        )
        assert seen == [(1, 3), (2, 3), (3, 3)]

    def test_broken_source_is_skipped(self, tmp_path):
        _skip_without_codec(tmp_path / "proba.mp4")
        good = _write_photo(tmp_path / "jo.jpg")
        bad = tmp_path / "romlott.jpg"
        bad.write_bytes(b"nem kep")
        report = export_movie(
            [good, bad],
            tmp_path / "film.mp4",
            MovieSettings(width=160, height=120, fps=5, seconds_per_photo=0.4,
                          transition_seconds=0.0),
        )
        assert report.used == (good,)
        assert report.skipped == (bad,)

    def test_all_broken_writes_nothing(self, tmp_path):
        bad = tmp_path / "romlott.jpg"
        bad.write_bytes(b"nem kep")
        target = tmp_path / "film.mp4"
        report = export_movie([bad], target, MovieSettings(width=160, height=120))
        assert report.used == ()
        assert report.frames == 0
        assert not target.exists()

    def test_empty_input_is_error(self, tmp_path):
        with pytest.raises(ValueError):
            export_movie([], tmp_path / "film.mp4")

    def test_target_directory_is_created(self, tmp_path):
        _skip_without_codec(tmp_path / "proba.mp4")
        photos = [_write_photo(tmp_path / "a.jpg")]
        target = tmp_path / "uj" / "mappa" / "film.mp4"
        export_movie(
            photos,
            target,
            MovieSettings(width=160, height=120, fps=5, seconds_per_photo=0.4,
                          transition_seconds=0.0),
        )
        assert target.exists()
