"""#7193: külön keresőszavak, kizárás és szókezdő egyezés."""

# rontás-kontroll: picasapy.index.queries._SEARCH_TAG_PREFIXES = () → 1 failed

from __future__ import annotations

import pytest

from picasapy.index import open_index, search_photos, sync_tree
from picasapy.index import queries as search_queries


@pytest.fixture
def search_conn(tmp_path):
    root = tmp_path / "kepek"
    content = root / "content"
    content.mkdir(parents=True)

    names = (
        "positive.jpg",
        "reversed.jpg",
        "only_zqa.jpg",
        "excluded.jpg",
        "negative_prefix.jpg",
        "zqab-name.jpg",
        "insidezqa_name.jpg",
        "caption.jpg",
        "keyword.jpg",
        "insidezqa_keyword.jpg",
    )
    for name in names:
        (content / name).write_bytes(b"test")
    (content / ".picasa.ini").write_text(
        "[positive.jpg]\ncaption=zqa middle far away zqb\n"
        "[reversed.jpg]\nkeywords=zqb first then zqa\n"
        "[only_zqa.jpg]\ncaption=zqa\n"
        "[excluded.jpg]\ncaption=zqa and zqb\n"
        "[negative_prefix.jpg]\ncaption=zqa and zqbad\n"
        "[zqab-name.jpg]\ncaption=ordinary\n"
        "[insidezqa_name.jpg]\ncaption=ordinary\n"
        "[caption.jpg]\ncaption=zqab-caption\n"
        "[keyword.jpg]\nkeywords=zqab-keyword\n"
        "[insidezqa_keyword.jpg]\nkeywords=insidezqa\n",
        encoding="utf-8",
    )

    matching_folder = root / "zqab-mappa-zqbb"
    matching_folder.mkdir()
    (matching_folder / "folder_match.jpg").write_bytes(b"test")
    partial_folder = root / "insidezqa-mappa-zqbb"
    partial_folder.mkdir()
    (partial_folder / "folder_partial.jpg").write_bytes(b"test")

    with open_index(tmp_path / "index.db") as connection:
        sync_tree(connection, root)
        yield connection


def _names(conn, query: str) -> set[str]:
    return {photo.name for photo in search_photos(conn, query)}


def test_a_szavak_sorrendtől_es_tavolsagtol_fuggetlenul_esz_kapcsolatuak(
    search_conn,
):
    names = _names(search_conn, "zqa zqb")

    assert {"positive.jpg", "reversed.jpg", "excluded.jpg"} <= names
    assert "only_zqa.jpg" not in names


def test_a_minuszos_szo_a_szavankenti_talalatokat_kizarja(search_conn):
    names = _names(search_conn, "zqa -zqb")

    assert "only_zqa.jpg" in names
    assert "reversed.jpg" not in names
    assert "excluded.jpg" not in names
    assert "negative_prefix.jpg" not in names
    assert "folder_match.jpg" not in names


def test_az_egyezes_szoelejen_kezdodik_a_foto_mezoiben_es_a_mappanevben(
    search_conn,
):
    names = _names(search_conn, "zqa")

    assert {"zqab-name.jpg", "caption.jpg", "keyword.jpg", "folder_match.jpg"} <= names
    assert "insidezqa_name.jpg" not in names
    assert "insidezqa_keyword.jpg" not in names
    assert "folder_partial.jpg" not in names


def test_a_mappanev_ag_is_szavankenti_es_esz_kapcsolatu(search_conn):
    names = _names(search_conn, "zqa zqb")

    assert "folder_match.jpg" in names
    assert "folder_partial.jpg" not in names


@pytest.mark.parametrize(
    ("query", "expected"),
    [("zqa -zqb", "zqa -zqb"), ("tag:zqa -zqb", "zqa -zqb")],
)
def test_a_normalizalo_megtartja_a_kizaro_elotagot(query, expected):
    assert search_queries._normalize_search_query(query) == expected


def test_a_cimke_elotag_levagodik_es_minden_mezo_keresheto_marad(search_conn):
    expected = _names(search_conn, "zqa")

    assert _names(search_conn, "tag:zqa") == expected
    assert _names(search_conn, "címke:zqa") == expected
