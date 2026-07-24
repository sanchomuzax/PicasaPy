"""Közös OpenCV képsegédek (#151/7): a thumbs↔export duplikáció helyett
egyetlen `picasapy.cvimage` modul."""

import cv2
import numpy as np

from picasapy.cvimage import read_image_bytes, reduced_color_flag, scale_down


def _encoded_jpeg(width: int, height: int) -> np.ndarray:
    """Egy `width x height` JPEG bájtjai np.uint8 tömbként (a
    `read_image_bytes` kimenetének alakjában)."""
    image = np.zeros((height, width, 3), dtype=np.uint8)
    image[:, :, 1] = np.linspace(0, 255, width, dtype=np.uint8)[np.newaxis, :]
    ok, encoded = cv2.imencode(".jpg", image)
    assert ok
    return encoded


class TestScaleDown:
    def test_none_limit_is_noop(self):
        image = np.zeros((10, 20, 3), dtype=np.uint8)
        assert scale_down(image, None) is image

    def test_small_image_untouched(self):
        image = np.zeros((10, 20, 3), dtype=np.uint8)
        assert scale_down(image, 64) is image

    def test_longest_side_capped_aspect_kept(self):
        image = np.zeros((100, 200, 3), dtype=np.uint8)
        result = scale_down(image, 50)
        assert result.shape[:2] == (25, 50)

    def test_never_zero_dimension(self):
        image = np.zeros((1, 1000, 3), dtype=np.uint8)
        result = scale_down(image, 10)
        assert result.shape[0] >= 1 and result.shape[1] == 10


class TestReadImageBytes:
    def test_missing_file_gives_none(self, tmp_path):
        assert read_image_bytes(tmp_path / "nincs.jpg") is None

    def test_empty_file_gives_none(self, tmp_path):
        path = tmp_path / "ures.jpg"
        path.write_bytes(b"")
        assert read_image_bytes(path) is None

    def test_valid_image_decodable(self, tmp_path):
        path = tmp_path / "kis.png"
        ok, encoded = cv2.imencode(".png", np.full((4, 4, 3), 128, dtype=np.uint8))
        assert ok
        path.write_bytes(encoded.tobytes())
        payload = read_image_bytes(path)
        assert payload is not None
        assert cv2.imdecode(payload, cv2.IMREAD_COLOR) is not None


class TestReducedColorFlag:
    """#294: a redukált JPEG-dekódolás közös döntése — eddig a
    `thumbs/cache.py::_read_flag`-ben élt, most a dedup dHash is ezt
    használja (a logika NEM duplikálódik)."""

    def test_small_image_decodes_at_full_resolution(self):
        payload = _encoded_jpeg(40, 40)
        assert reduced_color_flag(payload, 32) == cv2.IMREAD_COLOR

    def test_huge_image_uses_strongest_reduction(self):
        payload = _encoded_jpeg(1024, 512)
        assert reduced_color_flag(payload, 32) == cv2.IMREAD_REDUCED_COLOR_8

    def test_medium_image_uses_moderate_reduction(self):
        # 300 // 8 = 37 < 64, de 300 // 4 = 75 >= 64 → 4-es faktor
        payload = _encoded_jpeg(300, 200)
        assert reduced_color_flag(payload, 32) == cv2.IMREAD_REDUCED_COLOR_4

    def test_larger_goal_keeps_more_pixels(self):
        """Ugyanaz a kép nagyobb célmérethez kevésbé redukálva olvasódik —
        a bélyegkép-cache (goal=256) és a dHash (goal=32) így ugyanazt a
        helpert hívhatja eltérő igénnyel."""
        payload = _encoded_jpeg(1024, 512)
        assert reduced_color_flag(payload, 256) == cv2.IMREAD_REDUCED_COLOR_2
        assert reduced_color_flag(payload, 1024) == cv2.IMREAD_COLOR

    def test_undecodable_payload_falls_back_to_full_read(self):
        payload = np.frombuffer(b"nem kep", dtype=np.uint8)
        assert reduced_color_flag(payload, 32) == cv2.IMREAD_COLOR
