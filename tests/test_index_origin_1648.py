"""#1648 — a „Másolat mentése" kimenete a FORRÁS származás-kulcsát örökli.

A lelet mérve van a tulajdonos élő Picasa-adatbázisán
(`research/testdata/1557-masolat-mentese/db3.zip`): négy, egymástól
bájtban eltérő másolat KÖZÖS `originfast` értéket kapott, és az az érték
a forrás saját bájtjaiból számolt kulcs. A mező tehát **származást**
azonosít, nem tartalmat.

Ezért ezek a tesztek szándékosan olyan másolatot használnak, amely
bájtban ELTÉR a forrástól — ha a kulcsot a másolat tartalmából
számolnánk, mindegyik esetben más érték jönne ki.
"""

from __future__ import annotations

import sqlite3

import pytest

from picasapy.dedup.fastkey import picasa_fast_key
from picasapy.index.origin import (
    ensure_origin_table,
    forget_origin_key,
    inherit_origin_key,
    origin_key,
)


@pytest.fixture()
def conn():
    kapcsolat = sqlite3.connect(":memory:")
    ensure_origin_table(kapcsolat)
    yield kapcsolat
    kapcsolat.close()


def _kep(utvonal, bajtok: bytes) -> None:
    utvonal.write_bytes(bajtok)


def test_orokles_nelkul_a_sajat_bajtokbol_szamol(tmp_path, conn):
    """Az öröklés a KIVÉTEL: aki nem kapott átvett kulcsot, a sajátját kapja."""
    kep = tmp_path / "kep.jpg"
    _kep(kep, b"A" * 5000)

    assert origin_key(conn, kep) == picasa_fast_key(kep)


def test_a_masolat_kulcsa_bitre_a_forrase_pedig_a_bajtok_elternek(tmp_path, conn):
    """A jegy fő állítása: az öröklött kulcs bitre a forrásé."""
    forras = tmp_path / "kep.jpg"
    masolat = tmp_path / "kep-001.jpg"
    _kep(forras, b"A" * 5000)
    # A másolatba a szerkesztés bele van égetve: más méret, más tartalom.
    _kep(masolat, b"B" * 7000)

    forras_kulcs = picasa_fast_key(forras)
    assert picasa_fast_key(masolat) != forras_kulcs, "a próba értelmetlen volna"

    inherit_origin_key(conn, masolat, forras_kulcs)

    assert origin_key(conn, masolat) == forras_kulcs


def test_tobb_masolat_ugyanazt_az_erteket_kapja(tmp_path, conn):
    """A mérésben NÉGY másolat osztozott egyetlen értéken."""
    forras = tmp_path / "chart.jpg"
    _kep(forras, b"A" * 5000)
    forras_kulcs = picasa_fast_key(forras)

    kulcsok = set()
    for sorszam in range(1, 5):
        masolat = tmp_path / f"chart-{sorszam:03d}.jpg"
        _kep(masolat, bytes([sorszam]) * (5000 + sorszam))
        inherit_origin_key(conn, masolat, forras_kulcs)
        kulcsok.add(origin_key(conn, masolat))

    assert kulcsok == {forras_kulcs}


def test_az_orokles_tuleli_a_masolat_ujrairasat(tmp_path, conn):
    """A kulcs a SZÁRMAZÁSÉ: a fájl későbbi módosítása nem írja felül."""
    forras = tmp_path / "kep.jpg"
    masolat = tmp_path / "kep-001.jpg"
    _kep(forras, b"A" * 5000)
    _kep(masolat, b"B" * 7000)
    forras_kulcs = picasa_fast_key(forras)
    inherit_origin_key(conn, masolat, forras_kulcs)

    _kep(masolat, b"C" * 9000)  # a felhasználó újra elmenti

    assert origin_key(conn, masolat) == forras_kulcs


def test_az_ujraorokles_felulirja_a_regi_erteket(tmp_path, conn):
    """Ugyanarra az útra készült ÚJ másolat új forrást kaphat."""
    masolat = tmp_path / "kep-001.jpg"
    _kep(masolat, b"B" * 7000)

    inherit_origin_key(conn, masolat, 111)
    inherit_origin_key(conn, masolat, 222)

    assert origin_key(conn, masolat) == 222


def test_a_torles_visszaadja_a_szamolt_kulcsot(tmp_path, conn):
    """Törlés/átnevezés után a fájl megint a sajátját kapja."""
    masolat = tmp_path / "kep-001.jpg"
    _kep(masolat, b"B" * 7000)
    inherit_origin_key(conn, masolat, 111)

    forget_origin_key(conn, masolat)

    assert origin_key(conn, masolat) == picasa_fast_key(masolat)


def test_hianyzo_fajlra_es_orokles_nelkul_nincs_kulcs(tmp_path, conn):
    """Olvashatatlan fájl + nincs öröklés → `None`, nem kivétel."""
    assert origin_key(conn, tmp_path / "nincs.jpg") is None


def test_hianyzo_fajlra_az_orokolt_kulcs_akkor_is_megvan(tmp_path, conn):
    """Az öröklött érték az INDEXBEN van — nem kell hozzá a fájl."""
    inherit_origin_key(conn, tmp_path / "nincs.jpg", 777)

    assert origin_key(conn, tmp_path / "nincs.jpg") == 777


@pytest.mark.parametrize(
    "kulcs",
    [
        0,
        1,
        (1 << 63) - 1,  # a legnagyobb, ami előjelesen is elfér
        1 << 63,  # az első, ami MÁR NEM fér el — innen kezdődött a hiba
        0x8637E41C12B8EAA,  # a #1648 mérésében szereplő valódi érték
        0xFFFFFFFFFFFFFFFF,  # a legnagyobb 64 bites
    ],
)
def test_a_teljes_64_bites_tartomany_visszaolvashato(tmp_path, conn, kulcs):
    """A kulcs ELŐJEL NÉLKÜLI 64 bites — az SQLite INTEGER előjeles.

    Fog: e nélkül a `1 << 63`-tól fölfelé eső értékek `OverflowError`-t
    dobtak beíráskor. A mért kulcsok fele ebbe a tartományba esik, tehát
    ez nem elméleti szélsőérték.
    """
    cel = tmp_path / "masolat.jpg"
    cel.write_bytes(b"x" * 100)

    inherit_origin_key(conn, cel, kulcs)

    assert origin_key(conn, cel) == kulcs


def test_a_relativ_es_az_abszolut_ut_ugyanaz_a_sor(tmp_path, conn, monkeypatch):
    """Az útvonal FELOLDVA kulcsol — különben két sor lenne egy fájlra."""
    cel = tmp_path / "masolat.jpg"
    cel.write_bytes(b"x" * 100)
    inherit_origin_key(conn, cel, 4242)

    monkeypatch.chdir(tmp_path)

    assert origin_key(conn, "masolat.jpg") == 4242
