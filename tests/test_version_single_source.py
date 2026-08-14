"""A verziónak EGY igazságforrása van — #642, #651/1.

A hiba, amit ez az őr kizár: a `pyproject.toml`-t kiadásonként emelték, a
`picasapy/__init__.py`-ban lévő MÁSOLATOT viszont senki, így a program
hónapokig `v0.6.86`-ot írt ki, miközben a kód 0.7.35 volt — 26 kiadásnyi
eltérés. A felhasználó jóhiszeműen a kijelzett verziót jelentette a
hibabejelentésekben, ami a hibakeresést vitte rossz nyomra.

Ez a teszt Qt-mentes és gyors: a CI minden körben futtatja, tehát ha a két
érték bármikor szétcsúszik, azonnal piros. Pontosan ez hiányzott — a
korábbi hiba nem azért élt hónapokig, mert nehéz volt észrevenni, hanem
mert SEMMI nem ellenőrizte.
"""

from __future__ import annotations

import tomllib
from pathlib import Path

import picasapy

_REPO_ROOT = Path(__file__).resolve().parents[1]
_PYPROJECT = _REPO_ROOT / "pyproject.toml"


def _pyproject_version() -> str:
    with _PYPROJECT.open("rb") as handle:
        return tomllib.load(handle)["project"]["version"]


class TestTheVersionComesFromOnePlace:
    def test_the_package_version_matches_pyproject(self):
        assert picasapy.__version__ == _pyproject_version(), (
            "a program más verziót ír ki, mint amit a kiadási automatika "
            "a pyproject.toml-ból tagel — ez a #642 hibája"
        )

    def test_the_version_is_not_the_unknown_fallback(self):
        """A forrásfából futtatva a `pyproject.toml`-t meg KELL találni.

        Ha ez bukik, a származtatás elromlott (áthelyezett fájl, elrontott
        útvonal) — a felhasználó ilyenkor `0+unknown`-t látna."""
        assert picasapy.__version__ != "0+unknown"

    def test_no_literal_version_is_stored_in_the_package(self):
        """A `__init__.py` nem tartalmazhat beégetett verziószámot.

        A #642 pontosan attól állt elő, hogy volt egy második, kézzel
        karbantartott másolat. Ez az állítás a MÓDSZERT őrzi, nem az
        eredményt: egy új másolat akkor is megbukik itt, ha épp egyezik."""
        source = (_REPO_ROOT / "src" / "picasapy" / "__init__.py").read_text(
            encoding="utf-8"
        )
        version = _pyproject_version()
        assert f'"{version}"' not in source, (
            "a verziószám beégetve szerepel a csomagban — a pyproject.toml "
            "az egyetlen hely, ahol a szó szerinti szám állhat"
        )


class TestTheReleaseAutomationCanStillReadIt:
    """A `release.yml` szövegesen olvassa a `pyproject.toml`-t:

        grep -m1 '^version = ' pyproject.toml

    Ezért a `dynamic = ["version"]` irányba fordítás elrontaná a kiadást.
    Ez az őr azt rögzíti, hogy a szó szerinti sor a helyén marad."""

    def test_pyproject_has_a_literal_version_line(self):
        lines = _PYPROJECT.read_text(encoding="utf-8").splitlines()
        literal = [line for line in lines if line.startswith("version = ")]
        assert len(literal) == 1, (
            "a release.yml az első '^version = ' sorra épül — pontosan "
            "egynek kell lennie belőle"
        )
        assert literal[0] == f'version = "{_pyproject_version()}"'
