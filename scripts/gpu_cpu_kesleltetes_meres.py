"""MÉRÉS (#22): mennyi ideig tart a hat GPU-képes szűrő a MAI, CPU-s úton?

## Miért ez a kérdés

A #22 hatóköre 2026-09-17-én mérve lett: **hat** szűrőnk fejezhető ki három
csatornánkénti 256-os LUT-tal, tehát a mai shader fogadná őket
(`autocontrast`, `colortemp`, `crossprocess`, `enhance`, `invert`, `warm`).
A mérés akkor kimondta: az áttérés csak akkor indokolt, ha **egy mérés
kimutatja, hogy a mai út valahol tényleg akadozik**.

Ez a szkript azt a mérést végzi el — a CÉLGÉPEN (RPi5), a szerkesztő
ELŐNÉZETI felbontásán.

## Amit mér

A `render/chain.apply_filters` fal-ideje szűrőnként, az `edit_preview.py`
által használt 2560 képpontos élhosszra méretezett képen. Ez az a munka,
ami a felhasználó kattintása és a friss előnézet között lefut — a dekód és
a lánc-prefix gyorsítótárazott (#140), a kattintásra ez a SZŰRŐ fut.

## Amit NEM mér

- a GPU-út idejét (ahhoz működő `ShaderEffect` kellene; a #3070 mérése
  szerint a tesztkörnyezetünkben a shader **el sem indul**);
- a teljes lánc idejét több effekt egymás után;
- a lassú, NEM pontonkénti effekteket (azok a #514 háttérszálán futnak).

A küszöb, amihez mérünk: **100 ms** — e fölött a felhasználó a választ már
nem érzi azonnalinak (a projekt UX-alapelve 4: CPU-s pixelciklus a
UI-útvonalon tilos).
"""
from __future__ import annotations

import argparse
import statistics
import sys
import time

import numpy as np

sys.path.insert(0, "src")

from picasapy.ini.filter_registry import CANONICAL_FILTER_NAMES  # noqa: E402
from picasapy.ini.filters import parse_filters  # noqa: E402
from picasapy.render.chain import apply_filters  # noqa: E402
from picasapy.render.registry import FILTER_REGISTRY  # noqa: E402

#: A #22 2026-09-17-i mérése szerint HÁROM csatornánkénti LUT-tal
#: kifejezhető szűrők — csak ezek jöhetnek szóba a mai shaderhez.
GPU_KEPES = ("autocontrast", "colortemp", "crossprocess", "enhance", "invert", "warm")

#: Az `edit_preview.py` ekkora élhosszra méretez dekódoláskor.
ELONEZET_ELHOSSZ = 2560

#: E fölött nem érzi azonnalinak a felhasználó (UX-alapelv 4).
KUSZOB_MS = 100.0


def lanc_szoveg(nev: str) -> str:
    """Egy ÉRVÉNYES lánc-bejegyzés a regiszterből (a `gpu_pontonkenti_meres`
    mintáját követve: a csúszka-alapértékek pozíció szerint).

    ⚠️ A KANONIKUS névvel — a `parse_filters` a kis-nagybetűre érzékeny, és
    a rossz alakot NÉMÁN kihagyja: a mérés első futása így az `invert`-re
    0,1 ms-ot mért, holott a szűrő el sem indult."""
    kanonikus = {n.casefold(): n for n in CANONICAL_FILTER_NAMES}.get(nev, nev)
    spec = FILTER_REGISTRY.get(nev)
    if spec is None or not spec.sliders:
        return f"{kanonikus}=1;"
    ertekek = ",".join(
        f"{(s.default if s.default is not None else s.minimum):.6f}"
        for s in sorted(spec.sliders, key=lambda s: s.index)
    )
    return f"{kanonikus}=1,{ertekek};"


#: A próbakép SZŰK tartománya. ⛔ Nem esztétika: a teljes 0–255-ös
#: véletlen kép hisztogramja már kifeszített, ezért az `autocontrast`
#: (és részben az `enhance`) rajta **nem csinál semmit** — mérve: ugyanaz
#: a szűrő 0 és 3547 megváltozott képpontot adott két különböző magon.
#: Egy valódi fotó sem feszíti ki a teljes tartományt, tehát a szűk sáv
#: egyben élethűbb is.
PROBA_ALSO, PROBA_FELSO = 80, 170


