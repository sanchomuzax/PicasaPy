"""Retusálás (folt-eltávolítás) render-op.

Két, egymás utáni PicasaPy-saját megközelítés él egymás mellett (ld.
`picasapy.ini.retouch` docsztring — mindkettő kalibrálatlan, nincs hozzá
valódi Picasa golden-minta):

- **v1 — `apply_retouch`**: OpenCV Telea-inpaint (tartalom-tudatos
  kitöltés) a megjelölt téglalap-régiókon. Csak visszamenőleges olvasáshoz/
  renderhez maradt meg (korábban PicasaPy-jal mentett `.picasa.ini`-khez).
- **v2 — `apply_retouch_patches`** (#445): a Picasa saját súgószövege
  szerinti **irányított klónozás** — minden folt egy kör alakú területet
  másol a forrás-pont körül a cél-pont körüli azonos alakú területre.

Amint előkerül egy valódi golden-minta, mindkét modul a
`docs/specs/filters-decoded.md` golden-köreinek mintájára kalibrálandó.
"""

from __future__ import annotations

from picasapy import cv as cv2
import numpy as np

from picasapy.ini.rect64 import Rect64
from picasapy.ini.retouch import RetouchPatch
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


def _patch_radius_px(patch: RetouchPatch, width: int, height: int) -> int:
    """A relatív [0..1] sugár képpontban — a kép RÖVIDEBB oldalára
    vonatkoztatva (ld. modul-docsztring), legalább 1 px."""
    return max(1, round(patch.radius * min(width, height)))


def _apply_single_patch(result: np.ndarray, patch: RetouchPatch) -> None:
    """Egyetlen folt (kör alakú klónozás) alkalmazása HELYBEN a `result`-on."""
    height, width = result.shape[:2]
    radius = _patch_radius_px(patch, width, height)
    target_x = round(patch.target_x * width)
    target_y = round(patch.target_y * height)
    source_x = round(patch.source_x * width)
    source_y = round(patch.source_y * height)
    shift_x = source_x - target_x
    shift_y = source_y - target_y

    y0, y1 = max(0, target_y - radius), min(height, target_y + radius + 1)
    x0, x1 = max(0, target_x - radius), min(width, target_x + radius + 1)
    if y1 <= y0 or x1 <= x0:
        return

    yy, xx = np.mgrid[y0:y1, x0:x1]
    circle_mask = (xx - target_x) ** 2 + (yy - target_y) ** 2 <= radius**2
    source_yy = yy + shift_y
    source_xx = xx + shift_x
    valid = (
        circle_mask
        & (source_yy >= 0)
        & (source_yy < height)
        & (source_xx >= 0)
        & (source_xx < width)
    )
    if not valid.any():
        return
    target_rows, target_cols = yy[valid], xx[valid]
    source_rows, source_cols = source_yy[valid], source_xx[valid]
    # a forrás-szeletet MÁSOLATBAN olvassuk ki, mielőtt a célra írnánk — ha a
    # cél és a forrás kör átfedi egymást (kis elmozdulás), az írás ne
    # szennyezze be a még ki nem olvasott forrás-pixeleket.
    sampled = result[source_rows, source_cols].copy()
    result[target_rows, target_cols] = sampled


def apply_retouch_patches(image: np.ndarray, patches: tuple[RetouchPatch, ...] = ()) -> np.ndarray:
    """Irányított klónozás (#445) a megadott foltokkal.

    Minden folt egy kör alakú területet másol a forrás-pont körül a
    cél-pont körüli, azonos sugarú területre — a Picasa súgószövege szerinti
    munkamenet (cél kijelölése, forrás mozgatása, véglegesítés) eredménye.
    A foltok a megadott SORRENDBEN, egymásra épülve alkalmazódnak (a
    későbbi foltok a korábbiak által már módosított tartalmat is
    forrásként használhatják — „lather, rinse, repeat").

    Folt nélkül (`patches=()`) NO-OP. Elfajult (a képen kívüli cél/forrás,
    vagy nulla átfedésű) foltok csendben kimaradnak.
    """
    validate_image(image)
    result = image.copy()
    for patch in patches:
        _apply_single_patch(result, patch)
    return result
