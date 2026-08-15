"""Terheléstűrő teljesítmény-őr (#660).

## Miért kell

A renderelő három tesztje **abszolút wall-clock korláttal** mérte, hogy egy
effekt nem esett-e vissza a régi, percekben mérhető megvalósításra. Ez a
korlát a FUTTATÓ GÉP terheltségét méri, nem a kód sebességét: egy párhuzamos
munkamenet mellett az `apply_lomo` 12,3 másodpercre nőtt a 10 másodperces
határ alatt mért ~6 helyett, és a teszt elbukott — miközben a kód egy sort
sem változott.

A hamis piros ugyanúgy rombolja a tesztkészletbe vetett bizalmat, mint a
hamis zöld, csak fordítva: idővel mindenki „ja, az a flaky" alapon átlapozza,
és egy valódi lassulás is átcsúszik.

## A megoldás: viszonyítás, nem abszolút idő

Az őr UGYANABBAN a futásban megmér egy referencia-terhelést, és ahhoz
viszonyít. Ha a gép lassú, mindkettő lassul — az arány marad.

A védendő hibaosztály nagyságrendje ezt bőven megengedi: a #504-ben a
javítás előtti kód **25–37×** lassabb volt (37 s a mai ~1–6 s helyett, a
Vignette 124 s, a Matte 89 s), tehát egy valódi visszaesés az arányt
ezerszeres nagyságrendbe viszi. A mai arányok a fejlesztői gépen
`apply_lomo` ≈ 67×, `apply_holga` ≈ 95× — a `_MEGENGEDETT_SZORZO` ezekhez
képest is nagy tartalékkal dolgozik.
"""

from __future__ import annotations

import time

import numpy as np

#: Hányszorosa lehet az effekt a referencia-terhelésnek. A mai legrosszabb
#: mért arány ~95×; a védendő visszaesés ennek a sokszorosa lenne.
MEGENGEDETT_SZORZO = 400.0


def referencia_masodperc(kep: np.ndarray, ismetles: int = 3) -> float:
    """Egy fix, képméret-arányos numpy-terhelés átlagos futásideje.

    Ugyanolyan jellegű munka, mint amit az effektek végeznek (teljes képes
    float-konverzió és elemenkénti műveletek), ezért a gép terheltsége
    hasonló arányban lassítja mindkettőt.
    """
    if ismetles < 1:
        raise ValueError(f"az ismétlésszám legyen legalább 1: {ismetles}")
    kezdet = time.perf_counter()
    for _ in range(ismetles):
        munka = kep.astype(np.float32)
        munka *= 1.5
        munka += 3.0
        np.sqrt(munka, out=munka)
        float(munka.sum())
    return (time.perf_counter() - kezdet) / ismetles


def merd_es_ellenorizd(
    nev: str,
    kep: np.ndarray,
    muvelet,
    *,
    szorzo: float = MEGENGEDETT_SZORZO,
):
    """Lefuttatja `muvelet(kep)`-et, és a referenciához méri az idejét.

    Visszaadja a művelet eredményét, hogy a hívó tovább is tudjon
    ellenőrizni. A hibaüzenet MINDKÉT mért időt és az arányt tartalmazza —
    enélkül egy bukásból nem derülne ki, a kód lassult-e vagy a gép.
    """
    alapvonal = referencia_masodperc(kep)
    kezdet = time.perf_counter()
    eredmeny = muvelet(kep)
    eltelt = time.perf_counter() - kezdet
    arany = eltelt / alapvonal if alapvonal > 0 else float("inf")
    assert arany < szorzo, (
        f"{nev} túl lassú: {eltelt:.2f}s, ami a referencia-terhelés "
        f"({alapvonal:.3f}s) {arany:.0f}-szerese — a megengedett {szorzo:.0f}×. "
        "Ez a mérce a gép terheltségétől független, tehát valódi lassulást jelez."
    )
    return eredmeny
