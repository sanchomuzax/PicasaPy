"""A Picasa 2 korabeli, ötszámos `crop=` alak felismerése (#2008).

A `.picasa.ini` mai alakjában a vágás a `filters=` lánc `crop64` tokenjében
áll. Egy Picasa 3-mal még sosem megnyitott (Picasa 2-es korú) gyűjteményben
viszont a régi, **ötszámos** alak lehet:

```
crop=a,b,c,d,e;
```

Az eredeti Picasa ezt **beolvasáskor migrálja** `crop64=1,<hex>` tokenné
(`0x004221b0`, a `sscanf` a `0x00422361`-en, `cmp eax, 5` a `0x00422369`-en).
Nálunk eddig a `decode_rect64` **kivételt dobott** rá — vagyis a vágás
elveszett volna.

## A mezők — MÉRVE, nem találgatva

A `sscanf` öt kimenetének verem-rekesze kiszámolva; a forgató
(`FUN_009b4c80`) a **2. mező címéről** olvassa a négy dwordöt
(`0x004223eb: lea ecx,[esp+0x2c]`, ahol `esp = esp0−8`, tehát `esp0+0x24`).

⇒ **a téglalap a 2–5. szám**; az **1. mező szerepe NINCS MEGMÉRVE** — a
forgatás nem onnan jön.

## A forgatás sem az öt számból jön

Az eredeti a lánc **`rotate(N)`** tokenjéből olvassa ki
(`FUN_0042c830`, `sscanf("rotate(%d)")` a `0x0042c91a`-n), **negálja**, és a
téglalapot annyiszor 90°-kal visszaforgatja a befoglalón belül
(`FUN_009b4c80`). A migráció tehát **geometriai átszámítás**: a régi `crop=`
a forgatott nézet koordinátáiban áll, a `crop64` a forgatás nélküliben.

## ⚠️ Amit ez a modul SZÁNDÉKOSAN nem tesz

* **Nem írja át és nem törli a `crop=` sort.** Az eredeti viselkedése erre
  nincs mérve; a legbiztonságosabb érintetlenül hagyni, és csak a tokent
  hozzáadni (a jegy is ezt javasolja).
* **Nem skálázza a számokat.** A `crop64` 16 bites, `0…65535` egységekben
  számol; hogy a régi alak MILYEN egységben áll (képpont? ugyanez?),
  **nincs mérve** — ezért a modul a nyers számokat adja vissza, és a
  hívó dolga eldönteni. Egy találgatott skálázás némán rossz vágást adna.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

#: A régi alak: pontosan ÖT egész, pontosvesszővel zárva
#: (`0x00c8130c` = `"%d,%d,%d,%d,%d;"`, `cmp eax, 5` a `0x00422369`-en).
_REGI_CROP = re.compile(
    r"^\s*(-?\d+)\s*,\s*(-?\d+)\s*,\s*(-?\d+)\s*,\s*(-?\d+)\s*,\s*(-?\d+)\s*;?\s*$"
)

#: A lánc forgatás-tokenje (`0x00c81474` = `"rotate(%d)"`).
_ROTATE = re.compile(r"rotate\((-?\d+)\)")


@dataclass(frozen=True)
class LegacyCrop:
    """A régi `crop=` öt száma, MÉRT szereposztással.

    `elso`: az 1. mező — **a szerepe nincs megmérve**. Nem a forgatás (az a
    `rotate(N)`-ből jön) és nem a téglalap része.
    """

    elso: int
    bal: int
    fent: int
    jobb: int
    lent: int

    @property
    def teglalap(self) -> tuple[int, int, int, int]:
        """A 2–5. szám, a mért sorrendben."""
        return (self.bal, self.fent, self.jobb, self.lent)


def parse_legacy_crop(value: str) -> LegacyCrop | None:
    """A régi, ötszámos alak felismerése. `None`, ha nem ilyen.

    ⚠️ **Nem dob.** A mai `rect64(...)`/hex alakot NEM ez kezeli — a hívó
    előbb ezt próbálja, és ha `None`, marad a `decode_rect64`.
    """
    egyezes = _REGI_CROP.match(value)
    if egyezes is None:
        return None
    return LegacyCrop(*(int(cs) for cs in egyezes.groups()))


def rotate_lepesek(filters: str) -> int:
    """A lánc `rotate(N)` tokenjének értéke; `0`, ha nincs.

    Az eredeti a migrációnál ezt NEGÁLJA (`neg eax`, `0x004223ab` /
    `0x004223cc`), tehát a visszaforgatás iránya ellentétes a tárolttal.
    """
    talalat = _ROTATE.search(filters or "")
    return int(talalat.group(1)) if talalat else 0


def forgatott_teglalap(
    teglalap: tuple[int, int, int, int],
    lepesek: int,
    befoglalo: tuple[int, int, int, int],
) -> tuple[int, int, int, int]:
    """`lepesek` × 90°-os forgatás a befoglalón belül (`FUN_009b4c80`).

    A lépésszám **4 szerint pozitívra hozva** (a bináris ugyanezt teszi:
    `or edx,-1 / sub edx,edi / shr edx,2 / lea edi,[edi+edx*4+4]`), majd
    annyiszor egy negyedfordulat.
    """
    bal, fent, jobb, lent = teglalap
    b_bal, b_fent, b_jobb, b_lent = befoglalo
    szelesseg = b_jobb - b_bal
    magassag = b_lent - b_fent
    for _ in range(lepesek % 4):
        bal, fent, jobb, lent = (magassag - lent, bal, magassag - fent, jobb)
        szelesseg, magassag = magassag, szelesseg
    return (bal, fent, jobb, lent)


__all__ = [
    "LegacyCrop",
    "forgatott_teglalap",
    "parse_legacy_crop",
    "rotate_lepesek",
]
