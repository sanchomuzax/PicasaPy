"""Glimmer-effektek — keretes (MÉRETNÖVELŐ) csővezetékek (#381): `Border`,
`RoundedEdges`, `DropShadow`, `MuseumMatte`, `Polaroid`.

Ld. `glimmer_tone.py` modul-docstringjét az egzaktság-elvről. A modul MIND
AZ ÖT függvénye NAGYOBB képet ad vissza, mint a bemenet (ld. a korábbi
`effects_frames.py` modul-docstringjének figyelmeztetését a render-lánc/
gyorsítótár/export hatásairól — az továbbra is érvényes).

Bemenet/kimenet: `uint8` RGB `numpy.ndarray` (H, W, 3). Minden függvény
TISZTA: új tömböt ad vissza, a bemenetet sosem mutálja.
"""

from __future__ import annotations

from picasapy.render.curves import validate_image
from picasapy.render.glimmer_frame_ops import (
    add_border_sides,
    compose_drop_shadow,
    draw_border,
    draw_drop_shadow,
    drop_shadow_padding,
    rotate_with_pad,
)

#: Polaroid rögzített árnyék-recept (`DropShadowImageOperation` felülírás):
#: `blur`/`distance` KÉPPONTBAN (#1144). A vászon ugyanaz az uniós margó,
#: mint az önálló `DropShadow`-é (`drop_shadow_padding`, #3809): bal
#: `11 − dx`, fent `11 − dy`, jobb `11 + dx`, lent `11 + dy`, ahol
#: `11 = ceil(8 · 1,3501)`. A teljes méret ezért `+22` mindkét irányban —
#: ezt mérte a #1144 (`818×950`/`887×1004`).
_POLAROID_SHADOW_BLUR_PX = 8
_POLAROID_SHADOW_DISTANCE_PX = 3

#: A Polaroid képkerete — a `filterdesc.xml` `SimpleBorderImageOperation`-je
#: rögzítve adja (`color="0xffffff"`), a csúszka-szín nem hat rá (#3420).
_POLAROID_FRAME_COLOR = (255, 255, 255)


def apply_border(
    image,
    outer_color=(0, 0, 0),
    outer_thickness: float = 20.0,
    inner_color=(255, 255, 255),
    inner_thickness: float = 5.0,
    corner_radius: float = 0.0,
    caption_height: float = 0.0,
):
    """`Border=1,OuterThickness,InnerThickness,CornerRadius,színOuter,
    színInner,CaptionHeight` — `BorderImageOperation`. Vastagságok
    `[0..100]` (a rövidebb oldal százaléka), `CornerRadius`
    `[0..min(W,H)/2]`, `CaptionHeight` `[0..H/6]` (mindkettő PIXELBEN).
    """
    validate_image(image)
    return draw_border(
        image, outer_color, inner_color, outer_thickness, inner_thickness, corner_radius, caption_height
    )


def apply_rounded_edges(image, corner_radius: float | None = None, outer_color=(255, 255, 255)):
    """`RoundedEdges=1,CornerRadius,szín` — a `Border` motorja szegély
    nélkül, csak sarok-lekerekítéssel. `CornerRadius` alapértéke
    `min(W,H)/10`, ha nincs megadva.
    """
    validate_image(image)
    height, width = image.shape[:2]
    radius = corner_radius if corner_radius is not None else min(height, width) / 10.0
    return draw_border(image, outer_color, outer_color, 0.0, 0.0, radius, 0.0)


def apply_drop_shadow(
    image,
    distance: float = 4.0,
    angle: float = 90.0,
    blur: float = 10.0,
    shadow_color=(0, 0, 0),
    background_color=(255, 255, 255),
    fade: float = 30.0,
):
    """`DropShadow=1,Distance,Angle,Blur,színÁrnyék,színHáttér,Fade` —
    `shadowAlpha = 1 − Fade/100`, `Distance` `[0..30]`, `Angle` `[0..360]`,
    `Blur` `[0..100]`.
    """
    validate_image(image)
    return draw_drop_shadow(image, shadow_color, background_color, distance, angle, blur, fade)


