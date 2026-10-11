#!/usr/bin/env python3
"""CI-azonos helyi környezet EGY paranccsal (#4834).

    python3 scripts/ci_venv.py            # létrehozza / ellenőrzi a .venv-ci-t
    .venv-ci/bin/python scripts/run_tests.py

A venv a `print_dependencies.py --all` csomagjait kapja, a
`packaging/ci-constraints.txt` constraintjével — pontosan úgy, ahogy a CI.
Ha már létezik és a PySide6-verziója egyezik a CI-ével, nem épít újra
(`--ujra` kikényszeríti). Nem érinti a rendszer-Pythont.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ci_kornyezet  # noqa: E402

ALAP_HELY = ci_kornyezet.GYOKER / ".venv-ci"


def venv_python(hely: Path) -> Path:
    if sys.platform == "win32":
        return hely / "Scripts" / "python.exe"
    return hely / "bin" / "python"


def kell_ujraepiteni(
    van_venv: bool, venv_verzio: str | None, ci: str | None, ujra: bool = False
) -> bool:
    """Újraépít-e: kérésre, hiányzó/sérült venv-nél, vagy verzióeltérésnél."""
    if ujra or not van_venv:
        return True
    return venv_verzio is None or (ci is not None and venv_verzio != ci)


def _venv_pyside(python: Path) -> str | None:
    try:
        kimenet = subprocess.run(
            [str(python), "-c",
             "import importlib.metadata as m; print(m.version('PySide6'))"],
            capture_output=True, text=True, timeout=60, check=True,
        ).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return None
    return kimenet or None


def telepits_pip(hely: Path, python_exe: str) -> None:
    """A valódi építés: venv + pip install -c … $(print_dependencies --all)."""
    if hely.exists():
        shutil.rmtree(hely)
    subprocess.run([python_exe, "-m", "venv", str(hely)], check=True)
    py = str(venv_python(hely))
    subprocess.run([py, "-m", "pip", "install", "-q", "--upgrade", "pip"], check=True)
    csomagok = subprocess.run(
        [sys.executable, str(Path(__file__).with_name("print_dependencies.py")), "--all"],
        capture_output=True, text=True, check=True,
    ).stdout.split()
    subprocess.run(
        [py, "-m", "pip", "install", "-c", str(ci_kornyezet.CONSTRAINT_FAJL), *csomagok],
        check=True,
    )


def keszits(
    hely: Path,
    *,
    ujra: bool = False,
    python_exe: str | None = None,
    telepito: Callable[[Path, str], None] = telepits_pip,
    venv_verzio_olvaso: Callable[[Path], str | None] = _venv_pyside,
) -> tuple[Path, bool]:
    """(a venv python-ja, épült-e újra). A telepítő és az olvasó cserélhető."""
    ci = ci_kornyezet.ci_verzio()
    python = venv_python(hely)
    van = python.exists()
    verzio = venv_verzio_olvaso(python) if van else None
    if kell_ujraepiteni(van, verzio, ci, ujra):
        telepito(hely, python_exe or sys.executable)
        return python, True
    return python, False


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="CI-azonos helyi venv (#4834)")
    ap.add_argument("--hely", type=Path, default=ALAP_HELY, help="a venv helye")
    ap.add_argument("--ujra", action="store_true", help="újraépítés kikényszerítése")
    ap.add_argument("--python", default=None,
                    help="a venv alap-interpretere (a CI Python 3.12-t használ)")
    opciok = ap.parse_args(argv)
    python, epult = keszits(opciok.hely, ujra=opciok.ujra, python_exe=opciok.python)
    ci = ci_kornyezet.ci_verzio()
    print(f"{'Elkészült' if epult else 'Már kész, egyezik'}: {opciok.hely} (PySide6 {ci})")
    print(f"Futtatás vele:  {python} scripts/run_tests.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
