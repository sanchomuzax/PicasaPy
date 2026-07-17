"""Belépési pont: python -m picasapy.app [könyvtár-gyökér...]"""

import sys

from .application import run

if __name__ == "__main__":
    sys.exit(run(sys.argv))
