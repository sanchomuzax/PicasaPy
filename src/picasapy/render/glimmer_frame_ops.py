"""Keret-/árnyék-primitívek a Glimmer-effektekhez (#381) — a `glimmer_ops.py`
testvérmodulja, KÜLÖN fájlban, hogy egyik se lépje át a 800 soros korlátot.

`BorderImageOperation`, `DropShadow` és `Rotate(padBorder)` közös építőkövei:
szegélygyűrű, sarok-lekerekítés, felirat-sáv, vetett árnyék, kibővített
vászonra forgatás. Ezeket használja a `Border`, `RoundedEdges`,
`MuseumMatte`, `Sixties` (sarok-lekerekítés), `DropShadow` és `Polaroid`
csővezetéke (`glimmer_frames.py`).
"""

from __future__ import annotations

from picasapy import cv as cv2
import numpy as np

from picasapy.render.curves import validate_image
from picasapy.render.glimmer_ops import fade_alpha, gaussian_blur_f, to_float, to_uint8


def thickness_px(height: int, width: int, percent: float) -> int:
    """Százalék (0..100) → pixel, a kép rövidebb oldalára vetítve.

    #317 óta CSAK a `DropShadow` `Blur` paramétere használja (a szegély-
    vastagságok pixelben értendők, ld. `add_ring`) — ott nincs mért adat,
    ez marad a dokumentált közelítés.
    """
    return max(0, round(min(height, width) * percent / 100.0))


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


def compose_drop_shadow(
    image: np.ndarray,
    shadow_color: tuple[int, int, int],
    background_color: tuple[int, int, int],
    distance_px: int,
    angle: float,
    blur_px: int,
    margin: int,
    fade: float = 0.0,
) -> np.ndarray:
    """A `DropShadow` kompozitálása MÁR KISZÁMOLT pixel-paraméterekkel
    (elmosás-sugár, eltolás, vászon-margó) — a százalékos `draw_drop_shadow`
    és a Polaroid rögzített (pixelben megadott) árnyék-receptje közös magja
    (#1144). A hívó felel a `margin` helyes levezetéséért.
    """
    validate_image(image)
    height, width = image.shape[:2]
    canvas_h, canvas_w = height + margin * 2, width + margin * 2
    canvas = np.empty((canvas_h, canvas_w, 3), dtype=np.float32)
    canvas[:] = np.array(background_color, dtype=np.float32)

    angle_rad = np.deg2rad(angle)
    offset_x = int(round(distance_px * float(np.cos(angle_rad))))
    offset_y = int(round(distance_px * float(np.sin(angle_rad))))
    shadow_layer = np.zeros((canvas_h, canvas_w), dtype=np.float32)
    top = margin + offset_y
    left = margin + offset_x
    shadow_layer[top : top + height, left : left + width] = 1.0
    shadow_blurred = gaussian_blur_f(shadow_layer, blur_px)

    shadow_alpha = fade_alpha(fade)
    weight = np.clip(shadow_blurred * np.float32(shadow_alpha), 0.0, 1.0)
    shadow_color_arr = np.array(shadow_color, dtype=np.float32)
    canvas = canvas * (1.0 - weight[..., np.newaxis]) + shadow_color_arr * weight[..., np.newaxis]

    canvas[margin : margin + height, margin : margin + width] = to_float(image)
    return to_uint8(canvas)


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
    `distance`/`angle` szerint eltolva, `blur`-ral (0..100, a rövidebb oldal
    százalékában) elmosva, `shadowAlpha = fade_alpha(fade)` átlátszósággal.

    ⚠️ #1144/#626: ez a `blur`→pixel átváltás (rövidebb oldal százaléka,
    `margin = 2·blur_px + distance`) a Polaroid mérésén bizonyítottan HIBÁS
    modell — a valódi Flash-eredetű `DropShadowFilter`-ben a `blur` már
    PIXELBEN értendő, és a margó `blur_px + distance` (nincs duplázás). A
    Polaroid receptje ezért NEM ezt a függvényt hívja, hanem a
    `compose_drop_shadow` magot közvetlenül, kiszámolt pixel-margóval — az
    itteni százalékos modell (az önálló `DropShadow` effekt) javítása
    külön, nyitott jegy (#626), mert a `min`/`max` mérés ezzel a
    függvénnyel ELLENTMOND az egyszerű `blur_px + distance` képletnek.
    """
    validate_image(image)
    height, width = image.shape[:2]
    blur_px = max(1, thickness_px(height, width, blur))
    distance_px = int(round(distance))
    margin = blur_px * 2 + abs(distance_px)
    return compose_drop_shadow(
        image, shadow_color, background_color, distance_px, angle, blur_px, margin, fade
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
    "thickness_px",
    "add_ring",
    "add_border_sides",
    "round_corners",
    "add_caption",
    "draw_border",
    "compose_drop_shadow",
    "draw_drop_shadow",
    "rotate_with_pad",
]
