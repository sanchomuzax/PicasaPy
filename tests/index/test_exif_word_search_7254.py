"""#7254: az EXIF Artist és Copyright szavai kereshetők és javasolhatók."""

from __future__ import annotations

import piexif
import pytest

from picasapy.index import open_index, search_photos, search_suggestions, sync_tree
from picasapy.metadata import read_file_metadata
from tests.support.jpeg_factory import make_jpeg


def _add_search_exif(path, *, artist=None, copyright=None, camera=None):
    zeroth = {}
    if artist is not None:
        zeroth[piexif.ImageIFD.Artist] = artist.encode("utf-8")
    if copyright is not None:
        zeroth[piexif.ImageIFD.Copyright] = copyright.encode("utf-8")
    if camera is not None:
        zeroth[piexif.ImageIFD.Make] = camera[0]
        zeroth[piexif.ImageIFD.Model] = camera[1]
    piexif.insert(piexif.dump({"0th": zeroth}), str(path))


@pytest.fixture
def exif_search_conn(tmp_path):
    root = tmp_path / "library"
    folder = root / "photos"
    folder.mkdir(parents=True)

    diego = make_jpeg(folder / "diego.jpg")
    _add_search_exif(
        diego,
        artist="Diego Delso",
        copyright="CC-BY-SA 4.0",
    )
    slusarczyk = make_jpeg(folder / "case.jpg")
    _add_search_exif(
        slusarczyk,
        artist="SLUSARCZYK",
        camera=("Centered", "Inches"),
    )

    with open_index(tmp_path / "index.db") as conn:
        sync_tree(conn, root)
        yield conn, diego, slusarczyk


def _names(conn, query):
    return {photo.name for photo in search_photos(conn, query)}


def test_metadata_reader_exposes_artist_and_copyright(exif_search_conn):
    _conn, diego, _slusarczyk = exif_search_conn

    metadata = read_file_metadata(diego)

    assert metadata.artist == "Diego Delso"
    assert metadata.copyright == "CC-BY-SA 4.0"


def test_artist_and_copyright_words_are_casefolded_prefix_search_terms(
    exif_search_conn,
):
    conn, _diego, _slusarczyk = exif_search_conn

    assert _names(conn, "delso") == {"diego.jpg"}
    assert _names(conn, "diego delso") == {"diego.jpg"}
    assert _names(conn, "slusar") == {"case.jpg"}
    assert _names(conn, "cc") == {"diego.jpg"}
    assert _names(conn, "sa") == {"diego.jpg"}


def test_unmeasured_exif_fields_and_single_digit_tokens_are_not_indexed(
    exif_search_conn,
):
    conn, _diego, _slusarczyk = exif_search_conn

    assert _names(conn, "centered") == set()
    assert _names(conn, "inches") == set()
    assert _names(conn, "4") == set()


def test_artist_and_copyright_words_are_lowercase_word_suggestions(
    exif_search_conn,
):
    conn, _diego, _slusarczyk = exif_search_conn

    delso = {
        row.name: row.count for row in search_suggestions(conn, "del")
        if row.kind == "word"
    }
    copyright_words = {
        row.name: row.count for row in search_suggestions(conn, "s")
        if row.kind == "word"
    }

    assert delso["delso"] == 1
    assert copyright_words["sa"] == 1
