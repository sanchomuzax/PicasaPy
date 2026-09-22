"""Keret-/árnyék-primitívek a Glimmer-effektekhez (#381) — a `glimmer_ops.py`
testvérmodulja, KÜLÖN fájlban, hogy egyik se lépje át a 800 soros korlátot.

`BorderImageOperation`, `DropShadow` és `Rotate(padBorder)` közös építőkövei:
szegélygyűrű, sarok-lekerekítés, felirat-sáv, vetett árnyék, kibővített
vászonra forgatás. Ezeket használja a `Border`, `RoundedEdges`,
`MuseumMatte`, `Sixties` (sarok-lekerekítés), `DropShadow` és `Polaroid`
csővezetéke (`glimmer_frames.py`).
"""

from __future__ import annotations

import math

from picasapy.lazy_cv2 import cv2
import numpy as np

from picasapy.render.curves import validate_image
from picasapy.render.glimmer_ops import fade_alpha
from picasapy.render.nativ_blur import nativ_blur_csatorna


def add_ring(image: np.ndarray, thickness: float, color: tuple[int, int, int]) -> np.ndarray:
    """Egyetlen egyenletes szegélygyűrű hozzáadása — a vastagság PIXELBEN.

    #317: korábban a vastagságot a rövidebb oldal SZÁZALÉKÁNAK vettük, ezért
    egy 2560×1702-es fotón az alapértelmezett Museum Matte 1447 px-es (!)
    keretet rakott 65 helyett — a kimenet 5454×4596-ra hízott. A
    `referencia/museummatte/` hét exportja pixelre eldöntötte a kérdést: a
    hozzáadott keret oldalanként PONTOSAN `Outer + Inner` pixel
    (0/50/100-as külső és 0/100-as belső állásokon egyaránt).
    """
    validate_image(image)
    px = max(0, int(round(thickness)))
    if px == 0:
        return image.copy()
    return cv2.copyMakeBorder(image, px, px, px, px, cv2.BORDER_CONSTANT, value=color)


def add_border_sides(
    image: np.ndarray, left: int, right: int, top: int, bottom: int, color: tuple[int, int, int]
) -> np.ndarray:
    """Aszimmetrikus (oldalanként eltérő vastagságú) szegély, pixelben megadva."""
    validate_image(image)
    left, right, top, bottom = (max(0, int(round(v))) for v in (left, right, top, bottom))
    if left == right == top == bottom == 0:
        return image.copy()
    return cv2.copyMakeBorder(image, top, bottom, left, right, cv2.BORDER_CONSTANT, value=color)


