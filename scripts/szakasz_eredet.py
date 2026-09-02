"""Szakaszonkénti eredet: mikor frissült a forrás, és mitől frissülne — #2046.

A lap fejléce a GENERÁLÁS idejét írja ki, ezért minden futás után mainak
látszik. A tartalom nagy része viszont commitolt mérésből jön, ami hetekig
változatlan: a bináris térkép forrása például 2026-08-12 óta ugyanaz. A
tulajdonos joggal olvasta hamis frissességnek.

Ez a modul két dolgot ad minden szakaszhoz: a FORRÁS korát (nem a futásét), és
egy mondatot arról, mitől frissülne. A kettő együtt teszi olvashatóvá, hogy
melyik szám friss és melyik pillanatfelvétel.
"""

from __future__ import annotations

import html
import subprocess
from datetime import datetime
from pathlib import Path

#: A git-hívás nem foghatja meg a lapot: hiba esetén a fájl ideje a tartalék.
_IDOKORLAT = 20


def forras_datum(ut: Path | str) -> str | None:
    """A forrásadat kora `ÉÉÉÉ-HH-NN` alakban, vagy ``None``, ha nincs ilyen fájl.

    Elsődlegesen a git utolsó commit-dátuma, mert az mondja meg, mikor
    változott ÉRDEMBEN a tartalom. Ha a fájl nincs követve — például frissen
    generált mérés —, a módosítás ideje az adat kora.
    """
    ut = Path(ut)
    if not ut.exists():
        return None
    try:
        kimenet = subprocess.run(
            ["git", "log", "-1", "--format=%ad", "--date=short", "--", str(ut)],
            cwd=ut.parent,
            capture_output=True,
            text=True,
            timeout=_IDOKORLAT,
            check=True,
        ).stdout.strip()
    except (
        subprocess.CalledProcessError,
        subprocess.TimeoutExpired,
        FileNotFoundError,
        OSError,
    ):
        kimenet = ""
    if kimenet:
        return kimenet
    return datetime.fromtimestamp(ut.stat().st_mtime).strftime("%Y-%m-%d")


def eredet_sor(datum: str | None, mondat: str) -> str:
    """A szakaszcím alatti sor: a forrás kora, és mitől frissülne.

    Ismeretlen dátumnál a mondat akkor is kimegy — a „mitől frissül" önmagában
    is információ, és a hiányzó dátum nem indok a szakasz elhallgatására.
    """
    mondat_h = html.escape(str(mondat), quote=True)
    if not datum:
        return f'<p class="eredet">frissül: {mondat_h}</p>'
    d = html.escape(str(datum), quote=True)
    return (
        f'<p class="eredet">az adat kora: <time datetime="{d}">{d}</time>'
        f" · frissül: {mondat_h}</p>"
    )
