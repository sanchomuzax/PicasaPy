#!/usr/bin/env python3
"""Az UI-lefedettségi axis olvasója az állapotlaphoz (#1778).

## Miért ez a forrás

A lap „következő öt kutatnivaló" szakaszát eddig a menüparancs-lefedettség
töltötte fel. Az a forrás **2026-08-31-én kimerült**: a mérés 138/138, tehát
a `kovetkezo_ot()` üres listát ad. A következő axis az **UI-lefedettség** —
az eredeti panelek (2020 elem / 74 panel) és a QML-fánk összevetése.

## Miért olvasunk, és nem mérünk

Az `ui_lefedettseg.py` a **privát** `picasapy-agent` repóban él, a lap
generátora a publikusban. A lap ezért a **commitolt**
`docs/specs/ui-lefedettseg.md`-t olvassa — ugyanaz a minta, mint a
menü-axisnál a `docs/menu-lefedettseg.md`.

⚠️ Ezért a lap **kimondja a mérés dátumát**. Ha a fájl régi, az látszik;
nincs csendben mutatott régi szám.

## A rendezés MÁS elvű, mint a menü-axisé

A menü-sor ábécésorrend volt. Az UI-axis természetes egysége a **panel** —
egy panel egy kör munkája —, ezért a sor a **hiány + bizonytalan** szerint
csökkenő. Ez ugyanúgy nem válogatás (két futás ugyanazt adja), csak nem
ábécé, hanem hatás szerinti rangsor.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path

#: A commitolt mérés helye a publikus repóban.
LAP_UT = (
    Path(__file__).resolve().parents[1] / "docs/specs/ui-lefedettseg.md"
)

#: Hány nap után mondja ki a lap, hogy a mérés elavult.
ELAVULAS_NAP = 30

#: Panelek, amelyekre NEM küldünk kutatói kört, indoklással. A menü-axis
#: `HATOKORON_KIVUL` szűrőjének megfelelője.
#:
#: ⚠️ Szűrő nélkül a rangsor második ötöse már halott szolgáltatásra
#: küldene kört: a `upload` és a `buzzupload` a 7–8. helyen áll.
#:
#: Ami itt NINCS benne, arra kört lehet küldeni — a lista szándékosan
#: szűk: csak megszűnt Google-szolgáltatások szerepelnek benne, nem
#: minden, ami „nehéznek látszik".
HATOKORON_KIVUL: dict[str, str] = {
    "upload": "Picasa Web Albums feltöltő — a szolgáltatás 2016-ban megszűnt",
    "buzzupload": "Google Buzz feltöltés — a szolgáltatás megszűnt",
    "compose_share": (
        "Picasa Web Albums megosztási meghívó — a szolgáltatással együtt "
        "megszűnt"
    ),
}


@dataclass(frozen=True)
class Panel:
    """Egy panel a rangsorból."""

    nev: str
    hiany: int
    leiras: str


@dataclass(frozen=True)
class Meres:
    """A commitolt UI-lefedettségi mérés, ahogy a lap használja."""

    ideje: date | None
    rangsor: tuple[Panel, ...]
    parositva: int
    hianyzik: int
    #: #1878: a hiány KÉT külön dolog — a `hianyzik` feltáratlan (kutatói
    #: kör kell), a `lekutatva` fel van tárva, csak nem megépítve
    #: (fejlesztői kör). A lap mindkettőt kiírja, mert más munka.
    lekutatva: int
    bizonytalan: int
    felulbiralasok: int

    @property
    def kovetkezo_ot(self) -> tuple[Panel, ...]:
        """A hatókörön kívüliek nélkül, a rangsor élérőL."""
        return tuple(
            p for p in self.rangsor if p.nev not in HATOKORON_KIVUL
        )[:5]

    @property
    def kihagyott(self) -> tuple[tuple[str, str], ...]:
        """A rangsorból hatókörön kívül esők — a lap ezeket KIMONDJA,
        hogy a kihagyás ne látsszon feledékenységnek."""
        return tuple(
            (p.nev, HATOKORON_KIVUL[p.nev])
            for p in self.rangsor
            if p.nev in HATOKORON_KIVUL
        )

    def elavult(self, ma: date) -> bool:
        if self.ideje is None:
            return True
        return (ma - self.ideje).days > ELAVULAS_NAP


_DATUM = re.compile(r"\*\*Generálva:\*\*\s*(\d{4})-(\d{2})-(\d{2})")
_RANGSOR_SOR = re.compile(
    r"^\|\s*\d+\s*\|\s*`([^`]+)`\s*\|\s*(\d+)\s*\|\s*(.*?)\s*\|\s*$"
)
_OSSZESITO_SOR = re.compile(r"^\|\s*([^|]+?)\s*\|\s*\*{0,2}([\d.]+)%?\*{0,2}\s*\|\s*$")


def _osszesito(szoveg: str) -> dict[str, int]:
    """Az „Összesítés" tábla számai, kulcs szerint."""
    ki: dict[str, int] = {}
    for sor in szoveg.split("\n"):
        talalat = _OSSZESITO_SOR.match(sor)
        if not talalat:
            continue
        #: A félkövér jelölés a címke BELSEJÉBEN is állhat („hiányzik —
        #: **feltáratlan** (kutatói kör)"), ezért mindet kivesszük, nem
        #: csak a széleken — különben a kulcs nem illeszkedne.
        cimke = talalat.group(1).replace("*", "").strip().lower()
        try:
            ki[cimke] = int(talalat.group(2))
        except ValueError:
            continue
    return ki


