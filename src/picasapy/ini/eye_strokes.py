"""A `ReanimatedEyeColor` (Vámpírszem) festett vonásainak ini-modellje.

A vonások sora a `filters=` paraméterek első három eleme (engedélyező,
Blur, Fade) után következik. Az eredeti olvasó csak az 5 és 7 mezős rekordot
fogadja, ezért a többi rekordot nyers szövegként őrizzük meg: az eredeti író
néhány olyan alakot is kiad, amelyet az olvasó elutasít.
"""

from __future__ import annotations

import re
import struct
from dataclasses import dataclass

from picasapy.ini.filters import FilterOp


_ATOL_PREFIX = re.compile(r"^[\t\n\v\f\r ]*([+-]?\d+)")
_EXPONENT = re.compile(r"[eE]([+-])(\d+)$")
_FILTER_NAME = "ReanimatedEyeColor"
_BASE_PARAM_COUNT = 3


def _float32(value: float) -> float:
    """Az eredeti `_atof` utáni `float32` mezőt állítja elő."""
    try:
        return struct.unpack("!f", struct.pack("!f", value))[0]
    except OverflowError:
        return float("-inf") if value < 0 else float("inf")


def _parse_float32(value: str) -> float:
    return _float32(float(value))


def _atol(value: str) -> int:
    """A módmezőhöz szükséges `_atol`-szerű, egész prefixet olvasó alak."""
    match = _ATOL_PREFIX.match(value)
    return int(match.group(1)) if match else 0


def _mode(value: str) -> int:
    return int(_atol(value) != 0)


def _format_g(value: float) -> str:
    """A `%g` hat értékes jegyű alakja, MSVC-féle háromjegyű kitevővel."""
    result = format(value, ".6g")
    match = _EXPONENT.search(result)
    if match is None:
        return result
    sign, digits = match.groups()
    exponent = int(digits)
    return f"{result[:match.start()]}e{sign}{exponent:03d}"


@dataclass(frozen=True)
class BrushStyle:
    """Egy vonás ecsetstílusa; a `style_id` a mutatóazonosságot képviseli."""

    style_id: int
    mode: int
    size: float
    hardness: float

    def __post_init__(self) -> None:
        object.__setattr__(self, "mode", int(self.mode != 0))
        object.__setattr__(self, "size", _float32(self.size))
        object.__setattr__(self, "hardness", _float32(self.hardness))


@dataclass(frozen=True)
class StrokePoint:
    """Egy float32 koordinátapár."""

    x: float
    y: float

    def __post_init__(self) -> None:
        object.__setattr__(self, "x", _float32(self.x))
        object.__setattr__(self, "y", _float32(self.y))


@dataclass(frozen=True)
class EyeStroke:
    """A Vámpírszem egy festett vonása."""

    alpha: float
    spacing: float
    rotation: float
    style: BrushStyle
    points: tuple[StrokePoint, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "alpha", _float32(self.alpha))
        object.__setattr__(self, "spacing", _float32(self.spacing))
        object.__setattr__(self, "rotation", _float32(self.rotation))
        object.__setattr__(self, "points", tuple(self.points))


@dataclass(frozen=True)
class RawStroke:
    """Az eredeti olvasó által elutasított rekord változatlan szövege."""

    raw: str


StrokeRecord = EyeStroke | RawStroke


@dataclass(frozen=True)
class ReanimatedEyeColor:
    """A meglévő csúszkamezők és a sorrendben álló festett vonások."""

    base_params: tuple[str, ...]
    strokes: tuple[StrokeRecord, ...]


def parse_reanimated_eye_color(op: FilterOp) -> ReanimatedEyeColor:
    """A Vámpírszem szűrő vonásait float32 modellbe olvassa.

    A hibás vagy az eredeti olvasó által elutasított rekord nyers szövegként
    marad a modellben. Ilyen rekord után az örökölt stílus nem ismert, ezért
    a következő, stíluspár nélküli rekordot is nyersen hagyjuk a következő
    önálló (7 mezős) stílusdeklarációig.
    """
    if op.name != _FILTER_NAME:
        raise ValueError(f"Nem Vámpírszem szűrő: {op.name!r}")

    base_count = min(_BASE_PARAM_COUNT, len(op.params))
    base_params = op.params[:base_count]
    raw_records = op.params[base_count:]
    strokes: list[StrokeRecord] = []
    previous_style: BrushStyle | None = None
    next_style_id = 0

    for raw in raw_records:
        try:
            parsed, next_style_id = _parse_record(
                raw,
                previous_style=previous_style,
                next_style_id=next_style_id,
            )
        except (OverflowError, ValueError):
            parsed = None

        if parsed is None:
            strokes.append(RawStroke(raw))
            previous_style = None
            continue

        strokes.append(parsed)
        previous_style = parsed.style

    return ReanimatedEyeColor(tuple(base_params), tuple(strokes))


def _parse_record(
    raw: str,
    *,
    previous_style: BrushStyle | None,
    next_style_id: int,
) -> tuple[EyeStroke | None, int]:
    fields = raw.split(":")
    if len(fields) not in (5, 7):
        return None, next_style_id

    if len(fields) == 7:
        style = BrushStyle(
            style_id=next_style_id,
            mode=_mode(fields[3]),
            size=_parse_float32(fields[4]),
            hardness=_parse_float32(fields[5]),
        )
        point_text = fields[6]
        next_style_id += 1
    else:
        if previous_style is None:
            return None, next_style_id
        mode = _mode(fields[3])
        if mode == previous_style.mode:
            style = previous_style
        else:
            style = BrushStyle(
                style_id=next_style_id,
                mode=mode,
                size=previous_style.size,
                hardness=previous_style.hardness,
            )
            next_style_id += 1
        point_text = fields[4]

    point_fields = point_text.split("|")
    if len(point_fields) < 2 or len(point_fields) % 2:
        return None, next_style_id
    points = tuple(
        StrokePoint(_parse_float32(point_fields[index]), _parse_float32(point_fields[index + 1]))
        for index in range(0, len(point_fields), 2)
    )
    stroke = EyeStroke(
        alpha=_parse_float32(fields[0]),
        spacing=_parse_float32(fields[1]),
        rotation=_parse_float32(fields[2]),
        style=style,
        points=points,
    )
    return stroke, next_style_id


def serialize_reanimated_eye_color(model: ReanimatedEyeColor) -> FilterOp:
    """A modellből az eredeti Picasa 5/7 mezős sorát állítja elő."""
    records: list[str] = []
    previous_style: BrushStyle | None = None
    for record in model.strokes:
        if isinstance(record, RawStroke):
            records.append(record.raw)
            previous_style = None
            continue

        fields = [
            format(record.alpha, ".6f"),
            _format_g(record.spacing),
            _format_g(record.rotation),
            str(record.style.mode),
        ]
        if (
            previous_style is None
            or record.style.style_id != previous_style.style_id
        ):
            fields.extend((_format_g(record.style.size), _format_g(record.style.hardness)))
        fields.append(
            "|".join(
                _format_g(value)
                for point in record.points
                for value in (point.x, point.y)
            )
        )
        records.append(":".join(fields))
        previous_style = record.style

    return FilterOp(_FILTER_NAME, model.base_params + tuple(records))