def probakep(elhossz: int, rng: np.random.Generator) -> np.ndarray:
    """Előnézet-méretű, 3:2 arányú, SZŰK tartományú véletlen kép.

    A véletlenszerűség szándékos: semmi nem konstans, tehát a mért idő nem
    egy szerencsés gyorsítótár-találaté."""
    magassag = max(1, round(elhossz * 2 / 3))
    return rng.integers(
        PROBA_ALSO, PROBA_FELSO + 1, size=(magassag, elhossz, 3), dtype=np.uint8
    )


def valtozik_e(nev: str, rng: np.random.Generator) -> int:
    """Hány képpontot változtat meg a szűrő az ALAPÉRTÉKEIN? (ellenpróba)

    ⛔ Enélkül a mérés hazudik: egy szűrő, ami az alapértékén nem csinál
    semmit, villámgyorsnak látszik. A mérés első futásán pontosan ez
    történt — a nem kanonikus név miatt a `parse_filters` NÉMÁN kihagyta a
    bejegyzést, és az `invert` 0,1 ms-nak látszott. A nulla itt lelet,
    nem apróság."""
    kep = rng.integers(
        PROBA_ALSO, PROBA_FELSO + 1, size=(64, 64, 3), dtype=np.uint8
    )
    masolat = kep.copy()
    eredmeny = apply_filters(masolat, parse_filters(lanc_szoveg(nev)))
    ki = eredmeny[0] if isinstance(eredmeny, tuple) else eredmeny
    if ki is None:
        ki = masolat
    return int(np.count_nonzero(np.any(ki != kep, axis=2)))


def merd(nev: str, kep: np.ndarray, ismetles: int) -> list[float]:
    ops = parse_filters(lanc_szoveg(nev))
    idok = []
    for _ in range(ismetles):
        masolat = kep.copy()
        kezdet = time.perf_counter()
        apply_filters(masolat, ops)
        idok.append((time.perf_counter() - kezdet) * 1000.0)
    return idok


def main(argv: list[str] | None = None) -> int:
    elemzo = argparse.ArgumentParser(description=__doc__)
    elemzo.add_argument("--elhossz", type=int, default=ELONEZET_ELHOSSZ)
    elemzo.add_argument("--ismetles", type=int, default=5)
    beallitasok = elemzo.parse_args(argv)

    rng = np.random.default_rng(20260918)
    kep = probakep(beallitasok.elhossz, rng)
    print(f"próbakép: {kep.shape[1]} × {kep.shape[0]} "
          f"({kep.nbytes / 1024 / 1024:.1f} MiB), {beallitasok.ismetles} ismétlés")
    print(f"küszöb: {KUSZOB_MS:.0f} ms\n")
    print(f"{'szűrő':<14}{'medián ms':>11}{'min':>9}{'max':>9}{'változtat':>11}   verdikt")
    tullepok = []
    tetlenek = []
    for nev in GPU_KEPES:
        valtozott = valtozik_e(nev, rng)
        idok = merd(nev, kep, beallitasok.ismetles)
        median = statistics.median(idok)
        if not valtozott:
            tetlenek.append(nev)
            verdikt = "⛔ NEM VÁLTOZTAT — az idő nem értelmezhető"
        else:
            verdikt = "AKADOZIK" if median > KUSZOB_MS else "azonnali"
            if median > KUSZOB_MS:
                tullepok.append((nev, median))
        print(f"{nev:<14}{median:>11.1f}{min(idok):>9.1f}{max(idok):>9.1f}"
              f"{valtozott:>11}   {verdikt}")
    print()
    if tetlenek:
        print("⛔ Az alapértékein nem változtató szűrő(k): "
              + ", ".join(tetlenek)
              + " — ezekre a mért idő NEM a szűrő ideje.")
    if tullepok:
        print("A küszöböt átlépő szűrők: "
              + ", ".join(f"{n} ({m:.0f} ms)" for n, m in tullepok))
    else:
        print("Egyik sem lépi át a küszöböt — a GPU-áttérés ezen a haton "
              "mérhető felhasználói nyereséget nem hoz.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
