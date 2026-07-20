"""A `picasapy.render.tinting` színező effektek tesztjei.

Mért pont (golden 3. kör): `tint=1,79.842102,ffff` szürke rámpán az
R-csatornát nullázza, G és B változatlan (a `ffff` szín = 0000ffff → cián).
Az `ansel` semleges (R=G=B) kimenetet ad enyhe középemeléssel; a pontos
tónusgörbe nyitott — a görbe itt dokumentált közelítés. A `dir_tint`
térbeli modellje szintén közelítés (nincs mért maszk).
"""

from __future__ import annotations

import numpy as np
import pytest

from picasapy.render.tinting import (
    apply_ansel,
    apply_dir_tint,
    apply_tint,
    parse_rgb_hex,
)


def _uniform_image(
    value: int | tuple[int, int, int], height: int = 6, width: int = 8
) -> np.ndarray:
    return np.full((height, width, 3), value, dtype=np.uint8)


class TestParseRgbHex:
    def test_teljes_nyolcjegyu(self) -> None:
        assert parse_rgb_hex("ffccc6b2") == (0xCC, 0xC6, 0xB2)

    def test_rovid_alak_balra_nullaval_toltodik(self) -> None:
        # a Picasa a vezető nullákat elhagyja: "ffff" = 0000ffff → cián
        assert parse_rgb_hex("ffff") == (0x00, 0xFF, 0xFF)

    def test_ures_vagy_hibas_value_error(self) -> None:
        with pytest.raises(ValueError):
            parse_rgb_hex("")
        with pytest.raises(ValueError):
            parse_rgb_hex("xyz")
        with pytest.raises(ValueError):
            parse_rgb_hex("123456789")


class TestApplyTint:
    def test_mert_pont_cian_szurke_ramppan(self) -> None:
        # golden: tint=1,79.842102,ffff szürkén → R=0, G és B változatlan
        image = _uniform_image(128)
        result = apply_tint(image, preserve=79.842102, color=(0x00, 0xFF, 0xFF))
        assert int(result[0, 0, 0]) == 0
        assert abs(int(result[0, 0, 1]) - 128) <= 1
        assert abs(int(result[0, 0, 2]) - 128) <= 1

    def test_feher_szin_luma_lesz(self) -> None:
        image = _uniform_image((100, 150, 200))
        result = apply_tint(image, preserve=0.0, color=(0xFF, 0xFF, 0xFF))
        luma = round(0.299 * 100 + 0.587 * 150 + 0.114 * 200)
        assert abs(int(result[0, 0, 0]) - luma) <= 1
        assert result[0, 0, 0] == result[0, 0, 1] == result[0, 0, 2]

    def test_szurke_bemeneten_preserve_erteke_kozombos(self) -> None:
        # szürkén nincs megőrizhető króma → a preserve nem változtat
        image = _uniform_image(90)
        low = apply_tint(image, preserve=0.0, color=(0x00, 0xFF, 0xFF))
        high = apply_tint(image, preserve=100.0, color=(0x00, 0xFF, 0xFF))
        np.testing.assert_array_equal(low, high)

    def test_nem_mutalja_a_bemenetet(self) -> None:
        image = _uniform_image((10, 200, 30))
        original = image.copy()
        apply_tint(image, preserve=50.0, color=(0xFF, 0x00, 0x00))
        np.testing.assert_array_equal(image, original)

    def test_hibas_bemenet_value_error(self) -> None:
        with pytest.raises(ValueError):
            apply_tint(np.zeros((4, 4), dtype=np.uint8), 0.0, (255, 255, 255))


class TestApplyAnsel:
    def test_semleges_kimenet_feher_szinnel(self) -> None:
        # golden 3. kör: ansel=1,ffffffff kimenete semleges (R=G=B)
        image = _uniform_image((100, 150, 200))
        result = apply_ansel(image, color=(0xFF, 0xFF, 0xFF))
        assert result[0, 0, 0] == result[0, 0, 1] == result[0, 0, 2]

    def test_enyhe_kozepemeles(self) -> None:
        # mért jelleg: enyhe középemelés — a pontos görbe közelítés
        image = _uniform_image(128)
        result = apply_ansel(image, color=(0xFF, 0xFF, 0xFF))
        mid = int(result[0, 0, 0])
        assert 128 < mid <= 150

    def test_vegpontok_helyben_maradnak(self) -> None:
        black = apply_ansel(_uniform_image(0), color=(0xFF, 0xFF, 0xFF))
        white = apply_ansel(_uniform_image(255), color=(0xFF, 0xFF, 0xFF))
        assert int(black[0, 0, 0]) == 0
        assert int(white[0, 0, 0]) == 255

    def test_szines_ansel_szinez(self) -> None:
        image = _uniform_image(128)
        result = apply_ansel(image, color=(0xFF, 0xCC, 0x99))
        assert int(result[0, 0, 0]) > int(result[0, 0, 1]) > int(result[0, 0, 2])

    def test_nem_mutalja_a_bemenetet(self) -> None:
        image = _uniform_image((90, 20, 250))
        original = image.copy()
        apply_ansel(image, color=(0xFF, 0xFF, 0xFF))
        np.testing.assert_array_equal(image, original)


class TestApplyDirTint:
    def test_also_fel_valtozatlan(self) -> None:
        # a színátmenet a megadott y alatt kifut → az alsó szél érintetlen
        image = _uniform_image(100, height=40, width=20)
        result = apply_dir_tint(
            image, x=0.5, y=0.5, gradient=0.25, shade=0.5, color=(0xFF, 0xFF, 0xFF)
        )
        np.testing.assert_array_equal(result[-1], image[-1])

    def test_felso_sav_a_szin_fele_kevert(self) -> None:
        image = _uniform_image(100, height=40, width=20)
        result = apply_dir_tint(
            image, x=0.5, y=0.5, gradient=0.25, shade=0.5, color=(0xFF, 0xFF, 0xFF)
        )
        # a felső szélen a keverés teljes súlyú: 100 + 0,5·(255−100) = 177,5
        assert abs(int(result[0, 0, 0]) - 178) <= 1

    def test_nulla_shade_identitas(self) -> None:
        image = _uniform_image((80, 120, 160), height=20, width=10)
        result = apply_dir_tint(
            image, x=0.5, y=0.5, gradient=0.25, shade=0.0, color=(0x00, 0x00, 0xFF)
        )
        np.testing.assert_array_equal(result, image)

    def test_atmenet_monoton(self) -> None:
        image = _uniform_image(100, height=41, width=11)
        result = apply_dir_tint(
            image, x=0.5, y=0.5, gradient=0.5, shade=1.0, color=(0xFF, 0xFF, 0xFF)
        )
        column = result[:, 5, 0].astype(int)
        assert all(a >= b for a, b in zip(column, column[1:]))

    def test_nem_mutalja_a_bemenetet(self) -> None:
        image = _uniform_image(60, height=16, width=8)
        original = image.copy()
        apply_dir_tint(
            image, x=0.5, y=0.5, gradient=0.3, shade=0.7, color=(0xFF, 0x00, 0x00)
        )
        np.testing.assert_array_equal(image, original)
