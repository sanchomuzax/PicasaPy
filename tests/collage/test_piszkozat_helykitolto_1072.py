"""A piszkozat helykitöltő képe (#1072).

A tulajdonos jelentése: *„A friss képkollázs piszkozat mentése nem jelenik
meg a PicasaPy és Picasa alatt sem."*

Az eredeti a piszkozat mentésekor **azonnal** ír egy képet a `.cxf` mellé —
ettől látszik az albumban. A tulajdonos képernyőképe adta a méreteket:
`640 × 453`, vagyis **640 a hosszabb élen, a lap arányával**.

⚠️ **Három teszt, nem tizenöt.** A tulajdonos kifejezett kérése
(2026-08-20): *„a teszt ne legyen túlgondolva, túlpörgetve"*. A mérce: a
javítás nélkül bukjon el, és azt állítsa, amit a felhasználó lát.
"""

from __future__ import annotations

import numpy as np
import pytest

from picasapy.collage.draft_placeholder import (
    PLACEHOLDER_LONG_EDGE,
    draw_draft_label,
    placeholder_size,
)


class TestAMeret:
    """A mért érték: 640 a HOSSZABB élen, a lap arányával."""

    @pytest.mark.parametrize(
        ("arany", "vart"),
        [
            (453 / 640, (640, 453)),   # a tulajdonos A4 fekvő lapja
            (0.75, (640, 480)),        # 4:3 fekvő
            (1.5, (427, 640)),         # álló: a MAGASSÁG a korlát
        ],
    )
    def test_a_hosszabb_el_640(self, arany, vart):
        assert placeholder_size(arany) == vart

    def test_a_hosszabb_el_SOHA_nem_nagyobb(self):
        """Bármilyen arány mellett — ez a lényeg, nem a konkrét számok."""
        for arany in (0.1, 0.5, 1.0, 2.0, 9.9):
            szeles, magas = placeholder_size(arany)
            assert max(szeles, magas) == PLACEHOLDER_LONG_EDGE


class TestAFelirat:
    """A „PISZKOZAT" a KÉPBE van rajzolva — ez a felismerhető eleme."""

    def test_a_felirat_belekerul_a_kepbe(self):
        alap = np.zeros((453, 640, 3), dtype=np.uint8)

        eredmeny = draw_draft_label(alap, "PISZKOZAT")

        assert eredmeny.shape == alap.shape
        assert int(np.count_nonzero(eredmeny)) > 0, "a felirat nem rajzolódott ki"

    def test_a_felirat_a_KOZEPEN_all(self):
        """A képernyőkép szerint a felirat a kép közepén áll, nem a szélén."""
        alap = np.zeros((453, 640, 3), dtype=np.uint8)

        eredmeny = draw_draft_label(alap, "PISZKOZAT")

        ys, xs = np.nonzero(eredmeny.max(axis=2))
        assert abs((ys.min() + ys.max()) / 2 - 453 / 2) < 30
        assert abs((xs.min() + xs.max()) / 2 - 640 / 2) < 30
