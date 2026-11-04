"""Az effekt-térszelvény próbaképeinek mérése a valódi renderlánccal (#6522).

# SAJÁT FUNKCIÓ (#6522): a vizualizáció próbaképeit a tényleges effektlánc méri.
"""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np

from picasapy.ini.filters import FilterOp
from picasapy.lazy_cv2 import cv2
from picasapy.render import apply_filters

SLICE_STEPS = 12
TONE_COLUMNS = 33
PLANE_EDGE = 33
COLOR_STEPS = 5


def slider_sweep(
    minimum: float, maximum: float, current: float, *, count: int = SLICE_STEPS
) -> tuple[float, ...]:
    """A teljes csúszkatartomány egyenletes mintapontjai, a jelzőállástól függetlenül."""
    minimum = float(minimum)
    maximum = float(maximum)
    current = float(current)
    if count < 2 or not np.isfinite((minimum, maximum, current)).all():
        raise ValueError("érvénytelen csúszkatartomány")
    if minimum >= maximum:
        raise ValueError("a csúszka minimumának kisebbnek kell lennie a maximumnál")
    return tuple(float(value) for value in np.linspace(minimum, maximum, count))


def replace_slider_value(
    operations: Sequence[FilterOp], operation_index: int, parameter_index: int, value: float
) -> tuple[FilterOp, ...]:
    """Egy rétegtag egy csúszkáját cseréli le, minden más mezőt érintetlenül hagyva."""
    if not 0 <= operation_index < len(operations):
        return tuple(operations)
    operation = operations[operation_index]
    if not 0 <= parameter_index < len(operation.params):
        return tuple(operations)
    params = list(operation.params)
    params[parameter_index] = f"{float(value):.6f}"
    result = list(operations)
    result[operation_index] = FilterOp(operation.name, tuple(params))
    return tuple(result)


def render_surface(
    source: np.ndarray | None,
    operations: Sequence[FilterOp],
    view_type: str,
    *,
    depth: dict | None = None,
    probe_kind: str = "gray",
) -> dict:
    """Kicsi, memóriabeli próbaképből QML-nek átadható felület-adatot mér."""
    if view_type == "none":
        return {"kind": "none", "rows": [], "message": "none"}
    if not operations:
        return {
            "kind": "identity",
            "line": ((0.0, 0.0), (1.0, 1.0)),
            "rows": [],
        }
    if view_type == "tone":
        return _tone_surface(source, operations, depth, probe_kind)
    if view_type == "color":
        return _color_cube(operations)
    if view_type == "point":
        return _image_surface(operations, "point")
    if view_type == "grain":
        return _image_surface(operations, "grain")
    return _image_surface(operations, "image")


def _gray_ramp() -> np.ndarray:
    ramp = np.linspace(0, 255, TONE_COLUMNS, dtype=np.uint8)
    return np.repeat(ramp[None, :, None], 3, axis=2)


_LUMA = (0.2126, 0.7152, 0.0722)
#: #6536: a fotón mért átviteli görbe mintája (sor, oszlop)
_FOTO_MINTA = (96, 128)


def _atviteli_gorbe(bemenet: np.ndarray, kimenet: np.ndarray) -> list[float]:
    """Mért átviteli görbe: minden bemenő szinthez a kimenő szintek átlaga (0-1).

    #6536: az automatikus effektek (Jó napom van) képfüggők, ezért a fotón
    mérjük őket; a hiányzó szinteket a szomszédos mért szintek közt interpoláljuk."""
    oszlopok = TONE_COLUMNS
    be = np.clip(bemenet.astype(np.float64).ravel() / 255.0, 0.0, 1.0)
    ki = np.clip(kimenet.astype(np.float64).ravel() / 255.0, 0.0, 1.0)
    rekesz = np.rint(be * (oszlopok - 1)).astype(int)
    darab = np.bincount(rekesz, minlength=oszlopok)
    osszeg = np.bincount(rekesz, weights=ki, minlength=oszlopok)
    van = darab > 0
    if not van.any():
        return np.linspace(0.0, 1.0, oszlopok).tolist()
    helyek = np.flatnonzero(van)
    ertekek = osszeg[van] / darab[van]
    return np.interp(np.arange(oszlopok), helyek, ertekek).tolist()


