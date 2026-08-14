#!/usr/bin/env python3
"""Füst-teszt a TELEPÍTETT csomagon — #646, #651/2.

A `check_package_contents.py` a wheel névlistáját nézi; ez azt, hogy a
telepített csomag ténylegesen használható-e: betölthető-e a belépési pont,
és a helyükön vannak-e az erőforrások, amiket a program induláskor keres.

A telepített csomag Pythonjával kell futtatni — NEM a forrásfáéval:

    /path/to/venv/bin/python scripts/check_installed_package.py

Ha a forrásfából fut, hibával kilép: a forrásfa mindig „működik", ezért
onnan futtatva ez az ellenőrzés hamis biztonságot adna (pontosan ez a
#646 tanulsága).
"""

from __future__ import annotations

import sys
from importlib.resources import files
from pathlib import Path

#: Amit a program INDULÁSKOR keres — ha bármelyik hiányzik, a telepített
#: PicasaPy sérült, akkor is, ha a tesztek forrásból zöldek.
REQUIRED_RESOURCES: tuple[tuple[str, str], ...] = (
    ("picasapy.app", "qml/Main.qml"),
    ("picasapy.app", "qml/PicasaPy/qmldir"),
    ("picasapy.app", "qml/PicasaPy/EditorPanel.qml"),
    # #646 három reprezentatív áldozata:
    ("picasapy.app", "qml/PicasaPy/icons/deritofeny.svg"),
    ("picasapy.app", "qml/PicasaPy/Gpu/PointFilter.frag"),
    ("picasapy.webexport", "templates/feher/index.tpl"),
)


def _running_from_source_tree() -> bool:
    """Igaz, ha a betöltött `picasapy` a repó `src/` fájából jön."""
    import picasapy

    location = Path(picasapy.__file__).resolve()
    return location.parent.parent.name == "src"


def check() -> list[str]:
    """A hibák listája; üres lista = minden rendben."""
    problems: list[str] = []

    import picasapy

    if picasapy.__version__ == "0+unknown":
        problems.append(
            "a telepített csomag nem tudja a saját verzióját (0+unknown) — "
            "az importlib.metadata út elromlott"
        )

    try:
        from picasapy.app.__main__ import main  # noqa: F401
    except Exception as error:  # noqa: BLE001 — bármilyen hiba itt bukás
        problems.append(f"a belépési pont nem tölthető be: {error!r}")

    for package, relative in REQUIRED_RESOURCES:
        try:
            resource = files(package).joinpath(relative)
            present = resource.is_file()
        except (ImportError, OSError) as error:
            problems.append(f"{package}:{relative} — nem elérhető ({error!r})")
            continue
        if not present:
            problems.append(f"{package}:{relative} — hiányzik a csomagból")

    return problems


def main(argv: list[str] | None = None) -> int:
    if _running_from_source_tree():
        print(
            "HIBA: ez az ellenőrzés a TELEPÍTETT csomagot vizsgálja, de a "
            "forrásfából fut. A telepítés Pythonjával futtasd.",
            file=sys.stderr,
        )
        return 1

    problems = check()
    if problems:
        print("HIBA: a telepített csomag sérült:", file=sys.stderr)
        for problem in problems:
            print(f"    {problem}", file=sys.stderr)
        return 1

    import picasapy

    print(f"OK — a telepített PicasaPy {picasapy.__version__} használható.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
