#!/usr/bin/env python3
"""A felhasználót érintő PR hozzon CHANGELOG-bejegyzést (#1340).

## Miért

A v0.8.71 és a v0.8.72 ezzel a mondattal jelent meg a Releases hasábon:

    „Ez a kiadás nem hoz felhasználónak látszó változást."

Miközben az egyikben a letiltott gombok megjelenése javult (#893), a
másikban a lasszós kijelölés készült el (#897). A mondat HAZUDOTT — a
tulajdonos vette észre, és joggal háborodott fel: a Releases hasáb az ő
egyetlen látható verziókövetése.

Az ok: a kiadási jegyzet a CHANGELOG szakaszából készül, és egyik PR sem
írt bejegyzést, ezért a tartaléksablon ment ki. A szabály („a CHANGELOG
szövegét EMBER írja, a jegy PR-jében") le volt írva az `auto_bump.py`
fejlécében — de semmi nem őrizte.

## A mérce

Ugyanaz, mint a verzióemelésé (`kiadas_szukseges`): ami eljut a
felhasználóhoz, ahhoz mondat is jár. Két külön megfogalmazású szabály
előbb-utóbb elcsúszna egymástól.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from collections.abc import Callable, Iterable
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from kiadas_szukseges import kiadasra_erdemes  # noqa: E402

Runner = Callable[[list[str]], "subprocess.CompletedProcess[str]"]

#: A még ki nem adott munka szakasza — ide kell írni.
KIADATLAN_CIM = "## [Nem kiadott]"


def _valodi_git(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, capture_output=True, text=True, check=False)


#: A `pyproject.toml` verziósora — ezt az automatika írja át, nem ember.
_VERZIO_SOR = re.compile(r"^[+-]version\s*=")


def van_erdemi_valtozas(diff: str) -> bool:
    """Van-e a fájlban a VERZIÓSORON KÍVÜL is változás?

    ⚠️ Enélkül az őr a saját automatikánkat fogná meg: a verzióemelő PR a
    verziósort írja át és a CHANGELOG címét nevezi át, emberi mondatot pedig
    nem hoz — mert nem is neki kell. Ha ezt megfognánk, a verzióemelés soha
    nem tudna beolvadni, és a kiadás állna. Ugyanez a kivétel él a
    `ci.yml` változás-elemzésében is."""
    for sor in diff.splitlines():
        if not sor or sor[0] not in "+-" or sor.startswith(("+++", "---")):
            continue
        if not _VERZIO_SOR.match(sor):
            return True
    return False


def kell_bejegyzes(fajlok: Iterable[str]) -> bool:
    """Érinti-e a változás a felhasználót? Ugyanaz a mérce, mint a kiadásé."""
    return kiadasra_erdemes(list(fajlok))


def van_uj_bejegyzes(changelog_diff: str) -> bool:
    """Került-e ÚJ felsorolás-elem a naplóba?

    ⚠️ A szakaszcím átnevezése (`[Nem kiadott]` → `[0.8.71]`) NEM bejegyzés:
    azt a verzióemelő automatika végzi, emberi mondat nélkül. Ha ezt
    elfogadnánk, a kapu pont a hibás esetet engedné át."""
    for sor in changelog_diff.splitlines():
        if not sor.startswith("+") or sor.startswith("+++"):
            continue
        tartalom = sor[1:].strip()
        if tartalom.startswith(("- ", "* ")):
            return True
    return False


def van_kiadatlan_szakasz(changelog: str) -> bool:
    """Van-e egyáltalán hova írni? A hiányzó szakasz maga is hiba."""
    return KIADATLAN_CIM in changelog


def main(
    argv: list[str] | None = None,
    *,
    runner: Runner = _valodi_git,
) -> int:
    ertelmezo = argparse.ArgumentParser(description="Van-e CHANGELOG-bejegyzés?")
    ertelmezo.add_argument("--base", required=True)
    ertelmezo.add_argument("--head", required=True)
    ertelmezo.add_argument("--changelog", default=None)
    beallitas = ertelmezo.parse_args(argv)

    valtozott = runner(["git", "diff", "--name-only", beallitas.base, beallitas.head])
    if valtozott.returncode != 0:
        # ⚠️ A sikertelen mérésből SOHA nem lehet zöld út. Éles próbán jött
        # elő: hibás refekkel a diff elbukott, a fájllista üres lett, és az őr
        # „nincs mit ellenőrizni" címén átengedett. Ugyanaz a hibaosztály,
        # ami miatt ez a jegy megnyílt — csak eggyel feljebb.
        print(
            f"::error title=A CHANGELOG-őr nem tudott mérni::"
            f"A `git diff {beallitas.base} {beallitas.head}` elbukott: "
            f"{(valtozott.stderr or '').strip()[:200]}. Ellenőrzés nélkül nem "
            f"adunk zöld utat."
        )
        return 1
    fajlok = [s for s in (valtozott.stdout or "").splitlines() if s.strip()]

    erdemi = [f for f in fajlok if kell_bejegyzes([f])]
    if erdemi == ["pyproject.toml"]:
        pyproject_diff = runner([
            "git", "diff", beallitas.base, beallitas.head, "--", "pyproject.toml",
        ])
        if not van_erdemi_valtozas(pyproject_diff.stdout or ""):
            print("Csak a verziósor változott — ez az automatika saját PR-je.")
            return 0

    if not erdemi:
        print("A változás nem jut el a felhasználóhoz — nem kell CHANGELOG-bejegyzés.")
        return 0

    naplo_ut = Path(beallitas.changelog) if beallitas.changelog else (
        Path(__file__).resolve().parents[1] / "CHANGELOG.md"
    )
    try:
        naplo = naplo_ut.read_text(encoding="utf-8")
    except OSError:
        naplo = ""

    diff = runner([
        "git", "diff", beallitas.base, beallitas.head, "--", "CHANGELOG.md",
    ])
    if van_uj_bejegyzes(diff.stdout or ""):
        print("Van új CHANGELOG-bejegyzés — rendben.")
        return 0

    if not van_kiadatlan_szakasz(naplo):
        print(
            f"::error title=Hiányzik a CHANGELOG „Nem kiadott” szakasza::"
            f"A bejegyzésnek nincs hova kerülnie. Vedd fel a `{KIADATLAN_CIM}` "
            f"címet a CHANGELOG.md tetejére, és írd alá, mi változott."
        )
        return 1

    print(
        "::error title=Hiányzik a CHANGELOG-bejegyzés::"
        "Ez a PR a felhasználóhoz eljutó kódot módosít, de nem ír hozzá "
        "mondatot a CHANGELOG „Nem kiadott” szakaszába. Enélkül a kiadási "
        "jegyzet tartaléksablonra vált — a v0.8.71 és a v0.8.72 így állította "
        "magáról valótlanul, hogy nem hoz látható változást (#1340)."
    )
    print("A programot érintő fájlok:")
    for f in erdemi:
        print(f"  {f}")
    return 1


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
