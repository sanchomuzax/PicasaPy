"""DedupController: a duplikátum-kezelő ablak (#287) QML-hídja a
`picasapy.dedup.find_duplicates` mag fölött — valódi ideiglenes
könyvtárfán/indexen, mock nélkül."""

from __future__ import annotations

import os
import sqlite3

import numpy as np
import pytest
from PIL import Image
from PySide6.QtCore import QEventLoop, QTimer

from picasapy.index import open_index, sync_tree
from picasapy.thumbs import ThumbnailCache

from support.jpeg_factory import make_jpeg


def _quit_on(signal):
    loop = QEventLoop()
    signal.connect(loop.quit)
    QTimer.singleShot(5000, loop.quit)
    return loop


def _gradient_jpeg(path, size=(64, 64)):
    """Folytonos szürkeárnyalatos színátmenet — a dHash-nek van mit
    megkülönböztetnie (a sima, egyszínű teszt-JPEG-ekkel ellentétben)."""
    width, height = size
    xs = np.linspace(0, 255, width, dtype=np.uint8)
    ys = np.linspace(0, 255, height, dtype=np.uint8)
    ramp = (xs[np.newaxis, :].astype(np.uint16) + ys[:, np.newaxis]) // 2
    rgb = np.stack([ramp] * 3, axis=-1).astype(np.uint8)
    Image.fromarray(rgb, "RGB").save(path, "JPEG", quality=90)
    return path


def _resaved_jpeg(source_path, target_path, size=(24, 24), quality=60):
    """A forrás átméretezve/újratömörítve — "hasonló, de nem bitre azonos"."""
    with Image.open(source_path) as image:
        image.resize(size, Image.BICUBIC).save(target_path, "JPEG", quality=quality)
    return target_path


@pytest.fixture
def provider(tmp_path):
    from picasapy.app.thumbnail_provider import ThumbnailProvider

    return ThumbnailProvider(ThumbnailCache(tmp_path / "thumbs", size=32))


@pytest.fixture
def make_controller(qt_app):
    """`DedupController`-gyár, ami a teszt végén MEGVÁRJA a háttérszálakat
    (#438, a #430 SIGSEGV-osztály elkerülése — a `test_webexport_
    controller.py` mintája)."""
    from picasapy.app.dedup_controller import DedupController

    created = []

    def _make(db_path, provider):
        dedup = DedupController(db_path, provider)
        created.append(dedup)
        return dedup

    yield _make

    for dedup in created:
        assert dedup.waitForBackgroundWorkers(30.0), (
            "a dedup-keresés háttérszála nem állt le"
        )


@pytest.fixture
def controller(make_controller, tmp_path, provider):
    return make_controller(tmp_path / "index.db", provider)


