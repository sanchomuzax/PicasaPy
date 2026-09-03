#!/usr/bin/env python3
"""Kiadási őr — a félbemaradt automatika utáni rendrakás (#1319).

## Miért

A #1318 nem attól lett baj, hogy egy verzióemelő PR létrejött, hanem attól,
hogy utána nem volt, aki elrendezze. A GitHub a saját tokenjével nyitott
PR-en SZÁNDÉKOSAN nem indít workflow-t (#1190) — ez nem kapcsolható ki —,
így a kötelező ellenőrzés sosem futott le, az auto-merge sosem sült el, és a
PR némán ott ült. Észrevenni egy figyelmes műszak dolga volt.

Ez a szkript ütemezetten végigmegy az automatika saját PR-jein, és
visszaállítja a repót „nincs nyitott automatikus teendő" állapotba:

* elindítja a hiányzó ellenőrzést (`gh workflow run` — ez a bizonyítottan
  működő út: a v0.8.69 is így ment be);
* lezárja az elavult vagy fölöslegessé vált automatikus PR-eket;
* újraélesíti a leesett auto-merge-öt;
* pótolja a hiányzó kiadást;
* és ha valamelyik lépés elbukik, **jól látható issue-t nyit** — a néma
  bukás pontosan az a hiba, amit orvosolni akarunk.

## Hatókör — ez a legfontosabb szabály

Az őr KIZÁRÓLAG a saját automatika-ágaihoz nyúl (`chore/auto-bump-*`).
Emberi PR-t soha nem zár le, nem indít rajta semmit. Egy őr, ami emberi
munkába nyúlhat, többet ront, mint amennyit ment; van rá bukó teszt
(`test_emberi_pr_hoz_SOHA_nem_nyul`).
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from ensure_release import olvasott_verzio  # noqa: E402
from kiadas_szukseges import kiadasra_erdemes, valtozott_fajlok  # noqa: E402

Runner = Callable[[list[str]], "subprocess.CompletedProcess[str]"]

#: Az automatika saját ágainak előtagja. Az őr hatóköre EZ, semmi más.
AUTO_AG_ELOTAG = "chore/auto-bump-"

#: A `main` kötelező ellenőrzésének neve. Ha ez a fejen nincs meg, a PR
#: beolvadni sem tud — ilyenkor kell kézzel elindítani a CI-t.
KOTELEZO_ELLENORZES = "Test (ubuntu-latest)"

#: A hibajelző issue címkéje — ebből látszik a listában, hogy gépi lelet.
HIBA_CIMKE = "automatika"


@dataclass(frozen=True)
class Teendo:
    """Egy elvégzendő lépés. A `pr` a kiadáspótlásnál 0."""

    fajta: str  # "zaras" | "ci" | "automerge" | "kiadas"
    pr: int
    ag: str
    indok: str


def _valodi_gh(args: list[str]) -> subprocess.CompletedProcess[str]:
    # #2077: `errors="replace"` — a `git diff` kimenete NEM feltétlenül
    # érvényes UTF-8 (idegen kódolású fájl, bináris darab). Enélkül az
    # őr a DEKÓDOLÁSON hal meg, nem a leleten, és a CI úgy pirosodik,
    # hogy közben semmi baj nincs a vizsgált tartalommal.
    return subprocess.run(
        args, capture_output=True, text=True, encoding="utf-8", errors="replace", check=False
    )


def verzio_az_agbol(ag: str) -> tuple[int, ...] | None:
    """A `chore/auto-bump-0.8.70` ágból a (0, 8, 70) rendezhető alak.

    `None`, ha az ág nem az automatikáé, vagy nem SemVer-alakú a vége — az
    ilyen ághoz az őr HOZZÁ SEM NYÚL."""
    if not ag.startswith(AUTO_AG_ELOTAG):
        return None
    darabok = ag[len(AUTO_AG_ELOTAG) :].split(".")
    if len(darabok) != 3 or not all(d.isdigit() for d in darabok):
        return None
    return tuple(int(d) for d in darabok)


def _verzio_rendezheto(verzio: str) -> tuple[int, ...]:
    darabok = verzio.strip().split(".")
    return tuple(int(d) if d.isdigit() else 0 for d in darabok)


def teendok(
    prek: Iterable[dict],
    *,
    kiadott_verziok: set[str],
    fo_verzio: str,
    indokolt: bool = True,
) -> tuple[Teendo, ...]:
    """Mit kell tenni a nyitott PR-ekkel? — tiszta függvény, mérhető.

    A `prek` elemei: `szam`, `ag`, `automerge` (él-e), `van_ellenorzes`
    (van-e a fejen kötelező ellenőrzés).

    Az `indokolt` azt mondja meg, hogy az utolsó kiadás óta VAN-E egyáltalán
    kiadandó változás. Ha nincs, a PR nem elavult, hanem FÖLÖSLEGES — ez a
    #1324: a #1322 még a régi, feltétel nélküli automatikával született, és
    az őr kis híján kiadatott vele egy olyan verziót, amiben a felhasználó
    számára semmi nem változott."""
    jeloltek = [(p, verzio_az_agbol(p["ag"])) for p in prek]
    jeloltek = [(p, v) for p, v in jeloltek if v is not None]
    if not jeloltek:
        return ()

    legujabb = max(v for _, v in jeloltek)
    legujabb_szam = next(p["szam"] for p, v in jeloltek if v == legujabb)
    fo = _verzio_rendezheto(fo_verzio)

    lista: list[Teendo] = []
    for pr, verzio in jeloltek:
        cimke = ".".join(str(d) for d in verzio)
        if cimke in kiadott_verziok:
            lista.append(Teendo("zaras", pr["szam"], pr["ag"],
                                f"a v{cimke} kiadás már megvan"))
        elif verzio <= fo:
            lista.append(Teendo("zaras", pr["szam"], pr["ag"],
                                f"a main már a {fo_verzio} verziónál tart"))
        elif verzio < legujabb:
            lista.append(Teendo("zaras", pr["szam"], pr["ag"],
                                f"újabb verzióemelő PR van: #{legujabb_szam}"))
        elif not indokolt:
            lista.append(Teendo("zaras", pr["szam"], pr["ag"],
                                f"a v{fo_verzio} óta nincs kiadandó változás"))
        else:
            if not pr.get("van_ellenorzes"):
                lista.append(Teendo("ci", pr["szam"], pr["ag"],
                                    "a fejen nincs kötelező ellenőrzés (#1190)"))
            if not pr.get("automerge"):
                lista.append(Teendo("automerge", pr["szam"], pr["ag"],
                                    "az auto-merge nem él"))
    return tuple(lista)


def indokolt_e_az_emeles(fo_verzio: str, *, runner: Runner = _valodi_gh) -> bool:
    """Van-e egyáltalán kiadandó változás az utolsó kiadás óta?

    Ugyanaz a döntés, amit a `release.yml` a PR NYITÁSAKOR meghoz — csak itt
    utólag, a már nyitott PR-re. A kettő szándékosan ugyanaz a szkript: két
    külön szabály előbb-utóbb elcsúszna egymástól.

    ⚠️ Ha nem tudunk mérni (hiányzó címke, sekély klón), INDOKOLTNAK vesszük:
    lezárni csak biztos tudás alapján szabad, a kiadás elmaradása drágább."""
    fajlok = valtozott_fajlok(f"v{fo_verzio}", "HEAD", runner=runner)
    return kiadasra_erdemes(fajlok)


def kiadas_teendo(fo_verzio: str, kiadott_verziok: set[str]) -> Teendo | None:
    """A main verziójához hiányzó kiadás pótlása.

    A `release.yml` napi őrfutása is ezt nézi; itt negyedóránként ér célba,
    tehát a Releases hasáb nem tud fél napot lemaradni."""
    if fo_verzio in kiadott_verziok:
        return None
    return Teendo("kiadas", 0, "main", f"a v{fo_verzio} kiadás hiányzik")


def vegrehajt(
    lista: Sequence[Teendo], *, repo: str, runner: Runner = _valodi_gh
) -> tuple[Teendo, ...]:
    """A teendők elvégzése; a BUKOTTAK listáját adja vissza.

    ⚠️ Egy bukó lépés nem akaszthatja meg a többit: a #1318-ban pont az volt
    a baj, hogy egyetlen elmaradt lépés után minden más is állt."""
    bukott: list[Teendo] = []
    for teendo in lista:
        print(f"[{teendo.fajta}] #{teendo.pr or '-'} ({teendo.ag}): {teendo.indok}")
        parancsok: list[list[str]] = []
        if teendo.fajta == "zaras":
            parancsok.append([
                "gh", "pr", "comment", str(teendo.pr), "--repo", repo,
                "--body", f"A kiadási őr lezárja: {teendo.indok} (#1319).",
            ])
            parancsok.append([
                "gh", "pr", "close", str(teendo.pr), "--repo", repo, "--delete-branch",
            ])
        elif teendo.fajta == "ci":
            parancsok.append([
                "gh", "workflow", "run", "ci.yml", "--repo", repo, "--ref", teendo.ag,
            ])
        elif teendo.fajta == "automerge":
            parancsok.append([
                "gh", "pr", "merge", str(teendo.pr), "--repo", repo,
                "--auto", "--squash", "--delete-branch",
            ])
        elif teendo.fajta == "kiadas":
            parancsok.append([
                "gh", "workflow", "run", "release.yml", "--repo", repo, "--ref", "main",
            ])

        for parancs in parancsok:
            eredmeny = runner(parancs)
            if eredmeny.returncode != 0:
                print(f"  bukott: {(eredmeny.stderr or eredmeny.stdout or '').strip()[:200]}")
                bukott.append(teendo)
                break
    return tuple(bukott)


def jelents_hibat(cim: str, torzs: str, *, repo: str, runner: Runner = _valodi_gh) -> None:
    """Hibáról issue — de UGYANARRÓL csak egyszer.

    Negyedóránként futó őr issue-áradatot csinálna; a duplikátum-szűrés
    nélkül a jelzés maga válna zajjá, és pont azt veszítenénk el, amiért az
    egész készült: a láthatóságot."""
    meglevo = runner([
        "gh", "issue", "list", "--repo", repo, "--state", "open",
        "--search", cim, "--json", "number,title",
    ])
    if meglevo.returncode == 0:
        try:
            talalatok = json.loads(meglevo.stdout or "[]")
        except json.JSONDecodeError:
            talalatok = []
        if any(t.get("title") == cim for t in talalatok):
            print(f"Erről már van nyitott issue: {cim}")
            return
    runner([
        "gh", "issue", "create", "--repo", repo,
        "--title", cim, "--body", torzs, "--label", HIBA_CIMKE,
    ])


# --- a repó ÁLLAPOTÁNAK lekérdezése ---------------------------------------


def nyitott_auto_prek(*, repo: str, runner: Runner = _valodi_gh) -> list[dict]:
    """A nyitott verzióemelő PR-ek — ellenőrzés- és auto-merge-állapottal."""
    lista = runner([
        "gh", "pr", "list", "--repo", repo, "--state", "open", "--limit", "50",
        "--json", "number,headRefName,headRefOid,autoMergeRequest",
    ])
    if lista.returncode != 0:
        raise RuntimeError(f"A PR-lista lekérdezése bukott: {(lista.stderr or '').strip()}")
    prek = []
    for nyers in json.loads(lista.stdout or "[]"):
        ag = nyers.get("headRefName", "")
        if verzio_az_agbol(ag) is None:
            continue
        prek.append({
            "szam": nyers["number"],
            "ag": ag,
            "automerge": nyers.get("autoMergeRequest") is not None,
            "van_ellenorzes": van_kotelezo_ellenorzes(
                nyers.get("headRefOid", ""), repo=repo, runner=runner
            ),
        })
    return prek


def van_kotelezo_ellenorzes(sha: str, *, repo: str, runner: Runner = _valodi_gh) -> bool:
    """Fut-e (vagy futott-e) a kötelező ellenőrzés ezen a commiton?"""
    if not sha:
        return False
    valasz = runner([
        "gh", "api", f"repos/{repo}/commits/{sha}/check-runs",
        "--jq", "[.check_runs[].name]",
    ])
    if valasz.returncode != 0:
        # Bizonytalanságból nem indítunk fölösleges kört: a következő
        # negyedóra úgyis újra megkérdezi.
        return True
    try:
        nevek = json.loads(valasz.stdout or "[]")
    except json.JSONDecodeError:
        return True
    return KOTELEZO_ELLENORZES in nevek


def kiadott_verziok(*, repo: str, runner: Runner = _valodi_gh) -> set[str]:
    valasz = runner([
        "gh", "release", "list", "--repo", repo, "--limit", "30",
        "--json", "tagName", "--jq", ".[].tagName",
    ])
    if valasz.returncode != 0:
        raise RuntimeError(f"A kiadáslista lekérdezése bukott: {(valasz.stderr or '').strip()}")
    return {sor.strip().lstrip("v") for sor in (valasz.stdout or "").splitlines() if sor.strip()}


def main(argv: list[str] | None = None, *, runner: Runner = _valodi_gh) -> int:
    ertelmezo = argparse.ArgumentParser(description=__doc__)
    ertelmezo.add_argument("--repo", required=True, help="tulajdonos/repó")
    ertelmezo.add_argument("--szarazon", action="store_true",
                           help="csak kiírja, mit tenne")
    beallitas = ertelmezo.parse_args(argv)

    try:
        fo_verzio = olvasott_verzio()
        kiadott = kiadott_verziok(repo=beallitas.repo, runner=runner)
        prek = nyitott_auto_prek(repo=beallitas.repo, runner=runner)
    except (RuntimeError, json.JSONDecodeError, OSError) as hiba:
        print(f"::error::A kiadási őr nem tudta felmérni a repót: {hiba}")
        jelents_hibat(
            "A kiadási őr nem tudta felmérni a repót",
            f"A negyedórás őrfutás a lekérdezésnél bukott:\n\n```\n{hiba}\n```\n\n"
            f"Amíg ez áll, a verzióemelő PR-ek felügyelet nélkül maradnak (#1319).",
            repo=beallitas.repo,
            runner=runner,
        )
        return 1

    indokolt = indokolt_e_az_emeles(fo_verzio, runner=runner)
    lista = list(
        teendok(
            prek,
            kiadott_verziok=kiadott,
            fo_verzio=fo_verzio,
            indokolt=indokolt,
        )
    )
    kiadas = kiadas_teendo(fo_verzio, kiadott)
    if kiadas is not None:
        lista.append(kiadas)

    if not lista:
        print(f"Nincs nyitott automatikus teendő (main: {fo_verzio}).")
        return 0
    if beallitas.szarazon:
        for teendo in lista:
            print(f"[szárazon] {teendo}")
        return 0

    bukott = vegrehajt(lista, repo=beallitas.repo, runner=runner)
    if bukott:
        reszletek = "\n".join(f"- `{t.fajta}` #{t.pr} ({t.ag}): {t.indok}" for t in bukott)
        print("::error::A kiadási őr nem tudott mindent elrendezni.")
        jelents_hibat(
            "A kiadási őr nem tudta elrendezni az automatikus PR-eket",
            f"A negyedórás őrfutás az alábbi lépéseken bukott el:\n\n{reszletek}\n\n"
            f"Ezek EMBERI kézre várnak — amíg állnak, a kiadás nem megy tovább (#1319).",
            repo=beallitas.repo,
            runner=runner,
        )
        return 1
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
