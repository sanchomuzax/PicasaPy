"""A `picasapy.render.effects_artistic` (a Picasa 5. fülének, kék ecsetnek,
MÉRETTARTÓ effektjei) tesztjei.

**ŐSZINTESÉG:** nincs golden-mérés ezekhez az effektekhez (#330) — a
tesztek a MEGFIGYELHETŐ kimenetet ellenőrzik (blokkosítás, méret-
tartás, monoton viselkedés stb.), NEM azt, hogy a kimenet pixelhűen
egyezik a Picasáéval (arra nincs referencia-adat, ld. #317).
"""

from __future__ import annotations

import numpy as np
import pytest

from picasapy.render.effects_artistic import (
    apply_boost,
    apply_comicize,
    apply_focal_zoom,
    apply_neon,
    apply_pencil_sketch,
    apply_pixelate,
    apply_soften,
)


def _uniform_image(
    value: int | tuple[int, int, int], height: int = 20, width: int = 24
) -> np.ndarray:
    return np.full((height, width, 3), value, dtype=np.uint8)


def _checkerboard(height: int = 40, width: int = 40) -> np.ndarray:
    image = np.zeros((height, width, 3), dtype=np.uint8)
    image[::2, ::2] = 255
    image[1::2, 1::2] = 255
    return image


def _block_checkerboard(height: int = 40, width: int = 40, block: int = 5) -> np.ndarray:
    """Kockás minta BLOKKOKKAL (nem egypixeles), hogy a Canny-éldetektálás
    (Neon, Comicize) valódi, nem alul-mintavételezett éleket találjon."""
    image = np.zeros((height, width, 3), dtype=np.uint8)
    for block_y in range(0, height, block * 2):
        for block_x in range(0, width, block * 2):
            image[block_y : block_y + block, block_x : block_x + block] = 255
            image[block_y + block : block_y + 2 * block, block_x + block : block_x + 2 * block] = (
                255
            )
    return image


def _random_image(height: int = 24, width: int = 24, seed: int = 0) -> np.ndarray:
    rng = np.random.default_rng(seed)
    return rng.integers(0, 256, size=(height, width, 3), dtype=np.uint8)


class TestApplyBoost:
    def test_erosseg_nulla_identitas(self) -> None:
        image = _random_image()
        result = apply_boost(image, strength=0.0)
        np.testing.assert_array_equal(result, image)

    def test_szurke_kepen_a_kontraszt_no(self) -> None:
        # kontrasztos szürke gradiens: a 128 alatti pontok sötétebbek,
        # a 128 fölöttiek világosabbak legyenek a boost után
        image = np.zeros((10, 10, 3), dtype=np.uint8)
        image[:, :5] = 80
        image[:, 5:] = 200
        result = apply_boost(image, strength=80.0)
        assert int(result[0, 0, 0]) < 80
        assert int(result[0, 9, 0]) > 200

    def test_alak_es_dtype_megmarad(self) -> None:
        image = _random_image()
        result = apply_boost(image)
        assert result.shape == image.shape
        assert result.dtype == np.uint8

    def test_nem_mutalja_a_bemenetet(self) -> None:
        image = _random_image()
        original = image.copy()
        apply_boost(image, strength=70.0)
        np.testing.assert_array_equal(image, original)

    def test_negativ_erosseg_value_error(self) -> None:
        with pytest.raises(ValueError):
            apply_boost(_random_image(), strength=-1.0)

    def test_fekete_feher_szelso_bemenet_nem_dob(self) -> None:
        apply_boost(_uniform_image(0))
        apply_boost(_uniform_image(255))


class TestApplySoften:
    def test_erosseg_nulla_identitas(self) -> None:
        image = _checkerboard()
        result = apply_soften(image, amount=0.0)
        np.testing.assert_array_equal(result, image)

    def test_kontrasztos_mintan_a_szoras_csokken(self) -> None:
        image = _checkerboard()
        result = apply_soften(image, amount=100.0, radius=80.0)
        before = float(np.std(image[..., 0].astype(np.float64)))
        after = float(np.std(result[..., 0].astype(np.float64)))
        assert after < before

    def test_reszletek_megmaradnak_alacsony_erossegnel(self) -> None:
        # alacsony amount-nál a lágyítás csak részleges keverés — a kimenet
        # nem lehet azonos a teljesen elmosott (erős) verzióval
        image = _checkerboard()
        weak = apply_soften(image, amount=10.0, radius=80.0)
        strong = apply_soften(image, amount=100.0, radius=80.0)
        assert not np.array_equal(weak, strong)

    def test_nem_mutalja_a_bemenetet(self) -> None:
        image = _checkerboard()
        original = image.copy()
        apply_soften(image, amount=50.0, radius=50.0)
        np.testing.assert_array_equal(image, original)

    def test_negativ_parameter_value_error(self) -> None:
        with pytest.raises(ValueError):
            apply_soften(_random_image(), amount=-1.0)
        with pytest.raises(ValueError):
            apply_soften(_random_image(), radius=-1.0)

    def test_fekete_feher_szelso_bemenet_nem_dob(self) -> None:
        apply_soften(_uniform_image(0))
        apply_soften(_uniform_image(255))


