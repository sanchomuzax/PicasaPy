"""A Képkockamozaik helyre-kényszerítő pakolója (`CLocationTree`, #916).

A `framegrid` téma pakolója az eredetiben **nem** a Mozaik alap pakolója,
hanem a `CLocationTree` (spec 1.9.14). A különbség egyetlen mondatban: a
hangsúlyos — „képkockaközéppontként" beállított — kép téglalapját a téma
**kiszámolja**, és a fa azt **változatlanul átveszi**, abban az ágban nem
darabol tovább (`0x00897b1c`). A többi kép a maradék területre kerül.

## A hangsúlyos kép téglalapja — MÉRVE, nem illesztve

A „Beállítás képkockaközéppontként" gomb (`0x0083d520`) **téglalapot nem
állít**: csak egy jelzőt (`[téma+0x50] = 1`) és a kép azonosítóját
(`[téma+0x54]`) írja, majd újrapakolást kér. A téglalapot a téma pakolója
számolja (`0x00889185`–`0x00889241`):

```asm
0x00829d8c  fstp dword [eax+0x58]   ; a gyártóban: 0.5   (0xc7dafc)
…
0x00889192  fstp [esp+0x18]         ; s·A          (A = lapszélesség)
0x008891a4  fstp [esp+0x10]         ; s·A/a        (a = a KÉP oldalaránya)
0x008891b1  jne …                   ; ha a < 1 (ÁLLÓ kép), csere:
0x008891ba  fstp [esp+0x10]         ;   s·B        (B = lapmagasság)
0x008891c2  fstp [esp+0x18]         ;   a·s·B
0x008891e6  fld  qword [0xc72150]   ; 0.5 — a fél oldalak
0x0088920a  fstp [esp+0x24]         ; 0,5 − félszélesség
```

Azaz a cella a **lap közepére** kerül, és

| a kép | a cella |
|---|---|
| fekvő (`a ≥ 1`) | szélessége a lap szélességének **fele**, magassága `0,5·P/a` |
| álló (`a < 1`) | magassága a lap magasságának **fele**, szélessége `0,5·a/P` |

ahol `P` a lap oldalaránya (`A/B`). Mindkét ágban ugyanaz következik: a
cella **képpontban a kép oldalarányát tartja**, tehát a hangsúlyos kép nem
torzul, és a nagyobb oldala a lap fele.

⚠️ Ez a mérés vezette ki a korábbi `(0,25 … 0,75)` közelítést: az a
téglalap csak akkor helyes, ha a kép oldalaránya **éppen a lapé**
(`P/a = 1`). Egy panorámakép nála négyszer túl magas cellát kapott.

## Ami MÉRVE van a keresésről

* kényszeres kép **nélkül** a `CLocationTree` visszaesik az alap pakolóra
  (`0x00891032 → 0x0088e9d0`) — ezért itt is szó szerint az fut;
* a kényszer nélküli képeket a keresés **külön listába** gyűjti, és
  időkorláton belül, **véletlen sorrendekkel** próbálkozik
  (`0x00890bf0`–`0x00890cf5`);
* a megtartás mércéje a közös célfüggvény (`0x00893570`): a cellákban
  **üresen maradó terület**, és csak szigorúan kevesebb váltja le a
  kiindulót.

## Ami NINCS mérve — és ezért a MI szerkesztésünk

A kényszeres vágó (`0x00897af0`) a maradék területet a `0x0089e140`
(8524 b) hívással darabolja; ez a függvény **nincs dekompilálva**, tehát a
szabad terület felosztása nálunk saját, kimondott szerkezet: a hangsúlyos
cella körüli **négy sáv** (felül, alul, balra, jobbra), guillotine-módra —
ez az egyetlen felosztás, amit a cella maga kijelöl. A sávokon belül és a
sávok közti elosztásban az alap pakoló fái és a MÉRT célfüggvény dönt.

Amit ez NEM ígér: hogy a maradék képek pont ugyanabba a sávba esnek, mint
az eredetiben. Amit ígér: hogy egyik sem fedi a hangsúlyos képet, és hogy a
választás a mért költséget minimalizálja.
"""

from __future__ import annotations

import math
from collections.abc import Callable, Sequence

from . import packing
from .fitting import fisher_yates
from .packing import (
    BUILDERS,
    PACK_TIME_LIMIT,
    assign_rects,
    pack,
)
from .rects import NormRect

#: A hangsúlyos kép MÉRETE a lapon (`[téma+0x58]`, `0x00829d8c` → `0xc7dafc`).
#: A nagyobb oldala a lap megfelelő oldalának ennyi szerese.
FRAME_CENTER_SCALE = 0.5

#: A cella alatt nullának számító veszteség (`0x00893570`, `0xcf3a10`).
_COST_EPSILON = 1e-5

#: Egy sáv alatt már nincs értelme képet elhelyezni.
_MIN_BAND = 1e-6


