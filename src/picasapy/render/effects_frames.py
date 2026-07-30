"""A Picasa 5. fülének (kék ecset) művészi effektjei — II. rész: a keretes,
MÉRETNÖVELŐ effektek (Border, DropShadow, MuseumMatte, Polaroid).

**ŐSZINTESÉG (#330):** ld. `effects_artistic.py` modul-docstringjét — ugyanaz
az őszinteségi elv érvényes: nincs golden-mérés ezekhez az effektekhez, a
paraméterek jelentése nem dekódolt, a modellek dokumentáltan KÖZELÍTÉSEK
(kalibráció: #317).

**FIGYELEM — MÉRETVÁLTOZÁS:** a modul mind a NÉGY függvénye (`apply_border`,
`apply_drop_shadow`, `apply_museum_matte`, `apply_polaroid`) NAGYOBB képet ad
vissza, mint a bemenet (keretet/paszpartut/árnyék-margót tesz köré) — ez
eltér a modul többi (és a `render/effects.py`, `render/ops.py` stb.) függ-
vényétől, amik a bemenettel AZONOS alakú kimenetet adnak. Ennek a
renderláncra, a bélyegkép-gyorsítótárra és az exportra van hatása:

- a renderlánc nem feltételezheti, hogy a kép alakja (H, W) a lánc végéig
  változatlan marad, ha ezek közül bármelyik szerepel benne;
- a bélyegkép-gyorsítótár kulcsának/méretének figyelembe kell vennie, hogy
  a keretes effekt utáni kép nagyobb, mint az eredeti (más gyorsítótár-
  bejegyzés kell, ha az effekt be-/kikapcsol);
- az export a MEGNÖVELT méretet írja ki, nem az eredeti fotóét.

Bemenet/kimenet: `uint8` RGB `numpy.ndarray` (H, W, 3) — a projekt render-
rétegének konvenciója (ld. `picasapy.render.curves.validate_image`). Minden
függvény TISZTA: új tömböt ad vissza, a bemenetet sosem mutálja.
"""

from __future__ import annotations

import cv2
import numpy as np

from picasapy.render.curves import validate_image

# Polaroid: az alsó sáv ennyiszer szélesebb, mint az oldalsó/felső keret —
# a klasszikus polaroid-fotó arányának KÖZELÍTÉSE, nincs hozzá mért adat.
_POLAROID_BOTTOM_MULTIPLIER = 3.0

# MuseumMatte: a belső vékony vonal vastagsága a paszpartu szélességének
# hányadaként — KÖZELÍTÉS.
_MUSEUM_MATTE_LINE_THICKNESS_RATIO = 0.03


def _border_pixels(image: np.ndarray, width_percent: float) -> int:
    """A keret/paszpartu vastagsága px-ben: `width_percent`% a rövidebb oldalból."""
    height, wid = image.shape[:2]
    return max(0, round(min(height, wid) * width_percent / 100.0))


def apply_border(
    image: np.ndarray, width: float = 20.0, color: tuple[int, int, int] = (255, 255, 255)
) -> np.ndarray:
    """Szegély (Border): egyszínű keret a kép köré.

    **MEGNÖVELI A KÉP MÉRETÉT** — ld. a modul-docstring figyelmeztetését. A
    kimenet alakja `(H + 2·border_px, W + 2·border_px, 3)`, ahol
    `border_px = round(width% · min(H, W))`.

    KÖZELÍTŐ MODELL (#330, kalibráció: #317). `width` 0..100, a keret
    vastagsága a kép rövidebb oldalának százalékában (a
    `Border=1,20.000000,...` minta szerint az alapérték 20). `color` a
    keret színe (alapból fehér, a minta `00ffffff` paraméterének
    megfelelően).
    """
    validate_image(image)
    if width < 0:
        raise ValueError(f"A keret szélessége nem lehet negatív: {width}")
    if len(color) != 3:
        raise ValueError(f"A szín 3 elemű (R, G, B) kell legyen: {color!r}")
    border_px = _border_pixels(image, width)
    if border_px == 0:
        return image.copy()
    return cv2.copyMakeBorder(
        image, border_px, border_px, border_px, border_px, cv2.BORDER_CONSTANT, value=color
    )


