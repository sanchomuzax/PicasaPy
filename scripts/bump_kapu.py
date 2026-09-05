#!/usr/bin/env python3
"""Szabad-e MOST verzióemelő PR-t nyitni? (#1348)

## Miért

A #1319 konkurenciazára a `release.yml` FUTÁSAIT állítja sorba, de nem a
döntést, amit hoznak. A második futás akkor is elindul, amikor az elsőnek a
verzióemelő PR-je már nyitva van (vagy épp most olvadt be), csak a saját —
KORÁBBI — commitját nézi, ott pedig még a régi verzió áll. Így ugyanarra a
számra születik egy MÁSODIK verzióemelő PR.

Mért eset (a jegy törzse, 2026-08-24): a #1346 a 0.8.73 → 0.8.74 emelést
vitte és beolvadt, a #1347 öt perccel később ugyanezt nyitotta meg —
`CONFLICTING` állapotban, tehát beolvaszthatatlanul. A rendrakás kézzel
történt. Ugyanez a mintázat négyszer fordult elő (0.8.49, 0.8.70 kétszer is,
0.8.74, 0.8.95, 0.8.129).

## A szabály

Az automatikának egyszerre EGY verzióemelése lehet úton. Ez a kapu erre a
kérdésre válaszol, mielőtt bármit írnánk vagy pusholnánk:

1. van-e már nyitott automatika-PR (bármelyik verzióra) — ha igen, a másik
   futás dolgozik, nem nyitunk másodikat;
2. a cél verzió nem járt-e le: az `origin/main` már ott tart-e vagy tovább;
3. van-e már kiadás a cél verzióhoz.

## Melyik irányba tévedjünk?

A `kiadas_szukseges.py`-vel azonos elv: az ELMARADT kiadás drágább, mint egy
fölösleges PR (azt a kiadási őr magától lezárja, #1319). Ezért ha a
tájékozódás BUKIK — nem érjük el a `gh`-t, nem tudjuk kiolvasni az
`origin/main` verzióját —, a kapu **enged**, és a döntést naplózza.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections.abc import Callable, Iterable, Sequence
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from ensure_release import verzio_a_szovegbol  # noqa: E402
from kiadas_or import AUTO_AG_ELOTAG, verzio_az_agbol  # noqa: E402

Runner = Callable[[list[str]], "subprocess.CompletedProcess[str]"]


def _valodi_futtato(args: list[str]) -> subprocess.CompletedProcess[str]:
    # #2077: `errors="replace"` — az idegen kódolású kimenet ne a
    # DEKÓDOLÁSON ölje meg a kaput; a lelet fontosabb, mint a bájthűség.
    return subprocess.run(
        args, capture_output=True, text=True, encoding="utf-8", errors="replace", check=False
    )


def _rendezheto(verzio: str) -> tuple[int, ...] | None:
    darabok = verzio.strip().split(".")
    if len(darabok) != 3 or not all(d.isdigit() for d in darabok):
        return None
    return tuple(int(d) for d in darabok)


def dontes(
    cel: str,
    *,
    nyitott_agak: Iterable[str],
    fo_verzio: str | None,
    van_kiadas: bool | None,
) -> tuple[bool, str]:
    """Nyithatunk-e verzióemelő PR-t a `cel` verzióra?

    A `(szabad, indok)` párost adja vissza. Tiszta függvény: a `gh`/`git`
    lekérdezés máshol van, hogy a DÖNTÉSRE lehessen állítást írni.

    * `nyitott_agak` — a nyitott PR-ek fej-ágai (a nem automatikáé nem
      számít, azokat kiszűrjük);
    * `fo_verzio` — az `origin/main` verziója, `None`, ha nem olvasható;
    * `van_kiadas` — van-e már `v<cel>` kiadás, `None`, ha nem kérdezhető le.
    """
    auto = [ag for ag in nyitott_agak if verzio_az_agbol(ag) is not None]
    if auto:
        return False, (
            f"már van nyitott verzióemelő PR ({', '.join(sorted(auto))}) — "
            f"a másik futás emelése még úton van"
        )

    if van_kiadas:
        return False, f"a v{cel} kiadás már megvan — nincs mit emelni"

    cel_rend = _rendezheto(cel)
    fo_rend = _rendezheto(fo_verzio) if fo_verzio else None
    if cel_rend is not None and fo_rend is not None and cel_rend <= fo_rend:
        return False, (
            f"az origin/main már a {fo_verzio} verziónál tart — a {cel} "
            f"emelés lejárt"
        )

    return True, f"a {cel} emelésre nincs nyitott PR, és a main még nem tart ott"


def nyitott_auto_agak(repo: str, *, futtato: Runner = _valodi_futtato) -> tuple[str, ...]:
    """A nyitott automatika-PR-ek fej-ágai; lekérdezési hibára üres lista.

    ⚠️ Az üres lista ENGEDÉST jelent — ez szándékos (ld. a modul fejlécét):
    egy fölösleges PR-t a kiadási őr lezár, egy elmaradt kiadást senki."""
    eredmeny = futtato([
        "gh", "pr", "list", "--repo", repo, "--state", "open",
        "--limit", "100", "--json", "headRefName",
    ])
    if eredmeny.returncode != 0:
        return ()
    try:
        adat = json.loads(eredmeny.stdout or "[]")
    except json.JSONDecodeError:
        return ()
    return tuple(
        str(elem.get("headRefName", ""))
        for elem in adat
        if str(elem.get("headRefName", "")).startswith(AUTO_AG_ELOTAG)
    )


def fo_ag_verzioja(*, futtato: Runner = _valodi_futtato) -> str | None:
    """Az `origin/main` `pyproject.toml`-jának verziója; `None`, ha nem megy.

    ⚠️ Szándékosan NEM a munkafa fájlját olvassa: a futás a SAJÁT — akár
    percekkel korábbi — commitját nézi, épp ez a versenyhelyzet forrása."""
    if futtato(["git", "fetch", "--quiet", "origin", "main"]).returncode != 0:
        return None
    eredmeny = futtato(["git", "show", "origin/main:pyproject.toml"])
    if eredmeny.returncode != 0:
        return None
    try:
        return verzio_a_szovegbol(eredmeny.stdout or "", forras="az origin/main pyproject.toml-ja")
    except ValueError:
        return None


def van_e_kiadas(cel: str, repo: str, *, futtato: Runner = _valodi_futtato) -> bool:
    """Létezik-e már a `v<cel>` kiadás."""
    return futtato(["gh", "release", "view", f"v{cel}", "--repo", repo]).returncode == 0


def main(argv: Sequence[str] | None = None, *, futtato: Runner = _valodi_futtato) -> int:
    ertelmezo = argparse.ArgumentParser(description="Nyitható-e verzióemelő PR?")
    ertelmezo.add_argument("--repo", required=True, help="tulajdonos/repó")
    ertelmezo.add_argument("--cel", required=True, help="a tervezett új verzió")
    beallitas = ertelmezo.parse_args(list(argv) if argv is not None else None)

    szabad, indok = dontes(
        beallitas.cel,
        nyitott_agak=nyitott_auto_agak(beallitas.repo, futtato=futtato),
        fo_verzio=fo_ag_verzioja(futtato=futtato),
        van_kiadas=van_e_kiadas(beallitas.cel, beallitas.repo, futtato=futtato),
    )

    # Az ELSŐ sor a válasz — erre támaszkodik a `release.yml`. Utána ember
    # számára olvasható indoklás megy, hogy a döntés utólag is látszódjon.
    print("igen" if szabad else "nem")
    print(indok)
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
