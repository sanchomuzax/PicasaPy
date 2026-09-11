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


def _index_allapot(tmp_path) -> list[tuple[str, int, int]]:
    """(név, mtime_ns, méret) az indexből — a #2824 bukás-üzeneteihez.

    Az ingadozó bukás eddig csak annyit mondott, hogy `1 == 2`. Ez a
    segéd megmutatja, mit LÁTOTT az index abban a pillanatban, tehát a
    következő CI-bukás megkülönbözteti a szinkronizálás és a vezérlő
    hibáját."""
    with _index_conn(tmp_path) as conn:
        return [
            (sor[0], int(sor[1]), int(sor[2]))
            for sor in conn.execute(
                "SELECT name, mtime_ns, size FROM photos ORDER BY name"
            )
        ]


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
        nézni a képet.

        ⚠️ **#2824 — a próba INGADOZOTT a CI-n**, mindkét lábon (windows
        2026-09-11 19:46, ubuntu ugyanaznap 20:33), és helyben 14 futásból
        egyszer sem reprodukálható, terhelés alatt sem. A bukás alakja
        `1 == 2` volt: a detektor ÖSSZESEN egyszer futott, tehát vagy az
        ELSŐ, vagy a MÁSODIK menet maradt el.

        A két lehetőséget eddig semmi nem különböztette meg. Ezért a próba
        most **lépésenként** állít, és a bukás-üzenetben megmutatja az
        index állapotát — a következő CI-bukás így megmondja, melyik
        menetben és miért veszett el a hívás.
        """
        root = tmp_path / "kepek"
        root.mkdir()
        kep = root / "a.jpg"
        make_jpeg(kep)
        detektor = _FakeDetector()
        ctl = _make_controller(qt_app, tmp_path, root, detector=detektor)
        _run(ctl.scanFinished, ctl.scanForFaces)
        assert ctl.waitForBackgroundWorkers(5.0)
        # #2824: az ELSŐ menetnek le KELL futnia — ha nem, a hiba nem a
        # változás-felismerésben van, hanem abban, hogy a fotó még nem volt
        # az indexben a szkennelés pillanatában.
        assert len(detektor.calls) == 1, (
            f"az első menet {len(detektor.calls)} hívást adott 1 helyett — "
            f"az index tartalma: {_index_allapot(tmp_path)}"
        )

        # a fájl megváltozik, és az index is tudomást szerez róla
        make_jpeg(kep, size=(80, 60))
        uj = kep.stat()
        os.utime(kep, ns=(uj.st_mtime_ns + 1_000_000_000, uj.st_mtime_ns + 1_000_000_000))
        with _index_conn(tmp_path) as conn:
            from picasapy.index import sync_tree

            sync_tree(conn, root)
            conn.commit()

        # #2824: a MÁSODIK menet előfeltétele, hogy az index tényleg átvette
        # az új fájlállapotot. Ha nem, a detektor jogosan nem fut újra — és
        # akkor a hiba a szinkronizálásban van, nem a vezérlőben.
        allapot = _index_allapot(tmp_path)
        varhato = kep.stat()
        assert allapot and allapot[0][1] == varhato.st_mtime_ns, (
            "a szinkronizálás nem vette át az új fájlállapotot: "
            f"index={allapot}, fájl=(mtime_ns={varhato.st_mtime_ns}, "
            f"size={varhato.st_size})"
        )

        _run(ctl.scanFinished, ctl.scanForFaces)
        assert len(detektor.calls) == 2, (
            "a megváltozott fotót ÚJRA meg kell vizsgálni — a régi eredmény "
            f"másik tartalomra vonatkozott (index: {_index_allapot(tmp_path)})"
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