class TestApplyPixelate:
    def test_blokkon_belul_azonos_pixelek(self) -> None:
        image = _random_image(height=40, width=40, seed=3)
        result = apply_pixelate(image, block_size=25.0)
        # a rövidebb oldal (40) 25%-a = 10 px blokk: a (0,0)-(9,9) blokk
        # minden pixele azonosnak kell legyen
        block = result[0:10, 0:10]
        assert np.all(block == block[0, 0])

    def test_blokkmeret_nulla_identitas(self) -> None:
        image = _random_image()
        result = apply_pixelate(image, block_size=0.0)
        np.testing.assert_array_equal(result, image)

    def test_alak_es_dtype_megmarad(self) -> None:
        image = _random_image(height=33, width=27, seed=4)
        result = apply_pixelate(image, block_size=15.0)
        assert result.shape == image.shape
        assert result.dtype == np.uint8

    def test_nem_mutalja_a_bemenetet(self) -> None:
        image = _random_image()
        original = image.copy()
        apply_pixelate(image, block_size=20.0)
        np.testing.assert_array_equal(image, original)

    def test_negativ_blokkmeret_value_error(self) -> None:
        with pytest.raises(ValueError):
            apply_pixelate(_random_image(), block_size=-1.0)

    def test_fekete_feher_szelso_bemenet_nem_dob(self) -> None:
        apply_pixelate(_uniform_image(0))
        apply_pixelate(_uniform_image(255))


class TestApplyFocalZoom:
    def test_kozeppont_eles_marad(self) -> None:
        image = _random_image(height=40, width=40, seed=5)
        result = apply_focal_zoom(image, x=0.5, y=0.5, radius=30.0, strength=100.0)
        np.testing.assert_array_equal(result[20, 20], image[20, 20])

    def test_szel_elmosodik(self) -> None:
        image = _checkerboard()
        result = apply_focal_zoom(image, x=0.5, y=0.5, radius=5.0, strength=100.0)
        corner_before = float(np.std(image[0:4, 0:4, 0].astype(np.float64)))
        corner_after = float(np.std(result[0:4, 0:4, 0].astype(np.float64)))
        assert corner_after < corner_before

    def test_erosseg_nulla_identitas(self) -> None:
        image = _checkerboard()
        result = apply_focal_zoom(image, strength=0.0)
        np.testing.assert_array_equal(result, image)

    def test_alak_es_dtype_megmarad(self) -> None:
        image = _random_image(height=30, width=36, seed=6)
        result = apply_focal_zoom(image)
        assert result.shape == image.shape
        assert result.dtype == np.uint8

    def test_nem_mutalja_a_bemenetet(self) -> None:
        image = _checkerboard()
        original = image.copy()
        apply_focal_zoom(image, strength=80.0)
        np.testing.assert_array_equal(image, original)

    def test_ervenytelen_fokuszpont_value_error(self) -> None:
        with pytest.raises(ValueError):
            apply_focal_zoom(_random_image(), x=1.5)
        with pytest.raises(ValueError):
            apply_focal_zoom(_random_image(), y=-0.1)

    def test_negativ_parameter_value_error(self) -> None:
        with pytest.raises(ValueError):
            apply_focal_zoom(_random_image(), radius=-1.0)
        with pytest.raises(ValueError):
            apply_focal_zoom(_random_image(), strength=-1.0)

    def test_fekete_feher_szelso_bemenet_nem_dob(self) -> None:
        apply_focal_zoom(_uniform_image(0))
        apply_focal_zoom(_uniform_image(255))


