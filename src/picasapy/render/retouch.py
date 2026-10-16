"""Retusálás (folt-eltávolítás) render-op.

Két, egymás utáni PicasaPy-saját megközelítés él egymás mellett:

- **v1 — `apply_retouch`**: OpenCV Telea-inpaint (tartalom-tudatos
  kitöltés) a megjelölt téglalap-régiókon. Csak visszamenőleges olvasáshoz/
  renderhez maradt meg (korábban PicasaPy-jal mentett `.picasa.ini`-khez).
- **v2 — `apply_retouch_patches`** (#445, #4544): irányított **Poisson-
  gyógyítás** — a forrás körének gradiensei kerülnek a célkörbe, a cél
  eredeti határértékeivel. A `job-151` Colab-mérés lineáris szürke
  átmenetén a cél legfeljebb 1–2 szinttel térhet el az eredeti képtől.

Nyers Colab-golden kép nem található a helyi mérőcsomagban; a v2 tesztjei a
feladatbriefben rögzített `job-151` számszerű viselkedéséhez mérnek.
"""

from __future__ import annotations

from picasapy.lazy_cv2 import cv2
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


def _jacobi_clone_fallback(
    result: np.ndarray,
    source_patch: np.ndarray,
    clone_mask: np.ndarray,
    target_x: int,
    target_y: int,
    radius: int,
    x0: int,
    y0: int,
    x1: int,
    y1: int,
) -> None:
    """Kis/fallback Poisson-folt: a kör pereme Dirichlet-határfeltétel."""
    patch_y = np.arange(y0, y1) - target_y + radius
    patch_x = np.arange(x0, x1) - target_x + radius
    local_source = source_patch[patch_y[:, None], patch_x[None, :]].astype(np.float32)
    local_mask = clone_mask[patch_y[:, None], patch_x[None, :]] != 0
    if not local_mask.any():
        return

    # Csak a négy szomszédjával együtt a folton belül maradó pixeleket
    # oldjuk meg. A kör pereme és a képszél eredeti célpixeleket rögzít.
    interior = local_mask.copy()
    interior[1:, :] &= local_mask[:-1, :]
    interior[:-1, :] &= local_mask[1:, :]
    interior[:, 1:] &= local_mask[:, :-1]
    interior[:, :-1] &= local_mask[:, 1:]
    if y0 == 0:
        interior[0, :] = False
    if y1 == result.shape[0]:
        interior[-1, :] = False
    if x0 == 0:
        interior[:, 0] = False
    if x1 == result.shape[1]:
        interior[:, -1] = False
    if not interior.any():
        return

    solution = result[y0:y1, x0:x1].astype(np.float32)
    source_neighbors = (
        np.roll(local_source, 1, axis=0)
        + np.roll(local_source, -1, axis=0)
        + np.roll(local_source, 1, axis=1)
        + np.roll(local_source, -1, axis=1)
    )
    source_divergence = 4.0 * local_source - source_neighbors
    for _ in range(96):
        neighbors = (
            np.roll(solution, 1, axis=0)
            + np.roll(solution, -1, axis=0)
            + np.roll(solution, 1, axis=1)
            + np.roll(solution, -1, axis=1)
        )
        updated = (neighbors + source_divergence) * 0.25
        difference = float(np.max(np.abs(updated[interior] - solution[interior])))
        solution[interior] = updated[interior]
        if difference < 0.01:
            break
    result[y0:y1, x0:x1][interior] = np.clip(
        np.rint(solution[interior]), 0, 255
    ).astype(np.uint8)


