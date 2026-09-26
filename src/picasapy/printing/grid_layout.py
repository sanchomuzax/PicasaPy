"""A nyomatméret mint CELLA — rácsba rendezett nyomtatási lapok (#3647).

Az eredeti Picasa a kiválasztott nyomatméretet (4x6, 5x7, Tárcaméret…)
CELLAKÉNT kezeli, és a nyomtató papírján rácsba rendezi:

- sorfolytonosan rak, amíg a sor belefér, aztán új sort kezd;
- ha a következő sor már nem fér el, ÚJ LAPOT kezd ott, ahol abbahagyta —
  a kép- és a példányszámláló megmarad, nem indul újra;
- a maradék helyet laponként egyenletes térközként osztja szét;
- a tájolást úgy választja, hogy KEVESEBB lap legyen; döntetlennél az
  eredeti (portré) marad.

Forrás: `docs/specs/picasa-nyomtatas.md`, „A rácselrendező LAPTÖRÉSE” és az
előtte álló szakasz — célzott dekompiláció (`0x00778640`, `0x00778190`,
`0x007774b0`), élő méréssel megerősítve (Colab EN 3.9.141, PDF-nyomtató,
A4, 300 dpi).

Ez a modul Qt-független és determinisztikus, mint a `layout.py` és a
`contact_sheet.py` — a `picasapy.app.print_controller.PrintController`
hívja, a nyomtató (vagy az előnézet) tényleges lapgeometriájával."""

from __future__ import annotations

import math
from dataclasses import dataclass

from .layout import PageGeometry

#: A sor/oszlop-illesztés TŰRÉSE — mérve (`docs/specs/picasa-nyomtatas.md`,
#: „0,999-es tűrés”). Lebegőpontos kerekítés ellen véd: egy cella, ami
#: elméletileg PONTOSAN kitölti a sort, ne essen ki egy huszadmilliomodnyi
#: eltérés miatt.
FIT_TOLERANCE = 0.999

#: Ha a laponkénti egyenletes térköz a cella méretének ennyi hányada ALÁ
#: esne, a cellákat kicsinyítjük (ld. `GAP_SHRINK_FACTOR`).
#:
#: ⚠️ SAJÁT DÖNTÉS a viszonyítási alapban. A mérés a küszöböt és a
#: kicsinyítést KONSTANSKÉNT azonosította (`0xcf4748`/`0xc7e4b0` → 0,2;
#: `0xcf4a30` → 0,975, ld. a specifikációt), de hogy a 0,2 MIHEZ képest
#: relatív (a cellamérethez, a lapmérethez, vagy abszolút hüvelyk), abból
#: nincs kimérve. Itt a cellaméret hányadaként értelmezzük — ez skálázódik
#: a legkisebb (Tárcaméret) és a legnagyobb (FullPage) nyomatmérettel is,
#: szemben egy abszolút értékkel, ami az egyiknél jelentéktelen, a
#: másiknál eltúlzott lenne.
GAP_SHRINK_THRESHOLD_RATIO = 0.2

#: A mért kicsinyítő szorzó (ld. a fenti megjegyzést).
GAP_SHRINK_FACTOR = 0.975


@dataclass(frozen=True)
class GridCell:
    """Egy cella rajzolási téglalapja a lap bal felső sarkától mérve."""

    x: float
    y: float
    width: float
    height: float


@dataclass(frozen=True)
class GridPage:
    """Egy nyomtatott lap.

    A `first`/`count` a nyomtatandó képek (már a példányszámmal
    megsokszorozott) listájába mutat — ugyanaz a jelentés, mint a
    `contact_sheet.ContactSheetPage`-nél."""

    first: int
    count: int
    cells: tuple[GridCell, ...]

    def __post_init__(self) -> None:
        if self.count != len(self.cells):
            raise ValueError(
                f"{self.count} cella várt, de {len(self.cells)} hely készült"
            )


def page_capacity(
    page: PageGeometry,
    cell_width: float,
    cell_height: float,
    *,
    tolerance: float = FIT_TOLERANCE,
) -> tuple[int, int]:
    """Hány cella fér el a nyomtatható területen: (oszlop, sor).

    A `tolerance` a lebegőpontos kerekítés ellen véd: egy cella, ami
    elméletileg pontosan kitölti a sort/oszlopot, ne essen ki egy
    huszadmilliomodnyi eltérés miatt."""
    if cell_width <= 0 or cell_height <= 0:
        raise ValueError(f"Érvénytelen cellaméret: {cell_width}x{cell_height}")
    columns = int(page.printable_width / cell_width + (1.0 - tolerance))
    rows = int(page.printable_height / cell_height + (1.0 - tolerance))
    return max(columns, 0), max(rows, 0)


