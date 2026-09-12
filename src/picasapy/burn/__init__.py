"""Lemezre írás: kapacitás-számítás és lemezekre osztás (#2074).

## Mit ad ez a csomag, és mit NEM

Ez a modul a **számolás**: mennyi fér egy lemezre, és hány lemez kell.
A fizikai írás (és az ISO-kép előállítása) NINCS benne — a célkörnyezetben
(Linux/RPi5) a lemezírás nem tesztelhető, és a jegy külön döntést kér róla.

## A mért képlet (`0x0066be90`)

```
használható = szektorszám × 2048 − tartalék
```

| mennyiség | érték | cím |
|---|---:|---|
| szektorméret | 2048 | `0x0066bf35` (`push 0x800`) |
| DVD-tartalék | 4 096 000 bájt (2000 szektor) | `0x0066bf50` |
| CD-tartalék | 409 600 bájt (200 szektor) | `0x0066bf58` |
| kétrétegű kapacitás | 8 547 991 552 bájt | `0x0066bed3` |

⚠️ A kétrétegű lemez mérete **rögzített**, nem számolt: a bináris
közvetlenül ezt az értéket adja vissza (a médiatípus `0x214`).

A tartalék nem óvatoskodás: a lemezzáró sáv helye. Enélkül az utolsó
lemez az írás VÉGÉN bukna el, amikor a felhasználó már mindent rámásolt.
"""

from __future__ import annotations

from collections.abc import Iterable

#: médiatípusok — a nevük a mi fogalmunk, a SZÁMOK a mértek
CD = "cd"
DVD = "dvd"
KETRETEGU = "ketretegu"

#: `0x0066bf35`: a szektorméret
SZEKTOR_BAJT = 2048
#: `0x0066bf50` / `0x0066bf58`: a lemezzáró sáv tartaléka
TARTALEK = {DVD: 4_096_000, CD: 409_600, KETRETEGU: 0}
#: `0x0066bed3`: a kétrétegű lemez RÖGZÍTETT kapacitása
KETRETEGU_KAPACITAS = 8_547_991_552


def hasznalhato_kapacitas(media: str, *, szektorszam: int = 0) -> int:
    """A lemezre ténylegesen ráférő bájtok száma.

    A kétrétegűnél a `szektorszam` érdektelen: a bináris rögzített értéket
    ad vissza. A tartaléknál kisebb lemezre nulla fér — negatív méret
    nincs."""
    if media == KETRETEGU:
        return KETRETEGU_KAPACITAS
    nyers = int(szektorszam) * SZEKTOR_BAJT
    return max(0, nyers - TARTALEK.get(media, 0))


def lemezekre_oszt(
    fajlok: Iterable[tuple[str, int]], *, kapacitas: int
) -> tuple[tuple[tuple[str, int], ...], ...]:
    """A fájlokat sorrendben lemezekre osztja.

    A SORREND megmarad: a sorszámozott lemezek („Ez lesz a(z) %d. számú
    lemez a(z) %d darabból", `InsertNext::13`) csak akkor értelmesek, ha
    kiszámítható, mi hova került.

    ⚠️ A lemezméretnél NAGYOBB fájl saját lemezt kap — némán nem tűnhet
    el. Az a lemez túlcsordul, és ezt a hívónak kell kezelnie."""
    lemezek: list[list[tuple[str, int]]] = []
    aktualis: list[tuple[str, int]] = []
    hasznalt = 0
    for nev, meret in fajlok:
        meret = int(meret)
        if aktualis and hasznalt + meret > kapacitas:
            lemezek.append(aktualis)
            aktualis = []
            hasznalt = 0
        aktualis.append((nev, meret))
        hasznalt += meret
    if aktualis:
        lemezek.append(aktualis)
    return tuple(tuple(lemez) for lemez in lemezek)


def lemezek_szama(osszes_bajt: int, kapacitas: int) -> int:
    """Hány lemez kell — a felület becsléséhez („Est. %d CDs or %d DVDs").

    ⚠️ Ez BECSLÉS: a tényleges szám a fájlhatárokon múlik (egy fájl nem
    vágható ketté), ezért a `lemezekre_oszt` ennél többet is adhat."""
    if osszes_bajt <= 0 or kapacitas <= 0:
        return 0
    return -(-int(osszes_bajt) // int(kapacitas))


__all__ = [
    "CD",
    "DVD",
    "KETRETEGU",
    "KETRETEGU_KAPACITAS",
    "SZEKTOR_BAJT",
    "TARTALEK",
    "hasznalhato_kapacitas",
    "lemezek_szama",
    "lemezekre_oszt",
]
