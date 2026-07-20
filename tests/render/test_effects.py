"""A `picasapy.render.effects` térbeli effektek tesztjei a golden-elemzés
mérési pontjai ellen (`docs/specs/filters-decoded.md`, 3–4. kör).

Ahol van mért adat (Vignette-maszk, glow középemelés), ott ±1/255 a tűrés;
a többi (radblur, radsat térbeli modellje) dokumentált közelítés, ott a
tesztek a kvalitatív viselkedést rögzítik.
"""

from __future__ import annotations

import numpy as np
import pytest

from picasapy.render.effects import (
    GLOW_V1_INTENSITY,
    GLOW_V1_RADIUS,
    apply_glow,
    apply_radblur,
    apply_radsat,
    apply_vignette,
    vignette_gain,
)


def _uniform_image(
    value: int | tuple[int, int, int], height: int = 6, width: int = 8
) -> np.ndarray:
    return np.full((height, width, 3), value, dtype=np.uint8)


class TestVignetteGain:
    # Mért radiális profil (golden 4. kör, Vignette=1,35.0,1.4,0.0,00000000):
    # közép 1,000 · r≈0,25: 0,994 · r≈0,45: 0,729 · r≈0,65: 0,328 · sarok 0,250
    def test_mert_profil_pontjai(self) -> None:
        assert vignette_gain(0.0) == pytest.approx(1.0, abs=0.004)
        assert vignette_gain(0.25) == pytest.approx(0.994, abs=0.004)
        assert vignette_gain(0.45) == pytest.approx(0.729, abs=0.004)
        assert vignette_gain(0.65) == pytest.approx(0.328, abs=0.004)

    def test_sarkon_tuli_ertek_klippel(self) -> None:
        # a sarok (r≈0,7071) mért értéke 0,250; azon túl nem csökken tovább
        assert vignette_gain(0.7071) == pytest.approx(0.250, abs=0.004)
        assert vignette_gain(0.9) == pytest.approx(0.250, abs=0.004)

    def test_monoton_csokkeno(self) -> None:
        radii = np.linspace(0.0, 0.7071, 30)
        gains = [vignette_gain(float(r)) for r in radii]
        assert all(a >= b for a, b in zip(gains, gains[1:]))

    def test_negativ_sugar_value_error(self) -> None:
        with pytest.raises(ValueError):
            vignette_gain(-0.1)


class TestApplyVignette:
    def test_kozeppont_valtozatlan(self) -> None:
        image = _uniform_image(200, height=51, width=51)
        result = apply_vignette(image)
        assert int(result[25, 25, 0]) == 200

    def test_sarok_a_mert_maszkkal_sotetul(self) -> None:
        # nagy képen a sarokpixel r-je ≈0,706 → gain ≈0,250 → 200·0,25 = 50
        image = _uniform_image(200, height=201, width=201)
        result = apply_vignette(image)
        assert abs(int(result[0, 0, 0]) - 50) <= 2

    def test_mert_pont_r045(self) -> None:
        # r=0,45 → gain 0,729 → 200·0,729 = 145,8 ≈ 146 (±1)
        image = _uniform_image(200, height=201, width=201)
        result = apply_vignette(image)
        # a (100, 100) középponttól vízszintesen r=0,45-re eső pixel: x≈190,5
        column = 190
        radius = (column + 0.5) / 201 - 0.5
        expected = 200.0 * vignette_gain(abs(radius))
        assert abs(int(result[100, column, 0]) - round(expected)) <= 1

    def test_multiplikativ_fekete_fekete_marad(self) -> None:
        image = _uniform_image(0, height=21, width=21)
        result = apply_vignette(image)
        np.testing.assert_array_equal(result, image)

    def test_nem_mutalja_a_bemenetet(self) -> None:
        image = _uniform_image(180, height=11, width=11)
        original = image.copy()
        apply_vignette(image)
        np.testing.assert_array_equal(image, original)

    def test_hibas_bemenet_value_error(self) -> None:
        with pytest.raises(ValueError):
            apply_vignette(np.zeros((4, 4), dtype=np.uint8))

    def test_erosseg_nulla_identitas(self) -> None:
        image = _uniform_image(200, height=21, width=21)
        result = apply_vignette(image, strength=0.0)
        np.testing.assert_array_equal(result, image)


