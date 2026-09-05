"""A Picasa fej+farok GYORSKULCS tárolása az indexben (#1494).

A `picasa_fast_key()` eddig minden körben újraszámolt: két duplikátum-keresés
között semmi nem maradt meg, tehát a fej/farok ~33 KB-ot minden azonos méretű
jelöltre újra be kellett olvasni. A kulcs helye a `photo_hashes` tábla
`originfast` oszlopa — a dHash-gyorstár mellett, ugyanazzal a
fájl-azonosság-kulccsal (`útvonal, mtime_ns, méret`).

Az őr (`TestMegvaltozottFajl`) a jegy 4. pontja: megváltozott fájlnál a kulcs
ÚJRASZÁMOLÓDIK — a régi soha nem jön vissza. Egy elavult kulcs itt nem
kozmetikai hiba: a duplikátum-kezelő törlést ajánl rá (#287), az importálás
pedig szótlanul kihagyja a jelöltet (#441).
"""

import os
import sqlite3

import pytest

from picasapy.dedup.fastkey import picasa_fast_key
from picasapy.index import SCHEMA_VERSION, open_index
from picasapy.index.fast_key_source import IndexFastKeySource
from picasapy.index.hashes import (
    load_dhashes,
    load_fast_keys,
    save_dhashes,
    save_fast_keys,
)
from picasapy.index.schema import DDL


def _oszlopok(conn: sqlite3.Connection) -> set[str]:
    return {sor[1] for sor in conn.execute("PRAGMA table_info(photo_hashes)")}


class TestSema:
    def test_friss_adatbazisban_ott_az_originfast_oszlop(self, tmp_path):
        with open_index(tmp_path / "index.db") as conn:
            assert "originfast" in _oszlopok(conn)

    def test_a_dhash_oszlop_mar_lehet_null(self, tmp_path):
        """A gyorskulcs a dHash NÉLKÜL is tárolandó: az importálás
        duplikátum-szűrője (#441) soha nem számol dHash-t, tehát egy
        `NOT NULL` dhash-oszlop mellett a kulcsnak nem volna hova
        beírnia magát."""
        with open_index(tmp_path / "index.db") as conn:
            save_fast_keys(conn, [("/kepek/a.jpg", 1, 2, 0xABCD)])
            assert load_fast_keys(conn, [("/kepek/a.jpg", 1, 2)]) == {
                ("/kepek/a.jpg", 1, 2): 0xABCD
            }
            assert load_dhashes(conn, [("/kepek/a.jpg", 1, 2)]) == {}


class TestMigracio:
    """A v15-ös (originfast nélküli) index bővül, adatvesztés nélkül."""

    def _v15_adatbazis(self, tmp_path):
        path = tmp_path / "regi.db"
        raw = sqlite3.connect(path)
        raw.executescript(DDL)
        raw.executescript(
            "DROP TABLE photo_hashes;\n"
            "CREATE TABLE photo_hashes ("
            " path TEXT PRIMARY KEY,"
            " mtime_ns INTEGER NOT NULL,"
            " size INTEGER NOT NULL,"
            " dhash INTEGER NOT NULL);\n"
            "PRAGMA user_version = 15;"
        )
        raw.execute(
            "INSERT INTO photo_hashes(path, mtime_ns, size, dhash)"
            " VALUES ('/kepek/a.jpg', 11, 22, 7)"
        )
        raw.commit()
        raw.close()
        return path

    def test_a_verzio_emelkedik_es_az_oszlop_megjelenik(self, tmp_path):
        path = self._v15_adatbazis(tmp_path)
        with open_index(path) as conn:
            assert conn.execute("PRAGMA user_version").fetchone()[0] == SCHEMA_VERSION
            assert "originfast" in _oszlopok(conn)

    def test_a_meglevo_dhash_sorok_tulelik(self, tmp_path):
        path = self._v15_adatbazis(tmp_path)
        with open_index(path) as conn:
            assert load_dhashes(conn, [("/kepek/a.jpg", 11, 22)]) == {
                ("/kepek/a.jpg", 11, 22): 7
            }

    def test_a_meglevo_sorok_kulcsa_NULL_lal_indul(self, tmp_path):
        """A jegy 1. pontja: nincs újraszámolás a migrációkor — a meglévő
        sorok üres kulccsal indulnak, és lustán töltődnek fel."""
        path = self._v15_adatbazis(tmp_path)
        with open_index(path) as conn:
            assert load_fast_keys(conn, [("/kepek/a.jpg", 11, 22)]) == {}
            sor = conn.execute(
                "SELECT originfast FROM photo_hashes WHERE path = '/kepek/a.jpg'"
            ).fetchone()
            assert sor["originfast"] is None


