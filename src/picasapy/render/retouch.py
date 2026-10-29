"""Retusálás (folt-eltávolítás) render-op.

Két, egymás utáni PicasaPy-saját megközelítés él egymás mellett:

- **v1 — `apply_retouch`**: OpenCV Telea-inpaint (tartalom-tudatos
  kitöltés) a megjelölt téglalap-régiókon. Csak visszamenőleges olvasáshoz/
  renderhez maradt meg (korábban PicasaPy-jal mentett `.picasa.ini`-khez).
- **v2 — `apply_retouch_patches`** (#445, #4544): irányított **Poisson-
  gyógyítás** — a forrás- és célgradiens a #6009-ben feltárt radiális
  smoothstep szerint vált egymásba; a kör peremén a cél eredeti pixelértékei
  rögzülnek. A `job-151` Colab-mérés lineáris szürke átmenetén a cél
  legfeljebb 1–2 szinttel térhet el az eredeti képtől.

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


_GRADIENT_BLEND_START = 0.5


def _retouch_gradient_weight(
    distance: float | np.ndarray, radius: float
) -> np.ndarray:
    """A bináris smoothstep súlya: belül forrás-, a kör peremén célgradiens."""
    radial_limit = min(0.9 * radius, radius - 1.0)
    start = _GRADIENT_BLEND_START * radial_limit
    distances = np.asarray(distance, dtype=np.float64)
    weight = np.where(distances >= radial_limit, 1.0, 0.0)
    if radial_limit > start:
        t = (distances - start) / (radial_limit - start)
        smoothstep = t * t * (3.0 - 2.0 * t)
        between = (distances > start) & (distances < radial_limit)
        weight = np.where(between, smoothstep, weight)
    return np.where(distances <= start, 0.0, weight)


def _mix_retouch_gradients(
    source_gradient: np.ndarray,
    target_gradient: np.ndarray,
    distance: float | np.ndarray,
    radius: float,
) -> np.ndarray:
    """Egy él forrás- és célgradiensét keveri a bináris radiális súllyal."""
    weight = _retouch_gradient_weight(distance, radius)
    if weight.ndim == source_gradient.ndim - 1:
        weight = weight[..., None]
    return source_gradient + weight * (target_gradient - source_gradient)


def _mixed_gradient_divergence(
    source_patch: np.ndarray,
    target_patch: np.ndarray,
    distance: np.ndarray,
    radius: float,
) -> np.ndarray:
    """A négy irányított gradienst a pixelközéppont súlyával összegzi."""
    divergence = np.zeros_like(source_patch, dtype=np.float64)
    for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        shift = (-dy, -dx)
        source_neighbour = np.roll(source_patch, shift, axis=(0, 1))
        target_neighbour = np.roll(target_patch, shift, axis=(0, 1))
        divergence += _mix_retouch_gradients(
            source_patch - source_neighbour,
            target_patch - target_neighbour,
            distance,
            radius,
        )
    return divergence


def _poisson_operator(values: np.ndarray, active: np.ndarray) -> np.ndarray:
    """A maszkbeli 4-neighbor diszkrét Laplace-operátora."""
    neighbours = (
        np.roll(values, 1, axis=0)
        + np.roll(values, -1, axis=0)
        + np.roll(values, 1, axis=1)
        + np.roll(values, -1, axis=1)
    )
    return (4.0 * values - neighbours) * active[..., None]


def _solve_poisson(
    right_hand_side: np.ndarray,
    initial: np.ndarray,
    active: np.ndarray,
    radius: int,
) -> np.ndarray:
    """Dirichlet-határú Poisson-rendszer megoldása csatornánként CG-vel."""
    solution = initial.astype(np.float64) * active[..., None]
    residual = (
        right_hand_side - _poisson_operator(solution, active)
    ) * active[..., None]
    direction = residual.copy()
    residual_norm = np.sum(residual * residual, axis=(0, 1))
    initial_norm = residual_norm.copy()
    if float(np.max(initial_norm)) <= 1e-20:
        return solution

    for _ in range(min(2048, max(64, radius * 16))):
        applied = _poisson_operator(direction, active)
        denominator = np.sum(direction * applied, axis=(0, 1))
        alpha = np.divide(
            residual_norm,
            denominator,
            out=np.zeros_like(residual_norm),
            where=denominator > 1e-20,
        )
        solution += direction * alpha[None, None, :]
        residual -= applied * alpha[None, None, :]
        next_norm = np.sum(residual * residual, axis=(0, 1))
        if np.all(next_norm <= initial_norm * 1e-10):
            break
        beta = np.divide(
            next_norm,
            residual_norm,
            out=np.zeros_like(next_norm),
            where=residual_norm > 1e-20,
        )
        direction = (residual + direction * beta[None, None, :]) * active[
            ..., None
        ]
        residual_norm = next_norm
    return solution


def _apply_single_patch(result: np.ndarray, patch: RetouchPatch) -> None:
    """Egyetlen kör alakú Poisson-gyógyítás alkalmazása HELYBEN."""
    height, width = result.shape[:2]
    radius = _patch_radius_px(patch, width, height)
    target_x = round(patch.target_x * width)
    target_y = round(patch.target_y * height)
    source_x = round(patch.source_x * width)
    source_y = round(patch.source_y * height)
    if (
        target_x + radius < 0
        or target_x - radius >= width
        or target_y + radius < 0
        or target_y - radius >= height
        or source_x + radius < 0
        or source_x - radius >= width
        or source_y + radius < 0
        or source_y - radius >= height
    ):
        return

    # One padding pixel supplies every four-neighbor gradient at the circular
    # boundary. Reflection is only used for sampling; active pixels stay
    # clipped to the actual source and target images.
    pad = radius + 1
    border = cv2.BORDER_REFLECT_101 if min(width, height) > 1 else cv2.BORDER_REPLICATE
    padded = cv2.copyMakeBorder(result, pad, pad, pad, pad, border)
    extent = radius + 1

    def sample(center_x: int, center_y: int) -> np.ndarray:
        return padded[
            center_y + pad - extent : center_y + pad + extent + 1,
            center_x + pad - extent : center_x + pad + extent + 1,
        ]

    source_patch = sample(source_x, source_y).astype(np.float64)
    target_patch = sample(target_x, target_y).astype(np.float64)
    offsets = np.arange(-extent, extent + 1)
    offset_y, offset_x = np.meshgrid(offsets, offsets, indexing="ij")
    target_xs = target_x + offset_x
    target_ys = target_y + offset_y
    source_xs = source_x + offset_x
    source_ys = source_y + offset_y
    active = (
        (offset_x**2 + offset_y**2 <= radius**2)
        & (target_xs >= 0)
        & (target_xs < width)
        & (target_ys >= 0)
        & (target_ys < height)
        & (source_xs >= 0)
        & (source_xs < width)
        & (source_ys >= 0)
        & (source_ys < height)
    )
    if not active.any():
        return

    pixel_distance = np.hypot(offset_x, offset_y)
    divergence = _mixed_gradient_divergence(
        source_patch, target_patch, pixel_distance, radius
    )
    right_hand_side = np.zeros_like(source_patch, dtype=np.float64)
    for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        shift = (-dy, -dx)
        target_neighbour = np.roll(target_patch, shift, axis=(0, 1))
        neighbour_active = np.roll(active, shift, axis=(0, 1))
        boundary = active & ~neighbour_active
        right_hand_side += target_neighbour * boundary[..., None]

    right_hand_side = (right_hand_side + divergence) * active[..., None]
    solution = _solve_poisson(right_hand_side, target_patch, active, radius)
    rows, columns = np.nonzero(active)
    healed = np.clip(np.rint(solution[rows, columns]), 0, 255).astype(np.uint8)
    result[target_ys[rows, columns], target_xs[rows, columns]] = healed


def apply_retouch_patches(image: np.ndarray, patches: tuple[RetouchPatch, ...] = ()) -> np.ndarray:
    """Irányított Poisson-gyógyítás (#4544) a megadott foltokkal.

    A forrás- és célkör szomszédos pixelei közti gradiensek a #6009 szerinti
    radiális smoothstep súllyal keverednek (s=0.5,
    R=min(0.9*r, r-1)). A kör határán a cél eredeti pixelértékei adják a
    Dirichlet-feltételt, így a forrás textúrája a cél tónusába simul. A kör
    azonos sugara követi a Picasa súgószövege szerinti munkamenetet (cél
    kijelölése, forrás mozgatása, véglegesítés).
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
