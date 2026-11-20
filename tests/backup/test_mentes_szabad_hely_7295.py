"""#7295: A biztonsági mentés másolás előtt ellenőrzi a szabad helyet.

Mappába mentésnél és lemezkép-írásnál, ha a cél szabad helye kisebb, mint a
terv összmérete, nem indul másolás, és a hivatalos szöveg jelenik meg.
A szabad hely mérése (shutil.disk_usage) modulszintű fogantyúval cserélhető.
"""

from __future__ import annotations

from collections import namedtuple
from pathlib import Path

import pytest

from picasapy.backup import MANIFESZT_NEVE, NincsElegendoHelyError, futtasd, tervezd_meg
from picasapy.backup.lemezkep import LemezkepTetel, lemezkepekbe
from picasapy.burn import CD
from picasapy.index import open_index
from picasapy.index.backup_sets import keszlet_letrehozasa
from support.jpeg_factory import make_jpeg

_Usage = namedtuple("_Usage", ["total", "used", "free"])


@pytest.fixture
def conn(tmp_path):
    with open_index(tmp_path / "index.db") as kapcsolat:
        yield kapcsolat


@pytest.fixture
def gyujtemeny(tmp_path):
    gyoker = tmp_path / "kepek"
    (gyoker / "album").mkdir(parents=True)
    make_jpeg(gyoker / "album" / "1.jpg")
    make_jpeg(gyoker / "album" / "2.jpg")
    return gyoker


def _fajlok(gyoker: Path) -> list[Path]:
    return sorted(p for p in gyoker.rglob("*") if p.is_file())


class TestSzabadHelyMappabaMentes:
    def test_keves_hely_eseten_nincs_masolas_es_kivetelt_dob(
        self, conn, tmp_path, gyujtemeny, monkeypatch
    ):
        from picasapy.backup import futtatas as futtatas_modul

        cel = tmp_path / "mentes_cel"
        keszlet = keszlet_letrehozasa(conn, "TesztKeszlet", str(cel))
        terv = tervezd_meg(conn, keszlet, _fajlok(gyujtemeny), gyokerek=[gyujtemeny])
        assert terv.osszes_bajt > 0

        # Szimulált kevés hely: kevesebb szabad hely, mint a terv mérete
        monkeypatch.setattr(
            futtatas_modul,
            "_disk_usage",
            lambda path: _Usage(total=10_000_000, used=9_999_999, free=terv.osszes_bajt - 1),
        )

        with pytest.raises(NincsElegendoHelyError):
            futtasd(conn, keszlet, terv)

        # Semmi sem másolódhatott át
        assert not (cel / "album" / "1.jpg").exists()
        assert not (cel / "album" / "2.jpg").exists()
        assert not (cel / MANIFESZT_NEVE).exists()

    def test_elegendo_hely_eseten_a_masolas_lefut(
        self, conn, tmp_path, gyujtemeny, monkeypatch
    ):
        from picasapy.backup import futtatas as futtatas_modul

        cel = tmp_path / "mentes_cel"
        keszlet = keszlet_letrehozasa(conn, "TesztKeszlet", str(cel))
        terv = tervezd_meg(conn, keszlet, _fajlok(gyujtemeny), gyokerek=[gyujtemeny])
        assert terv.osszes_bajt > 0

        monkeypatch.setattr(
            futtatas_modul,
            "_disk_usage",
            lambda path: _Usage(total=10_000_000, used=0, free=terv.osszes_bajt + 1024),
        )

        masoltak = futtasd(conn, keszlet, terv)
        assert len(masoltak) == len(terv.fajlok)
        assert (cel / "album" / "1.jpg").exists()


class TestSzabadHelyLemezkep:
    def test_keves_hely_eseten_nem_keszul_lemezkep_es_kivetelt_dob(
        self, tmp_path, gyujtemeny, monkeypatch
    ):
        from picasapy.backup import lemezkep as lemezkep_modul

        cel = tmp_path / "iso_cel"
        fajlok = _fajlok(gyujtemeny)
        tetelek = [
            LemezkepTetel(relativ=Path(f.name), forras=f, meret=f.stat().st_size)
            for f in fajlok
        ]
        osszes_bajt = sum(t.meret for t in tetelek)
        assert osszes_bajt > 0

        monkeypatch.setattr(
            lemezkep_modul,
            "_disk_usage",
            lambda path: _Usage(total=10_000_000, used=9_999_999, free=osszes_bajt - 1),
        )

        with pytest.raises(NincsElegendoHelyError):
            lemezkepekbe(tetelek, cel, media=CD)

        # Nem készülhetett ISO fájl
        assert list(cel.glob("*.iso")) == []

    def test_elegendo_hely_eseten_a_lemezkep_elkeszul(
        self, tmp_path, gyujtemeny, monkeypatch
    ):
        from picasapy.backup import lemezkep as lemezkep_modul

        cel = tmp_path / "iso_cel"
        fajlok = _fajlok(gyujtemeny)
        tetelek = [
            LemezkepTetel(relativ=Path(f.name), forras=f, meret=f.stat().st_size)
            for f in fajlok
        ]
        osszes_bajt = sum(t.meret for t in tetelek)

        monkeypatch.setattr(
            lemezkep_modul,
            "_disk_usage",
            lambda path: _Usage(total=10_000_000, used=0, free=osszes_bajt + 1024),
        )

        eredmeny = lemezkepekbe(tetelek, cel, media=CD)
        assert len(eredmeny.kepek) > 0
        assert all(p.is_file() for p in eredmeny.kepek)
