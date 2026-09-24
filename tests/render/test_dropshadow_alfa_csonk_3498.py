"""#3498: a DropShadow árnyék-téglalapjának alfája CSONKOLVA számolódik.

Az eredeti rajzoló (`0x00bcda34`–`0x00bcda96`) a rekord float32 alfáját
(`+0x0c`, `clamp(shadowAlpha, 0, 1)`) 255-tel szorozza, majd a `fistp` ELŐTT
a kerekítési módot NULLA FELÉ állítja (`or 0xc00`) — az alfa-bájt tehát
`TRUNC(float32(a) · 255)`, nem `ROUND(a · 255)`. A 101 egész Fade-értékből
48-nál a kerekítés 1-gyel nagyobb alfát adott.
"""

from __future__ import annotations

import numpy as np
import pytest

from picasapy.render.glimmer_frame_ops import compose_drop_shadow, teglalap_alfa
from picasapy.render.glimmer_ops import fade_alpha


@pytest.mark.parametrize(
    "fade,vart",
    [(2, 249), (50, 127), (99, 2), (0, 255), (30, 178), (100, 0)],
)
def test_a_fade_ertekek_alfaja(fade, vart):
    assert teglalap_alfa(fade_alpha(fade)) == vart


def test_a_polaroid_rogzitett_alfaja():
    assert teglalap_alfa(0.4) == 102


def test_a_hatarokon_kivul_vagva():
    assert teglalap_alfa(-0.5) == 0
    assert teglalap_alfa(1.5) == 255


def test_a_kesz_kepen_is_a_csonkolt_alfa_latszik():
    """Fekete árnyék fehér háttéren: a képpont `255 − α`. Nagy eltolással a
    téglalap közepe szabadon látszik, az elmosás széle messze van."""
    kep = np.full((80, 80, 3), 128, dtype=np.uint8)
    ki = compose_drop_shadow(
        kep, (0, 0, 0), (255, 255, 255), distance_px=60, angle=0.0,
        blur_px=1.0, margin=70, fade=50.0,
    )
    alfa = 255 - ki[..., 0].astype(int)
    assert alfa.max() == 127