def _foto_atvitel(input_image: np.ndarray, output: np.ndarray) -> tuple[list[float], list[list[float]]]:
    """A fotón mért fényesség- és csatornánkénti átviteli görbe."""
    kimenet = _fit_rgb(output, input_image.shape[:2])
    sor = _atviteli_gorbe(input_image @ np.array(_LUMA), kimenet @ np.array(_LUMA))
    csatornak = [_atviteli_gorbe(input_image[:, :, c], kimenet[:, :, c]) for c in range(3)]
    return sor, csatornak


def _foto_minta(source) -> np.ndarray:
    """A fotó mintája alján egy keskeny szürke ékkel: minden bemenő szint mérhető.

    Egyszínű vagy szűk tónusú fotón az ék nélkül csak egy-két szint lenne
    mérhető, és a görbe lapos lenne; a 4 soros ék a képfüggő effekt
    statisztikáját alig mozdítja."""
    sorok, oszlopok = _FOTO_MINTA
    foto = _fit_rgb(source, (sorok - 4, oszlopok))
    ek = np.repeat(np.linspace(0, 255, oszlopok, dtype=np.uint8)[None, :, None], 3, axis=2)
    return np.vstack([foto, np.repeat(ek, 4, axis=0)])


def _tone_surface(source, operations, depth, probe_kind) -> dict:
    foto = probe_kind == "photo" and source is not None and np.asarray(source).size
    input_image = _foto_minta(source) if foto else _probe_source(source, probe_kind)
    if depth and depth.get("operationIndex") is not None:
        points = slider_sweep(
            depth["minimum"], depth["maximum"], depth["current"], count=SLICE_STEPS
        )
    else:
        # Csúszka nélküli tónuseffektnél is legyen kirajzolható, mélységben állandó felület.
        points = (0.0, 1.0)

    rows: list[list[float]] = []
    channels: list[list[list[float]]] = []
    for point in points:
        sampled_ops = operations
        if depth and depth.get("operationIndex") is not None:
            sampled_ops = replace_slider_value(
                operations,
                int(depth["operationIndex"]),
                int(depth["parameterIndex"]),
                point,
            )
        output = _apply(input_image, sampled_ops)
        if foto:
            sor, csatornak = _foto_atvitel(input_image, output)
            rows.append(sor)
            channels.append(csatornak)
            continue
        fitted = _fit_rgb(output, (1, TONE_COLUMNS))
        channels.append(
            [[float(value) / 255.0 for value in fitted[0, :, channel]] for channel in range(3)]
        )
        rows.append(
            [
                float(np.dot(fitted[0, column, :3], (0.2126, 0.7152, 0.0722))) / 255.0
                for column in range(TONE_COLUMNS)
            ]
        )
    if not rows:
        rows = [np.linspace(0.0, 1.0, TONE_COLUMNS).tolist()]
    current = float(depth["current"]) if depth else 0.0
    marker = 0
    if depth and depth.get("operationIndex") is not None:
        span = float(depth["maximum"]) - float(depth["minimum"])
        marker = round(
            (current - float(depth["minimum"])) / span * (len(rows) - 1)
        )
        marker = max(0, min(len(rows) - 1, marker))
    return {
        "kind": "tone",
        "rows": rows,
        "channels": channels,
        "markerRow": marker,
        "hasMarker": bool(depth and depth.get("operationIndex") is not None),
        "current": current,
        "minimum": float(depth["minimum"]) if depth else 0.0,
        "maximum": float(depth["maximum"]) if depth else 1.0,
    }


