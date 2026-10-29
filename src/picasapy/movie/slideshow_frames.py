"""A diavetítés fotóinak metaadat-, arc- és felirat-előkészítése (#6173)."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

from picasapy.lazy_cv2 import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from picasapy.ini import IniDocument

if TYPE_CHECKING:
    from .slideshow import MovieSettings


def picasa_caption_core(
    path: Path,
    documents: dict[Path, IniDocument | None],
    *,
    ini_name: str,
    loader,
) -> str:
    """A kép `.picasa.ini`-beli felirata, az adott filmhez cache-elve."""
    ini_path = path.parent / ini_name
    if ini_path not in documents:
        try:
            documents[ini_path] = loader(ini_path)
        except OSError:
            # A felirat metaadat; olvasási hiba esetén az EXIF-tartalék marad.
            documents[ini_path] = None
    document = documents[ini_path]
    section = document.section(path.name) if document is not None else None
    return (section.get("caption") or "").strip() if section is not None else ""


def picasa_face_rectangles_core(
    path: Path,
    image: np.ndarray,
    documents: dict[Path, IniDocument | None],
    *,
    ini_name: str,
    loader,
    parse_faces_fn,
    rect64_to_pixel_rect_fn,
) -> tuple[tuple[np.float32, np.float32, np.float32, np.float32], ...]:
    """A fotó Picasa-féle rect64 arcait forrásképpontokra alakítja."""
    ini_path = path.parent / ini_name
    if ini_path not in documents:
        try:
            documents[ini_path] = loader(ini_path)
        except OSError:
            documents[ini_path] = None
    document = documents[ini_path]
    section = document.section(path.name) if document is not None else None
    if section is None:
        return ()
    height, width = image.shape[:2]
    result = []
    for face in parse_faces_fn(section.get("faces") or ""):
        if face.is_ignored:
            continue
        rectangle = rect64_to_pixel_rect_fn(face.rect, width, height)
        if rectangle[2] > rectangle[0] and rectangle[3] > rectangle[1]:
            result.append(rectangle)
    return tuple(result)


def prepare_face_frame_core(
    path: Path,
    image: np.ndarray,
    rectangle: tuple[float, float, float, float],
    settings: MovieSettings,
    ini_docs: dict[Path, IniDocument | None],
    *,
    render_face_crop_fn,
    caption_fn,
    annotate_fn,
) -> np.ndarray:
    """A dekódolt fotót a megadott arcra keretezi és feliratozza."""
    frame = render_face_crop_fn(
        image,
        rectangle,
        (settings.width, settings.height),
        cropfit=settings.cropfit,
        background=settings.background,
    )
    caption = caption_fn(path, ini_docs) if settings.show_captions else ""
    return annotate_fn(frame, path, settings, caption)


def _capture_timestamp(path: Path) -> float | None:
    """A kép készítési ideje EXIF-ből, ennek hiányában fájlidőből."""
    try:
        with Image.open(path) as photo:
            exif = photo.getexif()
            exif_values = exif
            try:
                exif_values = exif.get_ifd(34665) or exif
            except (AttributeError, KeyError, TypeError):
                pass
            raw_date = str(exif_values.get(36867) or exif.get(306) or "")
            if raw_date:
                return datetime.strptime(raw_date, "%Y:%m:%d %H:%M:%S").timestamp()
    except (OSError, ValueError, TypeError):
        pass
    try:
        return path.stat().st_mtime
    except OSError:
        return None


def fotofelirat_core(
    frame: np.ndarray,
    path: Path,
    settings: MovieSettings,
    picasa_caption: str = "",
) -> np.ndarray:
    """Az elérhető EXIF-feliratot/dátumot diszkrét alsó sávban mutatja."""
    if not settings.show_captions and not settings.show_dates:
        return frame
    caption = picasa_caption
    date = ""
    try:
        with Image.open(path) as photo:
            exif = photo.getexif()
            if not caption:
                caption = str(exif.get(270, "") or "").strip()
            exif_values = exif
            try:
                exif_values = exif.get_ifd(34665) or exif
            except (AttributeError, KeyError, TypeError):
                pass
            raw_date = str(exif_values.get(36867) or exif.get(306) or "")
            if raw_date:
                date = raw_date.replace(":", "-", 2)
    except (OSError, ValueError):
        pass
    if settings.show_dates and not date:
        try:
            date = datetime.fromtimestamp(path.stat().st_mtime).strftime("%Y-%m-%d")
        except OSError:
            date = ""
    sorok = [
        s
        for s in (caption if settings.show_captions else "", date if settings.show_dates else "")
        if s
    ]
    if not sorok:
        return frame
    image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    draw = ImageDraw.Draw(image, "RGBA")
    font = ImageFont.load_default()
    pad = max(6, settings.width // 80)
    box = draw.multiline_textbbox((0, 0), "\n".join(sorok), font=font, spacing=2)
    band_h = box[3] - box[1] + 2 * pad
    y0 = settings.height - band_h
    draw.rectangle((0, y0, settings.width, settings.height), fill=(0, 0, 0, 180))
    draw.multiline_text((pad, y0 + pad), "\n".join(sorok), font=font, fill="white", spacing=2)
    return cv2.cvtColor(np.asarray(image), cv2.COLOR_RGB2BGR)


def prepare_photo_frame_core(
    path: Path,
    settings: MovieSettings,
    ini_docs: dict[Path, IniDocument | None],
    *,
    decoder,
    crop_to_fit_fn,
    letterbox_fn,
    caption_fn,
    annotate_fn,
) -> np.ndarray:
    """Dekódolja és a filmvászonra készíti a fotót.

    Az export és az élő előnézet ugyanazt a vágást/letterboxot, hátteret,
    feliratot és dátumsávot használja. A `decoder` csak a kis felbontású
    előnézeti dekódert cseréli be; exportkor a teljes képkocka készül.
    """
    photo_path = Path(path)
    image = decoder(photo_path)
    frame = (
        crop_to_fit_fn(image, settings.width, settings.height)
        if settings.cropfit
        else letterbox_fn(image, settings.width, settings.height, settings.background)
    )
    caption = caption_fn(photo_path, ini_docs) if settings.show_captions else ""
    return annotate_fn(frame, photo_path, settings, caption)
