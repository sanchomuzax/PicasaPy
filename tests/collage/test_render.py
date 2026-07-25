"""Kollázs-renderelés (#29): illesztés, vászon, hibatűrés, kiírás."""

import cv2
import numpy as np
import pytest

from picasapy.collage import (
    CONTACT_SHEET,
    GRID,
    MOSAIC,
    PILE,
    CollageSettings,
    fit_to_frame,
    make_collage,
    write_collage,
)


def _write_photo(path, size=(200, 120), color=(20, 60, 220)):
    """Egyszínű teszt-JPEG (BGR színnel), bájt-alapon kiírva."""
    image = np.full((size[1], size[0], 3), np.array(color, dtype=np.uint8), np.uint8)
    ok, encoded = cv2.imencode(".jpg", image, [int(cv2.IMWRITE_JPEG_QUALITY), 95])
    assert ok
    path.write_bytes(encoded.tobytes())
    return path


class TestFitToFrame:
    def test_fill_covers_the_whole_frame(self):
        image = np.zeros((100, 400, 3), np.uint8)
        assert fit_to_frame(image, 200, 200, fill=True).shape[:2] == (200, 200)

    def test_contain_keeps_aspect_ratio(self):
        image = np.zeros((100, 400, 3), np.uint8)
        result = fit_to_frame(image, 200, 200, fill=False)
        assert result.shape[1] == 200
        assert result.shape[0] == 50

    def test_invalid_frame(self):
        with pytest.raises(ValueError):
            fit_to_frame(np.zeros((10, 10, 3), np.uint8), 0, 10, fill=True)


class TestMakeCollage:
    def test_canvas_has_requested_size(self, tmp_path):
        photos = [_write_photo(tmp_path / f"{i}.jpg") for i in range(4)]
        report = make_collage(photos, CollageSettings(width=640, height=480))
        assert report.image.shape == (480, 640, 3)
        assert len(report.used) == 4

    @pytest.mark.parametrize("kind", [GRID, CONTACT_SHEET, MOSAIC, PILE])
    def test_every_kind_paints_the_photos(self, tmp_path, kind):
        photos = [_write_photo(tmp_path / f"{i}.jpg") for i in range(5)]
        report = make_collage(
            photos,
            CollageSettings(kind=kind, width=800, height=600, background=(0, 0, 0)),
        )
        # a fekete vásznon a képek pixelei látszanak (nem maradt üres)
        painted = np.count_nonzero(report.image.any(axis=2))
        assert painted > 800 * 600 * 0.1

    def test_broken_source_is_skipped_not_fatal(self, tmp_path):
        good = _write_photo(tmp_path / "jo.jpg")
        bad = tmp_path / "romlott.jpg"
        bad.write_bytes(b"nem kep")
        report = make_collage([good, bad], CollageSettings(width=400, height=300))
        assert report.used == (good,)
        assert report.skipped == (bad,)
        assert len(report.reasons) == 1

    def test_missing_file_is_skipped(self, tmp_path):
        good = _write_photo(tmp_path / "jo.jpg")
        report = make_collage(
            [good, tmp_path / "nincs.jpg"], CollageSettings(width=400, height=300)
        )
        assert report.used == (good,)
        assert len(report.skipped) == 1

    def test_all_broken_gives_empty_canvas(self, tmp_path):
        bad = tmp_path / "romlott.jpg"
        bad.write_bytes(b"nem kep")
        report = make_collage([bad], CollageSettings(width=200, height=200))
        assert report.used == ()
        assert report.image.shape == (200, 200, 3)

    def test_empty_input_is_error(self):
        with pytest.raises(ValueError):
            make_collage([])

    def test_pile_is_repeatable(self, tmp_path):
        photos = [_write_photo(tmp_path / f"{i}.jpg") for i in range(4)]
        settings = CollageSettings(kind=PILE, width=400, height=400, seed=5)
        first = make_collage(photos, settings).image
        second = make_collage(photos, settings).image
        assert np.array_equal(first, second)

    def test_background_shows_through_on_contact_sheet(self, tmp_path):
        photos = [_write_photo(tmp_path / f"{i}.jpg", size=(300, 100)) for i in range(2)]
        report = make_collage(
            photos,
            CollageSettings(
                kind=CONTACT_SHEET, width=600, height=600, background=(0, 255, 0)
            ),
        )
        greens = np.all(report.image == (0, 255, 0), axis=2)
        assert greens.any(), "a széles képek mellett látszania kell a háttérnek"


class TestSettingsValidation:
    def test_tiny_canvas(self):
        with pytest.raises(ValueError):
            CollageSettings(width=4, height=4)

    def test_negative_spacing(self):
        with pytest.raises(ValueError):
            CollageSettings(spacing=-1)

    def test_bad_background(self):
        with pytest.raises(ValueError):
            CollageSettings(background=(300, 0, 0))


class TestWriteCollage:
    def test_writes_readable_jpeg(self, tmp_path):
        photos = [_write_photo(tmp_path / f"{i}.jpg") for i in range(3)]
        report = make_collage(photos, CollageSettings(width=320, height=240))
        target = write_collage(tmp_path / "ki" / "kollazs.jpg", report.image)
        assert target.exists()
        decoded = cv2.imdecode(
            np.frombuffer(target.read_bytes(), np.uint8), cv2.IMREAD_COLOR
        )
        assert decoded.shape == (240, 320, 3)

    def test_accented_path_is_written(self, tmp_path):
        """A #190 tanulsága: ékezetes útvonalon a cv2.imwrite Windowson
        némán nem ír — a bájt-alapú útnak működnie kell."""
        photos = [_write_photo(tmp_path / "a.jpg")]
        report = make_collage(photos, CollageSettings(width=200, height=200))
        target = write_collage(tmp_path / "Képek" / "kollázs_ő.jpg", report.image)
        assert target.exists() and target.stat().st_size > 0

    def test_invalid_quality(self, tmp_path):
        image = np.zeros((10, 10, 3), np.uint8)
        with pytest.raises(ValueError):
            write_collage(tmp_path / "x.jpg", image, quality=0)
