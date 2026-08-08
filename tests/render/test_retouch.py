"""`picasapy.render.retouch` — determinisztikus pixel-tesztek szintetikus
képeken. Mindkét módszer (v1 cv2.inpaint/Telea, v2 kör alakú klónozás)
kalibrálatlan közelítés (ld. a modul docsztringjét) — a tesztek a
MECHANIZMUST (régió/folt-kitöltés, immutabilitás, határesetek)
ellenőrzik, nem a Picasa-hűséget."""

from __future__ import annotations

import numpy as np

from picasapy.ini.rect64 import Rect64
from picasapy.ini.retouch import RetouchPatch
from picasapy.render.retouch import apply_retouch, apply_retouch_patches


def _blotch_image(width: int = 40, height: int = 30) -> np.ndarray:
    """Egyenletes szürke háttér, közepén egy éles piros folttal."""
    image = np.full((height, width, 3), 180, dtype=np.uint8)
    image[10:20, 15:25] = (220, 30, 30)
    return image


class TestApplyRetouch:
    def test_regio_nelkul_no_op(self) -> None:
        image = _blotch_image()
        result = apply_retouch(image)
        np.testing.assert_array_equal(result, image)

    def test_regio_nelkul_masolatot_ad(self) -> None:
        image = _blotch_image()
        result = apply_retouch(image)
        result[0, 0, 0] = 5
        assert image[0, 0, 0] != 5

    def test_folt_eltuntetese(self) -> None:
        image = _blotch_image()
        region = Rect64(15 / 40, 10 / 30, 25 / 40, 20 / 30)
        result = apply_retouch(image, (region,))
        # a folt közepén a piros csatorna a háttér felé kell mozduljon
        center_before = image[15, 20]
        center_after = result[15, 20]
        assert abs(int(center_after[0]) - 180) < abs(int(center_before[0]) - 180)

    def test_nem_mutalja_a_bemenetet(self) -> None:
        image = _blotch_image()
        original = image.copy()
        apply_retouch(image, (Rect64(0.3, 0.3, 0.6, 0.6),))
        np.testing.assert_array_equal(image, original)

    def test_kepen_kivuli_regio_nem_dob_hibat(self) -> None:
        image = _blotch_image()
        result = apply_retouch(image, (Rect64(0.0, 0.0, 0.0, 0.0),))
        np.testing.assert_array_equal(result, image)

    def test_kimenet_merete_megegyezik(self) -> None:
        image = _blotch_image()
        result = apply_retouch(image, (Rect64(0.1, 0.1, 0.9, 0.9),))
        assert result.shape == image.shape
        assert result.dtype == image.dtype


def _two_tone_image(width: int = 40, height: int = 30) -> np.ndarray:
    """Bal fél piros, jobb fél zöld — a klónozás iránya jól ellenőrizhető."""
    image = np.zeros((height, width, 3), dtype=np.uint8)
    image[:, : width // 2] = (220, 30, 30)
    image[:, width // 2 :] = (30, 220, 30)
    return image


class TestApplyRetouchPatches:
    """#445: `apply_retouch_patches` — irányított klónozás (cél+forrás+sugár)."""

    def test_folt_nelkul_no_op(self) -> None:
        image = _two_tone_image()
        result = apply_retouch_patches(image)
        np.testing.assert_array_equal(result, image)

    def test_folt_nelkul_masolatot_ad(self) -> None:
        image = _two_tone_image()
        result = apply_retouch_patches(image)
        result[0, 0, 0] = 5
        assert image[0, 0, 0] != 5

    def test_nem_mutalja_a_bemenetet(self) -> None:
        image = _two_tone_image()
        original = image.copy()
        patch = RetouchPatch(0.75, 0.5, 0.25, 0.5, 0.15)
        apply_retouch_patches(image, (patch,))
        np.testing.assert_array_equal(image, original)

    def test_kimenet_merete_megegyezik(self) -> None:
        image = _two_tone_image()
        patch = RetouchPatch(0.75, 0.5, 0.25, 0.5, 0.15)
        result = apply_retouch_patches(image, (patch,))
        assert result.shape == image.shape
        assert result.dtype == image.dtype

    def test_cel_a_forras_szinet_veszi_fel(self) -> None:
        """A jobb (zöld) oldal célja a bal (piros) oldal forrás-tartalmát
        kapja a folt körén belül."""
        image = _two_tone_image()
        patch = RetouchPatch(target_x=0.75, target_y=0.5, source_x=0.25, source_y=0.5, radius=0.1)
        result = apply_retouch_patches(image, (patch,))
        # a cél középpontja most piros (a forrásról másolva)
        np.testing.assert_array_equal(result[15, 30], image[15, 10])
        assert tuple(result[15, 30]) == (220, 30, 30)

    def test_kor_alaku_a_folt(self) -> None:
        """A folton kívüli pixelek NEM változnak — a maszk kör, nem
        négyzet."""
        image = _two_tone_image()
        patch = RetouchPatch(target_x=0.75, target_y=0.5, source_x=0.25, source_y=0.5, radius=0.05)
        result = apply_retouch_patches(image, (patch,))
        # a folt sarkában (a bounding-boxban, de a körön kívül) érintetlen
        corner = image[10, 27]
        np.testing.assert_array_equal(result[10, 27], corner)

    def test_egymasra_epulo_foltok_sorrendben_alkalmazodnak(self) -> None:
        """Két, egymást átfedő folt sorrendben épül — a második a MÁR
        módosított tartalmat is forrásként használhatja (#445, "lather,
        rinse, repeat")."""
        image = _two_tone_image()
        first = RetouchPatch(target_x=0.75, target_y=0.5, source_x=0.25, source_y=0.5, radius=0.15)
        second = RetouchPatch(target_x=0.9, target_y=0.5, source_x=0.75, source_y=0.5, radius=0.05)
        result = apply_retouch_patches(image, (first, second))
        # a második folt cél-pontja a piros (első foltból eredő) tartalmat kapja
        assert tuple(result[15, 36]) == (220, 30, 30)

    def test_kepen_kivuli_forras_nem_dob_hibat(self) -> None:
        image = _two_tone_image()
        patch = RetouchPatch(target_x=0.5, target_y=0.5, source_x=0.0, source_y=0.0, radius=0.3)
        result = apply_retouch_patches(image, (patch,))
        assert result.shape == image.shape

    def test_nulla_sugaru_folt_nem_dob_hibat(self) -> None:
        image = _two_tone_image()
        patch = RetouchPatch(target_x=0.5, target_y=0.5, source_x=0.1, source_y=0.1, radius=0.0)
        result = apply_retouch_patches(image, (patch,))
        assert result.shape == image.shape