class TestTarolas:
    def test_ismeretlen_kulcs_hianyzik(self, tmp_path):
        with open_index(tmp_path / "index.db") as conn:
            assert load_fast_keys(conn, [("/kepek/nincs.jpg", 1, 1)]) == {}

    def test_ures_bemenet_nem_csinal_semmit(self, tmp_path):
        with open_index(tmp_path / "index.db") as conn:
            save_fast_keys(conn, [])
            assert load_fast_keys(conn, []) == {}

    @pytest.mark.parametrize(
        "ertek", [0, 1, (1 << 63) - 1, 1 << 63, (1 << 64) - 1, 0xFFFFFFFF00000000]
    )
    def test_a_teljes_elojel_nelkuli_64_bit_atmegy(self, tmp_path, ertek):
        """A gyorskulcs ELŐJEL NÉLKÜLI 64 bites (`<Q`), az SQLite INTEGER
        viszont előjeles — a mért kulcsok nagyjából fele a felső félbe
        esik, tehát konverzió nélkül minden második kép kiesne."""
        with open_index(tmp_path / "index.db") as conn:
            save_fast_keys(conn, [("/kepek/a.jpg", 1, 1, ertek)])
            assert load_fast_keys(conn, [("/kepek/a.jpg", 1, 1)]) == {
                ("/kepek/a.jpg", 1, 1): ertek
            }

    def test_eltero_mtime_vagy_meret_ervenytelenit(self, tmp_path):
        with open_index(tmp_path / "index.db") as conn:
            save_fast_keys(conn, [("/kepek/a.jpg", 11, 22, 5)])
            assert load_fast_keys(conn, [("/kepek/a.jpg", 99, 22)]) == {}
            assert load_fast_keys(conn, [("/kepek/a.jpg", 11, 99)]) == {}

    def test_egy_utvonalhoz_egy_sor(self, tmp_path):
        with open_index(tmp_path / "index.db") as conn:
            save_fast_keys(conn, [("/kepek/a.jpg", 11, 22, 5)])
            save_fast_keys(conn, [("/kepek/a.jpg", 33, 44, 6)])
            assert conn.execute(
                "SELECT COUNT(*) FROM photo_hashes"
            ).fetchone()[0] == 1

    def test_sok_kulcs_nem_futtat_bele_a_parameter_korlatba(self, tmp_path):
        tetelek = [(f"/kepek/{i}.jpg", i, i, i) for i in range(5000)]
        with open_index(tmp_path / "index.db") as conn:
            save_fast_keys(conn, tetelek)
            kulcsok = [(ut, m, s) for ut, m, s, _ in tetelek]
            betoltve = load_fast_keys(conn, kulcsok)
        assert len(betoltve) == 5000
        assert betoltve[("/kepek/4999.jpg", 4999, 4999)] == 4999


