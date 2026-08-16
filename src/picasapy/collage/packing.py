"""A Mozaik (`picturegrid`) bináris pakolófája (#431).

Forrás: `docs/specs/picasa-create-features.md` 1.9.7 (a keresés és a
költség), 1.9.9 (a faépítés) és 1.9.10 (melyik stratégia mikor fut).

A Mozaik **guillotine-felosztás**: a lapot rekurzívan két részre vágja, a
levelek a képek cellái. A keresés **két szinten** megy — kívül 0,5
másodpercig véletlen sorrendeket próbál, belül minden sorrendre több
felosztást —, és azt tartja meg, amelyik a legkevesebb területet hagyja
üresen a cellákban.

**A költség = a cellákban ÜRESEN maradó terület.** A képek nem torzulnak: a
cella marad üres, és ezt bünteti a költség. Pontosan ezt ígéri a súgó is:
„Mozaik: a képek automatikus illesztése az oldalra."

> ⚠️ **A Mozaik NEM determinisztikus.** A keresés valós órához van kötve
> (`QueryPerformanceCounter`) és `_rand()`-ot használ, tehát ugyanaz a
> képhalmaz kétszer futtatva más elrendezést adhat. Ezt nem „javítjuk meg":
> az eredeti viselkedés ez. Az órát és a véletlenforrást viszont be lehet
> fecskendezni, hogy a teszt megismételhető legyen — és a `.cxf`-ből
> visszatöltés (`cxf.py`) pontos.

**A geometria alapazonossága** (ez adja a két vágásirányt):

| ha a két blokkot… | a keletkező blokk oldalaránya |
|---|---|
| **egymás mellé** tesszük (azonos magasság) | `a1 + a2` |
| **egymás alá** tesszük (azonos szélesség) | `a1·a2 / (a1 + a2)` |

**Amit nem építettünk meg:** a spec négy faépítőt sorol fel (1.9.9); a
második (`0x00894940`, „költségvezérelt páros összevonás mind a 16
vágásirány-kombinációval") a legkevésbé rekonstruált, ezért kimaradt. Mivel
a választás mindig a legolcsóbb fát tartja meg, egy építő hiánya csak a
minőséget csökkentheti kicsit, a helyességet nem érinti. A `CGravityTree`
szándékosan hiányzik: a spec 1.9.10 szerint a Picasa 3.9-ben **soha nem
fut**, a beállítója halott kód.
"""

from __future__ import annotations

import math
import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass

from .rects import NormRect

# Egymás mellé (azonos magasság) — az oldalarányok összeadódnak.
CUT_SIDE_BY_SIDE = "side_by_side"
# Egymás alá (azonos szélesség) — harmonikus közép.
CUT_STACKED = "stacked"

# A keresés valós idejű korlátja másodpercben (a fa `+0x30` mezője).
PACK_TIME_LIMIT = 0.5

# Ennyi kép alatt fut a `CFullSearchTree` a finomító körrel.
FULL_SEARCH_LIMIT = 14

# A finomító kör csere-jelöltjeinek száma (`0x0088ed40`).
REFINE_CANDIDATES = 100

# A költségfüggvény alatt nullának számító veszteség.
_COST_EPSILON = 1e-5

# A gyerekek célaránya sosem csúszhat nullára vagy alá.
_MIN_TARGET = 1e-4


@dataclass(frozen=True)
class PackNode:
    """A pakolófa egy csomópontja.

    Levél esetén `index` a kép sorszáma, `left`/`right`/`cut` üres. Belső
    csomópontnál `cut` a vágásirány, `aspect` pedig a keletkező blokk
    oldalaránya (a két gyerek TÉNYLEGES arányából, nem a célarányból —
    különben a képek nem férnének el a celláikban)."""

    aspect: float
    index: int | None = None
    cut: str | None = None
    left: PackNode | None = None
    right: PackNode | None = None

    @property
    def is_leaf(self) -> bool:
        return self.index is not None

    @property
    def leaf_count(self) -> int:
        if self.is_leaf:
            return 1
        left = 0 if self.left is None else self.left.leaf_count
        right = 0 if self.right is None else self.right.leaf_count
        return left + right


# --- A geometria ------------------------------------------------------------


def combined_aspect(cut: str, aspect1: float, aspect2: float) -> float:
    """A két blokkból keletkező blokk oldalaránya."""
    if aspect1 <= 0.0 or aspect2 <= 0.0:
        raise ValueError(f"Érvénytelen oldalarány: {aspect1}, {aspect2}")
    if cut == CUT_SIDE_BY_SIDE:
        return aspect1 + aspect2
    if cut == CUT_STACKED:
        return aspect1 * aspect2 / (aspect1 + aspect2)
    raise ValueError(f"Ismeretlen vágásirány: {cut!r}")


