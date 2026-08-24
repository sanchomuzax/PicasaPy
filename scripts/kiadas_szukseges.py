#!/usr/bin/env python3
"""Kell-e verzióemelés a beolvadt munkához? (#1319)

## Miért

A `release.yml` #1127 óta a main minden pushja után emel verziót, ha a
jelenlegi verzióhoz MÁR van kiadás. Ez VAKON emelt: a #1318-as verzióemelő
PR-t egy olyan merge szülte, ami mindössze két `docs/specs/` fájlt
módosított. Kiadni nem volt mit, a PR mégis ott ült nyitva — a rendrakás egy
figyelmes műszakon múlt.

## A szabály

Akkor emelünk, ha az utolsó kiadás óta a **program maga** változott.
Dokumentáció, teszt, munkafolyamat és belső eszköz önmagában nem indokol
kiadást — ezek nem jutnak el a felhasználóhoz.

## Melyik irányba tévedjünk?

Nem szimmetrikus a két hiba. Egy felesleges patch-kiadás olcsó (egy sor a
Releases hasábban), egy ELMARADT kiadás viszont némán tartja vissza a kész
javítást a felhasználótól. Ezért az ismeretlen útvonal **kiadhatónak**
számít, és a tájékozódás bukása (hiányzó címke) is a kiadás felé dönt.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from collections.abc import Callable, Iterable

Runner = Callable[[list[str]], "subprocess.CompletedProcess[str]"]

#: Útvonal-előtagok, amelyek NEM jutnak el a felhasználóhoz: fejlesztői
#: dokumentáció, teszt, munkafolyamat-definíció, belső eszközök, kutatási
#: anyag. A `.md` kiterjesztést külön kezeljük — az bárhol állhat.
_NEM_KIADHATO_ELOTAGOK = (
    ".claude/",
    ".github/",
    "docs/",
    "research/",
    "scripts/",
    "tests/",
)

#: Fájlnevek, amelyek önmagukban sosem indokolnak kiadást.
_NEM_KIADHATO_FAJLOK = (
    ".gitignore",
    ".gitattributes",
    ".editorconfig",
)


def _kiadhato(fajl: str) -> bool:
    # ⚠️ `lstrip("./")` NEM jó: az minden vezető pontot és perjelet levág,
    # tehát a `.github/` a „github/" alakká válna, és kiadhatónak
    # látszana. A bukó teszt ezt fogta meg (#1319).
    ut = fajl.strip().removeprefix("./")
    if not ut:
        return False
    if ut.endswith(".md") or ut in _NEM_KIADHATO_FAJLOK:
        return False
    return not ut.startswith(_NEM_KIADHATO_ELOTAGOK)


def erdemi_fajlok(fajlok: Iterable[str]) -> tuple[str, ...]:
    """A felsoroltak közül azok, amelyek a felhasználóhoz eljutnak.

    A futás naplója ezt írja ki: enélkül a döntés visszakereshetetlen lenne
    — „miért nem lett kiadás?" nem válaszolható meg utólag."""
    return tuple(f.strip() for f in fajlok if _kiadhato(f))


def kiadasra_erdemes(fajlok: Iterable[str] | None) -> bool:
    """Indokol-e kiadást a felsorolt változás?

    A `None` a tájékozódás BUKÁSA (nem tudtuk lekérdezni a diffet) — ilyenkor
    a kiadás felé tévedünk, ld. a modul fejlécét."""
    if fajlok is None:
        return True
    return bool(erdemi_fajlok(fajlok))


def _valodi_git(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, capture_output=True, text=True, check=False)


def valtozott_fajlok(
    base: str, head: str, *, runner: Runner = _valodi_git
) -> tuple[str, ...] | None:
    """A két ref közti fájllista; `None`, ha a lekérdezés nem sikerült."""
    eredmeny = runner(["git", "diff", "--name-only", base, head])
    if eredmeny.returncode != 0:
        return None
    return tuple(sor for sor in (eredmeny.stdout or "").splitlines() if sor.strip())


def main(argv: list[str] | None = None, *, runner: Runner = _valodi_git) -> int:
    ertelmezo = argparse.ArgumentParser(description="Kell-e verzióemelés?")
    ertelmezo.add_argument("--base", required=True, help="az utolsó kiadás refje")
    ertelmezo.add_argument("--head", default="HEAD", help="a vizsgált fej")
    beallitas = ertelmezo.parse_args(argv)

    fajlok = valtozott_fajlok(beallitas.base, beallitas.head, runner=runner)
    kell = kiadasra_erdemes(fajlok)

    # Az ELSŐ sor a válasz — erre a munkafolyamat is támaszkodik. Utána
    # ember számára olvasható indoklás megy.
    print("igen" if kell else "nem")
    if fajlok is None:
        print(
            f"A(z) {beallitas.base} nem érhető el — a változás nem mérhető, "
            f"ezért a kiadás felé döntünk."
        )
        return 0
    erdemi = erdemi_fajlok(fajlok)
    if erdemi:
        print("A programot érintő fájlok:")
        for f in erdemi:
            print(f"  {f}")
    else:
        print(
            f"A(z) {beallitas.base} óta {len(fajlok)} fájl változott, de egyik "
            f"sem jut el a felhasználóhoz (dokumentáció/teszt/munkafolyamat)."
        )
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
