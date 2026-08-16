"""A „Rács" (`regulargrid`) sor- és oszlopszáma (#431).

Forrás: `docs/specs/picasa-create-features.md` 1.9.8 (`0x00885b00`).

A Rács NEM a Mozaik pakolófáját használja, hanem saját, zárt költségképlettel
választ osztást. Két dolgot mérlegel egymás ellen:

- mennyire tér el a **cella oldalaránya** a képek **átlagos** oldalarányától
  (`q`, 1,7-es súllyal),
- hány **cella marad üresen** (`sor·oszlop − N`, 1-es súllyal).

Vagyis egy üresen maradó cella körülbelül annyit „ér", mint 0,59-nyi relatív
oldalarány-eltérés.

⚠️ Két apróság, ami különben eltérést okoz: az összehasonlítás `<=`, tehát
**döntetlennél a nagyobb sorszám nyer**; és a ciklus 1000 sornál megáll.
"""

from __future__ import annotations

import math
from collections.abc import Sequence

from .rects import NormRect

# A cella-oldalarány eltérésének súlya az üres cellákéhoz képest.
ASPECT_WEIGHT = 1.7

# A dekompilált ciklus felső korlátja.
MAX_ROWS = 1000


def regular_grid_shape(
    aspects: Sequence[float], page_width: int, page_height: int
) -> tuple[int, int]:
    """A képek oldalarányaiból a legjobb `(sor, oszlop)` osztás.

    `aspects` képenként a szélesség/magasság hányados."""
    count = len(aspects)
    if count < 1:
        raise ValueError("A rácshoz legalább egy kép kell.")
    if any(a <= 0.0 for a in aspects):
        raise ValueError("Az oldalarány csak pozitív lehet.")
    if page_width < 1 or page_height < 1:
        raise ValueError(f"Érvénytelen lapméret: {page_width}×{page_height}")

    average_aspect = sum(aspects) / count

    best_rows = 1
    best_cost = math.inf
    for rows in range(1, min(count, MAX_ROWS - 1) + 1):
        columns = math.ceil(count / rows)
        cell_aspect = (page_width / columns) / (page_height / rows)
        ratio = cell_aspect / average_aspect
        if ratio < 1.0:
            ratio = 1.0 / ratio  # szimmetrikus eltérés, mindig >= 1
        cost = ratio * ASPECT_WEIGHT + (rows * columns - count)
        # `<=`: döntetlennél a NAGYOBB sorszám nyer (ez az eredeti viselkedés)
        if cost <= best_cost:
            best_rows = rows
            best_cost = cost

    return (best_rows, math.ceil(count / best_rows))


def regular_grid_rects(count: int, rows: int, columns: int) -> tuple[NormRect, ...]:
    """A rács normalizált cellái balról jobbra, fentről lefelé.

    Az utolsó sor hiányos lehet — a maradék cella egyszerűen kimarad, a
    képek nem nyúlnak szét (ezt bünteti a `regular_grid_shape` költsége)."""
    if count < 1:
        raise ValueError("A rácshoz legalább egy kép kell.")
    if rows < 1 or columns < 1:
        raise ValueError(f"Érvénytelen rács: {rows}×{columns}")
    if rows * columns < count:
        raise ValueError(f"A {rows}×{columns} rácsba nem fér el {count} kép.")

    cells = []
    for index in range(count):
        row, column = divmod(index, columns)
        cells.append(
            NormRect(
                x0=column / columns,
                y0=row / rows,
                x1=(column + 1) / columns,
                y1=(row + 1) / rows,
            )
        )
    return tuple(cells)


__all__ = ["ASPECT_WEIGHT", "MAX_ROWS", "regular_grid_rects", "regular_grid_shape"]