class TestApplyGlow:
    # Mért középemelés sík szürkén (golden 3. kör):
    # glow=1,0.432749,2.469705 → 128→144 · glow2=1,0.65,3.0 → 128→151
    def test_glow_v1_mert_kozepemeles(self) -> None:
        image = _uniform_image(128, height=32, width=32)
        result = apply_glow(image, GLOW_V1_INTENSITY, GLOW_V1_RADIUS)
        assert abs(int(result[16, 16, 0]) - 144) <= 1

    def test_glow2_mert_kozepemeles(self) -> None:
        image = _uniform_image(128, height=32, width=32)
        result = apply_glow(image, 0.65, 3.0)
        assert abs(int(result[16, 16, 0]) - 151) <= 1

    def test_nulla_intenzitas_identitas(self) -> None:
        image = _uniform_image((30, 90, 200))
        result = apply_glow(image, 0.0, 3.0)
        np.testing.assert_array_equal(result, image)

    def test_feher_nem_lo_tul(self) -> None:
        image = _uniform_image(255)
        result = apply_glow(image, 1.0, 3.0)
        assert result.max() <= 255

    def test_vilagosit_sohasem_sotetit(self) -> None:
        # a screen-keverés monoton: ki >= be minden pixelen
        rng = np.random.default_rng(7)
        image = rng.integers(0, 256, size=(16, 16, 3), dtype=np.uint8)
        result = apply_glow(image, 0.65, 3.0)
        assert np.all(result.astype(int) >= image.astype(int))

    def test_nem_mutalja_a_bemenetet(self) -> None:
        image = _uniform_image(128)
        original = image.copy()
        apply_glow(image, 0.65, 3.0)
        np.testing.assert_array_equal(image, original)


class TestApplyRadblur:
    def test_nulla_amount_identitas(self) -> None:
        # a golden-kit radblur-ja (size=0, amount=0) mérten no-op
        rng = np.random.default_rng(3)
        image = rng.integers(0, 256, size=(20, 20, 3), dtype=np.uint8)
        result = apply_radblur(image, 0.411585, 0.611111, 0.0, 0.0)
        np.testing.assert_array_equal(result, image)

    def test_kozeppont_eles_marad(self) -> None:
        rng = np.random.default_rng(5)
        image = rng.integers(0, 256, size=(40, 40, 3), dtype=np.uint8)
        result = apply_radblur(image, 0.5, 0.5, 0.3, 0.8)
        # a megadott középpont a védett zónán belül változatlan
        np.testing.assert_array_equal(result[20, 20], image[20, 20])

    def test_szel_elmosodik(self) -> None:
        # kontrasztos sakktáblán a szélső sáv szórása csökken
        image = np.zeros((40, 40, 3), dtype=np.uint8)
        image[::2, ::2] = 255
        image[1::2, 1::2] = 255
        result = apply_radblur(image, 0.5, 0.5, 0.1, 1.0)
        edge_before = float(np.std(image[0, :, 0].astype(np.float64)))
        edge_after = float(np.std(result[0, :, 0].astype(np.float64)))
        assert edge_after < edge_before

    def test_nem_mutalja_a_bemenetet(self) -> None:
        image = _uniform_image(90, height=16, width=16)
        original = image.copy()
        apply_radblur(image, 0.5, 0.5, 0.2, 0.7)
        np.testing.assert_array_equal(image, original)


class TestApplyRadsat:
    def test_kozeppont_telitettsege_megmarad(self) -> None:
        image = _uniform_image((200, 80, 80), height=41, width=41)
        result = apply_radsat(image, 0.5, 0.5, 0.4, 1.0)
        np.testing.assert_array_equal(result[20, 20], image[20, 20])

    def test_sarok_szurkul(self) -> None:
        image = _uniform_image((200, 80, 80), height=41, width=41)
        result = apply_radsat(image, 0.5, 0.5, 0.2, 1.0)
        corner = result[0, 0]
        assert int(corner[0]) == int(corner[1]) == int(corner[2])

    def test_sarok_lumaja_megmarad(self) -> None:
        image = _uniform_image((200, 80, 80), height=41, width=41)
        result = apply_radsat(image, 0.5, 0.5, 0.2, 1.0)
        luma = 0.299 * 200 + 0.587 * 80 + 0.114 * 80
        assert abs(int(result[0, 0, 0]) - round(luma)) <= 1

    def test_nagy_sugar_identitas(self) -> None:
        image = _uniform_image((200, 80, 80), height=21, width=21)
        result = apply_radsat(image, 0.5, 0.5, 1.0, 1.0)
        np.testing.assert_array_equal(result, image)

    def test_nem_mutalja_a_bemenetet(self) -> None:
        image = _uniform_image((150, 60, 40), height=15, width=15)
        original = image.copy()
        apply_radsat(image, 0.5, 0.5, 0.3, 0.5)
        np.testing.assert_array_equal(image, original)
