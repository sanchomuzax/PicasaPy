"""#459/5 — offline (jelenleg nem elérhető) mappa kezelése.

A levált NAS-mount üres könyvtárként jelenik meg. A #132 védelme csak a
GYÖKÉR szintjén óvott ettől; egy mélyebben lévő, leváló mappa fotói eddig
némán kiestek az indexből. Itt az a szerződés a tárgy, hogy az ilyen mappa
a fotóival együtt BENNMARAD, `offline = 1` jelöléssel, és a visszatérése
után a jelölés magától elmúlik.
"""

import os

import pytest

from picasapy.index import open_index, photos_in_folder, sync_folder, sync_tree


@pytest.fixture
def conn(tmp_path):
    with open_index(tmp_path / "index.db") as connection:
        yield connection


@pytest.fixture
def library(tmp_path):
    """Gyökér KÉT mappával: az egyik marad (így a gyökér-szintű #132 védelem
    biztosan nem lép be), a másik játssza a leváló mountot."""
    root = tmp_path / "kepek"
    (root / "helyi").mkdir(parents=True)
    (root / "helyi" / "a.jpg").write_bytes(b"x" * 10)
    (root / "nas").mkdir()
    (root / "nas" / "b.jpg").write_bytes(b"y" * 20)
    (root / "nas" / "c.jpg").write_bytes(b"z" * 20)
    return root


def _offline_flag(conn, path) -> int:
    row = conn.execute(
        "SELECT offline FROM folders WHERE path = ?", (str(path),)
    ).fetchone()
    return None if row is None else row["offline"]


def _empty_folder(path) -> None:
    """A mappa kiürítése — a levált mount látszatához (a könyvtár ott
    marad, de nulla bejegyzéssel)."""
    for entry in os.scandir(path):
        os.remove(entry.path)


class TestOfflineFolderInTreeSync:
    def test_empty_mountpoint_keeps_photos_and_marks_offline(self, conn, library):
        sync_tree(conn, library)
        assert len(photos_in_folder(conn, library / "nas")) == 2

        _empty_folder(library / "nas")
        sync_tree(conn, library, incremental=False)

        # a fotók megmaradtak, a mappa jelölést kapott
        assert len(photos_in_folder(conn, library / "nas")) == 2
        assert _offline_flag(conn, library / "nas") == 1
        # a másik mappa érintetlen és elérhető
        assert _offline_flag(conn, library / "helyi") == 0

    def test_returning_folder_clears_the_flag(self, conn, library):
        sync_tree(conn, library)
        _empty_folder(library / "nas")
        sync_tree(conn, library, incremental=False)
        assert _offline_flag(conn, library / "nas") == 1

        # a mount visszatér
        (library / "nas" / "b.jpg").write_bytes(b"y" * 20)
        (library / "nas" / "c.jpg").write_bytes(b"z" * 20)
        sync_tree(conn, library, incremental=False)

        assert _offline_flag(conn, library / "nas") == 0
        assert len(photos_in_folder(conn, library / "nas")) == 2

    def test_deleted_folder_is_still_pruned(self, conn, library):
        """A ténylegesen törölt mappa NEM offline — a takarítás lefut rá."""
        sync_tree(conn, library)
        _empty_folder(library / "nas")
        (library / "nas").rmdir()
        sync_tree(conn, library, incremental=False)

        assert _offline_flag(conn, library / "nas") is None
        assert list(photos_in_folder(conn, library / "nas")) == []

    def test_emptied_but_alive_folder_is_pruned(self, conn, library):
        """Ha a felhasználó kitörli a képeket, de a mappában marad más fájl,
        a mappa bizonyítottan él — nem offline, takarítható."""
        sync_tree(conn, library)
        _empty_folder(library / "nas")
        (library / "nas" / "olvasdel.txt").write_text("x", encoding="utf-8")
        sync_tree(conn, library, incremental=False)

        assert _offline_flag(conn, library / "nas") is None
        assert list(photos_in_folder(conn, library / "nas")) == []


class TestOfflineFolderInWatcherSync:
    def test_watcher_keeps_unavailable_folder(self, conn, library):
        sync_tree(conn, library)
        _empty_folder(library / "nas")
        sync_folder(conn, library, library / "nas")

        assert len(photos_in_folder(conn, library / "nas")) == 2
        assert _offline_flag(conn, library / "nas") == 1

    def test_watcher_removes_deleted_folder(self, conn, library):
        sync_tree(conn, library)
        _empty_folder(library / "nas")
        (library / "nas").rmdir()
        sync_folder(conn, library, library / "nas")

        assert _offline_flag(conn, library / "nas") is None
        assert list(photos_in_folder(conn, library / "nas")) == []