def choose_cut(target: float, aspect1: float, aspect2: float) -> str:
    """A vágásirány: amelyik jelölt oldalaránya közelebb esik a célhoz.

    Ezt egészíti ki a **tájolás-megőrző** peremeset: ha az egyik jelölt
    „átbillenne" az 1,0-s határon — álló cellából fekvő blokkot csinálna
    vagy fordítva —, akkor a tájolást megőrző jelölt nyer, akkor is, ha
    numerikusan távolabb van.

    > A peremeset olvasata a specben **következtetés** (a dekompilátor ott
    > FPU-jelzőbit-manipulációként adja vissza a `bool`-t). Az általános ág
    > és a két jelölt képlete viszont egyértelmű."""
    side = combined_aspect(CUT_SIDE_BY_SIDE, aspect1, aspect2)
    stacked = combined_aspect(CUT_STACKED, aspect1, aspect2)

    target_landscape = target > 1.0
    side_keeps = (side > 1.0) == target_landscape
    stacked_keeps = (stacked > 1.0) == target_landscape
    if side_keeps != stacked_keeps:
        return CUT_SIDE_BY_SIDE if side_keeps else CUT_STACKED

    return (
        CUT_SIDE_BY_SIDE
        if abs(side - target) <= abs(stacked - target)
        else CUT_STACKED
    )


def adjust_target(target: float, aspect1: float, aspect2: float, cut: str) -> float:
    """A `t` korrekció, amivel a két gyerek EGYÜTT pontosan a kívánt
    `target` arányt adná ki.

    ```c
    // egymás mellé:  (a1+t) + (a2+t) = A
    t = ((A - a1) - a2) * 0.5f;

    // egymás alá:    (a1+t)(a2+t) / ((a1+t)+(a2+t)) = A
    b = (a1 + a2) - 2*A;
    t = ( sqrtf(b*b - 4*(a1*a2 - A*a2 - A*a1)) - b ) * 0.5f;
    ```

    A második eset diszkriminánsa kifejtve `(a1 − a2)² + 4A²`, tehát **sosem
    negatív** — a másodfokú egyenletnek mindig van valós gyöke."""
    if cut == CUT_SIDE_BY_SIDE:
        return ((target - aspect1) - aspect2) * 0.5
    if cut == CUT_STACKED:
        b = (aspect1 + aspect2) - 2.0 * target
        discriminant = b * b - 4.0 * (
            aspect1 * aspect2 - target * aspect2 - target * aspect1
        )
        # matematikailag nem lehet negatív; a max() csak a lebegőpontos zaj ellen
        return (math.sqrt(max(discriminant, 0.0)) - b) * 0.5
    raise ValueError(f"Ismeretlen vágásirány: {cut!r}")


def _merge(target: float, left: PackNode, right: PackNode) -> PackNode:
    """Két blokk összevonása a célarányhoz illő iránnyal."""
    cut = choose_cut(target, left.aspect, right.aspect)
    return PackNode(
        aspect=combined_aspect(cut, left.aspect, right.aspect),
        cut=cut,
        left=left,
        right=right,
    )


# --- A négy (nálunk három) faépítő ------------------------------------------


def _average_aspect(aspects: Sequence[float], low: int, high: int) -> float:
    return sum(aspects[low:high]) / (high - low)


def build_guillotine(target: float, aspects: Sequence[float]) -> PackNode:
    """Rekurzív guillotine-építő (`0x00894bd0`) — a legtisztább változat.

    A lista közepén vág, **páros határra igazítva** (`ha (közép & 1) != 0 és
    n > 2, akkor közép++`), a két félnek kiszámolja az átlagos oldalarányát,
    ebből választ irányt, és a kiigazított célaránnyal megy tovább."""
    if target <= 0.0:
        raise ValueError(f"Érvénytelen célarány: {target}")
    if not aspects:
        raise ValueError("A pakoláshoz legalább egy kép kell.")
    if any(a <= 0.0 for a in aspects):
        raise ValueError("Az oldalarány csak pozitív lehet.")

    def build(goal: float, low: int, high: int) -> PackNode:
        count = high - low
        if count == 1:
            return PackNode(aspect=aspects[low], index=low)

        middle = low + count // 2
        if (middle & 1) != 0 and count > 2:
            middle += 1  # PÁROS határra igazít

        aspect1 = _average_aspect(aspects, low, middle)
        aspect2 = _average_aspect(aspects, middle, high)
        cut = choose_cut(goal, aspect1, aspect2)
        shift = adjust_target(goal, aspect1, aspect2, cut)

        left = build(max(aspect1 + shift, _MIN_TARGET), low, middle)
        right = build(max(aspect2 + shift, _MIN_TARGET), middle, high)
        return PackNode(
            aspect=combined_aspect(cut, left.aspect, right.aspect),
            cut=cut,
            left=left,
            right=right,
        )

    return build(target, 0, len(aspects))


