"""#2543 — a rekurzív bejárás nem old fel útvonalat mappánként újra.

## A mérés (a #2483 mérőmódszerével: `os.*` becsomagolva, a hívások a
hívási helyre visszavezetve; 50 mappás fa = 101 könyvtár)

| | fs-hívás | ebből `lstat` (= `resolve()`) |
|---|---|---|
| a javítás ELŐTT | **1921** | **1718 (89 %)** |
| a javítás UTÁN | **221** | **18** |

Két forrásból jött a felesleg:

1. az `is_path_excluded` **kétszer** futott ugyanarra a mappára — egyszer a
   szülő leszálló hurkában, egyszer a hívott `_walk` első soraiban;
2. a vizsgálat MINDEN mappára újra feloldotta az útvonalat, holott a
   bejárás a gyökértől lefelé kanonikus útvonalakon halad.

## ⚠️ Amit ez az őr valójában véd

A gyorsítás önmagában nem érdekes — a KIZÁRÁS ÍTÉLETE nem változhat tőle.
A `scanner/` sávhatára ezt külön mért állításként kéri (a NÉV-alapú és az
ELŐTAG-alapú kizárás külön), és a `..`-os, illetve a symlinkes hívószövegre
is kanonikus indexsort kell adnia — különben a rövidzár némán MÁS mappát
zárna ki.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

from picasapy.scanner import scan_tree
from picasapy.scanner.name_filters import NameFilters


def _fa(gyoker: Path, mappak: int = 3) -> None:
    for i in range(mappak):
        m = gyoker / f"m{i}"
        m.mkdir(parents=True, exist_ok=True)
        (m / "k.jpg").write_bytes(b"\xff\xd8\xff\xe0" + b"0" * 64)


def _utak(eredmeny) -> set[str]:
    return {str(f.path) for f in eredmeny}


class TestAzItéletVáltozatlan:
    """A rövidzár nem írhatja felül, MIT zárunk ki."""

    def test_elotagos_kizaras_a_rovidzar_mellett_is_hat(self, tmp_path):
        gyoker = tmp_path / "fa"
        _fa(gyoker)
        (gyoker / "m1" / "mely").mkdir()
        (gyoker / "m1" / "mely" / "k.jpg").write_bytes(b"\xff\xd8\xff\xe0" + b"0" * 64)

        szuro = NameFilters(path_prefix_filters=(str(gyoker / "m1"),))
        utak = _utak(scan_tree(gyoker, name_filters=szuro))

        assert str(gyoker / "m0") in utak
        assert not any("m1" in Path(u).parts for u in utak), (
            f"az útvonal-előtagos kizárás nem hatott: {sorted(utak)}"
        )

    def test_nev_alapu_kizaras_valtozatlan(self, tmp_path):
        gyoker = tmp_path / "fa"
        _fa(gyoker)
        (gyoker / "Originals").mkdir()
        (gyoker / "Originals" / "k.jpg").write_bytes(b"\xff\xd8\xff\xe0" + b"0" * 64)

        utak = _utak(scan_tree(gyoker))

        assert not any("Originals" in Path(u).parts for u in utak)

    def test_az_exclude_lista_valtozatlan(self, tmp_path):
        gyoker = tmp_path / "fa"
        _fa(gyoker)
        utak = _utak(scan_tree(gyoker, exclude=[gyoker / "m2"]))
        assert str(gyoker / "m2") not in utak
        assert str(gyoker / "m0") in utak


class TestKanonikusIndexsor:
    """A hívószöveg alakja nem szivároghat be az eredménybe."""

    def test_pont_pont_os_hivoszoveg_kanonikus_sort_ad(self, tmp_path):
        gyoker = tmp_path / "fa"
        _fa(gyoker)
        (tmp_path / "mellek").mkdir()

        egyenes = _utak(scan_tree(gyoker))
        kerulo = _utak(scan_tree(tmp_path / "mellek" / ".." / "fa"))

        assert kerulo == egyenes, (
            "a `..`-os hívószöveg NEM kanonikus indexsort adott:\n"
            f"  egyenes: {sorted(egyenes)}\n  kerülő:  {sorted(kerulo)}"
        )

    @pytest.mark.skipif(sys.platform.startswith("win"), reason="POSIX symlink")
    def test_symlinkes_hivoszoveg_kanonikus_sort_ad(self, tmp_path):
        gyoker = tmp_path / "fa"
        _fa(gyoker)
        link = tmp_path / "link"
        os.symlink(gyoker, link)

        egyenes = _utak(scan_tree(gyoker))
        linken_at = _utak(scan_tree(link))

        assert linken_at == egyenes, (
            "a symlinkes hívószöveg NEM a cél kanonikus útvonalát adta:\n"
            f"  egyenes:   {sorted(egyenes)}\n  linken át: {sorted(linken_at)}"
        )

    @pytest.mark.skipif(sys.platform.startswith("win"), reason="POSIX symlink")
    def test_symlinkes_ALMAPPA_kizarasa_is_hat(self, tmp_path):
        """A kanonikusság-jelző symlinknél KIKAPCSOL — enélkül a link
        útvonalát hasonlítanánk a feloldott előtaghoz, és a kizárás némán
        elmaradna."""
        gyoker = tmp_path / "fa"
        _fa(gyoker, mappak=1)
        titkos = tmp_path / "titkos"
        titkos.mkdir()
        (titkos / "k.jpg").write_bytes(b"\xff\xd8\xff\xe0" + b"0" * 64)
        os.symlink(titkos, gyoker / "link")

        szuro = NameFilters(path_prefix_filters=(str(titkos),))
        utak = _utak(scan_tree(gyoker, name_filters=szuro))

        assert str(gyoker / "m0") in utak
        # ⚠️ SZEGMENSRE nézünk, nem részsztringre: az ideiglenes mappa neve
        # („test_symlinkes_…") maga is tartalmazza a „link" szót, és a naiv
        # `in` erre hamis riasztást adott.
        tiltott = {"link", "titkos"}
        assert not any(tiltott & set(Path(u).parts) for u in utak), (
            f"a symlinken át elért, KIZÁRT mappa bekerült: {sorted(utak)}"
        )


class TestAFeloldasSzamaCSOKKENT:
    """A jegy fő állítása, mérve — nem becsülve."""

    def test_mappankent_legfeljebb_egy_feloldas(self, tmp_path, monkeypatch):
        gyoker = tmp_path / "fa"
        _fa(gyoker, mappak=8)
        for i in range(8):
            also = gyoker / f"m{i}" / "also"
            also.mkdir()
            (also / "k.jpg").write_bytes(b"\xff\xd8\xff\xe0" + b"0" * 64)

        szamlalo = {"lstat": 0}
        eredeti = os.lstat

        def burok(*a, **k):
            szamlalo["lstat"] += 1
            return eredeti(*a, **k)

        monkeypatch.setattr(os, "lstat", burok)
        eredmeny = scan_tree(gyoker)
        monkeypatch.undo()

        mappak = len(eredmeny)
        assert mappak == 16, f"a próba fája nem 16 mappás: {mappak}"
        # a javítás előtt ez ~270 volt (mappánként két teljes feloldás);
        # a bejárás maga egyetlen `lstat`-ot sem igényel
        assert szamlalo["lstat"] < 2 * mappak, (
            f"{szamlalo['lstat']} `lstat` hívás {mappak} mappára — a bejárás "
            "továbbra is mappánként old fel útvonalat"
        )
