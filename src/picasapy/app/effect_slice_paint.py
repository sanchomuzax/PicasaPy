"""Az effekt-térszelvény 3D rajzának geometriája és festése (#6522).

# SAJÁT FUNKCIÓ (#6522): az eredeti Picasában nincs mini 3D effekt-térszelvény.

A rajz a tulajdonossal végigiterált minta szerint készül: a keret 8 sarka
minden forgási szögben kitölti a rajzterületet, a hátsó falak folytonosak és
szintvonalasak, az elülső alapél szaggatott, a felület kék színskálán,
árnyalva, hátulról előre rajzolt négyszögekből áll.
"""

from __future__ import annotations

import math
from collections.abc import Callable, Sequence

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QPainter, QPen, QPolygonF

ELEVATION = 28.0
BASE_AZIMUTH = -32.0

# a nézettípusonkénti doboz-arányok (szélesség, mélység, magasság) a minta szerint
DIMENSIONS = {
    "tone": (1.0, 0.7, 0.5),
    "identity": (1.0, 0.7, 0.5),
    "image": (1.0, 0.7, 0.4),
    "point": (1.0, 1.0, 0.5),
    "grain": (1.0, 0.7, 0.35),
    "color": (1.0, 1.0, 0.85),
}

_RAMP = ((227, 237, 248), (120, 163, 216), (29, 79, 145))
_LIGHT = (-0.45, -0.35, 0.82)
MARKER_COLOR = QColor("#d9480f")
CHANNEL_COLORS = (QColor("#c62828"), QColor("#2e7d32"), QColor("#1565c0"))

Projector = Callable[[float, float, float], tuple[float, float, float]]


def make_projection(
    dims: Sequence[float], azimuth: float, elevation: float, rect: QRectF
) -> Projector:
    """(u, v, w) ∈ [0, 1]³ → (képernyő-x, képernyő-y, mélység); nagyobb mélység = hátrébb."""
    a = math.radians(azimuth)
    e = math.radians(elevation)
    ca, sa, ce, se = math.cos(a), math.sin(a), math.cos(e), math.sin(e)

    def raw(u: float, v: float, w: float) -> tuple[float, float, float]:
        x = (u - 0.5) * dims[0]
        y = (v - 0.5) * dims[1]
        z = w * dims[2]
        rx = x * ca - y * sa
        ry = x * sa + y * ca
        return rx, -(z * ce + ry * se), ry

    corners = [raw(u, v, w) for u in (0, 1) for v in (0, 1) for w in (0, 1)]
    x0 = min(c[0] for c in corners)
    x1 = max(c[0] for c in corners)
    y0 = min(c[1] for c in corners)
    y1 = max(c[1] for c in corners)
    scale = min((rect.width() - 4.0) / (x1 - x0), (rect.height() - 3.0) / (y1 - y0))
    ox = rect.x() + (rect.width() - (x1 - x0) * scale) / 2.0 - x0 * scale
    oy = rect.y() + (rect.height() - (y1 - y0) * scale) / 2.0 - y0 * scale

    def project(u: float, v: float, w: float) -> tuple[float, float, float]:
        px, py, depth = raw(u, v, w)
        return px * scale + ox, py * scale + oy, depth

    return project


def ramp_color(level: float, shade: float) -> QColor:
    """A minta kék színskálája (világos → sötétkék), fényerő-szorzóval."""
    t = max(0.0, min(1.0, level))
    low, high, local = (
        (_RAMP[0], _RAMP[1], t * 2.0) if t < 0.5 else (_RAMP[1], _RAMP[2], (t - 0.5) * 2.0)
    )
    channels = [
        round(min(255.0, (low[i] + (high[i] - low[i]) * local) * shade)) for i in range(3)
    ]
    return QColor(*channels)


def _point(projected: tuple[float, float, float]) -> QPointF:
    return QPointF(projected[0], projected[1])


def paint_frame(painter: QPainter, project: Projector) -> None:
    """Szintvonalas hátsó falak, folytonos hátsó élek, szaggatott elülső alapélek."""
    corners = ((0, 0), (1, 0), (1, 1), (0, 1))
    floor = [project(u, v, 0.0) for u, v in corners]
    top = [project(u, v, 1.0) for u, v in corners]
    near = min(range(4), key=lambda index: floor[index][2])
    grid, back, front = [], [], []
    for i in range(4):
        j = (i + 1) % 4
        if near in (i, j):
            front.append((floor[i], floor[j]))
            continue
        back.append((floor[i], floor[j]))
        back.append((top[i], top[j]))
        for step in (0.25, 0.5, 0.75):
            grid.append((project(*corners[i], step), project(*corners[j], step)))
    back.extend((floor[i], top[i]) for i in range(4) if i != near)
    for lines, pen in (
        (grid, QPen(QColor("#d0d0d0"), 0.4)),
        (back, QPen(QColor("#a0a0a0"), 0.5)),
        (front, _dashed(QColor("#a0a0a0"), 0.5, (2.0, 1.5))),
    ):
        painter.setPen(pen)
        for start, end in lines:
            painter.drawLine(_point(start), _point(end))


def _dashed(color: QColor, width: float, pattern: tuple[float, float]) -> QPen:
    pen = QPen(color, width)
    pen.setDashPattern([value / width for value in pattern])
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    return pen