def build_zigzag(target: float, aspects: Sequence[float]) -> PackNode:
    """Cikcakk páros összevonás (`0x00894470`).

    Minden szinten a szomszédos elemeket párosítja — az egyik szinten
    elölről, a következőn hátulról, váltakozva. Páratlan elemszámnál az
    utolsó változatlanul lép a következő szintre."""
    level = _leaves(aspects)
    forward = True
    while len(level) > 1:
        items = level if forward else list(reversed(level))
        merged: list[PackNode] = []
        for i in range(0, len(items) - 1, 2):
            merged.append(_merge(target, items[i], items[i + 1]))
        if len(items) % 2:
            merged.append(items[-1])
        if not forward:
            merged.reverse()
        level = merged
        forward = not forward
    return level[0]


def build_power_of_two(target: float, aspects: Sequence[float]) -> PackNode:
    """Kettőhatványra igazítás (`0x00893da0`).

    Addig von össze szomszédos párokat, amíg a szint elemszáma pontosan
    `2^k` nem lesz, onnantól tökéletesen kiegyensúlyozott bináris fa."""
    level = _leaves(aspects)
    while len(level) > 1 and (len(level) & (len(level) - 1)) != 0:
        level = [_merge(target, level[0], level[1]), *level[2:]]
    while len(level) > 1:
        level = [
            _merge(target, level[i], level[i + 1]) for i in range(0, len(level), 2)
        ]
    return level[0]


def _leaves(aspects: Sequence[float]) -> list[PackNode]:
    if not aspects:
        raise ValueError("A pakoláshoz legalább egy kép kell.")
    if any(a <= 0.0 for a in aspects):
        raise ValueError("Az oldalarány csak pozitív lehet.")
    return [PackNode(aspect=aspect, index=i) for i, aspect in enumerate(aspects)]


BUILDERS = (build_guillotine, build_zigzag, build_power_of_two)


# --- A cellák és a költség --------------------------------------------------


def _clamp01(value: float) -> float:
    return min(1.0, max(0.0, value))


def assign_rects(tree: PackNode, count: int) -> tuple[NormRect, ...]:
    """A fából normalizált cellák, a KÉPEK eredeti sorrendjében.

    A felosztás a gyerekek tényleges oldalarányát követi: egymás mellett a
    szélességek `a1 : a2` arányban, egymás alatt a magasságok `1/a1 : 1/a2`
    arányban oszlanak meg (ez utóbbi `a2 : a1`-re egyszerűsödik)."""
    cells: dict[int, NormRect] = {}

    def walk(node: PackNode, x0: float, y0: float, x1: float, y1: float) -> None:
        if node.is_leaf:
            cells[int(node.index)] = NormRect(
                _clamp01(x0), _clamp01(y0), _clamp01(x1), _clamp01(y1)
            )
            return
        left, right = node.left, node.right
        if left is None or right is None:
            raise ValueError("Hiányos pakolófa.")
        total = left.aspect + right.aspect
        if node.cut == CUT_SIDE_BY_SIDE:
            split = x0 + (x1 - x0) * (left.aspect / total)
            walk(left, x0, y0, split, y1)
            walk(right, split, y0, x1, y1)
        else:
            split = y0 + (y1 - y0) * (right.aspect / total)
            walk(left, x0, y0, x1, split)
            walk(right, x0, split, x1, y1)

    walk(tree, 0.0, 0.0, 1.0, 1.0)
    if len(cells) != count:
        raise ValueError(f"{count} képhez {len(cells)} cella készült.")
    return tuple(cells[i] for i in range(count))


def packing_cost(
    rects: Sequence[NormRect],
    aspects: Sequence[float],
    constraint: NormRect | None = None,
) -> float:
    """A pakolás költsége: a cellákban **üresen maradó** terület összege.

    A `constraint` a Képkockamozaik hangsúlyos középső területe — ha meg van
    adva, a cellák méretét ezzel szorozza a költségszámítás."""
    if len(rects) != len(aspects):
        raise ValueError("A cellák és a képek száma nem egyezik.")
    total = 0.0
    for rect, aspect in zip(rects, aspects, strict=True):
        width, height = rect.width, rect.height
        if constraint is not None:
            width *= constraint.width
            height *= constraint.height
        if width / aspect <= height:
            fitted_width, fitted_height = width, width / aspect
        else:
            fitted_width, fitted_height = aspect * height, height
        loss = abs(width * height - fitted_width * fitted_height)
        total += 0.0 if loss < _COST_EPSILON else loss
    return total


# --- A keresés --------------------------------------------------------------


