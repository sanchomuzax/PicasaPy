"""`picasapy.render.retouch.apply_retouch` — determinisztikus pixel-tesztek
szintetikus képeken. A módszer (cv2.inpaint/Telea) kalibrálatlan közelítés
(ld. a modul docsztringjét) — a tesztek a MECHANIZMUST (régió-kitöltés,
immutabilitás, határesetek) ellenőrzik, nem a Picasa-hűséget."""

from __future__ import annotations

import numpy as np

from picasapy.ini.rect64 import Rect64
from picasapy.render.retouch import apply_retouch


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
