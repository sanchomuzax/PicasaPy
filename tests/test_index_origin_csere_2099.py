"""#2099 — a kicserélt fájl NEM örökölhet idegen származást.

A #2038 takarítása akkor veszi ki az `origin_keys` sorát, ha a fájl eltűnt
a mappából ÉS nincs a lemezen. Ha a törölt fájl helyére a következő
szinkron előtt ÚJ fájl kerül ugyanazzal a névvel, a név szerepel a
listában és a fájl létezik — a régi sor tehát megmaradt, és az új kép
idegen származást örökölt.

A megoldás **horgony**: `anchor_size` + `anchor_mtime_ns`. A szinkron
lehorgonyoz, és minden későbbi futásnál összeveti; eltérésre az öröklés
törlődik. A döntés indoklása a jegyben.

⚠️ A két irányt EGYÜTT kell mérni. A „felejtsd el, ha változott" szabály
önmagában triviálisan teljesíthető úgy, hogy MINDIG felejtünk — a
`TestAJogosOroklesTuleli` osztály épp ezt zárja ki.
"""

from __future__ import annotations

import os
import sqlite3

import pytest

from picasapy.dedup.fastkey import picasa_fast_key
from picasapy.index.origin import (
    ensure_origin_table,
    forget_origin_keys_outside,
    inherit_origin_key,
    origin_key,
)


@pytest.fixture()
def conn():
    kapcsolat = sqlite3.connect(":memory:")
    ensure_origin_table(kapcsolat)
    yield kapcsolat
    kapcsolat.close()


def _ir(ut, bajtok: bytes, mtime_ns: int | None = None) -> None:
    ut.write_bytes(bajtok)
    if mtime_ns is not None:
        os.utime(ut, ns=(mtime_ns, mtime_ns))


def _szinkron(conn, mappa) -> None:
    """A mappa-szinkron origin-lépése: ezt hívja a `sync.py`."""
    forget_origin_keys_outside(
        conn, mappa, [b.name for b in mappa.iterdir() if b.is_file()]
    )


class TestACsereElvesziAzOroklest:
    def test_ujrairt_fajl_a_SAJAT_kulcsat_kapja(self, tmp_path, conn):
        """A jegy fő esete: törlés → ÚJ fájl ugyanazon a néven."""
        forras = tmp_path / "forras.jpg"
        _ir(forras, b"F" * 4000)
        masolat = tmp_path / "masolat.jpg"
        _ir(masolat, b"M" * 5000, mtime_ns=1_000_000_000_000_000_000)
        inherit_origin_key(conn, masolat, picasa_fast_key(forras))
        _szinkron(conn, tmp_path)
        assert origin_key(conn, masolat) == picasa_fast_key(forras)

        # a felhasználó kitörli, és ugyanoda MÁS fájlt tesz
        masolat.unlink()
        _ir(masolat, b"X" * 7000, mtime_ns=2_000_000_000_000_000_000)
        _szinkron(conn, tmp_path)

        assert origin_key(conn, masolat) == picasa_fast_key(masolat), (
            "az új fájl megörökölte a törölt fájl idegen származását"
        )

    def test_a_MERET_egyezese_sem_ment_meg(self, tmp_path, conn):
        """Azonos méretű csere: csak az mtime árulkodik."""
        forras = tmp_path / "forras.jpg"
        _ir(forras, b"F" * 4000)
        masolat = tmp_path / "masolat.jpg"
        _ir(masolat, b"M" * 5000, mtime_ns=1_000_000_000_000_000_000)
        inherit_origin_key(conn, masolat, picasa_fast_key(forras))
        _szinkron(conn, tmp_path)

        masolat.unlink()
        _ir(masolat, b"X" * 5000, mtime_ns=2_000_000_000_000_000_000)
        _szinkron(conn, tmp_path)

        assert origin_key(conn, masolat) == picasa_fast_key(masolat)

    def test_az_MTIME_egyezese_sem_ment_meg(self, tmp_path, conn):
        """Azonos mtime-ú csere: csak a méret árulkodik. Ezért `vagy`,
        nem `és` — külön-külön egyik jel sem elég."""
        forras = tmp_path / "forras.jpg"
        _ir(forras, b"F" * 4000)
        masolat = tmp_path / "masolat.jpg"
        _ir(masolat, b"M" * 5000, mtime_ns=1_000_000_000_000_000_000)
        inherit_origin_key(conn, masolat, picasa_fast_key(forras))
        _szinkron(conn, tmp_path)

        masolat.unlink()
        _ir(masolat, b"X" * 9000, mtime_ns=1_000_000_000_000_000_000)
        _szinkron(conn, tmp_path)

        assert origin_key(conn, masolat) == picasa_fast_key(masolat)