def apply_drop_shadow(
    image: np.ndarray,
    border_width: float = 4.0,
    angle: float = 90.0,
    blur: float = 10.0,
    shadow_color: tuple[int, int, int] = (0, 0, 0),
    border_color: tuple[int, int, int] = (255, 255, 255),
    opacity: float = 30.0,
) -> np.ndarray:
    """Árnyékvetés (DropShadow): keret + elmosott vetett árnyék.

    **MEGNÖVELI A KÉP MÉRETÉT** — ld. a modul-docstring figyelmeztetését. A
    kimenet a bekeretezett képnél is nagyobb (a vetett árnyék elmosási
    margójával).

    KÖZELÍTŐ MODELL (#330, kalibráció: #317) — a
    `DropShadow=1,4.000000,90.000000,10.000000,00000000,00ffffff,30.000000;`
    minta paramétereinek jelentése (csúszka-leképezés) nem dekódolt.
    `border_width` 0..100 a keret vastagsága (mint `apply_border`), `angle`
    fokban az árnyék eltolási iránya (0° = jobbra, 90° = lefelé), `blur`
    0..100 az árnyék elmosásának mértéke (a kép rövidebb oldalának
    százalékában), `opacity` 0..100 az árnyék átlátszatlansága. A háttér
    (paszpartu) színe `border_color`.
    """
    validate_image(image)
    if border_width < 0:
        raise ValueError(f"A keret szélessége nem lehet negatív: {border_width}")
    if blur < 0:
        raise ValueError(f"Az elmosás mértéke nem lehet negatív: {blur}")
    if not 0.0 <= opacity <= 100.0:
        raise ValueError(f"Az átlátszatlanság 0..100 tartományba kell essen: {opacity}")
    bordered = apply_border(image, border_width, border_color)
    inner_h, inner_w = bordered.shape[:2]
    blur_px = max(1, round(min(inner_h, inner_w) * blur / 100.0))
    margin = blur_px * 2
    canvas_h, canvas_w = inner_h + margin * 2, inner_w + margin * 2

    canvas = np.empty((canvas_h, canvas_w, 3), dtype=np.float32)
    canvas[:] = np.array(border_color, dtype=np.float32)

    angle_rad = np.deg2rad(angle)
    offset_x = round(blur_px * float(np.cos(angle_rad)))
    offset_y = round(blur_px * float(np.sin(angle_rad)))
    shadow_layer = np.zeros((canvas_h, canvas_w), dtype=np.float32)
    top = margin + offset_y
    left = margin + offset_x
    shadow_layer[top : top + inner_h, left : left + inner_w] = 1.0
    shadow_blurred = cv2.GaussianBlur(shadow_layer, (0, 0), blur_px)

    alpha = np.clip(shadow_blurred * np.float32(opacity / 100.0), 0.0, 1.0)
    shadow_color_arr = np.array(shadow_color, dtype=np.float32)
    canvas = canvas * (1.0 - alpha[..., np.newaxis]) + shadow_color_arr * alpha[..., np.newaxis]

    canvas[margin : margin + inner_h, margin : margin + inner_w] = bordered.astype(np.float32)
    return np.clip(np.rint(canvas), 0, 255).astype(np.uint8)


