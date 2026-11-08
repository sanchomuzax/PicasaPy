#!/usr/bin/env python3
"""Szálközi futás-kapu: Claude Code PreToolUse hook (picasapy-agent#308).

**A hibaosztály.** 2026-11-08 13:00 körül egy munkamenet helyben, teljes
tesztfutással (`run_tests.py --nightly-random-seed`) indította a véletlen
sorrendű mérést, miközben három Codex-szál, egy Claude-munkás és egy
ütemezett kör is futott. A négymagos gép terhelése 15 fölé ment, és a
tulajdonos újraindulásra gyanakodott.

A `run_tests.py` saját kapuja csak a teljes futások számát (legfeljebb 2) és a
szabad memóriát nézi; a futó szálakat és a terhelést nem. Ez a hook azt
állítja meg, amit az nem lát: a TELJES helyi futást, ha

1. fut legalább egy Codex-, Claude-munkás- vagy Gemini-szál (a folyamatlista
   szerint, ugyanazokkal a mintákkal, mint a szál-kihasználtság mérője), vagy
2. az egyperces terhelés a magszám fölött van.

A fájlonkénti alak (`--fajllista`) és a nem futtató kapcsolók átmennek: a
szálak mellett a fájlonkénti ellenőrzés a szabály, nem a tilalom.

Minden hibaágon **fail-open**: egy elromlott kapu nem foghat meg munkát.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from basetemp_kapu import _PYTHON, _fej, _szakaszok  # noqa: E402

#: Ezekkel a kapcsolókkal a futtató nem indít teljes készletet.
_NEM_TELJES = {"--fajllista", "--darabszam", "--csak-takaritas", "-h", "--help"}

#: A szálak jele a `ps -eww -o etimes=,args=` kimenetében.
_CODEX = re.compile(r"codex exec\b.*?-C (\S+)")
_CLAUDE = re.compile(r"^(?:\d+\s+)?claude -p\b.*--permission-mode acceptEdits")
_GEMINI = re.compile(r"^(?:\d+\s+)?(?:\S*/)?agy\s+(?:-p|--print|--prompt)\b")


def _futtato(tokenek: list[str]) -> list[str] | None:
    """A `run_tests.py` utáni argumentumok, ha a szakasz a futtatót indítja."""
    t = _fej(tokenek)
    # a burkoló saját kapcsolói (pl. `nice -n 10`) a valódi parancs előtt
    while t and (t[0].startswith("-") or t[0].isdigit()):
        t = t[1:]
    if not t:
        return None
    if _PYTHON.match(t[0]) and len(t) > 1:
        t = t[1:]
    if t[0] == "run_tests.py" or t[0].endswith("/run_tests.py"):
        return t[1:]
    return None


def teljes_futas(cmd: str) -> bool:
    """Igaz, ha a parancs a TELJES tesztkészletet indítja helyben."""
    for tokenek in _szakaszok(cmd):
        argok = _futtato(tokenek)
        if argok is None:
            continue
        if not any(a.split("=", 1)[0] in _NEM_TELJES for a in argok):
            return True
    return False


def futo_szalak(ps: str) -> dict[str, int]:
    """Szolgáltatónként a futó szálak száma (csak a nem nullák)."""
    sorok = [s.strip() for s in ps.splitlines()]
    db = {
        "codex": len(set(_CODEX.findall(ps))),
        "claude": sum(1 for s in sorok if _CLAUDE.match(s)),
        "gemini": sum(1 for s in sorok if _GEMINI.match(s)),
    }
    return {k: v for k, v in db.items() if v}


def blokkolando(cmd: str, *, ps: str, terheles: float, magok: int) -> str | None:
    """Az indok, ha a parancsot blokkolni kell, különben None."""
    if not teljes_futas(cmd):
        return None
    szalak = futo_szalak(ps)
    if szalak:
        lista = ", ".join(f"{v} {k}" for k, v in szalak.items())
        return f"teljes helyi tesztfutás futó szálak mellett ({lista})"
    if terheles > magok:
        return f"teljes helyi tesztfutás {terheles:.1f}-es terhelésnél ({magok} mag)"
    return None


def _ps() -> str:
    return subprocess.run(["ps", "-eww", "-o", "etimes=,args="],
                          capture_output=True, text=True, timeout=10).stdout


def _terheles() -> tuple[float, int]:
    return os.getloadavg()[0], os.cpu_count() or 1


def main() -> int:
    try:
        adat = json.load(sys.stdin)
        cmd = (adat.get("tool_input") or {}).get("command") or ""
    except Exception:
        return 0
    try:
        if not teljes_futas(cmd):
            return 0
        terheles, magok = _terheles()
        indok = blokkolando(cmd, ps=_ps(), terheles=terheles, magok=magok)
    except Exception:
        return 0
    if indok is None:
        return 0
    sys.stderr.write(
        "[Szálközi futás-kapu] BLOKKOLVA: " + indok + ".\n"
        "\n"
        "Szálak mellett csak fájlonként ellenőrizz:\n"
        "    python3 scripts/run_tests.py --fajllista <lista.txt>\n"
        "A teljes készletet a PR CI-ja futtatja; a helyi teljes futás\n"
        "éjszakára való, amikor nincs szál.\n"
        "\n"
        "Miért (picasapy-agent#308): 2026-11-08-án egy helyi teljes futás\n"
        "három Codex-szál és egy Claude-munkás mellett 15 fölé vitte a\n"
        "négymagos gép terhelését.\n"
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
