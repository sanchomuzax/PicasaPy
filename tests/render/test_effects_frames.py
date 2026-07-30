"""A `picasapy.render.effects_frames` (a Picasa 5. fülének, kék ecsetnek,
MÉRETNÖVELŐ, keretes effektjei: Border, DropShadow, MuseumMatte, Polaroid)
tesztjei.

**ŐSZINTESÉG:** nincs golden-mérés ezekhez az effektekhez (#330) — a
tesztek a MEGFIGYELHETŐ kimenetet (méretnövekedés, keretszín a szélen,
dtype-tartás) ellenőrzik, NEM azt, hogy a kimenet pixelhűen egyezik a
Picasáéval (arra nincs referencia-adat, ld. #317).

Mind a négy effekt megnöveli a kép méretét — ez a modul kiemelt tesztelési
szempontja (méret-asszerciók minden effektnél).
"""

from __future__ import annotations

import numpy as np
import pytest

from picasapy.render.effects_frames import (
    apply_border,
    apply_drop_shadow,
    apply_museum_matte,
    apply_polaroid,
)


def _uniform_image(
    value: int | tuple[int, int, int], height: int = 40, width: int = 60
) -> np.ndarray:
    return np.full((height, width, 3), value, dtype=np.uint8)


class TestApplyBorder:
    def test_meret_a_vartra_no(self) -> None:
        image = _uniform_image(100, height=40, width=60)
        result = apply_border(image, width=20.0, color=(255, 255, 255))
        # rövidebb oldal (40) 20%-a = 8 px keret mindkét oldalon
        assert result.shape == (56, 76, 3)

    def test_szelso_pixelsor_a_keret_szine(self) -> None:
        image = _uniform_image(0, height=40, width=60)
        result = apply_border(image, width=10.0, color=(200, 100, 50))
        np.testing.assert_array_equal(result[0, 0], (200, 100, 50))
        np.testing.assert_array_equal(result[-1, -1], (200, 100, 50))

    def test_belso_kep_valtozatlan(self) -> None:
        image = _uniform_image(77, height=40, width=60)
        result = apply_border(image, width=10.0, color=(255, 255, 255))
        border_px = round(min(40, 60) * 10.0 / 100.0)
        inner = result[border_px : border_px + 40, border_px : border_px + 60]
        np.testing.assert_array_equal(inner, image)

    def test_nulla_szelesseg_azonos_meret(self) -> None:
        image = _uniform_image(100)
        result = apply_border(image, width=0.0)
        assert result.shape == image.shape
        np.testing.assert_array_equal(result, image)

    def test_dtype_megmarad(self) -> None:
        image = _uniform_image(100)
        result = apply_border(image, width=15.0)
        assert result.dtype == np.uint8

    def test_nem_mutalja_a_bemenetet(self) -> None:
        image = _uniform_image(50)
        original = image.copy()
        apply_border(image, width=15.0)
        np.testing.assert_array_equal(image, original)

    def test_negativ_szelesseg_value_error(self) -> None:
        with pytest.raises(ValueError):
            apply_border(_uniform_image(0), width=-1.0)

    def test_hibas_szin_value_error(self) -> None:
        with pytest.raises(ValueError):
            apply_border(_uniform_image(0), color=(1, 2))  # type: ignore[arg-type]

    def test_fekete_feher_szelso_bemenet_nem_dob(self) -> None:
        apply_border(_uniform_image(0))
        apply_border(_uniform_image(255))


class TestApplyDropShadow:
    def test_meret_a_bemenetnel_nagyobb(self) -> None:
        image = _uniform_image(100, height=40, width=60)
        result = apply_drop_shadow(image, border_width=4.0, blur=10.0)
        assert result.shape[0] > image.shape[0]
        assert result.shape[1] > image.shape[1]

    def test_meret_a_bekeretezettnel_is_nagyobb(self) -> None:
        image = _uniform_image(100, height=40, width=60)
        bordered_result = apply_border(image, width=4.0, color=(255, 255, 255))
        shadow_result = apply_drop_shadow(
            image, border_width=4.0, blur=10.0, border_color=(255, 255, 255)
        )
        assert shadow_result.shape[0] > bordered_result.shape[0]
        assert shadow_result.shape[1] > bordered_result.shape[1]

    def test_dtype_megmarad(self) -> None:
        image = _uniform_image(100, height=30, width=30)
        result = apply_drop_shadow(image)
        assert result.dtype == np.uint8

    def test_nem_mutalja_a_bemenetet(self) -> None:
        image = _uniform_image(50, height=30, width=30)
        original = image.copy()
        apply_drop_shadow(image, border_width=4.0, blur=8.0)
        np.testing.assert_array_equal(image, original)

    def test_negativ_parameter_value_error(self) -> None:
        with pytest.raises(ValueError):
            apply_drop_shadow(_uniform_image(0), border_width=-1.0)
        with pytest.raises(ValueError):
            apply_drop_shadow(_uniform_image(0), blur=-1.0)
        with pytest.raises(ValueError):
            apply_drop_shadow(_uniform_image(0), opacity=-1.0)
        with pytest.raises(ValueError):
            apply_drop_shadow(_uniform_image(0), opacity=101.0)

    def test_fekete_feher_szelso_bemenet_nem_dob(self) -> None:
        apply_drop_shadow(_uniform_image(0, height=20, width=20))
        apply_drop_shadow(_uniform_image(255, height=20, width=20))


