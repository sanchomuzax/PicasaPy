#!/usr/bin/env python3
"""Szabályváltozás-jelző — Claude Code PreToolUse hook (agent-repó #48).

## A hibaosztály

A szabálykönyvek **csak induláskor** töltődnek be, a felhasználó viszont
szándékosan futtat napokig élő munkameneteket. Egy futó session tehát a régi
szöveggel dolgozik, és jóhiszeműen szembemegy a friss szabállyal.

**Mérve 2026-09-04:** egy 07:22-kor bevezetett szabály (a foglalás mostantól
munkamenet-azonosítót hordoz) után három élő munkamenet **hét órán át**
dolgozott a régi módon — a PicasaPy #2336 foglalása 14:18-kor azonosító
nélkül ment. Nem szegte meg senki: nem volt honnan tudniuk.

**Miért nem ért el hozzájuk az értesítés.** A szabályt egy ÜTEMEZETT kör
vezette be, onnan viszont a `send_message` tiltott („unavailable in unattended
sessions"). A pótmegoldás — az `eszkozok/session_emlekezteto.md` bővítése —
szerkezetileg csak az ütemezett köröket éri el: az ő promptjuk írja elő az
elolvasását. Az élő munkamenetekhez nem volt csatorna.

Ez a jelző az a csatorna: **minden** munkamenet futtat parancsot, tehát
mindegyikhez elér.

## Amit szándékosan NEM csinál

* **Nem kapu — soha nem blokkol.** A `release_kapu` és a `basetemp_kapu`
  megakadályoz egy kárt; itt nincs mit megakadályozni, csak tudatni kell
  valamit. Egy blokkoló jelző a szabály olvasása helyett a jelző
  megkerülésére ösztönözne.
* **Nem garancia.** A garancia a szabály mellé tett KAPU vagy MÉRŐ — ezt a
  privát `CLAUDE.md` mondja ki. Ez a jelző gyorsít: órákat, nem többet.
* **Nem ismétel.** Minden Bash-parancs előtt lefut; ugyanarra a változásra
  egyszer szól. A némítás a LÁTOTT állapotra szól, tehát egy újabb változást
  újra bejelent.

Minden hibaágon **fail-open**: elromlott jelző nem akaszthat meg munkát.
"""

from __future__ import annotations

import hashlib
import json
import os
import pathlib
import sys

#: A figyelt szabálykönyvek. A privát repó két helyen állhat (helyi gép,
#: felhős munkatér); a hiányzó fájl nem hiba — a klón hiányozhat.
_PRIVAT = [pathlib.Path.home() / "picasapy-agent",
           pathlib.Path("/workspace/picasapy-agent")]

SZABALYKONYVEK = [
    *(p / "CLAUDE.md" for p in _PRIVAT),
    *(p / "PROTOKOLL.md" for p in _PRIVAT),
    pathlib.Path(os.environ.get("CLAUDE_PROJECT_DIR", ".")) / "CLAUDE.md",
]

#: Munkamenetenkénti állapot. A `~/.cache` alatt, mert nem a repóé.
ALLAPOT_MAPPA = pathlib.Path.home() / ".cache" / "picasapy-agent" / "szabalylenyomat"


def _lenyomat() -> dict[str, str]:
    """Fájl → tartalom-ujjlenyomat. A hiányzó fájl kimarad, nem hibázik."""
    ki: dict[str, str] = {}
    for ut in SZABALYKONYVEK:
        try:
            ki[str(ut)] = hashlib.sha256(ut.read_bytes()).hexdigest()[:16]
        except OSError:
            continue
    return ki


def _allapot_fajl() -> pathlib.Path | None:
    azonosito = os.environ.get("CLAUDE_CODE_SESSION_ID", "").strip()
    if not azonosito:
        #: Azonosító nélkül nem tudjuk munkamenethez kötni az állapotot, és a
        #: közös fájl KERESZTBE szólna a párhuzamos sessionöknek. Inkább
        #: hallgatunk: a hamis jelzés rosszabb, mint a hiányzó.
        return None
    biztonsagos = "".join(c for c in azonosito if c.isalnum() or c in "-_")
    return ALLAPOT_MAPPA / f"{biztonsagos}.json"


def valtozasok(regi: dict[str, str], uj: dict[str, str]) -> list[str]:
    """Mely szabálykönyvek változtak a legutóbb LÁTOTT állapot óta."""
    return sorted(ut for ut, jegy in uj.items() if regi.get(ut, jegy) != jegy)


def main() -> int:
    try:
        json.load(sys.stdin)  # a parancs tartalma közömbös, a jelenléte nem
    except Exception:
        return 0

    try:
        fajl = _allapot_fajl()
        if fajl is None:
            return 0
        mostani = _lenyomat()
        if not mostani:
            return 0

        try:
            regi = json.loads(fajl.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            regi = {}

        fajl.parent.mkdir(parents=True, exist_ok=True)
        fajl.write_text(json.dumps(mostani), encoding="utf-8")

        if not regi:
            return 0  # első futás: rögzítünk, nincs mihez képest változás

        valt = valtozasok(regi, mostani)
        if not valt:
            return 0

        sys.stderr.write(
            "[Szabályváltozás] A munkameneted indulása óta módosult:\n  "
            + "\n  ".join(valt)
            + "\n⚠️ A szabálykönyvek CSAK INDULÁSKOR töltődnek be, tehát a "
            "kontextusodban a RÉGI szöveg van.\nOlvasd el a változást, "
            "mielőtt foglalsz vagy szabályra hivatkozol (agent-#48).\n"
        )
    except Exception:
        return 0  # fail-open: elromlott jelző nem akaszthat meg munkát
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