class TestKetOszlopEgyutt:
    """A két gyorstár EGY soron osztozik — egyik írása nem ronthatja a másikat."""

    def test_a_kulcs_irasa_megtartja_a_dhasht(self, tmp_path):
        with open_index(tmp_path / "index.db") as conn:
            save_dhashes(conn, [("/kepek/a.jpg", 11, 22, 7)])
            save_fast_keys(conn, [("/kepek/a.jpg", 11, 22, 5)])
            assert load_dhashes(conn, [("/kepek/a.jpg", 11, 22)]) == {
                ("/kepek/a.jpg", 11, 22): 7
            }
            assert load_fast_keys(conn, [("/kepek/a.jpg", 11, 22)]) == {
                ("/kepek/a.jpg", 11, 22): 5
            }

    def test_a_dhash_irasa_megtartja_a_kulcsot(self, tmp_path):
        with open_index(tmp_path / "index.db") as conn:
            save_fast_keys(conn, [("/kepek/a.jpg", 11, 22, 5)])
            save_dhashes(conn, [("/kepek/a.jpg", 11, 22, 7)])
            assert load_fast_keys(conn, [("/kepek/a.jpg", 11, 22)]) == {
                ("/kepek/a.jpg", 11, 22): 5
            }

    def test_megvaltozott_fajl_dhashe_nem_hagyja_meg_a_regi_kulcsot(self, tmp_path):
        """A dHash-írás a MÁSIK oszlop érvényességéért is felel: ha a fájl
        azonossága közben megváltozott, a sorban maradó régi gyorskulcs
        idegen fájlra vonatkozna."""
        with open_index(tmp_path / "index.db") as conn:
            save_fast_keys(conn, [("/kepek/a.jpg", 11, 22, 5)])
            save_dhashes(conn, [("/kepek/a.jpg", 99, 22, 7)])
            assert load_fast_keys(conn, [("/kepek/a.jpg", 99, 22)]) == {}

    def test_megvaltozott_fajl_kulcsa_nem_hagyja_meg_a_regi_dhasht(self, tmp_path):
        with open_index(tmp_path / "index.db") as conn:
            save_dhashes(conn, [("/kepek/a.jpg", 11, 22, 7)])
            save_fast_keys(conn, [("/kepek/a.jpg", 99, 22, 5)])
            assert load_dhashes(conn, [("/kepek/a.jpg", 99, 22)]) == {}


def _kep(path, tartalom: bytes) -> None:
    path.write_bytes(tartalom)


class _CommitBukikKapcsolat:
    """A valódi kapcsolat, de a `commit()` zárolást jelez.

    Az `sqlite3.Connection.commit` írásvédett attribútum, tehát
    monkeypatchelni nem lehet — a hibás commit útját csak burkolóval lehet
    kipróbálni."""

    def __init__(self, conn):
        self._conn = conn

    def __getattr__(self, nev):
        return getattr(self._conn, nev)

    def commit(self):
        raise sqlite3.OperationalError("database is locked")


class TestIndexFastKeySource:
    """A lusta, index-háttérrel dolgozó kulcsforrás — ezt kapja a
    `dedup/exact.py` és az `importsource.py`."""

    def test_elso_kor_szamol_masodik_kor_az_indexbol_olvas(self, tmp_path):
        kep = tmp_path / "a.jpg"
        _kep(kep, b"x" * 50_000)
        db = tmp_path / "index.db"
        with open_index(db) as conn:
            elso = IndexFastKeySource(conn)
            assert elso(kep) == picasa_fast_key(kep)
            assert (elso.talalat, elso.szamolt) == (0, 1)
            elso.flush()
            conn.commit()
        with open_index(db) as conn:
            masodik = IndexFastKeySource(conn)
            assert masodik(kep) == picasa_fast_key(kep)
            assert (masodik.talalat, masodik.szamolt) == (1, 0)

    def test_koron_belul_sem_szamol_ketszer(self, tmp_path):
        kep = tmp_path / "a.jpg"
        _kep(kep, b"x" * 50_000)
        with open_index(tmp_path / "index.db") as conn:
            forras = IndexFastKeySource(conn)
            forras(kep)
            forras(kep)
            assert forras.szamolt == 1

    def test_olvashatatlan_fajl_None(self, tmp_path):
        with open_index(tmp_path / "index.db") as conn:
            forras = IndexFastKeySource(conn)
            assert forras(tmp_path / "nincs.jpg") is None
            forras.flush()
            assert conn.execute(
                "SELECT COUNT(*) FROM photo_hashes"
            ).fetchone()[0] == 0

    def test_ures_fajl_nem_kerul_a_gyorstarba(self, tmp_path):
        ures = tmp_path / "ures.jpg"
        ures.write_bytes(b"")
        with open_index(tmp_path / "index.db") as conn:
            forras = IndexFastKeySource(conn)
            assert forras(ures) is None
            forras.flush()
            assert conn.execute(
                "SELECT COUNT(*) FROM photo_hashes"
            ).fetchone()[0] == 0