class TestApplyMuseumMatte:
    def test_meret_a_vartra_no(self) -> None:
        image = _uniform_image(100, height=40, width=60)
        result = apply_museum_matte(image, width=25.0)
        mat_px = round(min(40, 60) * 25.0 / 100.0)
        assert result.shape == (40 + 2 * mat_px, 60 + 2 * mat_px, 3)

    def test_sarok_a_paszpartu_szine(self) -> None:
        image = _uniform_image(0, height=40, width=60)
        result = apply_museum_matte(image, width=25.0, mat_color=(228, 234, 240))
        np.testing.assert_array_equal(result[0, 0], (228, 234, 240))

    def test_belso_vonal_a_vonal_szinevel_jelenik_meg(self) -> None:
        image = _uniform_image(0, height=40, width=60)
        result = apply_museum_matte(
            image,
            width=25.0,
            line_position=40.0,
            line_color=(3, 14, 26),
            mat_color=(228, 234, 240),
        )
        mat_px = round(min(40, 60) * 25.0 / 100.0)
        line_offset = round(mat_px * 40.0 / 100.0)
        row = mat_px - line_offset
        # a felső vékony vonal a paszpartu-szín és a kép közötti sávban
        assert tuple(int(c) for c in result[row, result.shape[1] // 2]) == (3, 14, 26)

    def test_nulla_szelesseg_azonos_meret(self) -> None:
        image = _uniform_image(100)
        result = apply_museum_matte(image, width=0.0)
        np.testing.assert_array_equal(result, image)

    def test_dtype_megmarad(self) -> None:
        image = _uniform_image(100)
        result = apply_museum_matte(image, width=20.0)
        assert result.dtype == np.uint8

    def test_nem_mutalja_a_bemenetet(self) -> None:
        image = _uniform_image(50)
        original = image.copy()
        apply_museum_matte(image, width=20.0)
        np.testing.assert_array_equal(image, original)

    def test_negativ_szelesseg_value_error(self) -> None:
        with pytest.raises(ValueError):
            apply_museum_matte(_uniform_image(0), width=-1.0)

    def test_ervenytelen_vonalpozicio_value_error(self) -> None:
        with pytest.raises(ValueError):
            apply_museum_matte(_uniform_image(0), line_position=-1.0)
        with pytest.raises(ValueError):
            apply_museum_matte(_uniform_image(0), line_position=101.0)

    def test_fekete_feher_szelso_bemenet_nem_dob(self) -> None:
        apply_museum_matte(_uniform_image(0))
        apply_museum_matte(_uniform_image(255))


class TestApplyPolaroid:
    def test_also_sav_szelesebb_mint_az_oldalso(self) -> None:
        image = _uniform_image(100, height=40, width=60)
        result = apply_polaroid(image, border_width=5.0, color=(226, 226, 226))
        side_px = round(min(40, 60) * 5.0 / 100.0)
        bottom_px = round(side_px * 3.0)
        assert result.shape == (40 + side_px + bottom_px, 60 + 2 * side_px, 3)
        # az aszimmetria: a magasság-növekmény nagyobb, mint 2×side_px
        assert (result.shape[0] - 40) > 2 * side_px

    def test_keret_a_keret_szinevel_jelenik_meg(self) -> None:
        image = _uniform_image(0, height=40, width=60)
        result = apply_polaroid(image, border_width=5.0, color=(226, 226, 226))
        np.testing.assert_array_equal(result[0, 0], (226, 226, 226))
        np.testing.assert_array_equal(result[-1, -1], (226, 226, 226))

    def test_nulla_szelesseg_azonos_meret(self) -> None:
        image = _uniform_image(100)
        result = apply_polaroid(image, border_width=0.0)
        np.testing.assert_array_equal(result, image)

    def test_dtype_megmarad(self) -> None:
        image = _uniform_image(100)
        result = apply_polaroid(image, border_width=5.0)
        assert result.dtype == np.uint8

    def test_nem_mutalja_a_bemenetet(self) -> None:
        image = _uniform_image(50)
        original = image.copy()
        apply_polaroid(image, border_width=5.0)
        np.testing.assert_array_equal(image, original)

    def test_negativ_szelesseg_value_error(self) -> None:
        with pytest.raises(ValueError):
            apply_polaroid(_uniform_image(0), border_width=-1.0)

    def test_hibas_szin_value_error(self) -> None:
        with pytest.raises(ValueError):
            apply_polaroid(_uniform_image(0), color=(1, 2))  # type: ignore[arg-type]

    def test_fekete_feher_szelso_bemenet_nem_dob(self) -> None:
        apply_polaroid(_uniform_image(0))
        apply_polaroid(_uniform_image(255))
