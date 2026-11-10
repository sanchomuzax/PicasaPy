"""Fájl-metaadat (EXIF/IPTC) integráció a szinkronba."""

import pytest

from picasapy.index import open_index, photos_in_folder, search_photos, sync_tree

from support.jpeg_factory import make_jpeg


@pytest.fixture
def conn(tmp_path):
    with open_index(tmp_path / "index.db") as connection:
        yield connection


@pytest.fixture
def library(tmp_path):
    root = tmp_path / "kepek"
    root.mkdir()
    make_jpeg(
        root / "IMG_0001.jpg",
        size=(32, 16),
        taken_at="2025:05:01 07:23:10",
        orientation=6,
        caption="balatoni naplemente",
        keywords=("balaton", "nyár"),
    )
    make_jpeg(root / "IMG_0002.jpg")
    return root


class TestFileMetadata:
    def test_exif_and_iptc_indexed(self, conn, library):
        sync_tree(conn, library)
        photo = photos_in_folder(conn, library)[0]
        assert photo.taken_at == "2025-05-01T07:23:10"
        assert photo.orientation == 6
        assert (photo.width, photo.height) == (32, 16)
        assert photo.caption == "balatoni naplemente"
        assert photo.keywords == "balaton,nyár"

    def test_iptc_caption_wins_over_ini(self, conn, library):
        # Picasa-viselkedés: JPEG-nél a felirat az IPTC-ben él.
        (library / ".picasa.ini").write_text("[IMG_0001.jpg]\ncaption=ini felirat\n", encoding="utf-8")
        sync_tree(conn, library)
        assert photos_in_folder(conn, library)[0].caption == "balatoni naplemente"

    def test_ini_caption_used_when_no_iptc(self, conn, library):
        (library / ".picasa.ini").write_text("[IMG_0002.jpg]\ncaption=ini felirat\n", encoding="utf-8")
        sync_tree(conn, library)
        assert photos_in_folder(conn, library)[1].caption == "ini felirat"

    def test_iptc_caption_searchable(self, conn, library):
        sync_tree(conn, library)
        assert [p.name for p in search_photos(conn, "naplemente")] == ["IMG_0001.jpg"]
        assert [p.name for p in search_photos(conn, "balaton")] == ["IMG_0001.jpg"]


class TestChangeDetection:
    def test_unchanged_file_not_reread(self, conn, library, monkeypatch):
        sync_tree(conn, library)
        calls = []
        import picasapy.index.sync as sync_module

        original = sync_module.read_file_metadata
        monkeypatch.setattr(
            sync_module,
            "read_file_metadata",
            lambda path: calls.append(path) or original(path),
        )
        sync_tree(conn, library)
        assert calls == []

    def test_changed_file_reread_and_updated(self, conn, library):
        sync_tree(conn, library)
        make_jpeg(library / "IMG_0002.jpg", size=(64, 8), caption="új felirat")
        sync_tree(conn, library)
        photo = photos_in_folder(conn, library)[1]
        assert (photo.width, photo.height) == (64, 8)
        assert photo.caption == "új felirat"

    def test_unchanged_file_still_gets_ini_updates(self, conn, library):
        sync_tree(conn, library)
        (library / ".picasa.ini").write_text("[IMG_0002.jpg]\nstar=yes\n", encoding="utf-8")
        sync_tree(conn, library)
        photo = photos_in_folder(conn, library)[1]
        assert photo.star is True
        assert (photo.width, photo.height) == (8, 6)  # fájl-metaadat megmaradt

    def test_changed_metadata_is_read_in_parallel_and_upserted_as_a_batch(
        self, conn, library, monkeypatch
    ):
        """#6698: a lemezolvasás párhuzamos, az SQLite-írás rendezett köteg."""
        import threading
        import time

        from picasapy.index import sync as sync_module

        sync_module.sync_tree(conn, library)
        names = tuple(f"uj_{index}.jpg" for index in range(4))
        for name in names:
            make_jpeg(library / name)

        lock = threading.Lock()
        active = 0
        max_active = 0
        original_read = sync_module.read_file_metadata

        def slow_read(path):
            nonlocal active, max_active
            with lock:
                active += 1
                max_active = max(max_active, active)
            try:
                time.sleep(0.04)
                return original_read(path)
            finally:
                with lock:
                    active -= 1

        monkeypatch.setattr(sync_module, "read_file_metadata", slow_read)

        class ConnectionProxy:
            def __init__(self, connection):
                self.connection = connection
                self.photo_batches = []

            def execute(self, *args, **kwargs):
                return self.connection.execute(*args, **kwargs)

            def executemany(self, sql, rows):
                rows = list(rows)
                if sql.lstrip().startswith("INSERT INTO photos"):
                    self.photo_batches.append(rows)
                return self.connection.executemany(sql, rows)

            def __getattr__(self, name):
                return getattr(self.connection, name)

        proxy = ConnectionProxy(conn)
        sync_module.sync_tree(proxy, library, incremental=False)

        assert max_active > 1
        assert len(proxy.photo_batches) == 1
        assert [row[1] for row in proxy.photo_batches[0]] == list(names)
        assert [photo.name for photo in photos_in_folder(conn, library)] == sorted(
            ("IMG_0001.jpg", "IMG_0002.jpg", *names)
        )