def _evenly_spaced(
    count: int,
    printable: float,
    size: float,
    *,
    gap_threshold_ratio: float,
    shrink_factor: float,
) -> tuple[tuple[float, ...], float]:
    """`count` darab, `size` méretű elem kezdőpontja egy sorban/oszlopban,
    a maradék hely egyenletesen elosztva köztük és a szélükön.

    Ha az így adódó térköz a cellaméret `gap_threshold_ratio` hányada alá
    esne, a cellákat `shrink_factor`-ral kicsinyítjük, és a (most már
    nagyobb) maradékot újraosztjuk — ld. a modul fejlécét."""
    gap = (printable - count * size) / (count + 1)
    if gap < size * gap_threshold_ratio:
        size *= shrink_factor
        gap = (printable - count * size) / (count + 1)
    gap = max(gap, 0.0)
    positions = tuple(gap * (index + 1) + size * index for index in range(count))
    return positions, size


def grid_pages(
    page: PageGeometry,
    cell_width: float,
    cell_height: float,
    count: int,
    *,
    tolerance: float = FIT_TOLERANCE,
    gap_threshold_ratio: float = GAP_SHRINK_THRESHOLD_RATIO,
    shrink_factor: float = GAP_SHRINK_FACTOR,
) -> tuple[GridPage, ...]:
    """`count` egyforma méretű cella lapokra osztva.

    Sorfolytonosan tölt (amíg a sor belefér), és ÚJ LAPOT kezd, ha a
    következő sor már nem fér el — a kép-/példányszámláló (a `first`)
    folytatódik, nem indul újra: a túlcsorduló cella a következő lap ELSŐ
    cellája.

    A térköz LAPONKÉNT egyenletes: a részben teli utolsó lap cellái a
    maradék helyen oszlanak el, nem nőnek óriásira (ugyanaz a döntés, mint
    a `contact_sheet.sheet_pages`-nél)."""
    if count < 1:
        raise ValueError("Legalább egy cella kell.")
    columns, rows_capacity = page_capacity(
        page, cell_width, cell_height, tolerance=tolerance
    )
    per_page = columns * rows_capacity
    if per_page < 1:
        raise ValueError("A cella nem fér el a lap nyomtatható területén.")

    pages: list[GridPage] = []
    for first in range(0, count, per_page):
        n = min(per_page, count - first)
        rows_used = math.ceil(n / columns)
        y_positions, row_height = _evenly_spaced(
            rows_used,
            page.printable_height,
            cell_height,
            gap_threshold_ratio=gap_threshold_ratio,
            shrink_factor=shrink_factor,
        )
        cells: list[GridCell] = []
        remaining = n
        for y in y_positions:
            in_row = min(columns, remaining)
            x_positions, col_width = _evenly_spaced(
                in_row,
                page.printable_width,
                cell_width,
                gap_threshold_ratio=gap_threshold_ratio,
                shrink_factor=shrink_factor,
            )
            for x in x_positions:
                cells.append(
                    GridCell(
                        x=page.margin + x,
                        y=page.margin + y,
                        width=col_width,
                        height=row_height,
                    )
                )
            remaining -= in_row
        pages.append(GridPage(first=first, count=n, cells=tuple(cells)))
    return tuple(pages)


def choose_page_orientation(
    portrait_page: PageGeometry,
    landscape_page: PageGeometry,
    cell_width: float,
    cell_height: float,
    count: int,
    **kwargs,
) -> tuple[bool, tuple[GridPage, ...]]:
    """A portré és a fekvő lapméret közül a KEVESEBB lapot adót választja.

    Visszaadja, hogy a fekvőt kellett-e választani (`True`), és a kész
    lapokat. Döntetlennél a portré (`False`) marad — ez az „eredeti”
    (`0x00778238`–`0x00778276`: a felcserélt tájolás csak akkor nyer, ha
    SZIGORÚAN kevesebb lapot ad).

    Ha az egyik lapállásba a cella BE SEM fér, a másikat veszi; ha
    egyikbe sem, `ValueError`-t dob (a bináris ilyenkor `-1`-gyel tér
    vissza, ld. a modul fejlécét)."""
    portrait_pages: tuple[GridPage, ...] | None
    landscape_pages: tuple[GridPage, ...] | None
    try:
        portrait_pages = grid_pages(
            portrait_page, cell_width, cell_height, count, **kwargs
        )
    except ValueError:
        portrait_pages = None
    try:
        landscape_pages = grid_pages(
            landscape_page, cell_width, cell_height, count, **kwargs
        )
    except ValueError:
        landscape_pages = None

    if portrait_pages is None and landscape_pages is None:
        raise ValueError(
            "A megadott cellaméret egyik lapállásban sem fér el a "
            "nyomtatható területen."
        )
    if portrait_pages is None:
        return True, landscape_pages
    if landscape_pages is None:
        return False, portrait_pages
    if len(landscape_pages) < len(portrait_pages):
        return True, landscape_pages
    return False, portrait_pages


__all__ = [
    "FIT_TOLERANCE",
    "GAP_SHRINK_FACTOR",
    "GAP_SHRINK_THRESHOLD_RATIO",
    "GridCell",
    "GridPage",
    "choose_page_orientation",
    "grid_pages",
    "page_capacity",
]