def apply_museum_matte(
    image,
    outer_color=(0x1A, 0x0E, 0x03),
    outer_thickness: float = 25.0,
    inner_color=(0xF0, 0xEA, 0xE4),
    inner_thickness: float = 40.0,
):
    """`MuseumMatte=1,OuterThickness,InnerThickness,színOuter,színInner` —
    belső ragyogás (fekete, `xblur = 2·0,02·max(W,H)/4`, `strength 1,3`,
    `alfa 0,7`) → belső gyűrű (`Inner`) → újra ragyogás (`alfa 0,6`) →
    külső gyűrű (`Outer`).
    """
    from picasapy.render.belso_ragyogas import inner_glow
    from picasapy.render.glimmer_frame_ops import add_ring

    validate_image(image)
    height, width = image.shape[:2]
    # #3827: a leíró `/4`-es képlete, a natív lánc maga kicsinyít és vág. A
    # második ragyogás blurja is az EREDETI kép méretéből számol (mérve: a
    # gyűrűs kép méretéből az alap 0,251 és a max 0,343 lenne, így 0,230 és
    # 0,287). Az alfa a művelet `BlendAlpha`-ja.
    xblur = 2.0 * 0.02 * max(height, width) / 4.0
    glowed_inner = inner_glow(image, (0, 0, 0), xblur, xblur, 1.3, alpha=0.7)
    ringed_inner = add_ring(glowed_inner, inner_thickness, inner_color)
    glowed_outer = inner_glow(ringed_inner, (0, 0, 0), xblur, xblur, 1.3, alpha=0.6)
    return add_ring(glowed_outer, outer_thickness, outer_color)


def apply_polaroid(image, rotate: float = 5.0, color=(0xE2, 0xE2, 0xE2), *, gyors: bool = False):
    """`Polaroid=1,Rotate,szín` — négyzetes középvágás → aszimmetrikus
    FEHÉR keret (oldalt 6,45%, fent 9,68%, lent 25,8% a négyzet oldalából)
    → vetett árnyék (`distance 3`, `angle = 90−Rotate`, `blur 8`,
    `shadowAlpha 0,4`, háttér: `szín`) → `padBorder` forgatás `Rotate`
    `[-10..10]` fokkal, pozitívnál az óramutató járása szerint, a sarkokban
    `szín` kitöltéssel.

    `gyors=True` (#3862): a záró forgatás a `rotate_with_pad` gyors útját
    választja — CSAK a Rotate-csúszka húzása közbeni élő előnézetnek, ld.
    ott a docsztringet.
    """
    validate_image(image)
    height, width = image.shape[:2]
    crop_size = min(height, width)
    top = (height - crop_size) // 2
    left = (width - crop_size) // 2
    cropped = image[top : top + crop_size, left : left + crop_size].copy()
    side_border = round(crop_size * 0.0645)
    top_border = round(crop_size * 0.0968)
    bottom_border = round(crop_size * 0.258)
    # #3420: a képkeret FEHÉR (`SimpleBorderImageOperation color="0xffffff"`);
    # a `color` csak az árnyék hátterére és a forgatás kitöltésére megy
    bordered = add_border_sides(
        cropped, side_border, side_border, top_border, bottom_border, _POLAROID_FRAME_COLOR
    )
    # shadowAlpha = 0,4 rögzített → fade_alpha(fade) = 0,4 ⇒ fade = 60.
    # #3809: a vászon az eredeti és az eltolt-kiterjesztett doboz UNIÓJA
    szog = 90.0 - rotate
    _, _, pads = drop_shadow_padding(_POLAROID_SHADOW_DISTANCE_PX, szog, _POLAROID_SHADOW_BLUR_PX)
    shadowed = compose_drop_shadow(
        bordered,
        (0, 0, 0),
        color,
        distance_px=_POLAROID_SHADOW_DISTANCE_PX,
        angle=szog,
        blur_px=_POLAROID_SHADOW_BLUR_PX,
        margin=0,
        fade=60.0,
        pads=pads,
    )
    return rotate_with_pad(shadowed, rotate, color, gyors=gyors)


__all__ = [
    "apply_border",
    "apply_rounded_edges",
    "apply_drop_shadow",
    "apply_museum_matte",
    "apply_polaroid",
]
