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
CARD_STEP = 0.04999999888241291
FOCUS_X = 0.666
VISIBLE_WIDTH = 0.1


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


def focus_parameter(
    points: Sequence[Sequence[float]] = DEFAULT_BEZIER_POINTS,
) -> float:
    """Az első paraméter a bináris 0,0001-es rácsán, ahol x a 0,666-hoz
    legközelebb esik (38.2.24–38.2.25).
    """
    best_parameter = -1.0
    best_distance = float("inf")
    for step in range(20_000):
        parameter = step / 10_000.0 - 1.0
        x, _y, _w = rational_cubic_bezier(parameter, points)
        distance = abs(x - FOCUS_X)
        if distance < best_distance:
            best_parameter = parameter
            best_distance = distance
    return best_parameter


DEFAULT_FOCUS_PARAMETER = focus_parameter()


def card_alpha(width: float) -> int:
    """A kártya mélység szerinti alfája (38.2.24–38.2.25)."""
    if not isfinite(width):
        raise ValueError("a kártyaszélesség csak véges szám lehet")
    if width <= 0.0:
        return 0
    depth = max(0.0, (1.0 / width - 1.0) / 9.0)
    return round((1.0 - depth**1.5) * 256.0)


def card_stack_offset(
    collection_index: int, photo_index: int
) -> tuple[float, float]:
    """A köteg egy kártyájának stabil, bináris tartományú szórása (#6713).

    A qshow minden kártyánál két `_rand()` értéket használ a
    `(rand - 0.5) * 0.15` képlethez. Itt a gyűjtemény- és fotóindex ad stabil
    magot, hogy a köteg két megnyitáskor azonos helyre kerüljön.
    """
    if collection_index < 0 or photo_index < 0:
        raise ValueError("a köteg indexei nem lehetnek negatívak")

    mask = 0xFFFFFFFF
    state = (
        0x9E3779B9
        ^ ((collection_index + 1) * 0x85EBCA6B)
        ^ ((photo_index + 1) * 0xC2B2AE35)
    ) & mask
    if state == 0:
        state = 1

    def next_random() -> float:
        nonlocal state
        state ^= (state << 13) & mask
        state &= mask
        state ^= state >> 17
        state &= mask
        state ^= (state << 5) & mask
        state &= mask
        return state / 4294967296.0

    return tuple((next_random() - 0.5) * 0.15 for _ in range(2))


def timeline_leader_points(
    p0: Sequence[float], p3: Sequence[float]
) -> tuple[tuple[float, float], ...]:
    """A 10 pontú eredeti Időrend-vezetőív (#6713, `0x007fee70`)."""
    if len(p0) != 2 or len(p3) != 2:
        raise ValueError("a vezetőív kezdő- és végpontja kétdimenziós")
    x0, y0 = map(float, p0)
    x3, y3 = map(float, p3)
    if not all(isfinite(value) for value in (x0, y0, x3, y3)):
        raise ValueError("a vezetőív koordinátái csak végesek lehetnek")
    x1, y1 = x0, y0 + 50.0
    x2, y2 = x3, y3 - 50.0
    points = []
    for index in range(10):
        t = index / 9.0
        one_minus_t = 1.0 - t
        points.append(
            (
                one_minus_t**3 * x0
                + 3.0 * one_minus_t**2 * t * x1
                + 3.0 * one_minus_t * t**2 * x2
                + t**3 * x3,
                one_minus_t**3 * y0
                + 3.0 * one_minus_t**2 * t * y1
                + 3.0 * one_minus_t * t**2 * y2
                + t**3 * y3,
            )
        )
    return tuple(points)


def timeline_text_alphas(progress: float) -> tuple[int, int]:
    """Az eredeti fehér felirat és 1 px-es fekete árnyék alfa-bájtjai."""
    if not isfinite(progress):
        raise ValueError("a felirat alpha-értéke csak véges lehet")
    bounded = min(256.0, max(0.0, progress))
    return floor(bounded * 255.0 / 256.0), floor(bounded * 127.0 / 256.0)


def carousel_layout(
    offset: float,
    count: int,
    points: Sequence[Sequence[float]] = DEFAULT_BEZIER_POINTS,
) -> list[dict[str, float | int | bool]]:
    """A teljes sáv kártyáinak normalizált görbehelye és láthatósága."""
    if not isfinite(offset):
        raise ValueError("a sáv eltolása csak véges szám lehet")
    if count < 0:
        raise ValueError("a gyűjtemények száma nem lehet negatív")
    cards = []
    for index in range(count):
        parameter = index * CARD_STEP + offset
        x, y, width = rational_cubic_bezier(parameter, points)
        cards.append(
            {
                "index": index,
                "t": parameter,
                "x": x,
                "y": y,
                "w": width,
                "alpha": card_alpha(width),
                "visible": width > VISIBLE_WIDTH,
            }
        )
    return cards


def clamp_offset(offset: float, count: int) -> float:
    """A sáv eltolását a fókusz és a gyűjteményszám határai közé szorítja."""
    if not isfinite(offset):
        raise ValueError("a sáv eltolása csak véges szám lehet")
    if count < 0:
        raise ValueError("a gyűjtemények száma nem lehet negatív")
    focus = DEFAULT_FOCUS_PARAMETER
    if count <= 1:
        return focus
    minimum = focus - (count - 1) * CARD_STEP
    return min(focus, max(minimum, offset))


def focus_index(
    offset: float,
    count: int,
    points: Sequence[Sequence[float]] = DEFAULT_BEZIER_POINTS,
) -> int:
    """A fókuszban levő kártya; azonos távolságnál a kisebb index nyer."""
    if count < 0:
        raise ValueError("a gyűjtemények száma nem lehet negatív")
    if count == 0:
        return -1
    best_index = 0
    best_distance = float("inf")
    for card in carousel_layout(offset, count, points):
        distance = abs(float(card["x"]) - FOCUS_X)
        if distance < best_distance:
            best_index = int(card["index"])
            best_distance = distance
    return best_index


def animator_position(
    base_offset: float,
    records: Sequence[dict[str, float]],
    current_time: float,
) -> float:
    """A qshow összegző animátorának pozíciója (38.2.24, 0x009e5e70).

    Minden rekord `delta`, `started_at` és `duration` mezőt tartalmaz; az
    időeltolás `+0.02` másodpercét a bináris `pos(t)` képlete adja.
    """
    if not isfinite(base_offset) or not isfinite(current_time):
        raise ValueError("az animátor ideje és kezdőpontja csak véges lehet")
    position = base_offset
    for record in records:
        delta = float(record["delta"])
        started_at = float(record["started_at"])
        duration = float(record["duration"])
        if not all(isfinite(value) for value in (delta, started_at, duration)):
            raise ValueError("az animátor rekordjának számai legyenek végesek")
        if duration <= 0.0:
            progress = 1.0 if current_time + 0.02 >= started_at else 0.0
        else:
            progress = (current_time + 0.02 - started_at) / duration
        position += slideshow_easing(progress) * delta
    return position


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
