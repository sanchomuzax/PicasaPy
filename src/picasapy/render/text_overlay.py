"""Szöveg-overlay rajzolása képre (#148) — cv2.putText alapú KÖZELÍTÉS.

**Szándékosan ELVÁLASZTVA** a `picasapy.ini.text_overlay` nyers `text=`
mezőitől: a valódi Picasa `text=` kulcs `raw_x`/`raw_y` számpárjának
jelentése nem megerősített (ld. az ini-modul docsztringjét), ezért ez a
függvény NEM ezekből számol pozíciót — a hívó explicit, relatív [0..1]
koordinátákat ad át. Ez PicasaPy-saját, dokumentált konvenció: amíg nincs
golden-minta a valódi `text=` mezők jelentésére, ez az egyetlen módja, hogy
a szöveg-eszköz determinisztikusan, találgatás nélkül működjön.

A betűtípus-leképezés is közelítés: OpenCV a Hershey-fontkészletet
használja, ami vizuálisan NEM egyezik a Picasa TrueType-betűtípusaival
(pl. `Aharoni`) — a `font` mező jelenleg csak MEGŐRZŐDIK (round-trip), a
rajzoláshoz egységes Hershey-alapfontot használunk.
"""

from __future__ import annotations

import cv2
import numpy as np

from picasapy.render.curves import validate_image

_FONT = cv2.FONT_HERSHEY_SIMPLEX
_LINE_TYPE = cv2.LINE_AA


def apply_text_overlay(
    image: np.ndarray,
    content: str,
    x: float,
    y: float,
    *,
    font_scale: float = 1.0,
    color: tuple[int, int, int] = (255, 255, 255),
    thickness: int = 2,
) -> np.ndarray:
    """Szöveg ráírása a képre.

    `x`, `y`: relatív [0..1] pozíció — a szöveg BAL ALSÓ sarka (OpenCV
    `putText`-konvenció) kerül ide. Üres `content`-nél no-op (a bemenet
    másolata). A `font_scale`/`thickness` nem lehet negatív.
    """
    validate_image(image)
    if not 0.0 <= x <= 1.0 or not 0.0 <= y <= 1.0:
        raise ValueError(f"x/y a [0..1] tartományon kívül: x={x}, y={y}")
    if font_scale <= 0:
        raise ValueError(f"A font_scale pozitív kell legyen: {font_scale}")
    if thickness <= 0:
        raise ValueError(f"A thickness pozitív kell legyen: {thickness}")
    result = image.copy()
    if not content:
        return result
    height, width = image.shape[:2]
    origin = (round(x * width), round(y * height))
    cv2.putText(
        result, content, origin, _FONT, font_scale, color, thickness, _LINE_TYPE
    )
    return result
