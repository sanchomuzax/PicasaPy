"""A második szkennelés NEM detektál újra (#2519).

A `face` tábla csak a megtalált arcokat tárolja, ezért egy arc nélküli fotó
megkülönböztethetetlen volt a még sosem vizsgálttól: a detektálás minden
szkennelésnél újrafutott rajta. A `face_scan` tábla (`index/faces_detected.py`)
fotónkénti nyomot hagy; ez a lap azt méri, hogy a vezérlő HASZNÁLJA is.

A mérce a detektor HÍVÁSAINAK SZÁMA (`_FakeDetector.calls`) — nem a
lefutás ideje: az idő a gép terhelésétől függ, a hívásszám nem.
"""

from __future__ import annotations

import os

from support.jpeg_factory import make_jpeg

from tests.app.test_face_scan_controller import _FakeDetector, _make_controller, _run


def _index_conn(tmp_path):
    from picasapy.index import open_index

    return open_index(tmp_path / "index.db")


class TestMasodikMenet:
    def test_a_valtozatlan_fotot_nem_vizsgalja_ujra(self, qt_app, tmp_path):
        root = tmp_path / "kepek"
        root.mkdir()
        make_jpeg(root / "a.jpg")
        detektor = _FakeDetector()
        ctl = _make_controller(qt_app, tmp_path, root, detector=detektor)

        _run(ctl.scanFinished, ctl.scanForFaces)
        assert ctl.waitForBackgroundWorkers(5.0)
        elso = len(detektor.calls)
        assert elso == 1, "az első menetnek meg kell néznie a fotót"

        arrived, args = _run(ctl.scanFinished, ctl.scanForFaces)
        assert arrived is True
        assert len(detektor.calls) == elso, (
            f"a második menet ÚJRA lefuttatta a detektálást "
            f"({len(detektor.calls)} hívás {elso} helyett) — a `face_scan` "
            f"jelölést nem nézi a vezérlő"
        )
        _found, scanned = args
        assert scanned == 0, "a második menet egyetlen fotót sem vizsgált meg újra"
        assert ctl.waitForBackgroundWorkers(5.0)

    def test_az_arc_nelkuli_foto_sem_fut_ujra(self, qt_app, tmp_path):
        """Ez a jegy MAGVA: pont az arc nélküli fotó volt megkülönböztethetetlen
        a még sosem vizsgálttól."""
        root = tmp_path / "kepek"
        root.mkdir()
        make_jpeg(root / "a.jpg")
        detektor = _FakeDetector()
        detektor.detect = lambda image: (detektor.calls.append(image), ())[1]
        ctl = _make_controller(qt_app, tmp_path, root, detector=detektor)

        _run(ctl.scanFinished, ctl.scanForFaces)
        assert ctl.waitForBackgroundWorkers(5.0)
        assert len(detektor.calls) == 1
        with _index_conn(tmp_path) as conn:
            assert conn.execute("SELECT COUNT(*) FROM face").fetchone()[0] == 0
            assert conn.execute("SELECT COUNT(*) FROM face_scan").fetchone()[0] == 1

        _run(ctl.scanFinished, ctl.scanForFaces)
        assert len(detektor.calls) == 1, (
            "az arc NÉLKÜLI fotón is újrafutott a detektálás — a nyom nélkül "
            "pontosan ez volt a hiba"
        )
        assert ctl.waitForBackgroundWorkers(5.0)

    def test_a_MEGVALTOZOTT_fotot_ujra_vizsgalja(self, qt_app, tmp_path):
        """A jelölés a fájl azonosságához kötött: szerkesztés után újra kell
        nézni a képet."""
        root = tmp_path / "kepek"
        root.mkdir()
        kep = root / "a.jpg"
        make_jpeg(kep)
        detektor = _FakeDetector()
        ctl = _make_controller(qt_app, tmp_path, root, detector=detektor)
        _run(ctl.scanFinished, ctl.scanForFaces)
        assert ctl.waitForBackgroundWorkers(5.0)

        # a fájl megváltozik, és az index is tudomást szerez róla
        make_jpeg(kep, size=(80, 60))
        uj = kep.stat()
        os.utime(kep, ns=(uj.st_mtime_ns + 1_000_000_000, uj.st_mtime_ns + 1_000_000_000))
        with _index_conn(tmp_path) as conn:
            from picasapy.index import sync_tree

            sync_tree(conn, root)
            conn.commit()

        _run(ctl.scanFinished, ctl.scanForFaces)
        assert len(detektor.calls) == 2, (
            "a megváltozott fotót ÚJRA meg kell vizsgálni — a régi eredmény "
            "másik tartalomra vonatkozott"
        )
        assert ctl.waitForBackgroundWorkers(5.0)

    def test_a_kizart_fotot_nem_vizsgalja(self, qt_app, tmp_path):
        """A `kizarva` jelölés az eredeti `facerect = 1`-ének megfelelője: a
        kizárt mappa képeit a szkennelés meg sem nézi."""
        from picasapy.index.faces_detected import mark_folder_excluded

        root = tmp_path / "kepek"
        root.mkdir()
        make_jpeg(root / "a.jpg")
        detektor = _FakeDetector()
        ctl = _make_controller(qt_app, tmp_path, root, detector=detektor)
        with _index_conn(tmp_path) as conn:
            assert mark_folder_excluded(conn, str(root)) == 1
            conn.commit()

        _run(ctl.scanFinished, ctl.scanForFaces)
        assert detektor.calls == [], (
            "a kizárt mappa fotóján lefutott a detektálás"
        )
        assert ctl.waitForBackgroundWorkers(5.0)
