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
    outline_color: tuple[int, int, int] | None = None,
    outline_thickness: int = 0,
    fill_enabled: bool = True,
    opacity: float = 1.0,
) -> np.ndarray:
    """Szöveg ráírása a képre — kitöltés + opcionális körvonal (#450).

    `x`, `y`: relatív [0..1] pozíció — a szöveg BAL ALSÓ sarka (OpenCV
    `putText`-konvenció) kerül ide. Üres `content`-nél no-op (a bemenet
    másolata). A `font_scale`/`thickness` nem lehet negatív.

    A körvonal (#450 — „a legfeltűnőbb hiány", tetszőleges hátterű képen
    olvasható felirathoz) a szöveg ELŐSZÖR `outline_color` színnel, a
    `thickness`-nél `2 * outline_thickness`-szel vastagabb vonallal kerül a
    képre, UTÁNA (ha `fill_enabled`) a `color` kitöltő szín rajzolódik rá,
    a normál `thickness`-szel — így a körvonal a kitöltés körül keretként
    látszik. `outline_thickness <= 0` esetén nincs körvonal (ez az
    alapérték — a meglévő hívók viselkedése változatlan). `fill_enabled
    =False` esetén ("Don't show the solid fill color (show outline
    only)") csak a körvonal marad; ha emellett nincs érvényes körvonal
    sem (`outline_thickness <= 0` vagy `outline_color is None`), a hívás
    no-op (semmi nem rajzolódik).

    Az `opacity` [0..1] — a rajzolt szöveg (kitöltés+körvonal együtt)
    alfa-keverése az EREDETI képpel, de KIZÁRÓLAG a szöveg által ténylegesen
    érintett képpontokon (a rajzolt réteg és az eredeti kép közti eltérés
    maszkolja ezt) — a kép többi képpontja `opacity` értékétől függetlenül
    bitre pontosan változatlan marad.
    """
    validate_image(image)
    if not 0.0 <= x <= 1.0 or not 0.0 <= y <= 1.0:
        raise ValueError(f"x/y a [0..1] tartományon kívül: x={x}, y={y}")
    if font_scale <= 0:
        raise ValueError(f"A font_scale pozitív kell legyen: {font_scale}")
    if thickness <= 0:
        raise ValueError(f"A thickness pozitív kell legyen: {thickness}")
    if outline_thickness < 0:
        raise ValueError(
            f"Az outline_thickness nem lehet negatív: {outline_thickness}"
        )
    if not 0.0 <= opacity <= 1.0:
        raise ValueError(f"Az opacity a [0..1] tartományon kívül: {opacity}")
    result = image.copy()
    if not content:
        return result
    has_outline = outline_color is not None and outline_thickness > 0
    if not fill_enabled and not has_outline:
        # se kitöltés, se körvonal — nincs mit rajzolni
        return result
    height, width = image.shape[:2]
    origin = (round(x * width), round(y * height))
    layer = result.copy()
    if has_outline:
        cv2.putText(
            layer,
            content,
            origin,
            _FONT,
            font_scale,
            outline_color,
            thickness + 2 * outline_thickness,
            _LINE_TYPE,
        )
    if fill_enabled:
        cv2.putText(
            layer, content, origin, _FONT, font_scale, color, thickness, _LINE_TYPE
        )
    changed = np.any(layer != result, axis=-1)
    if not changed.any():
        return result
    if opacity >= 1.0:
        result[changed] = layer[changed]
    else:
        blended = cv2.addWeighted(layer, opacity, result, 1.0 - opacity, 0.0)
        result[changed] = blended[changed]
    return result
