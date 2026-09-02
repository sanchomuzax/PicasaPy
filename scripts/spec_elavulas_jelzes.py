#!/usr/bin/env python3
"""Jelzés az elavulhatott spec-szakaszokra (#1958).

## Mit old meg

A `docs/specs/` lapjai „nálunk" oszlopban írják le, mi hiányzik a mi
megvalósításunkból. Ha egy fejlesztői kör **megépíti** azt, amit egy
kutatói kör hiányként írt le, a lap **némán elavul** — és a következő
kutatói kör valódi hiánynak hiszi.

MÉRVE (#1958): 2026-09-02-án egy nap alatt **négy** ilyen elavult állítás
vitt el egy-egy kutatói kört. A legélesebb eset: a spec **egy nappal** a
javítás előtt készült, és a javító jegy **hivatkozott is rá** — mégsem
frissült.

## A jelzés heurisztikája — és a korlátja

Egy szakasz gyanús, ha (a) tartalmazza a „nálunk" szót, ÉS (b) hivatkozik
egy **LEZÁRT** jegyre. Az ilyen szakasz gyakran épp azt írja le, hogy a
munka KÉSZ — ezért ez **figyelmeztetés, nem kapu**: a kilépőkód mindig 0.

⚠️ **A találat nem hiba.** A legtöbb jogos: a szakasz a lezárt jegy
eredményét dokumentálja. A lista arra való, hogy a következő kutatói kör
NE induljon el egy elavult állításból — nem arra, hogy bárki tömegesen
átírja a lapokat.

## Használat

    python3 scripts/spec_elavulas_jelzes.py            # a lezártságot `gh`-val kérdezi
    python3 scripts/spec_elavulas_jelzes.py --offline  # csak a szakaszokat listázza
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from collections.abc import Callable, Iterable
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SPEC_DIR = REPO / "docs" / "specs"

#: A „nálunk" oszlop jelölése — kis- és nagybetűtől függetlenül, a magyar
#: ragozott alakokat is beleértve („nálunk", „Nálunk mérve", „nálunk:").
NALUNK = re.compile(r"\bnálunk\b", re.IGNORECASE)

#: Jegyhivatkozás: `#1234`. A négyjegyűnél rövidebb számok túl sok hamis
#: találatot adnának (verziószám, sorszám), ezért három számjegytől.
JEGY = re.compile(r"#(\d{3,5})\b")

#: Ennyi sort nézünk a fájl elején a „generált" jelölés keresésekor —
#: ugyanaz a küszöb, mint a lefedettségi mérőkben.
_FEJLEC_SOROK = 3

#: Ennél több jegyszám egy szakaszban felsorolást jelent, nem állítást.
MAX_JEGY_SZAKASZONKENT = 3
_GENERALT_JELEK = ("generálva", "generált", "ne szerkeszd", "ne írd kézzel")


def generalt_lap(szoveg: str) -> bool:
    """Gépi lap-e — a FEJLÉCE alapján.

    A generált lapokat kihagyjuk: azokat úgysem kézzel javítja senki, és
    a bennük lévő jegyszámok a mérés kimenetei, nem állítások.
    """
    fejlec = "\n".join(szoveg.splitlines()[:_FEJLEC_SOROK]).casefold()
    return any(jel in fejlec for jel in _GENERALT_JELEK)


def szakaszok(szoveg: str) -> list[tuple[int, str]]:
    """(kezdősor, szöveg) párok markdown-címsorok mentén."""
    darabok: list[tuple[int, str]] = []
    kezdet = 1
    aktualis: list[str] = []
    for i, sor in enumerate(szoveg.splitlines(), start=1):
        if sor.startswith("#"):
            if aktualis:
                darabok.append((kezdet, "\n".join(aktualis)))
            kezdet = i
            aktualis = [sor]
        else:
            aktualis.append(sor)
    if aktualis:
        darabok.append((kezdet, "\n".join(aktualis)))
    return darabok


def gyanus_szakaszok(spec_dir: Path) -> list[tuple[str, int, set[str]]]:
    """(fájl, sor, jegyszámok) minden „nálunk"-ot ÉS jegyszámot tartalmazó
    szakaszra, a generált lapok nélkül."""
    ki: list[tuple[str, int, set[str]]] = []
    if not spec_dir.is_dir():
        return ki
    for f in sorted(spec_dir.glob("*.md")):
        szoveg = f.read_text(encoding="utf-8")
        if generalt_lap(szoveg):
            continue
        for sor, szakasz in szakaszok(szoveg):
            if not NALUNK.search(szakasz):
                continue
            jegyek = set(JEGY.findall(szakasz))
            #: ⚠️ A sok jegyszámot felsoroló szakasz TARTALOMJEGYZÉK, nem
            #: állítás a mi állapotunkról — a `00-index.md` egyik szakasza
            #: egyedül 28 jegyet sorol. MÉRVE a mai lapokon: 1 jegy → 67
            #: szakasz, 2 → 107, 3 → 124, és fölötte már csak indexek
            #: jönnek (5-nél több: 7 szakasz, köztük a 17-es és a 28-as).
            #: A háromnál több jegyet említő szakaszt ezért kihagyjuk.
            if jegyek and len(jegyek) <= MAX_JEGY_SZAKASZONKENT:
                ki.append((f.name, sor, jegyek))
    return ki


def _gh_zart(szamok: Iterable[str]) -> set[str]:
    """A lezárt jegyek halmaza — EGYETLEN `gh` hívással.

    ⚠️ Jegyenkénti `gh issue view` NEM jó: a mai lapokon 140 gyanús
    szakasz van, összesen több száz jegyszámmal — az percekig tartana a
    CI-ben egy olyan lépésért, ami nem is kapu. Egy listás lekérdezés
    ugyanazt adja egy kérésben.

    Hibánál ÜRES halmazt ad: a jelzés ilyenkor egyszerűen nem szűkít.
    Sosem dob, mert ez nem kapu.
    """
    kertek = {s for s in szamok}
    if not kertek:
        return set()
    try:
        eredmeny = subprocess.run(
            ["gh", "issue", "list", "--state", "closed",
             "--limit", "2000", "--json", "number"],
            capture_output=True, text=True, check=False, timeout=120,
        )
        if eredmeny.returncode != 0:
            return set()
        zartak = {
            str(t["number"]) for t in json.loads(eredmeny.stdout or "[]")
        }
    except (OSError, ValueError, subprocess.SubprocessError):
        return set()
    return kertek & zartak


def jelentes(
    spec_dir: Path = SPEC_DIR,
    *,
    zart_lekerdezo: Callable[[Iterable[str]], set[str]] | None = None,
) -> list[str]:
    """A kiírandó sorok. Üres lista = nincs gyanús szakasz."""
    gyanus = gyanus_szakaszok(spec_dir)
    if not gyanus:
        return []
    minden_jegy = {j for _f, _s, jegyek in gyanus for j in jegyek}
    zart = (zart_lekerdezo or _gh_zart)(minden_jegy)
    if not zart:
        return []
    #: FÁJLONKÉNT csoportosítva: egy kutatói kör egy KONKRÉT lapot néz, és
    #: a saját lapját akarja megtalálni — nem a teljes listát végigolvasni.
    #: A mai mérés 97 találatot ad; egy lapos folyamban az használhatatlan.
    szerint: dict[str, list[str]] = {}
    for fajl, sor, jegyek in gyanus:
        erintett = sorted(jegyek & zart, key=int)
        if erintett:
            szerint.setdefault(fajl, []).append(
                f"    :{sor} — lezárt jegy(ek): "
                + ", ".join(f"#{j}" for j in erintett)
            )
    sorok: list[str] = []
    for fajl in sorted(szerint):
        sorok.append(f"  {fajl}")
        sorok.extend(szerint[fajl])
    return sorok


def main(argv: list[str] | None = None) -> int:
    ertelmezo = argparse.ArgumentParser(description=__doc__)
    ertelmezo.add_argument(
        "--offline", action="store_true",
        help="ne kérdezze le a jegyek állapotát (csak a szakaszokat listázza)",
    )
    beallitasok = ertelmezo.parse_args(argv)

    if beallitasok.offline:
        gyanus = gyanus_szakaszok(SPEC_DIR)
        print(f"„nálunk” + jegyszám: {len(gyanus)} szakasz")
        for fajl, sor, jegyek in gyanus:
            print(f"  {fajl}:{sor} — {', '.join('#' + j for j in sorted(jegyek, key=int))}")
        return 0

    sorok = jelentes()
    if not sorok:
        print("Nincs olyan spec-szakasz, amely „nálunk”-ot ÉS lezárt jegyet "
              "is említ.")
        return 0

    lapok = sum(1 for s in sorok if not s.startswith("    "))
    print(
        f"⚠️  {len(sorok) - lapok} spec-szakasz {lapok} lapon említ "
        "„nálunk”-ot ÉS LEZÁRT jegyet.\n"
        "Ez NEM hiba — a legtöbb szakasz épp a lezárt jegy eredményét írja\n"
        "le. A lista arra való, hogy a következő KUTATÓI kör ne induljon el\n"
        "egy időközben megjavított állításból (#1958).\n"
        "\nHASZNÁLAT: keresd meg a SAJÁT lapodat, és mielőtt egy „nálunk\n"
        "hiányzik” állításra kört indítasz, nézd meg, hogy a hivatkozott\n"
        "jegy lezárása óta nem készült-e el.\n"
    )
    for sor in sorok:
        print(sor)
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
