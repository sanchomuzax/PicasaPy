"""#6608: a médiamentes, de ini-t tartalmazó mappa albumdefiníciója él."""

from pathlib import Path
import shutil

from picasapy.fileops import copy_photo, create_folder_for_move, move_photo
from picasapy.index import (
    album_photos,
    albums_in_index,
    open_index,
    sync_folder,
    sync_tree,
)
from picasapy.ini import parse_document, save_document
from picasapy.ini.albums import ensure_album, with_album
from support.jpeg_factory import make_jpeg

_ALBUM_TOKEN = "abc123"


def _album_state(conn):
    albums = {album.token: album for album in albums_in_index(conn)}
    album = albums.get(_ALBUM_TOKEN)
    members = {
        (Path(photo.folder_path).name, photo.name)
        for photo in album_photos(conn, _ALBUM_TOKEN)
    }
    return (album.photo_count if album is not None else None, members)


def _assert_incremental_matches_rebuild(conn, library, expected):
    incremental_state = _album_state(conn)
    with open_index(":memory:") as rebuilt:
        sync_tree(rebuilt, library)
        rebuilt_state = _album_state(rebuilt)

    assert incremental_state == rebuilt_state
    assert incremental_state == expected


def test_album_definition_survives_empty_source_folder_and_matches_rebuild(tmp_path):
    library = tmp_path / "library"
    library.mkdir()
    source = create_folder_for_move(library, "Album A")
    destination = create_folder_for_move(library, "Album B")
    for folder, name in (
        (source, "A-1.jpg"),
        (source, "A-2.jpg"),
        (destination, "B-1.jpg"),
    ):
        make_jpeg(folder / name)

    document = ensure_album(
        parse_document("[A-1.jpg]\n[A-2.jpg]\n"), _ALBUM_TOKEN, "Album"
    )
    document = with_album(document, "A-1.jpg", _ALBUM_TOKEN)
    save_document(document, source / ".picasa.ini")

    with open_index(tmp_path / "index.sqlite") as incremental:
        # 1. Kezdeti index.
        sync_tree(incremental, library)
        _assert_incremental_matches_rebuild(
            incremental, library, (1, {("Album A", "A-1.jpg")})
        )

        # 2. Az első kép áthelyezése; a megmaradt definíció továbbra is él.
        move_photo(source / "A-1.jpg", destination)
        sync_folder(incremental, library, source)
        sync_folder(incremental, library, destination)
        _assert_incremental_matches_rebuild(
            incremental, library, (1, {("Album B", "A-1.jpg")})
        )

        # 3. Az utolsó kép áthelyezése; az ini és az albumdefiníció megmarad.
        move_photo(source / "A-2.jpg", destination)
        sync_folder(incremental, library, source)
        sync_folder(incremental, library, destination)
        _assert_incremental_matches_rebuild(
            incremental, library, (1, {("Album B", "A-1.jpg")})
        )

        # 4. Egy tag visszamásolása; mindkét példány az album tagja.
        copy_photo(destination / "A-1.jpg", source)
        sync_folder(incremental, library, source)
        sync_folder(incremental, library, destination)
        _assert_incremental_matches_rebuild(
            incremental,
            library,
            (2, {("Album A", "A-1.jpg"), ("Album B", "A-1.jpg")}),
        )

        # A ténylegesen törölt definíciós mappa továbbra is árva albumot hagy.
        shutil.rmtree(source)
        sync_tree(incremental, library)
        _assert_incremental_matches_rebuild(incremental, library, (None, set()))
