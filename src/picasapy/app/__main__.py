"""Belépési pont: python -m picasapy.app [könyvtár-gyökér...]

A ``main()`` a csomagolt (pip/pipx-telepített) `picasapy` parancssori
belépési pontja is (ld. pyproject.toml [project.scripts], #4) — a
setuptools által generált indítószkript ezt hívja argumentum nélkül,
ezért itt olvassuk ki a sys.argv-t.
"""

import sys

from .application import run


def main() -> int:
    """A telepített `picasapy` parancs belépési pontja."""
    return run(sys.argv)


if __name__ == "__main__":
    sys.exit(main())
