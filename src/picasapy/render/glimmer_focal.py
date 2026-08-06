"""Glimmer-effektek — festhető maszkos csővezetékek (#381): `PicnikTint`,
`ReanimatedEyeColor`.

**A festhető-maszk kérdés (#381 elfogadási feltétel):** mindkét effekt a
Picnik `_mctr.mask` ecset-eszközével kijelölt RÉGIÓRA hat (pl. a szem íriszére
a `ReanimatedEyeColor` esetén) — a PicasaPy-nak MÉG NINCS ecset-eszköze
(a `retouch`/`redeye` régió-alapú keretrendszer erre kiterjeszthető lenne,
de ez nem #381 hatóköre). Emiatt itt a TELJES KÉPRE alkalmazzuk a hatást —
ez SZÁNDÉKOS ELTÉRÉS a Picasa viselkedésétől, amit a hívó (`chain.py`) egy
magyar figyelmeztetéssel jelez (`ChainReport.range_warnings`).

Bemenet/kimenet: `uint8` RGB `numpy.ndarray` (H, W, 3). Minden függvény
TISZTA: új tömböt ad vissza, a bemenetet sosem mutálja.
"""

from __future__ import annotations

from picasapy.render.curves import validate_image
from picasapy.render.glimmer_ops import (
    alpha_blend,
    apply_blend_mode,
    fade_alpha,
    gaussian_blur_f,
    to_float,
    to_uint8,
)


def _solid_layer(image_f, color):
    import numpy as np

    layer = np.empty_like(image_f)
    layer[..., 0] = color[0]
    layer[..., 1] = color[1]
    layer[..., 2] = color[2]
    return layer


def apply_picnik_tint(image, color=(0x80, 0xCF, 0xFF), fade: float = 0.0):
    """`PicnikTint=1,szín,Fade` — a kijelölt terület sima (`normal`) színes
    bevonása, `BlendAlpha = 1 − Fade/100` átlátszósággal. **Ecset-maszk
    nélkül: a TELJES KÉPRE fut** (ld. modul-docstring).
    """
    validate_image(image)
    image_f = to_float(image)
    layer = _solid_layer(image_f, color)
    return to_uint8(apply_blend_mode(image_f, layer, "normal", fade_alpha(fade)))


def apply_reanimated_eye_color(image, blur: float = 6.0, fade: float = 20.0, color=(0xC8, 0xFF, 0x00)):
    """`ReanimatedEyeColor=1,Blur,Fade` — a kijelölt terület (jellemzően az
    íriszek) enyhén elmosott szorzó-színezése. A `color` a `filterdesc.xml`
    csúszkatáblájában NEM szerepel (a registerben csak `Blur`/`Fade` van) —
    a tényleges szín-választás feltehetően egy külön, ezen effekten kívüli
    mechanizmus (pl. a felhasználó szemszín-palettája), ami itt NEM ismert;
    `color` ezért egy dokumentáltan ÖNKÉNYES alapérték. `Blur` `[0..30]`
    (alap 6), `Fade` `[0..100]` (alap 20). **Ecset-maszk nélkül: a TELJES
    KÉPRE fut** (ld. modul-docstring).
    """
    validate_image(image)
    image_f = to_float(image)
    blurred = gaussian_blur_f(image_f, max(blur, 1e-6))
    layer = _solid_layer(blurred, color)
    tinted = apply_blend_mode(blurred, layer, "multiply", 1.0)
    return to_uint8(alpha_blend(image_f, tinted, fade_alpha(fade)))


__all__ = ["apply_picnik_tint", "apply_reanimated_eye_color"]
