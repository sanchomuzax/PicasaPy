"""Exportálás mappába (issue #16): forgatás beleégetése + átméretezés OpenCV-vel."""

import cv2
import numpy as np
import pytest

from picasapy.export import ExportItem, ExportSettings, export_photos
from support.jpeg_factory import make_jpeg


def _make_half_and_half(path, width=40, height=20):
    """Bal fele fehér, jobb fele fekete — a forgásirány pixelszintű próbájához."""
    image = np.zeros((height, width, 3), dtype=np.uint8)
    image[:, : width // 2] = 255
    assert cv2.imwrite(str(path), image)
    return path


class TestBasicExport:
    def test_exports_jpeg_with_same_stem(self, tmp_path):
        source = make_jpeg(tmp_path / "nyaralás.jpg")
        target_dir = tmp_path / "out"
        report = export_photos([ExportItem(source)], target_dir)
        assert [p.name for p in report.exported] == ["nyaralás.jpg"]
        assert (target_dir / "nyaralás.jpg").exists()
        assert report.failed == ()

    def test_non_jpeg_source_is_reencoded_as_jpeg(self, tmp_path):
        source = _make_half_and_half(tmp_path / "kép.png")
        report = export_photos([ExportItem(source)], tmp_path / "out")
        assert [p.suffix for p in report.exported] == [".jpg"]

    def test_name_collision_gets_numbered_suffix(self, tmp_path):
        (tmp_path / "a").mkdir()
        (tmp_path / "b").mkdir()
        first = make_jpeg(tmp_path / "a" / "kép.jpg")
        second = make_jpeg(tmp_path / "b" / "kép.jpg")
        target_dir = tmp_path / "out"
        report = export_photos([ExportItem(first), ExportItem(second)], target_dir)
        assert [p.name for p in report.exported] == ["kép.jpg", "kép-1.jpg"]

    def test_export_order_follows_input_order(self, tmp_path):
        sources = [make_jpeg(tmp_path / f"{i}.jpg") for i in (3, 1, 2)]
        report = export_photos([ExportItem(s) for s in sources], tmp_path / "out")
        assert [p.stem for p in report.exported] == ["3", "1", "2"]


class TestResize:
    def test_longest_side_is_capped(self, tmp_path):
        source = _make_half_and_half(tmp_path / "nagy.png", width=40, height=20)
        report = export_photos(
            [ExportItem(source)], tmp_path / "out", ExportSettings(max_dimension=10)
        )
        exported = cv2.imread(str(report.exported[0]))
        assert exported.shape[:2] == (5, 10)  # (magasság, szélesség)

    def test_no_upscale_beyond_original(self, tmp_path):
        source = _make_half_and_half(tmp_path / "kicsi.png", width=40, height=20)
        report = export_photos(
            [ExportItem(source)], tmp_path / "out", ExportSettings(max_dimension=1000)
        )
        exported = cv2.imread(str(report.exported[0]))
        assert exported.shape[:2] == (20, 40)


class TestRotation:
    def test_one_step_rotates_90_clockwise(self, tmp_path):
        # A Picasa/Qt konvenció: 1 lépés = 90° órairányban → a bal (fehér)
        # szél felülre kerül.
        source = _make_half_and_half(tmp_path / "forgó.png", width=40, height=20)
        report = export_photos(
            [ExportItem(source, rotate_steps=1)], tmp_path / "out"
        )
        exported = cv2.imread(str(report.exported[0]))
        assert exported.shape[:2] == (40, 20)  # oldalak felcserélve
        assert exported[:10].mean() > 200  # felső negyed: fehér
        assert exported[-10:].mean() < 50  # alsó negyed: fekete

    def test_two_steps_rotate_180(self, tmp_path):
        source = _make_half_and_half(tmp_path / "forgó.png", width=40, height=20)
        report = export_photos(
            [ExportItem(source, rotate_steps=2)], tmp_path / "out"
        )
        exported = cv2.imread(str(report.exported[0]))
        assert exported.shape[:2] == (20, 40)
        assert exported[:, :20].mean() < 50  # bal fél: fekete lett
        assert exported[:, 20:].mean() > 200

    def test_steps_wrap_modulo_four(self, tmp_path):
        source = _make_half_and_half(tmp_path / "forgó.png")
        report = export_photos(
            [ExportItem(source, rotate_steps=4)], tmp_path / "out"
        )
        exported = cv2.imread(str(report.exported[0]))
        assert exported.shape[:2] == (20, 40)
        assert exported[:, :20].mean() > 200  # változatlan


class TestFallbacksAndErrors:
    def test_video_is_copied_verbatim(self, tmp_path):
        payload = "nem igazi mp4, de bitre pontosan másolandó".encode("utf-8")
        source = tmp_path / "videó.mp4"
        source.write_bytes(payload)
        report = export_photos([ExportItem(source)], tmp_path / "out")
        assert [p.name for p in report.exported] == ["videó.mp4"]
        assert report.exported[0].read_bytes() == payload

    def test_missing_source_goes_to_failed(self, tmp_path):
        report = export_photos(
            [ExportItem(tmp_path / "nincs.jpg")], tmp_path / "out"
        )
        assert report.exported == ()
        assert [p.name for p in report.failed] == ["nincs.jpg"]

    def test_undecodable_image_goes_to_failed(self, tmp_path):
        source = tmp_path / "rossz.jpg"
        source.write_bytes(b"ez nem JPEG")
        report = export_photos([ExportItem(source)], tmp_path / "out")
        assert [p.name for p in report.failed] == ["rossz.jpg"]

    def test_failure_does_not_stop_batch(self, tmp_path):
        bad = tmp_path / "rossz.jpg"
        bad.write_bytes(b"x")
        good = make_jpeg(tmp_path / "jó.jpg")
        report = export_photos(
            [ExportItem(bad), ExportItem(good)], tmp_path / "out"
        )
        assert [p.name for p in report.exported] == ["jó.jpg"]
        assert [p.name for p in report.failed] == ["rossz.jpg"]


class TestSettingsValidation:
    @pytest.mark.parametrize("quality", [0, 101, -5])
    def test_invalid_quality_raises(self, quality):
        with pytest.raises(ValueError):
            ExportSettings(jpeg_quality=quality)

    @pytest.mark.parametrize("dimension", [0, -1])
    def test_invalid_max_dimension_raises(self, dimension):
        with pytest.raises(ValueError):
            ExportSettings(max_dimension=dimension)

    def test_quality_is_respected(self, tmp_path):
        source = _make_half_and_half(tmp_path / "kép.png", width=400, height=200)
        low = export_photos(
            [ExportItem(source)], tmp_path / "low", ExportSettings(jpeg_quality=10)
        )
        high = export_photos(
            [ExportItem(source)], tmp_path / "high", ExportSettings(jpeg_quality=95)
        )
        assert low.exported[0].stat().st_size < high.exported[0].stat().st_size
