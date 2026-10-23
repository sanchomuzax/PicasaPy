"""A Picasa Időrend bemutatójának binárisból mért mozgásképletei.

A görbe pontjai, a transzformációk, a véletlen eltolás, a csúszka és a
`timelinedot` számítása a `docs/specs/picasa-idorend-bemutato-kutatas.md`
38.2.61–38.2.78 szakaszaiból származik. A függvények Qt-mentesek, hogy a
QEMU-kontrollpontok önállóan is ellenőrizhetők legyenek.
"""

from __future__ import annotations

from math import exp, floor, isfinite, trunc
from struct import pack, unpack
from typing import Sequence


DEFAULT_BEZIER_POINTS = (
    (-3.0, -3.0, 10.0),
    (-1.0, -0.5, 4.0),
    (-0.3, 0.9, 0.6),
    (0.9, 0.75, 1.1),
)

_OFFSET_SCALE = 0.1499999761581421
_ALPHA_THRESHOLD = 0.6800000071525574
_ALPHA_SPAN = 0.3199999928474426


def rational_cubic_bezier(
    t: float, points: Sequence[Sequence[float]] = DEFAULT_BEZIER_POINTS
) -> tuple[float, float, float]:
    """Visszaadja a Picasa racionális köbös görbéjének `(x, y, z)` értékét.

    A számláló súlyozatlan. Ez eltér a szokásos racionális Bézier-alaktól,
    és a 38.2.61 QEMU-mérése is ezt a változatot igazolja.
    """
    if len(points) != 4:
        raise ValueError("a Picasa-görbéhez pontosan négy vezérlőpont kell")
    if not isfinite(t):
        raise ValueError("a görbeparaméter csak véges szám lehet")

    one_minus_t = 1.0 - t
    basis = (
        one_minus_t**3,
        3.0 * one_minus_t**2 * t,
        3.0 * one_minus_t * t**2,
        t**3,
    )
    denominator = sum(
        b * point[2] for b, point in zip(basis, points, strict=True)
    )
    if denominator == 0.0:
        raise ValueError("a vezérlőpontoknál a görbe nevezője nulla")
    x_numerator = sum(
        b * point[0] for b, point in zip(basis, points, strict=True)
    )
    y_numerator = sum(
        b * point[1] for b, point in zip(basis, points, strict=True)
    )
    return (
        (x_numerator - 0.5) / denominator + 0.5,
        (y_numerator - 0.5) / denominator + 0.5,
        1.0 / denominator,
    )


def slideshow_easing(progress: float) -> float:
    """A `0x0072df60` qshow-easing függvénye (38.2.24, 38.2.32)."""
    if progress <= 0.0:
        return 0.0
    if progress >= 1.0:
        return 1.0

    def g(value: float) -> float:
        if value < 1.0:
            return value - 1.0 + exp(-value)
        first = exp(-1.0)
        return first + (1.0 - first) * (1.0 - exp(-(value - 1.0)))

    y = 8.0 * progress
    return g(y) / g(8.0)


def frame_transforms(
    progress: float,
    *,
    current_offset: tuple[float, float],
    previous_offset: tuple[float, float],
    previous_present: bool = True,
) -> dict[str, object]:
    """A két qshow-képréteg skálája, eltolása és átmeneti alfája (38.2.62)."""

    def scale(value: float) -> float:
        return 1.0 / (1.1 + 0.17647055523618382 * value**3 / 8.0)

    current_progress = progress**2 * (3.0 - progress) / 4.0
    previous_progress = 1.0 - (
        (1.0 - progress) ** 2 * (1.0 + progress / 2.0) / 2.0
    )
    alpha = (
        trunc(256.0 * (progress - _ALPHA_THRESHOLD) / _ALPHA_SPAN)
        if progress > _ALPHA_THRESHOLD
        else 0
    )
    return {
        "current": {
            "scale": scale(progress),
            "tx": 1.0 + current_progress * current_offset[0],
            "ty": 1.0 + current_progress * current_offset[1],
        },
        "previous": (
            {
                "scale": scale(progress + 1.0),
                "tx": 1.0 + previous_progress * previous_offset[0],
                "ty": 1.0 + previous_progress * previous_offset[1],
            }
            if previous_present
            else {"scale": 1.0, "tx": 0.0, "ty": 0.0}
        ),
        "alpha": alpha,
    }