def apply_museum_matte(
    image: np.ndarray,
    width: float = 25.0,
    line_position: float = 40.0,
    line_color: tuple[int, int, int] = (3, 14, 26),
    mat_color: tuple[int, int, int] = (228, 234, 240),
) -> np.ndarray:
    """Múzeumi matt (MuseumMatte): széles paszpartu, belső vékony vonallal.

    **MEGNÖVELI A KÉP MÉRETÉT** — ld. a modul-docstring figyelmeztetését. A
    kimenet alakja `(H + 2·mat_px, W + 2·mat_px, 3)`, ahol
    `mat_px = round(width% · min(H, W))`.

    KÖZELÍTŐ MODELL (#330, kalibráció: #317) — a
    `MuseumMatte=1,25.000000,40.000000,001a0e03,00f0eae4;` minta
    paramétereinek jelentése nem dekódolt. `width` 0..100 a paszpartu
    szélessége a kép rövidebb oldalának százalékában (alapérték 25),
    `line_position` 0..100 azt adja meg, hogy a vékony vonal a paszpartu
    szélességén belül milyen távol fut a kép belső élétől (alapérték 40).
    `line_color`/`mat_color` a vonal, ill. a paszpartu színe (az ini-minta
    `001a0e03`/`00f0eae4` hexértékeiből).
    """
    validate_image(image)
    if width < 0:
        raise ValueError(f"A paszpartu szélessége nem lehet negatív: {width}")
    if not 0.0 <= line_position <= 100.0:
        raise ValueError(f"A vonal pozíciója 0..100 tartományba kell essen: {line_position}")
    mat_px = _border_pixels(image, width)
    if mat_px == 0:
        return image.copy()
    canvas = cv2.copyMakeBorder(
        image, mat_px, mat_px, mat_px, mat_px, cv2.BORDER_CONSTANT, value=mat_color
    )
    canvas_h, canvas_w = canvas.shape[:2]

    line_offset = min(mat_px, max(1, round(mat_px * line_position / 100.0)))
    line_thickness = max(1, round(mat_px * _MUSEUM_MATTE_LINE_THICKNESS_RATIO))
    top = max(0, mat_px - line_offset)
    bottom = min(canvas_h, canvas_h - (mat_px - line_offset))
    left = max(0, mat_px - line_offset)
    right = min(canvas_w, canvas_w - (mat_px - line_offset))

    line_color_arr = np.array(line_color, dtype=canvas.dtype)
    canvas[top : top + line_thickness, left:right] = line_color_arr
    canvas[bottom - line_thickness : bottom, left:right] = line_color_arr
    canvas[top:bottom, left : left + line_thickness] = line_color_arr
    canvas[top:bottom, right - line_thickness : right] = line_color_arr
    return canvas


def apply_polaroid(
    image: np.ndarray, border_width: float = 5.0, color: tuple[int, int, int] = (226, 226, 226)
) -> np.ndarray:
    """Polaroid: fehéres keret a kép köré, alul jóval szélesebb sávval.

    **MEGNÖVELI A KÉP MÉRETÉT** — ld. a modul-docstring figyelmeztetését. A
    kimenet alakja `(H + side_px + bottom_px, W + 2·side_px, 3)` — a
    magasság-növekmény ASZIMMETRIKUS (az alsó sáv szélesebb), ez eltér a
    `apply_border`/`apply_museum_matte` szimmetrikus keretétől.

    KÖZELÍTŐ MODELL (#330, kalibráció: #317) — a
    `Polaroid=1,5.000000,00e2e2e2;` minta paramétereinek jelentése nem
    dekódolt. `border_width` 0..100 az oldalsó/felső keret szélessége a kép
    rövidebb oldalának százalékában (alapérték 5); az alsó sáv ennek
    `_POLAROID_BOTTOM_MULTIPLIER`-szerese (klasszikus polaroid-arány
    KÖZELÍTÉS, nincs hozzá mért adat). `color` a keret színe (alapból
    világosszürke, a minta `00e2e2e2` hexértékéből).
    """
    validate_image(image)
    if border_width < 0:
        raise ValueError(f"A keret szélessége nem lehet negatív: {border_width}")
    if len(color) != 3:
        raise ValueError(f"A szín 3 elemű (R, G, B) kell legyen: {color!r}")
    side_px = _border_pixels(image, border_width)
    bottom_px = round(side_px * _POLAROID_BOTTOM_MULTIPLIER)
    if side_px == 0 and bottom_px == 0:
        return image.copy()
    return cv2.copyMakeBorder(
        image, side_px, bottom_px, side_px, side_px, cv2.BORDER_CONSTANT, value=color
    )
