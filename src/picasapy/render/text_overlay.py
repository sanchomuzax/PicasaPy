"""Szöveg-overlay rajzolása képre (#148/#450).

**Szándékosan ELVÁLASZTVA** a `picasapy.ini.text_overlay` nyers `text=`
mezőitől: a valódi Picasa `text=` kulcs `raw_x`/`raw_y` számpárjának
jelentése nem megerősített (ld. az ini-modul docsztringjét), ezért ez a
függvény NEM ezekből számol pozíciót — a hívó explicit, relatív [0..1]
koordinátákat ad át. Ez PicasaPy-saját, dokumentált konvenció: amíg nincs
golden-minta a valódi `text=` mezők jelentésére, ez az egyetlen módja, hogy
a szöveg-eszköz determinisztikusan, találgatás nélkül működjön.

**A rajzoló (#450, 2. lépcső): TrueType, ha van.** A Pillow FreeType-útján
rajzolunk — ez adja a betűcsaládot, a félkövéret/dőltet, az aláhúzást és a
sorok igazítását, amit az OpenCV Hershey-készlete nem tud. Ha a gépen
egyetlen használható TrueType sincs, a régi Hershey-út fut tovább, hogy a
szöveg-eszköz sose essen ki — ilyenkor a stílus-vezérlők hatástalanok, a
szöveg viszont megjelenik.

A betűcsaládok leképezése (Arial → Liberation Sans stb.) a
`render.text_fonts` dolga; a `font` ini-mező továbbra is csak MEGŐRZŐDIK
(round-trip), mert a `text=` kulcs betűtípus-mezőjének pontos jelentése
nincs igazolva (#371).
"""

from __future__ import annotations

import cv2
import numpy as np
from PIL import Image, ImageDraw

from picasapy.render.curves import validate_image
from picasapy.render.text_fonts import DEFAULT_FAMILY, load_font

_FONT = cv2.FONT_HERSHEY_SIMPLEX
_LINE_TYPE = cv2.LINE_AA


#: A `font_scale` (a Hershey-út egysége) és a TrueType-pontméret közti
#: leképezés. A Hershey `SIMPLEX` nagybetű-magassága `font_scale`-enként
#: kb. 22 képpont, ezért ez a szorzó tartja meg a MEGLÉVŐ hívók látszólagos
#: méretét a rajzoló cseréje után is.
_SCALE_TO_PIXELS = 30

#: A sorok igazítása — a Picasa szöveg-eszközének három gombja.
_ALIGNMENTS = ("left", "center", "right")


def _size_px_for(font_scale: float) -> int:
    return max(1, round(font_scale * _SCALE_TO_PIXELS))


def _draw_hershey(
    base, content, origin, font_scale, color, thickness,
    outline_color, outline_thickness, fill_enabled, has_outline,
):
    """A RÉGI út: OpenCV Hershey-fontkészlet — akkor fut, ha a gépen nincs
    használható TrueType. A stílus-vezérlők ilyenkor hatástalanok."""
    layer = base.copy()
    if has_outline:
        cv2.putText(
            layer, content, origin, _FONT, font_scale, outline_color,
            thickness + 2 * outline_thickness, _LINE_TYPE,
        )
    if fill_enabled:
        cv2.putText(
            layer, content, origin, _FONT, font_scale, color, thickness, _LINE_TYPE
        )
    return layer


def _draw_truetype(
    base, content, origin, font, color, outline_color, outline_thickness,
    fill_enabled, has_outline, underline, align,
):
    """A TrueType-út (#450): betűcsalád, félkövér/dőlt, aláhúzás, igazítás.

    A Pillow RGB-ben dolgozik, a lánc viszont a projekt konvenciója szerint
    a hívó színrendjében kap képet — a színeket ezért NEM forgatjuk meg, a
    tömböt viszont igen, hogy a Pillow ugyanazokat a csatornákat lássa.
    """
    pil = Image.fromarray(base)
    draw = ImageDraw.Draw(pil)
    # a `putText` a bal ALSÓ sarokra rajzol, a Pillow a bal FELSŐRE — az
    # `ls` horgonnyal a két konvenció egybeesik (ld. Pillow anchor-doksi)
    anchor = {"left": "ls", "center": "ms", "right": "rs"}[align]
    if has_outline:
        draw.text(
            origin, content, font=font, fill=tuple(outline_color),
            anchor=anchor, align=align,
            stroke_width=outline_thickness, stroke_fill=tuple(outline_color),
        )
    if fill_enabled:
        draw.text(
            origin, content, font=font, fill=tuple(color),
            anchor=anchor, align=align,
        )
    if underline:
        _draw_underline(draw, origin, content, font, anchor,
                        color if fill_enabled else outline_color)
    return np.array(pil)


def _draw_underline(draw, origin, content, font, anchor, colour) -> None:
    """Aláhúzás: a TrueType-ben ez nem külön betűváltozat, hanem rajzolt
    vonal — a szöveg tényleges dobozának alján, a betűvastagsághoz mért
    magassággal."""
    left, _top, right, bottom = draw.textbbox(
        origin, content, font=font, anchor=anchor
    )
    # a vonal vastagsága a betűmérethez skálázódik (a szokásos tipográfiai
    # arány), és legalább egy képpont
    line_height = max(1, round(font.size / 14))
    y = bottom + line_height
    draw.rectangle((left, y, right, y + line_height - 1), fill=tuple(colour))


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
    font_family: str = DEFAULT_FAMILY,
    bold: bool = False,
    italic: bool = False,
    underline: bool = False,
    align: str = "left",
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
    if align not in _ALIGNMENTS:
        raise ValueError(f"Ismeretlen igazítás: {align!r}")
    height, width = image.shape[:2]
    origin = (round(x * width), round(y * height))
    font = load_font(
        font_family, _size_px_for(font_scale), bold=bold, italic=italic
    )
    if font is None:
        layer = _draw_hershey(
            result, content, origin, font_scale, color, thickness,
            outline_color, outline_thickness, fill_enabled, has_outline,
        )
    else:
        layer = _draw_truetype(
            result, content, origin, font, color, outline_color,
            outline_thickness, fill_enabled, has_outline, underline, align,
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
