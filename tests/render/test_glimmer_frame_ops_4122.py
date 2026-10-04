"""#4122: a Border fedése és alfája a natív fixpontos képletet követi."""

from __future__ import annotations

import numpy as np

from picasapy.render import glimmer_frame_ops as frame_ops


# `docs/specs/filterdesc-registry.md`, I. szakasz: a 0x00aa1840 →
# 0x009ab410 natív futtatásának 9×9-es, bájtra rögzített kimenete. A mintából
# levezetett q-középpont (127/32, 7/2), belső négyzetes távolság 15/2, külső
# négyzetes távolság 25/2; ebből Δ=5 és rounder(2²⁴/Δ)=3 355 443.
_NATIVE_9X9 = np.array(
    [
        [0xFF000000, 0xFF000000, 0xFF000000, 0xFF000000, 0xFF0B0B0B, 0xFF000000, 0xFF000000, 0xFF000000, 0xFF000000],
        [0xFF000000, 0xFF000000, 0xFF787878, 0xFFFFFFFF, 0xFFFFFFFF, 0xFFFFFFFF, 0xFF6B6B6B, 0xFF000000, 0xFF000000],
        [0xFF000000, 0xFF484848, 0xFFFFFFFF, 0xFFFFFFFF, 0xFFFFFFFF, 0xFFFFFFFF, 0xFFFFFFFF, 0xFF353535, 0xFF000000],
        [0xFF000000, 0xFFAEAEAE, 0xFFFFFFFF, 0xFFFFFFFF, 0xFFFFFFFF, 0xFFFFFFFF, 0xFFFFFFFF, 0xFF9B9B9B, 0xFF000000],
        [0xFF000000, 0xFFAEAEAE, 0xFFFFFFFF, 0xFFFFFFFF, 0xFFFFFFFF, 0xFFFFFFFF, 0xFFFFFFFF, 0xFF9B9B9B, 0xFF000000],
        [0xFF000000, 0xFF484848, 0xFFFFFFFF, 0xFFFFFFFF, 0xFFFFFFFF, 0xFFFFFFFF, 0xFFFFFFFF, 0xFF353535, 0xFF000000],
        [0xFF000000, 0xFF000000, 0xFF787878, 0xFFFFFFFF, 0xFFFFFFFF, 0xFFFFFFFF, 0xFF6B6B6B, 0xFF000000, 0xFF000000],
        [0xFF000000, 0xFF000000, 0xFF000000, 0xFF000000, 0xFF0B0B0B, 0xFF000000, 0xFF000000, 0xFF000000, 0xFF000000],
        [0xFF000000, 0xFF000000, 0xFF000000, 0xFF000000, 0xFF000000, 0xFF000000, 0xFF000000, 0xFF000000, 0xFF000000],
    ],
    dtype=np.uint32,
)


def _native_q_racs() -> np.ndarray:
    """A mintából visszafejtett q-rács: középpont=(127/32, 7/2)."""
    y, x = np.indices((9, 9), dtype=np.float64)
    return (x - 127 / 32) ** 2 + (y - 7 / 2) ** 2


def test_a_raszterizo_bajtra_visszaadja_a_nativ_9x9_mintat():
    eredmeny = frame_ops._raszterez_kor(
        _native_q_racs(),
        belso_negyzetes_tav=7.5,
        kulso_negyzetes_tav=12.5,
        forras_argb=0x20FFFFFF,
        cel_argb=0xFF000000,
    )

    assert np.array_equal(eredmeny, _NATIVE_9X9)


def test_a_reszleges_alfa_es_az_opaque_kompozit_kulon_ellenorizheto():
    # A spec kontrollpéldája: A=0x20, C=175 mellett a rajzoló köztes pixele.
    koztes = frame_ops._kever_reszleges_argb(0xFF010101, 0x20010101, 175)
    assert koztes == 0xFE010001

    # A 0x20 és 0xff forrásalfa különböző, C-vel súlyozott alfát őriz;
    # mindkettőből 0xff lesz az opaque cél fölötti végső alfa.
    alfa_20 = frame_ops._fedett_forras_alfa(0x20, 175)
    alfa_ff = frame_ops._fedett_forras_alfa(0xFF, 175)
    assert (alfa_20, alfa_ff) == (21, 174)
    koztes_ff = frame_ops._kever_reszleges_argb(0xFF010101, 0xFF010101, 175)
    assert koztes_ff == 0xFE010001
    assert frame_ops._kompozit_alfa(0xFF, alfa_20) == 0xFF
    assert frame_ops._kompozit_alfa(0xFF, alfa_ff) == 0xFF
    assert frame_ops._kompozit_alfa(0xFF, (koztes_ff >> 24) & 0xFF) == 0xFF
