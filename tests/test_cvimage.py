"""Közös OpenCV képsegédek (#151/7): a thumbs↔export duplikáció helyett
egyetlen `picasapy.cvimage` modul."""

import cv2
import numpy as np

from picasapy.cvimage import read_image_bytes, scale_down


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
