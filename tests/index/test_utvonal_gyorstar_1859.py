"""Az induláskori útvonal-feloldás gyorstára — #1859.

A `Path.resolve()` minden útvonal-komponensre rendszerhívást tesz (mérve:
gyökerenként 5, pontosan lineárisan), és ez MINDEN munkamenetben újrafut
ugyanazokra az útvonalakra. Helyi lemezen ingyen van; hálózati
megosztáson minden hívás körülfordulás — a tulajdonos a könyvtárát NAS-on
tartja.

## ⚠️ Amit a gyorstárnak KEZELNIE kell

A jegy három esetet nevez meg, mert egy elavult bejegyzés a #1667/#1560
védelmét lyukasztaná ki (egy védett mappa „idegennek" minősülne, és a
takarítás törölné az indexből):

1. szimbolikus link átirányítása,
2. NAS le-/felcsatolása (a feloldás hibázhat),
3. átnevezett/megszűnt exportcél.

Ezért a bejegyzés MINDKÉT végét azonosítjuk (`dev`/`ino`). A tesztek
lényege nem a gyorsulás, hanem hogy az EREDMÉNY soha nem különbözhet a
gyorstár nélkülitől.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from picasapy.index import open_index
from picasapy.index.sync import (
    _feloldas_gyorstarral,
    _resolved_protected_roots,
)


@pytest.fixture
def conn(tmp_path):
    with open_index(tmp_path / "index.db") as kapcsolat:
        yield kapcsolat


class TestAzEredmenyAZONOS:
    def test_elso_futas_ugyanazt_adja(self, conn, tmp_path):
        gyoker = tmp_path / "kepek"
        gyoker.mkdir()
        assert _feloldas_gyorstarral(conn, (str(gyoker),)) == (
            _resolved_protected_roots((str(gyoker),))
        )

    def test_masodik_futas_is_ugyanazt_adja(self, conn, tmp_path):
        """Ez a gyorstárazott ág — az eredménye bitre ugyanaz."""
        gyoker = tmp_path / "kepek"
        gyoker.mkdir()
        elso = _feloldas_gyorstarral(conn, (str(gyoker),))
        masodik = _feloldas_gyorstarral(conn, (str(gyoker),))
        assert masodik == elso == _resolved_protected_roots((str(gyoker),))

    def test_az_ismetlodo_nyers_utvonal_egyszer_szerepel(self, conn, tmp_path):
        gyoker = tmp_path / "kepek"
        gyoker.mkdir()
        assert len(_feloldas_gyorstarral(conn, (str(gyoker), str(gyoker)))) == 1

    def test_nem_letezo_utvonal_sem_dol_el(self, conn, tmp_path):
        nincs = tmp_path / "nincs-ilyen"
        assert _feloldas_gyorstarral(conn, (str(nincs),)) == (
            _resolved_protected_roots((str(nincs),))
        )


class TestAzElavulas:
    @pytest.mark.skipif(
        os.name != "posix", reason="szimbolikus link — POSIX-specifikus eset"
    )
    def test_a_link_ATIRANYITASA_utan_az_UJ_celt_adja(self, conn, tmp_path):
        """A jegy 1. esete, és a legveszélyesebb: a nyers útvonal ugyanaz,
        a feloldott más. Elavult gyorstárral egy védett mappa idegennek
        minősülne."""
        egy = tmp_path / "egy"
        ketto = tmp_path / "ketto"
        egy.mkdir()
        ketto.mkdir()
        link = tmp_path / "link"
        link.symlink_to(egy)

        elso = _feloldas_gyorstarral(conn, (str(link),))
        assert elso == (Path(str(egy.resolve())),)

        link.unlink()
        link.symlink_to(ketto)

        masodik = _feloldas_gyorstarral(conn, (str(link),))
        assert masodik == (Path(str(ketto.resolve())),)
        assert masodik == _resolved_protected_roots((str(link),))

    def test_a_MEGSZUNT_cel_nem_ad_gyorstar_talalatot(self, conn, tmp_path):
        """A jegy 3. esete: a gyorstárazott feloldás már nem létező helyre
        mutat. A friss feloldásnak kell nyernie."""
        gyoker = tmp_path / "export"
        gyoker.mkdir()
        _feloldas_gyorstarral(conn, (str(gyoker),))
        gyoker.rmdir()

        assert _feloldas_gyorstarral(conn, (str(gyoker),)) == (
            _resolved_protected_roots((str(gyoker),))
        )

    def test_az_UJRALETREHOZOTT_mappa_uj_azonossagot_kap(self, conn, tmp_path):
        """Törlés + újralétrehozás: ugyanaz az útvonal, MÁS inode. A
        gyorstár nem hihet a réginek."""
        gyoker = tmp_path / "export"
        gyoker.mkdir()
        _feloldas_gyorstarral(conn, (str(gyoker),))
        gyoker.rmdir()
        gyoker.mkdir()

        assert _feloldas_gyorstarral(conn, (str(gyoker),)) == (
            _resolved_protected_roots((str(gyoker),))
        )


class TestATablaHianya:
    def test_tabla_nelkul_is_mukodik(self, conn, tmp_path):
        """Régi index vagy félbemaradt migráció: a gyorstár származtatott
        adat, nélküle a régi út működik — nem kivétel."""
        gyoker = tmp_path / "kepek"
        gyoker.mkdir()
        conn.execute("DROP TABLE resolved_root_cache")
        conn.commit()

        assert _feloldas_gyorstarral(conn, (str(gyoker),)) == (
            _resolved_protected_roots((str(gyoker),))
        )


class TestANyereseg:
    def test_a_masodik_futas_KEVESEBB_rendszerhivast_tesz(
        self, conn, tmp_path, monkeypatch
    ):
        """A jegy célja. Nem időt mérünk (az terhelt gépen zajos), hanem a
        `stat` hívások SZÁMÁT — ahogy a #1706 mérése is tette."""
        gyoker = tmp_path / "a" / "b" / "c" / "kepek"
        gyoker.mkdir(parents=True)

        szamlalo = {"n": 0}

        #: ⚠️ MINDKÉT hívást számoljuk. A `Path.resolve()` a
        #: `posixpath.realpath`-on át `os.lstat`-ot hív komponensenként, a
        #: mi azonosság-ellenőrzésünk pedig `os.stat`-ot. Csak az egyiket
        #: figyelve a mérés hazudna: az első futás is „2 hívásnak"
        #: látszana, és a teszt fogatlan lenne.
        for nev in ("stat", "lstat"):
            eredeti = getattr(os, nev)

            def burok(*args, _eredeti=eredeti, **kwargs):
                szamlalo["n"] += 1
                return _eredeti(*args, **kwargs)

            monkeypatch.setattr(os, nev, burok)

        _feloldas_gyorstarral(conn, (str(gyoker),))
        elso = szamlalo["n"]
        szamlalo["n"] = 0
        _feloldas_gyorstarral(conn, (str(gyoker),))
        masodik = szamlalo["n"]

        assert masodik < elso, (
            f"a gyorstárazott futás nem lett olcsóbb: {masodik} ≥ {elso}"
        )
        #: A gyorstáras ág PONTOSAN két azonosság-ellenőrzés (nyers +
        #: feloldott) — az útvonal HOSSZÁTÓL függetlenül, szemben a
        #: feloldással, ami komponensenként fizet.
        assert masodik == 2
