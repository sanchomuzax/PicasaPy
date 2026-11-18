"""#7242: A keresés javaslatlistájának szósorai darabszámot mutatnak,
és darabszám szerint csökkenő sorrendben állnak.
"""

from __future__ import annotations

import pytest

from picasapy.index import open_index, search_suggestions, sync_tree


@pytest.fixture
def ai_sample_conn(tmp_path):
    root = tmp_path / "kepek"
    root.mkdir()

    # Mappasor az "ai"-mintához
    folder = root / "aifolder"
    folder.mkdir()
    (folder / "cover.jpg").write_bytes(b"x")

    # 3 kép ai1, ai2, ai3 kulcsszavakkal
    group_three = root / "group3"
    group_three.mkdir()
    three_sections = []
    for i in (1, 2, 3):
        fn = f"three_{i}.jpg"
        (group_three / fn).write_bytes(b"x")
        three_sections.append(f"[{fn}]\nkeywords=ai1, ai2, ai3\n")
    (group_three / ".picasa.ini").write_text("".join(three_sections), encoding="utf-8")

    # 2 kép ai4..ai8 kulcsszavakkal
    group_two = root / "group2"
    group_two.mkdir()
    two_sections = []
    for i in (1, 2):
        fn = f"two_{i}.jpg"
        (group_two / fn).write_bytes(b"x")
        two_sections.append(f"[{fn}]\nkeywords=ai4, ai5, ai6, ai7, ai8\n")
    (group_two / ".picasa.ini").write_text("".join(two_sections), encoding="utf-8")

    with open_index(tmp_path / "index.db") as conn:
        sync_tree(conn, root)
        yield conn


def test_ai_sample_word_counts_descending_and_folder_leads(ai_sample_conn):
    rows = search_suggestions(ai_sample_conn, "ai")

    # Mappasor az élen
    assert rows[0].kind == "folder"
    assert rows[0].name == "aifolder"

    word_rows = [r for r in rows if r.kind == "word"]
    # 8 szósor (ai1..ai3 és ai4..ai8)
    assert len(word_rows) == 8

    # A szósorok darabszám szerint csökkenő sorrendben állnak
    counts = [r.count for r in word_rows]
    assert counts == [3, 3, 3, 2, 2, 2, 2, 2]

    # Az első 3 szó ai1..ai3
    assert {r.name for r in word_rows[:3]} == {"ai1", "ai2", "ai3"}
    # A maradék 5 szó ai4..ai8
    assert {r.name for r in word_rows[3:8]} == {"ai4", "ai5", "ai6", "ai7", "ai8"}

    # Param megegyezik a névvel
    for r in word_rows:
        assert r.param == r.name


def test_multiword_keyword_is_split_into_words(tmp_path):
    root = tmp_path / "kepek"
    root.mkdir()
    folder = root / "photos"
    folder.mkdir()
    (folder / "img.jpg").write_bytes(b"x")
    (folder / ".picasa.ini").write_text("[img.jpg]\nkeywords=AI image\n", encoding="utf-8")

    with open_index(tmp_path / "index.db") as conn:
        sync_tree(conn, root)
        rows = search_suggestions(conn, "ai")

    word_rows = [r for r in rows if r.kind == "word"]
    assert len(word_rows) == 1
    assert word_rows[0].name == "ai"
    assert word_rows[0].count == 1
    assert word_rows[0].param == "ai"
