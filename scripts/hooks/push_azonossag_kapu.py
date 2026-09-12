#!/usr/bin/env python3
"""Push-azonosság kapu — Claude Code PreToolUse hook (picasapy-agent#84).

## Miért

A GitHub idővonalán a **„X added N commits"** sor NEM a commit szerzőjét
nevezi meg, hanem azt, aki **feltolta** az ágat. A commit szerzője helyes
(`Claude <noreply@anthropic.com>`), a push viszont a gépen tárolt
HTTPS-hitelesítéssel megy — vagyis a TULAJDONOS fiókjával. Kívülről ezért
úgy látszik, mintha ő commitolt volna a saját projektjébe.

> „A nevemben ki a fasz kommitolgat??????"

A projekt szabálya nem kétértelmű: *GitHub-műveletet KIZÁRÓLAG a bot
azonosságával.* A push GitHub-művelet.

## Mérés (2026-09-12, a repók `events` folyama)

| repó | bot tolta | a tulajdonos fiókja tolta |
|---|---:|---:|
| `PicasaPy` | 10 | **11** |
| `picasapy-agent` | 1 | **63** |

⇒ Nem egyetlen kör baklövése: ez volt az ALAPÉRTELMEZETT út.

## ⛔ Amiért a burkoló önmagában kevés

A `eszkozok/git-push-bot` burkoló megvan, és mellé memória-jegyzet került.
De a szabálykönyvek **csak induláskor** töltődnek be, a tulajdonos pedig
napokig élő munkameneteket futtat — azok jóhiszeműen tolnak tovább a régi
módon. A projekt saját szabálya szerint a garancia a KAPU, nem az üzenet.

## Amit ez az őr csinál

Megállítja a csupasz `git push`-t, és kiírja a helyes parancsot.

⚠️ **A `git push` MINDEN alakját fogja**, nem csak a csupasz szót. Ez a
hibaosztály a projektben már kétszer megharapott: a kiadás-kapu a
`git -C <út>` alakon csúszott el, a jegycím-őr pedig azon, hogy csak a
csupasz `gh`-t ismerte. Ezért itt a globális git-kapcsolók (`-C`, `-c`,
`--git-dir`, `--work-tree`, `--namespace`) átugrása kifejezett.

Minden hibaágon átenged (fail-open): egy elromlott kapu nem akaszthatja meg
a párhuzamos munkameneteket.
"""

import json
import os
import re
import sys

#: Idezet-szakaszok — kivagjuk, mielott parancsot keresnenk (#3105). Enelkul
#: egy jegytorzs vagy dokumentum, amiben a tiltott parancs SZOVEGKENT
#: szerepel, sajat magat blokkolja. Elesben pontosan ez tortent: a kaput
#: leiro jegy megnyitasat akadalyozta meg a kapu.
_IDEZET = re.compile(r"'[^']*'|\"[^\"]*\"|`[^`]*`")

#: A projekt repoi. A kapu MAS projektben nema — a felhasznalo gepen tobb
#: repo el, es a bot GitHub Appja csak ezekre van telepitve, tehat mashol a
#: javasolt burkolo sem jarhato ut.
_HATOKOR = ("picasapy", "PicasaPy")

#: A parancsban megnevezett munkakonyvtar: `cd X` vagy `-C X`. A `cwd`
#: onmagaban felrevisz: `cd <masik repo>` utan a munkamenet cwd-je meg a
#: mienk, a muvelet viszont mashova megy.
_UTVONAL = re.compile(
    r"(?:^|[;&|]\s*|\n\s*)cd\s+(\S+)|(?:^|\s)-C[=\s]+(\S+)")


def megnevezett_utvonalak(cmd: str) -> list[str]:
    """A parancsban kimondott konyvtarak, sorrendben."""
    return [(a or b) for a, b in _UTVONAL.findall(cmd) if (a or b)]


