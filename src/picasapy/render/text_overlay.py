"""Szöveg-overlay rajzolása képre (#148/#450).

**Szándékosan ELVÁLASZTVA** a `picasapy.ini.text_overlay` `text=` mezőitől:
ez a függvény nem ini-adatot vesz át, hanem explicit, relatív [0..1]
koordinátákat — így a rajzoló önmagában, ini nélkül is tesztelhető.

A `text=` geometria-mezője (#371-ben megfejtve) UGYANEBBEN a normalizált
[0..1] egységben adja a pozíciót, ezért a hívó (`app.edit_controller`) ma
közvetlenül átadhatja. A geometria `méret` mezője viszont a Picasa saját
betűrajzolójára vonatkozik, a mi `font_scale`-ünk pedig a Hershey/FreeType
útra — a kettő leképezése nincs mérve, ezért a méret ma NEM köti a
rajzolót.

**A rajzoló (#450, 2. lépcső): TrueType, ha van.** A Pillow FreeType-útján
rajzolunk — ez adja a betűcsaládot, a félkövéret/dőltet, az aláhúzást és a
sorok igazítását, amit az OpenCV Hershey-készlete nem tud. Ha a gépen
egyetlen használható TrueType sincs, a régi Hershey-út fut tovább, hogy a
szöveg-eszköz sose essen ki — ilyenkor a stílus-vezérlők hatástalanok, a
szöveg viszont megjelenik.

A betűcsaládok leképezése (Arial → Liberation Sans stb.) a
`render.text_fonts` dolga. A `text=` betűtípus-mezője a betűtípus TELJES
neve (#371: `Arial`, `Bickham Script Pro Regular`) — ezt beolvasva
MEGŐRIZZÜK, de a rajzolót ma nem köti: a Picasa Windows-os betűkészletére
hivatkozik, aminek a Linuxos megfelelője gépenként más.
"""

from __future__ import annotations

import math

from picasapy.lazy_cv2 import cv2
import numpy as np
from PIL import Image, ImageDraw

from picasapy.render.curves import validate_image
from picasapy.render.text_fonts import DEFAULT_FAMILY, load_font, qt_font_for

# #1611: a két Hershey-konstans a HASZNÁLAT helyén olvasódik ki, nem
# modulszinten — modulszinten a `cv2.X` a BETÖLTÉSKOR behozná az OpenCV-t,
# és a `text_overlay` az indulási láncban van (`app/edit_controller` →
# `app/edit_preview` → `render/text_overlay`).


#: A `font_scale` (a Hershey-út egysége) és a TrueType-pontméret közti
#: leképezés. A Hershey `SIMPLEX` nagybetű-magassága `font_scale`-enként
#: kb. 22 képpont, ezért ez a szorzó tartja meg a MEGLÉVŐ hívók látszólagos
#: méretét a rajzoló cseréje után is.
_SCALE_TO_PIXELS = 30

#: A sorok igazítása — a Picasa szöveg-eszközének három gombja.
_ALIGNMENTS = ("left", "center", "right")


def _size_px_for(font_scale: float) -> int:
    """A régi, kép-független út — tartalék (#2287).

    Csak akkor fut, ha a hívó NEM ad `font_size_pt`-t; a szerkesztő ma
    mindig ad. Megtartva, hogy a `font_scale`-t használó régebbi hívók
    (és a saját próbáink) változatlanul működjenek.
    """
    return max(1, round(font_scale * _SCALE_TO_PIXELS))


def betumeret_keppontban(font_size_pt: float, kep_magassag: int) -> int:
    """A listaértékből képpont — az EREDETI képlete (#2287).

    A `0x005b35a0` utasításról utasításra: `érték × (magasság ÷ 360)`; a
    `360.0` a `0xcf3d50`-en. A kép magassága tehát nem esik ki: ugyanaz a
    felirat nagyobb képen arányosan nagyobb.

    Ez zárja be a kört a tárolással: az író `méret ÷ magasság`-ot tárol
    (#2271), ezért a `.picasa.ini`-ben `érték ÷ 360` áll — de a
    RAJZOLÁSHOZ vissza kell szorozni a magassággal.
    """
    return max(1, round(float(font_size_pt) * kep_magassag / 360.0))


