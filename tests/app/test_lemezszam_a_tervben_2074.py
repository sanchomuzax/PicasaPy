"""#2074: a mentés TERVE megmondja, hány lemezre férne.

A kapacitás-képlet próbái a `tests/burn/` alatt futnak (Qt nélkül); ez a
fájl a VEZÉRLŐ oldala, ezért kell hozzá a `qt_app` fixture.

Az eredeti is megmutatja a becslést („Est. %d CDs or %d DVDs"), mielőtt a
felhasználó belefog a másolásba.
"""

from __future__ import annotations


class TestATervbenIsLatszik:
    """A mentés TERVE megmondja, hány lemezre férne — az eredeti is
    megmutatja („Est. %d CDs or %d DVDs")."""

    def test_a_terv_lemezszamot_is_ad(self, qt_app, tmp_path):
        from picasapy.app.backup_controller import BackupController
        from picasapy.index import open_index
        from picasapy.index.backup_sets import keszlet_letrehozasa

        forras = tmp_path / "kepek"
        forras.mkdir()
        (forras / "a.jpg").write_bytes(b"\xff\xd8\xff" + b"x" * 4096)
        db = tmp_path / "index.db"
        with open_index(db) as conn:
            keszlet_id = keszlet_letrehozasa(
                conn, "T", str(tmp_path / "cel")
            ).id
            conn.commit()
        ctl = BackupController(db, (str(forras),))
        ctl._jeloltek = lambda: (str(forras / "a.jpg"),)

        terv = ctl.terv(keszlet_id)

        assert terv["cd"] == 1 and terv["dvd"] == 1, (
            f"a terv nem ad lemezszámot: {terv}"
        )

    def test_URES_tervnel_nulla_lemez(self, qt_app, tmp_path):
        from picasapy.app.backup_controller import BackupController
        from picasapy.index import open_index
        from picasapy.index.backup_sets import keszlet_letrehozasa

        db = tmp_path / "index.db"
        with open_index(db) as conn:
            keszlet_id = keszlet_letrehozasa(
                conn, "T", str(tmp_path / "cel")
            ).id
            conn.commit()
        ctl = BackupController(db, (str(tmp_path),))
        ctl._jeloltek = lambda: ()

        terv = ctl.terv(keszlet_id)

        assert terv["cd"] == 0 and terv["dvd"] == 0
