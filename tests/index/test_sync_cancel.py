"""#216: futó szinkron tiszta megszakítása mappa-határon.

A megszakítás kétféle úton kérhető: a `progress` callback igaz visszatérési
értékével (az app worker-útja — a controller-indirekció csak a progresst
adja tovább), vagy a `should_stop` hívhatóval (közvetlen hívók). Megszakadt
futás után a takarítás (`_prune_folders`) kimarad — a hiányos „látott"
halmaz nem törölhet érvényes mappákat.
"""

import pytest

from picasapy.index import open_index, photos_in_folder, sync_tree
from picasapy.index.sync import sync_folder


@pytest.fixture
def multi_library(tmp_path):
    root = tmp_path / "kepek"
    for nev in ("alma", "birs", "citrom"):
        (root / nev).mkdir(parents=True)
        (root / nev / "IMG_0001.jpg").write_bytes(b"x" * 10)
    return root


@pytest.fixture
def conn(tmp_path):
    with open_index(tmp_path / "index.db") as connection:
        yield connection


def _folder_paths(conn):
    return {row["path"] for row in conn.execute("SELECT path FROM folders")}


class TestSyncTreeCancel:
    def test_progress_true_stops_after_folder_commit(self, conn, multi_library):
        # az első mappa commitja még lefut (konzisztens állapot), utána
        # a futás tisztán leáll — a többi mappa nem kerül az indexbe
        calls = []

        def progress(folder, done, total, new_photos):
            calls.append(folder)
            return True  # azonnali megszakítás-kérés

        sync_tree(conn, multi_library, progress=progress)
        assert len(calls) == 1
        assert _folder_paths(conn) == {str(multi_library / "alma")}

    def test_should_stop_prevents_any_processing(self, conn, multi_library):
        sync_tree(conn, multi_library, should_stop=lambda: True)
        assert _folder_paths(conn) == set()

    def test_cancel_skips_prune(self, conn, multi_library):
        # teljes index után megszakított futás: a most nem látott mappák
        # NEM törlődnek (a hiányos seen-halmaz nem takaríthat)
        sync_tree(conn, multi_library)
        before = _folder_paths(conn)
        assert len(before) == 3
        sync_tree(conn, multi_library, incremental=False, progress=lambda *a: True)
        assert _folder_paths(conn) == before

    def test_progress_none_return_keeps_running(self, conn, multi_library):
        # None visszatérés (a #209-es, érték nélküli callbackek) nem szakít meg
        sync_tree(conn, multi_library, progress=lambda *a: None)
        assert len(_folder_paths(conn)) == 3

    def test_should_stop_mid_run_stops_at_boundary(self, conn, multi_library):
        # a jelző a 2. mappa előtt vált igazra → pontosan 1 mappa kerül be
        state = {"stop": False}

        def progress(folder, done, total, new_photos):
            state["stop"] = True  # az első mappa UTÁN kérünk leállást
            return False

        sync_tree(
            conn,
            multi_library,
            progress=progress,
            should_stop=lambda: state["stop"],
        )
        assert _folder_paths(conn) == {str(multi_library / "alma")}


class TestSyncFolderCancel:
    def test_should_stop_leaves_index_untouched(self, conn, multi_library):
        sync_tree(conn, multi_library)
        folder = multi_library / "alma"
        (folder / "IMG_0001.jpg").unlink()  # a sync ezt törölné az indexből
        sync_folder(conn, multi_library, folder, should_stop=lambda: True)
        # a megszakított sync semmit nem írt: a fotó sora megmaradt
        assert [p.name for p in photos_in_folder(conn, folder)] == [
            "IMG_0001.jpg"
        ]
