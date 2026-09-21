"""#3421: a gradiens-LUT-ok indexe a PIROS csatorna, nem a luma.

A `GradientMap` építője (`0x00bb87b0`, a TwoTone-é is) és a `HSVGradientMap`
építője (`0x00bbc260`) a 256 elemű színtáblát a közös futószalag
(`0x00bcb2f0`) `+0x800` rekeszébe írja — ez a BGRA-képpont `src[2]` bájtja,
a piros —, a `+0x400` és `+0x000` rekeszt nullázza (`0x00bbc56a`–`0x00bbc588`).
A kimenet tehát CSAK a bemenet piros csatornájától függ.

A HeatMap leírója (`filterdesc.xml`) előtte `SimpleColorMatrix
Saturation="0"`-t ír, ami a mért viselkedés szerint NEM szürkít (a TwoTone
ugyanígy, #3433).
"""

from __future__ import annotations

import numpy as np

from picasapy.render import glimmer_ops as g
from picasapy.render import glimmer_tone as t


def _kep(*keppontok) -> np.ndarray:
    return np.array([list(keppontok)], dtype=np.uint8)


def test_a_gradient_map_csak_a_piros_csatornat_nezi():
    szinek = ((0, 0, 0), (255, 255, 255))
    ki = g.gradient_map(_kep((255, 0, 0), (0, 255, 255), (128, 7, 200)), szinek)
    assert tuple(int(v) for v in ki[0, 0]) == (255, 255, 255)
    assert tuple(int(v) for v in ki[0, 1]) == (0, 0, 0)
    assert tuple(int(v) for v in ki[0, 2]) == (128, 128, 128)


def test_a_hsv_gradient_map_csak_a_piros_csatornat_nezi():
    megallok = ((0.0, 240.0, 100.0, 100.0), (255.0, 0.0, 100.0, 100.0))
    ki = g.hsv_gradient_map(_kep((255, 0, 0), (0, 0, 255), (255, 255, 255)), megallok)
    # piros=255 → a felső megálló (tiszta vörös); kék (piros=0) → az alsó (kék)
    assert tuple(int(v) for v in ki[0, 0]) == (255, 0, 0)
    assert tuple(int(v) for v in ki[0, 1]) == (0, 0, 255)
    # a fehér piros csatornája is 255 → ugyanaz, mint a tiszta vörösé
    assert tuple(int(v) for v in ki[0, 2]) == tuple(int(v) for v in ki[0, 0])


def test_a_heatmap_nem_szurkit_a_gradiens_elott():
    """Egy tiszta vörös és egy tiszta kék képpont a luma szerint közel esne
    (76 vs 29), a piros csatorna szerint a skála két végére kerül."""
    ki = t.apply_heatmap(_kep((255, 0, 0), (0, 0, 255)))
    varhato_teteje = g.hsv_gradient_map(_kep((255, 0, 0)), t._HEATMAP_STOPS)[0, 0]
    varhato_alja = g.hsv_gradient_map(_kep((0, 0, 0)), t._HEATMAP_STOPS)[0, 0]
    np.testing.assert_array_equal(ki[0, 0], varhato_teteje)
    np.testing.assert_array_equal(ki[0, 1], varhato_alja)
