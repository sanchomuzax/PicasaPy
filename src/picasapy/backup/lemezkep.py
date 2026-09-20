"""A mentés kimenete LEMEZKÉPEKBE (#2074).

A tulajdonos 2026-09-18-án a **(b)** ágat választotta:

> Biztonsági mentés - a gyűjtemény mentése több lemezképre

Ez a modul a mentés-terv fájljait a MÉRT kapacitás-képlet szerint lemezekre
osztja (`burn.lemezekre_oszt`), és lemezenként egy ISO 9660 + Joliet képet ír
(`burn.iso.iso_kiirasa`). Fizikai lemezírás NINCS — a tulajdonos gépén nincs
lemezíró, és az eredeti is lemezképet ír helyette
(`il_BurnPanel::InsertNext::7s/7p`).

## Ami minden lemezre rákerül

* a rá eső fájlok, a gyűjteménybeli **relatív útjukkal** (a fa megmarad);
* a fájlok mellé a mappájuk `.picasa.ini`-je — ettől lesz a lemez önmagában
  teljes értékű archívum (a címkék, csillagok, szerkesztések a képek mellett
  maradnak, ld. `futtatas.py`);
* a gyökérben a `files.txt` manifeszt — a mentés a programunk nélkül is
  olvasható és ellenőrizhető legyen.

## A sorszámozás

A képek neve `<alap>-01.iso`, `<alap>-02.iso` … — az eredeti is sorszámoz
(`InsertNext::13`: „Ez lesz a(z) %d. számú lemez a(z) %d darabból."). A
kötetnév ugyanezt hordozza, hogy a felcsatolt lemezen is látszódjon.

⚠️ A lemezméretnél NAGYOBB egyetlen fájl SAJÁT lemezt kap, és az a lemez
túlcsordul — a `burn.lemezekre_oszt` így tesz, és ez a modul ki is mondja a
hívónak (`tulcsordulo`), nem hallgatja el.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path

from picasapy.burn import hasznalhato_kapacitas, lemezekre_oszt
from picasapy.burn.iso import iso_kiirasa
from picasapy.scanner import PICASA_INI_NAME

from .futtatas import MANIFESZT_NEVE

#: A lemezképek nevének alapja és a kötetnév előtagja.
ALAPNEV = "picasapy-mentes"


@dataclass(frozen=True)
class LemezkepTetel:
    """Egy fájl, ahogy a lemezképbe kerül."""

    relativ: Path
    forras: Path
    meret: int


@dataclass(frozen=True)
class LemezkepEredmeny:
    """Mi készült el — a felület ebből beszél a felhasználóval."""

    #: a kiírt képek útjai, sorrendben
    kepek: tuple[Path, ...]
    #: lemezenként a ráírt fájlok darabszáma
    darabok: tuple[int, ...]
    #: azok a fájlok, amelyek EGYEDÜL sem férnek rá egy lemezre
    tulcsordulo: tuple[Path, ...]


def _manifeszt_szoveg(tetelek: Sequence[LemezkepTetel]) -> str:
    sorok = [f"{tetel.relativ.as_posix()}\t{tetel.meret}" for tetel in tetelek]
    return "\n".join(sorok) + ("\n" if sorok else "")


def _ini_tarsak(tetelek: Sequence[LemezkepTetel]) -> list[tuple[str, Path]]:
    """A lemezre kerülő fájlok mappáinak `.picasa.ini`-jei.

    Mappánként egyszer, és csak ha a forrásmappában tényleg van ini —
    üres fájlt nem gyártunk.
    """
    parok: dict[str, Path] = {}
    for tetel in tetelek:
        ini = tetel.forras.parent / PICASA_INI_NAME
        if not ini.is_file():
            continue
        cel = tetel.relativ.parent / PICASA_INI_NAME
        parok.setdefault(cel.as_posix(), ini)
    return sorted(parok.items())


def lemezkepekbe(
    tetelek: Iterable[LemezkepTetel],
    cel_mappa: Path,
    *,
    media: str,
    szektorszam: int = 0,
    alapnev: str = ALAPNEV,
    ido: float | None = None,
    haladas: Callable[[tuple[int, int]], None] | None = None,
) -> LemezkepEredmeny:
    """A terv fájljait sorszámozott ISO-képekbe írja.

    A kapacitás a MÉRT képletből jön (`szektor × 2048 − tartalék`,
    `0x0066be90`) — a hívó a médiatípust és a névleges szektorszámot adja meg.
    """
    tetelek = list(tetelek)
    cel_mappa = Path(cel_mappa)
    cel_mappa.mkdir(parents=True, exist_ok=True)
    kapacitas = hasznalhato_kapacitas(media, szektorszam=szektorszam)

    csoportok = lemezekre_oszt(
        ((str(index), tetel.meret) for index, tetel in enumerate(tetelek)),
        kapacitas=kapacitas,
    )
    kepek: list[Path] = []
    darabok: list[int] = []
    tulcsordulo = tuple(
        tetel.forras for tetel in tetelek if tetel.meret > kapacitas
    )
    osszes = len(csoportok)
    for sorszam, csoport in enumerate(csoportok, start=1):
        rajta = [tetelek[int(kulcs)] for kulcs, _meret in csoport]
        nev = f"{alapnev}-{sorszam:02d}.iso"
        kotetnev = f"{alapnev.upper()}-{sorszam:02d}"[:32]
        manifeszt = cel_mappa / f".{nev}.{MANIFESZT_NEVE}"
        manifeszt.write_text(_manifeszt_szoveg(rajta), encoding="utf-8")
        tartalom: list[tuple[str, Path]] = [
            (tetel.relativ.as_posix(), tetel.forras) for tetel in rajta
        ]
        tartalom.extend(_ini_tarsak(rajta))
        tartalom.append((MANIFESZT_NEVE, manifeszt))
        kep = iso_kiirasa(tartalom, cel_mappa / nev, kotetnev=kotetnev, ido=ido)
        manifeszt.unlink(missing_ok=True)
        kepek.append(kep)
        darabok.append(len(rajta))
        if haladas is not None:
            haladas((sorszam, osszes))
    return LemezkepEredmeny(
        kepek=tuple(kepek), darabok=tuple(darabok), tulcsordulo=tulcsordulo
    )


__all__ = ["ALAPNEV", "LemezkepEredmeny", "LemezkepTetel", "lemezkepekbe"]
