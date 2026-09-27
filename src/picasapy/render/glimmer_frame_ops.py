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


#: A lekerekített sarkok élsimítása: képpontonként `n × n` részminta — a
#: `border__max` exportját ezzel a modell ΔE 0,1 alatt adja vissza (#3768).
_SAROK_RESZMINTA = 4


def _sarok_fedes(sugar: int) -> np.ndarray:
    """`sugar × sugar`-es float32 fedés a BAL FELSŐ sarokhoz: a kör
    középpontja a négyzet jobb alsó csúcsa, `(sugar, sugar)`."""
    n = _SAROK_RESZMINTA
    reszek = (np.arange(n, dtype=np.float64) + 0.5) / n
    tav = sugar - (np.arange(sugar, dtype=np.float64)[:, None] + reszek[None, :]).reshape(-1)
    bent = (tav[:, None] ** 2 + tav[None, :] ** 2) <= float(sugar) ** 2
    return bent.reshape(sugar, n, sugar, n).mean(axis=(1, 3)).astype(np.float32)


def _sarok_folt(
    kep_sarok: np.ndarray,
    belso: int,
    outer_color: tuple[int, int, int],
    inner_color: tuple[int, int, int],
) -> np.ndarray:
    """A bal felső sarok `(R + belső)²`-es foltja: külső szín → a sáv
    `R + belső` sugarú íve belső színnel → a kép `R` sugarú íve."""
    sugar = kep_sarok.shape[0]
    sav_fedes = _sarok_fedes(sugar + belso)[..., np.newaxis]
    kulso = np.asarray(outer_color, dtype=np.float32)
    bel = np.asarray(inner_color, dtype=np.float32)
    alap = kulso * (1.0 - sav_fedes) + bel * sav_fedes
    kep_fedes = _sarok_fedes(sugar)[..., np.newaxis]
    kep_resz = alap[belso:, belso:] * (1.0 - kep_fedes) + kep_sarok.astype(np.float32) * kep_fedes
    folt = np.concatenate(
        [alap[:belso], np.concatenate([alap[belso:, :belso], kep_resz], axis=1)], axis=0
    )
    return np.clip(np.rint(folt), 0, 255).astype(np.uint8)


