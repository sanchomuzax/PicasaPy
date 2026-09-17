"""MÉRÉS (#22): mely szűrőink PONTONKÉNTIEK — azaz GPU-shaderrel kifejezhetők.

Egy szűrő pontonkénti, ha a kimeneti pixel CSAK a bemeneti pixeltől függ
(nincs környezet-, hely- vagy geometria-függés). Ezt méréssel döntjük el: a
próbaképen ugyanaz a bemeneti RGB több HELYEN is előfordul — ha a kimenet
minden előfordulásnál azonos, a szűrő pontonkénti.

Csatornánkénti bontás: a pontonkéntiek közül azok fejezhetők ki HÁROM
független 256-os LUT-tal, amelyeknél a kimenet minden csatornája csak a
SAJÁT bemeneti csatornájától függ.
"""
from __future__ import annotations

import sys
import numpy as np

sys.path.insert(0, "src")

from picasapy.ini.filter_registry import CANONICAL_FILTER_NAMES
from picasapy.ini.filters import parse_filters
from picasapy.render.chain import apply_filters
from picasapy.render.registry import FILTER_REGISTRY

#: A #3229 őrének MÉRT kihagyás-listája: ezeknél a csúszka-INDEX nem
#: paraméter-POZÍCIÓ (szín-mezők), tehát a regiszterből épített lista
#: érvénytelen bejegyzést adna, és a lánc NÉMÁN kihagyná.
ISMERT_KIHAGYAS = frozenset(
    {"border", "dropshadow", "focalzoom", "dir_tint", "finetune", "finetune2"}
)


def lanc_szoveg(nev: str) -> str:
    """Egy ÉRVÉNYES lánc-bejegyzés a regiszterből (a #3229 mintájára)."""
    kanonikus = {n.casefold(): n for n in CANONICAL_FILTER_NAMES}.get(nev, nev)
    spec = FILTER_REGISTRY.get(nev)
    if spec is None or not spec.sliders:
        return f"{kanonikus}=1;"
    ertekek = ",".join(
        f"{(s.default if s.default is not None else s.minimum):.6f}"
        for s in sorted(spec.sliders, key=lambda s: s.index)
    )
    return f"{kanonikus}=1,{ertekek};"


def probakep(rng: np.random.Generator) -> np.ndarray:
    """64×64, ahol minden bemeneti RGB TÖBB, EGYMÁSSAL NEM SZIMMETRIKUS
    helyen áll.

    ⚠️ Az első változat a felső felet TÜKRÖZVE ismételte — és a sugaras
    effektek (`vignette`, `radsat`, `radtint`) épp erre a tengelyre
    szimmetrikusak, tehát a tükörpár ugyanazt a súlyt kapta, és a mérés
    tévesen PONTONKÉNTINEK mondta őket. A javítás: a második fél a
    pixelek VÉLETLEN permutációja, így a szimmetria nem segíthet."""
    alap = rng.integers(0, 256, size=(32, 64, 3), dtype=np.uint8)
    lapos = alap.reshape(-1, 3)
    kevert = lapos[rng.permutation(lapos.shape[0])].reshape(alap.shape)
    return np.vstack([alap, kevert])


def pontonkenti(be: np.ndarray, ki: np.ndarray) -> bool:
    """Ugyanaz a bemeneti pixel MINDIG ugyanazt a kimenetet adja?"""
    if be.shape != ki.shape:
        return False                              # geometriát változtat
    kulcs = be.reshape(-1, 3).astype(np.int64)
    kulcs = (kulcs[:, 0] << 16) | (kulcs[:, 1] << 8) | kulcs[:, 2]
    ertek = ki.reshape(-1, 3).astype(np.int64)
    ertek = (ertek[:, 0] << 16) | (ertek[:, 1] << 8) | ertek[:, 2]
    rend = np.argsort(kulcs, kind="stable")
    k, e = kulcs[rend], ertek[rend]
    hatar = np.flatnonzero(np.diff(k)) + 1
    for szelet in np.split(e, hatar):
        if szelet.size > 1 and not np.all(szelet == szelet[0]):
            return False
    return True


def csatornankenti(be: np.ndarray, ki: np.ndarray) -> bool:
    """Minden kimeneti csatorna csak a SAJÁT bemenetétől függ?"""
    for cs in range(3):
        b = be[..., cs].reshape(-1)
        k = ki[..., cs].reshape(-1)
        rend = np.argsort(b, kind="stable")
        bs, ks = b[rend], k[rend]
        hatar = np.flatnonzero(np.diff(bs)) + 1
        for szelet in np.split(ks, hatar):
            if szelet.size > 1 and not np.all(szelet == szelet[0]):
                return False
    return True


def main() -> int:
    rng = np.random.default_rng(20260917)
    kep = probakep(rng)
    pont, csat, nem, kihagy = [], [], [], []
    for nev in sorted(FILTER_REGISTRY):
        if nev in ISMERT_KIHAGYAS:
            kihagy.append((nev, "szín-paraméter, #3229 szerint nem mérhető így"))
            continue
        opok = parse_filters(lanc_szoveg(nev))
        if not opok:
            kihagy.append((nev, "a lánc-szöveg nem elemezhető"))
            continue
        op = opok[0]
        try:
            jelentes = apply_filters(kep.copy(), (op,))
        except Exception as hiba:                  # noqa: BLE001 — leltár
            kihagy.append((nev, type(hiba).__name__))
            continue
        ki, kihagyott = jelentes[0], jelentes[1]
        if kihagyott:
            kihagy.append((nev, "a lánc kihagyta"))
            continue
        if np.array_equal(ki, kep):
            kihagy.append((nev, "nem változtat"))
            continue
        if not pontonkenti(kep, ki):
            nem.append(nev)
        elif csatornankenti(kep, ki):
            csat.append(nev)
        else:
            pont.append(nev)
    print(f"csatornánkénti LUT-tal kifejezhető ({len(csat)}): {', '.join(csat)}")
    print(f"pontonkénti, de CSATORNÁK KEVERŐDNEK ({len(pont)}): {', '.join(pont)}")
    print(f"NEM pontonkénti ({len(nem)}): {', '.join(nem)}")
    print(f"kihagyva ({len(kihagy)}): " + ", ".join(f"{n} [{ok}]" for n, ok in kihagy))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
