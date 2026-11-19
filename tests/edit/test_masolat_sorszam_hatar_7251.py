"""#7251: A másolat névütközési számozása legfeljebb -4095-ig keres.

Eredeti: a másolat névütközési keresője (`0x00993650`; Ghidra-kimenet:
`2026-11-18-koteg-466-495.txt:7099-7397`, Capstone `0x00993b52-0x00993b63`;
a Save a Copy útja `0x005e6a20` hívja; spec: `docs/specs/paritas-ellenorzes-archiv-1.md`,
#7235).

A `%s-%03lu` mintájú másolatnév keresése legfeljebb a `-4095` sorszámig
próbálkozik. Ha mind a 4095 sorszám foglalt, FileNameCollisionError-ral áll meg,
és nem ajánl `-4096`-ot.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from picasapy.edit.save_copy import (
    FileNameCollisionError,
    next_copy_path,
)


def _ures_fajl(utvonal: Path) -> None:
    fd = os.open(utvonal, os.O_CREAT | os.O_WRONLY, 0o644)
    os.close(fd)


class TestMasolatSorszamHatar7251:
    """A másolat névütközési számozása legfeljebb -4095-ig keres (#7251)."""

    def test_utolso_szabad_sorszam_4095(self, tmp_path: Path):
        """Ha -001-től -4094-ig minden foglalt és -4095 szabad, azt adja."""
        forras = tmp_path / "kep.jpg"
        _ures_fajl(forras)

        for i in range(1, 4095):
            _ures_fajl(tmp_path / f"kep-{i:03d}.jpg")

        kovetkezo = next_copy_path(forras)
        assert kovetkezo == tmp_path / "kep-4095.jpg"

    def test_mind_foglalt_nem_ad_4096_ot_kivetelt_dob(self, tmp_path: Path):
        """Ha mind a 4095 sorszám foglalt, nem ad -4096-ot, hanem FileNameCollisionError-t dob."""
        forras = tmp_path / "kep.jpg"
        _ures_fajl(forras)

        for i in range(1, 4096):
            _ures_fajl(tmp_path / f"kep-{i:03d}.jpg")

        with pytest.raises(FileNameCollisionError) as exc_info:
            next_copy_path(forras)

        assert "Nem található szabad másolat-név" in str(exc_info.value)

    def test_korabbi_szabad_sorszamnal_legkisebbet_valasztja(self, tmp_path: Path):
        """Korábbi szabad sorszámnál továbbra is a legkisebbet választja."""
        forras = tmp_path / "kep.jpg"
        _ures_fajl(forras)

        # kep-001 és kep-002 foglalt, kep-003 szabad, kep-004 foglalt
        _ures_fajl(tmp_path / "kep-001.jpg")
        _ures_fajl(tmp_path / "kep-002.jpg")
        _ures_fajl(tmp_path / "kep-004.jpg")

        assert next_copy_path(forras) == tmp_path / "kep-003.jpg"
