"""A bejáró NYILVÁNTARTJA a hibás bejegyzéseket (#1998).

## A lelet

A `scanner/walker.py` hét helyen fogott `OSError`-t, és mind a hét
**jelzés nélkül** tért vissza. A felhasználó annyit látott, hogy egy
mappa vagy egy kép „nincs ott" — és semmi nem mondta meg, miért.
(`grep -rn "badfile" src/` → nulla találat.)

## Az eredeti

A Picasa könyvtárbejárója minden bejegyzéshez tárol egy `Type` mezőt,
aminek **4 = hibás fájl**, **5 = hibás mappa** értéke van, és kérésre
kilistázza őket (`badfiles.txt`, `0x004f25f0`; a két sorformátum
`%s (badfile)` / `%s (baddirectory)`, `0x004f2a58` és `0x004f2aaa`).

⚠️ **Ez a jegy NEM a `badfiles.txt` lemásolásáról szól.** Az eredeti
formátuma azt bizonyítja, hogy a bejáró **egyáltalán számon tartja** a
hibát — nálunk ez a fogalom nem létezett. A mi kimenetünk: naplósor +
a hívónak átadott lista.

## A foga

A gyűjtésnek a hibátlan fát VÁLTOZATLANUL kell hagynia — ezért van
külön eset arra, hogy hibamentes bejáráson a lista üres, és hogy az
eredmény ugyanaz, mint gyűjtő nélkül.
"""

from __future__ import annotations

import errno
import logging
import os
import stat as stat_module

import pytest

from picasapy.scanner.walker import HibasBejegyzes, scan_tree

from support.jpeg_factory import make_jpeg


@pytest.fixture
def fa(tmp_path):
    """Két mappa képekkel — az egyiket a teszt teszi olvashatatlanná."""
    (tmp_path / "jo").mkdir()
    (tmp_path / "rossz").mkdir()
    make_jpeg(tmp_path / "jo" / "a.jpg")
    make_jpeg(tmp_path / "rossz" / "b.jpg")
    return tmp_path


def _olvashatatlanna(path):
    eredeti = os.stat(path).st_mode
    os.chmod(path, 0o000)
    return lambda: os.chmod(path, stat_module.S_IMODE(eredeti))


class TestAHibatlanFa:
    def test_ures_a_lista(self, fa):
        hibak: list[HibasBejegyzes] = []
        scan_tree(fa, hibas_bejegyzesek=hibak)
        assert hibak == []

    def test_az_eredmeny_valtozatlan_gyujtovel_es_nelkule(self, fa):
        """A foga: ha a gyűjtés bármit megváltoztatna a bejáráson, ez
        bukik."""
        gyujtovel = scan_tree(fa, hibas_bejegyzesek=[])
        nelkule = scan_tree(fa)
        assert [f.path for f in gyujtovel] == [f.path for f in nelkule]
        assert [tuple(f.files) for f in gyujtovel] == [
            tuple(f.files) for f in nelkule
        ]


@pytest.mark.skipif(os.getuid() == 0, reason="root mindent olvashat")
class TestAzOlvashatatlanMappa:
    def test_bekerul_a_listaba_MAPPAKENT(self, fa):
        vissza = _olvashatatlanna(fa / "rossz")
        try:
            hibak: list[HibasBejegyzes] = []
            scan_tree(fa, hibas_bejegyzesek=hibak)
        finally:
            vissza()
        assert len(hibak) == 1, f"pontosan egy hibás elemet vártunk: {hibak}"
        assert hibak[0].path == fa / "rossz"
        assert hibak[0].mappa is True, "a mappa-hibát fájlként vettük fel"
        assert hibak[0].errno == errno.EACCES

    def test_a_TOBBI_mappa_bejarasa_folytatodik(self, fa):
        """Egy olvashatatlan mappa nem buktathatja el a bejárást."""
        vissza = _olvashatatlanna(fa / "rossz")
        try:
            scans = scan_tree(fa, hibas_bejegyzesek=[])
        finally:
            vissza()
        assert any(s.path == fa / "jo" for s in scans)

    def test_NAPLOZ_is(self, fa, caplog):
        vissza = _olvashatatlanna(fa / "rossz")
        try:
            with caplog.at_level(logging.WARNING, logger="picasapy.scanner.walker"):
                scan_tree(fa, hibas_bejegyzesek=[])
        finally:
            vissza()
        assert any("rossz" in r.message for r in caplog.records), (
            "az olvashatatlan mappáról nincs naplósor"
        )

    def test_gyujto_NELKUL_is_naploz(self, fa, caplog):
        """A napló nem függhet attól, hogy a hívó kért-e listát."""
        vissza = _olvashatatlanna(fa / "rossz")
        try:
            with caplog.at_level(logging.WARNING, logger="picasapy.scanner.walker"):
                scan_tree(fa)
        finally:
            vissza()
        assert any("rossz" in r.message for r in caplog.records)


