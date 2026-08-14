#!/usr/bin/env python3
"""A pyproject.toml deklarált setuptools-minimuma VALÓBAN elég-e — #652 őre.

A #652 hibája: `[build-system] requires = ["setuptools>=68"]` mellett a
`[project] license = "GPL-3.0-or-later"` PEP 639 string-alakját a
setuptools csak 77.0.0-tól érti. Build-izolációval (`python -m build`,
`pip install .`) ez nem tűnt fel, mert az MINDIG a legfrissebb setuptoolst
húzza be — a deklarált minimum csak `--no-build-isolation` mellett számít
(disztribúciós/csomagolói build, tükrözött index, pinnelt környezet).

Ez a szkript ezt a helyzetet szimulálja VALÓDIAN, nem a deklarációt nézve:
kiolvassa a `pyproject.toml`-ból deklarált setuptools-minimumot, egy friss
venv-be a deklarált főverzió-családot (`<minimum>.*`, pl. `77.*` — a
minimum PONTOS száma gyakran nem létező kiadás, ld. a docstring alján)
telepíti, és `--no-isolation`-nel próbál wheelt építeni. Ha a deklarált
minimum nem elég, a build elbukik — ez a fajta ellenőrzés a deklarációt a
valósághoz méri, nem önmagához.

Használat:

    python scripts/check_declared_setuptools_minimum.py

Kilépési kód: 0 ha a deklarált minimum valóban elég a buildhez, 1 ha nem
(vagy a próba maga nem futtatható le).

Miért `<minimum>.*` és nem a pontos szám: a `pyproject.toml`-ban a
`setuptools>=77` a 77-es FŐVERZIÓ-küszöböt jelöli, de a PyPI-n gyakran
nincs pontosan "77.0.0" kiadás (csak pl. 77.0.1, 77.0.3) — az `==77`
emiatt hamisan "nem telepíthető" hibát adna. A `77.*` a főverzió-családot
pontosan a deklarált küszöbnek megfelelő granularitásban célozza meg (ezt
javasolja maga a #652 jegy is, mint egyszerűbb, de valódi alternatívát).

Miért TISZTA forrásfa-másolaton épít, nem a repón magán: a `python -m
build` a `build/`-ot és az `*.egg-info`-t a FORRÁSFÁBA írja, nem csak az
`--outdir`-ba — ha ez a szkript közvetlenül a repón futna, saját magát
szennyezné be a #655-ben leírt módon (ez a próbafuttatás közben ki is
derült). Ezért előbb egy ideiglenes könyvtárba MÁSOLJA a forrásfát (a `.git`,
`build`, `dist` és `*.egg-info` nélkül), és ott épít.
"""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
import tempfile
import tomllib
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]

#: `"setuptools>=77"` alakú bejegyzésből a "77" kiolvasása.
_SETUPTOOLS_MIN_RE = re.compile(r"setuptools>=(\d+(?:\.\d+)*)")

#: Amit a forrásfa-másolat NEM kap meg — a build-melléktermékek és a VCS.
_EXCLUDED_FROM_COPY = frozenset({".git", "build", "dist", "__pycache__"})


def _copy_clean_source_tree(destination: Path) -> None:
    """A repó TISZTA másolata — a próba ne szennyezze be az igazi fát (#655)."""

    def _ignore(_directory: str, names: list[str]) -> set[str]:
        return {
            name
            for name in names
            if name in _EXCLUDED_FROM_COPY or name.endswith(".egg-info")
        }

    shutil.copytree(_REPO_ROOT, destination, ignore=_ignore)


def declared_minimum() -> str:
    """A `[build-system] requires`-ben deklarált setuptools alsó határa."""
    with (_REPO_ROOT / "pyproject.toml").open("rb") as handle:
        config = tomllib.load(handle)

    for entry in config["build-system"]["requires"]:
        match = _SETUPTOOLS_MIN_RE.fullmatch(entry.strip())
        if match:
            return match.group(1)

    raise SystemExit(
        "HIBA: a pyproject.toml [build-system] requires listájában nincs "
        "'setuptools>=<szám>' alakú bejegyzés — a szkript ezt várná."
    )


def _venv_python(venv_dir: Path) -> Path:
    candidate = venv_dir / "bin" / "python"
    if candidate.is_file():
        return candidate
    return venv_dir / "Scripts" / "python.exe"


def main() -> int:
    version = declared_minimum()
    print(
        f"Deklarált setuptools-minimum: {version} — valódi build-próba "
        "--no-build-isolation-nel."
    )

    with tempfile.TemporaryDirectory(prefix="picasapy-min-setuptools-") as tmp:
        tmp_path = Path(tmp)
        source_copy = tmp_path / "source"
        _copy_clean_source_tree(source_copy)

        venv_dir = tmp_path / "venv"
        subprocess.run(
            [sys.executable, "-m", "venv", str(venv_dir)], check=True
        )
        venv_python = _venv_python(venv_dir)

        pinned_family = f"setuptools=={version}.*"
        install = subprocess.run(
            [
                str(venv_python),
                "-m",
                "pip",
                "install",
                "--no-cache-dir",
                "--quiet",
                pinned_family,
                "wheel",
                "build",
            ]
        )
        if install.returncode != 0:
            print(
                f"HIBA: a deklarált minimum ({pinned_family}) nem "
                "telepíthető — ellenőrizd, hogy ez a főverzió-család "
                "létezik-e a PyPI-n.",
                file=sys.stderr,
            )
            return 1

        build = subprocess.run(
            [
                str(venv_python),
                "-m",
                "build",
                "--wheel",
                "--no-isolation",
                "--outdir",
                str(tmp_path / "dist"),
                str(source_copy),
            ]
        )

    if build.returncode != 0:
        print(
            f"HIBA: a deklarált setuptools-minimum (>={version}) NEM elég a "
            "csomagépítéshez build-izoláció nélkül — a pyproject.toml "
            "[build-system] requires sora hazudik (#652). Emeld a "
            "minimumot, amíg a build itt is sikerül.",
            file=sys.stderr,
        )
        return 1

    print(f"OK — a deklarált setuptools>={version} valóban elég a buildhez.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
