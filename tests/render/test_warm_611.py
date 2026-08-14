"""#611: a `warm` (Melegítés) beégetett, 256 elemű LUT-jának pixelpontos
tesztje — a jegyben dokumentált kilenc mintapont és a tábla monotonitása.

Forrás: a natív `0x0090c040` munkafüggvény és a `0x00d33b70` beégetett
tábla (`docs/specs/picasa-native-filter-workers.md` 2.8. pont).
"""

from __future__ import annotations

import numpy as np
import pytest

from picasapy.render.color import apply_warm
from picasapy.render.warmify_lut import WARMIFY_TABLE

# A jegyben dokumentált kilenc mintapont: be -> (R, G, B).
_DOKUMENTALT_PONTOK = {
    0: (0, 0, 0),
    32: (41, 29, 21),
    64: (79, 60, 44),
    96: (112, 88, 69),
    128: (139, 113, 97),
    160: (163, 138, 128),
    192: (187, 168, 162),
    224: (214, 200, 198),
    255: (242, 232, 234),
}


def _uniform_image(value: int) -> np.ndarray:
    return np.full((4, 5, 3), value, dtype=np.uint8)


class TestWarmDokumentaltPontok:
    @pytest.mark.parametrize("be,vart", sorted(_DOKUMENTALT_PONTOK.items()))
    def test_kilenc_mintapont(
        self, be: int, vart: tuple[int, int, int]
    ) -> None:
        result = apply_warm(_uniform_image(be))
        assert tuple(int(channel) for channel in result[0, 0]) == vart


class TestWarmTablaMonotonitas:
    def test_gyengen_monoton_novo_mindharom_csatornan(self) -> None:
        # A tábla 8 bites kvantálás miatt NEM szigorúan monoton (vannak
        # egyenlő szomszédos kimenetek), de sosem csökken.
        for channel in range(3):
            values = [row[channel] for row in WARMIFY_TABLE]
            assert all(
                values[i] <= values[i + 1] for i in range(len(values) - 1)
            ), f"a(z) {channel}. csatorna nem monoton"

    def test_vegpontok(self) -> None:
        assert WARMIFY_TABLE[0] == (0, 0, 0)
        assert WARMIFY_TABLE[255] == (242, 232, 234)


class TestWarmCsatornankentSajatIndex:
    def test_szines_bemenet_csatornankent_sajat_ertekevel_indexel(self) -> None:
        # A tábla NEM keresztez: minden csatorna a SAJÁT bemeneti értékével
        # indexel, nem a másik csatornáéval.
        image = np.zeros((1, 1, 3), dtype=np.uint8)
        image[0, 0] = (32, 96, 224)
        result = apply_warm(image)
        r_vart, _, _ = _DOKUMENTALT_PONTOK[32]
        _, g_vart, _ = _DOKUMENTALT_PONTOK[96]
        _, _, b_vart = _DOKUMENTALT_PONTOK[224]
        assert tuple(int(channel) for channel in result[0, 0]) == (
            r_vart,
            g_vart,
            b_vart,
        )

    def test_nem_mutalja_a_bemenetet(self) -> None:
        image = _uniform_image(100)
        original = image.copy()
        apply_warm(image)
        np.testing.assert_array_equal(image, original)
