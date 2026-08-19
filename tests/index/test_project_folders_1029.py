"""#1029: a **Projektek** gyűjtemény tartalma — a `.picasa.ini` `[Picasa]`
`P2category=Projects (internal)` mappái, névvel és darabszámmal.

A legfontosabb eset a REGRESSZIÓ: a korpusz 456 `Folders on Disk` értékű
mappája a **Mappák** alá tartozik, nem a Projektek alá — a `folders` tábla
(és vele a mappalista) egyetlen sort sem veszíthet ettől a lekérdezéstől.
"""

from __future__ import annotations

import pytest

from picasapy.index import open_index, project_folders, sync_tree

_PROJECTS = "[Picasa]\nP2category=Projects (internal)\n"


@pytest.fixture
def library(tmp_path):
    """Négy mappa — pontosan a korpuszban látott értékekkel."""
    root = tmp_path / "kepek"
    for name in ("Kollázsok", "Rögzített videoklipek", "nyaralas", "egyeb"):
        (root / name).mkdir(parents=True)
        (root / name / "IMG_0001.jpg").write_bytes(b"x" * 10)
    (root / "Kollázsok" / "IMG_0002.jpg").write_bytes(b"x" * 10)
    (root / "Kollázsok" / ".picasa.ini").write_text(_PROJECTS, encoding="utf-8")
    (root / "Rögzített videoklipek" / ".picasa.ini").write_text(
        _PROJECTS, encoding="utf-8"
    )
    # ⚠️ a 456 elemű többség: ez a MAPPÁK alá tartozik
    (root / "nyaralas" / ".picasa.ini").write_text(
        "[Picasa]\nP2category=Folders on Disk\n", encoding="utf-8"
    )
    # ini nélküli mappa — sehova nem sorolt, marad a Mappák alatt
    return root


@pytest.fixture
def conn(tmp_path, library):
    with open_index(tmp_path / "index.db") as connection:
        sync_tree(connection, library)
        yield connection


def _names(conn) -> list[str]:
    return [folder.name for folder in project_folders(conn)]


class TestProjectFoldersListed:
    def test_projects_category_folders_are_listed(self, conn):
        assert _names(conn) == ["Kollázsok", "Rögzített videoklipek"]

    def test_row_carries_path_and_photo_count(self, conn, library):
        row = project_folders(conn)[0]
        assert row.path == str(library / "Kollázsok")
        assert row.name == "Kollázsok"
        assert row.photo_count == 2

    def test_folders_on_disk_is_not_a_project(self, conn):
        """⚠️ A fő csapda: a `P2category` ÉRTÉKE dönt, nem a kulcs megléte."""
        assert "nyaralas" not in _names(conn)

    def test_folder_without_ini_is_not_a_project(self, conn):
        assert "egyeb" not in _names(conn)

    def test_custom_collection_value_is_not_a_project(self, tmp_path, library):
        (library / "egyeb" / ".picasa.ini").write_text(
            "[Picasa]\nP2category=tech\n", encoding="utf-8"
        )
        with open_index(tmp_path / "index2.db") as conn:
            sync_tree(conn, library)
            assert "egyeb" not in _names(conn)

    def test_value_is_matched_case_insensitively(self, tmp_path, library):
        (library / "egyeb" / ".picasa.ini").write_text(
            "[Picasa]\nP2category=projects (internal)\n", encoding="utf-8"
        )
        with open_index(tmp_path / "index2.db") as conn:
            sync_tree(conn, library)
            assert "egyeb" in _names(conn)

    def test_empty_library_yields_empty_list(self, tmp_path):
        with open_index(tmp_path / "ures.db") as conn:
            assert project_folders(conn) == ()

    def test_unreadable_ini_is_skipped_without_error(self, tmp_path, library):
        with open_index(tmp_path / "index2.db") as conn:
            sync_tree(conn, library)
            (library / "Kollázsok" / ".picasa.ini").unlink()
            # az ini időközben eltűnt (másik folyamat) — a lista ne omoljon
            assert _names(conn) == ["Rögzített videoklipek"]

    def test_newly_created_project_folder_appears_after_sync(
        self, tmp_path, library
    ):
        """A mentett kollázs mappája a következő szinkron után LÁTSZIK —
        ez a #969 kimenete (a mentés írja a kulcsot az ini-be).

        Kép nélküli mappát a beolvasó eleve nem indexel (`walker._scan_folder`:
        média nélkül nincs `FolderScan`), ezért a mappában kép is van."""
        new_folder = library / "Filmek"
        new_folder.mkdir()
        (new_folder / "film.jpg").write_bytes(b"x" * 10)
        (new_folder / ".picasa.ini").write_text(_PROJECTS, encoding="utf-8")
        with open_index(tmp_path / "index2.db") as conn:
            sync_tree(conn, library)
            rows = {row.name: row.photo_count for row in project_folders(conn)}
            assert rows.get("Filmek") == 1


class TestFoldersViewIsNotBroken:
    """⚠️ A legvalószínűbb regresszió: a Projektek feltöltése ne vegyen el
    semmit a Mappák nézettől."""

    def test_every_folder_stays_in_the_folders_table(self, conn, library):
        paths = {
            row["path"]
            for row in conn.execute("SELECT path FROM folders")
        }
        for name in ("Kollázsok", "Rögzített videoklipek", "nyaralas", "egyeb"):
            assert str(library / name) in paths

    def test_folders_on_disk_folder_keeps_its_photos(self, conn, library):
        row = conn.execute(
            "SELECT COUNT(p.id) AS n FROM folders f"
            " JOIN photos p ON p.folder_id = f.id WHERE f.path = ?",
            (str(library / "nyaralas"),),
        ).fetchone()
        assert row["n"] == 1
