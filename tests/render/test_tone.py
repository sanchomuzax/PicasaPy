"""A `picasapy.render.tone` tónus-műveletek tesztjei.

A négy Finomhangolás-csúszka várt értékei a #551 REFERENCIA-MÉRÉSÉBŐL
származnak (`sanchomuzax/picasapy-agent`: `referencia/deritofeny/`,
`referencia/szinhomerseklet/`, `referencia/finomhangolas/` — ugyanaz a
fotó, csúszkánként több állásban, a valódi Picasa 3.9 kimenetével).
"""

from __future__ import annotations

import numpy as np
import pytest

from picasapy.render.tone import (
    apply_color_temperature,
    apply_fill,
    fill_lut,
    apply_finetune2,
    apply_highlights,
    apply_neutral_pipette,
    apply_shadows,
    parse_neutral_argb,
)


def _uniform_image(value: int | tuple[int, int, int]) -> np.ndarray:
    return np.full((6, 8, 3), value, dtype=np.uint8)


class TestApplyFill:
    def test_nulla_erosseg_identitas(self) -> None:
        image = _uniform_image(90)
        np.testing.assert_array_equal(apply_fill(image, 0.0), image)

    @pytest.mark.parametrize(
        ("strength", "bemenet", "vart"),
        [
            # #551: a MÉRT d(világosság) görbék horgonyértékei — egyenletes
            # szürke képen a világosság maga a bemeneti szint. A #575-ös
            # natív modell ezekhez képest 2–3 egységen belül marad, miközben
            # a teljes mérőkészleten kisebb a hibája: a tűrés ezért 3, nem 1.
            (0.10, 32, 32 + 4.1),
            (0.10, 128, 128 + 5.3),
            (0.25, 32, 32 + 15.9),
            (0.25, 128, 128 + 19.1),
            (0.50, 32, 32 + 38.5),
            (0.50, 128, 128 + 39.7),
            (0.75, 128, 128 + 68.3),
            (1.00, 32, 32 + 128.8),
            (1.00, 128, 128 + 87.9),
        ],
    )
    def test_mert_gorbe_pontjai(
        self, strength: float, bemenet: int, vart: float
    ) -> None:
        image = _uniform_image(bemenet)
        result = apply_fill(image, strength)
        assert abs(int(result[0, 0, 0]) - vart) <= 3.0

    def test_a_lut_azonossag_nulla_eroseggnel(self) -> None:
        """#575: `fill = 0`-nál `g = 1`, a kitevő is 1 — a LUT azonosság."""
        np.testing.assert_array_equal(fill_lut(0.0), np.arange(256))

    def test_a_sotet_keppont_tobbet_kap_mint_a_vilagos(self) -> None:
        """#575: a natív kód a LUT-ot a világossággal FORDÍTOTTAN arányos
        súllyal keveri be — sötétben teljes hatás, világosban semmi."""
        sotet = int(apply_fill(_uniform_image(40), 0.5)[0, 0, 0]) - 40
        kozepes = int(apply_fill(_uniform_image(128), 0.5)[0, 0, 0]) - 128
        vilagos = int(apply_fill(_uniform_image(220), 0.5)[0, 0, 0]) - 220
        assert sotet > kozepes > vilagos >= 0

    def test_a_csatorna_sorrend_nem_szamit(self) -> None:
        """#575: a `luma4 = (B + 2G + R) >> 2` súly szimmetrikus az R-re és
        a B-re, ezért az RGB/BGR sorrend nem befolyásolja az eredményt."""
        rgb = apply_fill(_uniform_image((60, 90, 120)), 0.5)
        bgr = apply_fill(_uniform_image((120, 90, 60)), 0.5)
        assert int(rgb[0, 0, 0]) == int(bgr[0, 0, 2])
        assert int(rgb[0, 0, 2]) == int(bgr[0, 0, 0])

    def test_feherpont_kozel_tarto(self) -> None:
        """A mért görbe a csúcsfényeknél ~0 (max állásban −1,8): a fehér
        nem világosodik tovább."""
        result = apply_fill(_uniform_image(255), 1.0)
        assert int(result[0, 0, 0]) >= 250

    def test_kozbulso_erosseg_a_szomszedos_gorbek_koze_esik(self) -> None:
        image = _uniform_image(128)
        low = int(apply_fill(image, 0.25)[0, 0, 0])
        mid = int(apply_fill(image, 0.375)[0, 0, 0])
        high = int(apply_fill(image, 0.5)[0, 0, 0])
        assert low < mid < high

    def test_nem_mutalja_a_bemenetet(self) -> None:
        image = _uniform_image(50)
        original = image.copy()
        apply_fill(image, 0.8)
        np.testing.assert_array_equal(image, original)

    def test_hibas_bemenet_value_error(self) -> None:
        with pytest.raises(ValueError):
            apply_fill(np.zeros((4, 4), dtype=np.uint8), 0.5)


