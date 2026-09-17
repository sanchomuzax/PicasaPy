"""A kézi sorrend SZÁMÍTÁSA és mentése (#1721, ADR-014).

A rácson húzással átrendezett képek sorrendjét a mappa `.picasa.ini`-je
hordozza (`priority=`, `ini/priority.py`). Ez a modul a Qt-tól független
mag: kiszámolja, MELY képeknek MILYEN új kézi hely jár, és kiírja őket.

## Miért nem írja át mindig az egész mappát

Az ADR kimondja: „egy áthelyezés nem írja át az egész mappát (és nem termel
tucatnyi `.picasa.ini`-írást)". Ezért két ág van:

* **bootstrap** — ha a mappában MÉG NINCS egyetlen kézi hely sem, a teljes
  új sorrend kiíródik (0, 1, 2, …). Egyszer, egyetlen ini-írásban: ez az az
  „első húzás", amelyik a mappát kézi rendbe teszi;
* **beszúrás** — ha már VAN kézi hely, csak a MOZGATOTT képek kapnak új
  értéket, a két szomszéd közötti felezőpontból (`ini.priority.kozteslepes`).

## Mappahatár

A kézi sorrend mappánként él (a kulcs a mappa ini-jében van), és a
kijelölés hatóköre az eredetiben is EGY mappa (#1219, mérve). Több mappát
érintő húzásra ezért nincs értelmezhető művelet — az `ellenorizd_az_egy_mappat`
`None`-t ad, és a hívó nem ír semmit.
"""

from __future__ import annotations

from pathlib import Path

from picasapy.ini.io import update_document
from picasapy.ini.priority import (
    kozteslepes,
    olvasd_a_prioritasokat,
    prioritassal,
)

#: a mappa ini-fájljának neve — az `ini/` csomag konvenciója
INI_FAJLNEV = ".picasa.ini"


def ellenorizd_az_egy_mappat(kepek) -> str | None:
    """A képek KÖZÖS mappája, vagy `None`, ha nem egy mappában vannak.

    Üres listánál is `None`: nincs mit átrendezni.
    """
    mappak = {kep.folder_path for kep in kepek}
    if len(mappak) != 1:
        return None
    return next(iter(mappak))


def atrendezett_prioritasok(
    uj_sorrend, meglevo: dict, mozgatott
) -> dict[str, float]:
    """A KIÍRANDÓ kézi helyek: fájlnév → érték.

    `uj_sorrend`: a mappa képeinek fájlnevei a húzás UTÁNI sorrendben.
    `meglevo`: a mappa mai kézi helyei (`ini.priority.olvasd_a_prioritasokat`).
    `mozgatott`: a húzással áthelyezett képek fájlnevei.

    Csak azt adja vissza, amit tényleg ki kell írni — a nem mozgatott képek
    kulcsa érintetlen marad.
    """
    uj_sorrend = list(uj_sorrend)
    mozgatott = {nev for nev in mozgatott if nev in uj_sorrend}
    if not mozgatott:
        return {}

    if not meglevo:
        # bootstrap: a mappa most kerül kézi rendbe — egyszer, egészben
        return {nev: float(i) for i, nev in enumerate(uj_sorrend)}

    return _beszurt_ertekek(uj_sorrend, meglevo, mozgatott)


def _beszurt_ertekek(
    uj_sorrend: list, meglevo: dict, mozgatott: set
) -> dict[str, float]:
    """A mozgatott képek új értékei, a szomszédok közé felezve.

    Az EGYMÁS UTÁNI mozgatott képek (blokkos húzás) egy „rést" osztanak fel
    egymás között — így a blokk sorrendje is megmarad, és a nem mozgatott
    szomszédok kulcsához nem kell hozzányúlni.
    """
    ertekek: dict[str, float] = {}
    i = 0
    while i < len(uj_sorrend):
        if uj_sorrend[i] not in mozgatott:
            i += 1
            continue
        # a mozgatott FUTAM hossza
        j = i
        while j < len(uj_sorrend) and uj_sorrend[j] in mozgatott:
            j += 1
        elozo = _horgony(uj_sorrend, i - 1, meglevo, ertekek, elore=False)
        kovetkezo = _horgony(uj_sorrend, j, meglevo, ertekek, elore=True)
        ertekek.update(_futam_ertekei(uj_sorrend[i:j], elozo, kovetkezo))
        i = j
    return ertekek


def _horgony(sorrend, index, meglevo, ertekek, *, elore: bool):
    """A futam melletti, KÉZI HELLYEL rendelkező szomszéd értéke.

    A mozgatott képeken túl lép: azok értéke épp most készül. Ha nincs ilyen
    szomszéd (a lista széle), `None` — ekkor a hívó a szélre szúr be.
    """
    lepes = 1 if elore else -1
    while 0 <= index < len(sorrend):
        nev = sorrend[index]
        if nev in ertekek:
            return ertekek[nev]
        if nev in meglevo:
            return float(meglevo[nev])
        index += lepes
    return None


def _futam_ertekei(nevek, elozo, kovetkezo) -> dict[str, float]:
    """Egy mozgatott futam értékei a két horgony KÖZÖTT, sorrendtartóan."""
    if len(nevek) == 1:
        return {nevek[0]: kozteslepes(elozo, kovetkezo)}
    # több kép: a rés egyenletes felosztása, hogy a blokk sorrendje éljen
    also = elozo if elozo is not None else (
        (kovetkezo - len(nevek) - 1.0) if kovetkezo is not None else 0.0
    )
    felso = kovetkezo if kovetkezo is not None else also + len(nevek) + 1.0
    lepes = (felso - also) / (len(nevek) + 1)
    return {nev: also + lepes * (i + 1) for i, nev in enumerate(nevek)}


def mentsd_a_prioritasokat(mappa, ertekek: dict) -> None:
    """A kiszámolt kézi helyek kiírása a mappa `.picasa.ini`-jébe.

    Üres szótárnál NEM nyit fájlt: egy fölösleges írás a #643 óta a
    képfájlok mtime-ját is megérintené.
    """
    if not ertekek:
        return

    def mutate(document):
        for nev, ertek in ertekek.items():
            document = prioritassal(document, nev, ertek)
        return document

    update_document(Path(mappa) / INI_FAJLNEV, mutate)


def mappa_prioritasai(mappa) -> dict[str, float]:
    """A mappa mai kézi helyei — hiányzó vagy olvashatatlan fájlnál üres.

    A rendezés soha nem borulhat el egy olvasási hibán: ilyenkor a mappa
    „nincs kézi helyen" állapotba esik, és a rács fájlnév-sorrendre vált.
    """
    from picasapy.ini.io import load_or_empty

    try:
        document = load_or_empty(Path(mappa) / INI_FAJLNEV)
    except OSError:
        return {}
    return olvasd_a_prioritasokat(document)
