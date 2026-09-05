"""A thumbindex slot-ellenőrzőösszege — mindkét mód (#2435).

A `thumbs_index.db` / `previews_index.db` minden slotja hordoz egy 32 bites
ellenőrzőösszeget. Az eredeti Picasa **kétféleképpen** számolja, és eddig
egyiket sem tudtuk kiszámolni: a mezőt beolvastuk, de sosem ellenőriztük —
egy elromlott vagy elcsúszott index-fájlt tehát némán elfogadtunk, és a
rossz slotból olvastunk bélyegképet.

Ez a modul **tiszta számítás**: nem nyúl lemezhez és nem ismer
`.picasa.ini`-t. A hívó dolga eldönteni, mit kezd az eltéréssel.

## 1. mód — útvonalas (a szokásos)

```
Checksum₁ = (JS_hash(teljes_út) mod 1 000 231)
            ^ rol(idő_lo, 13) ^ rol(idő_hi, 17) ^ rol(méret, 18)
```

## 2. mód — útvonal és méret NÉLKÜL (`0x006b9b26`)

```
q = (FILETIME + 5 000 000) / 10 000 000        # egész másodpercre kerekít
Checksum₂ = rol(q_lo, 13) ^ rol(q_hi, 17)
```

## Melyik mód

A módválasztás három feltétele (`0x004e3bc2` · `0x004e3bcb` · `0x004e3bd7`):
a hívó kifejezetten `0`-t kér, **vagy** a rekord típusa `0`, **vagy** nincs
szülője. ⇒ a könyvtárak és az üres slotok mindig a 2. módot kapják.

## ⚠️ Két részlet, ami a binárisból jön, nem a képlet „szépítéséből"

1. **A bájt ELŐJELES** (`movsx eax, al` a `0x006b98da`/`0x006b98e2`-n): a
   0x80 fölötti bájtok NEGATÍV számként adódnak hozzá. ASCII néven ez nem
   látszik; nem-ASCII néven a hash teljesen eltér. A spec 8.10 mérése épp
   ezen bukott 615 soron.
2. **A jobbra tolás ELŐJELTELEN** (`shr ebx, 2` a `0x006b98f1`-en, NEM
   `sar`). Egy `sar`-ra írt változat a hash felénél más eredményt adna.

## ⚠️ Amit ez a modul NEM dönt el

* **Az útvonal KÓDOLÁSA.** A bináris bájtokon dolgozik; hogy nem-ASCII
  néven melyik kódlap a helyes, NINCS MÉRVE. A `kodolas` paraméter ezért
  kívülről állítható, az alapértelmezés UTF-8 (a PMP-sztringek kódolása).
* **A 615 nem egyező sor oka** (spec 8.10): 2. mód, másik Picasa-verzió
  vagy tényleges romlás — nyitott.
* **Az időzóna-tolerancia.** Az eredeti verifikálója (`FUN_006b9870`)
  −12 h…+12 h között minden egész órás eltolást végigpróbál. Ez
  ELLENŐRZÉS, nem képlet; ide szándékosan nem került be.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

#: A JS-hash kezdőértéke (`0x006b98cb`).
_HASH_KEZDET = 0x12345678

#: A hash modulusa (`0xF4327`, `0x006b9911`).
_HASH_MODULUS = 1_000_231

_MASZK32 = 0xFFFFFFFF

#: A FILETIME egész másodpercre kerekítésének két állandója
#: (`0x006b987e` / `0x006b9883`).
_FELKEREKITES = 5_000_000
_MASODPERC = 10_000_000


def rol(ertek: int, bitek: int) -> int:
    """32 bites balra forgatás (`rol`), ahogy a bináris teszi."""
    ertek &= _MASZK32
    bitek %= 32
    return ((ertek << bitek) | (ertek >> (32 - bitek))) & _MASZK32 if bitek else ertek


def js_hash(szoveg: str, *, kodolas: str = "utf-8") -> int:
    """A Picasa sztring-hashe, `mod 1 000 231`-gyel lezárva.

    A ciklus (`0x006b98d2`–`0x006b98fd`):

    * `'A'..'Z'` → `+0x20` (csak az ASCII nagybetűk kisbetűsödnek);
    * a bájt **előjeles** (`movsx`), tehát `>= 0x80` esetén `− 256`;
    * `h ^= (h << 5) + c + (h >>> 2)`, 32 biten, **előjeltelen** tolással.
    """
    h = _HASH_KEZDET
    for bajt in szoveg.encode(kodolas):
        c = bajt + 0x20 if 0x41 <= bajt <= 0x5A else bajt
        if c >= 0x80:
            c -= 256
        h = (h ^ (((h << 5) & _MASZK32) + c + (h >> 2))) & _MASZK32
    return h % _HASH_MODULUS


def _egesz_masodperc(filetime: int) -> int:
    """A FILETIME egész másodpercre kerekítve (`+5e6`, `/1e7`)."""
    return (filetime + _FELKEREKITES) // _MASODPERC


def checksum_utvonalas(
    teljes_ut: str, filetime: int, meret: int, *, kodolas: str = "utf-8"
) -> int:
    """**1. mód**: útvonal + időbélyeg + méret."""
    ido_lo = filetime & _MASZK32
    ido_hi = (filetime >> 32) & _MASZK32
    return (
        js_hash(teljes_ut, kodolas=kodolas)
        ^ rol(ido_lo, 13)
        ^ rol(ido_hi, 17)
        ^ rol(meret, 18)
    ) & _MASZK32


def checksum_idobelyeges(filetime: int) -> int:
    """**2. mód**: csak a másodpercre kerekített időbélyeg (`0x006b9b26`)."""
    q = _egesz_masodperc(filetime)
    return (rol(q & _MASZK32, 13) ^ rol((q >> 32) & _MASZK32, 17)) & _MASZK32


def utvonalas_modot_kell(
    *, kert_mod: int, tipus: int, van_szuloje: bool
) -> bool:
    """Az útvonalas (1.) módot kell-e használni.

    A három kizáró feltétel (`0x004e3bc2` · `0x004e3bcb` · `0x004e3bd7`):
    a hívó `0`-t kér, a rekord típusa `0`, vagy nincs szülője — bármelyik
    a 2. módra vált. A könyvtárak és az üres slotok tehát mindig a 2.
    módot kapják.
    """
    return bool(kert_mod) and tipus != 0 and van_szuloje


@dataclass(frozen=True)
class EllenorzoJelentes:
    """Egy index-fájl ellenőrzésének összesítése — kivétel NÉLKÜL.

    A nem egyező sor **ma is használható adat**: a 4%-os eltérés oka nincs
    eldöntve (másik Picasa-verzió? más kódlap? romlás?), és az eredeti
    verifikálója ráadásul időzóna-toleráns, amit mi nem utánzunk. Kivételt
    dobni erre annyi volna, mint egy meg nem értett jelenség miatt eldobni
    a katalógus 4%-át.
    """

    osszes: int
    utvonalas_egyezik: int
    idobelyeges_egyezik: int
    nem_egyezik: int

    @property
    def egyezik(self) -> int:
        return self.utvonalas_egyezik + self.idobelyeges_egyezik

    @property
    def egyezes_aranya(self) -> float:
        return self.egyezik / self.osszes if self.osszes else 1.0


def ellenorizd(parok, *, kodolas: str = "utf-8") -> EllenorzoJelentes:
    """Slot–bejegyzés párok ellenőrzése; NEM dob, jelentést ad.

    `parok`: `(tarolt_checksum, teljes_ut, filetime, meret)` négyesek.

    Mindkét módot megpróbálja, mert a MÓD a rekordból nem mindig
    állapítható meg utólag (a `kert_mod` a hívó futásidejű döntése volt).
    Ez a mérésnek elég: az `utvonalas_modot_kell` külön áll annak, aki a
    módot előre tudja.
    """
    utvonalas = idobelyeges = nem = 0
    ossz = 0
    for tarolt, teljes_ut, filetime, meret in parok:
        ossz += 1
        if tarolt == checksum_utvonalas(
            teljes_ut, filetime, meret, kodolas=kodolas
        ):
            utvonalas += 1
        elif tarolt == checksum_idobelyeges(filetime):
            idobelyeges += 1
        else:
            nem += 1
    jelentes = EllenorzoJelentes(ossz, utvonalas, idobelyeges, nem)
    if nem:
        logger.warning(
            "A thumbindex %d slotjából %d ellenőrzőösszege egyikkel sem "
            "egyezik (%d útvonalas, %d időbélyeges) — az adatot NEM dobjuk "
            "el, csak jelezzük",
            ossz,
            nem,
            utvonalas,
            idobelyeges,
        )
    return jelentes


__all__ = [
    "EllenorzoJelentes",
    "ellenorizd",
    "checksum_idobelyeges",
    "checksum_utvonalas",
    "js_hash",
    "rol",
    "utvonalas_modot_kell",
]
