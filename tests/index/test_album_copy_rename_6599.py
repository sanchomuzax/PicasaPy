"""#6599: az albumtagság maradjon azonos a teljes újraépítéssel."""

from pathlib import Path

from picasapy.fileops import copy_photo, create_folder_for_move, rename_folder
from picasapy.index import (
    album_photos,
    albums_in_index,
    move_folder_tree,
    open_index,
    sync_folder,
    sync_tree,
)
from picasapy.ini import parse_document, save_document
from picasapy.ini.albums import ensure_album, with_album
from support.jpeg_factory import make_jpeg

_ALBUM_TOKEN = "abc123"


def _album_counts_and_members(conn):
    albums = {album.token: album for album in albums_in_index(conn)}
    members = {
        (Path(photo.folder_path).name, photo.name)
        for photo in album_photos(conn, _ALBUM_TOKEN)
    }
    return albums[_ALBUM_TOKEN].photo_count, members


def test_copy_tag_survives_source_folder_rename_and_rebuild(tmp_path):
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

    source_ini = ensure_album(
        parse_document("[A-1.jpg]\n"), _ALBUM_TOKEN, "Album"
    )
    source_ini = with_album(source_ini, "A-1.jpg", _ALBUM_TOKEN)
    save_document(source_ini, source / ".picasa.ini")
    save_document(
        parse_document("[B-1.jpg]\n"), destination / ".picasa.ini"
    )

    with open_index(tmp_path / "index.sqlite") as incremental:
        # 1–2. Kezdeti index, majd másolás és a két érintett mappa szinkronja.
        sync_tree(incremental, library)
        copied = copy_photo(source / "A-1.jpg", destination)
        sync_folder(incremental, library, source)
        sync_folder(incremental, library, destination)

        # A cél ini-je csak a másolt kép hivatkozását kapja meg; definíciót nem.
        destination_ini = (destination / ".picasa.ini").read_text(
            encoding="utf-8"
        )
        assert f"[.album:{_ALBUM_TOKEN}]" not in destination_ini
        assert f"albums={_ALBUM_TOKEN}" in destination_ini

        # 3. A definíciót tartalmazó forrásmappa átnevezése és indexbeli mozgatása.
        renamed = rename_folder(source, "Atnevezett 1")
        move_folder_tree(incremental, source, renamed)
        sync_folder(incremental, library, renamed.parent)
        sync_folder(incremental, library, renamed)

        incremental_count, incremental_members = _album_counts_and_members(
            incremental
        )
        assert incremental_count == 2
        assert incremental_members == {
            ("Atnevezett 1", "A-1.jpg"),
            ("Album B", copied.name),
        }

        # 4–5. Ugyanabból az ini-fából új index épül; a tagság és darabszám egyezzen.
        with open_index(":memory:") as rebuilt:
            sync_tree(rebuilt, library)
            rebuilt_count, rebuilt_members = _album_counts_and_members(rebuilt)

        assert rebuilt_count == incremental_count
        assert rebuilt_members == incremental_members