class TestApplyHighlights:
    def test_nulla_erosseg_identitas(self) -> None:
        image = _uniform_image(120)
        np.testing.assert_array_equal(apply_highlights(image, 0.0), image)

    def test_mert_meredekseg_max_allasban(self) -> None:
        """#551: h=0,48-nál a mért meredekség 1,9235; a képlet 1/(1−h)."""
        image = _uniform_image(100)
        result = apply_highlights(image, 0.48)
        assert abs(int(result[0, 0, 0]) - 100 / (1 - 0.48)) <= 1

    def test_a_parameter_048_ra_van_vagva(self) -> None:
        """A `filterdesc.xml` tartománya [0..0.48] — a fölötte lévő érték
        (idegen/sérült lánc) nem robbanthatja fel a képletet."""
        image = _uniform_image(100)
        assert np.array_equal(
            apply_highlights(image, 1.0), apply_highlights(image, 0.48)
        )

    def test_vilagosit(self) -> None:
        image = _uniform_image(100)
        result = apply_highlights(image, 0.4)
        assert int(result[0, 0, 0]) > 100


class TestApplyShadows:
    def test_nulla_erosseg_identitas(self) -> None:
        image = _uniform_image(120)
        np.testing.assert_array_equal(apply_shadows(image, 0.0), image)

    def test_mert_feketepont_max_allasban(self) -> None:
        """#551: s=0,48-nál a feketepont 255·0,48 = 122,4-re ugrik, a
        meredekség 1/(1−s)."""
        image = _uniform_image(200)
        result = apply_shadows(image, 0.48)
        assert abs(int(result[0, 0, 0]) - (200 - 255 * 0.48) / (1 - 0.48)) <= 1

    def test_sotetit_es_feherpontot_tart(self) -> None:
        image = _uniform_image(120)
        result = apply_shadows(image, 0.4)
        assert int(result[0, 0, 0]) < 120
        white = _uniform_image(255)
        assert apply_shadows(white, 0.4)[0, 0, 0] == 255


class TestApplyColorTemperature:
    def test_nulla_identitas(self) -> None:
        image = _uniform_image(128)
        np.testing.assert_array_equal(apply_color_temperature(image, 0.0), image)

    def test_hutes_mert_szorzoi(self) -> None:
        # #551, p5=−0,5: R 0,8956 · G 1,0225 · B 1,1739 (csatornánkénti
        # KONSTANS szorzás, nem eltolás)
        result = apply_color_temperature(_uniform_image(128), -0.5)
        assert abs(int(result[0, 0, 0]) - 128 * 0.8956) <= 1
        assert abs(int(result[0, 0, 1]) - 128 * 1.0225) <= 1
        assert abs(int(result[0, 0, 2]) - 128 * 1.1739) <= 1

    def test_melegites_mert_szorzoi(self) -> None:
        # #551, p5=+1,0: R 1,0546 · G 0,9974 · B 0,8430 — a melegítés
        # lényegesen gyengébb, mint a hűtés
        result = apply_color_temperature(_uniform_image(128), 1.0)
        assert abs(int(result[0, 0, 0]) - 128 * 1.0546) <= 1
        assert abs(int(result[0, 0, 2]) - 128 * 0.8430) <= 1

    def test_a_hutes_erosebb_mint_a_melegites(self) -> None:
        """#551 kulcsmegfigyelése: a két irány NEM tükörképe egymásnak."""
        hideg = apply_color_temperature(_uniform_image(128), -1.0)
        meleg = apply_color_temperature(_uniform_image(128), 1.0)
        assert int(hideg[0, 0, 2]) - 128 > 128 - int(meleg[0, 0, 2])

    def test_clip_a_hatarokon(self) -> None:
        image = _uniform_image(250)
        result = apply_color_temperature(image, -1.0)
        assert result.max() <= 255


