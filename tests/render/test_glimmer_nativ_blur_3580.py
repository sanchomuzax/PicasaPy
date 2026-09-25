"""#3580 — a Glimmer-effektek `BlurImageOperation`-je a natív dobozszűrőt futtatja.

A `glimmer::BlurImageOperation` (`0x00bb4de0`) a DropShadow-val közös natív
diszpécsert hívja (`render/nativ_blur.blur_image_operation`, #3084). A
Poszterizálás már átállt rá; ez az őr a többi hét hívóhelyet köti:

| effekt | `xblur` | `yblur` | `quality` | forrás |
|---|---|---|---|---|
| `Soften` | `Impact·20/50` | ugyanaz | 3 | a csúszka-képlet |
| `Orton` | `Bloom` | `Bloom` | 3 | #317: a mért σ a Bloom FELE = a 3 menetes doboz szórása |
| `PencilSketch` | `Radius` | `Radius` | 3 | `filterdesc-registry.md` 4.5, példa-recept |
| `Holga` | 18 | 20 | 3 | a maszkolt elmosás (4.4, „ami Blur") |
| `Lomo` | 20 | 20 | 3 | ugyanaz |
| `IR` | `greenglow` = 5 | 5 | 3 | a gyerek `+0x24`/`+0x2c` tagja = `Blur` (`0x00bc3ff3`…) |
| `ReanimatedEyeColor` | `Blur` | `Blur` | 3 | `filterdesc.xml` 1269–1295 |

A Gauss-közelítés (`gaussian_blur_f`) egyik helyen sem hívódhat.
"""

from __future__ import annotations

import numpy as np
import pytest

from picasapy.render import glimmer_artistic, glimmer_creative, glimmer_focal, glimmer_ops
from picasapy.render import nativ_blur


def _kep(seed: int = 7, meret: tuple[int, int] = (48, 64)) -> np.ndarray:
    return np.random.default_rng(seed).integers(0, 256, (*meret, 3), dtype=np.uint8)


@pytest.fixture
def hivasok(monkeypatch):
    """Rögzíti a natív út hívásait, és tiltja a Gauss-közelítést."""
    rogzitett: list[tuple[float, float, int]] = []
    eredeti = nativ_blur.blur_image_operation

    def _nativ(kep, xblur, yblur, quality=3):
        assert kep.dtype == np.uint8
        rogzitett.append((float(xblur), float(yblur), int(quality)))
        return eredeti(kep, xblur, yblur, quality)

    def _tiltott(*_a, **_k):
        raise AssertionError("a Gauss-közelítés hívódott a natív BlurImageOperation helyett")

    for modul in (glimmer_artistic, glimmer_creative, glimmer_focal):
        monkeypatch.setattr(modul, "blur_image_operation", _nativ, raising=False)
        monkeypatch.setattr(modul, "gaussian_blur_f", _tiltott, raising=False)
    return rogzitett


@pytest.mark.parametrize(
    ("futtat", "vart"),
    [
        (lambda k: glimmer_artistic.apply_soften(k, impact=50.0, fade=50.0), [(20.0, 20.0, 3)]),
        (lambda k: glimmer_artistic.apply_soften(k, impact=80.0, fade=0.0), [(32.0, 32.0, 3)]),
        (lambda k: glimmer_creative.apply_orton(k, bloom=25.0), [(25.0, 25.0, 3)]),
        (lambda k: glimmer_creative.apply_pencil_sketch(k, radius=2.0), [(2.0, 2.0, 3)]),
        (lambda k: glimmer_creative.apply_holga(k), [(18.0, 20.0, 3)]),
        (lambda k: glimmer_creative.apply_lomo(k), [(20.0, 20.0, 3)]),
        (lambda k: glimmer_creative.apply_ir(k), [(5.0, 5.0, 3)]),
        (
            lambda k: glimmer_focal.apply_reanimated_eye_color(
                k, blur=6.0, mask=np.ones(k.shape[:2])
            ),
            [(6.0, 6.0, 3)],
        ),
    ],
    ids=["soften-alap", "soften-80", "orton", "pencilsketch", "holga", "lomo", "ir", "reanimated"],
)
def test_a_nativ_blur_image_operation_hivodik_a_leiro_ertekeivel(hivasok, futtat, vart):
    futtat(_kep())
    assert hivasok == vart


def test_orton_a_nativ_elmosott_reteget_keveri_overlay_modban():
    kep = _kep(3)
    elmosott = glimmer_ops.to_float(nativ_blur.blur_image_operation(kep, 25.0, 25.0, 3))
    overlaid = glimmer_ops.apply_blend_mode(glimmer_ops.to_float(kep), elmosott, "overlay", 1.0)
    vart = glimmer_ops.adjust_curves(
        glimmer_ops.to_uint8(overlaid), master=((0.0, 0.0), (128.0, 128.0), (255.0, 255.0))
    )
    np.testing.assert_array_equal(glimmer_creative.apply_orton(kep, bloom=25.0), vart)


def test_soften_a_nativ_elmosast_keveri_vissza():
    kep = _kep(4)
    elmosott = glimmer_ops.to_float(nativ_blur.blur_image_operation(kep, 20.0, 20.0, 3))
    vart = glimmer_ops.to_uint8(glimmer_ops.alpha_blend(glimmer_ops.to_float(kep), elmosott, 0.4))
    np.testing.assert_array_equal(glimmer_artistic.apply_soften(kep, impact=50.0, fade=50.0), vart)


def test_soften_nulla_impactnal_nem_mos():
    """`Impact = 0` → a kvantáló 0-t ad → a natív út nem mos (a Gauss-út 1e-6
    szigmával szintén azonosság volt)."""
    kep = _kep(5)
    np.testing.assert_array_equal(glimmer_artistic.apply_soften(kep, impact=0.0, fade=0.0), kep)
