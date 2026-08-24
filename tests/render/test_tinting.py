"""A `picasapy.render.tinting` színező effektek tesztjei.

A `tint` tesztjei a binárisból megerősített hatlépéses receptet rögzítik
(#872): szinthúzás, egész telítetlenítés, gamma-LUT és `mx`-normalizált
szorzás. Az `ansel` semleges (R=G=B) kimenetet ad mért tónusgörbével; a
`dir_tint` térbeli modellje továbbra is közelítés (nincs mért maszk).
"""

from __future__ import annotations

import numpy as np
import pytest

from picasapy.render.ops import apply_channel_levels_stretch
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


def _full_range_image(value: int | tuple[int, int, int]) -> np.ndarray:
    """Tesztkép, amelyen a megelőző szinthúzás bájtra azonosság.

    A 20×20 képen a natív 0,5%-os küszöb két pixel. A két fekete és két
    fehér őrpont az elemzési ablakon belül van, így minden csatorna
    vágópontja pontosan 0/255 marad.
    """
    image = _uniform_image(value, height=20, width=20)
    image[1, 0:2] = 0
    image[2, 0:2] = 255
    return image


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
    def test_a_nyolcnal_hosszabb_mezo_az_elso_nyolcra_vagodik(self) -> None:
        # #1142: az eredeti beolvasó az ELSŐ 8 jegyet veszi — ez korábban
        # kivételt dobott, amitől a lánc egész tagja elesett
        assert parse_rgb_hex("123456789") == parse_rgb_hex("12345678")


