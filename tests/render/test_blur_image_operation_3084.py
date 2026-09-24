"""#3084 — a `BlurImageOperation` a natív dobozszűrőt futtatja, kvantált sugárral.

A `glimmer::BlurImageOperation` alkalmazója (`0x00bb4de0`) tengelyenként
255-re vágja az `xblur`/`yblur` attribútumot, a `0x00bb5050`
sugár-kvantálón vezeti át, majd a DropShadow-val KÖZÖS natív diszpécsert
hívja (`0x00bb4fc9  call 0x00bc5680`, ld. `render/nativ_blur.py`).

A kvantáló leképezése utasításszinten kiolvasva (a konstansok float32-k):

| bemenet | kimenet |
|---|---|
| `x < 1` | 0 |
| `2 < x < 2,065` | 2,065 |
| `3 ≤ x < 3,0625` | 3,0625 |
| `4 < x < 4,13` | 4,13 |
| `5 < x < 5,13` | 5,13 |
| egyébként | `x` |
"""

from __future__ import annotations

import numpy as np
import pytest

from picasapy.render.nativ_blur import blur_image_operation, nativ_blur_bgra, sugar_kvantal

F = np.float32


@pytest.mark.parametrize(
    ("be", "ki"),
    [
        (0.5, 0.0),
        (0.999, 0.0),
        (1.0, 1.0),
        (2.0, 2.0),
        (2.03, float(F(2.065))),
        (2.065, float(F(2.065))),
        (2.1, float(F(2.1))),
        (3.0, float(F(3.0625))),
        (3.05, float(F(3.0625))),
        (3.07, float(F(3.07))),
        (4.0, 4.0),
        (4.1, float(F(4.13))),
        (5.0, 5.0),
        (5.1, float(F(5.13))),
        (10.1, float(F(10.1))),
    ],
)
def test_a_sugar_kvantalo(be, ki):
    assert sugar_kvantal(be) == pytest.approx(ki, abs=0)


def test_255_folott_255():
    kep = np.random.default_rng(1).integers(0, 256, (20, 30, 3), dtype=np.uint8)
    assert np.array_equal(blur_image_operation(kep, 400.0, 400.0), blur_image_operation(kep, 255.0, 255.0))


def test_ugyanaz_mint_a_nativ_diszpecser_a_kvantalt_sugarral():
    kep = np.random.default_rng(2).integers(0, 256, (37, 53, 3), dtype=np.uint8)
    bgra = np.dstack([kep, np.full(kep.shape[:2], 255, np.uint8)])
    varhato = nativ_blur_bgra(bgra, float(F(3.0625)), 6.5, 3)[..., :3]
    assert np.array_equal(blur_image_operation(kep, 3.0, 6.5, quality=3), varhato)


def test_a_bemenetet_nem_irja_at():
    kep = np.random.default_rng(3).integers(0, 256, (10, 12, 3), dtype=np.uint8)
    eredeti = kep.copy()
    blur_image_operation(kep, 2.1, 2.1)
    assert np.array_equal(kep, eredeti)


def _regi_menet(kep, tengely, k, h, w, oszto):
    """A #3084 előtti numpy-menet, szó szerint — a gyors út mércéje."""
    x = np.moveaxis(kep, tengely, -2).astype(np.int32)
    n = x.shape[-2]
    idx = np.clip(np.arange(-h, n + h), 0, n - 1)
    p = x[..., idx, :]
    cs = np.concatenate(
        [np.zeros(p.shape[:-2] + (1, p.shape[-1]), np.int32), np.cumsum(p, axis=-2, dtype=np.int32)], axis=-2
    )
    belso = cs[..., 2 * h : 2 * h + n, :] - cs[..., 1 : 1 + n, :]
    szel = p[..., 0:n, :] + p[..., 2 * h : 2 * h + n, :]
    ki = (szel * w + (belso << k)) // oszto
    return np.moveaxis(ki.astype(np.uint8), -2, tengely)


@pytest.mark.parametrize("sugar", [1.01, 1.5, 2.065, 3.0625, 4.7, 10.1, 33.3, 120.0, 252.0])
@pytest.mark.parametrize("tengely", [0, 1])
def test_a_gyors_menet_bitre_a_regi(sugar, tengely):
    from picasapy.render import nativ_blur as nb

    kep = np.random.default_rng(int(sugar * 10)).integers(0, 256, (61, 290, 3), dtype=np.uint8)
    par = nb.sugar_egyutthatok(sugar)
    assert np.array_equal(nb._menet(kep, tengely, *par), _regi_menet(kep, tengely, *par))


def test_a_gyors_menet_egy_csatornan_is():
    from picasapy.render import nativ_blur as nb

    kep = np.random.default_rng(9).integers(0, 256, (40, 70, 1), dtype=np.uint8)
    par = nb.sugar_egyutthatok(6.0)
    assert np.array_equal(nb._menet(kep, 1, *par), _regi_menet(kep, 1, *par))