def draw_border(
    image: np.ndarray,
    outer_color: tuple[int, int, int],
    inner_color: tuple[int, int, int],
    outer_thickness: float,
    inner_thickness: float,
    corner_radius_px: float = 0.0,
    caption_height_px: float = 0.0,
) -> np.ndarray:
    """`BorderImageOperation` (a Border és a RoundedEdges közös motorja).

    Koncentrikus geometria (#3768, mérve a `border__max` exportján,
    `docs/specs/filterdesc-registry.md`): a vászon szögletes, külső színű;
    a belső sáv `R + belső` sugarú lekerekített téglalap belső színnel; a
    kép sarka `R` sugarú, a kimaradó rész alól a sáv látszik. `R = 0`
    mellett a sáv is szögletes (a `border__alap` exportján mérve). A
    feliratsáv a vászon alján, külső színnel; a magassága CSONKÍTOTT egész
    (`0x008eea90`).
    """
    validate_image(image)
    height, width = image.shape[:2]
    belso = max(0, int(round(inner_thickness)))
    kulso = max(0, int(round(outer_thickness)))
    felirat = max(0, int(caption_height_px))
    sugar = max(0, min(int(round(corner_radius_px)), height // 2, width // 2))
    keret = kulso + belso
    vaszon = np.empty((height + 2 * keret + felirat, width + 2 * keret, 3), dtype=image.dtype)
    vaszon[:] = np.asarray(outer_color, dtype=image.dtype)
    vaszon[kulso : kulso + height + 2 * belso, kulso : kulso + width + 2 * belso] = np.asarray(
        inner_color, dtype=image.dtype
    )
    vaszon[keret : keret + height, keret : keret + width] = image
    if sugar == 0:
        return vaszon
    meret = sugar + belso
    also = kulso + height + 2 * belso
    jobb = kulso + width + 2 * belso
    for fuggoleges, vizszintes in ((False, False), (False, True), (True, False), (True, True)):
        sor = slice(None, None, -1 if fuggoleges else 1)
        oszlop = slice(None, None, -1 if vizszintes else 1)
        kep_sor = slice(height - sugar, height) if fuggoleges else slice(0, sugar)
        kep_oszlop = slice(width - sugar, width) if vizszintes else slice(0, sugar)
        folt = _sarok_folt(image[kep_sor, kep_oszlop][sor, oszlop], belso, outer_color, inner_color)
        v_sor = slice(also - meret, also) if fuggoleges else slice(kulso, kulso + meret)
        v_oszlop = slice(jobb - meret, jobb) if vizszintes else slice(kulso, kulso + meret)
        vaszon[v_sor, v_oszlop] = folt[sor, oszlop]
    return vaszon


#: #649/#626/#3809: a `DropShadowImageOperation` árnyék-eltolása
#: (`0x00bcdea0`):
#:
#:     dx = floor( (cos(szög·π/180) + 6,7e−06) · távolság + 0,001825 )
#:     dy = floor( (sin(szög·π/180) + 6,7e−06) · távolság + 0,001825 )
#:
#: A két apró szám NEM paraméter, hanem lebegőpontos védelem: a 2,9999…
#: alakban kijövő, valójában egész szorzatot emeli az egész fölé, mielőtt a
#: `floor` lecsípné (`docs/specs/filterdesc-registry.md`, „A Polaroid
#: geometriája”).
_SHADOW_TIE_SLOPE = 6.7e-06
_SHADOW_TIE_OFFSET = 0.001825


def shadow_offset(distance_px: float, angle: float) -> tuple[int, int]:
    """Az árnyék (dx, dy) eltolása a natív képlettel (#649, #3809).

    A kerekítés `floor` (`0x00bcdece` `call 0x00c0b1e0`), nem C-`round`: a
    (távolság 0–30, szög 0–359°) párok 71%-ánál a kettő eltér — például az
    alapértelmezett 4 / 45°-nál `(2, 2)` a natív, nem `(3, 3)`. Tengelyirányú
    szögnél (0°, 90°, 180°, 270°) a kettő egybeesik.
    """
    radian = math.radians(angle)
    return (
        math.floor(
            (math.cos(radian) + _SHADOW_TIE_SLOPE) * distance_px
            + _SHADOW_TIE_OFFSET
        ),
        math.floor(
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


def teglalap_alfa(shadow_alpha: float) -> int:
    """Az árnyék-téglalap alfa-bájtja (#3498).

    A konstruktor a `shadowAlpha`-t `[0, 1]`-re vágja, és float32-ként tárolja
    (`0x00bcd654`–`0x00bcd68c`); a rajzoló 255-tel szoroz, majd a `fistp`
    ELŐTT a kerekítési módot nulla felé állítja (`0x00bcda7a`: `or 0xc00`).
    Az eredmény tehát CSONKOLT, nem kerekített érték.
    """
    vagott = float(np.float32(min(max(float(shadow_alpha), 0.0), 1.0)))
    return math.trunc(vagott * 255.0)


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
    # vászon `árnyékszín | alfa 0`, a téglalap `TRUNC(shadowAlpha · 255)`
    # alfával (#3498, `teglalap_alfa`). Az elmosás (`0x00bc5680`, quality=3: 3 vízszintes + 3
    # függőleges egész menet) az állandó RGB-t nem változtatja, tehát
    # gyakorlatilag csak az alfát mossa — ezért elég az alfa-csatorna.
    offset_x, offset_y = shadow_offset(distance_px, angle)
    top = fent + offset_y
    left = bal + offset_x
    alfa = np.zeros((canvas_h, canvas_w), dtype=np.uint8)
    alfa[top : top + height, left : left + width] = teglalap_alfa(fade_alpha(fade))
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


#: A mintavevő (`0x009e7060`) 16.16 fixpontban lép; a forrás képpontközepét
#: a `− 32767` (`add edx, 0xffff8001`) teszi az egész koordinátára.
_FIX_EGY = 65536
_FIX_FEL = 32767


def _fixpontos_bilinearis(
    image: np.ndarray, matrix: tuple[float, ...], cel_w: int, cel_h: int,
    border_color: tuple[int, int, int],
) -> np.ndarray:
    """A natív forgató mintavevő (`0x009e7060`, #3809) vektorosan.

    Soronként `U = fistp(u(x+0,5, y+0,5) · 65536) − 32767`, a lépés
    `fistp(m0 · 65536)`; `ix = U >> 16`, `fx = (U >> 8) & 0xFF`. A súly 8
    bites: `lerp(a, b, f) = a + floor((b − a)·f/256)`, előbb vízszintesen. A
    perem egy képpontos sávjában a kilógó szomszéd a szélső képpont; azon
    kívül a cél a `border_color` marad. (`fistp` = páros felé kerekítés,
    mint az `np.rint`.)
    """
    m0, m1, m2, m3, m4, m5 = matrix
    src_h, src_w = image.shape[:2]
    sor = np.arange(cel_h, dtype=np.float64) + 0.5
    oszlop = np.arange(cel_w, dtype=np.int64)
    u0 = np.rint((m0 * 0.5 + m1 * sor + m2) * _FIX_EGY).astype(np.int64) - _FIX_FEL
    v0 = np.rint((m3 * 0.5 + m4 * sor + m5) * _FIX_EGY).astype(np.int64) - _FIX_FEL
    u = u0[:, None] + oszlop[None, :] * int(np.rint(m0 * _FIX_EGY))
    v = v0[:, None] + oszlop[None, :] * int(np.rint(m3 * _FIX_EGY))
    ix, iy = u >> 16, v >> 16
    ervenyes = (ix >= -1) & (ix <= src_w - 1) & (iy >= -1) & (iy <= src_h - 1)
    ix, iy = ix[ervenyes], iy[ervenyes]
    fx = ((u[ervenyes] >> 8) & 0xFF)[:, None]
    fy = ((v[ervenyes] >> 8) & 0xFF)[:, None]
    x0, x1 = np.clip(ix, 0, src_w - 1), np.clip(ix + 1, 0, src_w - 1)
    y0, y1 = np.clip(iy, 0, src_h - 1), np.clip(iy + 1, 0, src_h - 1)
    forras = image.astype(np.int32)
    fent = forras[y0, x0] + (((forras[y0, x1] - forras[y0, x0]) * fx) >> 8)
    lent = forras[y1, x0] + (((forras[y1, x1] - forras[y1, x0]) * fx) >> 8)
    cel = np.empty((cel_h, cel_w, image.shape[2]), dtype=image.dtype)
    cel[:] = np.array(border_color, dtype=image.dtype)
    cel[ervenyes] = (fent + (((lent - fent) * fy) >> 8)).astype(image.dtype)
    return cel


def rotate_with_pad(
    image: np.ndarray, angle_deg: float, border_color: tuple[int, int, int]
) -> np.ndarray:
    """`Rotate(..., padBorder, borderColor=...)`: elforgatás a forgatott
    téglalap befoglaló méretű vásznára; az üresen maradó sarkokat
    `border_color` tölti ki.

    #3420: a szög a Picasa `RotateImageOperation degAngle`-je, és POZITÍV
    értéknél az óramutató JÁRÁSA szerint forgat (a 684-es Polaroid-exporton
    `Rotate = 5`-nél a keret felső éle jobbra lejt).

    #1144: a befoglaló méret `csonk(|W·cos θ| + |H·sin θ|)` ×
    `csonk(|W·sin θ| + |H·cos θ|)` (`0x00bc7ca0`) — a Polaroid `818×950`/
    `887×1004` mért kimenete csak így egyezik.

    #3809: a cél → forrás mátrix `T(sW/2, sH/2) · R · T(−dW/2, −dH/2)`
    (`0x00bc8060`), a képpont KÖZEPÉT vetíti vissza, tehát a forrás közepe
    pontosan a cél közepére esik. A mintavétel a natív 8 bites fixpontos
    bilineáris (`_fixpontos_bilinearis`). A korábbi út (a kép `//2`-vel a
    vászonra, majd OpenCV-sarok-konvenciós `warpAffine`) fél képpontokat
    tolt el, és a peremen a kitöltő színnel mosott össze.
    """
    validate_image(image)
    src_h, src_w = image.shape[:2]
    radian = math.radians(angle_deg)
    cos_a, sin_a = math.cos(radian), math.sin(radian)
    cel_w = int(math.floor(src_w * abs(cos_a) + src_h * abs(sin_a)))
    cel_h = int(math.floor(src_w * abs(sin_a) + src_h * abs(cos_a)))
    # cél → forrás: az óramutató szerinti forgatás inverze
    matrix = (
        cos_a, sin_a, src_w / 2.0 - cos_a * cel_w / 2.0 - sin_a * cel_h / 2.0,
        -sin_a, cos_a, src_h / 2.0 + sin_a * cel_w / 2.0 - cos_a * cel_h / 2.0,
    )
    return _fixpontos_bilinearis(image, matrix, cel_w, cel_h, border_color)


__all__ = [
    "add_ring",
    "add_border_sides",
    "round_corners",
    "draw_border",
    "compose_drop_shadow",
    "teglalap_alfa",
    "shadow_offset",
    "drop_shadow_padding",
    "draw_drop_shadow",
    "rotate_with_pad",
]
