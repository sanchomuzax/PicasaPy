"""Retusálás (folt-eltávolítás) render-op — cv2.inpaint alapú KÖZELÍTÉS.

**Kalibrálatlan** (ld. `picasapy.ini.retouch` docsztring): a valódi Picasa
retusáló algoritmusa nem publikus és golden-minta sincs hozzá, ezért itt egy
általános, tartalom-tudatos kitöltés (OpenCV Telea-inpaint) fut a megjelölt
régiókon — vizuálisan hihető foltjavítás, de NEM állítjuk, hogy pixelhű a
Picasa eredményéhez. Amint előkerül egy valódi golden-minta, ez a modul a
`docs/specs/filters-decoded.md` golden-köreinek mintájára kalibrálandó.
"""

from __future__ import annotations

import cv2
import numpy as np

from picasapy.ini.rect64 import Rect64
from picasapy.render.curves import validate_image

#: Az inpaint "keresési sugara" (px) — mekkora környező sávból tanul az
#: algoritmus. Kis érték: gyors, de durvább; nagy érték: simább, lassabb.
#: A választott érték a Telea-módszer szokásos alapértéke (OpenCV-doksi).
_INPAINT_RADIUS = 5


def _rect_to_pixels(rect: Rect64, width: int, height: int) -> tuple[int, int, int, int]:
    left = round(rect.left * width)
    top = round(rect.top * height)
    right = round(rect.right * width)
    bottom = round(rect.bottom * height)
    return left, top, right, bottom


def apply_retouch(image: np.ndarray, regions: tuple[Rect64, ...] = ()) -> np.ndarray:
    """Folt-eltávolítás a megadott relatív [0..1] régiókban.

    Régió nélkül (`regions=()`) NO-OP — a valódi Picasa `retouch=1;` bejegyzés
    régió-adata nem ismert, ilyenkor nincs mit kitölteni (ld. modul-docsztring
    a `picasapy.ini.retouch`-ban). Elfajult (nulla méretű vagy a képen kívüli)
    régiók csendben kimaradnak a maszkból.
    """
    validate_image(image)
    if not regions:
        return image.copy()
    height, width = image.shape[:2]
    mask = np.zeros((height, width), dtype=np.uint8)
    for rect in regions:
        left, top, right, bottom = _rect_to_pixels(rect, width, height)
        left, top = max(left, 0), max(top, 0)
        right, bottom = min(right, width), min(bottom, height)
        if right > left and bottom > top:
            mask[top:bottom, left:right] = 255
    if not mask.any():
        return image.copy()
    # cv2.inpaint BGR-t vár — a projekt RGB-konvenciója miatt a csatornákat
    # a hívás körül megcseréljük, majd vissza.
    bgr = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
    inpainted_bgr = cv2.inpaint(bgr, mask, _INPAINT_RADIUS, cv2.INPAINT_TELEA)
    return cv2.cvtColor(inpainted_bgr, cv2.COLOR_BGR2RGB)