def _best_tree(
    page_aspect: float, aspects: Sequence[float], constraint: NormRect | None
) -> tuple[tuple[NormRect, ...], float]:
    """A több faépítő közül a legolcsóbb eredménye (`0x00891fc0`)."""
    best_rects: tuple[NormRect, ...] | None = None
    best_cost = math.inf
    for builder in BUILDERS:
        rects = assign_rects(builder(page_aspect, aspects), count=len(aspects))
        cost = packing_cost(rects, aspects, constraint)
        if cost < best_cost:
            best_rects, best_cost = rects, cost
    if best_rects is None:  # pragma: no cover — a BUILDERS sosem üres
        raise ValueError("Egyetlen faépítő sem adott eredményt.")
    return (best_rects, best_cost)


def _shuffle(order: Sequence[int], rng) -> list[int]:
    """Fisher–Yates `rand() % n`-nel (`0x0088fcf0`)."""
    items = list(order)
    for i in range(len(items) - 1, 0, -1):
        j = rng.rand() % (i + 1)
        items[i], items[j] = items[j], items[i]
    return items


def pack(
    aspects: Sequence[float],
    page_aspect: float,
    rng,
    *,
    constraint: NormRect | None = None,
    time_limit: float = PACK_TIME_LIMIT,
    clock: Callable[[], float] = time.perf_counter,
) -> tuple[NormRect, ...]:
    """A Mozaik pakolása: időkorlátos keresés véletlen sorrendekkel.

    A kiinduló jelölt a képek EREDETI sorrendjéből épül, és csak szigorúan
    olcsóbb elrendezés válthatja le — a végeredmény tehát sosem rosszabb a
    kiindulónál.

    `rng` egy `MsvcRandom`-szerű objektum (`rand()` metódussal), `clock` a
    másodperceket adó óra — mindkettő befecskendezhető, hogy a teszt
    megismételhető legyen."""
    if not aspects:
        raise ValueError("A pakoláshoz legalább egy kép kell.")
    if any(a <= 0.0 for a in aspects):
        raise ValueError("Az oldalarány csak pozitív lehet.")
    if page_aspect <= 0.0:
        raise ValueError(f"Érvénytelen lapoldalarány: {page_aspect}")

    identity = list(range(len(aspects)))
    best_rects, best_cost = _best_tree(page_aspect, aspects, constraint)
    best_order = identity

    start = clock()
    while clock() - start < time_limit:
        candidate = _shuffle(identity, rng)
        rects, cost = _evaluate(candidate, aspects, page_aspect, constraint)
        if cost < best_cost:
            best_rects, best_cost, best_order = rects, cost, candidate

    if len(aspects) < FULL_SEARCH_LIMIT:
        best_rects, best_cost = _refine(
            best_order, best_rects, best_cost, aspects, page_aspect, constraint, rng
        )
    return best_rects


def _evaluate(
    order: Sequence[int],
    aspects: Sequence[float],
    page_aspect: float,
    constraint: NormRect | None,
) -> tuple[tuple[NormRect, ...], float]:
    """Egy sorrend kiértékelése; a cellák az EREDETI képsorrendbe rendezve."""
    reordered = [aspects[i] for i in order]
    rects, cost = _best_tree(page_aspect, reordered, constraint)
    restored: list[NormRect | None] = [None] * len(order)
    for position, original in enumerate(order):
        restored[original] = rects[position]
    return (tuple(rect for rect in restored if rect is not None), cost)


def _refine(
    order: Sequence[int],
    rects: tuple[NormRect, ...],
    cost: float,
    aspects: Sequence[float],
    page_aspect: float,
    constraint: NormRect | None,
    rng,
) -> tuple[tuple[NormRect, ...], float]:
    """A `CFullSearchTree` finomító köre (`0x0088ed40`), kevés képnél.

    Száz véletlen **csere-jelöltet** értékel ki (két kép felcserélése),
    és a legjobbat tartja meg, ha jobb a kiindulónál."""
    count = len(aspects)
    if count < 2:
        return (rects, cost)

    best_rects, best_cost = rects, cost
    for _ in range(REFINE_CANDIDATES):
        candidate = list(order)
        i = rng.rand() % count
        j = rng.rand() % count
        candidate[i], candidate[j] = candidate[j], candidate[i]
        swapped_rects, swapped_cost = _evaluate(
            candidate, aspects, page_aspect, constraint
        )
        if swapped_cost < best_cost:
            best_rects, best_cost = swapped_rects, swapped_cost
    return (best_rects, best_cost)


__all__ = [
    "BUILDERS",
    "CUT_SIDE_BY_SIDE",
    "CUT_STACKED",
    "FULL_SEARCH_LIMIT",
    "PACK_TIME_LIMIT",
    "REFINE_CANDIDATES",
    "PackNode",
    "adjust_target",
    "assign_rects",
    "build_guillotine",
    "build_power_of_two",
    "build_zigzag",
    "choose_cut",
    "combined_aspect",
    "pack",
    "packing_cost",
]