class TestAzElerhetetlenFAJL:
    """A `Type = 4` megfelelője: a bejegyzés hibás, de FÁJL.

    Kiváltó eset: törött symlink médiakiterjesztéssel. A listázás
    megtalálja, a `stat()` viszont a nem létező célra fut."""

    def test_bekerul_a_listaba_FAJLKENT(self, fa):
        (fa / "jo" / "torott.jpg").symlink_to(fa / "jo" / "nincs-ilyen.jpg")
        hibak: list[HibasBejegyzes] = []
        scan_tree(fa, hibas_bejegyzesek=hibak)
        assert len(hibak) == 1, f"pontosan egy hibás elemet vártunk: {hibak}"
        assert hibak[0].mappa is False, "a fájl-hibát mappaként vettük fel"
        assert str(hibak[0].path).endswith("torott.jpg")
        assert hibak[0].errno == errno.ENOENT

    def test_a_TOBBI_kep_bekerul(self, fa):
        """Egy törött symlink nem viheti el a mappa többi képét."""
        (fa / "jo" / "torott.jpg").symlink_to(fa / "jo" / "nincs-ilyen.jpg")
        scans = scan_tree(fa, hibas_bejegyzesek=[])
        jo = next(s for s in scans if s.path == fa / "jo")
        assert [f.name for f in jo.files] == ["a.jpg"]


class TestAzElemLeirasa:
    def test_a_mappa_es_a_fajl_MEGKULONBOZTETHETO(self):
        """A `Type` 4/5 megfelelője nálunk: a `mappa` mező."""
        fajl = HibasBejegyzes(path=os.curdir, errno=errno.EACCES, mappa=False)
        mappa = HibasBejegyzes(path=os.curdir, errno=errno.EACCES, mappa=True)
        assert fajl.mappa is False and mappa.mappa is True


@pytest.mark.skipif(os.getuid() == 0, reason="root mindent olvashat")
class TestAzOSSZESITO_JELZES:
    """A hosszú scan naplójában az egyedi sorok elvesznek — a szinkron
    ezért egy összesítő sort is ad (#1998, „a felhasználó lát valamit")."""

    def test_a_sync_kiirja_a_DARABSZAMOT(self, fa, tmp_path, caplog):
        from picasapy.index import open_index, sync_tree

        vissza = _olvashatatlanna(fa / "rossz")
        try:
            with caplog.at_level(logging.WARNING, logger="picasapy.index.sync"):
                with open_index(tmp_path / "x.db") as conn:
                    sync_tree(conn, fa)
        finally:
            vissza()
        osszesito = [
            r for r in caplog.records if "nem tudott feldolgozni" in r.message
        ]
        assert osszesito, "a szinkron nem adott összesítő jelzést"
        szoveg = osszesito[0].getMessage()
        assert "1 elemet" in szoveg, szoveg
        assert "(1 mappa, 0 fájl)" in szoveg, (
            f"a mappa/fájl bontás hiányzik vagy hibás: {szoveg}"
        )
