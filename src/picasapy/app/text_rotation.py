"""A Szöveg eszköz forgatókorongjának szög- és dobozgeometriája (#7457)."""

from __future__ import annotations

import math


def _soft_snap(degrees: float, period: float, tolerance: float) -> float:
    """Lágyan a periódus többszörösére tapadó, korlátlan fokérték."""
    while degrees < 0:
        degrees += 360.0
    multiple = math.floor(degrees / period)
    remainder = math.fmod(degrees, period)
    transition = (remainder - tolerance) * period / (period - 2 * tolerance)
    return multiple * period + min(max(transition, 0.0), period)


def snap_text_rotation_degrees(degrees: float) -> float:
    """A Picasa két egymás utáni lágy szűrőjét alkalmazza fokban."""
    return _soft_snap(_soft_snap(float(degrees), 45.0, 7.0), 15.0, 3.0)


def rotation_from_drag(
    start_pointer_angle: float,
    pointer_angle: float,
    start_rotation: float,
) -> float:
    """A húzás végpontjából számolja az új forgatást; minden szög radián."""
    raw_degrees = math.degrees(
        float(pointer_angle) - float(start_pointer_angle) + float(start_rotation)
    )
    return math.radians(snap_text_rotation_degrees(raw_degrees))


def rotated_bounds(
    width: float,
    height: float,
    angle: float,
    scale_x: float = 1.0,
    scale_y: float = 1.0,
) -> tuple[float, float]:
    """A forgatott befoglaló szélessége/magassága a normalizált tengelyeken."""
    width = float(width)
    height = float(height)
    scale_x = float(scale_x)
    scale_y = float(scale_y)
    if width < 0 or height < 0:
        raise ValueError("A szövegdoboz mérete nem lehet negatív")
    if scale_x <= 0 or scale_y <= 0:
        raise ValueError("A szövegkoordináta méretaránya legyen pozitív")
    cosine = abs(math.cos(float(angle)))
    sine = abs(math.sin(float(angle)))
    pixel_width = width * scale_x
    pixel_height = height * scale_y
    rotated_pixel_width = pixel_width * cosine + pixel_height * sine
    rotated_pixel_height = pixel_width * sine + pixel_height * cosine
    return rotated_pixel_width / scale_x, rotated_pixel_height / scale_y


def rotated_top_left(
    *,
    center_x: float,
    center_y: float,
    width: float,
    height: float,
    angle: float,
    scale_x: float = 1.0,
    scale_y: float = 1.0,
) -> tuple[float, float]:
    """A forgáspont körüli elforgatás utáni befoglaló bal felső sarka."""
    rotated_width, rotated_height = rotated_bounds(
        width, height, angle, scale_x, scale_y
    )
    return center_x - rotated_width / 2, center_y - rotated_height / 2
