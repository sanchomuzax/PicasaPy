"""A `picasapy.render.ops` műveletek tesztjei: szintetikus numpy képeken,
fájl-IO nélkül, determinisztikus asszertekkel."""

from __future__ import annotations

import numpy as np
import pytest

from picasapy.ini.rect64 import Rect64
from picasapy.render.ops import (
    apply_autocolor,
    apply_autolight,
    apply_crop,
    apply_enhance,
    apply_redeye,
    apply_tilt,
)


def _gradient_image(width: int = 20, height: int = 10) -> np.ndarray:
    """Determinisztikus, alacsony kontrasztú RGB gradiens teszt-kép."""
    row = np.linspace(80, 180, width, dtype=np.uint8)
    image = np.tile(row, (height, 1))
    return np.stack([image, image, image], axis=-1).astype(np.uint8)


class TestApplyCrop:
    def test_pixel_pontos_meret(self) -> None:
        image = _gradient_image(width=20, height=10)
        rect = Rect64(left=0.25, top=0.2, right=0.75, bottom=0.8)
        result = apply_crop(image, rect)
        assert result.shape == (6, 10, 3)

    def test_nem_mutalja_a_bemenetet(self) -> None:
        image = _gradient_image()
        original = image.copy()
        apply_crop(image, Rect64(0.0, 0.0, 1.0, 1.0))[0, 0, 0] = 255
        np.testing.assert_array_equal(image, original)

    def test_ures_kivagas_value_error(self) -> None:
        image = _gradient_image()
        with pytest.raises(ValueError):
            apply_crop(image, Rect64(0.5, 0.5, 0.5, 0.9))

    def test_teljes_kep_valtozatlan(self) -> None:
        image = _gradient_image()
        result = apply_crop(image, Rect64(0.0, 0.0, 1.0, 1.0))
        np.testing.assert_array_equal(result, image)


class TestApplyTilt:
    def test_nulla_szog_identitas_meret(self) -> None:
        image = _gradient_image()
        result = apply_tilt(image, angle=0.0, scale=1.0)
        assert result.shape == image.shape

    def test_kimenet_merete_megegyezik_bemenettel(self) -> None:
        image = _gradient_image(width=30, height=15)
        result = apply_tilt(image, angle=0.2, scale=1.1)
        assert result.shape == image.shape

    def test_nem_mutalja_a_bemenetet(self) -> None:
        image = _gradient_image()
        original = image.copy()
        apply_tilt(image, angle=0.3, scale=1.0)
        np.testing.assert_array_equal(image, original)


class TestApplyAutolight:
    def test_szethuzza_a_hisztogramot(self) -> None:
        image = _gradient_image()
        result = apply_autolight(image)
        assert result.min() < 10
        assert result.max() > 245

    def test_nem_mutalja_a_bemenetet(self) -> None:
        image = _gradient_image()
        original = image.copy()
        apply_autolight(image)
        np.testing.assert_array_equal(image, original)

    def test_dtype_uint8(self) -> None:
        image = _gradient_image()
        result = apply_autolight(image)
        assert result.dtype == np.uint8


class TestApplyAutocolor:
    def test_csatorna_fehérpontra_skaláz(self) -> None:
        image = np.zeros((10, 10, 3), dtype=np.uint8)
        image[..., 0] = 100  # R csatorna gyenge
        image[..., 1] = 200  # G csatorna erősebb
        image[..., 2] = 50  # B csatorna leggyengébb
        result = apply_autocolor(image)
        # a legerősebb csatornákat (percentilis alapján) 255 közelébe kell húzni
        assert result[..., 1].max() >= 250

    def test_nem_mutalja_a_bemenetet(self) -> None:
        image = _gradient_image()
        original = image.copy()
        apply_autocolor(image)
        np.testing.assert_array_equal(image, original)

    def test_clip_0_255(self) -> None:
        image = _gradient_image()
        result = apply_autocolor(image)
        assert result.min() >= 0
        assert result.max() <= 255


class TestApplyEnhance:
    def test_autolight_es_autocolor_egymas_utan(self) -> None:
        image = _gradient_image()
        expected = apply_autocolor(apply_autolight(image))
        result = apply_enhance(image)
        np.testing.assert_array_equal(result, expected)

    def test_nem_mutalja_a_bemenetet(self) -> None:
        image = _gradient_image()
        original = image.copy()
        apply_enhance(image)
        np.testing.assert_array_equal(image, original)


class TestApplyRedeye:
    def _kep_voros_pupillaval(self) -> np.ndarray:
        image = np.full((20, 20, 3), 120, dtype=np.uint8)  # semleges bőrtónus-szerű háttér
        image[8:12, 8:12] = (200, 30, 30)  # erősen vörös "pupilla"
        return image

    def test_csak_a_voros_regiot_modositja(self) -> None:
        image = self._kep_voros_pupillaval()
        result = apply_redeye(image)
        # a háttér változatlan
        np.testing.assert_array_equal(result[0:8, 0:8], image[0:8, 0:8])
        # a vörös régió R csatornája csökken
        assert result[10, 10, 0] < image[10, 10, 0]

    def test_bortonust_nem_bantja(self) -> None:
        image = np.full((10, 10, 3), (180, 140, 120), dtype=np.uint8)
        result = apply_redeye(image)
        np.testing.assert_array_equal(result, image)

    def test_regiokra_korlatozhato(self) -> None:
        image = self._kep_voros_pupillaval()
        # a régión kívüli terület nem kap figyelmet, még ha lenne is benne vörös
        regions = (Rect64(0.0, 0.0, 0.3, 0.3),)  # nem fedi a vörös foltot (0.4-0.6)
        result = apply_redeye(image, regions=regions)
        np.testing.assert_array_equal(result, image)

    def test_nem_mutalja_a_bemenetet(self) -> None:
        image = self._kep_voros_pupillaval()
        original = image.copy()
        apply_redeye(image)
        np.testing.assert_array_equal(image, original)
