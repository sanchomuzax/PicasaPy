#!/usr/bin/env python3
"""PR-kapu — Claude Code PreToolUse hook (agent-#92).

## Ket szabaly, amelyiknek eddig nem volt kapuja

**1. A PR nevezzen meg jegyet.** A szabalykonyv: ha a munka commitot er,
akkor jegyet is er — elobb nyisd meg, es a repotol KAPOTT szamot hasznald.
Mero VAN a kitalalt jegyszamra, de semmi nem ellenorizte, hogy a PR
egyaltalan megnevez-e egyet. 2026-09-17-en ket PR jegy nelkul nyilt; csak a
tulajdonos kerdesere lett jegye.

**2. Az alairas tiltott.** A globalis szabaly szerint az attribucio ki van
kapcsolva, es a PR szerzoje amugy is a bot — a lablec ugyanazt ismetli, amit
a szerzo mezo megmond.

## A torzs jellemzoen FAJLBOL jon

A projekt szabalya szerint a gh torzset mindig body-file-lal adjuk at (a
backtickes szoveget a shell kitorolne). A parancssorban tehat csak az UTVONAL
all — a kapunak a fajlt is el kell olvasnia. Enelkul minden valodi hivasra
vak lenne, es pont a szokasos alakot engedne at.

## Amit NEM fog

Olvasast (pr view, pr list, pr checks, pr diff) nem erint. A pr edit-et csak
akkor, ha a torzset irja at — cimkezesbe, alap-ag valtasba nem szol bele.

Minden hibaagon fail-open: egy elromlott kapu nem akaszthatja meg a munkat.
"""

import json
import os
import re
import shlex
import sys

#: Parancspozicio: sor eleje, shell-elvalaszto, vagy behelyettesites.
_POZICIO = r"(?:^\s*|[;&|(]\s*|\$\(\s*)(?:\w+=\S*\s+)*"

#: A GitHub-eszkoz minden irasmodja — a bot-burkolok is (eszkozonkent van
#: sajatjuk, es a kapunak MINDEGYIKRE hatnia kell).
_GH = r"(?:[\w./~-]*/)?(?:gh|gh-bot|codex-bot|opencode-bot|hermes-bot)"

_PR_CREATE = re.compile(_POZICIO + _GH + r"\s+pr\s+create\b")
_PR_EDIT = re.compile(_POZICIO + _GH + r"\s+pr\s+edit\b")

#: Jegyhivatkozas: #123 vagy owner/repo#123.
_JEGY = re.compile(r"(?:[\w.-]+/[\w.-]+)?#\d{1,6}\b")

#: A tiltott alairas — a szerzo mezo ugyanazt mondja.
_ALAIRAS = re.compile(r"Generated with \[?Claude Code|Generated with \[Claude")

_CIM = ("--title", "-t")
_TORZS = ("--body", "-b")
_FAJL = ("--body-file", "-F")

#: A torzs-fajl kapcsoloja es utana az utvonal, a NYERS parancsbol
#: (idezve vagy idezojel nelkul). Lasd a #3302-t.
_FAJL_MINTA = re.compile(
    r"(?:" + "|".join(re.escape(k) for k in _FAJL) + r")(?:=|\s+)"
    r"(?P<ut>'[^']*'|\"[^\"]*\"|\S+)")


def _szoveg(cmd: str):
    """A PR cime + torzse. None, ha a parancs nem PR-iras."""
    if not (_PR_CREATE.search(cmd) or _PR_EDIT.search(cmd)):
        return None
    try:
        tokenek = shlex.split(cmd)
    except ValueError:
        return None
    reszek = []
    ir_torzset = _PR_CREATE.search(cmd) is not None
    #: Ha egy megadott torzs-fajlt NEM tudtunk elolvasni, a kapu nem tudja,
    #: mi van benne — ilyenkor atenged. A docstring fail-open-t igert, a
    #: kod viszont blokkolt volna: a probaba beirt kontroll fogta meg.
    olvashatatlan = False
    for i, t in enumerate(tokenek):
        kov = tokenek[i + 1] if i + 1 < len(tokenek) else ""
        if t in _CIM or t in _TORZS:
            reszek.append(kov)
            if t in _TORZS:
                ir_torzset = True
        elif any(t.startswith(k + "=") for k in _CIM + _TORZS):
            kulcs, _, ertek = t.partition("=")
            reszek.append(ertek)
            if kulcs in _TORZS:
                ir_torzset = True
    # #3302: a torzs-fajl utvonalat a NYERS parancsbol olvassuk ki, nem a
    # `shlex` tokenjeibol. A `shlex` POSIX-modban a `\`-t escape-nek veszi,
    # tehat egy windowsos utvonalbol (`C:\Users\...`) eltunnek a
    # valasztojelek: a kapu nem letezo fajlt nyitna, az "olvashatatlan ->
    # atenged" agra futna, es a VALODI elkovetot is atengedne. Merve: harom
    # proba `None`-t kapott ott, ahol blokkolast var.
    for talalat in _FAJL_MINTA.finditer(cmd):
        ut = talalat.group("ut").strip("'\"")
        ir_torzset = True
        try:
            # `errors="replace"`: a tartalmat csak jegyszamra es alairasra
            # nezzuk, tehat egy rossz bajt nem indokolja, hogy a kapu
            # atengedjen. Korabban a rendszer kodlapja UnicodeDecodeError-t
            # adott, es a kapu nemen fail-open lett.
            with open(os.path.expanduser(ut), encoding="utf-8",
                      errors="replace") as f:
                reszek.append(f.read())
        except OSError:
            olvashatatlan = True
    if olvashatatlan:
        return None
    return "\n".join(reszek) if ir_torzset else None


_SEGITSEG = """
A szabaly: ha a munka commitot er, akkor jegyet is er — ELOBB nyisd meg, es a
repotol KAPOTT szamot hasznald. A jegyszam a commit-uzenet es a PR
legtartosabb szovege.

Gepezet-jegy a PRIVAT repoba megy; a PR akkor is hivatkozhat ra:
sanchomuzax/picasapy-agent#92
"""

_ALAIRAS_SEGITSEG = """
A PR szerzoje mar a bot — a lablec ugyanazt ismetli, amit a szerzo mezo
megmond, es a globalis szabaly szerint az attribucio ki van kapcsolva.
Hagyd el a sort.
"""


def blokkolando(cmd: str):
    """A blokkolas indoka, vagy None."""
    szoveg = _szoveg(cmd)
    if szoveg is None:
        return None
    if _ALAIRAS.search(szoveg):
        return "a PR torzseben ott az attribucios lablec" + _ALAIRAS_SEGITSEG
    if not _JEGY.search(szoveg):
        return ("a PR nem nevez meg jegyet (se a cimben, se a torzsben)"
                + _SEGITSEG)
    return None


def main() -> int:
    try:
        adat = json.load(sys.stdin)
        cmd = (adat.get("tool_input") or {}).get("command") or ""
    except Exception:
        return 0  # fail-open: rossz bemenet nem blokkolhat
    try:
        indok = blokkolando(cmd)
    except Exception:
        return 0  # fail-open: elromlott kapu nem akaszthat meg munkat
    if indok is None:
        return 0
    sys.stderr.write("[PR-kapu] BLOKKOLVA: " + indok)
    return 2


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
