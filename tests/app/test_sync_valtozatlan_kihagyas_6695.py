"""#6695: változatlan szinkron után ne induljon teljes újratöltés."""

from __future__ import annotations

import os
import threading
import time
from contextlib import contextmanager
from pathlib import Path

import pytest
from PySide6.QtCore import QSettings

from picasapy.app.controller import AppController
from picasapy.app.timeline_controller import TimelineController
from picasapy.app.thumbnail_provider import ThumbnailProvider
from picasapy.index import all_photos, open_index, sync_tree
from picasapy.index import folder_ini, queries
from picasapy.index.side_pane import load_side_pane_collections
from picasapy.scanner import DirectoryChange
from picasapy.thumbs import ThumbnailCache
from support.jpeg_factory import make_jpeg


def _wait(qt_app, predicate, timeout: float = 15.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        qt_app.processEvents()
        if predicate():
            return
        time.sleep(0.05)
    pytest.fail("A háttérszinkron nem fejeződött be határidőn belül")


@pytest.fixture
def library_setup(qt_app, tmp_path):
    root = tmp_path / "kepek"
    folder_a = root / "mappa_a"
    folder_b = root / "mappa_b"
    folder_a.mkdir(parents=True)
    folder_b.mkdir(parents=True)
    make_jpeg(folder_a / "a1.jpg", size=(32, 32))
    make_jpeg(folder_b / "b1.jpg", size=(32, 32))
    (folder_a / ".picasa.ini").write_text(
        "[Picasa]\nP2category=Folders on Disk\n"
        "[a1.jpg]\nstar=yes\ncaption=Starred photo\n",
        encoding="utf-8",
    )
    (folder_b / ".picasa.ini").write_text(
        "[Picasa]\nP2category=Folders on Disk\n",
        encoding="utf-8",
    )

    db_path = tmp_path / "index.db"
    with open_index(db_path) as conn:
        sync_tree(conn, root)

    old_time = time.time() - 10
    for path in (
        root,
        folder_a,
        folder_b,
        folder_a / "a1.jpg",
        folder_b / "b1.jpg",
        folder_a / ".picasa.ini",
        folder_b / ".picasa.ini",
    ):
        os.utime(path, (old_time, old_time))
    # Az index és a lemez kezdő mtime-ja egyezzen; különben a következő
    # szinkron jogosan módosítaná a fotórekordokat.
    with open_index(db_path) as conn:
        sync_tree(conn, root)

    provider = ThumbnailProvider(ThumbnailCache(tmp_path / "thumbs", size=32))
    settings = QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat)
    controller = AppController(
        db_path,
        (str(root),),
        provider,
        settings=settings,
        watched_file=tmp_path / "WatchedFolders.txt",
    )
    # A valós indulás háttérszinkronja előállítja ezt az adatot. Itt a fixture
    # ugyanezt a kész állapotot készíti elő, hogy a mérés csak az új szinkront
    # számolja.
    with open_index(db_path) as conn:
        controller._precompute_side_pane(conn)
    controller._take_side_pane_stash()
    controller._reload()

    timeline = TimelineController(db_path, provider)
    timeline._sync_controller = controller
    controller.syncFinished.connect(timeline.reload)
    yield controller, timeline, root, folder_a, folder_b, db_path, provider
    controller.shutdown()
    assert controller.waitForBackgroundWorkers(30.0), "háttérszál nem állt le"


