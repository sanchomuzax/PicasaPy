#!/usr/bin/env python3
"""Basetemp-kapu — Claude Code PreToolUse hook (#1649).

**A hibaosztály.** A `PROTOKOLL.md` kimondja, hogy a tesztfuttató a
`scripts/run_tests.py`, vagy fájlonkénti futtatásnál KÖZÖS `--basetemp` kell
(a pytest a „tartsd meg az utolsó hármat" takarítást basetemp-enként végzi,
tehát minden külön basetemp hagy maga után egy könyvtárat).

Ez a szabály **le volt írva, és mégis megsérült**: 2026-08-15-én öt párhuzamos
kör csupasz `python3 -m pytest`-tel **5,8 GB**-ot hagyott a `pytest-of-sancho`
alatt, és a 8 GB-os tmpfs 85%-ra telt. A kár nem a vétkes körnél jelentkezik,
hanem a **párhuzamosan futó** munkameneteknél, némán, félrevezető `ENOSPC`-vel.

**Miért hook, és nem több szöveg.** Mert a szöveget már kipróbáltuk. A
`release_kapu.py` ugyanezt a mintát követi, és bevált: a kiadás-tilalom azért
nem jelenik meg az agent-briefekben, mert **nem is kell** — ki van véve a
promptból, kódba.

**Vaklárma-osztályok, amiket a `release_kapu` élesben tanult (2026-08-19), és
itt előre kivédünk:**

1. a parancs SZÖVEGÉBEN előforduló említés (`grep`, fájlírás) nem blokkolhat —
   ezért az idézett szakaszokat kivágjuk az elemzés előtt;
2. a listázó/segítség-alakok nem hoznak létre tmpdir-t (`--help`, `--version`,
   `--collect-only`), tehát átmennek.

Minden hibaágon **fail-open**: egy elromlott kapu nem foghatja meg a
párhuzamos munkameneteket — épp azokat védené.
"""

from __future__ import annotations

import json
import re
import sys

#: Idézett szakaszok — ezeket kivágjuk, mielőtt parancsot keresnénk benne.
_IDEZET = re.compile(r"'[^']*'|\"[^\"]*\"")

#: Szakaszhatárok: külön parancsnak számít mindegyik oldal.
_HATAR = re.compile(r"&&|\|\||[;|]")

#: `VAR=ertek` alakú előtag a parancs elején.
_ERTEKADAS = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=")

#: Burkoló programok, amik után a VALÓDI parancs jön.
_BURKOLO = {"env", "nice", "xvfb-run", "stdbuf", "time"}

#: Python-értelmezők, amikkel a `-m pytest` alak indul.
_PYTHON = re.compile(r"^(.*/)?python[0-9.]*$")

#: Ezek az alakok nem hoznak létre ideiglenes könyvtárat.
_ARTALMATLAN_KAPCSOLO = {"-h", "--help", "--version", "--collect-only", "--co"}


def _szakaszok(cmd: str) -> list[list[str]]:
    """A parancs szakaszai tokenekre bontva, idézetek nélkül."""
    tiszta = _IDEZET.sub(" ", cmd)
    return [r.split() for r in _HATAR.split(tiszta) if r.split()]


def _fej(tokenek: list[str]) -> list[str]:
    """A tokenlista az értékadások és burkolók levágása után."""
    i = 0
    while i < len(tokenek):
        t = tokenek[i]
        if _ERTEKADAS.match(t) or t in _BURKOLO:
            i += 1
            continue
        if t == "timeout":
            i += 1
            # a timeout első argumentuma az időkorlát (pl. `timeout 60 …`)
            if i < len(tokenek) and re.fullmatch(r"[0-9]+[smhd]?", tokenek[i]):
                i += 1
            continue
        break
    return tokenek[i:]


def _pytest_hivas(tokenek: list[str]) -> bool:
    """Igaz, ha ez a szakasz TÉNYLEGESEN pytestet indít."""
    t = _fej(tokenek)
    if not t:
        return False
    fej = t[0]
    if fej == "pytest" or fej.endswith("/pytest"):
        return True
    # `python -m pytest …` — a `-m pytest` közvetlenül az értelmező után áll
    return bool(_PYTHON.match(fej)) and t[1:3] == ["-m", "pytest"]


def blokkolando(cmd: str) -> str | None:
    """Az indok, ha a parancsot blokkolni kell — különben None."""
    for tokenek in _szakaszok(cmd):
        if not _pytest_hivas(tokenek):
            continue
        if any(k in _ARTALMATLAN_KAPCSOLO for k in tokenek):
            continue
        if any(k == "--basetemp" or k.startswith("--basetemp=") for k in tokenek):
            continue
        return "pytest-hívás közös `--basetemp` nélkül"
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
        return 0  # fail-open: elromlott kapu nem akaszthat meg munkát
    if indok is None:
        return 0
    sys.stderr.write(
        "[Basetemp-kapu] BLOKKOLVA: " + indok + ".\n"
        "\n"
        "Használd a projekt futtatóját:\n"
        "    python scripts/run_tests.py\n"
        "\n"
        "Vagy ha tényleg fájlonként futtatsz, adj KÖZÖS basetempet:\n"
        "    BT=\"$SCRATCH/bt\"; mkdir -p \"$BT\"\n"
        "    python3 -m pytest <fájl> -q --basetemp=\"$BT\"\n"
        "\n"
        "Miért: a pytest a „tartsd meg az utolsó hármat\" takarítást\n"
        "basetemp-enként végzi. Külön basetemppel minden részfutás hagy egy\n"
        "könyvtárat. 2026-08-15-én öt párhuzamos kör így 5,8 GB-ot hagyott a\n"
        "tmpfs-en. A kár NEM nálad jelentkezik, hanem a párhuzamosan futó\n"
        "munkameneteknél, némán — ezért kapu ez, és nem ajánlás.\n"
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