#: Az összesítő tábla címkéi EMBERI szövegek — a generátor bővítheti őket
#: („hiányzik" → „hiányzik — **feltáratlan** (kutatói kör kell)"). Ezért
#: prefixre illesztünk, nem pontos egyezésre.
#:
#: ⚠️ MÉRT eset (#1878): amikor a generátor átnevezte ezt a sort, a pontos
#: egyezés némán **0-t** adott — az állapotlapon ez HAMIS JAVULÁSKÉNT
#: jelent volna meg („nincs több hiány"). A `KOTELEZO_KULCSOK` őre ezért
#: nem stílus kérdése: az fogja meg, ha a lap és az olvasó elcsúszik.
KOTELEZO_KULCSOK = (
    "párosítva",
    "hiányzik — feltáratlan",
    "hiányzik — lekutatva",
    "bizonytalan",
)


def _szam(szamok: dict[str, int], prefix: str) -> int:
    """Az első olyan összesítő-sor száma, amelynek címkéje `prefix`-szel kezdődik."""
    for cimke, ertek in szamok.items():
        if cimke.startswith(prefix):
            return ertek
    return 0


def hianyzo_kulcsok(szoveg: str) -> tuple[str, ...]:
    """Mely kötelező összesítő-kulcsok NINCSENEK meg a lapon.

    Ezt az őr-teszt hívja a COMMITOLT lapra. Üres eredmény = a lap és az
    olvasó összhangban van.
    """
    szamok = _osszesito(szoveg)
    return tuple(
        prefix
        for prefix in KOTELEZO_KULCSOK
        if not any(cimke.startswith(prefix) for cimke in szamok)
    )


def _felulbiralasok(gyoker: Path) -> int:
    """Hány elemre van kézi felülbírálás?

    Ez a szám azért kell a lapra, mert a „hiányzik" szám **felfelé
    torzít**, amíg a felülbírálások nincsenek átfésülve — és a csökkenése
    így MUNKA eredménye, nem a mérce lazulása. Két egymást követő kör
    talált téves riasztást: tíz elem az `acquirepanel`-en, három a
    `quicktagconfig`-on."""
    ut = gyoker / "docs/specs/ui-lefedettseg-elemek.csv"
    try:
        sorok = ut.read_text(encoding="utf-8").strip().split("\n")
    except OSError:
        return 0
    return max(0, len(sorok) - 1)  # fejléc nélkül


def olvas(ut: Path | None = None) -> Meres | None:
    """A commitolt mérés beolvasása. `None`, ha a fájl nincs meg."""
    ut = ut or LAP_UT
    try:
        szoveg = ut.read_text(encoding="utf-8")
    except OSError:
        return None

    datum = _DATUM.search(szoveg)
    ideje = (
        date(int(datum.group(1)), int(datum.group(2)), int(datum.group(3)))
        if datum
        else None
    )

    rangsor: list[Panel] = []
    for sor in szoveg.split("\n"):
        talalat = _RANGSOR_SOR.match(sor)
        if talalat:
            rangsor.append(
                Panel(
                    nev=talalat.group(1),
                    hiany=int(talalat.group(2)),
                    leiras=talalat.group(3),
                )
            )

    szamok = _osszesito(szoveg)
    return Meres(
        ideje=ideje,
        rangsor=tuple(rangsor),
        parositva=_szam(szamok, "párosítva"),
        hianyzik=_szam(szamok, "hiányzik — feltáratlan"),
        lekutatva=_szam(szamok, "hiányzik — lekutatva"),
        bizonytalan=_szam(szamok, "bizonytalan"),
        felulbiralasok=_felulbiralasok(ut.resolve().parents[2]),
    )