def hatokorben(cmd: str, cwd: str = "") -> bool:
    """A projekt repoit erinti-e a parancs?"""
    utak = megnevezett_utvonalak(cmd)
    if utak:
        return any(j in u for u in utak for j in _HATOKOR)
    return any(j in (cwd or "") for j in _HATOKOR)


#: Parancspozíció: sor eleje vagy shell-elválasztó után, esetleges
#: környezeti előtagokkal. Enélkül a parancs SZÖVEGÉBEN szereplő említés is
#: kiváltaná a kaput — ez a hibaosztály a kiadás-kaput élesben megvezette.
_POZICIO = r"(?:^|[;&|]\s*|\n\s*|\$\(\s*|`\s*)(?:\w+=\S*\s+)*"

#: A git GLOBÁLIS kapcsolói, amelyek az alparancs ELÉ kerülnek. A
#: `git -C ~/repo push` alak miatt kell: enélkül a kapu pont a
#: worktree-s munkát engedné át, ami a leggyakoribb alak.
_GLOBALIS = (
    r"(?:(?:-C|-c|--git-dir|--work-tree|--namespace)(?:=\S+|\s+\S+)\s+"
    r"|--\S+\s+)*"
)

#: `git [globális…] push`, bárhonnan hívva (`git`, `/usr/bin/git`).
_GIT_PUSH = re.compile(_POZICIO + r"(?:[\w./~-]*/)?git\s+" + _GLOBALIS + r"push\b")

#: A burkoló MINDEN írásmódja: útvonallal vagy anélkül.
_BURKOLO = re.compile(r"(?:^|[\s;&|/])git-push-bot\b")

#: Ha a parancs maga állítja be a bot azonosságát (a burkoló belsejében, vagy
#: egy tudatosan megírt egyedi push), az rendben van.
_BOT_AZONOSSAG = re.compile(r"x-access-token|gh_bot_token\.py")


def blokkolando(cmd: str, cwd: str = "") -> bool:
    """Csupasz feltoltes a projekt repojaba, NEM a bot azonossagaval?"""
    if not hatokorben(cmd, cwd):
        return False
    if _BURKOLO.search(cmd) or _BOT_AZONOSSAG.search(cmd):
        return False
    #: Az idezeteket a burkolo-vizsgalat UTAN vagjuk ki: a helyes
    #: parancs utvonala is allhat idezojelben.
    return bool(_GIT_PUSH.search(_IDEZET.sub(" ", cmd)))


_SEGITSEG = """
A GitHub idővonalán az „X added N commits" sort a PUSH gazdája adja, nem a
commit szerzője. Tárolt HTTPS-hitelesítéssel tolva ott a TULAJDONOS neve
jelenik meg a gépi munkán — ő ezt többször kikérte magának.

Helyette:

  ~/picasapy-agent/eszkozok/git-push-bot <munkafa> <ág>
  ~/picasapy-agent/eszkozok/git-push-bot <munkafa> <ág> --force

Például a jelenlegi munkafa main-ágára:

  ~/picasapy-agent/eszkozok/git-push-bot . main

Mindkét repóra érvényes — a publikusra és a privátra is. A vegyes használat
rosszabb, mint a következetes tévedés: abból nem látszik, melyik a szabály.
"""


def main() -> int:
    try:
        adat = json.load(sys.stdin)
        cmd = (adat.get("tool_input") or {}).get("command") or ""
        cwd = adat.get("cwd") or os.getcwd()
    except Exception:
        return 0  # fail-open: rossz bemenet nem blokkolhat
    try:
        fogva = blokkolando(cmd, cwd)
    except Exception:
        return 0  # fail-open: elromlott kapu nem akaszthat meg munkát
    if not fogva:
        return 0
    sys.stderr.write(
        "[Push-azonosság kapu] BLOKKOLVA: a csupasz `git push` a TULAJDONOS "
        "fiókjával tolna.\n" + _SEGITSEG
    )
    return 2


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