class TestScanForDuplicates:
    def test_finds_exact_duplicate_group_with_thumb_urls(
        self, make_controller, tmp_path, provider
    ):

        lib = tmp_path / "kepek"
        lib.mkdir()
        original = make_jpeg(lib / "a.jpg", size=(40, 20))
        (lib / "b.jpg").write_bytes(original.read_bytes())
        db = tmp_path / "index.db"
        with open_index(db) as conn:
            sync_tree(conn, lib)

        dedup = make_controller(db, provider)
        results = []
        dedup.scanFinished.connect(lambda groups: results.append(groups))
        loop = _quit_on(dedup.scanFinished)
        dedup.scanForDuplicates()
        loop.exec()

        assert len(results) == 1
        groups = results[0]
        assert isinstance(groups, list)
        exact = [g for g in groups if g["kind"] == "exact"]
        assert len(exact) == 1
        paths = {item["path"] for item in exact[0]["items"]}
        assert paths == {str(lib / "a.jpg"), str(lib / "b.jpg")}
        for item in exact[0]["items"]:
            assert item["thumbUrl"].startswith("image://thumbs/")
            assert item["thumbUrl"] != "image://thumbs/"

    def test_finds_similar_group_for_resized_variant(self, make_controller, tmp_path, provider):

        lib = tmp_path / "kepek"
        lib.mkdir()
        _gradient_jpeg(lib / "eredeti.jpg", size=(256, 256))
        _resaved_jpeg(lib / "eredeti.jpg", lib / "atmeretezett.jpg")
        db = tmp_path / "index.db"
        with open_index(db) as conn:
            sync_tree(conn, lib)

        dedup = make_controller(db, provider)
        results = []
        dedup.scanFinished.connect(lambda groups: results.append(groups))
        loop = _quit_on(dedup.scanFinished)
        dedup.scanForDuplicates()
        loop.exec()

        groups = results[0]
        similar = [g for g in groups if g["kind"] == "similar"]
        assert len(similar) == 1
        assert similar[0]["maxDistance"] >= 0
        paths = {item["path"] for item in similar[0]["items"]}
        assert paths == {str(lib / "eredeti.jpg"), str(lib / "atmeretezett.jpg")}

    def test_no_duplicates_yields_empty_list(self, make_controller, tmp_path, provider):

        lib = tmp_path / "kepek"
        lib.mkdir()
        make_jpeg(lib / "egyedi.jpg", size=(40, 20))
        db = tmp_path / "index.db"
        with open_index(db) as conn:
            sync_tree(conn, lib)

        dedup = make_controller(db, provider)
        results = []
        dedup.scanFinished.connect(lambda groups: results.append(groups))
        loop = _quit_on(dedup.scanFinished)
        dedup.scanForDuplicates()
        loop.exec()

        assert results == [[]]

    def test_groups_and_items_are_plain_lists_not_tuples(
        self, make_controller, tmp_path, provider
    ):
        """QML-nek adott adat mindig `list` legyen, soha `tuple` (a projekt
        szabálya) — enélkül a QML-oldali `.length` undefined lenne."""

        lib = tmp_path / "kepek"
        lib.mkdir()
        original = make_jpeg(lib / "a.jpg", size=(40, 20))
        (lib / "b.jpg").write_bytes(original.read_bytes())
        db = tmp_path / "index.db"
        with open_index(db) as conn:
            sync_tree(conn, lib)

        dedup = make_controller(db, provider)
        results = []
        dedup.scanFinished.connect(lambda groups: results.append(groups))
        loop = _quit_on(dedup.scanFinished)
        dedup.scanForDuplicates()
        loop.exec()

        groups = results[0]
        assert isinstance(groups, list)
        for group in groups:
            assert isinstance(group["items"], list)
            for item in group["items"]:
                assert isinstance(item, dict)

    def test_scan_started_emitted_before_finished(self, make_controller, tmp_path, provider):

        lib = tmp_path / "kepek"
        lib.mkdir()
        make_jpeg(lib / "a.jpg", size=(40, 20))
        db = tmp_path / "index.db"
        with open_index(db) as conn:
            sync_tree(conn, lib)

        dedup = make_controller(db, provider)
        events = []
        dedup.scanStarted.connect(lambda: events.append("started"))
        dedup.scanFinished.connect(lambda groups: events.append("finished"))
        loop = _quit_on(dedup.scanFinished)
        dedup.scanForDuplicates()
        loop.exec()

        assert events == ["started", "finished"]


class TestMoveOthersToDuplicatesFolder:
    def test_moves_every_item_except_keep_into_subfolder(self, controller, tmp_path):
        lib = tmp_path / "kepek"
        lib.mkdir()
        keep = make_jpeg(lib / "keep.jpg", size=(40, 20))
        other = tmp_path / "kepek" / "masolat.jpg"
        other.write_bytes(keep.read_bytes())

        resolved = []
        controller.itemResolved.connect(lambda path: resolved.append(path))
        controller.moveOthersToDuplicatesFolder([str(keep), str(other)], str(keep))

        assert keep.exists()
        assert not other.exists()
        moved = lib / "Duplikátumok" / "masolat.jpg"
        assert moved.exists()
        assert resolved == [str(other)]

    def test_keep_path_is_never_touched(self, controller, tmp_path):
        lib = tmp_path / "kepek"
        lib.mkdir()
        keep = make_jpeg(lib / "keep.jpg", size=(40, 20))

        controller.moveOthersToDuplicatesFolder([str(keep)], str(keep))

        assert keep.exists()
        assert not (lib / "Duplikátumok").exists()

    def test_move_failure_emits_operation_failed(self, controller, tmp_path):
        lib = tmp_path / "kepek"
        lib.mkdir()
        keep = make_jpeg(lib / "keep.jpg", size=(40, 20))
        missing = lib / "nincs.jpg"

        failures = []
        controller.operationFailed.connect(
            lambda path, msg: failures.append((path, msg))
        )
        controller.moveOthersToDuplicatesFolder([str(keep), str(missing)], str(keep))

        assert failures[0][0] == str(missing)


