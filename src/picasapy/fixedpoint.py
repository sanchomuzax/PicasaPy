"""A natív kód fixpontos aritmetikájának Python-megfelelői (#926).

## Miért kell ez a modul

A Picasa szűrőit x86 gépi kódból portoljuk. A C `/` operátor — az x86
`idiv` utasítás — **NULLA felé csonkol**, a Python és a numpy `//`
viszont a **PADLÓ felé kerekít**. Pozitív számlálónál a kettő ugyanaz,
negatívnál pontosan **1** az eltérés, és ez képpontonként végigfut az
egész szűrőn.

Ez nem elméleti kockázat, kétszer meg is történt:

- **`autocolor`** (#759): a becslő két osztása `//`-val ment; csonkolásra
  javítva a 12 golden-páron **1,370 → 0,614** lett a hiba — a maradék
  több mint felét ez az egy sor adta.
- **`linear_blur`**: egy korábbi kör megírta ugyanezt a segédfüggvényt,
  de csak a saját moduljában.

A #926 három egymástól független másolatot talált (`linear_blur`,
`autocolor_matrix`, `color/classify`), és a harmadik az **osztó**
előjelét nem is kezelte. Ezért van egyetlen közös megvalósítás, és ezért
őrzi kapu (`tests/test_fixedpoint_926.py`), hogy ne szülessen
negyedik.

## Mikor NEM kell

- **Eltolás:** a `>>` Pythonban is padlóz, ugyanúgy, mint az x86 `sar` —
  az mindig hű.
- **Nemnegatív számláló:** ott a két szemantika azonos, `//` a helyes és
  olcsóbb választás.

Vagyis csak az **osztás** veszélyes, és csak ott, ahol a számláló
negatív is lehet.

## Miért nem a `render/` alatt van

A jegy a `render/fixedpoint.py`-t vetette fel, de a `render/__init__.py` a
teljes szűrőláncot re-exportálja: onnan importálva a `color/classify.py`
egy 60 soros aritmetikai segédért az egész render-csomagot behúzná.
Mérve: `import picasapy.color.classify` **3 → 62** betöltött
`picasapy`-modul, **0,083 → 0,131 mp**. Ez a modul ezért csomagsemleges,
a `cvimage.py` / `ioutil.py` / `paths.py` mintájára.

## Hogyan dönthető el egy konkrét portolt osztásról, kell-e ez

A natív oldalon a diszasszemblátumból kell eldönteni, `idiv` (csonkol)
vagy `sar`/`shr` (padlóz) áll-e ott. A recept — a csomagolt (SWAR)
számolás buktatójával együtt, amibe a #926 is beleszaladt — a
`docs/specs/binaris-regeszet-modszertan.md` 23. szakaszában van.
"""

from __future__ import annotations

import numpy as np

__all__ = ["c_int_div"]


def c_int_div(numerator, denominator):
    """Előjeles egész-osztás **nulla felé csonkolva** — a C `/` (x86 `idiv`).

    A Python `//` padlóz: `-7 // 2 == -4`, miközben a C `-7 / 2 == -3`.

    Skalárra Python `int`-et ad vissza, tömbre `numpy.ndarray`-t; a két ág
    ugyanazt az eredményt adja, és a bemenetet egyik sem módosítja.
    A nulla osztó ugyanúgy hibát vált ki, mint a `//`-nál.

    >>> c_int_div(-7, 2)
    -3
    >>> c_int_div(7, -2)
    -3
    """
    if isinstance(numerator, np.ndarray) or isinstance(denominator, np.ndarray):
        return _tombos_osztas(numerator, denominator)
    quotient = abs(numerator) // abs(denominator)
    return -quotient if (numerator < 0) != (denominator < 0) else quotient


def _tombos_osztas(numerator, denominator) -> np.ndarray:
    """A tömbös ág: elemenként ugyanaz, új tömbbe."""
    szamlalo = np.asarray(numerator)
    oszto = np.asarray(denominator)
    hanyados = np.abs(szamlalo) // np.abs(oszto)
    ellentetes = (szamlalo < 0) != (oszto < 0)
    return np.where(ellentetes, -hanyados, hanyados)
