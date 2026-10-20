"""Az arcfilm klipjének keretezése a Picasa `0x00813c50` képlete szerint."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from picasapy.lazy_cv2 import cv2
from picasapy.ini.rect64 import Rect64

# `0x00cf48f8`: a float32(0.499) érték double-ként tárolva.
_DELTA = float(np.float32(0.499))
# `0x00cf4160`: külön double konstans, csak a végső ROUND-hoz.
_ROUND_BIAS = 0.499
_LOW_RES_FACE_WIDTH = 136.5
_MAX_ZOOM = np.float32(1.2999999523162842)


@dataclass(frozen=True)
class FaceCropGeometry:
    """A mérőfüggvény kimeneti téglalapja és a képkockához szükséges skálák."""

    source_rectangle: tuple[np.float32, np.float32, np.float32, np.float32]
    rectangle: tuple[np.float32, np.float32, np.float32, np.float32]
    rounded_rectangle: tuple[int, int, int, int]
    scale: np.float32
    zoom: np.float32
    fit_offset: tuple[int, int]


def rect64_to_pixel_rect(
    rect64: Rect64 | tuple[int, int, int, int],
    image_width: int,
    image_height: int,
) -> tuple[np.float32, np.float32, np.float32, np.float32]:
    """Rect64-koordinátát alakít Picasa-pixel dwordökké.

    A Picasa 65535.0-val osztott, float32 skálát használ, nem az ini
    round-trip API 65536-os normalizálását. A konverzió után az x87
    `FISTP`-jének alapértelmezett, legközelebbi egészre kerekítését követjük.
    """
    if image_width < 1 or image_height < 1:
        raise ValueError("A forráskép mérete pozitív legyen.")
    if isinstance(rect64, Rect64):
        coords = tuple(
            round(float(value) * 65536)
            for value in (rect64.left, rect64.top, rect64.right, rect64.bottom)
        )
    else:
        coords = tuple(int(value) for value in rect64)
    if len(coords) != 4 or any(value < 0 or value > 65535 for value in coords):
        raise ValueError("A rect64 négy 16 bites koordinátából áll.")

    scale_x = np.float32(image_width / 65535.0)
    scale_y = np.float32(image_height / 65535.0)
    scaled = (
        round(float(np.float32(np.float32(coords[0]) * scale_x))),
        round(float(np.float32(np.float32(coords[1]) * scale_y))),
        round(float(np.float32(np.float32(coords[2]) * scale_x))),
        round(float(np.float32(np.float32(coords[3]) * scale_y))),
    )
    left = min(max(0, scaled[0]), image_width - 1)
    top = min(max(0, scaled[1]), image_height - 1)
    right = min(max(1, scaled[2]), image_width)
    bottom = min(max(1, scaled[3]), image_height)
    if right <= left:
        right = min(image_width, left + 1)
    if bottom <= top:
        bottom = min(image_height, top + 1)
    return tuple(np.float32(value) for value in (left, top, right, bottom))  # type: ignore[return-value]


def face_is_usable(
    rectangle: tuple[float, float, float, float], *, remove_low_res_faces: bool
) -> bool:
    """A `removelowresfaces` opció 136,5 px alatti arcot hagy ki."""
    if not remove_low_res_faces:
        return True
    width = np.float32(np.float32(rectangle[2]) - np.float32(rectangle[0]))
    return bool(np.isfinite(width) and width >= _LOW_RES_FACE_WIDTH)


def calculate_face_crop(
    face_rectangle: tuple[float, float, float, float],
    *,
    source_size: tuple[int, int],
    viewport_size: tuple[int, int],
    cropfit: bool,
    crop_rect: tuple[float, float, float, float] | None = None,
) -> FaceCropGeometry:
    """A `0x00813c50` arc-téglalapját számolja, float32 lépésekkel.

    A visszaadott `rectangle` a face AOI-téglalapja a kezdeti, középre
    igazított képskálán, a zoommal bővítve; ez a bináris által visszaadott
    négyes. A `crop_rect` opcionális, teljes kép hiányában a forrás teljes
    téglalapját használjuk.
    """
    source_width, source_height = (int(value) for value in source_size)
    viewport_width, viewport_height = (int(value) for value in viewport_size)
    if min(source_width, source_height, viewport_width, viewport_height) < 1:
        raise ValueError("A forrás és a filmvászon mérete pozitív legyen.")

    f32 = np.float32
    left, top, right, bottom = (f32(value) for value in face_rectangle)
    left = f32(max(f32(0), left))
    top = f32(max(f32(0), top))
    right = f32(min(f32(source_width), right))
    bottom = f32(min(f32(source_height), bottom))

    if crop_rect is None:
        crop_left, crop_top, crop_right, crop_bottom = (
            f32(0), f32(0), f32(source_width), f32(source_height)
        )
    else:
        crop_left, crop_top, crop_right, crop_bottom = (
            f32(value) for value in crop_rect
        )
        crop_left = f32(max(f32(0), crop_left))
        crop_top = f32(max(f32(0), crop_top))
        crop_right = f32(min(f32(source_width), crop_right))
        crop_bottom = f32(min(f32(source_height), crop_bottom))
    left = f32(max(left, crop_left))
    top = f32(max(top, crop_top))
    right = f32(min(right, crop_right))
    bottom = f32(min(bottom, crop_bottom))
    if right <= left or bottom <= top:
        raise ValueError("Az arc és a forrás crop-téglalapja nem metszi egymást.")
    source_rectangle = (left, top, right, bottom)

    # A két képarányt double pontosságú osztással számoljuk, majd a bináris
    # lebegőpontos tárolóregiszterének megfelelően float32-re kerekítjük.
    width_ratio = (viewport_width + _DELTA) / source_width
    height_ratio = (viewport_height + _DELTA) / source_height
    scale = f32(max(width_ratio, height_ratio) if cropfit else min(width_ratio, height_ratio))

    scaled_width = f32(scale * f32(source_width))
    scaled_height = f32(scale * f32(source_height))
    offset_x = round((viewport_width - float(scaled_width)) / 2)
    offset_y = round((viewport_height - float(scaled_height)) / 2)

    x0 = f32(f32(left * scale) + f32(offset_x))
    y0 = f32(f32(top * scale) + f32(offset_y))
    x1 = f32(f32(right * scale) + f32(offset_x))
    y1 = f32(f32(bottom * scale) + f32(offset_y))
    box_width = f32(x1 - x0)
    box_height = f32(y1 - y0)
    if box_width <= 0 or box_height <= 0:
        raise ValueError("Az arc téglalapja üres.")

    zoom_ratio = f32(
        min(
            (viewport_width + _DELTA) / float(box_width),
            (viewport_height + _DELTA) / float(box_height),
        )
    )
    if zoom_ratio > f32(4.0):
        zoom = f32(zoom_ratio / f32(3.0))
    else:
        zoom = f32(min(zoom_ratio, _MAX_ZOOM))

    center_x = f32(f32(x0 + x1) / f32(2.0))
    center_y = f32(f32(y0 + y1) / f32(2.0))
    half_width = f32(f32(box_width * zoom) / f32(2.0))
    half_height = f32(f32(box_height * zoom) / f32(2.0))
    rectangle = (
        f32(max(f32(0), min(f32(viewport_width), f32(center_x - half_width)))),
        f32(max(f32(0), min(f32(viewport_height), f32(center_y - half_height)))),
        f32(max(f32(0), min(f32(viewport_width), f32(center_x + half_width)))),
        f32(max(f32(0), min(f32(viewport_height), f32(center_y + half_height)))),
    )
    rounded_rectangle = tuple(
        round(float(value) - _ROUND_BIAS) for value in rectangle
    )
    return FaceCropGeometry(
        source_rectangle=source_rectangle,
        rectangle=rectangle,
        rounded_rectangle=rounded_rectangle,
        scale=scale,
        zoom=zoom,
        fit_offset=(offset_x, offset_y),
    )


def render_face_crop(
    image: np.ndarray,
    face_rectangle: tuple[float, float, float, float],
    viewport_size: tuple[int, int],
    *,
    cropfit: bool,
    background: tuple[int, int, int] = (0, 0, 0),
) -> np.ndarray:
    """Az arcot középre igazítva, a számított nagyítással rendereli ki."""
    viewport_width, viewport_height = viewport_size
    source_height, source_width = image.shape[:2]
    geometry = calculate_face_crop(
        face_rectangle,
        source_size=(source_width, source_height),
        viewport_size=viewport_size,
        cropfit=cropfit,
    )
    f32 = np.float32
    x0, y0, x1, y1 = geometry.source_rectangle
    center_x = f32(f32(x0 + x1) / f32(2.0))
    center_y = f32(f32(y0 + y1) / f32(2.0))
    magnification = f32(geometry.scale * geometry.zoom)
    translate_x = f32(f32(viewport_width / 2) - f32(magnification * center_x))
    translate_y = f32(f32(viewport_height / 2) - f32(magnification * center_y))
    matrix = np.asarray(
        ((magnification, 0, translate_x), (0, magnification, translate_y)),
        dtype=np.float32,
    )
    return cv2.warpAffine(
        image,
        matrix,
        (viewport_width, viewport_height),
        flags=cv2.INTER_LINEAR,
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=background,
    )


__all__ = [
    "FaceCropGeometry",
    "calculate_face_crop",
    "face_is_usable",
    "rect64_to_pixel_rect",
    "render_face_crop",
]