def round_corners(
    image: np.ndarray, corner_radius_px: float, fill_color: tuple[int, int, int]
) -> np.ndarray:
    """A kép sarkainak lekerekítése: a levágott sarok-háromszögeket
    `fill_color`-ral tölti ki (nincs alfa-csatornánk, ezért a kivágott
    sarok a HÁTTÉRSZÍNNEL — jellemzően a keret külső színével — látszik).
    """
    validate_image(image)
    radius = int(round(corner_radius_px))
    if radius <= 0:
        return image.copy()
    height, width = image.shape[:2]
    radius = min(radius, height // 2, width // 2)
    if radius <= 0:
        return image.copy()
    mask = np.zeros((height, width), dtype=np.uint8)
    cv2.rectangle(mask, (radius, 0), (width - radius, height), 1, -1)
    cv2.rectangle(mask, (0, radius), (width, height - radius), 1, -1)
    for corner_x, corner_y in (
        (radius, radius),
        (width - radius, radius),
        (radius, height - radius),
        (width - radius, height - radius),
    ):
        cv2.circle(mask, (corner_x, corner_y), radius, 1, -1)
    color_arr = np.array(fill_color, dtype=image.dtype)
    filled = np.empty_like(image)
    filled[:] = color_arr
    return np.where(mask[..., np.newaxis] == 1, image, filled)


def add_caption(image: np.ndarray, height_px: float, color: tuple[int, int, int]) -> np.ndarray:
    """Aljára fűzött, egyszínű felirat-sáv (a szövegrajzolás nem #381 hatóköre)."""
    validate_image(image)
    px = max(0, int(round(height_px)))
    if px == 0:
        return image.copy()
    strip = np.empty((px, image.shape[1], 3), dtype=image.dtype)
    strip[:] = np.array(color, dtype=image.dtype)
    return np.concatenate([image, strip], axis=0)


def draw_border(
    image: np.ndarray,
    outer_color: tuple[int, int, int],
    inner_color: tuple[int, int, int],
    outer_thickness: float,
    inner_thickness: float,
    corner_radius_px: float = 0.0,
    caption_height_px: float = 0.0,
) -> np.ndarray:
    """`BorderImageOperation`: belső gyűrű (a fotót érinti) → külső gyűrű →
    sarok-lekerekítés → felirat-sáv, ebben a sorrendben (a Border/
    RoundedEdges/MuseumMatte/Sixties közös implementációja).
    """
    ring = add_ring(image, inner_thickness, inner_color)
    ring = add_ring(ring, outer_thickness, outer_color)
    ring = round_corners(ring, corner_radius_px, outer_color)
    return add_caption(ring, caption_height_px, outer_color)


#: #649/#626: a `DropShadowImageOperation` (`0x00bbb720`) DÖNTETLEN-ELDÖNTŐ
#: eltolásai. A natív kód az árnyék eltolását így számolja:
#:
#:     dx = round( (cosf(szög·π/180) + 6.7e-06f) · távolság + 0.001825f )
#:     dy = round( (sinf(szög·π/180) + 6.7e-06f) · távolság + 0.001825f )
#:
#: A két apró szám NEM paraméter: az egész értékhez közeli eseteknél dönti
#: el, merre billen a kerekítés (`docs/specs/filterdesc-registry.md` 4.11).
_SHADOW_TIE_SLOPE = 6.7e-06
_SHADOW_TIE_OFFSET = 0.001825


def _c_round(value: float) -> int:
    """A C `round()`-ja: a felet a nullától ELFELÉ kerekíti.

    ⚠️ A Python `round()` bankári kerekítést végez (`round(0.5) == 0`),
    tehát a natív képletet vele nem lehet reprodukálni — épp a döntetlen
    eseteknél térne el, amikre a fenti két konstans készült."""
    return (
        int(math.floor(value + 0.5))
        if value >= 0
        else -int(math.floor(-value + 0.5))
    )


def shadow_offset(distance_px: float, angle: float) -> tuple[int, int]:
    """Az árnyék (dx, dy) eltolása a MÉRT natív képlettel (#649).

    A korábbi alak a döntetlen-igazítás nélkül, Python-kerekítéssel számolt:
    a 12 × 360 (távolság, szög) kombinációból **42**-nél adott más értéket —
    például 1 képpont távolságnál 30°-on `(1, 0)` helyett a natív `(1, 1)`.
    """
    radian = math.radians(angle)
    return (
        _c_round(
            (math.cos(radian) + _SHADOW_TIE_SLOPE) * distance_px
            + _SHADOW_TIE_OFFSET
        ),
        _c_round(
            (math.sin(radian) + _SHADOW_TIE_SLOPE) * distance_px
            + _SHADOW_TIE_OFFSET
        ),
    )


#: A `DropShadow` határoló-doboz kiterjesztőjének (`0x00bcd760`) szorzója a
#: leíró `quality="{BitmapFilterQuality.HIGH}"` (= 3) fokozatán, `0x00cf4368`.
_DROPSHADOW_HIGH_FAKTOR = 1.3501
#: `quality="{BitmapFilterQuality.HIGH}"` (`filterdesc.xml`) = 3: a natív
#: elmosás 3 vízszintes + 3 függőleges menete (#3474, `0x00bc7540`/`0x00bc77b0`).
_DROPSHADOW_QUALITY = 3
#: A paraméter-vágó (`0x00bcd640`) a `blurX`/`blurY`-t erre a tartományra szorítja.
_DROPSHADOW_BLUR_MIN = 1.0
_DROPSHADOW_BLUR_MAX = 255.0


def drop_shadow_padding(
    distance: float, angle: float, blur: float
) -> tuple[float, tuple[int, int], tuple[int, int, int, int]]:
    """A `DropShadow` vásznának oldalankénti bővítése (#3419).

    A `0x00bcd760` a képet oldalanként `ceil(blur · 1,3501)` képponttal
    tágítja; a `blur` KÉPPONT, `clamp(1, 255)`. A kitágított dobozt az
    árnyék `(dx, dy)` eltolja, és a kimenet a kettő UNIÓJA az eredeti
    képpel — ha az eltolás nagyobb a margónál, a vászon aszimmetrikus.

    Vissza: `(blur_px, (dx, dy), (bal, fent, jobb, lent))`.
    """
    blur_px = min(max(float(blur), _DROPSHADOW_BLUR_MIN), _DROPSHADOW_BLUR_MAX)
    margo = math.ceil(blur_px * _DROPSHADOW_HIGH_FAKTOR)
    dx, dy = shadow_offset(int(round(distance)), angle)
    return (
        blur_px,
        (dx, dy),
        (max(0, margo - dx), max(0, margo - dy), max(0, margo + dx), max(0, margo + dy)),
    )


def compose_drop_shadow(
    image: np.ndarray,
    shadow_color: tuple[int, int, int],
    background_color: tuple[int, int, int],
    distance_px: int,
    angle: float,
    blur_px: float,
    margin: int,
    fade: float = 0.0,
    pads: tuple[int, int, int, int] | None = None,
) -> np.ndarray:
    """A `DropShadow` kompozitálása MÁR KISZÁMOLT pixel-paraméterekkel
    (elmosás-sugár, eltolás, vászon-margó) — az önálló `draw_drop_shadow`
    és a Polaroid rögzített (pixelben megadott) árnyék-receptje közös magja
    (#1144). A hívó felel a `margin` helyes levezetéséért; a `pads`
    (bal, fent, jobb, lent) megadásakor a vászon aszimmetrikus, és a
    `margin` figyelmen kívül marad.
    """
    validate_image(image)
    height, width = image.shape[:2]
    bal, fent, jobb, lent = pads if pads is not None else (margin,) * 4
    canvas_h, canvas_w = height + fent + lent, width + bal + jobb

    # #3474: a natív út (`0x00bcd940`). Az árnyékréteg egyenes BGRA: a teljes
    # vászon `árnyékszín | alfa 0`, a téglalap `ROUND(shadowAlpha · 255)`
    # alfával. Az elmosás (`0x00bc5680`, quality=3: 3 vízszintes + 3
    # függőleges egész menet) az állandó RGB-t nem változtatja, tehát
    # gyakorlatilag csak az alfát mossa — ezért elég az alfa-csatorna.
    offset_x, offset_y = shadow_offset(distance_px, angle)
    top = fent + offset_y
    left = bal + offset_x
    alfa = np.zeros((canvas_h, canvas_w), dtype=np.uint8)
    # a `round` a fistp alapértelmezett (páros felé kerekítő) módja
    alfa[top : top + height, left : left + width] = round(fade_alpha(fade) * 255)
    alfa = nativ_blur_csatorna(alfa, blur_px, blur_px, _DROPSHADOW_QUALITY).astype(np.uint32)

    # a keverés (`0x008f48b0`) egész: `(S·α + D·(255 − α)) // 255`
    hatter = np.array(background_color, dtype=np.uint32)
    arnyek = np.array(shadow_color, dtype=np.uint32)
    canvas = (arnyek * alfa[..., np.newaxis] + hatter * (255 - alfa[..., np.newaxis])) // 255
    canvas = canvas.astype(np.uint8)

    canvas[fent : fent + height, bal : bal + width] = image
    return canvas


def draw_drop_shadow(
    image: np.ndarray,
    shadow_color: tuple[int, int, int],
    background_color: tuple[int, int, int],
    distance: float,
    angle: float,
    blur: float,
    fade: float = 0.0,
) -> np.ndarray:
    """`DropShadow`: a kép vetett árnyéka a `background_color` vászonra,
    `distance`/`angle` szerint eltolva, `blur` KÉPPONTNYI elmosással,
    `shadowAlpha = fade_alpha(fade)` átlátszósággal.

    A vászon mérete a bináris kiterjesztőjét követi (`drop_shadow_padding`,
    #3419): a 684-es golden mindhárom állásában képpontra egyezik a valódi
    Picasa-exporttal. A korábbi modell (a `blur` a rövidebb oldal százaléka,
    margó `2·blur + distance`) a `0x00bcd760` szerint mindkét pontján téves
    volt.

    Az elmosás a natív `quality=3` út (#3474, `render/nativ_blur.py`): az
    emulátorban futtatott eredeti kóddal bitre azonos.
    """
    validate_image(image)
    blur_px, _, pads = drop_shadow_padding(distance, angle, blur)
    return compose_drop_shadow(
        image,
        shadow_color,
        background_color,
        int(round(distance)),
        angle,
        blur_px,
        0,
        fade,
        pads=pads,
    )


def rotate_with_pad(
    image: np.ndarray, angle_deg: float, border_color: tuple[int, int, int]
) -> np.ndarray:
    """`Rotate(..., padBorder, borderColor=...)`: elforgatás úgy, hogy a
    vászon előbb kibővül (a forgatott téglalap befoglaló mérete), így a
    sarkok (majdnem) nem vágódnak le — az üresen maradó sarkokat
    `border_color` tölti ki.

    #1144: a befoglaló méretet LEFELÉ kerekítjük (`floor`), nem felfelé — a
    Polaroid `818×950`/`887×1004` mért kimenete csak `floor`-ral egyezik
    (két különböző forgatási szöggel is ellenőrizve; `ceil` mindkét esetben
    +1 képpontot ad mindkét irányban). A gyakorlatban ez a forgatott
    téglalap sarkaiból tör le fél képpontnál kevesebbet.
    """
    validate_image(image)
    height, width = image.shape[:2]
    angle_rad = np.deg2rad(angle_deg)
    cos_a, sin_a = abs(np.cos(angle_rad)), abs(np.sin(angle_rad))
    new_w = int(np.floor(width * cos_a + height * sin_a))
    new_h = int(np.floor(width * sin_a + height * cos_a))
    canvas = np.empty((new_h, new_w, 3), dtype=image.dtype)
    canvas[:] = np.array(border_color, dtype=image.dtype)
    top = (new_h - height) // 2
    left = (new_w - width) // 2
    canvas[top : top + height, left : left + width] = image
    center = (new_w / 2.0, new_h / 2.0)
    matrix = cv2.getRotationMatrix2D(center, angle_deg, 1.0)
    return cv2.warpAffine(
        canvas,
        matrix,
        (new_w, new_h),
        flags=cv2.INTER_LINEAR,
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=border_color,
    )


__all__ = [
    "add_ring",
    "add_border_sides",
    "round_corners",
    "add_caption",
    "draw_border",
    "compose_drop_shadow",
    "shadow_offset",
    "drop_shadow_padding",
    "draw_drop_shadow",
    "rotate_with_pad",
]