class TestMegvaltozottFajl:
    """ŐR (#1494, a jegy 4. pontja): más `mtime_ns` → ÚJRASZÁMOLT kulcs.

    Az elavult kulcs visszaadása itt visszafordíthatatlan kárt okozna: a
    duplikátum-kezelő törlést ajánlana rá, az importálás pedig kihagyná
    a fényképet."""

    def test_a_megvaltozott_fajl_kulcsa_ujraszamolodik(self, tmp_path):
        kep = tmp_path / "a.jpg"
        _kep(kep, b"x" * 50_000)
        db = tmp_path / "index.db"
        with open_index(db) as conn:
            forras = IndexFastKeySource(conn)
            regi_kulcs = forras(kep)
            forras.flush()
            conn.commit()

        # ugyanaz a MÉRET, más tartalom és más mtime — a puszta útvonal-
        # egyezésre építő gyorstár itt adná vissza a régi kulcsot
        _kep(kep, b"y" * 50_000)
        os.utime(kep, ns=(0, 1_000_000_000))
        uj_kulcs = picasa_fast_key(kep)
        assert uj_kulcs != regi_kulcs, "a próba értelmetlen volna"

        with open_index(db) as conn:
            forras = IndexFastKeySource(conn)
            assert forras(kep) == uj_kulcs
            assert forras.szamolt == 1
            assert forras.talalat == 0

    def test_a_megvaltozott_fajl_sora_frissul_nem_halmozodik(self, tmp_path):
        kep = tmp_path / "a.jpg"
        _kep(kep, b"x" * 50_000)
        db = tmp_path / "index.db"
        with open_index(db) as conn:
            forras = IndexFastKeySource(conn)
            forras(kep)
            forras.flush()
            conn.commit()
        _kep(kep, b"y" * 60_000)
        with open_index(db) as conn:
            forras = IndexFastKeySource(conn)
            forras(kep)
            forras.flush()
            conn.commit()
            assert conn.execute(
                "SELECT COUNT(*) FROM photo_hashes"
            ).fetchone()[0] == 1
            assert load_fast_keys(
                conn, [(str(kep), kep.stat().st_mtime_ns, 60_000)]
            ) == {(str(kep), kep.stat().st_mtime_ns, 60_000): picasa_fast_key(kep)}


