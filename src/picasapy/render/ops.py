"""A Picasa `filters=` lánc műveleteinek régi import-homlokzata.

A képműveletek implementációi kisebb modulokban vannak; a régi importútvonal
és az `ops._channel_histograms` patch-pont változatlanul elérhető.
"""

from __future__ import annotations
import math
from picasapy.lazy_cv2 import cv2
import numpy as np
from picasapy.ini.rect64 import Rect64
from picasapy.render.autocolor_matrix import (
    apply_autocolor_matrix,
    autocolor_matrix_16_16,
    estimate_illuminant,
)
from picasapy.render.curves import (
    apply_channel_luts,
    apply_lut,
    lut_ramp,
    validate_image,
)
from picasapy.render.fixpontos_mintavevo import fixpontos_bilinearis

_validate_image = validate_image

#: A `calcHist` float32 rekeszekbe számol, ami 2^24 fölött már nem pontos
#: egész — a sávok összege int64.
_HISZTOGRAM_SAV_KEPPONT = (1 << 24) - 1

def _channel_histograms(image: np.ndarray) -> np.ndarray:
    """A három csatorna 256 rekeszes hisztogramja, `(3, 256)` int64 (#22).

    Ugyanaz, mint csatornánként egy `np.bincount`, de az OpenCV
    `calcHist`-jével: a célgép előnézeti felbontásán ~45 ms helyett ~14 ms.
    """
    height, width = image.shape[:2]
    oszlopok = min(max(width, 1), _HISZTOGRAM_SAV_KEPPONT)
    sorok = max(1, _HISZTOGRAM_SAV_KEPPONT // oszlopok)
    osszeg = np.zeros((3, 256), dtype=np.int64)
    for felso in range(0, height, sorok):
        for bal in range(0, width, oszlopok):
            sav = np.ascontiguousarray(
                image[felso:felso + sorok, bal:bal + oszlopok]
            )
            for csatorna in range(3):
                darab = cv2.calcHist([sav], [csatorna], None, [256], [0, 256])
                osszeg[csatorna] += darab.reshape(-1).astype(np.int64)
    return osszeg

# A szétbontott modulok importja a régi patch-pont definíciója UTÁN történik:
# az elemzőmodul az `ops._channel_histograms` függvényt használja.
from picasapy.render.ops_geometry import (  # noqa: E402, F401
    _rect_to_pixels,
    apply_crop,
    apply_tilt,
    tilt_matrix,
    tilt_scale,
)
from picasapy.render.ops_levels_analysis import (  # noqa: E402, F401
    _AUTOCOLOR_MAX_SATURATION,
    _AUTOCOLOR_MIN_LEVEL,
    _AUTOCOLOR_MIN_PIXELS,
    _CAREFUL_BLACK_SCALE,
    _LEVELS_CLIP_RATIO,
    _LEVELS_MARGIN_PERCENT,
    _analysis_region,
    _blend_clip_points,
    _channel_black_white_points,
    _levels_clip_threshold,
    _native_clip_points,
    _native_levels_lut,
    _union_black_white_point,
    autocolor_gains,
)
from picasapy.render.ops_levels import (  # noqa: E402, F401
    _AUTOCONTRAST_BLEND,
    _CAREFUL_MAX_OUT,
    _ENHANCE_BLEND,
    apply_autocolor,
    apply_autocontrast,
    apply_autolight,
    apply_channel_levels_stretch,
    apply_enhance,
)
from picasapy.render.ops_redeye import (  # noqa: E402, F401
    _REDEYE_CONTEXT_RADIUS_FACTOR,
    _REDEYE_DOMINANCE_RATIO,
    _REDEYE_LOCAL_SIGMA_FACTOR,
    _REDEYE_MIN_FILL,
    _REDEYE_MIN_ROUNDNESS,
    _REDEYE_MIN_SPOT_PIXELS,
    _eye_circle_mask,
    _eye_red_pixel_mask,
    _redeye_pixel_mask,
    apply_redeye,
    count_redeye_spots,
)

__all__ = (
    "annotations",
    "Rect64",
    "apply_autocolor",
    "apply_autocolor_matrix",
    "apply_autocontrast",
    "apply_autolight",
    "apply_channel_levels_stretch",
    "apply_channel_luts",
    "apply_crop",
    "apply_enhance",
    "apply_lut",
    "apply_redeye",
    "apply_tilt",
    "autocolor_gains",
    "autocolor_matrix_16_16",
    "count_redeye_spots",
    "cv2",
    "estimate_illuminant",
    "fixpontos_bilinearis",
    "lut_ramp",
    "math",
    "np",
    "tilt_matrix",
    "tilt_scale",
    "validate_image",
)
