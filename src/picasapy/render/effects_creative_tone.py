"""A Picasa 4. fülének (zöld ecset) kreatív effektjei — II. rész: HDR,
Invert, HeatMap, CrossProcess, QuantizePalette, TwoTone.

**ŐSZINTESÉG (#329):** ugyanaz a fenntartás érvényes, mint az
`picasapy.render.effects_creative` modulra — a Picasa e effektjeinek pontos
algoritmusa NEM publikus, ehhez NINCS golden-mérés. Az itt implementált
modellek a fotós/képfeldolgozási szakirodalomból ismert hatás-JELLEGET
közelítik (pl. mit csinál egy lokális kontraszt-kiemelés, egy poszterizálás
vagy egy duotone leképezés) — NEM állítjuk, hogy pixelhűen egyeznek a Picasa
kimenetével. A kalibráció (ha valaha lesz hozzá mérési adat) a #317-es jegy
feladata; addig ez a modul dokumentáltan KÖZELÍTÉS. Az `Invert` kivétel: a
színinvertálás (`ki = 255 − be`) matematikailag egyértelmű művelet, itt nincs
mit közelíteni.

Bemenet/kimenet: `uint8` RGB `numpy.ndarray` (H, W, 3) — a projekt render-
rétegének konvenciója (ld. `picasapy.render.curves.validate_image`). Minden
függvény TISZTA: új tömböt ad vissza, a bemenetet sosem mutálja.
"""

from __future__ import annotations

import cv2
import numpy as np

from picasapy.render.curves import (
    apply_channel_luts,
    blend_luts,
    curve_lut,
    lut_ramp,
    validate_image,
)

_REC601_WEIGHTS = (0.299, 0.587, 0.114)

# CrossProcess: csatornánkénti S-görbe töréspontjai — a keresztelőhívás
# jellemző jegyét (zöldes árnyék, kékes-sárgás felsőfény-eltolás) idézik;
# NEM mértek, csak a hatás JELLEGÉT rögzítik.
_CROSS_RED_POINTS = ((0.0, 12.0), (64.0, 58.0), (128.0, 150.0), (192.0, 215.0), (255.0, 248.0))
_CROSS_GREEN_POINTS = ((0.0, 0.0), (64.0, 50.0), (128.0, 132.0), (192.0, 200.0), (255.0, 255.0))
_CROSS_BLUE_POINTS = ((0.0, 25.0), (64.0, 42.0), (128.0, 100.0), (192.0, 165.0), (255.0, 225.0))


def _luma(image: np.ndarray) -> np.ndarray:
    """Rec.601 luminancia float32 (H, W) tömbként."""
    red_w, green_w, blue_w = _REC601_WEIGHTS
    return (
        np.float32(red_w) * image[..., 0].astype(np.float32)
        + np.float32(green_w) * image[..., 1].astype(np.float32)
        + np.float32(blue_w) * image[..., 2].astype(np.float32)
    )


def _to_uint8(values: np.ndarray) -> np.ndarray:
    return np.clip(np.rint(values), 0, 255).astype(np.uint8)


def _validate_color(color: tuple[int, int, int], name: str) -> None:
    if len(color) != 3 or any(not 0 <= component <= 255 for component in color):
        raise ValueError(f"A(z) {name} szín 3 elemű, 0..255 tartományú kell legyen: {color!r}")


def apply_hdr(
    image: np.ndarray,
    clip_limit: float = 2.0,
    tile_grid_size: int = 8,
    strength: float = 1.0,
) -> np.ndarray:
    """„HDR-szerű" lokális kontraszt-kiemelés — KÖZELÍTÉS (#329, #317).

    Modell: CLAHE (kontraszt-korlátozott adaptív hisztogram-kiegyenlítés) a
    LAB-térbeli L (világosság) csatornán, majd `strength` súllyal
    visszakeverve az eredetivel — ez a szokásos „HDR tone-mapping look"
    közelítése (helyi kontraszt kiemelése globális tónus-összenyomással),
    NEM a Picasa mért algoritmusa.
    """
    validate_image(image)
    if clip_limit <= 0:
        raise ValueError(f"A clip_limit pozitív kell legyen: {clip_limit}")
    if tile_grid_size < 1:
        raise ValueError(f"A csempeméret legalább 1 kell legyen: {tile_grid_size}")
    if not 0.0 <= strength <= 1.0:
        raise ValueError(f"Az erősség 0..1 tartományba kell essen: {strength}")
    lab = cv2.cvtColor(image, cv2.COLOR_RGB2LAB)
    lightness, red_axis, blue_axis = cv2.split(lab)
    clahe = cv2.createCLAHE(
        clipLimit=float(clip_limit), tileGridSize=(int(tile_grid_size), int(tile_grid_size))
    )
    equalized = clahe.apply(lightness)
    merged = cv2.merge((equalized, red_axis, blue_axis))
    enhanced = cv2.cvtColor(merged, cv2.COLOR_LAB2RGB)
    if strength >= 1.0:
        return enhanced
    if strength == 0.0:
        return image.copy()
    image_f = image.astype(np.float32)
    blended = image_f + np.float32(strength) * (enhanced.astype(np.float32) - image_f)
    return _to_uint8(blended)