class TestValtozatlanSzinkron:
    def test_valtozatlan_rescan_nem_olvas_iniket_es_nem_frissit_nezeteket(
        self, qt_app, library_setup, monkeypatch
    ):
        controller, timeline, *_ = library_setup
        ini_olvasasok = []
        eredeti_olvasas = folder_ini.load_document

        def szamlal(path):
            ini_olvasasok.append((threading.get_ident(), str(path)))
            return eredeti_olvasas(path)

        monkeypatch.setattr(folder_ini, "load_document", szamlal)
        racs_frissitesek = []
        eredeti_racs = controller._reload
        monkeypatch.setattr(
            controller,
            "_reload",
            lambda *args, **kwargs: (
                racs_frissitesek.append(True) or eredeti_racs(*args, **kwargs)
            ),
        )
        timeline_frissitesek = []
        timeline.collectionsChanged.connect(lambda: timeline_frissitesek.append(True))
        szinkron_kesz = []
        controller.syncFinished.connect(lambda: szinkron_kesz.append(True))

        controller.rescan()
        _wait(qt_app, lambda: bool(szinkron_kesz))

        assert controller._last_sync_changed is False
        assert ini_olvasasok == []
        assert racs_frissitesek == []
        assert timeline_frissitesek == []

    def test_valtozatlan_celzott_szinkron_utan_sem_tolt_ujra_a_racs(
        self, qt_app, library_setup, monkeypatch
    ):
        controller, _timeline, _root, folder_a, *_ = library_setup
        racs_frissitesek = []
        eredeti_racs = controller._reload
        monkeypatch.setattr(
            controller,
            "_reload",
            lambda *args, **kwargs: (
                racs_frissitesek.append(True) or eredeti_racs(*args, **kwargs)
            ),
        )
        szinkron_kesz = []
        controller.syncFinished.connect(lambda: szinkron_kesz.append(True))

        controller._on_folders_dirty([DirectoryChange(str(folder_a), "refresh")])
        _wait(qt_app, lambda: bool(szinkron_kesz))

        assert controller._last_sync_changed is False
        assert racs_frissitesek == []


class TestIniGyorstar:
    def test_valtozatlan_ini_ket_betoltes_kozott_nem_olvasodik_ujra(
        self, library_setup, monkeypatch
    ):
        _controller, _timeline, _root, _folder_a, _folder_b, db_path, _provider = (
            library_setup
        )
        with open_index(db_path) as conn:
            load_side_pane_collections(conn)

        olvasasok = []
        eredeti_olvasas = folder_ini.load_document
        monkeypatch.setattr(
            folder_ini,
            "load_document",
            lambda path: (olvasasok.append(str(path)) or eredeti_olvasas(path)),
        )
        with open_index(db_path) as conn:
            load_side_pane_collections(conn)

        assert olvasasok == []

    def test_ini_valtozas_utan_csak_az_erintett_mappa_olvasodik_ujra(
        self, library_setup, monkeypatch
    ):
        _controller, _timeline, _root, folder_a, folder_b, db_path, _provider = (
            library_setup
        )
        (folder_b / ".picasa.ini").write_text(
            "[Picasa]\nP2category=Projects (internal)\n"
            "[b1.jpg]\nstar=yes\ncaption=Fresh caption\n",
            encoding="utf-8",
        )
        past = time.time() - 10
        os.utime(folder_b / ".picasa.ini", (past, past))

        olvasasok = []
        eredeti_olvasas = folder_ini.load_document
        monkeypatch.setattr(
            folder_ini,
            "load_document",
            lambda path: (olvasasok.append(str(path)) or eredeti_olvasas(path)),
        )
        with open_index(db_path) as conn:
            collections = load_side_pane_collections(conn)

        assert [Path(path) for path in olvasasok] == [folder_b / ".picasa.ini"]
        assert [Path(row.path) for row in collections.project_folders] == [folder_b]
        assert folder_a / ".picasa.ini" not in [Path(path) for path in olvasasok]


