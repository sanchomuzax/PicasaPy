#!/usr/bin/env python3
"""#2083: verziókövetett fájl nem lehet nagyobb a küszöbnél — kivétellistával.

## Az eset, ami miatt van

2026-09-03-án egy `git add -A` bevitte a munkafában heverő `temp_1645/`
mappát egy PR-be: **168 fájl, 84 MB**, a tulajdonos Picasa-adatbázisának
(`db3`) másolata — egy PUBLIKUS repóba. A beolvadást csak az akadályozta
meg, hogy a changelog-őr a bináris `git diff`-en dekódolási hibára futott.
Vagyis a védelem **véletlen** volt, nem szándékos.

## A küszöb MÉRÉSBŐL jön, nem hasra ütésből

A repó akkori állapotában (1605 követett fájl):

| küszöb | fölötte |
|---|---:|
| 1 MB | **1** |
| 512 KB | 3 |
| 256 KB | 5 |

Egyetlen fájl van 1 MB fölött (`docs/assets/notebooklm-infografika.png`,
5,2 MB), és az szándékos. A bevitt adathalmaz legnagyobb darabja **12 MB**
volt. Az 1 MB-os küszöb tehát MA nulla hamis riasztást ad, és az esetet
megfogta volna.

⚠️ **A kivétel nem kényelmi lehetőség.** Aki ide vesz fel egy fájlt, azzal
azt állítja, hogy a repóban a helye — és az indoklás ezt megmondja. Ha a
lista nőni kezd, az nem a küszöb hibája, hanem jelzés.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

GYOKER = Path(__file__).resolve().parents[1]

#: A küszöb bájtban. A mérés szerint 1 MB fölött MA egyetlen fájl van.
KUSZOB = 1_000_000

#: Szándékosan a repóban tartott, küszöb fölötti fájlok — útvonal → indok.
KIVETELEK: dict[str, str] = {
    "docs/assets/notebooklm-infografika.png": (
        "a projekt kutatási infografikája, a README-ből hivatkozva (5,2 MB)"
    ),
}


def _utf8_kimenet() -> None:
    """#2077: a Windows-konzol cp1252-je nem tudja a `✅`-t."""
    for folyam in (sys.stdout, sys.stderr):
        try:
            folyam.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, OSError, ValueError):
            pass


def kovetett_fajlok() -> list[str]:
    ki = subprocess.run(
        ["git", "ls-files"],
        cwd=GYOKER,
        capture_output=True,
        text=True,
        errors="replace",
        check=False,
    )
    return [s for s in ki.stdout.split("\n") if s.strip()]


def main() -> int:
    _utf8_kimenet()
    hibak: list[str] = []
    ellenorzott = 0
    for rel in kovetett_fajlok():
        p = GYOKER / rel
        if not p.is_file():
            continue
        ellenorzott += 1
        meret = p.stat().st_size
        if meret <= KUSZOB or rel in KIVETELEK:
            continue
        hibak.append(f"{rel}: {meret:,} bájt (küszöb: {KUSZOB:,})")

    if hibak:
        print("Nagy-fájl őr: küszöb fölötti, verziókövetett fájl:")
        for h in hibak:
            print(f"  {h}")
        print(
            "\nHa SZÁNDÉKOS, vedd fel a KIVETELEK szótárba INDOKLÁSSAL.\n"
            "Ha nem az: valószínűleg `git add -A` vitte be (#2083) — "
            "`git rm --cached` és `.gitignore`."
        )
        return 1

    print(
        f"✅ {ellenorzott} követett fájl, egyik sem lépi túl a "
        f"{KUSZOB:,} bájtos küszöböt ({len(KIVETELEK)} kimondott kivétel)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
