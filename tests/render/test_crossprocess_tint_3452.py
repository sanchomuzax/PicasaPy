"""#3452: a CrossProcess záró `Tint` lépése a fényesség-tartó színezés.

A `filterdesc.xml` `CrossProcess` láncának utolsó tagja:

    <TintImageOperation Color="0xfcff00" BlendAlpha=".2" BlendMode="multiply"/>

A `TintImageOperation` maga a #878-ban megfejtett, FÉNYESSÉG-TARTÓ színezés
(`glimmer_ops.tint_luma_preserving`); a `BlendMode`/`BlendAlpha` azt mondja
meg, hogyan kerül az eredménye a bemenetre: szorzó keveréssel, 0,2 súllyal.
A kódunk ehelyett a nyers sárga színnel szorzott (`tint_multiply`), ami a kék
csatornát a világos tónusokban is 0,8-szorosára nyomta — a Picasa-exporton a
kék a csúcsfényben megmarad.

A 684-es golden (`crossprocess__alap.jpg`, Fade 0) ΔE-je: 8,885 → 1,035.
"""

from __future__ import annotations

import numpy as np

from picasapy.render import glimmer_tone as t
from picasapy.render.glimmer_ops import (
    apply_blend_mode,
    tint_luma_preserving,
    to_float,
    to_uint8,
)

SARGA = (0xFC, 0xFF, 0x00)


def _kep() -> np.ndarray:
    rng = np.random.default_rng(3452)
    return rng.integers(0, 256, size=(24, 32, 3), dtype=np.uint8)


def _tint_elotti(kep: np.ndarray) -> np.ndarray:
    gorbe = t.adjust_curves(kep, red=t._CROSS_RED, green=t._CROSS_GREEN, blue=t._CROSS_BLUE)
    return t.simple_color_matrix(gorbe, brightness=10.0, contrast=10.0)


def test_a_tint_szorzo_keveres_a_fenyesseg_tarto_szinezessel():
    kep = _kep()
    elotte = _tint_elotti(kep)
    szinezett = tint_luma_preserving(elotte, SARGA)
    vart = to_uint8(apply_blend_mode(to_float(elotte), to_float(szinezett), "multiply", 0.2))
    np.testing.assert_array_equal(t.apply_crossprocess(kep, fade=0.0), vart)


def test_a_csucsfenyben_a_kek_csatorna_megmarad():
    feher = np.full((4, 4, 3), 250, dtype=np.uint8)
    elotte = _tint_elotti(feher)
    kimenet = t.apply_crossprocess(feher, fade=0.0)
    # a nyers sárga szorzó 0,8-szorosra vágná a kéket; a Picasán nem esik
    assert kimenet[..., 2].mean() > 0.95 * elotte[..., 2].mean()


def test_teljes_halvanyitasnal_az_eredeti_marad():
    kep = _kep()
    np.testing.assert_array_equal(t.apply_crossprocess(kep, fade=100.0), kep)
