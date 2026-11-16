"""A #7081 keresőszöveg-tisztításának és szóhatárainak őrei."""

from __future__ import annotations

import pytest

from picasapy.index import open_index, search_photos, sync_tree
from picasapy.index import queries as search_queries


@pytest.fixture
def search_conn(tmp_path):
    root = tmp_path / "kepek"
    album = root / "summer_trip"
    album.mkdir(parents=True)
    (album / "photo.jpg").write_bytes(b"teszt")
    with open_index(tmp_path / "index.db") as connection:
        sync_tree(connection, root)
        yield connection


def _normalizald(query: str) -> str:
    normalizalo = getattr(search_queries, "_normalize_search_query", None)
    assert callable(normalizalo), "hiányzik a keresőkifejezés normalizálója"
    return normalizalo(query)


def test_a_szovegszeli_eredeti_elvalasztok_nem_valtoztatjak_a_mappatalalatot(
    search_conn,
):
    hits = search_photos(search_conn, " ,./\\summer_trip\\,./ ")

    assert [photo.name for photo in hits] == ["photo.jpg"]


def test_a_pont_es_alahuzas_szoelvalaszto_a_mappatalalatban(search_conn):
    hits = search_photos(search_conn, "summer.trip")

    assert [photo.name for photo in hits] == ["photo.jpg"]


@pytest.mark.parametrize(
    ("query", "expected"),
    [
        (" ,./\\NYARALÁS_fő.album\\,./ ", "nyaralás fő album"),
        ("É東京:42", "é東京:42"),
        ("Címke:CSALÁD", "család"),
        ("tag:Family", "family"),
    ],
)
def test_az_eredeti_karakterosztaly_es_lokalizalt_elotag(query, expected):
    assert _normalizald(query) == expected
