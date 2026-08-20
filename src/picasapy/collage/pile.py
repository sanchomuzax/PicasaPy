"""A Képkupac (`picturepile`) elrendezése (#431).

Forrás: `docs/specs/picasa-create-features.md` 1.9.2 (`0x0087bcb0`,
`0x0087dcd0`) és 1.9.12 (`0x0087cb70`).

Három dolog adja a Képkupac jellegzetes külsejét, és mindhármat el lehet
véteni úgy, hogy a képletek külön-külön helyesnek látszanak:

1. **A méret lecseng** — a sorrendben hátrébb lévő kép kisebb.
2. **A szórás „legjobb jelölt" mintavételezés** (Mitchell best-candidate):
   képenként ÖT véletlen pontot sorsol, és azt választja, amelyik a
   legmesszebb van a már elhelyezettektől. Sima `rand()`-dal a kupac
   csomós lesz — egyes képek egymásra torlódnak, máshol lyuk marad.
3. **A forgatás nem szimmetrikus szórás**, hanem legyezőhatás: a szöget a
   kép vízszintes helyzete modulálja.

A véletlenforrás **befecskendezhető** (bármi, aminek van `uniform01()`
metódusa — alapesetben `fitting.MsvcRandom`), hogy a teszt megismételhető
legyen. A valós viselkedés viszont az eredetié marad: éles futáskor friss
maggal indul, tehát minden „Képek szétszórása" új elrendezést ad.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Protocol


# A legnagyobb kép a lap szélességének ekkora hányada.
PILE_BASE_RATIO = 0.33

# Képenként ennyi véletlen jelöltből választ a szórás (Mitchell).
PILE_CANDIDATES = 5

# A szórási sáv szűkítése: `sáv = 1 − pile_scale(N) * 0.495`.
PILE_BAND_FACTOR = 0.495

# A forgatás képlete: `fok = −36 * u * (0.1 − (x − 0.5) * 0.5)`.
_ROTATION_GAIN = -36.0
_ROTATION_BIAS = 0.1
_ROTATION_SLOPE = 0.5


class UniformSource(Protocol):
    """Bármi, ami egyenletes `[0, 1)` számokat ad — pl. `MsvcRandom`."""

    def uniform01(self) -> float: ...


@dataclass(frozen=True)
class PilePlacement:
    """Egy kép helye a kupacban.

    `center_x` / `center_y` a szórási TERÜLET koordinátáiban van (nem a
    lapén) — a lapra váltást a `pile_top_left()` végzi, mert ahhoz kell a
    kép tényleges, illesztés utáni mérete is.

    `theta` **radiánban**, ahogy a `.cxf` tárolja."""

    index: int
    center_x: float
    center_y: float
    size: int
    theta: float


def pile_scale(index: int) -> float:
    """A méret-szorzó a kép 1-alapú sorszámához.

    ```c
    if (i <= 1) return 1.0f;
    s = 1.0f / sqrtf(sqrtf((float)i) - 1.0f);
    return s > 1.0f ? 1.0f : s;      // felül 1,0-ra vágva
    ```

    Az 1–4. kép ezért egyforma, onnantól lassan csökken (10. → 0,68,
    50. → 0,41, 100. → 0,33)."""
    if index < 1:
        raise ValueError(f"A kép sorszáma 1-től indul: {index}")
    if index == 1:
        return 1.0
    inner = math.sqrt(index) - 1.0
    if inner <= 0.0:
        return 1.0
    scale = 1.0 / math.sqrt(inner)
    return min(1.0, scale)


def pile_size(index: int, page_width: int) -> int:
    """A kép célmérete képpontban (a `.cxf` `scale` mezője).

    ⚠️ #1059: **CSONKÍT, nem kerekít.** Ez az egyetlen hely, ahol a Picasa
    geometriájából a csonkítás igazolt — a `picasa_round` mindenhol máshol
    dekódolt és bizonyított viselkedés, ide viszont nem illik.

    A bizonyíték a tulajdonos kollázsainak `scale` mezői. Az `AI1.cxf`
    kilenc értéke csomópont-sorrendben `337, 337, 337, 337, 303, 280, 263,
    249, 238`; a képletünk pontos értékei `337,92 … 238,95`:

    | | egyezés |
    |---|---:|
    | `picasa_round` | **1/9** |
    | `math.floor` | **9/9** |

    Az `AI.cxf` ugyanígy 9/9 csonkítással; az `AI2.cxf` 7/9, és a két
    kivétel bizonyítottan KÉZZEL átméretezett csomópont (nem egész `scale`).

    Kerekítéssel a kupac minden csempéje egy képponttal nagyobb volt a
    kelleténél — rendszeresen és egyirányúan. A méret a szórás sávjába és a
    beszorításba is bemegy, a polaroid keret pedig 1,374-szeresére nagyítja
    magasságban."""
    if page_width < 1:
        raise ValueError(f"Érvénytelen lapszélesség: {page_width}")
    return math.floor(pile_scale(index) * PILE_BASE_RATIO * page_width)


def scatter_centers(
    count: int,
    area_width: float,
    area_height: float,
    rng: UniformSource,
    candidates: int = PILE_CANDIDATES,
) -> tuple[tuple[float, float], ...]:
    """A képközéppontok „legjobb jelölt" szórása.

    A sáv a képszámmal együtt tágul: sok képnél `pile_scale(N)` kicsi, így
    a szórás majdnem a teljes lapra kiterjed; kevés képnél a középpontok a
    lap középső felében maradnak.

    A `candidates` paraméter csak a teszthez van (1-gyel a naiv, csomós
    viselkedés áll elő) — élesben mindig az eredeti öt."""
    if count < 1:
        raise ValueError("A kupachoz legalább egy kép kell.")
    if candidates < 1:
        raise ValueError(f"Érvénytelen jelöltszám: {candidates}")
    if area_width <= 0.0 or area_height <= 0.0:
        raise ValueError(f"Érvénytelen terület: {area_width}×{area_height}")

    band = 1.0 - pile_scale(count) * PILE_BAND_FACTOR
    offset = (1.0 - band) * 0.5

    placed: list[tuple[float, float]] = []
    for _ in range(count):
        best_distance = 0.0
        best_point = (0.0, 0.0)
        for _candidate in range(candidates):
            # a két hívás sorrendje számít: előbb x, aztán y
            x = (band * rng.uniform01() + offset) * area_width
            y = (offset + rng.uniform01() * band) * area_height
            distance = 1e6
            for point in placed:
                delta = (x - point[0]) ** 2 + (y - point[1]) ** 2
                distance = min(distance, delta)
            if distance > best_distance:
                best_distance = distance
                best_point = (x, y)
        placed.append(best_point)
    return tuple(placed)


def pile_rotation(uniform: float, center_x: float, area_width: float) -> float:
    """A kép forgatása **radiánban**, a vízszintes helyzetéből modulálva.

    `fok = −36 · u · (0.1 − (x − 0.5) · 0.5)`, ami `u · (18x − 12.6)`.
    A bal szélen 0…−12,6°, körülbelül 70%-nál nulla, a jobb szélen
    0…+5,4° — enyhe legyezőhatás, nem szimmetrikus szórás."""
    if area_width <= 0.0:
        raise ValueError(f"Érvénytelen területszélesség: {area_width}")
    position = center_x / area_width
    degrees = (
        _ROTATION_GAIN
        * uniform
        * (_ROTATION_BIAS - (position - 0.5) * _ROTATION_SLOPE)
    )
    return math.radians(degrees)


def pile_top_left(
    center: float, rendered_extent: float, area_extent: float, page_extent: float
) -> float:
    """A középpontból a bal felső sarok, a lap koordinátáira normalizálva.

    ```c
    X = (lap.jobb − lap.bal) * (x − kepSzelesseg * skala * 0.5f) / teruletSzelesseg;
    ```"""
    if area_extent <= 0.0:
        raise ValueError(f"Érvénytelen területméret: {area_extent}")
    return page_extent * (center - rendered_extent * 0.5) / area_extent


def pile_layout(
    count: int,
    page_width: int,
    page_height: int,
    rng: UniformSource,
) -> tuple[PilePlacement, ...]:
    """A teljes kupac: méret, középpont és forgatás képenként.

    A szórás fut le előbb (mind a `count` képre), utána a forgatások —
    ahogy az eredetiben is két külön menet: a szög a MÁR kiszámolt
    vízszintes helyzetből jön."""
    if count < 1:
        raise ValueError("A kupachoz legalább egy kép kell.")
    if page_width < 1 or page_height < 1:
        raise ValueError(f"Érvénytelen lapméret: {page_width}×{page_height}")

    centers = scatter_centers(count, page_width, page_height, rng)
    elhelyezesek = []
    for index, (center_x, center_y) in enumerate(centers):
        meret = pile_size(index + 1, page_width)
        # ⚠️ #1045: a KÖZÉPPONT a sávon belül van, a képnek viszont MÉRETE
        # van a középpont körül — 11 képtől a legnagyobb kép fele kilóg a
        # lapról, és a felhasználó ezt látja csonka képként.
        #
        # A hiba darabszámfüggő, és ezért nem fogta meg egyetlen teszt sem:
        # a `scatter_centers` a sávot `pile_scale(count)`-tal szűkíti (a
        # LEGKISEBB kép szorzójával), a margót viszont a LEGNAGYOBB kép
        # igényli, annak a szorzója pedig mindig 1,0. A legnagyobb kép bal
        # széle 9 képnél +0,0100, 10-nél +0,0033, **11-nél −0,0024**,
        # 25-nél −0,0412. A golden minták és a régi teszteseteink mind
        # 9 képesek voltak.
        #
        # A sávot NEM szűkítjük: a 9 képes eset a mért minták középpontjait
        # négy tizedesig hozza, tehát a sáv képlete helyes.
        #
        # ⚠️ A BESZORÍTÁS NEM ITT VAN, hanem a `_pile_nodes`-ban: ott ismert
        # a KERETES csempe mérete (`outer_box`), és a kilógást az dönti el,
        # nem a fotó négyzete. Itt beszorítva a keretes kép tovább lógna —
        # egy 15 képes próbarenderen ez mérve is látszott.
        elhelyezesek.append(
            PilePlacement(
                index=index,
                center_x=center_x,
                center_y=center_y,
                size=meret,
                theta=pile_rotation(rng.uniform01(), center_x, page_width),
            )
        )
    return tuple(elhelyezesek)


__all__ = [
    "PILE_BAND_FACTOR",
    "PILE_BASE_RATIO",
    "PILE_CANDIDATES",
    "PilePlacement",
    "UniformSource",
    "pile_layout",
    "pile_rotation",
    "pile_scale",
    "pile_size",
    "pile_top_left",
    "scatter_centers",
]
