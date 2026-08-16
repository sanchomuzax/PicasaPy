"""Normalizált téglalapok és a „Rács vastagsága" csúszka (#431).

A Picasa rácsos elrendezései (`picturegrid`, `framegrid`, `regulargrid`)
**normalizált téglalapokban** dolgoznak: minden képnek egy `(x0, y0, x1, y1)`
négyese van a `[0, 1]²` egységnégyzetben. A pakolás ezeket állítja elő, a
rajzolás pedig ebből számol képpontot — a térközzel együtt.

Forrás: `docs/specs/picasa-create-features.md` 1.9.3 (`0x00880e30`).

Két szabály, ami nélkül a kollázs nem néz ki egyenletesnek:

1. **A lap szélét érintő él a TELJES hézagot kapja, a belső élek
   felet-felet.** Így két szomszédos kép közé pontosan egy hézagnyi rés
   kerül, és a külső margó ugyanakkora, mint a belső rés.
2. **A függőleges hézagot a lap oldalaránya (`W/H`) szorozza**, tehát a rés
   KÉPPONTBAN négyzetes — nem a normalizált térben.
"""

from __future__ import annotations

from dataclasses import dataclass

from .fitting import picasa_round

# A csúszka „Max." állása ekkora hézagot ad a legkisebb cella oldalához
# viszonyítva (a dekompilált kódban `0.45f`).
SPACING_FACTOR = 0.45


@dataclass(frozen=True)
class NormRect:
    """Egy cella a `[0, 1]²` egységnégyzetben."""

    x0: float
    y0: float
    x1: float
    y1: float

    def __post_init__(self) -> None:
        if not (0.0 <= self.x0 < self.x1 <= 1.0):
            raise ValueError(f"Érvénytelen vízszintes tartomány: {self.x0}…{self.x1}")
        if not (0.0 <= self.y0 < self.y1 <= 1.0):
            raise ValueError(f"Érvénytelen függőleges tartomány: {self.y0}…{self.y1}")

    @property
    def width(self) -> float:
        return self.x1 - self.x0

    @property
    def height(self) -> float:
        return self.y1 - self.y0

    @property
    def aspect(self) -> float:
        """A cella oldalaránya (szélesség / magasság)."""
        return self.width / self.height


@dataclass(frozen=True)
class PixelRect:
    """Egy cella képpontban, félig nyílt tartománnyal (`x0` benne, `x1` kívül)."""

    x0: int
    y0: int
    x1: int
    y1: int

    @property
    def width(self) -> int:
        return self.x1 - self.x0

    @property
    def height(self) -> int:
        return self.y1 - self.y0


def _edge(value: float, on_border: bool, gap: float, half: float) -> float:
    """A lap szélét érintő él a teljes hézagot kapja, a belső fél hézagot."""
    return gap if on_border else half


def to_pixel_rects(
    rects: tuple[NormRect, ...] | list[NormRect],
    page_width: int,
    page_height: int,
    spacing: float,
) -> tuple[PixelRect, ...]:
    """Normalizált cellákból képpontos cellák, a térköz beszámításával.

    `spacing` a csúszka értéke 0 („None") és 1 („Max.") között."""
    if page_width < 1 or page_height < 1:
        raise ValueError(f"Érvénytelen lapméret: {page_width}×{page_height}")
    if not 0.0 <= spacing <= 1.0:
        raise ValueError(f"Érvénytelen térköz: {spacing} (várt: 0…1)")
    if not rects:
        return ()

    smallest = min(min(rect.width, rect.height) for rect in rects)
    gap = spacing * SPACING_FACTOR * smallest
    half = gap * 0.5
    aspect = page_width / page_height

    boxes = []
    for rect in rects:
        x0 = rect.x0 + _edge(rect.x0, rect.x0 == 0.0, gap, half)
        x1 = rect.x1 - _edge(rect.x1, rect.x1 == 1.0, gap, half)
        y0 = rect.y0 + aspect * _edge(rect.y0, rect.y0 == 0.0, gap, half)
        y1 = rect.y1 - aspect * _edge(rect.y1, rect.y1 == 1.0, gap, half)
        boxes.append(
            PixelRect(
                x0=picasa_round(x0 * page_width),
                y0=picasa_round(y0 * page_height),
                x1=picasa_round(x1 * page_width),
                y1=picasa_round(y1 * page_height),
            )
        )
    return tuple(boxes)


__all__ = ["SPACING_FACTOR", "NormRect", "PixelRect", "to_pixel_rects"]
