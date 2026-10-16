"""`picasapy.render.retouch` — determinisztikus pixel-tesztek szintetikus
képeken. A v2 irányított Poisson-gyógyítás a #4544 `job-151` Colab-
mérésének lineáris átmenet és textúra viselkedését őrzi."""

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
    """Bal fél piros, jobb fél zöld — sík forráskörnél a cél tónusa marad."""
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

    def test_lapos_forras_gradiens_nelkul_megtartja_a_cel_tonusat(self) -> None:
        """A lapos forrás nem húzza át a teljes színét a célkörre."""
        image = _two_tone_image()
        patch = RetouchPatch(target_x=0.75, target_y=0.5, source_x=0.25, source_y=0.5, radius=0.1)
        result = apply_retouch_patches(image, (patch,))
        # A forráskörön nincs gradiens; a cél eredeti zöld tónusa marad.
        assert int(np.abs(result[15, 30].astype(np.int16) - image[15, 30]).max()) <= 2

    def test_linearis_atmenet_forrasbol_gyogyitva_a_referencia_marad(self) -> None:
        """A #4544 job-151 mérése szerint 28→200-as sima rámpán a
        célkör legfeljebb 1–2 szintet térhet el az eredeti rámpától."""
        width, height = 400, 200
        gray = np.rint(np.linspace(0, 255, width)).astype(np.uint8)
        image = np.repeat(gray[np.newaxis, :, np.newaxis], height, axis=0)
        image = np.repeat(image, 3, axis=2)
        original = image.copy()
        patch = RetouchPatch(
            target_x=0.11,
            target_y=0.5,
            source_x=0.78,
            source_y=0.5,
            radius=0.05,
        )

        result = apply_retouch_patches(image, (patch,))

        assert int(original[height // 2, round(patch.target_x * width), 0]) == 28
        assert int(original[height // 2, round(patch.source_x * width), 0]) in (199, 200)
        elt = np.abs(result.astype(np.int16) - original.astype(np.int16))
        assert int(elt.max()) <= 2
        np.testing.assert_array_equal(image, original)

    def test_texturas_forras_gradienset_atveszi_de_a_cel_atlagszintjet_tartja(self) -> None:
        """A forrás textúrája átkerül, de az eltérő forrás-átlag nem festi
        világosra a 128-as célkörnyezetet."""
        width, height = 160, 120
        image = np.full((height, width, 3), 128, dtype=np.uint8)
        yy, xx = np.indices((height, width))
        checker = ((xx + yy) % 2) == 0
        source_area = xx < 56
        image[source_area & checker] = 170
        image[source_area & ~checker] = 230
        patch = RetouchPatch(
            target_x=0.75,
            target_y=0.5,
            source_x=0.25,
            source_y=0.5,
            radius=0.1,
        )

        result = apply_retouch_patches(image, (patch,))

        cy = round(patch.target_y * height)
        cx = round(patch.target_x * width)
        radius = round(patch.radius * min(width, height))
        py, px = np.ogrid[:height, :width]
        inner_circle = (px - cx) ** 2 + (py - cy) ** 2 <= (radius - 2) ** 2
        target = result[inner_circle, 0].astype(np.float32)
        assert abs(float(target.mean()) - 128.0) <= 2.0
        assert float(target.std()) >= 15.0

    def test_kep_szelere_eso_folt_gyogyit_es_nem_dob_kivetelt(self) -> None:
        """A képszél levágja a kör egy részét, de a mért rámpa ott is
        folytonos marad, és a renderelés nem dob kivételt."""
        width, height = 120, 80
        gray = np.rint(np.linspace(0, 255, width)).astype(np.uint8)
        image = np.repeat(gray[np.newaxis, :, np.newaxis], height, axis=0)
        image = np.repeat(image, 3, axis=2)
        original = image.copy()
        patch = RetouchPatch(
            target_x=0.02,
            target_y=0.5,
            source_x=0.75,
            source_y=0.5,
            radius=0.1,
        )

        result = apply_retouch_patches(image, (patch,))

        elt = np.abs(result.astype(np.int16) - original.astype(np.int16))
        assert int(elt.max()) <= 4
        np.testing.assert_array_equal(image, original)

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
        """A második folt az első gyógyításával keletkezett textúrát is
        forrásként használja (#445, "lather, rinse, repeat")."""
        image = np.full((120, 160, 3), 128, dtype=np.uint8)
        yy, xx = np.indices(image.shape[:2])
        checker = ((xx + yy) % 2) == 0
        source_area = xx < 56
        image[source_area & checker] = 170
        image[source_area & ~checker] = 230
        first = RetouchPatch(0.5, 0.5, 0.25, 0.5, 0.12)
        second = RetouchPatch(0.8, 0.5, 0.5, 0.5, 0.08)
        first_result = apply_retouch_patches(image, (first,))
        result = apply_retouch_patches(image, (first, second))

        py, px = np.ogrid[:120, :160]
        second_inner = (px - 128) ** 2 + (py - 60) ** 2 <= 8**2
        before_second = first_result[second_inner, 0].astype(np.float32)
        after_second = result[second_inner, 0].astype(np.float32)
        assert float(before_second.std()) < 1.0
        assert abs(float(after_second.mean()) - 128.0) <= 2.0
        assert float(after_second.std()) >= 15.0

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
