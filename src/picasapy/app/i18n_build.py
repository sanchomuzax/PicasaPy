"""A futásidejű `.qm` fordítás helyben készül a `.ts` forrásból (#4817).

A lefordított `.qm` bináris, ezért a git nem tud összefésülni: amíg a
PR-ek is hordozták, bármelyik beolvadás után az összes többi PR ütközött,
és csak egyenként mehettek be. A `.qm` ezért nincs a repóban; itt készül:

* forrásból indítva a program a betöltés előtt lefordítja a kért nyelvet,
  ha a `.qm` hiányzik vagy régebbi a `.ts`-nél;
* a tesztmunkamenet és a csomagépítés az összeset lefordítja
  (`scripts/build_qm.py`).

A telepített csomagban (wheel, PyInstaller) a `.ts` nincs benne, csak a
már lefordított `.qm` — ott ez a modul semmit nem csinál.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

LRELEASE = "pyside6-lrelease"

#: a teszt EZT cseréli, nem a globális `subprocess.run`-t (#1375)
_run = subprocess.run


def lrelease_parancs() -> str | None:
    """A `pyside6-lrelease` útja: PATH-ból, vagy a futó Python mellől."""
    talalt = shutil.which(LRELEASE)
    if talalt:
        return talalt
    bin_dir = Path(sys.executable).parent
    for jelolt in (bin_dir / LRELEASE, bin_dir / f"{LRELEASE}.exe",
                   bin_dir / "Scripts" / f"{LRELEASE}.exe"):
        if jelolt.is_file():
            return str(jelolt)
    return None


def _friss(ts: Path, qm: Path) -> bool:
    return qm.is_file() and qm.stat().st_mtime >= ts.stat().st_mtime


def forditsd(ts: Path, parancs: str | None = None) -> bool:
    """A `ts` mellé lefordítja a `.qm`-et, ha hiányzik vagy elavult.

    Igaz, ha utána friss `.qm` áll a helyén. Párhuzamos hívók (fájlonkénti
    tesztfolyamatok) ne lássanak félig írt fájlt: ideiglenes fájlba
    fordítunk, és atomikusan cseréljük."""
    qm = ts.with_suffix(".qm")
    if not ts.is_file():
        return qm.is_file()
    if _friss(ts, qm):
        return True
    parancs = parancs or lrelease_parancs()
    if parancs is None:
        return qm.is_file()
    fd, ideiglenes = tempfile.mkstemp(suffix=".qm", dir=ts.parent)
    os.close(fd)
    try:
        eredmeny = _run(
            [parancs, str(ts), "-qm", ideiglenes, "-silent"],
            capture_output=True, text=True, encoding="utf-8",
            errors="replace", check=False, timeout=120,
        )
        if eredmeny.returncode != 0 or Path(ideiglenes).stat().st_size == 0:
            return qm.is_file()
        os.replace(ideiglenes, qm)
        return True
    except (OSError, subprocess.SubprocessError):
        return qm.is_file()
    finally:
        if os.path.exists(ideiglenes):
            os.unlink(ideiglenes)


def forditsd_mind(i18n_dir: Path) -> list[Path]:
    """Az összes `picasapy_*.ts` lefordítása; a sikertelenek listája."""
    parancs = lrelease_parancs()
    return [ts for ts in sorted(i18n_dir.glob("picasapy_*.ts"))
            if not forditsd(ts, parancs)]
