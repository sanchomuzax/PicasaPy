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
    rotate_with_pad,
)

#: Polaroid rögzített árnyék-recept (`DropShadowImageOperation` felülírás):
#: `blur`/`distance` itt PIXELBEN értendő, nem a rövidebb oldal
#: százalékában (#1144 — a `818×950`/`887×1004` mért kimenet csak ezzel a
#: két konstanssal, `margin = blur + distance` képlettel egyezik; a
#: `draw_drop_shadow` %-os modellje ide NEM alkalmazható, ld. annak
#: docstringjét).
_POLAROID_SHADOW_BLUR_PX = 8
_POLAROID_SHADOW_DISTANCE_PX = 3


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
    belső ragyogás (fekete, `sugár = 2·0,02·max(W,H)/8`, `strength 1,3`,
    `alfa 0,7`) → belső gyűrű (`Inner`) → újra ragyogás (`alfa 0,6`) →
    külső gyűrű (`Outer`).
    """
    from picasapy.render.glimmer_frame_ops import add_ring
    from picasapy.render.glimmer_ops import inner_glow
    from picasapy.render.glimmer_tone import VIGNETTE_RADIUS_FACTOR

    validate_image(image)
    height, width = image.shape[:2]
    # #317: ugyanaz a `/8`-as szorzó, mint a Vignette-nél — a
    # `referencia/museummatte/` FÜGGETLENÜL ugyanezt adta (a
    # `filterdesc.xml` `/4`-es képlete helyett): az alapértelmezett
    # exporttól való eltérés 3,67 → 2,07.
    radius = 2.0 * VIGNETTE_RADIUS_FACTOR * max(height, width)
    glowed_inner = inner_glow(image, (0, 0, 0), radius, radius, 1.3, alpha=0.7)
    ringed_inner = add_ring(glowed_inner, inner_thickness, inner_color)
    glowed_outer = inner_glow(ringed_inner, (0, 0, 0), radius, radius, 1.3, alpha=0.6)
    return add_ring(glowed_outer, outer_thickness, outer_color)


def apply_polaroid(image, rotate: float = 5.0, color=(0xE2, 0xE2, 0xE2)):
    """`Polaroid=1,Rotate,szín` — négyzetes középvágás → aszimmetrikus
    fehér keret (oldalt 6,45%, fent 9,68%, lent 25,8% a négyzet oldalából)
    → vetett árnyék (`distance 3`, `angle = 90−Rotate`, `blur 8`,
    `shadowAlpha 0,4`) → `padBorder` forgatás `Rotate` `[-10..10]` fokkal.
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
    bordered = add_border_sides(cropped, side_border, side_border, top_border, bottom_border, color)
    # shadowAlpha = 0,4 rögzített → fade_alpha(fade) = 0,4 ⇒ fade = 60.
    # #1144: a margó `blur_px + distance_px` (NEM `2·blur_px + distance_px` —
    # az a `draw_drop_shadow` %-os, ide nem érvényes modellje volt, ami a
    # kimenetet 29%-kal megnövelte).
    margin = _POLAROID_SHADOW_BLUR_PX + _POLAROID_SHADOW_DISTANCE_PX
    shadowed = compose_drop_shadow(
        bordered,
        (0, 0, 0),
        color,
        distance_px=_POLAROID_SHADOW_DISTANCE_PX,
        angle=90.0 - rotate,
        blur_px=_POLAROID_SHADOW_BLUR_PX,
        margin=margin,
        fade=60.0,
    )
    return rotate_with_pad(shadowed, rotate, color)


__all__ = [
    "apply_border",
    "apply_rounded_edges",
    "apply_drop_shadow",
    "apply_museum_matte",
    "apply_polaroid",
]
