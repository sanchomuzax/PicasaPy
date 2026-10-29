"""Kivágás és kiegyenesítés műveletei a régi `ops` API mögött."""

from __future__ import annotations

import math

from picasapy.lazy_cv2 import cv2
import numpy as np

from picasapy.ini.rect64 import Rect64
from picasapy.render.curves import validate_image as _validate_image
from picasapy.render.fixpontos_mintavevo import fixpontos_bilinearis

def _rect_to_pixels(rect: Rect64, width: int, height: int) -> tuple[int, int, int, int]:
    """Relatív [0..1] Rect64 → pixel-koordináták (left, top, right, bottom)."""
    left = round(rect.left * width)
    top = round(rect.top * height)
    right = round(rect.right * width)
    bottom = round(rect.bottom * height)
    return left, top, right, bottom

def apply_crop(image: np.ndarray, rect: Rect64) -> np.ndarray:
    """Kivágás a relatív [0..1] `rect` koordináták alapján, pixelre pontosan.

    Üres (nulla szélességű/magasságú) kivágásnál ValueError.
    """
    _validate_image(image)
    height, width = image.shape[:2]
    left, top, right, bottom = _rect_to_pixels(rect, width, height)
    if right <= left or bottom <= top:
        raise ValueError(
            f"Üres kivágás: rect={rect} -> pixel=({left}, {top}, {right}, {bottom})"
        )
    return image[top:bottom, left:right].copy()

def tilt_scale(width: int, height: int, angle: float) -> float:
    """A Kiegyenesítés natív skálája (`0x0090a720`, #3846).

    A két sarkot, `(W/2, H/2)`-t és `(W/2, −H/2)`-t `R(θ)`-val elforgatja, és
    `s = min(1, min_sarok(W/2 / |x′|, H/2 / |y′|))` — ekkora kicsinyítésű
    forrásablak fér el a forgatott képen, tehát a kimenetben nincs üres sarok.
    Fekvő képnél ez `1 / (cos θ + (W/H)·sin θ)`. `angle` radiánban.
    """
    if width <= 0 or height <= 0:
        raise ValueError(f"A méretek pozitívak kell legyenek: {width}x{height}")
    cos_a, sin_a = math.cos(angle), math.sin(angle)
    fel_w, fel_h = width / 2.0, height / 2.0
    skala = 1.0
    for sarok_y in (fel_h, -fel_h):
        x_r = cos_a * fel_w - sin_a * sarok_y
        y_r = sin_a * fel_w + cos_a * sarok_y
        if x_r != 0.0:
            skala = min(skala, fel_w / abs(x_r))
        if y_r != 0.0:
            skala = min(skala, fel_h / abs(y_r))
    return skala

def tilt_matrix(width: int, height: int, angle: float) -> tuple[float, ...]:
    """A Kiegyenesítés cél → forrás mátrixa (`0x0090a720`, #3846).

    `M = T(W/2, H/2) · R(θ) · S(s) · T(−W/2, −H/2)`, `R = [[c, −s_θ], [s_θ,
    c]]`, `s = tilt_scale(...)`. KÉPPONTKÖZEPES koordinátában értendő: a cél
    `(x + 0,5, y + 0,5)` pontját vetíti a forrásba (a `fixpontos_bilinearis`
    konvenciója) — a középpont `W/2`, `H/2`, egész felezés nélkül. Az OpenCV
    egész-képpont konvenciója ugyanezzel a középponttal fél képpontot tolt.
    Kimenet: `(m0, m1, m2, m3, m4, m5)`, `u = m0·x + m1·y + m2`.
    """
    skala = tilt_scale(width, height, angle)
    cos_s, sin_s = math.cos(angle) * skala, math.sin(angle) * skala
    kozep_x, kozep_y = width / 2.0, height / 2.0
    return (
        cos_s, -sin_s, kozep_x - cos_s * kozep_x + sin_s * kozep_y,
        sin_s, cos_s, kozep_y - sin_s * kozep_x - cos_s * kozep_y,
    )

def apply_tilt(image: np.ndarray, angle: float, *, gyors: bool = False) -> np.ndarray:
    """Kiegyenesítés: forgatás a kép közepe körül a natív úton (#3846).

    `angle` radiánban (a lánc a Picasa `p` paraméterét `θ = p · 0,2`-vel
    váltja át). A mátrix a `tilt_matrix`, a skála a `tilt_scale` — a
    kitöltéshez szükséges kicsinyítést maga számolja, kívülről NEM kap
    skálát (a natív út a szűrő 2. paraméterét nem olvassa). A mintavevő a
    Polaroid forgatásával közös 16.16 fixpontos, 8 bites súlyú bilineáris
    (`0x009e7060`); a perem egy képpontos sávjában a szélső képpont
    ismétlődik. A kimenet mérete a bemenetéé.

    `gyors=True` (#3846): CSAK a csúszka-húzás közbeni élő előnézetnek.
    Ugyanaz a képpontközepes mátrix, de `cv2.INTER_LINEAR` a mintavevő —
    a 684-es készleten ΔE 0,28 a natív 0,24 helyett (a régi út 0,92 volt),
    viszont ~a régi OpenCV-út sebességével fut.
    """
    _validate_image(image)
    height, width = image.shape[:2]
    matrix = tilt_matrix(width, height, angle)
    if gyors:
        m0, m1, m2, m3, m4, m5 = matrix
        # képpontközepes → képpont-index: G = T(−0,5) · M · T(0,5)
        index_matrix = np.array(
            [[m0, m1, m2 + 0.5 * (m0 + m1) - 0.5], [m3, m4, m5 + 0.5 * (m3 + m4) - 0.5]]
        )
        return cv2.warpAffine(
            image,
            index_matrix,
            (width, height),
            flags=cv2.INTER_LINEAR | cv2.WARP_INVERSE_MAP,
            borderMode=cv2.BORDER_REPLICATE,
        )
    return fixpontos_bilinearis(image, matrix, width, height, (0, 0, 0))