class TestFlushSzerzodes:
    """A `flush()` szerződése (#1494 átnézés, 1./2./5. lelet).

    Két, egymástól független ígéret, és mindkettő a FELHASZNÁLÓ kárát
    előzi meg:

    * **commitol** — enélkül az `executemany` után nyitva maradó írási zár
      a teljes összevetés idejére (kártyányi képnél percek) kizárná a többi
      írót az indexből (mappaszinkron, mentés, arckeresés);
    * **soha nem dob** — a gyorstár feltöltése kényelmi szolgáltatás; egy
      zárolt vagy tele index nem semmisítheti meg a KÉSZ eredményt (az
      "Exclude Duplicates" ilyenkor szótlanul üres halmazt adott, és a
      felhasználó újraimportálta a már meglévő képeit).
    """

    def test_a_flush_commitol_es_elengedi_az_irasi_zarat(self, tmp_path):
        kep = tmp_path / "a.jpg"
        _kep(kep, b"x" * 50_000)
        db = tmp_path / "index.db"
        with open_index(db) as conn:
            forras = IndexFastKeySource(conn)
            forras(kep)
            forras.flush()

            assert conn.in_transaction is False

            masik = sqlite3.connect(db)
            try:
                masik.execute("PRAGMA busy_timeout=300")
                masik.execute("CREATE TABLE proba_1494(x)")
                masik.commit()
            finally:
                masik.close()

    def test_a_kotegek_tartosan_kimennek_flush_kozben_is(self, tmp_path):
        """A `_FLUSH_MERET` ígérete („egy megszakított keresés munkája se
        vesszen el") CSAK commitolt kötegre igaz — commit nélkül a köteg
        egy nyitott tranzakcióban ülne a kör végéig."""
        kep = tmp_path / "a.jpg"
        _kep(kep, b"x" * 50_000)
        db = tmp_path / "index.db"
        with open_index(db) as conn:
            forras = IndexFastKeySource(conn)
            forras(kep)
            forras.flush()
            # a köteg egy MÁSIK kapcsolatból is látszik: tényleg kint van
            masik = sqlite3.connect(db)
            try:
                assert masik.execute(
                    "SELECT COUNT(*) FROM photo_hashes WHERE originfast IS NOT NULL"
                ).fetchone()[0] == 1
            finally:
                masik.close()

    def test_a_flush_nem_dob_ha_a_mentes_bukik(self, tmp_path, monkeypatch):
        kep = tmp_path / "a.jpg"
        _kep(kep, b"x" * 50_000)

        def bukik(*_args, **_kwargs):
            raise sqlite3.OperationalError("database is locked")

        monkeypatch.setattr(
            "picasapy.index.fast_key_source.save_fast_keys", bukik
        )
        with open_index(tmp_path / "index.db") as conn:
            forras = IndexFastKeySource(conn)
            ertek = forras(kep)
            forras.flush()  # nem dobhat
            assert ertek == picasa_fast_key(kep)
            assert conn.in_transaction is False

    def test_a_flush_nem_dob_ha_a_commit_bukik(self, tmp_path):
        """A KÉSZ eredményt a commit hibája sem viheti el — az 1. lelet
        pontosan itt bújt meg: a `save` védve volt, a `commit` nem."""
        kep = tmp_path / "a.jpg"
        _kep(kep, b"x" * 50_000)
        with open_index(tmp_path / "index.db") as conn:
            forras = IndexFastKeySource(_CommitBukikKapcsolat(conn))
            forras(kep)
            forras.flush()  # nem dobhat
            assert conn.in_transaction is False


class TestKapottAzonossag:
    """A hívó megadhatja a fájl-azonosságot (#1494 átnézés, 3. lelet).

    A `photo_hashes` KÉT oszlopa (dHash, gyorskulcs) egy soron osztozik, és
    minden írás NULL-ozza a párját, ha a sorban tárolt azonosság más. Két
    külön azonosság-forrásból a két gyorstár körönként váltakozva ürítené
    egymást — a megtakarítás épp a legdrágább képekre veszne el."""

    def test_a_kapott_azonossag_elsobbseget_elvez_a_stat_elott(self, tmp_path):
        kep = tmp_path / "a.jpg"
        _kep(kep, b"x" * 50_000)
        azonossag = (str(kep), 4242, 50_000)  # NEM a lemez mai mtime-ja
        with open_index(tmp_path / "index.db") as conn:
            forras = IndexFastKeySource(conn, {str(kep): azonossag})
            assert forras(kep) == picasa_fast_key(kep)
            forras.flush()
            assert load_fast_keys(conn, [azonossag]) == {
                azonossag: picasa_fast_key(kep)
            }

    def test_a_terkepben_nem_szereplo_fajlra_friss_stat_fut(self, tmp_path):
        kep = tmp_path / "a.jpg"
        _kep(kep, b"x" * 50_000)
        with open_index(tmp_path / "index.db") as conn:
            forras = IndexFastKeySource(conn, {"/mas/utvonal.jpg": ("/x", 1, 2)})
            assert forras(kep) == picasa_fast_key(kep)
            forras.flush()
            valodi = (str(kep), kep.stat().st_mtime_ns, 50_000)
            assert load_fast_keys(conn, [valodi]) == {valodi: picasa_fast_key(kep)}