class TestApplyPencilSketch:
    def test_alapertelmezesnel_szurke_marad(self) -> None:
        # color_mix=0 alapértéknél R=G=B mindenütt (tiszta szürkeárnyalat)
        image = _random_image(height=16, width=16, seed=7)
        result = apply_pencil_sketch(image)
        np.testing.assert_array_equal(result[..., 0], result[..., 1])
        np.testing.assert_array_equal(result[..., 1], result[..., 2])

    def test_tulnyomoan_vilagos_es_alacsony_telitettsegu(self) -> None:
        image = _random_image(height=32, width=32, seed=8)
        result = apply_pencil_sketch(image)
        assert float(result.mean()) > 150.0
        saturation = result.astype(np.int16).max(axis=-1) - result.astype(np.int16).min(axis=-1)
        assert float(saturation.mean()) < 10.0

    def test_szinkeveres_visszahozza_a_szint(self) -> None:
        image = _random_image(height=16, width=16, seed=9)
        pure_gray = apply_pencil_sketch(image, color_mix=0.0)
        colored = apply_pencil_sketch(image, color_mix=100.0)
        assert not np.array_equal(pure_gray, colored)

    def test_alak_es_dtype_megmarad(self) -> None:
        image = _random_image(height=18, width=22, seed=10)
        result = apply_pencil_sketch(image)
        assert result.shape == image.shape
        assert result.dtype == np.uint8

    def test_nem_mutalja_a_bemenetet(self) -> None:
        image = _random_image(height=16, width=16, seed=11)
        original = image.copy()
        apply_pencil_sketch(image)
        np.testing.assert_array_equal(image, original)

    def test_negativ_parameter_value_error(self) -> None:
        with pytest.raises(ValueError):
            apply_pencil_sketch(_random_image(), blur_radius=-1.0)
        with pytest.raises(ValueError):
            apply_pencil_sketch(_random_image(), brightness=-1.0)
        with pytest.raises(ValueError):
            apply_pencil_sketch(_random_image(), color_mix=-1.0)

    def test_fekete_feher_szelso_bemenet_nem_dob(self) -> None:
        apply_pencil_sketch(_uniform_image(0))
        apply_pencil_sketch(_uniform_image(255))


class TestApplyNeon:
    def test_sik_kepen_szinte_fekete(self) -> None:
        image = _uniform_image(128, height=20, width=20)
        result = apply_neon(image)
        assert int(result.max()) <= 5

    def test_elekkel_szinesen_izzik(self) -> None:
        image = _block_checkerboard()
        result = apply_neon(image, intensity=100.0, color=(0, 255, 0))
        # az élgazdag képen kell legyen zöld dominanciájú, nem fekete pixel
        assert int(result[..., 1].max()) > 50

    def test_alak_es_dtype_megmarad(self) -> None:
        image = _checkerboard()
        result = apply_neon(image)
        assert result.shape == image.shape
        assert result.dtype == np.uint8

    def test_nem_mutalja_a_bemenetet(self) -> None:
        image = _checkerboard()
        original = image.copy()
        apply_neon(image)
        np.testing.assert_array_equal(image, original)

    def test_negativ_intenzitas_value_error(self) -> None:
        with pytest.raises(ValueError):
            apply_neon(_random_image(), intensity=-1.0)

    def test_hibas_szin_value_error(self) -> None:
        with pytest.raises(ValueError):
            apply_neon(_random_image(), color=(1, 2))  # type: ignore[arg-type]

    def test_fekete_feher_szelso_bemenet_nem_dob(self) -> None:
        apply_neon(_uniform_image(0))
        apply_neon(_uniform_image(255))


class TestApplyComicize:
    def test_szinszam_csokken(self) -> None:
        image = _random_image(height=32, width=32, seed=12)
        result = apply_comicize(image, posterize=90.0)
        unique_before = len(np.unique(image.reshape(-1, 3), axis=0))
        unique_after = len(np.unique(result.reshape(-1, 3), axis=0))
        assert unique_after < unique_before

    def test_kontrasztos_elen_fekete_kontur_jelenik_meg(self) -> None:
        image = _checkerboard()
        result = apply_comicize(image, edge_strength=100.0, smoothness=0.0)
        has_black = np.any(np.all(result == 0, axis=-1))
        assert has_black

    def test_alak_es_dtype_megmarad(self) -> None:
        image = _random_image(height=24, width=28, seed=13)
        result = apply_comicize(image)
        assert result.shape == image.shape
        assert result.dtype == np.uint8

    def test_nem_mutalja_a_bemenetet(self) -> None:
        image = _checkerboard()
        original = image.copy()
        apply_comicize(image)
        np.testing.assert_array_equal(image, original)

    def test_negativ_parameter_value_error(self) -> None:
        with pytest.raises(ValueError):
            apply_comicize(_random_image(), edge_strength=-1.0)
        with pytest.raises(ValueError):
            apply_comicize(_random_image(), posterize=-1.0)
        with pytest.raises(ValueError):
            apply_comicize(_random_image(), smoothness=-1.0)

    def test_fekete_feher_szelso_bemenet_nem_dob(self) -> None:
        apply_comicize(_uniform_image(0))
        apply_comicize(_uniform_image(255))