class TestApplyTint:
    def test_eloszor_030_as_nem_careful_szinthuzas_fut(self) -> None:
        ramp = np.linspace(100, 130, 64, dtype=np.uint8)
        image = np.tile(ramp[np.newaxis, :, np.newaxis], (64, 1, 3))

        result = apply_tint(image, preserve=256.0, color=(128, 128, 128))
        expected = apply_channel_levels_stretch(image, blend=0.30, careful=False)

        np.testing.assert_array_equal(result, expected)
        assert int(result.max()) - int(result.min()) > 240

    def test_preserve_127_es_255_kulonbozo_kimenetet_ad(self) -> None:
        image = _full_range_image((17, 113, 241))

        middle = apply_tint(image, preserve=127.0, color=(255, 128, 64))
        maximum = apply_tint(image, preserve=255.0, color=(255, 128, 64))

        assert not np.array_equal(middle, maximum)

    def test_preserve_egeszre_csonkolodik(self) -> None:
        image = _full_range_image((0, 255, 0))

        low_fraction = apply_tint(image, preserve=79.1, color=(255, 128, 64))
        high_fraction = apply_tint(image, preserve=79.9, color=(255, 128, 64))

        np.testing.assert_array_equal(low_fraction, high_fraction)

    def test_preserve_elobb_float32_dword_majd_csonkolodik(self) -> None:
        image = _full_range_image((0, 5, 65))

        near_boundary = apply_tint(
            image, preserve=79.999999, color=(128, 128, 128)
        )
        at_80 = apply_tint(image, preserve=80.0, color=(128, 128, 128))
        at_79 = apply_tint(image, preserve=79.0, color=(128, 128, 128))

        # A natív paraméter dword: 79,999999 float32-ként már 80,0.
        np.testing.assert_array_equal(near_boundary, at_80)
        assert not np.array_equal(near_boundary, at_79)

    def test_negativ_egeszhatarnal_is_float32_utan_csonkol(self) -> None:
        image = _full_range_image((0, 1, 13))

        near_boundary = apply_tint(
            image, preserve=-0.99999999, color=(128, 128, 128)
        )
        at_minus_one = apply_tint(
            image, preserve=-1.0, color=(128, 128, 128)
        )
        at_zero = apply_tint(image, preserve=0.0, color=(128, 128, 128))

        # A natív dword -0,99999999-et -1,0-ra kerekíti a csonkítás előtt.
        np.testing.assert_array_equal(near_boundary, at_minus_one)
        assert not np.array_equal(near_boundary, at_zero)

    def test_preserve_minusz_egy_a_257_es_sulyt_hasznalja(self) -> None:
        image = _full_range_image((0, 1, 13))

        result = apply_tint(image, preserve=-1.0, color=(128, 128, 128))

        # Y=2; w=257 → [2,2,1]. A negatív különbség aritmetikai jobbra
        # tolása miatt az eredmény egy szinttel eltérhet a tiszta szürkétől.
        np.testing.assert_array_equal(result[5, 5], np.array([2, 2, 1]))

    def test_fekete_tint_biztonsagosan_fekete_kimenetet_ad(self) -> None:
        image = _full_range_image((17, 113, 241))

        result = apply_tint(image, preserve=127.0, color=(0, 0, 0))

        np.testing.assert_array_equal(result, np.zeros_like(image))

    def test_preserve_256_es_szurke_szin_mellett_a_kroma_erintetlen(self) -> None:
        image = _full_range_image((17, 113, 241))

        result = apply_tint(image, preserve=256.0, color=(128, 128, 128))

        np.testing.assert_array_equal(result, image)

    def test_szurke_szinnel_k_egy_es_egesz_luma_marad(self) -> None:
        image = _full_range_image((100, 150, 200))

        result = apply_tint(image, preserve=0.0, color=(128, 128, 128))

        # (77*100 + 151*150 + 28*200) >> 8 = 140. A szürke tintnél
        # k=1, ezért nincs gamma; az mx-normalizálás a 128-at egységre hozza.
        np.testing.assert_array_equal(result[5, 5], np.array([140, 140, 140]))

    def test_telitett_szin_gamma_lutja_vilagosit(self) -> None:
        image = _full_range_image(64)

        result = apply_tint(image, preserve=0.0, color=(255, 128, 64))

        # k=1,3557047; LUT[64]=92; mx=255 → skála=257.
        np.testing.assert_array_equal(result[5, 5], np.array([91, 46, 23]))

    def test_a_sorrend_telitetlenites_gamma_majd_mx_szorzasa(self) -> None:
        image = _full_range_image((17, 113, 241))

        result = apply_tint(image, preserve=127.0, color=(255, 128, 64))

        # Y=98; w=129 → [57,105,168]; gamma → [84,133,187];
        # az mx-normalizált szorzás végeredménye [83,66,46].
        np.testing.assert_array_equal(result[5, 5], np.array([83, 66, 46]))

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

    def test_vegpontok_kozel_helyben_maradnak(self) -> None:
        """#317: a mért görbe a feketét pontosan tartja, a fehéret viszont
        épphogy visszafogja (254) — a `referencia/filteredbw/` exportján a
        kvázi-fehér bemenet átlagosan 251,4-re jön ki, tehát ez a
        Picasa valódi viselkedése, nem a modellünk pontatlansága."""
        black = apply_ansel(_uniform_image(0), color=(0xFF, 0xFF, 0xFF))
        white = apply_ansel(_uniform_image(255), color=(0xFF, 0xFF, 0xFF))
        assert int(black[0, 0, 0]) == 0
        assert 250 <= int(white[0, 0, 0]) <= 255

    def test_a_szin_szuro_nem_festek(self) -> None:
        """#317: a Filtered B&W színe fényképészeti SZŰRŐ — a kimenet
        semleges marad, a szín csak azt dönti el, melyik csatorna számít
        bele a szürkébe (a Picasa palettája sárga/narancs/vörös/zöld
        szűrőkből áll, ld. `referencia/filteredbw/panel-screenshot-2.png`).
        """
        red_patch = _uniform_image((200, 40, 40))
        through_red = apply_ansel(red_patch, color=(0xFF, 0x00, 0x00))
        through_blue = apply_ansel(red_patch, color=(0x00, 0x00, 0xFF))

        for result in (through_red, through_blue):
            pixel = result[0, 0]
            assert int(pixel[0]) == int(pixel[1]) == int(pixel[2]), (
                "a Filtered B&W kimenete nem lehet színes"
            )
        # vörös szűrőn át a vörös folt VILÁGOS, kék szűrőn át sötét
        assert int(through_red[0, 0, 0]) > int(through_blue[0, 0, 0]) + 100

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
        # szomszédos-pár (pairwise) összehasonlítás — szándékosan eggyel
        # rövidebb a második sorozat.
        assert all(a >= b for a, b in zip(column, column[1:], strict=False))

    def test_nem_mutalja_a_bemenetet(self) -> None:
        image = _uniform_image(60, height=16, width=8)
        original = image.copy()
        apply_dir_tint(
            image, x=0.5, y=0.5, gradient=0.3, shade=0.7, color=(0xFF, 0x00, 0x00)
        )
        np.testing.assert_array_equal(image, original)
