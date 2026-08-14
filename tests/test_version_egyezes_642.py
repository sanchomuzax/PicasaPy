"""A kijelzett verzió egyezzen a `pyproject.toml`-lal — #642.

**A hiba, ami ellen ez az őr szól.** A verzió két helyen élt (`pyproject.toml`
és `src/picasapy/__init__.py`), és csak az egyiket emelték kiadáskor. A kettő
**26 kiadásnyira** csúszott szét: a program `v0.6.86`-ot mutatott, miközben a
main 0.7.35 volt.

Ez nem kozmetika. A felhasználó jóhiszeműen a kijelzett verziót jelenti a
hibabejelentésben, és az rossz nyomra viszi a keresést — a #641 vizsgálata
emiatt indult először rossz irányba: a bejelentett `v0.6.86` alapján egy már
javított, régi hibának tűnt, holott a friss main-en élt.

A hiba pontosan azért élhetett hónapokig, mert **semmi nem ellenőrizte**.
Ez a teszt Qt-mentes, gyors, és minden körben fut.
"""

from __future__ import annotations

import re
import tomllib
from pathlib import Path

import picasapy

_PYPROJECT = Path(__file__).resolve().parents[1] / "pyproject.toml"


def _pyproject_verzio() -> str:
    adat = tomllib.loads(_PYPROJECT.read_text(encoding="utf-8"))
    return adat["project"]["version"]


class TestVerzioEgyezes:
    def test_a_csomag_verzioja_a_pyprojectbol_jon(self) -> None:
        assert picasapy.__version__ == _pyproject_verzio()

    def test_nincs_beegetett_szam_az_initben(self) -> None:
        """Az igazságforrás EGY hely; a `__init__.py`-ban nem állhat
        szó szerinti verziószám — pont az csúszott el."""
        forras = (
            Path(picasapy.__file__).resolve()
        ).read_text(encoding="utf-8")

        assert not re.search(r'__version__\s*=\s*["\']\d', forras), (
            "a __version__ nem lehet beégetett szám — származtatni kell"
        )

    def test_a_verzio_ertelmes_alaku(self) -> None:
        """Ne csússzon át a visszaesési érték sem észrevétlenül."""
        assert re.match(r"^\d+\.\d+\.\d+", picasapy.__version__), (
            f"gyanús verzió: {picasapy.__version__!r}"
        )


class TestAKijelzettVerzio:
    def test_a_version_string_ezt_hasznalja(self) -> None:
        """A Névjegy és a teljesítmény-jelentés ezen a láncon át kap számot."""
        from picasapy.version import version_string

        assert version_string().startswith(f"v{picasapy.__version__}")