def blend_channel(current: int, previous: int, alpha: int) -> int:
    """A `0x009dc040` csatornaművelete, beleértve az `a-1` súlyt."""
    current_weight = max(alpha - 1, 0)
    return floor(
        (
            current_weight * current
            + (255 - current_weight) * previous
        )
        / 256.0
    )


def random_slide_offsets(
    previous: tuple[float, float],
    *,
    rand_y: int,
    rand_x: int,
    width: int,
    height: int,
) -> tuple[tuple[float, float], tuple[float, float]]:
    """Új, nemnegatív eltolás és az előző eltolás másolata (38.2.62)."""
    if not (0 <= rand_x <= 32767 and 0 <= rand_y <= 32767):
        raise ValueError("a rand bemenetnek 0 és 32767 közé kell esnie")
    if width < 0 or height < 0:
        raise ValueError("a kép mérete nem lehet negatív")

    def f32(value: float) -> float:
        return unpack("<f", pack("<f", value))[0]

    x = f32(_OFFSET_SCALE * width * rand_x / 32768.0)
    y = f32(_OFFSET_SCALE * 0.5 * height * rand_y / 32768.0)
    return (x, y), previous


def slider_index(values: Sequence[float], ratio: float) -> int:
    """Legközelebbi `A[i]/A[n-1]` index; döntetlennél az első nyer (38.2.77)."""
    if not values:
        return -1
    target = min(1.0, max(0.0, ratio))
    denominator = values[-1]
    ratios = [value / denominator if denominator else 0.0 for value in values]
    best_index = 0
    best_distance = float("inf")
    for index, value in enumerate(ratios):
        distance = abs(target - value)
        if distance < best_distance:
            best_index = index
            best_distance = distance
    return best_index


def slider_thumb_x(
    x: float, *, left: int, width: int, thumb_width: int
) -> int:
    """A csúszka hüvelykujja: sávra szorítás, fél szélesség és 3 px levonás."""
    if width < 0 or thumb_width < 0:
        raise ValueError("a csúszka méretei nem lehetnek negatívak")
    clamped_x = min(float(left + width), max(float(left), x))
    return trunc(clamped_x - ((thumb_width >> 1) + 3))


def timeline_dot_positions(
    values: Sequence[float],
    *,
    x_start: int,
    track_span_minus_four: int,
    dot_width: int,
    y_top: int,
    track_spacing: int,
    dot_height: int,
) -> list[dict[str, int | bool]]:
    """A timelinedot koordinátái és a mért 0/7/14 px ismétlődési ágak."""
    if not values:
        return []
    denominator = values[-1]
    ratios = [value / denominator if denominator else 0.0 for value in values]
    output: list[dict[str, int | bool]] = []
    duplicate_run = 0
    previous_ratio: float | None = None
    last_drawn_x: int | None = None
    last_drawn_y: int | None = None
    for ratio in ratios:
        duplicate_run = (
            duplicate_run + 1
            if previous_ratio is not None and ratio == previous_ratio
            else 0
        )
        previous_ratio = ratio
        x = trunc(
            ratio * track_span_minus_four + x_start - (dot_width >> 1)
        )
        offset = {0: 0, 1: 7, 3: 14}.get(duplicate_run)
        draw = offset is not None
        y = (
            ((y_top + 2 * track_spacing) >> 1)
            - (dot_height >> 1)
            - (offset or 0)
        )
        if draw:
            last_drawn_x, last_drawn_y = x, y
        elif last_drawn_x is not None and last_drawn_y is not None:
            # A kettes duplikátumág egyik mezőt sem írja felül. A rajzoló
            # objektum így az előző pont koordinátáján marad (38.2.78).
            x, y = last_drawn_x, last_drawn_y
        output.append({"x": x, "y": y, "draw": draw})
    return output
