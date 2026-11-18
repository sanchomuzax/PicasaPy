"""#7217: mappa- és kulcsszó-javaslatok az eredetivel mért sorrendben."""

from __future__ import annotations

import pytest

from picasapy.index import open_index, search_suggestions, sync_tree


@pytest.fixture
def suggestion_conn(tmp_path):
    root = tmp_path / "kepek"
    root.mkdir()

    folder = root / "ai-folder"
    folder.mkdir()
    (folder / "one.jpg").write_bytes(b"x")
    (folder / ".picasa.ini").write_text(
        "[one.jpg]\nkeywords=ai\n", encoding="utf-8"
    )

    another = root / "other"
    another.mkdir()
    (another / "two.jpg").write_bytes(b"x")
    (another / ".picasa.ini").write_text(
        "[two.jpg]\nkeywords=mainstream\n", encoding="utf-8"
    )

    many = root / "many"
    many.mkdir()
    sections = []
    for number in range(1, 16):
        filename = f"word_{number:02}.jpg"
        (many / filename).write_bytes(b"x")
        sections.append(f"[{filename}]\nkeywords=ai{number}\n")
    (many / ".picasa.ini").write_text("".join(sections), encoding="utf-8")

    with open_index(tmp_path / "index.db") as conn:
        sync_tree(conn, root)
        yield conn


def test_measured_folder_and_keyword_suggestions_are_both_returned(
    suggestion_conn,
):
    rows = search_suggestions(suggestion_conn, "ai", limit=2)

    assert [(row.kind, row.name) for row in rows] == [
        ("folder", "ai-folder"),
        ("word", "ai"),
    ]


def test_measured_substring_keyword_is_suggested(suggestion_conn):
    rows = search_suggestions(suggestion_conn, "main")

    assert [(row.kind, row.name) for row in rows] == [("word", "mainstream")]


def test_suggestions_have_a_hard_ten_row_limit_and_folder_rows_lead(
    suggestion_conn,
):
    rows = search_suggestions(suggestion_conn, "ai", limit=50)

    assert len(rows) == 10
    word_indexes = [index for index, row in enumerate(rows) if row.kind == "word"]
    folder_indexes = [
        index for index, row in enumerate(rows) if row.kind == "folder"
    ]
    assert word_indexes and folder_indexes
    assert max(folder_indexes) < min(word_indexes)