def _apply_single_patch(result: np.ndarray, patch: RetouchPatch) -> None:
    """Egyetlen kör alakú Poisson-gyógyítás alkalmazása HELYBEN."""
    height, width = result.shape[:2]
    radius = _patch_radius_px(patch, width, height)
    target_x = round(patch.target_x * width)
    target_y = round(patch.target_y * height)
    source_x = round(patch.source_x * width)
    source_y = round(patch.source_y * height)
    y0, y1 = max(0, target_y - radius), min(height, target_y + radius + 1)
    x0, x1 = max(0, target_x - radius), min(width, target_x + radius + 1)
    if y1 <= y0 or x1 <= x0:
        return

    offsets = np.arange(-radius, radius + 1)
    source_yy, source_xx = np.meshgrid(
        source_y + offsets, source_x + offsets, indexing="ij"
    )
    circle_mask = offsets[:, None] ** 2 + offsets[None, :] ** 2 <= radius**2
    clone_mask = (
        circle_mask
        & (source_yy >= 0)
        & (source_yy < height)
        & (source_xx >= 0)
        & (source_xx < width)
    ).astype(np.uint8) * 255
    if not clone_mask.any():
        return

    # A forrás és a cél is kap peremet, így a teljes kör-ROI a képszélen sem
    # fut ki az OpenCV seamlessClone által elvárt képtartományból. A forrás
    # tükrözött kiterjesztése csak olvasási segéd; a maszk kizárja a képen
    # kívüli forráspixeleket.
    pad = radius + 4
    border = cv2.BORDER_REFLECT_101 if min(width, height) > 1 else cv2.BORDER_REPLICATE
    source_padded = cv2.copyMakeBorder(result, pad, pad, pad, pad, border)
    source_patch = source_padded[
        source_y + pad - radius : source_y + pad + radius + 1,
        source_x + pad - radius : source_x + pad + radius + 1,
    ]
    local_target = result[y0:y1, x0:x1]
    target_padded = cv2.copyMakeBorder(local_target, pad, pad, pad, pad, border)
    clone_center = (target_x - x0 + pad, target_y - y0 + pad)

    # A seamlessClone egypixeles körnél OpenCV-hibával leáll; annak egyetlen
    # lehetséges belső pixele közvetlenül megoldható a diszkrét Poisson-
    # egyenletből, a négy cél-szomszédot rögzítve.
    if radius == 1:
        if 0 < target_x < width - 1 and 0 < target_y < height - 1:
            source_center = source_patch[1, 1].astype(np.float32)
            source_around = (
                source_patch[0, 1].astype(np.float32)
                + source_patch[2, 1].astype(np.float32)
                + source_patch[1, 0].astype(np.float32)
                + source_patch[1, 2].astype(np.float32)
            )
            target_around = (
                result[target_y - 1, target_x].astype(np.float32)
                + result[target_y + 1, target_x].astype(np.float32)
                + result[target_y, target_x - 1].astype(np.float32)
                + result[target_y, target_x + 1].astype(np.float32)
            )
            healed = (target_around + 4.0 * source_center - source_around) * 0.25
            result[target_y, target_x] = np.clip(np.rint(healed), 0, 255).astype(np.uint8)
        return

    try:
        cloned = cv2.seamlessClone(
            cv2.cvtColor(source_patch, cv2.COLOR_RGB2BGR),
            cv2.cvtColor(target_padded, cv2.COLOR_RGB2BGR),
            clone_mask,
            clone_center,
            cv2.NORMAL_CLONE,
        )
        cloned_rgb = cv2.cvtColor(cloned, cv2.COLOR_BGR2RGB)
        result[y0:y1, x0:x1] = cloned_rgb[
            pad : pad + (y1 - y0), pad : pad + (x1 - x0)
        ]
    except cv2.error:
        _jacobi_clone_fallback(
            result,
            source_patch,
            clone_mask,
            target_x,
            target_y,
            radius,
            x0,
            y0,
            x1,
            y1,
        )


def apply_retouch_patches(image: np.ndarray, patches: tuple[RetouchPatch, ...] = ()) -> np.ndarray:
    """Irányított Poisson-gyógyítás (#4544) a megadott foltokkal.

    A forráskör gradiens-tartománya kerül át a célkörre, a kör határán a
    cél eredeti pixelértékeit rögzítve. Így a forrás textúrája átjön, de a
    célkör tónusa a környezetbe illeszkedik. A kör azonos sugara követi a
    Picasa súgószövege szerinti munkamenetet (cél kijelölése, forrás
    mozgatása, véglegesítés).
    A foltok a megadott SORRENDBEN, egymásra épülve alkalmazódnak (a
    későbbi foltok a korábbiak által már módosított tartalmat is
    forrásként használhatják — „lather, rinse, repeat"). A bemenet
    változatlan marad.

    Folt nélkül (`patches=()`) NO-OP. Elfajult (a képen kívüli cél/forrás,
    vagy nulla átfedésű) foltok csendben kimaradnak.
    """
    validate_image(image)
    result = image.copy()
    for patch in patches:
        _apply_single_patch(result, patch)
    return result
