#!/usr/bin/env python3
"""A kiadás utókövetése a verzióemelő PR beolvadása után (#1338).

## A lelet

A `release.yml` a `push: branches: [main]` eseményre indul. A verzióemelő
PR-t viszont az **integrációs token** olvasztja be, és a GitHub a saját
tokenjével keletkező pushra **szándékosan nem indít workflow-t** — ugyanaz a
rekurzióvédelem, amit a #1190 óta ismerünk, és ami nem kapcsolható ki.
Következmény: a `pyproject.toml` verziója felmegy, a Releases hasáb nem
követi, és a kiadás kézi indításra vár.

**Mérve (2026-08-24):** a `release.yml` negyven futásából egyetlen `push`
sem a verzióemelő PR beolvasztásából jött — mind a negyven `push` egy
EMBERI merge-ből. A nap kiadásait a tulajdonos indította kézzel
(tizennégyszer), és a `github-actions[bot]` mindössze EGYSZER ért oda
előbb (20:03:36), a negyedórás kiadási őrből.

## Miért nem elég a meglévő védelem

A `kiadasi-or.yml` őre már ma is pótolja a hiányzó kiadást
(`kiadas_or.kiadas_teendo`), csak lassan: a `*/15`-ös `cron`-t a GitHub
ütemezője **25–48 percenként** kézbesíti (mérve ugyanazon a napon). A
`release.yml` napi őrfutása pedig legfeljebb egy nap késéssel pótol.

## A megoldás — és miért EZ

A `workflow_dispatch` a rekurzióvédelem **dokumentált kivétele**, és a
repóban **mért** bizonyíték van rá, hogy működik: a fenti 20:03:36-os
`release.yml` futást a `github-actions[bot]` indította így. Ez a szkript
ugyanezt az utat használja — nem újat, aminek a viselkedését csak élesben
lehetne kipróbálni.

A `release.yml` a verzióemelő PR megnyitása után elindítja az utókövetőt.
Az figyeli az `origin/main` verzióját, és amint a beolvadástól az egy még
ki nem adott verzióra ugrik, elindítja a `release.yml`-t. A késleltetés így
**másodpercek**, nem fél nap.

## Amit SOHA nem tesz

* **Nem ad ki semmit.** Csak elindítja a `release.yml`-t, ami idempotens: az
  `ensure_release.py` előbb megnézi, létezik-e már a kiadás. Két helyen
  kiadni két helyen lehetne duplikálni — a kiadás pedig visszavonhatatlan.
* **Tudatlanságból nem indít.** Ha a verzió nem olvasható, vagy a
  létezés-ellenőrzés átmeneti hibába fut (503), a kör kihagyja: a hiányzó
  kiadás pótolható, a fölösleges nem vonható vissza.
* **Legfeljebb egyszer indít**, aztán kilép.

## Ha lejár az idő

Nem hiba: a negyedórás kiadási őr és a `release.yml` napi őrfutása
változatlanul a háló mögötte. Az utókövető a GYORS ÚT, nem az egyetlen.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import time
from collections.abc import Callable
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from ensure_release import atmeneti_hiba, verzio_a_szovegbol  # noqa: E402

Runner = Callable[[list[str]], "subprocess.CompletedProcess[str]"]

#: Hány kört figyeljünk. A verzióemelő PR-ek MÉRT beolvadási ideje
#: (2026-08-24, húsz PR): jellemzően 1–10 perc, medián ~2,5 perc; a
#: leghosszabb 55 perc volt. A 80 kör × 30 mp = 40 perc a mért esetek
#: nagy többségét lefedi, a maradékot a negyedórás kiadási őr viszi.
_ALAP_KOROK = 80
#: Két kérdezés között ennyit várunk, másodpercben.
_ALAP_VARAKOZAS = 30.0


def _valodi_futtato(args: list[str]) -> subprocess.CompletedProcess[str]:
    # #2077: `errors="replace"` — a `git diff` kimenete NEM feltétlenül
    # érvényes UTF-8 (idegen kódolású fájl, bináris darab). Enélkül az
    # őr a DEKÓDOLÁSON hal meg, nem a leleten, és a CI úgy pirosodik,
    # hogy közben semmi baj nincs a vizsgált tartalommal.
    return subprocess.run(
        args, capture_output=True, text=True, encoding="utf-8", errors="replace", check=False
    )


def fo_verzio(*, runner: Runner = _valodi_futtato) -> str | None:
    """A `main` FEJÉN álló verzió — nem a munkafáé.

    ⚠️ A munkafa a futás indulásakori állapotot mutatja, a verzióemelő PR
    pedig épp azután olvad be. A kérdés csak a friss `origin/main`-en
    válaszolható meg, ezért minden kör előtt `fetch`-elünk.

    `None`, ha nem sikerült megállapítani. Ez NEM ugyanaz, mint egy verzió:
    tudatlanságból kiadást indítani tilos."""
    runner(["git", "fetch", "--quiet", "origin", "main"])
    eredmeny = runner(["git", "show", "origin/main:pyproject.toml"])
    if eredmeny.returncode != 0:
        return None
    try:
        return verzio_a_szovegbol(
            eredmeny.stdout or "", forras="az origin/main pyproject.toml-ja"
        )
    except ValueError:
        return None


def van_kiadas(verzio: str, *, repo: str, runner: Runner = _valodi_futtato) -> bool | None:
    """Létezik-e a `v<verzió>` kiadás? `None`, ha nem tudjuk megállapítani.

    ⚠️ A `gh` hibakódja nem különbözteti meg a „nincs ilyen"-t a „nem érhető
    el"-től. Egy 503-ból tehát NEM következik, hogy a kiadás hiányzik — ez
    ugyanaz a csapda, amit az `ensure_release.py` fejléce leír."""
    valasz = runner(["gh", "release", "view", f"v{verzio}", "--repo", repo])
    if valasz.returncode == 0:
        return True
    if atmeneti_hiba(valasz):
        return None
    return False


def kiadas_inditasa(*, repo: str, runner: Runner = _valodi_futtato) -> bool:
    """A `release.yml` elindítása a `main`-en. Sikerült-e?

    ⚠️ SZÁNDÉKOSAN `workflow_dispatch`: ez a rekurzióvédelem dokumentált
    kivétele, tehát az integrációs token is el tudja indítani vele a
    kiadót. Ugyanezt az utat járja a `kiadas_or.py` is."""
    eredmeny = runner([
        "gh", "workflow", "run", "release.yml", "--repo", repo, "--ref", "main",
    ])
    if eredmeny.returncode == 0:
        return True
    print(
        f"::error title=A kiadás indítása nem sikerült::"
        f"A `gh workflow run release.yml` elbukott: "
        f"{(eredmeny.stderr or eredmeny.stdout or '').strip()[:200]}"
    )
    return False


def utokovet(
    *,
    repo: str,
    runner: Runner = _valodi_futtato,
    sleeper: Callable[[float], None] = time.sleep,
    korok: int = _ALAP_KOROK,
    varakozas: float = _ALAP_VARAKOZAS,
) -> int:
    """Megvárja, hogy a `main` egy kiadatlan verzióra ugorjon, és kiad.

    `0`, ha elindította a kiadást, vagy ha nem volt mit tenni; `1`, ha az
    indítás elbukott.

    ⚠️ A hurok ALVÁSSAL kezd. Indulásakor a `main` még a régi, MÁR KIADOTT
    verziónál tart (a `release.yml` kiadó lépése akár még futhat is) —
    azonnal kérdezni fölösleges kört indítana a kiadóra."""
    for _ in range(korok):
        sleeper(varakozas)

        verzio = fo_verzio(runner=runner)
        if verzio is None:
            print("Az origin/main verziója most nem olvasható — a következő körben újra.")
            continue

        kiadva = van_kiadas(verzio, repo=repo, runner=runner)
        if kiadva is None:
            print(f"A v{verzio} létezés-ellenőrzése átmeneti hibába futott — újra.")
            continue
        if kiadva:
            continue

        print(f"A main a v{verzio}-nál tart, és ehhez még nincs kiadás — indítjuk.")
        return 0 if kiadas_inditasa(repo=repo, runner=runner) else 1

    print(
        "::notice title=Az utókövetés lejárt::"
        "A figyelt idő alatt nem jelent meg kiadatlan verzió a main-en. "
        "Ha mégis lemaradt volna, a negyedórás kiadási őr pótolja (#1319)."
    )
    return 0


def main(argv: list[str] | None = None, *, runner: Runner = _valodi_futtato) -> int:
    ertelmezo = argparse.ArgumentParser(description="A kiadás utókövetése (#1338)")
    ertelmezo.add_argument("--repo", required=True, help="tulajdonos/repó")
    ertelmezo.add_argument("--korok", type=int, default=_ALAP_KOROK)
    ertelmezo.add_argument("--varakozas", type=float, default=_ALAP_VARAKOZAS)
    beallitas = ertelmezo.parse_args(argv)

    return utokovet(
        repo=beallitas.repo,
        runner=runner,
        korok=beallitas.korok,
        varakozas=beallitas.varakozas,
    )


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
