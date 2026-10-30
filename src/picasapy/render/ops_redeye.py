"""Vörösszem-javítási műveletek a régi `ops` API mögött."""

from __future__ import annotations

import numpy as np
from picasapy.lazy_cv2 import cv2

from picasapy.ini.rect64 import Rect64
from picasapy.render.curves import validate_image as _validate_image
from picasapy.render.ops_geometry import _rect_to_pixels

_REDEYE_DOMINANCE_RATIO = 1.67
_REDEYE_LOCAL_SIGMA_FACTOR = 1.5
_REDEYE_CONTEXT_RADIUS_FACTOR = 2.5
_REDEYE_MIN_ROUNDNESS = 0.6
_REDEYE_MIN_FILL = 0.5
#: A `count_redeye_spots` zajszűrése: a hat pixelnél kisebb összefüggő
#: foltok nem számítanak külön szemnek; a JPEG-zaj is abszolút méretű.
_REDEYE_MIN_SPOT_PIXELS = 6

def apply_redeye(
    image: np.ndarray,
    regions: tuple[Rect64, ...] = (),
    *,
    eye_circles: tuple[tuple[float, float, float], ...] | None = None,
) -> np.ndarray:
    """Mért Picasa-küszöbbel javít, opcionálisan csak a YuNet szemköreiben.

    `eye_circles is None` a modell nélküli tartalék: a kézi téglalapokon,
    vagy kézi régió híján a teljes képen fut. Üres tuple modell által
    igazolt nulla arctalálat, ezért kézi régió híján semmit nem módosít.
    A színfeltétel a #720 mérése szerinti `R / max(G, B) > 1.67`, a három
    csatorna kimenete pedig keményen `min(G, B)`.
    """
    _validate_image(image)
    height, width = image.shape[:2]
    result = image.copy()

    manual_mask = np.zeros((height, width), dtype=bool)
    for rect in regions:
        left, top, right, bottom = _rect_to_pixels(rect, width, height)
        manual_mask[max(top, 0) : max(bottom, 0), max(left, 0) : max(right, 0)] = True

    if eye_circles is None:
        red_eye_mask = (
            manual_mask & _redeye_pixel_mask(image)
            if regions
            else _redeye_pixel_mask(image)
        )
    else:
        red_eye_mask = _eye_red_pixel_mask(image, eye_circles)
        red_eye_mask |= manual_mask & _redeye_pixel_mask(image)
    green = image[..., 1].astype(np.uint8)
    blue = image[..., 2].astype(np.uint8)
    neutral = np.minimum(green, blue)
    result[red_eye_mask] = neutral[red_eye_mask, None]
    return result

def _redeye_pixel_mask(image: np.ndarray) -> np.ndarray:
    """A vörösszem-színküszöb bool maszkja (ld. `apply_redeye` docsztring)."""
    red = image[..., 0].astype(np.float32)
    strongest_other = np.maximum(image[..., 1], image[..., 2]).astype(np.float32)
    return red > (_REDEYE_DOMINANCE_RATIO * strongest_other)

def _eye_circle_mask(
    height: int,
    width: int,
    eye_circles: tuple[tuple[float, float, float], ...],
) -> np.ndarray:
    """A YuNet-pontok körül a képpontokat a szemtávolságból számolt sugárral jelöli."""
    yy, xx = np.ogrid[:height, :width]
    mask = np.zeros((height, width), dtype=bool)
    for x, y, circle_radius in eye_circles:
        radius = max(0.0, float(circle_radius))
        if radius == 0:
            continue
        mask |= (xx - float(x)) ** 2 + (yy - float(y)) ** 2 <= radius**2
    return mask