def _draw_hershey(
    base, content, origin, font_scale, color, thickness,
    outline_color, outline_thickness, fill_enabled, has_outline,
):
    """A RÉGI út: OpenCV Hershey-fontkészlet — akkor fut, ha a gépen nincs
    használható TrueType. A stílus-vezérlők ilyenkor hatástalanok.

    #7380: az `origin` a szövegdoboz FELSŐ sarka; a `putText` alapvonalat
    kér, ezért az y-t a nagybetű-magassággal toljuk lejjebb.
    """
    layer = base.copy()
    (_szelesseg, betumagassag), _alap = cv2.getTextSize(
        content, cv2.FONT_HERSHEY_SIMPLEX, font_scale, thickness
    )
    origin = (origin[0], origin[1] + betumagassag)
    if has_outline:
        cv2.putText(
            layer, content, origin, cv2.FONT_HERSHEY_SIMPLEX, font_scale,
            outline_color,
            thickness + 2 * outline_thickness, cv2.LINE_AA,
        )
    if fill_enabled:
        cv2.putText(
            layer, content, origin, cv2.FONT_HERSHEY_SIMPLEX, font_scale,
            color, thickness, cv2.LINE_AA,
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
    # #7380: az `origin` a szövegdoboz FELSŐ sarka (az eredeti Picasa
    # `text=` pozíciója) — az `la`/`ma`/`ra` horgony az ascender-vonalat
    # (a sor tetejét) teszi a pontra, a betűk tehát a pont ALATT állnak
    anchor = {"left": "la", "center": "ma", "right": "ra"}[align]
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


def _draw_qt_font(
    base, content, origin, font, color, outline_color, outline_thickness,
    fill_enabled, has_outline, align,
):
    """A Qt által kiválasztott rendszer-betűcsaládot rajzolja a képre."""
    from PySide6.QtCore import QPointF
    from PySide6.QtGui import (
        QColor,
        QFontMetricsF,
        QImage,
        QPainter,
        QPainterPath,
        QPen,
    )

    height, width = base.shape[:2]
    contiguous = np.ascontiguousarray(base)
    qimage = QImage(
        contiguous.data,
        width,
        height,
        int(contiguous.strides[0]),
        QImage.Format.Format_RGB888,
    ).copy()
    painter = QPainter(qimage)
    # #7432: a festőt kivétel esetén is le kell zárni, különben a megtartott
    # traceback miatt a kép a festő ELŐTT szabadul fel (szegmenshiba)
    try:
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        text_width = QFontMetricsF(font).horizontalAdvance(content)
        x = float(origin[0])
        if align == "center":
            x -= text_width / 2
        elif align == "right":
            x -= text_width
        # #7380: az `origin` a szövegdoboz FELSŐ sarka; a `QPainterPath.addText`
        # az ALAPVONALAT kéri, ami a sor tetejétől az ascent-nyire van
        alapvonal = float(origin[1]) + QFontMetricsF(font).ascent()
        path = QPainterPath()
        path.addText(QPointF(x, alapvonal), font, content)
        if has_outline:
            pen = QPen(QColor(*map(int, outline_color)))
            pen.setWidthF(max(1.0, float(outline_thickness)))
            painter.strokePath(path, pen)
        if fill_enabled:
            painter.fillPath(path, QColor(*map(int, color)))
    finally:
        painter.end()

    raw = np.frombuffer(
        qimage.bits(), dtype=np.uint8, count=qimage.sizeInBytes()
    ).reshape(height, qimage.bytesPerLine())
    return raw[:, : width * 3].reshape(height, width, 3).copy()


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


def _text_box_size(content: str, qt_font, pillow_font, font_scale: float) -> tuple[float, float]:
    """A forgatáshoz szükséges szövegdoboz-méret az aktív betűút szerint."""
    lines = content.splitlines() or [""]
    if qt_font is not None:
        from PySide6.QtGui import QFontMetricsF

        metrics = QFontMetricsF(qt_font)
        return (
            max(metrics.horizontalAdvance(line) for line in lines),
            metrics.lineSpacing() * len(lines),
        )
    if pillow_font is not None:
        bounds = [pillow_font.getbbox(line, anchor="la") for line in lines]
        return (
            max(right - left for left, _top, right, _bottom in bounds),
            max(bottom - top for _left, top, _right, bottom in bounds)
            * len(lines),
        )
    meret, _ = cv2.getTextSize(
        max(lines, key=len), cv2.FONT_HERSHEY_SIMPLEX, font_scale, 2
    )
    return float(meret[0]), float(meret[1] * len(lines))


def apply_text_overlay(
    image: np.ndarray,
    content: str,
    x: float,
    y: float,
    *,
    font_scale: float = 1.0,
    #: #2287: a választott listaérték (8…96). Ha meg van adva, EZ dönt,
    #: és a méret a kép magasságából számolódik — a `font_scale` csak
    #: a régebbi hívók tartalék-útja.
    font_size_pt: float | None = None,
    color: tuple[int, int, int] = (255, 255, 255),
    thickness: int = 2,
    outline_color: tuple[int, int, int] | None = None,
    outline_thickness: int = 0,
    fill_enabled: bool = True,
    opacity: float = 1.0,
    rotation: float = 0.0,
    font_family: str = DEFAULT_FAMILY,
    bold: bool = False,
    italic: bool = False,
    underline: bool = False,
    align: str = "left",
) -> np.ndarray:
    """Szöveg ráírása a képre — kitöltés + opcionális körvonal (#450).

    `x`, `y`: relatív képkoordináta: a szövegdoboz BAL FELSŐ sarka kerül
    ide (#7380: az eredeti Picasa `text=` pozíciója; a betűk a pont ALATT
    állnak, a bal szél a ponton). Üres `content`-nél no-op (a bemenet
    másolata). A `font_scale`/`thickness` nem lehet negatív.
    Elforgatásnál a tárolt befoglaló sarok kilóghat a képből; a rajzolás
    ilyenkor a kép határánál levágódik.

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
    if not math.isfinite(x) or not math.isfinite(y):
        raise ValueError(f"x/y csak véges szám lehet: x={x}, y={y}")
    if not math.isfinite(rotation):
        raise ValueError(f"A rotation csak véges szám lehet: {rotation}")
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
    # #2287: ha a hívó a listaértéket adja, a méret a KÉP MAGASSÁGÁBÓL
    # számolódik (az eredeti képlete); `font_size_pt` nélkül a régi,
    # kép-független tartalék-út fut.
    meret_px = (
        betumeret_keppontban(font_size_pt, height)
        if font_size_pt is not None
        else _size_px_for(font_scale)
    )
    qt_font = qt_font_for(
        font_family,
        meret_px,
        bold=bold,
        italic=italic,
        underline=underline,
    )
    center = None
    if rotation:
        pillow_font = None
        if qt_font is None:
            pillow_font = load_font(
                font_family, meret_px, bold=bold, italic=italic
            )
        text_width, text_height = _text_box_size(
            content, qt_font, pillow_font, meret_px / _SCALE_TO_PIXELS
        )
        theta = float(rotation)
        rotated_width = (
            text_width * abs(math.cos(theta))
            + text_height * abs(math.sin(theta))
        )
        rotated_height = (
            text_width * abs(math.sin(theta))
            + text_height * abs(math.cos(theta))
        )
        center = (
            origin[0] + rotated_width / 2,
            origin[1] + rotated_height / 2,
        )
        box_left = center[0] - text_width / 2
        if align == "center":
            origin_x = center[0]
        elif align == "right":
            origin_x = center[0] + text_width / 2
        else:
            origin_x = box_left
        origin = (round(origin_x), round(center[1] - text_height / 2))
    if qt_font is not None:
        layer = _draw_qt_font(
            result,
            content,
            origin,
            qt_font,
            color,
            outline_color,
            outline_thickness,
            fill_enabled,
            has_outline,
            align,
        )
    else:
        font = load_font(font_family, meret_px, bold=bold, italic=italic)
        if font is None:
            layer = _draw_hershey(
                result, content, origin, meret_px / _SCALE_TO_PIXELS, color,
                thickness, outline_color, outline_thickness, fill_enabled,
                has_outline,
            )
        else:
            layer = _draw_truetype(
                result, content, origin, font, color, outline_color,
                outline_thickness, fill_enabled, has_outline, underline, align,
            )
    if center is not None:
        delta = layer.astype(np.float32) - result.astype(np.float32)
        matrix = cv2.getRotationMatrix2D(
            center, -math.degrees(float(rotation)), 1.0
        )
        delta = cv2.warpAffine(
            delta,
            matrix,
            (width, height),
            flags=cv2.INTER_LINEAR,
            borderMode=cv2.BORDER_CONSTANT,
            borderValue=0,
        )
        layer = np.clip(result.astype(np.float32) + delta, 0, 255).astype(
            np.uint8
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
