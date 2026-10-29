"""JPEG-kódolás, minőségátvétel és vízjel az exportban."""

from __future__ import annotations

import io
from pathlib import Path

from picasapy.lazy_cv2 import cv2
import numpy as np
from PIL import Image, ImageDraw, UnidentifiedImageError

from picasapy.render.flip import FLIP_MASK
from picasapy.render.text_fonts import DEFAULT_FAMILY, load_font

from .export_models import ExportItem
from .export_settings import ExportSettings


# A bájthű (no-op) másolás csak valódi JPEG-forrásra alkalmazható — más
# formátumot mindenképp JPEG-be kell kódolni (meglévő viselkedés).
_JPEG_EXTENSIONS = frozenset({".jpg", ".jpeg"})

def _first_frame(source: Path) -> np.ndarray | None:
    """A videó ELSŐ olvasható képkockája BGR tömbként, vagy `None` (#1166).

    Az eredeti „Első képkocka" választása ezt teszi a mappába a film
    helyett. A ThumbnailCache időkorlátos, elszigetelt dekóderét használja,
    így az export és a bélyegkép ugyanazt a videóképkocka-kinyerést kapja.
    Olvashatatlan felvételnél a hívó a teljes film másolására esik vissza."""
    # Lusta import: a bélyegkép-dekóder csak videó első-kockás exportnál
    # kell, ne növelje a normál export indulási költségét.
    from picasapy.thumbs.cache import _decode_video_frame_isolated

    try:
        frame = _decode_video_frame_isolated(source)
        return frame if frame is not None and frame.size else None
    except (OSError, ValueError):
        return None


def _encode_jpeg(
    image: np.ndarray, settings: ExportSettings, source: Path | None
) -> bytes:
    """A kirenderelt kép JPEG-bájtjai.

    Az „Automatikus" fokozatnál (#1138, #4017) a FORRÁS JPEG kvantálási
    tábláival és mintavételezésével kódolunk. Más fokozatoknál a mért
    minőséghez tartozó táblát és a fokozat saját mintavételezését használjuk."""
    if settings.quality_automatic and source is not None:
        payload = _encode_with_source_qtables(image, source)
        if payload is not None:
            return payload
    try:
        rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        puffer = io.BytesIO()
        Image.fromarray(rgb).save(
            puffer,
            format="JPEG",
            quality=settings.jpeg_quality,
            subsampling=settings.jpeg_subsampling,
        )
    except (OSError, ValueError, TypeError, cv2.error) as exc:
        raise ValueError(f"JPEG-kódolás sikertelen: {source}") from exc
    return puffer.getvalue()


def _source_jpeg_parameters(source: Path) -> tuple[dict, int] | None:
    """A forrás JPEG kvantálási táblái és mintája, vagy `None`.

    Sosem dob: nem JPEG, sérült vagy olvashatatlan forrásnál `None` —
    a hívó ilyenkor a minőségszámos ágra esik vissza."""
    try:
        with Image.open(source) as kep:
            if kep.format != "JPEG":
                return None
            tablak = dict(kep.quantization)
            subsampling = _subsampling_from_layer(kep.layer)
    except (OSError, ValueError, UnidentifiedImageError):
        return None
    if not tablak or subsampling is None:
        return None
    return tablak, subsampling


def _encode_with_source_qtables(image: np.ndarray, source: Path) -> bytes | None:
    """Kódolás a forrás kvantálási tábláival (#1138), vagy `None`, ha nem
    megy — a hívó ilyenkor a szokásos úton kódol.

    A Pillow a beolvasott `quantization` szótárat `qtables=`-ként
    változtatás nélkül visszaveszi, tehát a kimenet DQT-je bájtra a
    forrásé lesz."""
    parameters = _source_jpeg_parameters(source)
    if parameters is None:
        return None
    tablak, subsampling = parameters
    try:
        rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        puffer = io.BytesIO()
        Image.fromarray(rgb).save(
            puffer,
            format="JPEG",
            qtables=tablak,
            subsampling=subsampling,
        )
    except (OSError, ValueError, TypeError, cv2.error):
        return None
    return puffer.getvalue()


def _subsampling_from_layer(layer) -> int | None:
    """Pillow `Image.layer` komponensfaktoraiból JPEG-módot olvas ki."""
    try:
        components = tuple(layer)
        if len(components) not in (1, 3, 4):
            return None
        _y_id, y_h, y_v, _y_table = components[0]
        chroma_sampling = tuple(
            (h, v) for _id, h, v, _table in components[1:]
        )
        if any(factor != (1, 1) for factor in chroma_sampling):
            return None
    except (TypeError, ValueError):
        return None
    return {(1, 1): 0, (2, 1): 1, (2, 2): 2}.get((y_h, y_v))


def _is_noop_copy(
    source: Path,
    item: ExportItem,
    settings: ExportSettings,
) -> bool:
    """Nincs mit beégetni: se forgatás, se tükrözés (#3977), se átméretezés,
    se szerkesztés, se vízjel — és a forrás már JPEG. Ilyenkor a sima másolás a helyes (bájthű,
    mtime-őrző); a sorszámozás (#369) csak a fájlnevet érinti, a bájthű
    másolást nem zárja ki. A nem üres nyers `filters=` láncot akkor is
    újrakódoljuk, ha a renderelés egyes vagy összes tagot kihagy: az eredeti
    Picasa ilyenkor is új JPEG-et ír, és a metaadatoknak is le kell futniuk
    (#3997, #4017)."""
    return (
        source.suffix.lower() in _JPEG_EXTENSIONS
        and item.rotate_steps % 4 == 0
        and not int(item.flip_flags or 0) & FLIP_MASK
        and settings.max_dimension is None
        and not settings.watermark_text
        and not item.filters
        and not item.taken_at_override
    )