def apply_invert(image: np.ndarray) -> np.ndarray:
    """Színinvertálás: `ki = 255 − be` — pontos művelet, nincs közelítés."""
    validate_image(image)
    return cv2.bitwise_not(image)


def apply_heatmap(image: np.ndarray, blend: float = 1.0) -> np.ndarray:
    """Hőtérkép hamis-szín leképezés — KÖZELÍTÉS (#329, kalibráció: #317).

    Modell: a Rec.601 luminancia leképezése `COLORMAP_JET` hamis-szín
    palettával (a hőkamera-képek megszokott kék→zöld→sárga→piros
    átmenete), `blend` súllyal keverve az eredetivel. A konkrét paletta és
    a keverési arány itt megválasztott, NEM mért Picasa-érték.
    """
    validate_image(image)
    if not 0.0 <= blend <= 1.0:
        raise ValueError(f"A keverési súly 0..1 tartományba kell essen: {blend}")
    gray = _to_uint8(_luma(image))
    colored_bgr = cv2.applyColorMap(gray, cv2.COLORMAP_JET)
    colored_rgb = cv2.cvtColor(colored_bgr, cv2.COLOR_BGR2RGB)
    if blend >= 1.0:
        return colored_rgb
    if blend == 0.0:
        return image.copy()
    image_f = image.astype(np.float32)
    colored_f = colored_rgb.astype(np.float32)
    return _to_uint8(image_f + np.float32(blend) * (colored_f - image_f))


def apply_crossprocess(image: np.ndarray, strength: float = 1.0) -> np.ndarray:
    """Keresztelőhívás (cross-process) — KÖZELÍTÉS (#329, kalibráció: #317).

    Modell: csatornánként ELTÉRŐ S-görbe (töréspontos LUT, `strength`
    súllyal az identitás felé keverve) — a vegyi keresztelőhívás jellemző,
    csatornánként aszimmetrikus kontraszt- és színeltolását idézi. A
    töréspontok NEM mértek, csak a hatás JELLEGÉT (zöldes árnyék, kékes-
    sárgás felsőfény) rögzítik.
    """
    validate_image(image)
    if not 0.0 <= strength <= 1.0:
        raise ValueError(f"Az erősség 0..1 tartományba kell essen: {strength}")
    ramp = lut_ramp()
    lut_r = blend_luts(ramp, curve_lut(_CROSS_RED_POINTS), strength)
    lut_g = blend_luts(ramp, curve_lut(_CROSS_GREEN_POINTS), strength)
    lut_b = blend_luts(ramp, curve_lut(_CROSS_BLUE_POINTS), strength)
    return apply_channel_luts(image, (lut_r, lut_g, lut_b))


def apply_quantizepalette(image: np.ndarray, levels: int = 4) -> np.ndarray:
    """Színszám-csökkentés (poszterizálás) — KÖZELÍTÉS (#329, kalibráció: #317).

    Modell: csatornánként egyenletes lépésközű kvantálás
    (`levels` szint 0..255 között), a klasszikus poszterizáló szűrők
    szokásos definíciója. A Picasa `QuantizePalette` pontos (esetleg
    palettaválasztó, nem egyenletes) algoritmusa NEM ismert — ez a
    legegyszerűbb, jellegre illő közelítés.
    """
    validate_image(image)
    if not isinstance(levels, int) or levels < 2:
        raise ValueError(f"A szintszám legalább 2 egész szám kell legyen: {levels!r}")
    if levels > 256:
        raise ValueError(f"A szintszám legfeljebb 256 lehet: {levels}")
    if levels == 256:
        return image.copy()
    image_f = image.astype(np.float32)
    scale = np.float32(255.0 / (levels - 1))
    quantized = np.rint(np.rint(image_f / scale) * scale)
    return np.clip(quantized, 0, 255).astype(np.uint8)


def apply_twotone(
    image: np.ndarray,
    shadow_color: tuple[int, int, int] = (10, 10, 40),
    highlight_color: tuple[int, int, int] = (255, 225, 140),
) -> np.ndarray:
    """Kéttónusú (duotone) leképezés — KÖZELÍTÉS (#329, kalibráció: #317).

    Modell: a Rec.601 luminancia [0..1]-re normálva lineárisan
    interpolál a `shadow_color` (sötét) és a `highlight_color` (világos)
    között — a nyomdai duotone-eljárás digitális közelítése. A Picasa
    alapértelmezett színpárja NEM ismert, itt megválasztott érték.
    """
    validate_image(image)
    _validate_color(shadow_color, "shadow_color")
    _validate_color(highlight_color, "highlight_color")
    gray = (_luma(image) / np.float32(255.0))[..., np.newaxis]
    shadow = np.array(shadow_color, dtype=np.float32)
    highlight = np.array(highlight_color, dtype=np.float32)
    return _to_uint8(shadow + gray * (highlight - shadow))
