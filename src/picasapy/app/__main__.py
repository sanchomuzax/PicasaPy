"""Belépési pont: python -m picasapy.app [könyvtár-gyökér...]

A ``main()`` a csomagolt (pip/pipx-telepített) `picasapy` parancssori
belépési pontja is (ld. pyproject.toml [project.scripts], #4) — a
setuptools által generált indítószkript ezt hívja argumentum nélkül,
ezért itt olvassuk ki a sys.argv-t.
"""

import sys
import time

#: #1601: a LEGELSŐ saját sorunk a processzben — innen mérjük, mennyit visz
#: el maga a PySide6- és picasapy-import, mielőtt a `run()` egyáltalán
#: elindulna. Az idővonal alapból ki van kapcsolva, ez a hívás pedig egy
#: óraolvasás, tehát kikapcsolva sem kerül semmibe.
_ENTRY_AT = time.monotonic()

from .application import run  # noqa: E402 — az időbélyeg elé nem kerülhet


def main() -> int:
    """A telepített `picasapy` parancs belépési pontja."""
    return run(sys.argv, entry_at=_ENTRY_AT)


if __name__ == "__main__":
    sys.exit(main())
