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
        assert result.min() == 0
        assert result.max() == 255

    def test_globalis_min_max_linearis(self) -> None:
        # megfejtve (golden 3. kör): ki = (be − gmin)·255/(gmax − gmin)
        image = np.zeros((1, 3, 3), dtype=np.uint8)
        image[0, 0] = 80
        image[0, 1] = 130
        image[0, 2] = 180
        result = apply_autolight(image)
        assert result[0, 0, 0] == 0
        assert abs(int(result[0, 1, 0]) - 128) <= 1
        assert result[0, 2, 0] == 255

    def test_kozos_csatorna_transzformacio(self) -> None:
        # a stretch KÖZÖS mindhárom csatornára — a színegyensúly megmarad
        image = np.zeros((1, 2, 3), dtype=np.uint8)
        image[0, 0] = (60, 80, 100)
        image[0, 1] = (180, 200, 220)
        result = apply_autolight(image)
        # gmin=60, gmax=220 → skála 255/160
        assert result[0, 0, 0] == 0
        assert abs(int(result[0, 0, 1]) - 32) <= 1
        assert result[0, 1, 2] == 255

    def test_teljes_tartomanyu_kepen_no_op(self) -> None:
        # megfejtve: full-range bemeneten az autolightnak nincs dolga
        ramp = np.tile(np.arange(256, dtype=np.uint8), (2, 1))
        image = np.stack([ramp, ramp, ramp], axis=-1)
        np.testing.assert_array_equal(apply_autolight(image), image)

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
    def test_semleges_kepen_no_op(self) -> None:
        # megfejtve: semleges (szürke) bemeneten az autocolor nem csinál semmit
        image = _gradient_image()
        np.testing.assert_array_equal(apply_autocolor(image), image)

    def test_szinontetet_a_szurke_fele_huzza_csillapitva(self) -> None:
        # megfejtve (golden 3-4. kör): csillapított szürkevilág-korrekció —
        # a cast csökken, de nem tűnik el teljesen
        image = np.full((10, 10, 3), (135, 142, 157), dtype=np.uint8)
        result = apply_autocolor(image)
        spread_before = int(image[..., 2].max()) - int(image[..., 0].min())
        spread_after = int(result[0, 0, 2]) - int(result[0, 0, 0])
        assert 0 < spread_after < spread_before
        # irány: a gyenge R erősödik, az erős B gyengül
        assert int(result[0, 0, 0]) > 135
        assert int(result[0, 0, 2]) < 157

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
    def test_fix_tonusgorbe_a_semleges_rampan(self) -> None:
        # megfejtve (golden 3. kör): enhance = fixLUT(stretch(autocolor(kép))).
        # Teljes tartományú semleges rámpán a stretch és az autocolor no-op,
        # így a kimenet maga a mért reziduál-görbe.
        ramp = np.tile(np.arange(256, dtype=np.uint8), (2, 1))
        image = np.stack([ramp, ramp, ramp], axis=-1)
        result = apply_enhance(image)
        mert_pontok = {16: 18.7, 64: 71.3, 128: 142.7, 192: 214.0, 240: 255.0}
        for bemenet, vart in mert_pontok.items():
            assert abs(int(result[0, bemenet, 0]) - vart) <= 1.0

    def test_vilagosit_kozeptonusban(self) -> None:
        # a reziduál-görbe enyhén emel — az enhance nem sötétebb a stretchnél
        image = _gradient_image()
        result = apply_enhance(image)
        assert result.mean() >= apply_autolight(image).mean()

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
