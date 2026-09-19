"""#2074 — a mentés lemezképbe: az ISO-író és a lemezekre osztás.

A tulajdonos 2026-09-18-án a **(b)** ágat választotta: „a gyűjtemény mentése
több lemezképre". A számoló réteg (`burn`) a v0.8.432 óta megvolt; ami
hiányzott, az a KIMENET.

## Miért `7z` a mérce

⛔ Egy saját ISO-olvasóval való összevetés **önigazolás** volna: ugyanaz a
félreértés mindkét oldalon ugyanúgy jelenne meg. A próbák ezért a `7z`-vel
(p7zip — teljesen független megvalósítás) olvassák vissza a képet: az adja a
könyvtárneveket, a fájlneveket ÉS a bájtokat.

A `7z` hiánya ezért NEM „akkor hagyjuk ki": a fájl elején álló őr megbukik,
ha nincs — egy csendben kihagyott ellenőrzés rosszabb, mint a bukás
(`a-kornyezetfuggo-skip-nem-or`).
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

from picasapy.backup.lemezkep import LemezkepTetel, lemezkepekbe
from picasapy.burn import CD, DVD, KETRETEGU, hasznalhato_kapacitas
from picasapy.burn.iso import iso_kiirasa

_HETZ = shutil.which("7z") or shutil.which("7za")


def _kicsomagol(kep: Path, cel: Path) -> None:
    """A képet FÜGGETLEN megvalósítással bontjuk ki."""
    assert _HETZ, (
        "nincs `7z` a gépen — az ISO-író ellenőrzése így nem mérés, hanem "
        "önigazolás lenne; telepítsd a p7zip-et (a CI telepíti)"
    )
    cel.mkdir(parents=True, exist_ok=True)
    kesz = subprocess.run(
        [_HETZ, "x", "-y", f"-o{cel}", str(kep)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=120,
    )
    assert kesz.returncode == 0, kesz.stdout + kesz.stderr


@pytest.fixture
def minta(tmp_path: Path) -> Path:
    """Kis gyűjtemény: két mappa, ékezetes nevek, egy `.picasa.ini`."""
    gyoker = tmp_path / "gyujtemeny"
    (gyoker / "2020" / "nyár").mkdir(parents=True)
    (gyoker / "2021").mkdir(parents=True)
    (gyoker / "2020" / "nyár" / "árvíztűrő.jpg").write_bytes(bytes(range(256)) * 20)
    (gyoker / "2020" / "nyár" / ".picasa.ini").write_text(
        "[árvíztűrő.jpg]\nstar=yes\n", encoding="utf-8"
    )
    (gyoker / "2021" / "kép.png").write_bytes(b"PNG" * 1000)
    return gyoker


def _tetelek(gyoker: Path) -> list[LemezkepTetel]:
    return [
        LemezkepTetel(
            relativ=ut.relative_to(gyoker), forras=ut, meret=ut.stat().st_size
        )
        for ut in sorted(gyoker.rglob("*"))
        if ut.is_file() and ut.name != ".picasa.ini"
    ]


class TestAMertKapacitas:
    """A képlet HÁROM küszöbe — pontosan a mért bájtszámokkal."""

    def test_cd(self):
        # 700 MB-os CD: 360 000 szektor × 2048 − 409 600
        assert hasznalhato_kapacitas(CD, szektorszam=360_000) == 736_870_400

    def test_dvd(self):
        # 4,7 GB-os DVD: 2 295 104 szektor × 2048 − 4 096 000
        assert hasznalhato_kapacitas(DVD, szektorszam=2_295_104) == 4_696_276_992

    def test_ketretegu_ROGZITETT(self):
        """A kétrétegűt a bináris közvetlenül adja vissza (`0x0066bed3`)."""
        assert hasznalhato_kapacitas(KETRETEGU) == 8_547_991_552
        assert hasznalhato_kapacitas(KETRETEGU, szektorszam=7) == 8_547_991_552


class TestAKiirtKep:
    def test_a_fa_es_a_NEVEK_megmaradnak(self, minta, tmp_path):
        kep = iso_kiirasa(
            [
                ("2020/nyár/árvíztűrő.jpg", minta / "2020" / "nyár" / "árvíztűrő.jpg"),
                ("2021/kép.png", minta / "2021" / "kép.png"),
            ],
            tmp_path / "proba.iso",
        )
        ki = tmp_path / "ki"
        _kicsomagol(kep, ki)
        assert (ki / "2020" / "nyár" / "árvíztűrő.jpg").is_file()
        assert (ki / "2021" / "kép.png").is_file()

    def test_a_BAJTOK_azonosak(self, minta, tmp_path):
        forras = minta / "2020" / "nyár" / "árvíztűrő.jpg"
        kep = iso_kiirasa([("kep.jpg", forras)], tmp_path / "b.iso")
        ki = tmp_path / "ki"
        _kicsomagol(kep, ki)
        assert (ki / "kep.jpg").read_bytes() == forras.read_bytes()

    def test_az_URES_fajl_sem_vesz_el(self, tmp_path):
        ures = tmp_path / "ures.txt"
        ures.write_bytes(b"")
        kep = iso_kiirasa([("ures.txt", ures)], tmp_path / "u.iso")
        ki = tmp_path / "ki"
        _kicsomagol(kep, ki)
        assert (ki / "ures.txt").is_file()
        assert (ki / "ures.txt").read_bytes() == b""

    def test_a_kep_szektorhataron_vegzodik(self, minta, tmp_path):
        kep = iso_kiirasa(
            [("a.jpg", minta / "2020" / "nyár" / "árvíztűrő.jpg")],
            tmp_path / "s.iso",
        )
        assert kep.stat().st_size % 2048 == 0


class TestATobbLemez:
    def test_egy_lemez_ha_elfer(self, minta, tmp_path):
        eredmeny = lemezkepekbe(
            _tetelek(minta), tmp_path / "ki", media=DVD, szektorszam=2_295_104
        )
        assert len(eredmeny.kepek) == 1
        assert eredmeny.kepek[0].name == "picasapy-mentes-01.iso"
        assert eredmeny.tulcsordulo == ()

    def test_TOBB_lemez_es_a_sorszamozas(self, minta, tmp_path):
        """Szűk kapacitás: a fájlok külön lemezekre esnek, sorszámozva."""
        eredmeny = lemezkepekbe(
            _tetelek(minta), tmp_path / "ki", media=CD, szektorszam=201
        )
        assert [k.name for k in eredmeny.kepek] == [
            "picasapy-mentes-01.iso",
            "picasapy-mentes-02.iso",
        ]
        assert sum(eredmeny.darabok) == len(_tetelek(minta))

    def test_minden_lemez_KULON_is_kibonthato(self, minta, tmp_path):
        eredmeny = lemezkepekbe(
            _tetelek(minta), tmp_path / "ki", media=CD, szektorszam=201
        )
        talalt: set[str] = set()
        for index, kep in enumerate(eredmeny.kepek):
            ki = tmp_path / f"ki{index}"
            _kicsomagol(kep, ki)
            talalt |= {
                ut.relative_to(ki).as_posix()
                for ut in ki.rglob("*")
                if ut.is_file()
            }
        assert "2020/nyár/árvíztűrő.jpg" in talalt
        assert "2021/kép.png" in talalt

    def test_a_picasa_ini_a_kepei_MELLE_kerul(self, minta, tmp_path):
        eredmeny = lemezkepekbe(
            _tetelek(minta), tmp_path / "ki", media=DVD, szektorszam=2_295_104
        )
        ki = tmp_path / "ki-bontva"
        _kicsomagol(eredmeny.kepek[0], ki)
        ini = ki / "2020" / "nyár" / ".picasa.ini"
        assert ini.is_file(), "a mentés nem önmagában teljes értékű archívum"
        assert "star=yes" in ini.read_text(encoding="utf-8")

    def test_MANIFESZT_van_minden_lemez_gyokereben(self, minta, tmp_path):
        eredmeny = lemezkepekbe(
            _tetelek(minta), tmp_path / "ki", media=CD, szektorszam=201
        )
        for index, kep in enumerate(eredmeny.kepek):
            ki = tmp_path / f"m{index}"
            _kicsomagol(kep, ki)
            manifeszt = ki / "files.txt"
            assert manifeszt.is_file(), f"{kep.name}: nincs manifeszt"
            assert manifeszt.read_text(encoding="utf-8").strip()

    def test_a_koztes_manifeszt_NEM_marad_a_celmappaban(self, minta, tmp_path):
        cel = tmp_path / "ki"
        lemezkepekbe(_tetelek(minta), cel, media=CD, szektorszam=201)
        assert sorted(ut.name for ut in cel.iterdir()) == [
            "picasapy-mentes-01.iso",
            "picasapy-mentes-02.iso",
        ]

    def test_a_lemeznel_NAGYOBB_fajlt_kimondja(self, minta, tmp_path):
        eredmeny = lemezkepekbe(
            _tetelek(minta), tmp_path / "ki", media=CD, szektorszam=200
        )
        assert eredmeny.tulcsordulo, (
            "a lemezre nem férő fájl némán túlcsordult volna"
        )
