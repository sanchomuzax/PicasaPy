"""#7291: az írásvédett forrásból nem lesz írásvédett másolat, és a meglévő
írásvédett cél felülírható.

## Mi volt a baj

A `futtasd` a `shutil.copy2`-vel másolt, ami a módbiteket is viszi: az
írásvédett forrásból írásvédett cél lett. A következő futás a megváltozott
képet már nem tudta ráírni (`PermissionError`), a hibát csendben
elnyelte, a fájl nem került a nyilvántartásba, tehát MINDEN futás újra
megtervezte, és a felület mégis „Backup Complete"-et mutatott.

## Az eredeti (`Picasa3.exe`)

`0x0067834e` `GetFileAttributes` a célon, `0x00678359` `test al,1`
(írásvédett?), `0x0067835d` `and eax,0xfffffffe`, `0x00678362`
`SetFileAttributes`: a meglévő írásvédett cél előbb írhatóvá válik. Utána
`0x0067839a` `CreateFile(OPEN_ALWAYS, FILE_ATTRIBUTE_NORMAL)`: az új cél
sosem örökli a forrás attribútumait. Hibaág: `0x006783a0` `cmp eax,-1` ->
naplósor (`.\\yt\\ytIO.cpp:417`) -> `0x00678425`, a következő fájl.

## Amit ez a próba mér

Csak a viselkedést (cél tartalma, módbitek, tervezés, napló). Külön
felhasználói üzenetet az eredeti nem ad, ezt nem is mérjük.
"""

from __future__ import annotations

import logging
import os
import stat
from pathlib import Path

import pytest

from picasapy.backup import futtasd, tervezd_meg
from picasapy.index import open_index
from picasapy.index.backup_sets import keszlet_letrehozasa

# #1864: a `chmod` Windowson a POSIX-biteket nem érvényesíti, ezért a fájl
# minden próbája (az írásvédett forrás/cél a fixture-ben áll elő) csak
# POSIX-on fut. Rendszergazdán is fut: az írhatóságot a módbitből mérjük.
pytestmark = pytest.mark.skipif(
    os.name != "posix",
    reason="#1864: a chmod Windowson a POSIX-biteket nem érvényesíti",
)

_IRAS_BITEK = stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH


def _irasvedett(fajl: Path) -> None:
    fajl.chmod(fajl.stat().st_mode & ~_IRAS_BITEK)


def _irhato(fajl: Path) -> None:
    fajl.chmod(fajl.stat().st_mode | stat.S_IWUSR)


def _irhato_e(fajl: Path) -> bool:
    """A módbitből olvasva, nem `os.access`-szel: a root az írásvédettet is
    írja, így a hozzáférés-próba ott semmit nem mérne."""
    return bool(fajl.stat().st_mode & stat.S_IWUSR)


@pytest.fixture
def conn(tmp_path):
    with open_index(tmp_path / "index.db") as kapcsolat:
        yield kapcsolat


@pytest.fixture
def kornyezet(tmp_path, conn):
    """Egy írásvédett forrásfájl (`a.jpg`) és egy író (`b.jpg`), üres cél."""
    forras = tmp_path / "kepek"
    forras.mkdir()
    a = forras / "a.jpg"
    a.write_bytes(b"\xff\xd8\xff" + b"A" * 64)
    _irasvedett(a)
    (forras / "b.jpg").write_bytes(b"\xff\xd8\xff" + b"B" * 64)
    cel = tmp_path / "mentes"
    keszlet = keszlet_letrehozasa(conn, "Teszt", str(cel))
    return forras, cel, keszlet


def _terv(conn, keszlet, forras: Path):
    fajlok = sorted(p for p in forras.rglob("*") if p.is_file())
    return tervezd_meg(conn, keszlet, fajlok, gyokerek=[forras])


class TestAzIrasvedettForras:
    def test_a_masolat_NEM_orokli_az_irasvedettseget(self, conn, kornyezet):
        forras, cel, keszlet = kornyezet
        assert not _irhato_e(forras / "a.jpg"), "a próba előfeltétele"

        futtasd(conn, keszlet, _terv(conn, keszlet, forras))

        assert (cel / "a.jpg").is_file()
        assert _irhato_e(cel / "a.jpg"), "az írásvédett forrásból írásvédett cél lett"

    def test_a_tartalom_es_az_idok_atmennek(self, conn, kornyezet):
        """Módbit nélkül is: a tartalom és az idők a másolat részei."""
        forras, cel, keszlet = kornyezet
        os.utime(forras / "a.jpg", ns=(1_600_000_000_000_000_000,) * 2)

        futtasd(conn, keszlet, _terv(conn, keszlet, forras))

        celfajl = cel / "a.jpg"
        assert celfajl.read_bytes() == (forras / "a.jpg").read_bytes()
        assert celfajl.stat().st_mtime_ns == 1_600_000_000_000_000_000

    def test_a_modosult_kep_a_masodik_futasban_atmegy(self, conn, kornyezet):
        """Az M1 forgatókönyv: 1. futás mindent visz; a forrás módosul
        (írásvédetten marad); 2. futás pontosan azt az 1-et másolja át, a
        cél tartalma az új; a 3. terv üres."""
        forras, cel, keszlet = kornyezet
        elso = futtasd(conn, keszlet, _terv(conn, keszlet, forras))
        assert len(elso) == 2

        a = forras / "a.jpg"
        _irhato(a)
        a.write_bytes(b"\xff\xd8\xff" + b"UJ" * 40)
        _irasvedett(a)

        masodik_terv = _terv(conn, keszlet, forras)
        assert [f.forras.name for f in masodik_terv.fajlok] == ["a.jpg"]
        masodik = futtasd(conn, keszlet, masodik_terv)

        assert [p.name for p in masodik] == ["a.jpg"], "a módosult kép nem íródott át"
        assert (cel / "a.jpg").read_bytes() == a.read_bytes()
        assert _terv(conn, keszlet, forras).fajlok == (), (
            "a harmadik futás is újratervezi: a módosult fájl nem került "
            "a nyilvántartásba"
        )


