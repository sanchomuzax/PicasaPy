#!/usr/bin/env python3
"""Kiadás-kapu — Claude Code PreToolUse hook.

Blokkolja a visszavonhatatlan kiadási lépéseket (GitHub release, tag
létrehozása, tag push), hogy sub-agent vagy elhamarkodott session ne adhasson
ki verziót a kiadási ceremónia (review -> zöld CI -> integrátor) előtt.

A feloldó jelölőt szándékosan NEM ez a fájl dokumentálja: a privát
picasapy-agent repó munkafolyamat-lapján van, és csak az integrátor session
használhatja. Ez nem titkosítás, hanem szándékossági küszöb — a kapu a
jóhiszemű "zöld a teszt, kiadom" reflexet fogja meg, nem a rosszindulatot.

Minden hibaágon átenged (fail-open): egy elromlott kapu nem foghatja meg a
párhuzamos sessionök normál munkáját.
"""

import json
import re
import sys

FELOLDO = "PICASA_KIADAS=engedelyezve"

# Csak listázó/olvasó/törlő git tag alakok — ezek nem kiadási lépések.
_TAG_ARTALMATLAN = re.compile(
    r"git\s+tag(\s+(-l\b|--list\b|-d\b|--delete\b|-v\b|--verify\b"
    r"|--contains\b|--points-at\b|--merged\b|--no-merged\b)|\s*$)"
)


def _blokkolando(cmd: str) -> str | None:
    """A parancs kiadási lépés-e; ha igen, rövid indok, ha nem, None."""
    if FELOLDO in cmd:
        return None
    if re.search(r"\bgh\s+release\s+(create|edit|upload)\b", cmd):
        return "GitHub release létrehozása/módosítása"
    if re.search(r"\bgit\s+tag\b", cmd) and not _TAG_ARTALMATLAN.search(cmd):
        return "git tag létrehozása"
    if re.search(r"\bgit\s+push\b", cmd) and re.search(
        r"(--tags\b|--follow-tags\b|refs/tags/|\sv\d+[.\w]*(\s|$))", cmd
    ):
        return "tag push (kiadás publikálása)"
    return None


def main() -> int:
    try:
        adat = json.load(sys.stdin)
        cmd = (adat.get("tool_input") or {}).get("command") or ""
    except Exception:
        return 0  # fail-open: rossz bemenet nem blokkolhat
    indok = _blokkolando(cmd)
    if indok is None:
        return 0
    sys.stderr.write(
        "[Kiadás-kapu] BLOKKOLVA: " + indok + ".\n"
        "A kiadás visszavonhatatlan, ezért csak az integrátor session adhatja\n"
        "ki, a teljes ceremónia után (code review -> zöld CI -> éles próba).\n"
        "Ha sub-agent vagy: ÁLLJ LE, és jelentsd a hívónak, hogy a munkád\n"
        "kiadásra kész — a kiadásról a hívó dönt.\n"
        "Ha integrátor vagy és a ceremónia megvolt: a feloldó jelölő a privát\n"
        "picasapy-agent repó memory/munkafolyamat.md kiadási szakaszában van.\n"
    )
    return 2


if __name__ == "__main__":
    sys.exit(main())