def frame_center_rect(
    aspect: float, page_aspect: float, scale: float = FRAME_CENTER_SCALE
) -> NormRect:
    """A hangsúlyos („képkockaközéppont") kép cellája a lapon.

    A lap közepére kerül, a kép oldalarányát KÉPPONTBAN tartva; a nagyobb
    oldala a lap megfelelő oldalának `scale`-szerese (mérve: 0,5).

    A lapon túlnyúló cellát **levágjuk**: az eredeti nem korlátozza, de a
    `[0, 1]²`-en kívüli téglalap nálunk értelmezhetetlen (`NormRect`), és
    egy kirajzolhatatlan cella rosszabb, mint egy levágott.
    """
    if aspect <= 0.0:
        raise ValueError(f"Érvénytelen oldalarány: {aspect}")
    if page_aspect <= 0.0:
        raise ValueError(f"Érvénytelen lapoldalarány: {page_aspect}")
    if scale <= 0.0:
        raise ValueError(f"Érvénytelen méretarány: {scale}")
    if aspect >= 1.0:
        fel_szelesseg = scale / 2.0
        fel_magassag = scale * page_aspect / aspect / 2.0
    else:
        fel_magassag = scale / 2.0
        fel_szelesseg = scale * aspect / page_aspect / 2.0
    fel_szelesseg = min(fel_szelesseg, 0.5)
    fel_magassag = min(fel_magassag, 0.5)
    return NormRect(
        0.5 - fel_szelesseg,
        0.5 - fel_magassag,
        0.5 + fel_szelesseg,
        0.5 + fel_magassag,
    )


def free_bands(center: NormRect) -> tuple[NormRect, ...]:
    """A hangsúlyos cella körüli szabad sávok: felül, alul, balra, jobbra.

    A vízszintes sávok a lap TELJES szélességét kapják, a két oldalsó csak a
    cella magasságát — így a négy sáv hézag és átfedés nélkül fedi le a
    maradékot. A degenerált (nulla oldalú) sávok kimaradnak.
    """
    savok = []
    if center.y0 > _MIN_BAND:
        savok.append(NormRect(0.0, 0.0, 1.0, center.y0))
    if 1.0 - center.y1 > _MIN_BAND:
        savok.append(NormRect(0.0, center.y1, 1.0, 1.0))
    if center.x0 > _MIN_BAND:
        savok.append(NormRect(0.0, center.y0, center.x0, center.y1))
    if 1.0 - center.x1 > _MIN_BAND:
        savok.append(NormRect(center.x1, center.y0, 1.0, center.y1))
    return tuple(savok)


def wasted_area(
    rects: Sequence[NormRect], aspects: Sequence[float], page_aspect: float
) -> float:
    """A célfüggvény (`0x00893570`): a cellákban ÜRESEN maradó terület.

    A lap oldalaránya benne van: a sávok alakja nagyon különböző, és egy
    egységnégyzetben mért veszteség épp a rosszabb sávot hozná ki jobbnak.
    """
    if len(rects) != len(aspects):
        raise ValueError("A cellák és a képek száma nem egyezik.")
    osszeg = 0.0
    for cella, arany in zip(rects, aspects, strict=True):
        szelesseg = cella.width * page_aspect
        magassag = cella.height
        if szelesseg / arany <= magassag:
            beirt = szelesseg * (szelesseg / arany)
        else:
            beirt = (arany * magassag) * magassag
        veszteseg = abs(szelesseg * magassag - beirt)
        osszeg += 0.0 if veszteseg < _COST_EPSILON else veszteseg
    return osszeg


def _in_band(band: NormRect, cell: NormRect) -> NormRect:
    """Egy sávon belüli normalizált cella a LAP koordinátáira."""
    return NormRect(
        band.x0 + cell.x0 * band.width,
        band.y0 + cell.y0 * band.height,
        band.x0 + cell.x1 * band.width,
        band.y0 + cell.y1 * band.height,
    )


def _band_rects(
    band: NormRect, aspects: Sequence[float], page_aspect: float
) -> tuple[NormRect, ...]:
    """Egy sáv kiosztása a legolcsóbb alap-fával (`0x00891fc0` választása)."""
    cel = band.aspect * page_aspect
    legjobb: tuple[NormRect, ...] | None = None
    legjobb_koltseg = math.inf
    for epito in BUILDERS:
        cellak = assign_rects(epito(cel, aspects), count=len(aspects))
        lapon = tuple(_in_band(band, cella) for cella in cellak)
        koltseg = wasted_area(lapon, aspects, page_aspect)
        if koltseg < legjobb_koltseg:
            legjobb, legjobb_koltseg = lapon, koltseg
    if legjobb is None:  # pragma: no cover — a BUILDERS sosem üres
        raise ValueError("Egyetlen faépítő sem adott eredményt.")
    return legjobb


