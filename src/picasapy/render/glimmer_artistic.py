"""Glimmer-effektek — művészi csővezetékek (#381): `Boost`, `Soften`,
`Pixelate`, `PicnikGrain`.

Ld. `glimmer_tone.py` modul-docstringjét az egzaktság-elvről.

Bemenet/kimenet: `uint8` RGB `numpy.ndarray` (H, W, 3). Minden függvény
TISZTA: új tömböt ad vissza, a bemenetet sosem mutálja.
"""

from __future__ import annotations

from picasapy.render.curves import validate_image
from picasapy.render.glimmer_ops import (
    BLEND_MODE_BY_INDEX,
    alpha_blend,
    apply_blend_mode,
    apply_noise,
    fade_alpha,
    resize_image,
    simple_color_matrix,
    to_float,
    to_uint8,
)
from picasapy.render.nativ_blur import blur_image_operation


def apply_boost(image, impact: float = 50.0):
    """`Boost=1,Impact` — `SimpleColorMatrix(Brightness = Impact·−20/50,
    Saturation = Impact·20/50, Contrast = Impact·40/50)`. Nincs Fade.

    A fényerő-PARAMÉTER negatív irányba megy, de a TELJES lánc kimenete
    ettől függetlenül **világosodik**: a kontraszt 63,5-ös forgáspontja
    (#904) a fölötte lévő tónusokat sokkal erősebben futtatja fel, mint
    amennyit a szerény negatív fényerő levon, és a felfutó képpontok
    255-re vágódnak. A `64,128,192` képpont `Impact=90`-nél `0,255,255`-re
    megy, a középszürke `128,128,128` tiszta fehérre.

    ⚠️ Egy korábbi docstring azt állította, hogy nagyobb `Impact` sötétebb
    képet ad — **ez megdőlt** (#964). A binárisból megerősítve: az eredeti
    is telítődő vágással dolgozik (`packuswb`, `0x008f28ae`), a három lépés
    egyetlen 5×5 mátrixba fűzve (`0x008f28d0`), tehát a kiégés az EREDETI
    viselkedése is, nem a mi hibánk.
    """
    validate_image(image)
    return simple_color_matrix(
        image, brightness=impact * -20.0 / 50.0, saturation=impact * 20.0 / 50.0, contrast=impact * 40.0 / 50.0
    )


def apply_soften(image, impact: float = 50.0, fade: float = 50.0):
    """`Soften=1,Impact,Fade` — `BlurImageOperation` (`xblur = yblur =
    Impact·20/50`, `quality = 3`) keverve `BlendAlpha = (100−Fade)·0,8/100`
    súllyal — a Fade itt 0,8-as szorzóval hat, NEM 1,0-val.

    Az elmosás a natív dobozszűrő (`render/nativ_blur.blur_image_operation`,
    #3580), nem Gauss-közelítés: a háromszoros doboz szórása ≈ `xblur/2`.
    """
    validate_image(image)
    radius = impact * 20.0 / 50.0
    if radius <= 0.0:
        # 0-s sugárnál nincs elmosás, és keverés sincs: a Picasa exportja itt a
        # bemenettel azonos (684-es golden, `soften__min`: MINDKETTO_TETLEN). Az
        # egész keverés (#3442) két azonos réteget is `>>8`-cal osztana, ami
        # minden képpontot eggyel sötétítene.
        return image.copy()
    image_f = to_float(image)
    blurred = to_float(blur_image_operation(image, radius, radius, quality=3))
    alpha = max(0.0, min(1.0, (100.0 - fade) * 0.8 / 100.0))
    return to_uint8(alpha_blend(image_f, blurred, alpha))


def apply_pixelate(image, impact: float = 20.0, fade: float = 0.0, blend_mode: int = 9):
    """`Pixelate=1,Impact,BlendMode,Fade` — `Resize(W/Impact, H/Impact)` →
    `Resize(W, H, smoothing=false)`, `Impact` `[2..150]`.

    A pixelesített kép (felső) a BEMENETTEL (alsó) a `BlendMode` sorszámú
    natív móddal keveredik, utána a `Fade` szerinti átlátszósággal (a
    `filterdesc.xml`: `BlendMode="{_sldrBlendMode.value}"`,
    `BlendAlpha="{1-(_sldrFade.value/100)}"`). A csúszka `[0..9]`, alap 9
    (Normal); a sorszám közvetlenül a módtábla (`0x00cf0e98`) indexe — ld.
    `glimmer_ops.BLEND_MODE_BY_INDEX` (#3443).

    Csúszkán kívüli sorszámra `ValueError`: némán Normalt futtatni hamis
    képet adna.
    """
    validate_image(image)
    # a csúszka 0–9-ig megy; a 10-es Softlight a táblában van, de itt nem
    mode = BLEND_MODE_BY_INDEX.get(int(blend_mode)) if 0 <= int(blend_mode) <= 9 else None
    if mode is None:
        raise ValueError(f"A Pixelate keverési módja 0 és 9 közé esik: {blend_mode}")
    height, width = image.shape[:2]
    small_w = max(1, round(width / impact))
    small_h = max(1, round(height / impact))
    small = resize_image(image, small_w, small_h, smoothing=True)
    pixelated = resize_image(small, width, height, smoothing=False)
    return to_uint8(apply_blend_mode(to_float(image), to_float(pixelated), mode, fade_alpha(fade)))


#: A `PicnikGrain` leírójának rögzített `randomSeed`-je (`filterdesc.xml`,
#: `NoiseImageOperation randomSeed="1"`, #3757).
_PICNIK_GRAIN_SEED = 1

#: A leíró `BlendMode="{_radioLighten.selected?7:5}"`-je a natív módtábla
#: (`0x00cf0e98`) sorszámait adja: 7 = Screen, 5 = Multiply (#3444).
_PICNIK_GRAIN_VILAGOSITO_MOD = 7
_PICNIK_GRAIN_SOTETITO_MOD = 5


def apply_picnik_grain(image, grain: float = 10.0, lighten: bool = False):
    """`PicnikGrain=1,Grain,Lighten` — szürke zaj a `NoiseImageOperation`
    natív generátorával (MT19937, Picasa-magvetés, #3736) a leíró rögzített
    `randomSeed = 1`-ével. `Lighten` esetén a zaj `[0, 2,55·Grain]`, a mód
    **Screen** (7); egyébként `[255 − 2,55·Grain, 255]`, a mód **Multiply**
    (5) — a sorszámok a natív módtábla (`0x00cf0e98`) szerint (#3444).
    Nincs Fade.

    ## A mag RÖGZÍTETT (#3757)

    A #907 „két alkalmazás független mintát ad" mérése a natív, kisbetűs
    `grain` szűrőre vonatkozott, nem erre. A `PicnikGrain` zaja a Picasában
    képpontra ugyanaz: a 684-es exporton ΔE alap 3,01 → 0,88, max 12,21 →
    1,38, a merokit-2 `Grain 30` esetén 7,79 → 0,98.
    """
    validate_image(image)
    grain = min(max(grain, 0.0), 100.0)
    if lighten:
        low, high, mode = 0.0, 2.55 * grain, _PICNIK_GRAIN_VILAGOSITO_MOD
    else:
        low, high, mode = 255.0 - 2.55 * grain, 255.0, _PICNIK_GRAIN_SOTETITO_MOD
    return apply_noise(
        image,
        seed=_PICNIK_GRAIN_SEED,
        low=low,
        high=high,
        grayscale=True,
        blend_alpha=1.0,
        blend_mode=mode,
    )


__all__ = ["apply_boost", "apply_soften", "apply_pixelate", "apply_picnik_grain"]