class TestMoveIntoCollectorFolderItself:
    """#1697: a felhasználó jelentése szerint a `Duplikátumok` mappából
    ismét áthelyezve `Duplikátumok/Duplikátumok` beágyazott szerkezet jött
    létre. Ha a forrásmappa MAGA már a gyűjtőmappa, a fájl helyben marad
    (nincs mit tenni), és `operationFailed`-en EGYÉRTELMŰ üzenetet kap a
    felhasználó — néma hatástalanság éppúgy hiba lenne, mint a beágyazás."""

    def test_does_not_create_nested_duplicates_folder(self, controller, tmp_path):
        lib = tmp_path / "kepek"
        collector = lib / "Duplikátumok"
        collector.mkdir(parents=True)
        keep = make_jpeg(collector / "keep.jpg", size=(40, 20))
        other = collector / "masolat.jpg"
        other.write_bytes(keep.read_bytes())

        controller.moveOthersToDuplicatesFolder([str(keep), str(other)], str(keep))

        assert other.exists()  # helyben marad
        assert not (collector / "Duplikátumok").exists()  # nincs beágyazás

    def test_reports_a_clear_message_instead_of_silent_inaction(
        self, controller, tmp_path
    ):
        lib = tmp_path / "kepek"
        collector = lib / "Duplikátumok"
        collector.mkdir(parents=True)
        keep = make_jpeg(collector / "keep.jpg", size=(40, 20))
        other = collector / "masolat.jpg"
        other.write_bytes(keep.read_bytes())

        failures = []
        controller.operationFailed.connect(
            lambda path, msg: failures.append((path, msg))
        )
        resolved = []
        controller.itemResolved.connect(lambda path: resolved.append(path))
        controller.moveOthersToDuplicatesFolder([str(keep), str(other)], str(keep))

        assert len(failures) == 1
        assert failures[0][0] == str(other)
        assert failures[0][1]  # NEM üres — a néma elutasítás is hiba
        assert "Duplikátumok" in failures[0][1]
        assert resolved == []  # nem "megoldott", mert nem történt semmi

    def test_matches_by_name_case_insensitively(self, controller, tmp_path):
        """Windowson a `duplikátumok` és a `Duplikátumok` UGYANAZ a
        könyvtár (#1682) — az illesztés kis-nagybetűre érzéketlen kell
        legyen, nem csak a mi saját írásmódunkra."""
        lib = tmp_path / "kepek"
        collector = lib / "duplikátumok"  # kisbetűs 'd', felhasználó hozta létre
        collector.mkdir(parents=True)
        keep = make_jpeg(collector / "keep.jpg", size=(40, 20))
        other = collector / "masolat.jpg"
        other.write_bytes(keep.read_bytes())

        controller.moveOthersToDuplicatesFolder([str(keep), str(other)], str(keep))

        assert other.exists()
        assert not (collector / "Duplikátumok").exists()
        assert not (collector / "duplikátumok").exists()

    def test_search_still_works_inside_the_collector_folder(
        self, make_controller, tmp_path, provider
    ):
        """A jegy 2. elvárása: a `Duplikátumok` mappában a KERESÉS
        továbbra is működjön — csak a beágyazó áthelyezést tiltjuk."""
        lib = tmp_path / "kepek"
        collector = lib / "Duplikátumok"
        collector.mkdir(parents=True)
        original = make_jpeg(collector / "a.jpg", size=(40, 20))
        (collector / "b.jpg").write_bytes(original.read_bytes())
        db = tmp_path / "index.db"
        with open_index(db) as conn:
            sync_tree(conn, lib)

        dedup = make_controller(db, provider)
        results = []
        dedup.scanFinished.connect(lambda groups: results.append(groups))
        loop = _quit_on(dedup.scanFinished)
        dedup.scanFolder(str(collector))
        loop.exec()

        assert len(results) == 1
        exact = [g for g in results[0] if g["kind"] == "exact"]
        assert len(exact) == 1


class TestDeleteOthers:
    def test_deletes_every_item_except_keep(self, controller, tmp_path, monkeypatch):
        monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "xdg"))
        lib = tmp_path / "kepek"
        lib.mkdir()
        keep = make_jpeg(lib / "keep.jpg", size=(40, 20))
        other = lib / "masolat.jpg"
        other.write_bytes(keep.read_bytes())

        resolved = []
        controller.itemResolved.connect(lambda path: resolved.append(path))
        controller.deleteOthers([str(keep), str(other)], str(keep))

        assert keep.exists()
        assert not other.exists()
        assert resolved == [str(other)]

    def test_delete_failure_emits_operation_failed(self, controller, tmp_path):
        lib = tmp_path / "kepek"
        lib.mkdir()
        keep = make_jpeg(lib / "keep.jpg", size=(40, 20))
        missing = lib / "nincs.jpg"

        failures = []
        controller.operationFailed.connect(
            lambda path, msg: failures.append((path, msg))
        )
        controller.deleteOthers([str(keep), str(missing)], str(keep))

        assert failures[0][0] == str(missing)