def _distribute(
    order: Sequence[int], bands: Sequence[NormRect], page_aspect: float
) -> list[list[int]]:
    """A sorrend szétosztása a sávok között, TERÜLET-arányosan.

    Minden sáv legalább egy képet kap, amíg van kép — egy üresen hagyott sáv
    a lapon üres folt, amit a célfüggvény amúgy is büntetne.
    """
    darab = len(order)
    teruletek = [sav.width * page_aspect * sav.height for sav in bands]
    ossz = sum(teruletek)
    kvota = [max(1, int(round(darab * t / ossz))) for t in teruletek]
    # a kvóták összege ritkán egyezik — a legnagyobb sávon korrigálunk
    while sum(kvota) > darab:
        i = max(range(len(kvota)), key=lambda k: (kvota[k], teruletek[k]))
        if kvota[i] == 1 and sum(1 for k in kvota if k > 0) > darab:
            kvota[i] = 0
        else:
            kvota[i] -= 1
        if all(k <= 0 for k in kvota):  # pragma: no cover — védőág
            break
    while sum(kvota) < darab:
        i = max(range(len(teruletek)), key=lambda k: teruletek[k] / (kvota[k] + 1))
        kvota[i] += 1
    kiosztas: list[list[int]] = []
    honnan = 0
    for mennyi in kvota:
        kiosztas.append(list(order[honnan : honnan + mennyi]))
        honnan += mennyi
    return kiosztas


def _candidate(
    order: Sequence[int],
    aspects: Sequence[float],
    bands: Sequence[NormRect],
    page_aspect: float,
) -> dict[int, NormRect]:
    """Egy jelölt elrendezés: melyik kép melyik sáv melyik cellájába kerül."""
    cellak: dict[int, NormRect] = {}
    for sav, indexek in zip(bands, _distribute(order, bands, page_aspect), strict=True):
        if not indexek:
            continue
        sav_aranyok = [aspects[i] for i in indexek]
        for index, cella in zip(
            indexek, _band_rects(sav, sav_aranyok, page_aspect), strict=True
        ):
            cellak[index] = cella
    return cellak


def pack_with_center(
    aspects: Sequence[float],
    page_aspect: float,
    rng,
    *,
    center: int | None = None,
    scale: float = FRAME_CENTER_SCALE,
    time_limit: float = PACK_TIME_LIMIT,
    clock: Callable[[], float] | None = None,
) -> tuple[NormRect, ...]:
    """A `framegrid` pakolása: a hangsúlyos kép a mért cellát kapja.

    `center` a hangsúlyos kép sorszáma, vagy `None`. **Kényszeres kép nélkül
    — és érvénytelen sorszámnál is — szó szerint az alap pakoló fut**, ahogy
    az eredeti is visszaesik rá (`0x00891032`).
    """
    if not aspects:
        raise ValueError("A pakoláshoz legalább egy kép kell.")
    if any(a <= 0.0 for a in aspects):
        raise ValueError("Az oldalarány csak pozitív lehet.")
    if page_aspect <= 0.0:
        raise ValueError(f"Érvénytelen lapoldalarány: {page_aspect}")
    if center is None or not 0 <= center < len(aspects):
        return pack(aspects, page_aspect, rng, time_limit=time_limit)
    if len(aspects) == 1:
        # nincs mit köré pakolni: a kényszer nem szűkíthet egyetlen képet
        return (NormRect(0.0, 0.0, 1.0, 1.0),)

    kozep = frame_center_rect(aspects[center], page_aspect, scale)
    savok = free_bands(kozep)
    tobbi = [i for i in range(len(aspects)) if i != center]
    if not savok:  # pragma: no cover — a 0,5-es méret mindig hagy sávot
        return pack(aspects, page_aspect, rng, time_limit=time_limit)

    def teljes(cellak: dict[int, NormRect]) -> tuple[NormRect, ...]:
        cellak = dict(cellak)
        cellak[center] = kozep
        return tuple(cellak[i] for i in range(len(aspects)))

    legjobb = _candidate(tobbi, aspects, savok, page_aspect)
    legjobb_koltseg = wasted_area(teljes(legjobb), aspects, page_aspect)

    #: #1043: az óra EGYETLEN kapuja a `packing._perf_counter` — a termékkód
    #: sosem ad saját órát a keresésnek, különben a tesztek rögzítése némán
    #: hatástalan lenne. A feloldás HÍVÁSKOR történik, nem `def`-kor.
    tick = clock if clock is not None else packing._perf_counter
    start = tick()
    while tick() - start < time_limit:
        jelolt = _candidate(
            fisher_yates(tobbi, rng), aspects, savok, page_aspect
        )
        koltseg = wasted_area(teljes(jelolt), aspects, page_aspect)
        if koltseg < legjobb_koltseg:
            legjobb, legjobb_koltseg = jelolt, koltseg
    return teljes(legjobb)


__all__ = [
    "FRAME_CENTER_SCALE",
    "frame_center_rect",
    "free_bands",
    "pack_with_center",
    "wasted_area",
]
