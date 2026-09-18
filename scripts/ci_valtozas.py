#!/usr/bin/env python3
"""A CI változás-elemzése: lefut-e a tesztmátrix? (#3298)

A döntés korábban a munkafolyamat YAML-jében élt, beágyazott shellként,
próba nélkül — pedig épp ő dönti el, hogy a kód kap-e egyáltalán mérést.
Ha téved, a hiba NÉMA és fordított irányú: nem piros CI lesz belőle, hanem
kimaradt tesztfutás, zöld pipával.

Bemenet (környezeti változók, a GitHub eseményéből):

    BASE / HEAD     a `pull_request` base- és head-SHA-ja (pushnál üres)
    ELOZO / MOSTANI `github.event.before` és `github.sha` (push esetén)

Kimenet a `GITHUB_OUTPUT`-ba: `kod=true|false` és `docs=true|false`.

⚠️ NEM MÉRI (kimondott korlátok — ld. a `NEM_MERT` állandót):
a nem szöveges (bináris) ütközéseket, az átnevezéseket tartalom szerint,
és az almodulok mozgását. Mindhárom a fájlNÉV listáján keresztül látszik
csak; ha egy ilyen változás kódot érint, azt a fájlnév-szűrő fogja meg,
nem a tartalom-vizsgálat.
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from dataclasses import dataclass

NEM_MERT = (
    "A döntés a fájlNEVEK listáján és két fájl soronkénti diffjén alapul. "
    "NEM méri: a bináris ütközéseket (a diff szövegsorai üresek lehetnek), "
    "az átnevezéseket tartalom szerint (mindkét út külön fájlként számít), "
    "és az almodul-mutatók mozgását (csak a `gitlink` útja látszik). "
    "Mindhárom esetben a fájlnév-szűrő dönt, és az a teljes kör felé téved."
)

NULLA_SHA = "0" * 40

# Nem érinti a kód futását: bármilyen .md és a docs/ egésze.
# ⚠️ A .github/ SZÁNDÉKOSAN kód: ha a CI-t magát változtatjuk, a teljes
# mátrixnak le KELL futnia, különben egy elrontott munkafolyamat-definíció
# zölden beolvad.
DOKUMENTACIO = re.compile(r"^(.*\.md|docs/.*)$")

# A verzióemelés két fájlja csak akkor számít nem-kódnak, ha bennük CSAK a
# verziósor változott — kódot ezen az úton nem lehet becsempészni.
VERZIOFAJLOK = {
    "pyproject.toml": re.compile(r"^[+-]version = "),
    "src/picasapy/__init__.py": re.compile(r"^[+-]__version__ = "),
}


@dataclass(frozen=True)
class Dontes:
    """Az elemzés eredménye — új példány, sosem módosított."""

    kod: bool
    docs: bool
    valtozott: tuple[str, ...]
    erdemi: tuple[str, ...]
    indoklas: str


def _git(tarolo: str, *argumentumok: str) -> str:
    kesz = subprocess.run(
        ["git", "-C", tarolo, *argumentumok],
        capture_output=True, text=True, check=True,
        encoding="utf-8", errors="replace",
    )
    return kesz.stdout


def _van_kozos_elod(tarolo: str, alap: str, fej: str) -> str | None:
    try:
        kimenet = _git(tarolo, "merge-base", alap, fej).strip()
    except subprocess.CalledProcessError:
        return None
    return kimenet or None


def _csak_verziosor(tarolo: str, alap: str, fej: str, fajl: str,
                    minta: re.Pattern[str]) -> bool:
    """Igaz, ha a fájlban a verziósoron KÍVÜL semmi nem változott."""
    diff = _git(tarolo, "diff", "-U0", alap, fej, "--", fajl)
    for sor in diff.splitlines():
        if not sor or sor[0] not in "+-":
            continue
        if sor.startswith(("+++", "---")):
            continue
        if not minta.search(sor):
            return False
    return True


def elemezd(tarolo: str, alap_jelolt: str, fej: str) -> Dontes:
    """A döntés két SHA között. `alap_jelolt` a base-ág tipje lehet."""
    # #3288: az ELÁGAZÁS HELYÉHEZ kell mérni, nem a base-ág mai csúcsához.
    # A base.sha a PR élete alatt továbbmegy, és akkor a közben beolvadt
    # IDEGEN commitok fájljai is „a PR változásának" látszanak.
    kozos = _van_kozos_elod(tarolo, alap_jelolt, fej)
    if kozos:
        alap = kozos
        indoklas = f"Összevetés az elágazás helyétől ({alap})."
    else:
        # Fail-safe: sekély klón vagy átírt történet — inkább több mérés.
        return Dontes(
            kod=True, docs=False, valtozott=(), erdemi=(),
            indoklas="Nincs közös előd (sekély klón vagy átírt történet) — teljes kör.",
        )

    valtozott = tuple(
        s for s in _git(tarolo, "diff", "--name-only", alap, fej).splitlines() if s
    )
    maradek = [s for s in valtozott if not DOKUMENTACIO.match(s)]
    for fajl, minta in VERZIOFAJLOK.items():
        if fajl in maradek and _csak_verziosor(tarolo, alap, fej, fajl, minta):
            maradek = [s for s in maradek if s != fajl]

    # #1863: a `docs/` alatt TESZTADAT is van (105 lapot nyitnak meg az őrök),
    # ezért a mátrix ugyan kimarad, de a docs-ot olvasó őrök külön futnak.
    docs = any(s.startswith("docs/") for s in valtozott)
    return Dontes(
        kod=bool(maradek), docs=docs, valtozott=valtozott,
        erdemi=tuple(maradek), indoklas=indoklas,
    )


def _push_alap(tarolo: str, elozo: str, mostani: str) -> tuple[str, str] | None:
    """Push-eseménynél a `github.event.before` az előzmény."""
    if not elozo or elozo == NULLA_SHA:
        return None
    try:
        _git(tarolo, "cat-file", "-e", f"{elozo}^{{commit}}")
    except subprocess.CalledProcessError:
        return None
    return elozo, mostani


def main(ervek: list[str] | None = None) -> int:
    ertelmezo = argparse.ArgumentParser(description=__doc__)
    ertelmezo.add_argument("--tarolo", default=".", help="a git-munkafa útja")
    beallitas = ertelmezo.parse_args(ervek)
    tarolo = beallitas.tarolo

    alap = os.environ.get("BASE", "")
    fej = os.environ.get("HEAD", "")
    if not alap:
        # A `main`-en is ugyanaz a döntés szülessen, mint a PR-en: pushnál
        # nincs `pull_request.base`, de az eseménynek VAN előzménye.
        parban = _push_alap(
            tarolo, os.environ.get("ELOZO", ""), os.environ.get("MOSTANI", ""))
        if parban is None:
            print("Nincs használható előzmény (új ág vagy kézi indítás) — teljes kör.")
            _ird_ki(kod=True, docs=False)
            return 0
        alap, fej = parban
        print(f"push — összevetés az előző állapottal ({alap}).")

    dontes = elemezd(tarolo, alap, fej)
    print(dontes.indoklas)
    print("Változott fájlok:")
    for sor in dontes.valtozott:
        print(sor)
    if dontes.kod:
        print("A kód futását ÉRINTŐ fájlok:")
        for sor in dontes.erdemi:
            print(sor)
    else:
        print("Csak dokumentáció és/vagy verziósor — a mátrix kimarad.")
    _ird_ki(kod=dontes.kod, docs=dontes.docs)
    return 0


def _ird_ki(*, kod: bool, docs: bool) -> None:
    ut = os.environ.get("GITHUB_OUTPUT")
    sorok = f"kod={'true' if kod else 'false'}\ndocs={'true' if docs else 'false'}\n"
    if not ut:
        print(sorok, end="")
        return
    with open(ut, "a", encoding="utf-8") as kimenet:
        kimenet.write(sorok)


if __name__ == "__main__":
    sys.exit(main())
