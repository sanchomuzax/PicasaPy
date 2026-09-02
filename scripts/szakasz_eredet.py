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


#: #2057: PERC kell, nem nap. Az élő szakaszok naponta többször frissülnek,
#: ezért a puszta dátumból nem dönthető el, hogy „most" vagy „ma reggel".
IDO_ALAK = "%Y-%m-%d %H:%M"


def forras_ideje(ut: Path | str) -> str | None:
    """A forrásadat kelte `ÉÉÉÉ-HH-NN ÓÓ:PP` alakban, vagy ``None``.

    Elsődlegesen a git utolsó commit-ideje, mert az mondja meg, mikor változott
    ÉRDEMBEN a tartalom. Ha a fájl nincs követve — például frissen generált
    mérés —, a módosítás ideje az adat kelte.
    """
    ut = Path(ut)
    if not ut.exists():
        return None
    try:
        kimenet = subprocess.run(
            ["git", "log", "-1", "--format=%ad",
             f"--date=format:{IDO_ALAK}", "--", str(ut)],
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
    return datetime.fromtimestamp(ut.stat().st_mtime).strftime(IDO_ALAK)


def eredet_sor(idopont: str | None, esemeny: str) -> str:
    """A szakaszcím alatti sor: az adat kelte, és mi VÁLTOZTATJA MEG.

    Az `esemeny` a valódi kiváltó ok a felhasználó nyelvén — „új kiadás
    készül", „egy kutatási kör újramér" —, **nem** a lekérdezés mechanikája.
    #2057: a „minden futáskor, élő GitHub-lekérdezés" azt mondta meg, hogyan
    jön az adat, nem azt, mitől lesz más.

    Ismeretlen időpontnál az esemény akkor is kimegy: a „mi változtatja meg"
    önmagában is információ.
    """
    esemeny_h = html.escape(str(esemeny), quote=True)
    if not idopont:
        return f'<p class="eredet">változik: {esemeny_h}</p>'
    d = html.escape(str(idopont), quote=True)
    return (
        f'<p class="eredet">az adat kelte: <time datetime="{d}">{d}</time>'
        f" · változik: {esemeny_h}</p>"
    )