class TestAJogosOroklesTuleli:
    """Az ellenkező irány — enélkül a fenti három úgy is zöld lenne, hogy
    az öröklést MINDIG eldobjuk."""

    def test_a_friss_orokles_tuleli_a_kovetkezo_szinkront(
        self, tmp_path, conn
    ):
        forras = tmp_path / "forras.jpg"
        _ir(forras, b"F" * 4000)
        masolat = tmp_path / "masolat.jpg"
        _ir(masolat, b"M" * 5000)
        inherit_origin_key(conn, masolat, picasa_fast_key(forras))

        _szinkron(conn, tmp_path)

        assert origin_key(conn, masolat) == picasa_fast_key(forras), (
            "a közvetlenül a kiírás utáni szinkron eldobta a jogos öröklést"
        )

    def test_tobb_szinkron_utan_is_megmarad(self, tmp_path, conn):
        forras = tmp_path / "forras.jpg"
        _ir(forras, b"F" * 4000)
        masolat = tmp_path / "masolat.jpg"
        _ir(masolat, b"M" * 5000)
        inherit_origin_key(conn, masolat, picasa_fast_key(forras))
        for _ in range(5):
            _szinkron(conn, tmp_path)
        assert origin_key(conn, masolat) == picasa_fast_key(forras)

    def test_a_KIIRAS_ELOTTI_orokles_is_tuleli(self, tmp_path, conn):
        """A modul fejléce szerint a sorrend nem garantált: az öröklés a
        fájl kiírása ELŐTT is beírható. Ilyenkor a horgony NULL, és az
        első szinkron horgonyoz le."""
        forras = tmp_path / "forras.jpg"
        _ir(forras, b"F" * 4000)
        masolat = tmp_path / "masolat.jpg"
        inherit_origin_key(conn, masolat, picasa_fast_key(forras))
        _ir(masolat, b"M" * 5000)

        _szinkron(conn, tmp_path)
        _szinkron(conn, tmp_path)

        assert origin_key(conn, masolat) == picasa_fast_key(forras)


class TestAzElhagyottSorTovabbraIsTorlodik:
    def test_a_nyomtalanul_eltunt_fajl_sora_kimegy(self, tmp_path, conn):
        """A #2038 viselkedése nem romolhat el."""
        forras = tmp_path / "forras.jpg"
        _ir(forras, b"F" * 4000)
        masolat = tmp_path / "masolat.jpg"
        _ir(masolat, b"M" * 5000)
        inherit_origin_key(conn, masolat, picasa_fast_key(forras))
        _szinkron(conn, tmp_path)

        masolat.unlink()
        _szinkron(conn, tmp_path)

        assert conn.execute(
            "SELECT COUNT(*) FROM origin_keys WHERE path LIKE ?",
            (f"%{masolat.name}",),
        ).fetchone()[0] == 0


class TestARegiSemaMigracioja:
    """A #2099 előtti index táblája kétoszlopos. A `CREATE TABLE IF NOT
    EXISTS` egy MEGLÉVŐ táblát nem bővít — enélkül a régi index némán a
    régi sémával futna, és a csere-felismerés csendben hatástalan lenne."""

    def test_a_ket_oszlopos_tabla_kiegeszul(self, tmp_path):
        kapcsolat = sqlite3.connect(":memory:")
        kapcsolat.execute(
            "CREATE TABLE origin_keys (path TEXT PRIMARY KEY, "
            "origin_key INTEGER NOT NULL)"
        )
        forras = tmp_path / "forras.jpg"
        _ir(forras, b"F" * 4000)
        masolat = tmp_path / "masolat.jpg"
        _ir(masolat, b"M" * 5000)
        kapcsolat.execute(
            "INSERT INTO origin_keys(path, origin_key) VALUES (?, ?)",
            (str(masolat.resolve()), picasa_fast_key(forras)),
        )

        ensure_origin_table(kapcsolat)

        oszlopok = {
            sor[1] for sor in kapcsolat.execute("PRAGMA table_info(origin_keys)")
        }
        assert {"anchor_size", "anchor_mtime_ns"} <= oszlopok
        # a régi sor megmaradt, és lehorgonyzás után túléli a szinkront
        _szinkron(kapcsolat, tmp_path)
        assert origin_key(kapcsolat, masolat) == picasa_fast_key(forras)
        masolat.unlink()
        _ir(masolat, b"X" * 7000, mtime_ns=2_000_000_000_000_000_000)
        _szinkron(kapcsolat, tmp_path)
        assert origin_key(kapcsolat, masolat) == picasa_fast_key(masolat)
        kapcsolat.close()