class TestIniValtozasUtaniFrissites:
    def test_ini_valtozas_utan_oldalpanel_es_racs_frissul(
        self, qt_app, library_setup, monkeypatch
    ):
        controller, _timeline, _root, _folder_a, folder_b, db_path, _provider = (
            library_setup
        )
        (folder_b / ".picasa.ini").write_text(
            "[Picasa]\nP2category=Projects (internal)\n"
            "[b1.jpg]\nstar=yes\ncaption=Fresh caption\n",
            encoding="utf-8",
        )
        past = time.time() - 10
        os.utime(folder_b / ".picasa.ini", (past, past))

        racs_frissitesek = []
        eredeti_racs = controller._reload
        monkeypatch.setattr(
            controller,
            "_reload",
            lambda *args, **kwargs: (
                racs_frissitesek.append(True) or eredeti_racs(*args, **kwargs)
            ),
        )
        szinkron_kesz = []
        controller.syncFinished.connect(lambda: szinkron_kesz.append(True))
        controller.rescan()
        _wait(qt_app, lambda: bool(szinkron_kesz))

        assert controller._last_sync_changed is True
        assert racs_frissitesek == [True]
        assert any(Path(row["path"]) == folder_b for row in controller.projectFolders)
        with open_index(db_path) as conn:
            photo = next(row for row in all_photos(conn) if row.name == "b1.jpg")
        assert photo.star is True
        assert photo.caption == "Fresh caption"


class TestTimelineLustaBetoltes:
    def test_teljes_konyvtarat_es_provider_regisztraciot_hasznal_szures_mellett(
        self, library_setup, monkeypatch
    ):
        controller, timeline, _root, _folder_a, _folder_b, _db_path, provider = (
            library_setup
        )
        controller.showStarred()
        assert controller._photos.rowCount() == 1

        regisztralt = []
        monkeypatch.setattr(
            provider, "register_photos", lambda records: regisztralt.append(tuple(records))
        )
        timeline.setTimelineOpen(True)

        timeline_ids = {
            photo["id"]
            for collection in timeline.collections
            for photo in collection["photos"]
        }
        with open_index(controller._db_path) as conn:
            teljes_ids = {photo.id for photo in all_photos(conn) if not photo.hidden}
        assert timeline_ids == teljes_ids
        assert len(regisztralt) == 1
        assert {photo.id for photo in regisztralt[0]} == teljes_ids

    def test_albumtagsagot_egy_lekérdezés_tölti_be(self, library_setup, monkeypatch):
        _controller, timeline, _root, _folder_a, _folder_b, db_path, _provider = (
            library_setup
        )
        with open_index(db_path) as conn:
            rows = conn.execute("SELECT id FROM photos ORDER BY id").fetchall()
            first_id, second_id = (row["id"] for row in rows)
            folders = conn.execute("SELECT id FROM folders ORDER BY path").fetchall()
            conn.executemany(
                "INSERT INTO albums (folder_id, token, name) VALUES (?, ?, ?)",
                [
                    (folders[0]["id"], "album-one", "One"),
                    (folders[1]["id"], "album-two", "Two"),
                ],
            )
            conn.executemany(
                "INSERT INTO photo_albums (photo_id, token, place) VALUES (?, ?, ?)",
                [(first_id, "album-one", 0), (second_id, "album-two", 0)],
            )

        statements = []
        from picasapy.app import timeline_controller as timeline_module

        eredeti_open = timeline_module.open_index

        @contextmanager
        def traced_open(_path):
            with eredeti_open(db_path) as conn:
                conn.set_trace_callback(statements.append)
                yield conn

        monkeypatch.setattr(
            timeline_module, "open_index", traced_open
        )
        timeline.setTimelineOpen(True)

        membership_queries = [
            sql for sql in statements if "SELECT pa.token, pa.photo_id" in sql
        ]
        assert len(membership_queries) == 1


class TestAllPhotosGroupedFaceCounts:
    def test_arcszamokhoz_nincs_soronkénti_korrelalt_allekerdezes(self):
        assert "(SELECT COUNT(*) FROM face WHERE face.photo_id = p.id)" not in (
            queries._SELECT_SABLON
        )
        assert "GROUP BY photo_id" in queries._SELECT_SABLON
        assert "LEFT JOIN" in queries._SELECT_SABLON
