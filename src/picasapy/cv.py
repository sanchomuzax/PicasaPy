"""Lusta `cv2`-homlokzat — az indulás legnagyobb egyetlen tétele (#1611).

## A lelet

`import picasapy.app.application` importidejének **1 639 ms**-át a `cv2`
betöltése viszi el (`python3 -X importtime`, RPi5). Ez minden induláskor
lefut, akkor is, ha a felhasználó egyetlen effektet, mentést vagy
arckeresést sem használ.

## Miért nem elég egy helyen javítani — MÉRVE

Az indulási modullista és a `cv2`-t importáló modulok metszete
**33 modul** (`render/` 13, `collage/` 7, `thumbs`, `edit`, `export`,
`dedup`, `movie`, `webexport`, `index.colors`, `app.*`, `cvimage`). Ha
egyetlen láncot halasztunk, a `cv2`-t a következő modul behúzza — ez a
#1601 nulla nyereségének oka.

## A megoldás alakja

Ez a modul **PEP 562 `__getattr__`**-rel áll a `cv2` elé: az importja
ingyen van, az első attribútum-hozzáféréskor tölti be a valódi `cv2`-t,
majd **minden** hozzáférésnél a valódihoz továbbít. A továbbítás ára
mérve 0,16 mikroszekundum hívásonként — a képműveletek
ezredmásodperces nagyságrendjéhez képest nem mérhető, cserébe a
homlokzat ÁTLÁTSZÓ marad (a `cv2` futásidejű foltozása működik).

A hívó modulok `import cv2` helyett `from picasapy import cv as cv2`
alakot használnak: a törzsük **egyetlen karakterrel sem változik**, a
`cv2.LUT(...)` hívások változatlanok. Ez 26 modulnál elég.

⚠️ **Hét modul a betöltésekor is HÍV** `cv2`-t (konstans-kiolvasás vagy
valódi hívás) — azok külön, nevesített kezelést kaptak; ld. az érintett
fájlok `#1611` kommentjeit.

## Amit ez NEM old meg

A `cv2` első valódi használatakor a költség megjelenik — a felhasználó
ott várni fog. A mérés szerint ez a bélyegkép-rajzolás első köre, ami
amúgy is háttérszálon fut; a felület megjelenése viszont nem várja meg.
"""

from __future__ import annotations

from typing import Any

__all__ = ["betoltve"]


def __getattr__(nev: str) -> Any:
    """A valódi `cv2` attribútuma, az első kéréskor betöltve.

    ⚠️ SZÁNDÉKOSAN NEM gyorsítótárazunk a modul szótárába. A memoizálás
    (`globals()[nev] = ertek`) gyorsabb lenne, de ELTÖRNÉ az
    ÁTLÁTSZÓSÁGOT: egy `monkeypatch.setattr(cv2, "imencode", …)` a
    memoizálás UTÁN már nem érné el a hívóhelyeket, mert azok a
    homlokzat saját szótárából olvasnának. Élesben is ugyanez a
    kockázat mindenhol, ahol valaki futásidőben cserél egy cv2-tagot.

    Az ár MÉRVE: 264 ms vs. 101 ms **millió** hozzáférésenként, azaz
    **0,16 mikroszekundum** hívásonként. A képműveletek ezredmásodperces
    nagyságrendűek — ez nem mérhető. Az átlátszóság viszont valódi
    hibákat előz meg."""
    import cv2

    return getattr(cv2, nev)


def betoltve() -> bool:
    """Betöltődött-e már a valódi `cv2`? (Csak mérésnek és őrnek.)"""
    import sys

    return "cv2" in sys.modules