class TestNeutralPipette:
    def test_parse_alpha_nulla_nincs_kijeloles(self) -> None:
        assert parse_neutral_argb("00000000") is None

    def test_parse_ervenyes_szin(self) -> None:
        assert parse_neutral_argb("ffccc6b2") == (204, 198, 178)

    def test_parse_ervenytelen_value_error(self) -> None:
        with pytest.raises(ValueError):
            parse_neutral_argb("nemhexa!")

    def test_meleg_szurke_kekkel_kompenzal(self) -> None:
        # mérve: ffccc6b2 (meleg-szürke) kijelölésekor ΔB pozitív, ΔR negatív
        image = _uniform_image(128)
        result = apply_neutral_pipette(image, (204, 198, 178))
        assert int(result[0, 0, 2]) > 128
        assert int(result[0, 0, 0]) < 128

    def test_szurke_pipetta_identitas(self) -> None:
        image = _uniform_image(77)
        result = apply_neutral_pipette(image, (200, 200, 200))
        np.testing.assert_array_equal(result, image)

    @pytest.mark.parametrize(
        ("p4", "vart_r", "vart_b"),
        [
            # #551: a Picasa maga írta ki ezeket a p4-eket a .picasa.ini-be
            # (referencia/szinpalca-proba2/); a szorzók a ZÖLDRE normálva
            ((107, 128, 136), 128 / 107, 128 / 136),
            ((132, 128, 128), 128 / 132, 1.0),
            ((93, 128, 120), 128 / 93, 128 / 120),
        ],
    )
    def test_a_szorzok_a_zoldhoz_viszonyitanak(
        self, p4: tuple[int, int, int], vart_r: float, vart_b: float
    ) -> None:
        image = _uniform_image(100)
        result = apply_neutral_pipette(image, p4)
        assert abs(int(result[0, 0, 0]) - 100 * vart_r) <= 1.0
        assert int(result[0, 0, 1]) == 100  # a zöld a viszonyítási alap
        assert abs(int(result[0, 0, 2]) - 100 * vart_b) <= 1.0


class TestApplyFinetune2:
    def test_minden_parameter_semleges_identitas(self) -> None:
        image = _uniform_image(140)
        result = apply_finetune2(
            image, fill=0.0, highlights=0.0, shadows=0.0, neutral=None, temperature=0.0
        )
        np.testing.assert_array_equal(result, image)

    def test_fill_p1_azonos_az_onallo_fill_szurovel(self) -> None:
        # mérve: a finetune2 p1 LUT-ja bitre azonos az önálló fill-ével
        image = _uniform_image(64)
        via_finetune = apply_finetune2(
            image, fill=0.5, highlights=0.0, shadows=0.0, neutral=None, temperature=0.0
        )
        np.testing.assert_array_equal(via_finetune, apply_fill(image, 0.5))

    def test_nem_mutalja_a_bemenetet(self) -> None:
        image = _uniform_image(90)
        original = image.copy()
        apply_finetune2(
            image, fill=0.3, highlights=0.1, shadows=0.2, neutral=None, temperature=0.5
        )
        np.testing.assert_array_equal(image, original)