def _eye_red_pixel_mask(
    image: np.ndarray,
    eye_circles: tuple[tuple[float, float, float], ...],
) -> np.ndarray:
    """YCbCr-jelöltmaszk a szemkörökön belül, alakszűréssel és mért aránnyal.

    A maszk zárása csak a jelöltfoltok alakvizsgálatához szolgál; a kimenet
    továbbra is a nyers, arányfeltételt teljesítő képpontokat cseréli, nem
    fest ki teljes korongot a mérten pixelpontos Picasa-viselkedés helyett.
    """
    height, width = image.shape[:2]
    eye_mask = _eye_circle_mask(height, width, eye_circles)
    if not eye_mask.any():
        return eye_mask
    red_candidates = eye_mask & _redeye_pixel_mask(image)
    if not red_candidates.any():
        return red_candidates

    ycrcb = cv2.cvtColor(image, cv2.COLOR_RGB2YCrCb)
    cr = ycrcb[..., 1].astype(np.float32)
    kernel = np.ones((3, 3), dtype=np.uint8)
    selected = np.zeros((height, width), dtype=bool)
    for x, y, circle_radius in eye_circles:
        radius = max(0.0, float(circle_radius))
        if radius == 0:
            continue
        left = max(0, int(np.floor(x - radius)))
        top = max(0, int(np.floor(y - radius)))
        right = min(width, int(np.ceil(x + radius)) + 1)
        bottom = min(height, int(np.ceil(y + radius)) + 1)
        context_radius = radius * _REDEYE_CONTEXT_RADIUS_FACTOR
        context_left = max(0, int(np.floor(x - context_radius)))
        context_top = max(0, int(np.floor(y - context_radius)))
        context_right = min(width, int(np.ceil(x + context_radius)) + 1)
        context_bottom = min(height, int(np.ceil(y + context_radius)) + 1)
        if (
            right <= left
            or bottom <= top
            or context_right <= context_left
            or context_bottom <= context_top
        ):
            continue
        local_eye = eye_mask[top:bottom, left:right]
        local_cr = cr[top:bottom, left:right]
        context_cr = cr[context_top:context_bottom, context_left:context_right]
        values = context_cr.ravel()
        if values.size == 0:
            continue
        threshold = float(values.mean() + _REDEYE_LOCAL_SIGMA_FACTOR * values.std())
        candidates = (
            red_candidates[top:bottom, left:right]
            & local_eye
            & (local_cr > threshold)
        ).astype(np.uint8)
        closed = cv2.morphologyEx(candidates, cv2.MORPH_CLOSE, kernel)
        contours, _ = cv2.findContours(
            closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )
        for contour in contours:
            area = float(cv2.contourArea(contour))
            perimeter = float(cv2.arcLength(contour, True))
            x, y, box_width, box_height = cv2.boundingRect(contour)
            if not box_width or not box_height or not perimeter:
                continue
            roundness = 4.0 * np.pi * area / (perimeter * perimeter)
            fill = area / (box_width * box_height)
            if roundness < _REDEYE_MIN_ROUNDNESS or fill < _REDEYE_MIN_FILL:
                continue
            component = np.zeros_like(candidates)
            cv2.drawContours(component, [contour], -1, 1, thickness=cv2.FILLED)
            selected[top:bottom, left:right] |= (candidates != 0) & (component != 0)
    return selected

def count_redeye_spots(
    image: np.ndarray,
    *,
    eye_circles: tuple[tuple[float, float, float], ...] | None = None,
) -> int:
    """Hány KÜLÖNÁLLÓ vörösszem-folt van a képen (#445).

    `eye_circles=None` a modell nélküli teljes képes tartalék; a tuple a
    YuNet-szemkörökön belüli összefüggő komponenseket számolja. A
    `_REDEYE_MIN_SPOT_PIXELS`-nél kisebb, jellemzően zaj- vagy tömörítési
    eredetű foltok kimaradnak. Csak a felhasználói
    visszajelzéshez („Picasa has found and corrected red eye(s)") kell — a
    javítás maga továbbra is pixel-maszkkal dolgozik, nem foltonként.
    """
    _validate_image(image)
    pixel_mask = (
        _redeye_pixel_mask(image)
        if eye_circles is None
        else _eye_red_pixel_mask(image, eye_circles)
    )
    mask = pixel_mask.astype(np.uint8)
    count, _, stats, _ = cv2.connectedComponentsWithStats(mask, connectivity=8)
    # a 0. komponens a háttér (a maszkon kívüli pixelek) — kihagyva
    return int(
        sum(
            1
            for i in range(1, count)
            if stats[i, cv2.CC_STAT_AREA] >= _REDEYE_MIN_SPOT_PIXELS
        )
    )
