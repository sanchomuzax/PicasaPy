"""#4536: a személy-album indexképe tartósan az SQLite indexben él."""

from __future__ import annotations

from picasapy.index import (
    SCHEMA_VERSION,
    open_index,
    person_thumbnail,
    person_thumbnail_face,
    set_person_thumbnail,
    sync_tree,
)
from picasapy.index.queries import photos_in_folder
from tests.support.jpeg_factory import make_jpeg

_PERSON_ID = "aaaaaaaaaaaaaaaa"
_RECT = "1e00280045006e00"


def _make_library(root):
    root.mkdir()
    make_jpeg(root / "a.jpg")
    make_jpeg(root / "b.jpg")
    (root / ".picasa.ini").write_text(
        "[Contacts2]\n"
        f"{_PERSON_ID}=Anna;;\n"
        "[a.jpg]\n"
        f"faces=rect64({_RECT}),{_PERSON_ID}\n"
        "[b.jpg]\n",
        encoding="utf-8",
    )


def test_person_thumbnail_face_is_resolved_from_the_selected_photo(tmp_path):
    library = tmp_path / "kepek"
    _make_library(library)
    db = tmp_path / "index.db"

    with open_index(db) as conn:
        sync_tree(conn, library)
        photo = next(p for p in photos_in_folder(conn, library) if p.name == "a.jpg")
        assert person_thumbnail_face(conn, "Anna", photo.id) == (
            0.1171875,
            0.15625,
            0.26953125,
            0.4296875,
        )
        assert person_thumbnail_face(conn, "Anna", -1) is None
        assert person_thumbnail_face(conn, "Anna", next(
            p.id for p in photos_in_folder(conn, library) if p.name == "b.jpg"
        )) is None


def test_person_thumbnail_survives_reopening_the_index(tmp_path):
    library = tmp_path / "kepek"
    _make_library(library)
    db = tmp_path / "index.db"
    ini_path = library / ".picasa.ini"
    ini_before = ini_path.read_bytes()

    with open_index(db) as conn:
        sync_tree(conn, library)
        photo = next(p for p in photos_in_folder(conn, library) if p.name == "a.jpg")
        assert set_person_thumbnail(conn, "Anna", photo.id) is True
        conn.commit()
    assert ini_path.read_bytes() == ini_before

    with open_index(db) as conn:
        saved = person_thumbnail(conn, "ANNA")
        assert saved is not None
        assert saved.photo_id == photo.id
        assert saved.rect == (
            0.1171875,
            0.15625,
            0.26953125,
            0.4296875,
        )


def test_person_thumbnail_rejects_a_photo_without_that_person(tmp_path):
    library = tmp_path / "kepek"
    _make_library(library)
    db = tmp_path / "index.db"

    with open_index(db) as conn:
        sync_tree(conn, library)
        photo = next(p for p in photos_in_folder(conn, library) if p.name == "b.jpg")
        assert set_person_thumbnail(conn, "Anna", photo.id) is False
        assert set_person_thumbnail(conn, "Ismeretlen", photo.id) is False
        assert person_thumbnail(conn, "Anna") is None


def test_v23_index_migrates_the_thumbnail_table(tmp_path):
    library = tmp_path / "kepek"
    _make_library(library)
    db = tmp_path / "index.db"

    with open_index(db) as conn:
        sync_tree(conn, library)
        conn.execute("DROP TABLE person_thumbnails")
        conn.execute("PRAGMA user_version = 23")
        conn.commit()

    with open_index(db) as conn:
        assert SCHEMA_VERSION == 24
        assert conn.execute("PRAGMA user_version").fetchone()[0] == 24
        columns = {
            row["name"]
            for row in conn.execute("PRAGMA table_info(person_thumbnails)")
        }
        assert columns == {"person_key", "photo_id"}
        assert conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' "
            "AND name = 'person_thumbnails'"
        ).fetchone() is not None


def test_deleted_photo_clears_the_saved_thumbnail(tmp_path):
    library = tmp_path / "kepek"
    _make_library(library)
    db = tmp_path / "index.db"

    with open_index(db) as conn:
        sync_tree(conn, library)
        photo = next(p for p in photos_in_folder(conn, library) if p.name == "a.jpg")
        assert set_person_thumbnail(conn, "Anna", photo.id)
        conn.commit()
        conn.execute("DELETE FROM photos WHERE id = ?", (photo.id,))
        conn.commit()
        assert person_thumbnail(conn, "Anna") is None


def test_fresh_database_has_no_saved_thumbnail(tmp_path):
    with open_index(tmp_path / "empty.db") as conn:
        assert conn.execute("PRAGMA user_version").fetchone()[0] == SCHEMA_VERSION
        assert conn.execute(
            "SELECT COUNT(*) FROM person_thumbnails"
        ).fetchone()[0] == 0