def _color_cube(operations) -> dict:
    coordinates = np.linspace(0, 255, COLOR_STEPS, dtype=np.uint8)
    inputs = np.asarray(
        [(red, green, blue) for red in coordinates for green in coordinates for blue in coordinates],
        dtype=np.uint8,
    )
    output = _apply(inputs.reshape(COLOR_STEPS, COLOR_STEPS * COLOR_STEPS, 3), operations)
    colors = np.asarray(output)
    if colors.ndim == 2:
        colors = np.repeat(colors[:, :, None], 3, axis=2)
    if colors.ndim != 3 or colors.shape[2] < 3 or colors.size == 0:
        colors = inputs.reshape(COLOR_STEPS, COLOR_STEPS * COLOR_STEPS, 3)
    if colors.shape[:2] != (COLOR_STEPS, COLOR_STEPS * COLOR_STEPS):
        colors = cv2.resize(
            colors[:, :, :3],
            (COLOR_STEPS * COLOR_STEPS, COLOR_STEPS),
            interpolation=cv2.INTER_AREA,
        )
    colors = np.clip(colors[:, :, :3], 0, 255).astype(np.uint8).reshape(-1, 3)
    points = []
    for index in range(len(inputs)):
        out = colors[min(index, len(colors) - 1)]
        # a pont oda kerül, ahová az effekt a színt viszi, és olyan színű lesz
        points.append(
            {
                "x": float(out[0]) / 255.0,
                "y": float(out[1]) / 255.0,
                "z": float(out[2]) / 255.0,
                "color": [int(out[0]), int(out[1]), int(out[2])],
            }
        )
    return {"kind": "color", "points": points}


def _image_surface(operations, kind: str) -> dict:
    if kind == "point":
        image = np.full((PLANE_EDGE, PLANE_EDGE, 3), 127, dtype=np.uint8)
        image[PLANE_EDGE // 2, PLANE_EDGE // 2] = 255
    elif kind == "grain":
        random = np.random.default_rng(6522)
        noise = np.clip(127 + random.integers(-2, 3, (PLANE_EDGE, PLANE_EDGE)), 0, 255)
        image = np.repeat(noise[:, :, None].astype(np.uint8), 3, axis=2)
    else:
        image = _plane_probe(operations)
    output = _fit_rgb(_apply(image, operations), (PLANE_EDGE, PLANE_EDGE))
    delta = np.abs(output.astype(np.float32) - image.astype(np.float32))
    if kind == "point":
        height = np.max(output.astype(np.float32), axis=2) / 255.0
    elif kind == "grain":
        height = np.mean(output.astype(np.float32), axis=2) / 255.0
    else:
        height = np.max(delta, axis=2) / 255.0
    return {"kind": kind, "rows": _to_rows(height)}


# A képsík-próba a hatás fajtája szerint: egyenletes szürke a fényerő-jellegű,
# telített mező a színtelítés-jellegű, sakktábla a szerkezetet módosító effektnek.
_GRAY_PLANE_EFFECTS = frozenset({"dir_brite"})
_SATURATED_PLANE_EFFECTS = frozenset({"boost", "dir_sat", "sixties"})


def _plane_probe(operations) -> np.ndarray:
    names = {str(operation.name).casefold() for operation in operations}
    if names and names <= _GRAY_PLANE_EFFECTS:
        return np.full((PLANE_EDGE, PLANE_EDGE, 3), 160, dtype=np.uint8)
    if names and names <= _GRAY_PLANE_EFFECTS | _SATURATED_PLANE_EFFECTS:
        image = np.empty((PLANE_EDGE, PLANE_EDGE, 3), dtype=np.uint8)
        image[:, :] = (196, 92, 64)
        return image
    y, x = np.indices((PLANE_EDGE, PLANE_EDGE))
    checker = np.where(((x // 4 + y // 4) % 2) == 0, 112, 144).astype(np.uint8)
    return np.repeat(checker[:, :, None], 3, axis=2)


def _probe_source(source, probe_kind):
    if probe_kind == "photo" and source is not None and source.size:
        return _fit_rgb(source, (32, TONE_COLUMNS))
    return _gray_ramp()


def _apply(image, operations):
    if not operations:
        return image
    try:
        return apply_filters(image, tuple(operations)).image
    except Exception:  # noqa: BLE001 - egy hibás lánctag ne tegye üressé a dobozt
        return image


def _fit_rgb(image, size: tuple[int, int]) -> np.ndarray:
    array = np.asarray(image)
    if array.ndim == 2:
        array = np.repeat(array[:, :, None], 3, axis=2)
    if array.ndim != 3 or array.shape[2] < 3 or array.size == 0:
        return np.zeros((size[0], size[1], 3), dtype=np.uint8)
    if array.shape[:2] != size:
        array = cv2.resize(array[:, :, :3], (size[1], size[0]), interpolation=cv2.INTER_AREA)
    return np.clip(array[:, :, :3], 0, 255).astype(np.uint8)


def _to_rows(values: np.ndarray) -> list[list[float]]:
    return [[float(value) for value in row] for row in values]