class TestBackgroundThreadTeardown:
    """#438 (a #430 SIGSEGV-osztály maradéka): a keresés háttérszála
    bevárható legyen, mielőtt a controller megsemmisül."""

    def test_wait_without_a_run_returns_immediately(self, controller):
        assert controller.waitForBackgroundWorkers(0.0)

    def test_wait_joins_the_worker_thread(self, controller, tmp_path):
        loop = _quit_on(controller.scanFinished)
        controller.scanForDuplicates()
        loop.exec()
        assert controller.waitForBackgroundWorkers(30.0)
        assert not controller.backgroundWorkersRunning()


class TestGyorstarSzerzodes:
    """A két gyorstár és a KÉSZ jelentés viszonya (#1494 átnézés, 3./5. lelet)."""

    def _konyvtar(self, tmp_path):
        lib = tmp_path / "kepek"
        lib.mkdir()
        original = _gradient_jpeg(lib / "a.jpg")
        (lib / "b.jpg").write_bytes(original.read_bytes())
        db = tmp_path / "index.db"
        with open_index(db) as conn:
            sync_tree(conn, lib)
        return lib, db

    def test_a_ket_gyorstar_egyutt_el_ugyanazon_a_soron(
        self, make_controller, tmp_path, provider
    ):
        """ŐR (3. lelet): a dHash és a gyorskulcs UGYANABBÓL az
        azonosság-forrásból dolgozik, ezért egy soron megférnek.

        A szinkron ÓTA megváltozott fájl a próba lényege: itt tért el a
        rekordbeli (`PhotoRecord.mtime_ns`) és a friss `stat()` szerinti
        azonosság, és a két írás ilyenkor NULL-ozta egymást — a #294 fő
        nyeresége (a JPEG-dekódolás megspórolása) épp ezekre a képekre
        veszett el minden második körben."""
        lib, db = self._konyvtar(tmp_path)
        # a szinkron óta „hozzáért" valaki a fájlokhoz: az indexbeli
        # rekord mtime-ja elavul, a tartalom változatlan
        for nev in ("a.jpg", "b.jpg"):
            os.utime(lib / nev, ns=(0, 1_000_000_000))

        dedup = make_controller(db, provider)
        loop = _quit_on(dedup.scanFinished)
        dedup.scanForDuplicates()
        loop.exec()

        with open_index(db) as conn:
            sorok = {
                sor["path"]: (sor["dhash"], sor["originfast"])
                for sor in conn.execute(
                    "SELECT path, dhash, originfast FROM photo_hashes"
                )
            }
        for nev in ("a.jpg", "b.jpg"):
            dhash, gyorskulcs = sorok[str(lib / nev)]
            assert dhash is not None, f"{nev}: a gyorskulcs kiütötte a dHash-t"
            assert gyorskulcs is not None, f"{nev}: a dHash kiütötte a gyorskulcsot"

    def test_a_gyorstar_mentes_hibaja_nem_buktatja_a_keresest(
        self, make_controller, tmp_path, provider, monkeypatch
    ):
        """ŐR (5. lelet): zárolt indexen is a KÉSZ jelentés megy ki, nem
        `scanFailed` — a gyorstár feltöltése kényelmi szolgáltatás."""
        lib, db = self._konyvtar(tmp_path)

        def bukik(*_args, **_kwargs):
            raise sqlite3.OperationalError("database is locked")

        monkeypatch.setattr("picasapy.app.dedup_controller.save_dhashes", bukik)
        monkeypatch.setattr(
            "picasapy.index.fast_key_source.save_fast_keys", bukik
        )

        dedup = make_controller(db, provider)
        kesz, hibak = [], []
        dedup.scanFinished.connect(kesz.append)
        dedup.scanFailed.connect(hibak.append)
        loop = _quit_on(dedup.scanFinished)
        dedup.scanForDuplicates()
        loop.exec()

        assert hibak == []
        assert len(kesz) == 1
        exact = [csoport for csoport in kesz[0] if csoport["kind"] == "exact"]
        assert len(exact) == 1
