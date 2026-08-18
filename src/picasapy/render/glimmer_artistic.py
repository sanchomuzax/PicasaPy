"""Glimmer-effektek — művészi csővezetékek (#381): `Boost`, `Soften`,
`Pixelate`, `PicnikGrain`.

Ld. `glimmer_tone.py` modul-docstringjét az egzaktság-elvről.

Bemenet/kimenet: `uint8` RGB `numpy.ndarray` (H, W, 3). Minden függvény
TISZTA: új tömböt ad vissza, a bemenetet sosem mutálja.
"""

from __future__ import annotations

from picasapy.render.curves import validate_image
from picasapy.render.glimmer_ops import (
    alpha_blend,
    apply_noise,
    fade_alpha,
    gaussian_blur_f,
    resize_image,
    simple_color_matrix,
    to_float,
    to_uint8,
)


def apply_boost(image, impact: float = 50.0):
    """`Boost=1,Impact` — `SimpleColorMatrix(Brightness = Impact·−20/50,
    Saturation = Impact·20/50, Contrast = Impact·40/50)`. **Figyelem: a
    fényerő NEGATÍV irányba megy** (nagyobb `Impact` → sötétebb kép, a
    kontraszt/telítettség-emelés mellett). Nincs Fade.
    """
    validate_image(image)
    return simple_color_matrix(
        image, brightness=impact * -20.0 / 50.0, saturation=impact * 20.0 / 50.0, contrast=impact * 40.0 / 50.0
    )


def apply_soften(image, impact: float = 50.0, fade: float = 50.0):
    """`Soften=1,Impact,Fade` — Gauss-elmosás (`σ = Impact·20/50`) keverve
    `BlendAlpha = (100−Fade)·0,8/100` súllyal — a Fade itt 0,8-as
    szorzóval hat, NEM 1,0-val.
    """
    validate_image(image)
    image_f = to_float(image)
    sigma = max(impact * 20.0 / 50.0, 1e-6)
    blurred = gaussian_blur_f(image_f, sigma)
    alpha = max(0.0, min(1.0, (100.0 - fade) * 0.8 / 100.0))
    return to_uint8(alpha_blend(image_f, blurred, alpha))


def apply_pixelate(image, impact: float = 20.0, fade: float = 0.0):
    """`Pixelate=1,Impact,BlendMode,Fade` — `Resize(W/Impact, H/Impact)` →
    `Resize(W, H, smoothing=false)`, `Impact` `[2..150]`. A `BlendMode`
    csúszka (`[0..9]`, alap 9) jelentése a `filterdesc.xml`-ből NEM
    dekódolható (nincs leírt formula/enum-lista) — a paraméter átveendő
    a lánc `filters=` sorából, de a pixelesítést a Fade-szabályon kívül
    NEM módosítja (nyitott részlet, ld. `docs/specs/filters-decoded.md`).
    """
    validate_image(image)
    height, width = image.shape[:2]
    small_w = max(1, round(width / impact))
    small_h = max(1, round(height / impact))
    small = resize_image(image, small_w, small_h, smoothing=True)
    pixelated = resize_image(small, width, height, smoothing=False)
    return to_uint8(alpha_blend(to_float(image), to_float(pixelated), fade_alpha(fade)))


def apply_picnik_grain(image, grain: float = 10.0, lighten: bool = False, seed: int | None = None):
    """`PicnikGrain=1,Grain,Lighten` — szürke zaj, `Lighten` esetén
    `[0, 2,55·Grain]` tartományon `lighten` móddal, egyébként
    `[255−2,55·Grain, 255]` tartományon `darken` móddal (a `BlendMode`
    csúszka `7`/`5` indexeit a `Lighten` jelölő NEVE alapján a `lighten`/
    `darken` blend-módra képezzük — a `filterdesc.xml` konkrét mód-index
    → névtáblát nem közli). Nincs Fade.

    `seed` alapból `None` (#907): a zajminta FÜGGETLEN minden alkalmazásnál,
    mint az eredeti Picasánál. Csak tesztelési célra adj explicit `seed`-et,
    ha determinisztikus/reprodukálható kimenet kell.
    """
    validate_image(image)
    if lighten:
        low, high, mode = 0.0, 2.55 * grain, "lighten"
    else:
        low, high, mode = 255.0 - 2.55 * grain, 255.0, "darken"
    return apply_noise(
        image, low=low, high=high, grayscale=True, blend_alpha=1.0, blend_mode=mode, seed=seed
    )


__all__ = ["apply_boost", "apply_soften", "apply_pixelate", "apply_picnik_grain"]