class TestAzIrasvedettCel:
    def test_a_meglevo_irasvedett_cel_felulirodik(self, conn, kornyezet):
        """A célban már ott van egy írásvédett példány (pl. egy korábbi,
        hibás mentésből): az eredeti előbb írhatóvá teszi, aztán ír."""
        forras, cel, keszlet = kornyezet
        cel.mkdir(parents=True)
        regi = cel / "b.jpg"
        regi.write_bytes(b"regi tartalom")
        _irasvedett(regi)

        masoltak = futtasd(conn, keszlet, _terv(conn, keszlet, forras))

        assert regi in masoltak
        assert regi.read_bytes() == (forras / "b.jpg").read_bytes()
        assert _irhato_e(regi), "a felülírt cél írásvédett maradt"
        assert _terv(conn, keszlet, forras).fajlok == ()

    def test_az_irasvedett_cel_ini_is_felulirodik(self, conn, tmp_path):
        """A `.picasa.ini` másolata ugyanazon az úton megy, mint a képé."""
        forras = tmp_path / "kepek" / "nyaralas"
        forras.mkdir(parents=True)
        (forras / "a.jpg").write_bytes(b"\xff\xd8\xff" + b"A" * 64)
        ini = forras / ".picasa.ini"
        ini.write_text("[a.jpg]\nstar=yes\n", encoding="utf-8")
        cel = tmp_path / "mentes"
        keszlet = keszlet_letrehozasa(conn, "Teszt", str(cel))
        regi_ini = cel / "nyaralas" / ".picasa.ini"
        regi_ini.parent.mkdir(parents=True)
        regi_ini.write_text("[regi]\n", encoding="utf-8")
        _irasvedett(regi_ini)

        futtasd(conn, keszlet, _terv(conn, keszlet, tmp_path / "kepek"))

        assert "star=yes" in regi_ini.read_text(encoding="utf-8")


class TestASikertelenFajl:
    def _naplosor_a_fajlrol(self, caplog, fajlnev: str) -> bool:
        return any(
            fajlnev in rekord.getMessage()
            for rekord in caplog.records
            if rekord.levelno >= logging.WARNING
        )

    def test_az_eltunt_forras_naplosor_es_a_futas_folytatodik(
        self, conn, kornyezet, caplog
    ):
        """A tervezés és a másolás között eltűnt fájl (`OSError`): naplósor
        készül, a fájl nem kerül a nyilvántartásba, a többi viszont átmegy
        (`0x006783d9` -> `0x00678425`, a következő fájl)."""
        forras, _, keszlet = kornyezet
        terv = _terv(conn, keszlet, forras)
        (forras / "a.jpg").unlink()

        with caplog.at_level(logging.WARNING, logger="picasapy.backup.futtatas"):
            masoltak = futtasd(conn, keszlet, terv)

        assert [p.name for p in masoltak] == ["b.jpg"], "a futás megállt a hibánál"
        assert self._naplosor_a_fajlrol(caplog, "a.jpg"), (
            "a kimaradt fájlról nem készült naplósor"
        )
        assert [f.forras.name for f in _terv(conn, keszlet, forras).fajlok] == [], (
            "az eltűnt fájl nem tervezhető újra, a másik viszont be van jegyezve"
        )

    @pytest.mark.skipif(
        os.name == "nt" or (hasattr(os, "geteuid") and os.geteuid() == 0),
        reason="a nem írható mappa POSIX-on, nem root jogon mér",
    )
    def test_a_nem_irhato_cel_naplosor_es_a_futas_folytatodik(
        self, conn, tmp_path, caplog
    ):
        """Nem írható célmappa: a benne lévő fájl hibája naplósor lesz és
        nem kerül a nyilvántartásba; a másik mappa fájlja átmegy."""
        forras = tmp_path / "kepek"
        (forras / "x").mkdir(parents=True)
        (forras / "y").mkdir()
        (forras / "x" / "a.jpg").write_bytes(b"\xff\xd8\xff" + b"A" * 64)
        (forras / "y" / "b.jpg").write_bytes(b"\xff\xd8\xff" + b"B" * 64)
        cel = tmp_path / "mentes"
        keszlet = keszlet_letrehozasa(conn, "Teszt", str(cel))
        (cel / "x").mkdir(parents=True)
        (cel / "x").chmod(0o555)
        try:
            with caplog.at_level(logging.WARNING, logger="picasapy.backup.futtatas"):
                masoltak = futtasd(conn, keszlet, _terv(conn, keszlet, forras))
        finally:
            (cel / "x").chmod(0o755)

        assert [p.name for p in masoltak] == ["b.jpg"], "a futás megállt a hibánál"
        assert self._naplosor_a_fajlrol(caplog, "a.jpg")
        maradt = _terv(conn, keszlet, forras)
        assert [f.forras.name for f in maradt.fajlok] == ["a.jpg"]