# #1603: a vízjel geometriai szabályai a `0x0045c4b0` dekompilálásából
# (955 bájt; hívja: `CPreparedDBImage` a `0x007948c0`-n, a `0x0045c430`-on
# át). Az állítás, hogy ezek a paraméterek „nem rekonstruálhatók" — MEGDŐLT.
#: 32 képpontnál ALACSONYABB MAGASSÁGÚ (nem a szélesség — ld. `cmp ecx,
#: 0x20` az `[esi+0xc]` = magasság mezőn) képre nem kerül vízjel; az
#: eredeti ilyenkor a 4-es hibakóddal tér vissza.
_WATERMARK_MIN_HEIGHT = 32
#: A betűméret alsó korlátja (`mov ebx, 0xc`), hogy nagyon kis képen se
#: legyen a felirat olvashatatlanul apró.
_WATERMARK_MIN_FONT_SIZE = 12
#: A betűméretet a kép HOSSZABB oldalából adja, egész osztással
#: (`0x51eb851f`-es szorzó + `shr edx, 4` ≡ osztás 50-nel).
_WATERMARK_FONT_DIVISOR = 50
#: A mérés (#1603) átlátszatlan fehéret mutatott (`0xffffffff`,
#: `[esp+0x88]`) — ez a jegy leggyengébb (bár „erős") bizonyítékú
#: állítása, mert a `0xFFFFFFFF` elméletileg „nincs színkulcs" jelölő is
#: lehetne. Egy windowsos referencia-export döntené el megnyugtatóan
#: (a kérdés a jegyben BLOKKOLTKÉNT szerepel); addig a mért értéket
#: (átlátszatlan, nincs alfa-keverés) visszük át — ez a korábbi
#: `alpha = 0.6` közelítést váltja fel.
_WATERMARK_COLOR = (255, 255, 255)


def _watermark_font_size_px(width: int, height: int) -> int:
    """A vízjel betűmérete képpontban (#1603): a kép HOSSZABB oldalából,
    egész osztással 50-nel, de legalább 12 képpont."""
    return max(_WATERMARK_MIN_FONT_SIZE, max(width, height) // _WATERMARK_FONT_DIVISOR)


def _apply_watermark(
    image: np.ndarray, text: str | None, *, font_loader=load_font
) -> np.ndarray:
    """A vízjelszöveg beégetése a jobb alsó sarokba (#369, pontosítva #1603).

    A paraméterek a Picasa `0x0045c4b0` függvényéből visszafejtettek:
    Arial, 600-as vastagság (félkövér), méretezés 1.0; betűméret =
    `max(12, hosszabb oldal // 50)` képpont; a margó mind a négy oldalon a
    betűmérettel egyenlő, ezért a szöveg jobb éle és alsó (leszálló) éle a
    `(szélesség - betűméret, magasság - betűméret)` pontra esik. 32
    képpontnál alacsonyabb MAGASSÁGÚ képre nem kerül vízjel (az eredeti
    ilyenkor a 4-es hibakóddal tér vissza — itt a kép egyszerűen
    változatlan marad). Üres/`None` szöveg esetén szintén nincs változás.

    Ha a gépen nincs használható TrueType-betű (pl. csupasz CI-kép), a
    rajzolás Hershey-visszaesésre vált (ld. `render.text_fonts.load_font`)
    — a méret/elhelyezés szabályai ilyenkor is érvényben maradnak, csak a
    betű ALAKJA közelítő, nem az eredeti Arial."""
    if not text:
        return image
    height, width = image.shape[:2]
    if height < _WATERMARK_MIN_HEIGHT:
        return image
    size = _watermark_font_size_px(width, height)
    margin = size
    anchor = (width - margin, height - margin)
    font = font_loader(DEFAULT_FAMILY, size, bold=True)
    if font is not None:
        pil_image = Image.fromarray(image)
        draw = ImageDraw.Draw(pil_image)
        # "rd" = jobb (right) + leszálló (descender) horgony: a szöveg
        # jobb és alsó éle pontosan az `anchor`-ra esik, ahogy a
        # dekompilált margó-számítás (jobb = szélesség-betűméret, alsó =
        # magasság-betűméret) is mutatja.
        draw.text(anchor, text, font=font, fill=_WATERMARK_COLOR, anchor="rd")
        return np.asarray(pil_image)
    # Hershey-visszaesés: nincs TrueType a gépen. A DUPLEX vaskosabb
    # vonala közelebb áll a 600-as vastagsághoz, mint a vékony SIMPLEX; a
    # méretezés a betűméret cél-nagybetű-magasságára hangolt.
    font_face = cv2.FONT_HERSHEY_DUPLEX
    font_scale = size / 22
    thickness = max(1, round(font_scale * 2))
    (text_width, _text_height), baseline = cv2.getTextSize(
        text, font_face, font_scale, thickness
    )
    origin = (anchor[0] - text_width, anchor[1] - baseline)
    result = image.copy()
    cv2.putText(
        result, text, origin, font_face, font_scale, _WATERMARK_COLOR,
        thickness, cv2.LINE_AA,
    )
    return result
