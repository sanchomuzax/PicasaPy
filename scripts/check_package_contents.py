#!/usr/bin/env python3
"""A FELÉPÍTETT csomag tartalmát veti össze a forrásfával — #646, #651/2.

Miért kell: a CI a forrásfából futtat (`pythonpath = ["src"]`), ezért a
tesztek akkor is zöldek, ha a telepített csomag használhatatlan. Pontosan
ez történt: a `pyproject.toml` tételes `package-data` mintalistája csendben
kihagyott 40 futásidőben szükséges fájlt (a teljes `qml/PicasaPy/icons/`
ikonkészletet, a `Gpu/*.frag`-ot és a `webexport/templates/**`-ot). A hibát
a felhasználó találta meg, éles Windows-telepítésen.

Ez a szkript a kimenetet méri, nem a szándékot: kicsomagolja a wheel
névlistáját, és minden nem-Python forrásfájlra megköveteli, hogy benne
legyen. Ami szándékosan marad ki, azt itt, NÉVVEL kell felsorolni — így a
kihagyás tudatos döntés, nem véletlen elmaradás.

Használat:

    python scripts/check_package_contents.py dist/picasapy-*.whl

Kilépési kód: 0 ha minden megvan, 1 ha bármi hiányzik.
"""

from __future__ import annotations

import argparse
import fnmatch
import sys
import zipfile
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_PACKAGE_ROOT = _REPO_ROOT / "src" / "picasapy"

#: SZÁNDÉKOS kivételek — a `MANIFEST.in` kizárásaival összhangban.
#: Bővíteni csak indoklással szabad: minden új sor egy fájl, amit a
#: telepített PicasaPy NEM kap meg.
INTENTIONALLY_EXCLUDED: tuple[tuple[str, str], ...] = (
    (
        "picasapy/app/i18n/*.ts",
        "fordítási FORRÁS — futásidőben a lefordított .qm pár kell",
    ),
)

#: Sosem tartoznak a csomagba (fejlesztői melléktermékek).
_IGNORED_SUFFIXES = frozenset({".py", ".pyc", ".pyo", ".orig", ".rej"})
_IGNORED_DIRS = frozenset({"__pycache__"})


def source_data_files() -> set[str]:
    """A forrásfa nem-Python fájljai, csomagon belüli útvonalként."""
    files = set()
    for path in _PACKAGE_ROOT.rglob("*"):
        if path.is_dir():
            continue
        if _IGNORED_DIRS & set(path.parts):
            continue
        if path.suffix in _IGNORED_SUFFIXES:
            continue
        files.add("picasapy/" + path.relative_to(_PACKAGE_ROOT).as_posix())
    return files


def wheel_entries(wheel: Path) -> set[str]:
    """A wheel névlistája a `.dist-info` metaadatok nélkül."""
    with zipfile.ZipFile(wheel) as archive:
        return {
            name
            for name in archive.namelist()
            if not name.endswith("/") and ".dist-info/" not in name
        }


def is_intentionally_excluded(name: str) -> str | None:
    """A kivétel indoklása, vagy None ha nem szándékos kihagyás."""
    for pattern, reason in INTENTIONALLY_EXCLUDED:
        if fnmatch.fnmatch(name, pattern):
            return reason
    return None


def missing_from_wheel(wheel: Path) -> list[str]:
    """A csomagból hiányzó, NEM szándékosan kihagyott fájlok."""
    entries = wheel_entries(wheel)
    return sorted(
        name
        for name in source_data_files() - entries
        if is_intentionally_excluded(name) is None
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("wheel", type=Path, help="a vizsgálandó .whl fájl")
    args = parser.parse_args(argv)

    if not args.wheel.is_file():
        print(f"HIBA: nincs ilyen fájl: {args.wheel}", file=sys.stderr)
        return 1

    missing = missing_from_wheel(args.wheel)
    if missing:
        print(
            f"HIBA: {len(missing)} futásidőben szükséges fájl hiányzik a "
            f"csomagból ({args.wheel.name}):",
            file=sys.stderr,
        )
        for name in missing:
            print(f"    {name}", file=sys.stderr)
        print(
            "\nA MANIFEST.in `graft`-ja MINDENT bevesz a csomagfa alól — ha "
            "valami mégis kimarad, vagy egy kizárás túl tág, vagy a fájl "
            "szándékosan marad ki: akkor vedd fel a szkript "
            "INTENTIONALLY_EXCLUDED listájába, INDOKLÁSSAL.",
            file=sys.stderr,
        )
        return 1

    data_files = len(source_data_files())
    print(f"OK — mind a(z) {data_files} nem-Python fájl benne van a csomagban.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
