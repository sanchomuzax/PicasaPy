"""Kollázs-elrendezések — tiszta geometria, képfeldolgozás nélkül (#29).

Minden elrendezés ugyanazt adja vissza: `Placement`-ek sorozatát a vászon
koordinátáiban. Így a geometria önmagában tesztelhető (nincs se OpenCV, se
fájl-IO), a `render.py` pedig csak „képet tesz a helyére".

A Picasa kollázs-típusai közül a determinisztikusan reprodukálhatókat
vittük át:

- **rács** (Picture Grid) — azonos méretű cellák, a képek kitöltik őket;
- **kontaktmásolat** (Contact Sheet) — rács fix oszlopszámmal, a képek
  arányosan, keret nélküli üres hellyel (a Picasa „proof sheet"-je);
- **mozaik** (Frame Mosaic) — az első kép nagy, a többi körülötte
  keretben;
- **képhalom** (Picture Pile) — szórt, forgatott, egymást átfedő képek;
  a szórás MAGVAS (seed) — ugyanaz a bemenet mindig ugyanazt a kollázst
  adja, tehát tesztelhető és megismételhető.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass

# A támogatott típusok azonosítói (a UI és a controller ezeket használja).
GRID = "grid"
CONTACT_SHEET = "contact_sheet"
MOSAIC = "mosaic"
PILE = "pile"

COLLAGE_KINDS = (GRID, CONTACT_SHEET, MOSAIC, PILE)

# A képhalom szórásának határai — a kollázs „kézzel odadobott fotók"
# hatása, de úgy, hogy minden kép látható maradjon.
_PILE_MAX_ANGLE = 18.0
_PILE_SCALE = 0.42


@dataclass(frozen=True)
class Placement:
    """Egy kép helye a vásznon: bal felső sarok, méret, elforgatás (fok).

    Az `angle` a KÉPERNYŐ-konvenció szerinti fok (#1035): a pozitív érték az
    óramutató járásával EGYEZŐ irányba dönt — ugyanaz, amit a `.cxf` `theta`-ja
    és a QML `Item.rotation` jelent. (Az OpenCV ezzel ellentétesen forgat; az
    átfordítás a `render.screen_rotation` dolga, egyetlen helyen.)

    A `fill` dönti el, hogyan illeszkedik a kép a kerethez: True esetén
    kitölti (a túllógó rész levágva — rácsnál ez a szép), False esetén
    arányosan belefér (kontaktmásolat, ahol a teljes kép kell)."""

    x: int
    y: int
    width: int
    height: int
    angle: float = 0.0
    fill: bool = True

    def __post_init__(self) -> None:
        if self.width < 1 or self.height < 1:
            raise ValueError(f"Érvénytelen keretméret: {self.width}×{self.height}")


def grid_shape(count: int) -> tuple[int, int]:
    """A képek számához illő (oszlop, sor) rács — a lehető legnégyzetesebb."""
    if count < 1:
        raise ValueError("Kollázshoz legalább egy kép kell.")
    columns = math.ceil(math.sqrt(count))
    rows = math.ceil(count / columns)
    return (columns, rows)


def _cells(
    count: int,
    width: int,
    height: int,
    columns: int,
    rows: int,
    spacing: int,
    *,
    fill: bool,
) -> tuple[Placement, ...]:
    """Egyenletes rács-cellák; a maradék képpontokat az utolsó sor/oszlop
    nyeli el, hogy a kollázs pontosan kitöltse a vásznat."""
    inner_w = width - spacing * (columns + 1)
    inner_h = height - spacing * (rows + 1)
    if inner_w < columns or inner_h < rows:
        raise ValueError("A vászon túl kicsi ehhez a rácshoz.")
    cell_w = inner_w // columns
    cell_h = inner_h // rows
    placements = []
    for index in range(count):
        row, column = divmod(index, columns)
        placements.append(
            Placement(
                x=spacing + column * (cell_w + spacing),
                y=spacing + row * (cell_h + spacing),
                width=cell_w,
                height=cell_h,
                fill=fill,
            )
        )
    return tuple(placements)


def grid_layout(
    count: int, width: int, height: int, spacing: int = 8
) -> tuple[Placement, ...]:
    """Azonos méretű cellák; a képek kitöltik a cellát (a túllógás levágva)."""
    columns, rows = grid_shape(count)
    return _cells(count, width, height, columns, rows, spacing, fill=True)


def contact_sheet_layout(
    count: int, width: int, height: int, columns: int = 4, spacing: int = 12
) -> tuple[Placement, ...]:
    """Kontaktmásolat: fix oszlopszám, a teljes kép látszik (nincs vágás)."""
    if columns < 1:
        raise ValueError(f"Érvénytelen oszlopszám: {columns}")
    columns = min(columns, count)
    rows = math.ceil(count / columns)
    return _cells(count, width, height, columns, rows, spacing, fill=False)


def mosaic_layout(
    count: int, width: int, height: int, spacing: int = 8
) -> tuple[Placement, ...]:
    """Az első kép nagy (bal felső blokk), a többi körülötte keretben.

    Egyetlen képnél a teljes vászon az övé; kettőnél függőleges osztás.
    A „körülötte" a jobb oldali oszlop + az alsó sáv — a kisképek
    egyenletesen oszlanak el köztük."""
    if count < 1:
        raise ValueError("Kollázshoz legalább egy kép kell.")
    if count == 1:
        return (
            Placement(
                x=spacing,
                y=spacing,
                width=width - 2 * spacing,
                height=height - 2 * spacing,
            ),
        )
    hero_w = (width - 3 * spacing) * 2 // 3
    hero_h = (height - 3 * spacing) * 2 // 3
    if hero_w < 1 or hero_h < 1:
        raise ValueError("A vászon túl kicsi a mozaikhoz.")
    placements = [Placement(x=spacing, y=spacing, width=hero_w, height=hero_h)]

    others = count - 1
    # a maradék képek fele a jobb oszlopba, fele az alsó sávba kerül
    right_count = math.ceil(others / 2)
    bottom_count = others - right_count

    right_x = hero_w + 2 * spacing
    right_w = width - right_x - spacing
    if right_count:
        step = (hero_h - spacing * (right_count - 1)) // right_count
        if step < 1 or right_w < 1:
            raise ValueError("A vászon túl kicsi a mozaikhoz.")
        for i in range(right_count):
            placements.append(
                Placement(
                    x=right_x,
                    y=spacing + i * (step + spacing),
                    width=right_w,
                    height=step,
                )
            )

    bottom_y = hero_h + 2 * spacing
    bottom_h = height - bottom_y - spacing
    if bottom_count:
        step = (width - spacing * (bottom_count + 1)) // bottom_count
        if step < 1 or bottom_h < 1:
            raise ValueError("A vászon túl kicsi a mozaikhoz.")
        for i in range(bottom_count):
            placements.append(
                Placement(
                    x=spacing + i * (step + spacing),
                    y=bottom_y,
                    width=step,
                    height=bottom_h,
                )
            )
    return tuple(placements)


def pile_layout(
    count: int, width: int, height: int, seed: int = 0
) -> tuple[Placement, ...]:
    """Szórt, forgatott képhalom — MAGVAS véletlennel, tehát ismételhető.

    A képek mérete a vászon rövidebb oldalához igazodik, a középpontjuk
    egy belső téglalapon szóródik, hogy egyik se csússzon le a vászonról."""
    if count < 1:
        raise ValueError("Kollázshoz legalább egy kép kell.")
    rng = random.Random(seed)
    card = int(min(width, height) * _PILE_SCALE)
    if card < 2:
        raise ValueError("A vászon túl kicsi a képhalomhoz.")
    margin = card // 2
    placements = []
    for _ in range(count):
        cx = rng.randint(margin, max(margin, width - margin))
        cy = rng.randint(margin, max(margin, height - margin))
        angle = rng.uniform(-_PILE_MAX_ANGLE, _PILE_MAX_ANGLE)
        placements.append(
            Placement(
                x=cx - card // 2,
                y=cy - card // 2,
                width=card,
                height=card,
                angle=angle,
            )
        )
    return tuple(placements)


def layout_for(
    kind: str,
    count: int,
    width: int,
    height: int,
    *,
    spacing: int = 8,
    columns: int = 4,
    seed: int = 0,
) -> tuple[Placement, ...]:
    """A típus-azonosítóhoz tartozó elrendezés; ismeretlen típus = hiba."""
    if kind == GRID:
        return grid_layout(count, width, height, spacing)
    if kind == CONTACT_SHEET:
        return contact_sheet_layout(count, width, height, columns, spacing)
    if kind == MOSAIC:
        return mosaic_layout(count, width, height, spacing)
    if kind == PILE:
        return pile_layout(count, width, height, seed)
    raise ValueError(f"Ismeretlen kollázs-típus: {kind}")
