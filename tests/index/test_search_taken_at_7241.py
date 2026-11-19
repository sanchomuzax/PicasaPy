"""A felvételi dátum keresőszóként működik (#7241)."""

from __future__ import annotations

from pathlib import Path

import pytest

from picasapy.index import open_index, search_photos, sync_tree
from support.jpeg_factory import make_jpeg


@pytest.fixture
def date_search_conn(tmp_path):
    root = tmp_path / "photos"
    sets = {
        "tavaszi_kepek": (
            "2019:03:01 09:15:00",
            "2019:03:02 09:15:00",
            "2019:03:03 09:15:00",
            "2019:03:04 09:15:00",
            "2019:03:05 09:15:00",
            "2019:03:06 09:15:00",
            "2019:03:07 09:15:00",
        ),
        "oszi_kepek": (
            "2014:11:01 09:15:00",
            "2014:11:02 09:15:00",
            "2014:11:03 09:15:00",
        ),
        "regi_kepek": ("2009:05:08 09:15:00",),
        "fajlido_pelda": (
            "2021:01:03 09:15:00",
            "2021:12:20 09:15:00",
        ),
    }
    for folder_name, dates in sets.items():
        folder = root / folder_name
        folder.mkdir(parents=True)
        for number, taken_at in enumerate(dates, start=1):
            make_jpeg(folder / f"photo_{number:02}.jpg", taken_at=taken_at)

    with open_index(tmp_path / "index.db") as conn:
        sync_tree(conn, root)
        yield conn


def _names(conn, query: str) -> set[str]:
    return {photo.name for photo in search_photos(conn, query)}


@pytest.mark.parametrize(
    ("query", "expected_count"),
    [
        ("2019:03", 7),
        ("2019", 7),
        ("2014:11", 3),
        ("2009:05", 1),
        ("2021", 2),
    ],
)
def test_a_felveteli_datum_es_az_ev_keresoszav(date_search_conn, query, expected_count):
    hits = search_photos(date_search_conn, query)

    assert len(hits) == expected_count
    assert all(query[:4] not in Path(photo.folder_path).name for photo in hits)


def test_a_honap_es_a_teljes_datum_elotagkent_illeszkedik(date_search_conn):
    assert len(search_photos(date_search_conn, "2019:03:0")) == 7
    assert _names(date_search_conn, "2019:03:01") == {"photo_01.jpg"}


def test_a_datum_es_mas_keresoszo_egyutt_is_illeszkedik(date_search_conn):
    assert len(search_photos(date_search_conn, "2019:03 photo")) == 7


def test_a_kizaro_ev_a_felveteli_datumot_is_kizarja(date_search_conn):
    assert len(search_photos(date_search_conn, "photo -2019")) == 6


def test_az_ev_talalatot_a_taken_at_adja_a_mappanev_nelkul(date_search_conn):
    hits = search_photos(date_search_conn, "2021")

    assert len(hits) == 2
    assert {photo.taken_at[:4] for photo in hits} == {"2021"}
    assert {Path(photo.folder_path).name for photo in hits} == {"fajlido_pelda"}
