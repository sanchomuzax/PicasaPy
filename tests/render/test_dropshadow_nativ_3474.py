"""#3474: a `DropShadow` a natív elmosással és egész keveréssel kompozitál.

A natív út (`0x00bcd940`): az árnyékréteg alfája a téglalapon
`ROUND(shadowAlpha · 255)`, az elmosás a `quality=3` hatmenetes egész út
(`render/nativ_blur.py`, emulátorral bitre igazolva), a keverés
`(S·α + D·(255 − α)) // 255` (`0x008f48b0`, emulátorral igazolva).

Mérve a tulajdonos 684-es golden-exportjain (`EXIF Software = Picasa`),
átlagos ΔE a Picasa-exporttól: `alap` 0,713 → 0,084, `min` 0,279 → 0,083,
`max` 0,054 → 0,054 (Fade = 100: nincs látható árnyék).
"""

from __future__ import annotations

import numpy as np
import pytest

from picasapy.render.glimmer_frame_ops import compose_drop_shadow, draw_drop_shadow
from picasapy.render.nativ_blur import nativ_blur_csatorna

ARNYEK = (10, 20, 30)
HATTER = (250, 240, 230)


def _kep(szeles=60, magas=40):
    return np.full((magas, szeles, 3), 128, dtype=np.uint8)


@pytest.mark.parametrize(("fade", "alfa"), [(0.0, 255), (30.0, 178), (50.0, 128), (100.0, 0)])
def test_a_tavoli_arnyek_kepont_egesz_keveres(fade, alfa):
    """Az árnyék belsejében (az elmosás hatókörén túl) az alfa a téglalapé:
    `ROUND(shadowAlpha·255)` — 0,7·255 = 178,5 → 178 (páros felé)."""
    kep = _kep()
    ki = compose_drop_shadow(kep, ARNYEK, HATTER, distance_px=30, angle=0.0,
                             blur_px=2.0, margin=40, fade=fade)
    # az eltolt árnyék jobb szélén, a képen kívül, a sáv közepén
    y, x = 40 + 20, 40 + 60 + 20
    vart = [(s * alfa + h * (255 - alfa)) // 255 for s, h in zip(ARNYEK, HATTER, strict=True)]
    assert ki[y, x].tolist() == vart


def test_az_elmosas_a_nativ_ut():
    """A kimenet árnyékrésze pontosan a natív elmosott alfával kevert."""
    kep = _kep()
    ki = compose_drop_shadow(kep, ARNYEK, HATTER, distance_px=6, angle=45.0,
                             blur_px=5.0, margin=12, fade=30.0)
    from picasapy.render.glimmer_frame_ops import shadow_offset

    dx, dy = shadow_offset(6, 45.0)
    alfa = np.zeros(ki.shape[:2], dtype=np.uint8)
    alfa[12 + dy : 12 + dy + 40, 12 + dx : 12 + dx + 60] = 178
    ab = nativ_blur_csatorna(alfa, 5.0, 5.0, 3).astype(np.uint32)
    vart = ((np.array(ARNYEK, np.uint32) * ab[..., None]
             + np.array(HATTER, np.uint32) * (255 - ab[..., None])) // 255).astype(np.uint8)
    vart[12:52, 12:72] = kep
    np.testing.assert_array_equal(ki, vart)


def test_a_draw_drop_shadow_merete_valtozatlan():
    """A vászon mérete (#3419) nem függ az elmosás módjától."""
    ki = draw_drop_shadow(_kep(), ARNYEK, HATTER, distance=4, angle=90, blur=10, fade=30)
    # margó = ceil(10 · 1,3501) = 14; a 4 képpontos eltolás a margón belül marad
    assert ki.shape[:2] == (40 + 2 * 14, 60 + 2 * 14)
