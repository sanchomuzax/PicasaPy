"""A kollázs három képkerete + a háttérkép tompítása (#431).

Forrás: `docs/specs/picasa-create-features.md` 1.9.5 — a számok a
dekompilált Picasából valók, nem becslések.

| keret | szabály |
|---|---|
| Polaroid | külső = `foto * (1.145, 1.374)`, margó = `fotoSzélesség * 0.0725`, papír `#D9D9D9` |
| Fehér szegély | `b = round(min(szél, mag) * 0.05)`, szín `#EEEEEE` (**nem** tiszta fehér) |
| Nincs szegély | csak a kép |
| tompított | fényerő −0,15, kontraszt 1,0 (háttérképre) |

A színek szürkék, ezért az RGB és a BGR sorrend egybeesik — a konstansokat
mégis BGR-ként nevezzük el, mert az OpenCV így várja őket.

Immutabilitás: minden függvény ÚJ tömböt ad vissza, a bemenetet sosem írja.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .fitting import picasa_round
from .themes import BORDER_THEMES, NOBORDER, POLAROID, WHITEBORDER

# --- A dekompilált konstansok -----------------------------------------------

POLAROID_WIDTH_RATIO = 1.145
POLAROID_HEIGHT_RATIO = 1.374
POLAROID_MARGIN_RATIO = 0.0725  # = (1.145 − 1) / 2
POLAROID_PAPER_BGR = (217, 217, 217)  # 0xFFD9D9D9

WHITE_BORDER_RATIO = 0.05  # a RÖVIDEBB oldal 5%-a
WHITE_BORDER_BGR = (238, 238, 238)  # 0xFFEEEEEE

DIM_BRIGHTNESS = -0.15  # a 0…1 skálán (0xbe19999a)
DIM_CONTRAST = 1.0  # (0x3f800000)


@dataclass(frozen=True)
class PolaroidGeometry:
    """A polaroid-lap méretei és a fotó helye rajta.

    A `caption_height` az alul MARADÓ sáv — ide kerül a képfelirat. Nem
    külön számolt érték: a magasság-arányból adódik, ezért nagyon széles
    fotónál el is fogyhat (a Picasa a kollázsban közel négyzetes kivágást
    tesz a polaroid-keretbe, így ez a gyakorlatban nem fordul elő)."""

    outer_width: int
    outer_height: int
    margin: int
    photo_x: int
    photo_y: int
    caption_height: int


def polaroid_geometry(photo_width: int, photo_height: int) -> PolaroidGeometry:
    """A polaroid-keret geometriája egy adott méretű fotóhoz.

    ⚠️ A margót a fotó **szélessége** adja (nem a rövidebb oldala) — ez
    eltér a fehér szegélytől, és könnyű elnézni."""
    if photo_width < 1 or photo_height < 1:
        raise ValueError(f"Érvénytelen fotóméret: {photo_width}×{photo_height}")
    outer_width = picasa_round(photo_width * POLAROID_WIDTH_RATIO)
    outer_height = picasa_round(photo_height * POLAROID_HEIGHT_RATIO)
    margin = picasa_round(photo_width * POLAROID_MARGIN_RATIO)
    # a fotó balról, jobbról és FELÜLRŐL margónyira; a maradék alul a felirat sávja
    outer_width = max(outer_width, photo_width + 2 * margin)
    outer_height = max(outer_height, photo_height + margin)
    return PolaroidGeometry(
        outer_width=outer_width,
        outer_height=outer_height,
        margin=margin,
        photo_x=margin,
        photo_y=margin,
        caption_height=outer_height - margin - photo_height,
    )


def white_border_width(width: int, height: int) -> int:
    """A fehér szegély vastagsága: a **rövidebb** oldal 5%-a."""
    if width < 1 or height < 1:
        raise ValueError(f"Érvénytelen képméret: {width}×{height}")
    return picasa_round(min(width, height) * WHITE_BORDER_RATIO)


def _framed_canvas(
    height: int, width: int, color: tuple[int, int, int], dtype
) -> np.ndarray:
    return np.full((height, width, 3), np.array(color, dtype=dtype), dtype=dtype)


def _polaroid(image: np.ndarray) -> np.ndarray:
    photo_height, photo_width = image.shape[:2]
    geometry = polaroid_geometry(photo_width, photo_height)
    canvas = _framed_canvas(
        geometry.outer_height, geometry.outer_width, POLAROID_PAPER_BGR, image.dtype
    )
    canvas[
        geometry.photo_y : geometry.photo_y + photo_height,
        geometry.photo_x : geometry.photo_x + photo_width,
    ] = image
    return canvas


def _white_border(image: np.ndarray) -> np.ndarray:
    height, width = image.shape[:2]
    border = white_border_width(width, height)
    if border < 1:
        return image.copy()
    canvas = _framed_canvas(
        height + 2 * border, width + 2 * border, WHITE_BORDER_BGR, image.dtype
    )
    canvas[border : border + height, border : border + width] = image
    return canvas


def apply_border(image: np.ndarray, theme: str) -> np.ndarray:
    """A képkeret ráhúzása; ÚJ tömböt ad vissza.

    `theme` a `themes.BORDER_THEMES` egyike. A képfelirat rajzolása nem itt
    történik: a hívó a `polaroid_geometry()`-ből tudja meg, hova férhet
    (és a felirat **csak** a polaroid keretnél jelenik meg)."""
    if image.ndim != 3 or image.shape[2] != 3:
        raise ValueError("A képkerethez háromcsatornás kép kell.")
    if theme == NOBORDER:
        return image.copy()
    if theme == WHITEBORDER:
        return _white_border(image)
    if theme == POLAROID:
        return _polaroid(image)
    raise ValueError(f"Ismeretlen képkeret: {theme!r} (várt: {BORDER_THEMES})")


def dim_for_background(image: np.ndarray) -> np.ndarray:
    """A háttérként használt kép tompítása (`DimmedBitmapTheme`).

    Fényerő −0,15 a 0…1 skálán (= −38,25 a 0…255-ösön), kontraszt 1,0 —
    a rátett képek így olvashatók maradnak a háttér előtt."""
    adjusted = image.astype(np.float32) * DIM_CONTRAST + DIM_BRIGHTNESS * 255.0
    # `+0.5` majd csonkolás = felfelé kerekítés a félnél, mint a `picasa_round`
    return np.clip(adjusted + 0.5, 0.0, 255.0).astype(np.uint8)


__all__ = [
    "DIM_BRIGHTNESS",
    "DIM_CONTRAST",
    "NOBORDER",
    "POLAROID",
    "POLAROID_HEIGHT_RATIO",
    "POLAROID_MARGIN_RATIO",
    "POLAROID_PAPER_BGR",
    "POLAROID_WIDTH_RATIO",
    "PolaroidGeometry",
    "WHITEBORDER",
    "WHITE_BORDER_BGR",
    "WHITE_BORDER_RATIO",
    "apply_border",
    "dim_for_background",
    "polaroid_geometry",
    "white_border_width",
]
