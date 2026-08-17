#!/usr/bin/env python3
"""A futtatókörnyezet csomagjainak EGYETLEN lekérdezője.

Miért kell: a környezet csomaglistája korábban négy végrehajtható helyen élt
egymás mellett (CI, Claude-hook, Codex-hook, `pyproject.toml`), és a
szinkronjukat csak egy komment kérte — a `libpulse0` már el is csúszott
közöttük. A javítás nem őr, hanem a többi lista megszüntetése: a telepítők
innen kérdezik le, mit kell telepíteni.

Igazságforrások:

- Python-csomagok: `pyproject.toml` — a `[project] dependencies` (futásidejű)
  és a `[project.optional-dependencies] dev` (teszt/lint/build eszközök).
- Rendszercsomagok: `packaging/qt-runtime-deps.txt`.

Használat (a kimenet szóközzel/újsorral tagolt, közvetlenül a telepítőnek
adható):

    pip install $(python scripts/print_dependencies.py --all)
    sudo apt-get install -y $(python scripts/print_dependencies.py --apt)

Szándékosan NEM telepíti a projektet magát (`pip install -e .`): az
`*.egg-info`-t hagyna a munkafában, amit a `git status` nem is mutat, a
csomag-ellenőrzők viszont újrahasznosítanak belőle — pontosan ez a #655-ben
leírt hamis zöld. A tesztek úgyis a forrásfából futnak (`pythonpath=["src"]`).

Őr: `tests/test_kornyezet_szinkron.py`.
"""

from __future__ import annotations

import argparse
import sys
import tomllib
from pathlib import Path

_GYOKER = Path(__file__).resolve().parents[1]
_PYPROJECT = _GYOKER / "pyproject.toml"
_APT_LISTA = _GYOKER / "packaging" / "qt-runtime-deps.txt"


def _python_csomagok(dev: bool, futasideju: bool) -> list[str]:
    adat = tomllib.loads(_PYPROJECT.read_text(encoding="utf-8"))
    projekt = adat["project"]
    csomagok: list[str] = []
    if futasideju:
        csomagok.extend(projekt.get("dependencies", []))
    if dev:
        csomagok.extend(projekt.get("optional-dependencies", {}).get("dev", []))
    return csomagok


def _apt_csomagok() -> list[str]:
    sorok = _APT_LISTA.read_text(encoding="utf-8").splitlines()
    return [s.strip() for s in sorok if s.strip() and not s.strip().startswith("#")]


def main(argv: list[str] | None = None) -> int:
    ertelmezo = argparse.ArgumentParser(
        description="A futtatókörnyezet csomagjai, soronként egy."
    )
    csoport = ertelmezo.add_mutually_exclusive_group()
    csoport.add_argument(
        "--dev",
        action="store_true",
        help="csak a fejlesztői eszközök (teszt, lint, build)",
    )
    csoport.add_argument(
        "--all",
        action="store_true",
        help="futásidejű + fejlesztői csomagok együtt",
    )
    csoport.add_argument(
        "--apt",
        action="store_true",
        help="a Qt-hez kellő Linux rendszercsomagok",
    )
    opciok = ertelmezo.parse_args(argv)

    if opciok.apt:
        csomagok = _apt_csomagok()
    else:
        csomagok = _python_csomagok(
            dev=opciok.dev or opciok.all,
            futasideju=not opciok.dev,
        )

    print("\n".join(csomagok))
    return 0


if __name__ == "__main__":
    sys.exit(main())
