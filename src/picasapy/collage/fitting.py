"""A kollázs közös építőelemei — a Picasa binárisából (#431).

Két apróság, ami minden kollázs-elrendezésben ott van, és amitől képpontnyi
eltérések múlnak. Forrás: `docs/specs/picasa-create-features.md` 1.9.1.

1. **Illeszkedés a kereten belülre** (`0x009b4aa0`) — mindenütt ez adja a
   képméretet. A `+0.499` és a `+1e-5` NEM elírás: a Picasa így kerekít
   felfelé a határesetben.
2. **Az MSVC `_rand()` egyenletes lebegőpontossá alakítása** — a bináris a
   klasszikus bittrükköt használja (`0x3f800000 | (rand << 8)` mint float,
   mínusz 1,0). Ugyanaz a szám kell, hogy a szórás-eloszlás ugyanolyan
   legyen, mint az eredetiben.

A modul szándékosan nem függ se OpenCV-től, se Qt-től: tiszta aritmetika,
így önmagában tesztelhető.
"""

from __future__ import annotations

import math
import struct

# Az MSVC `_rand()` felső határa (RAND_MAX).
MSVC_RAND_MAX = 32767

# A közös illesztő két „mágikus" toldaléka a dekompilált kódból.
_FIT_SLACK = 0.499
_FIT_EPSILON = 1e-5


def picasa_round(value: float) -> int:
    """Kerekítés a C `floor(x + 0.5)` idiómája szerint (fél MINDIG felfelé).

    A Python beépített `round()`-ja bankári kerekítést végez (0,5 → páros),
    ami minden második egész felénél egy képpontos eltérést adna az eredeti
    Picasához képest — épp ott, ahol az illesztő a `+0.499`-cel amúgy is a
    határesetre játszik."""
    return math.floor(value + 0.5)


def fit_inside(
    src_width: int, src_height: int, dst_width: int, dst_height: int
) -> tuple[int, int]:
    """A forráskép mérete, arányt tartva, a cél-téglalapba illesztve.

    A Picasa képlete (1.9.1):

    ```c
    s = min((dstW + 0.499f) / srcW, (dstH + 0.499f) / srcH);
    w = round(s * srcW + 1e-5f);
    h = round(s * srcH + 1e-5f);
    ```

    A kép sosem torzul: a hosszabbik oldal ül fel a keretre, a másik
    arányosan követi."""
    if src_width < 1 or src_height < 1:
        raise ValueError(f"Érvénytelen forrásméret: {src_width}×{src_height}")
    if dst_width < 1 or dst_height < 1:
        raise ValueError(f"Érvénytelen célméret: {dst_width}×{dst_height}")
    scale = min(
        (dst_width + _FIT_SLACK) / src_width,
        (dst_height + _FIT_SLACK) / src_height,
    )
    width = picasa_round(scale * src_width + _FIT_EPSILON)
    height = picasa_round(scale * src_height + _FIT_EPSILON)
    return (max(1, width), max(1, height))


def fit_aspect_inside(
    aspect: float, dst_width: int, dst_height: int
) -> tuple[int, int]:
    """Ugyanaz az illesztés, de a forrás OLDALARÁNYÁBÓL (#989).

    A `fit_inside` képlete a forrás abszolút méretétől független — a
    szorzatot kibontva (`a = srcW / srcH`):

    ```
    s·srcW = min( dstW + 0,499 ; (dstH + 0,499)·a )
    s·srcH = min( (dstW + 0,499)/a ; dstH + 0,499 )
    ```

    Ez azért kell, mert a kollázs-panel **csak az index oldalarányát
    ismeri** (a képet nem dekódolja — 350 képnél nem is tehetné), a
    rajzolónak viszont a dekódolt kép van a kezében. Enélkül a kettő két
    külön illesztőt használna, és a vászon mást mutatna, mint a mentett
    kép.
    """
    if not aspect > 0.0:
        raise ValueError(f"Érvénytelen oldalarány: {aspect}")
    if dst_width < 1 or dst_height < 1:
        raise ValueError(f"Érvénytelen célméret: {dst_width}×{dst_height}")
    vizszintes = dst_width + _FIT_SLACK
    fuggoleges = dst_height + _FIT_SLACK
    width = picasa_round(min(vizszintes, fuggoleges * aspect) + _FIT_EPSILON)
    height = picasa_round(min(vizszintes / aspect, fuggoleges) + _FIT_EPSILON)
    return (max(1, width), max(1, height))


def msvc_uniform01(rand_value: int) -> float:
    """Az MSVC `_rand()` 0…32767-es értékéből egyenletes `[0, 1)` szám.

    A bináris nem oszt `RAND_MAX`-szal, hanem a mantisszába tolja a
    véletlen biteket: `bitcast_float(0x3f800000 | (rand << 8)) - 1.0f`.
    Az eredmény 15 bites felbontású, és — ellentétben a naiv osztással —
    SOSEM éri el az 1,0-t."""
    if not 0 <= rand_value <= MSVC_RAND_MAX:
        raise ValueError(f"Érvénytelen _rand() érték: {rand_value}")
    bits = 0x3F800000 | (rand_value << 8)
    (as_float,) = struct.unpack("<f", struct.pack("<I", bits))
    return as_float - 1.0


class MsvcRandom:
    """Az MSVC `_rand()` lineáris kongruens generátora — befecskendezhető.

    `holdrand = holdrand * 0x343fd + 0x269ec3`, a visszaadott érték a felső
    bitekből: `(holdrand >> 16) & 0x7fff`.

    Miért kell saját generátor a `random.Random` helyett? Mert a kollázs
    eloszlásai (a Képkupac „legjobb jelölt" szórása, a Mozaik keverése) az
    eredeti sorozatra vannak hangolva, és mert így a teszt egy rögzített
    maggal pontosan ugyanazt az elrendezést kapja vissza minden gépen."""

    __slots__ = ("_state",)

    def __init__(self, seed: int = 1) -> None:
        if seed < 0:
            raise ValueError(f"Érvénytelen mag: {seed}")
        self._state = seed & 0xFFFFFFFF

    def rand(self) -> int:
        """A következő `_rand()` érték (0…32767)."""
        self._state = (self._state * 0x343FD + 0x269EC3) & 0xFFFFFFFF
        return (self._state >> 16) & 0x7FFF

    def uniform01(self) -> float:
        """A következő egyenletes `[0, 1)` szám a bittrükkel."""
        return msvc_uniform01(self.rand())


def fisher_yates(items, rng) -> list:
    """Fisher–Yates keverés `rand() % n`-nel (`0x0088fcf0`).

    Ugyanez a keverő szolgálja ki a Mozaik sorrend-keresését (`packing`) és
    a „Képek összekeverése" parancsot (`canvas`) — az eredetiben is egy
    rutin. ÚJ listát ad vissza, a bemenetet nem írja."""
    result = list(items)
    for i in range(len(result) - 1, 0, -1):
        j = rng.rand() % (i + 1)
        result[i], result[j] = result[j], result[i]
    return result


__all__ = [
    "MSVC_RAND_MAX",
    "MsvcRandom",
    "fisher_yates",
    "fit_aspect_inside",
    "fit_inside",
    "msvc_uniform01",
    "picasa_round",
]
