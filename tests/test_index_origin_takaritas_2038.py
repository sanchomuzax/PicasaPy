"""#2038: az `origin_keys` tábla TAKARÍTÁSA.

A #1648 bevezette a származás-kulcs öröklését, útvonalra kulcsolva — a
takarítás kimaradt. Ha egy másolatot törölnek vagy átneveznek, a sor ott
marad; egy később ugyanoda kerülő, teljesen MÁS kép ezért idegen származást
örökölne.

Az őrök a VALÓDI belépési ponton mennek végig (`index/sync.py`), nem a
`fileops/` felől: a fájl eltűnhet a kukába dobással, átnevezéssel, vagy a
felhasználó fájlkezelőjéből is — mindegyik útnak a mappa-szinkron a közös
végpontja.
"""

from __future__ import annotations

import sqlite3

import pytest

from picasapy.index.origin import (
    ensure_origin_table,
    forget_origin_keys_outside,
    inherit_origin_key,
    origin_key,
)


@pytest.fixture
def conn() -> sqlite3.Connection:
    kapcsolat = sqlite3.connect(":memory:")
    ensure_origin_table(kapcsolat)
    yield kapcsolat
    kapcsolat.close()


def _kep(ut, bajtok: bytes = b"\xff\xd8kep") -> None:
    ut.write_bytes(bajtok)


class TestEltuntFajlSora:
    def test_az_eltunt_fajl_sora_KIVESZ(self, conn, tmp_path):
        """A mappában maradt nevek listája a mérce — ami nincs benne, megy."""
        maradt, eltunt = tmp_path / "maradt.jpg", tmp_path / "eltunt.jpg"
        inherit_origin_key(conn, maradt, 0x1111)
        inherit_origin_key(conn, eltunt, 0x2222)

        forget_origin_keys_outside(conn, tmp_path, ["maradt.jpg"])

        sorok = dict(conn.execute("SELECT path, origin_key FROM origin_keys"))
        assert str(maradt.resolve()) in sorok
        assert str(eltunt.resolve()) not in sorok

    def test_a_helyere_kerulo_UJ_fajl_a_SAJAT_kulcsat_kapja(self, conn, tmp_path):
        """Ez a jegy tényleges kára: a takarítás nélkül az új kép az ELŐZŐ
        lakó idegen származását viselné."""
        ut = tmp_path / "kep.jpg"
        inherit_origin_key(conn, ut, 0x08637E41C12B8EAA)

        forget_origin_keys_outside(conn, tmp_path, [])  # a fájl eltűnt
        _kep(ut, b"\xff\xd8egeszen mas tartalom")  # más fájl került a helyére

        sajat = origin_key(conn, ut)
        assert sajat is not None
        assert sajat != 0x08637E41C12B8EAA

    def test_az_ALMAPPAK_sorai_MEGMARADNAK(self, conn, tmp_path):
        """Buktató: egy naiv előtag-szűrés az almappák sorait is elvinné,
        pedig azokat egy másik mappa szinkronja kezeli."""
        almappa = tmp_path / "alma"
        almappa.mkdir()
        melyebb = almappa / "melyebb.jpg"
        inherit_origin_key(conn, melyebb, 0x3333)

        forget_origin_keys_outside(conn, tmp_path, [])

        assert conn.execute(
            "SELECT 1 FROM origin_keys WHERE path = ?", (str(melyebb.resolve()),)
        ).fetchone() is not None

    def test_a_SZAZALEKJEL_a_mappanevben_nem_visz_felre(self, conn, tmp_path):
        """A `%` és a `_` az SQL `LIKE` joker-karakterei. Ha a takarítás
        `LIKE`-kal szűrne, egy ilyen nevű mappa IDEGEN sorokat is elvinne."""
        furcsa = tmp_path / "100%_nyar"
        masik = tmp_path / "100X-nyar"
        furcsa.mkdir()
        masik.mkdir()
        idegen = masik / "kep.jpg"
        inherit_origin_key(conn, idegen, 0x4444)
        inherit_origin_key(conn, furcsa / "sajat.jpg", 0x5555)

        forget_origin_keys_outside(conn, furcsa, [])

        assert conn.execute(
            "SELECT 1 FROM origin_keys WHERE path = ?", (str(idegen.resolve()),)
        ).fetchone() is not None


class TestNemUjraszamolhatoAdat:
    def test_a_LETEZO_fajl_sora_akkor_is_marad_ha_kimaradt_a_listabol(
        self, conn, tmp_path
    ):
        """Az `origin_keys` NEM újraszámolható (ld. `index/origin.py` fejléc):
        ha elveszik, a fájlból nem állítható vissza. Egy átmeneti hiba miatt
        üres névlista ezért nem vihet el létező fájlhoz tartozó sort."""
        ut = tmp_path / "megvan.jpg"
        _kep(ut)
        inherit_origin_key(conn, ut, 0x7777)

        forget_origin_keys_outside(conn, tmp_path, [])  # „üres" scan

        assert origin_key(conn, ut) == 0x7777


class TestASzinkronVegigviszi:
    """A VALÓDI úton: nem a takarító függvényt hívjuk, hanem szinkronizálunk.

    A #1743 tanulsága szerint a köztes függvény közvetlen hívása zöld maradhat
    egy be nem kötött vagy rosszul bekötött lánc fölött.
    """

    def test_a_torolt_masolat_sora_a_szinkron_utan_eltunik(self, tmp_path):
        from picasapy.index import open_index, sync_tree

        gyoker = tmp_path / "kepek"
        gyoker.mkdir()
        forras = gyoker / "eredeti.jpg"
        masolat = gyoker / "eredeti-1.jpg"
        _kep(forras, b"\xff\xd8forras")
        _kep(masolat, b"\xff\xd8masolat, mas bajtok")

        with open_index(tmp_path / "index.db") as kapcsolat:
            sync_tree(kapcsolat, gyoker)
            inherit_origin_key(kapcsolat, masolat, 0x08637E41C12B8EAA)
            assert origin_key(kapcsolat, masolat) == 0x08637E41C12B8EAA

            masolat.unlink()  # a felhasználó törli
            sync_tree(kapcsolat, gyoker)

            _kep(masolat, b"\xff\xd8teljesen mas kep kerult ide")
            uj = origin_key(kapcsolat, masolat)
            assert uj is not None
            assert uj != 0x08637E41C12B8EAA, (
                "a szinkron nem takarította ki a törölt másolat sorát, "
                "ezért az új kép idegen származást örökölt (#2038)"
            )

    def test_a_MEGLEVO_masolat_orokleset_a_szinkron_NEM_bantja(self, tmp_path):
        """Ellenkező irányú őr: a takarítás ne vigye el a jó adatot."""
        from picasapy.index import open_index, sync_tree

        gyoker = tmp_path / "kepek"
        gyoker.mkdir()
        masolat = gyoker / "eredeti-1.jpg"
        _kep(masolat, b"\xff\xd8masolat")

        with open_index(tmp_path / "index.db") as kapcsolat:
            sync_tree(kapcsolat, gyoker)
            inherit_origin_key(kapcsolat, masolat, 0x1234)
            sync_tree(kapcsolat, gyoker)
            assert origin_key(kapcsolat, masolat) == 0x1234