def paint_surface(
    painter: QPainter, project: Projector, rows: Sequence[Sequence[float]], dims
) -> None:
    """Árnyalt kék felület, hátulról előre rajzolt négyszögekből (takarás)."""
    row_count = len(rows)
    col_count = min((len(row) for row in rows), default=0)
    if row_count < 2 or col_count < 2:
        return
    nu, nv = col_count - 1, row_count - 1
    faces = []
    for j in range(nv):
        for i in range(nu):
            h00, h10 = _height(rows, j, i), _height(rows, j, i + 1)
            h11, h01 = _height(rows, j + 1, i + 1), _height(rows, j + 1, i)
            quad = (
                project(i / nu, j / nv, h00),
                project((i + 1) / nu, j / nv, h10),
                project((i + 1) / nu, (j + 1) / nv, h11),
                project(i / nu, (j + 1) / nv, h01),
            )
            dzx = ((h10 - h00) + (h11 - h01)) / 2.0 * dims[2] / (dims[0] / nu)
            dzy = ((h01 - h00) + (h11 - h10)) / 2.0 * dims[2] / (dims[1] / nv)
            norm = math.sqrt(dzx * dzx + dzy * dzy + 1.0)
            dot = (-dzx * _LIGHT[0] - dzy * _LIGHT[1] + _LIGHT[2]) / norm
            shade = max(0.62, min(1.08, 0.7 + 0.34 * dot))
            level = (h00 + h10 + h11 + h01) / 4.0
            depth = sum(corner[2] for corner in quad) / 4.0
            faces.append((depth, quad, ramp_color(level, shade)))
    faces.sort(key=lambda face: -face[0])
    painter.setPen(QPen(QColor(255, 255, 255, 82), 0.3))
    for _depth, quad, color in faces:
        painter.setBrush(color)
        painter.drawPolygon(QPolygonF([_point(corner) for corner in quad]))
    painter.setBrush(Qt.BrushStyle.NoBrush)


def _height(rows, row: int, col: int) -> float:
    return max(0.0, min(1.0, float(rows[row][col])))


def paint_polyline(
    painter: QPainter,
    project: Projector,
    depth: float,
    heights: Sequence[float],
    color: QColor,
    width: float,
) -> None:
    """Egy mélységi állású metszet (narancs jelölő vagy csatornavonal)."""
    count = len(heights)
    if count < 2:
        return
    painter.setPen(QPen(color, width))
    painter.drawPolyline(
        QPolygonF(
            [
                _point(project(index / (count - 1), depth, _clamp(heights[index])))
                for index in range(count)
            ]
        )
    )


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def interpolate_row(rows: Sequence[Sequence[float]], position: float) -> list[float]:
    """A mélységtengely tört helyén két szomszédos sor lineáris keveréke."""
    if not rows:
        return []
    last = len(rows) - 1
    exact = max(0.0, min(1.0, position)) * last
    low = int(math.floor(exact))
    high = min(last, low + 1)
    weight = exact - low
    return [
        float(a) * (1.0 - weight) + float(b) * weight for a, b in zip(rows[low], rows[high], strict=False)
    ]


def paint_color_cube(painter: QPainter, project: Projector, points: Sequence[dict]) -> None:
    """Szaggatott eredeti színtér-kocka, átló, a kimenő színek rácsa és pontjai."""
    reference = [
        project(*corner)
        for corner in (
            (0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0),
            (0, 0, 1), (1, 0, 1), (1, 1, 1), (0, 1, 1),
        )
    ]
    edges = (
        (0, 1), (1, 2), (2, 3), (3, 0), (4, 5), (5, 6),
        (6, 7), (7, 4), (0, 4), (1, 5), (2, 6), (3, 7),
    )
    painter.setPen(_dashed(QColor("#9c9c9c"), 0.5, (2.0, 1.5)))
    for start, end in edges:
        painter.drawLine(_point(reference[start]), _point(reference[end]))
    painter.setPen(_dashed(QColor("#7a7a7a"), 0.6, (0.6, 1.4)))
    painter.drawLine(_point(reference[0]), _point(reference[6]))
    steps = round(len(points) ** (1.0 / 3.0))
    if steps < 2 or steps**3 != len(points):
        return
    projected = [
        project(float(p.get("x", 0.0)), float(p.get("y", 0.0)), float(p.get("z", 0.0)))
        for p in points
    ]
    painter.setPen(QPen(QColor(50, 50, 50, 71), 0.45))
    for a in range(steps):
        for b in range(steps):
            for c in range(steps):
                index = (a * steps + b) * steps + c
                for neighbour, ok in (
                    (index + steps * steps, a < steps - 1),
                    (index + steps, b < steps - 1),
                    (index + 1, c < steps - 1),
                ):
                    if ok:
                        painter.drawLine(_point(projected[index]), _point(projected[neighbour]))
    painter.setPen(QPen(QColor(0, 0, 0, 115), 0.35))
    for index in sorted(range(len(points)), key=lambda k: -projected[k][2]):
        rgb = points[index].get("color") or (120, 140, 170)
        painter.setBrush(QColor(int(rgb[0]), int(rgb[1]), int(rgb[2])))
        painter.drawEllipse(_point(projected[index]), 2.1, 2.1)
    painter.setBrush(Qt.BrushStyle.NoBrush)
