"""#320: felhasználói egyéni gyűjtemények — létrehozás, mappa-áthelyezés,
JSON-perzisztencia (tiszta függvények, Qt nélkül)."""

from __future__ import annotations

from picasapy.app.custom_collections import (
    CustomCollection,
    create_collection,
    delete_collection,
    move_folder_to_collection,
    parse_custom_collections,
    rename_collection,
    serialize_custom_collections,
)


class TestParseRoundTrip:
    def test_empty_or_missing_raw_yields_empty_tuple(self):
        assert parse_custom_collections(None) == ()
        assert parse_custom_collections("") == ()

    def test_garbage_json_yields_empty_tuple(self):
        assert parse_custom_collections("nem json{{{") == ()

    def test_non_list_json_yields_empty_tuple(self):
        assert parse_custom_collections('{"name": "x"}') == ()

    def test_round_trip_preserves_name_and_folders(self):
        collections = (
            CustomCollection(name="Nyaralások", folders=("/a", "/b")),
            CustomCollection(name="Munka", folders=()),
        )
        raw = serialize_custom_collections(collections)
        assert parse_custom_collections(raw) == collections

    def test_malformed_items_are_skipped_not_fatal(self):
        raw = (
            '[{"name": "OK", "folders": ["/a"]}, "nem-dict", '
            '{"folders": ["/b"]}, {"name": "  "}, '
            '{"name": "FolderekVegyesen", "folders": ["/c", 5, null]}]'
        )
        result = parse_custom_collections(raw)
        assert result == (
            CustomCollection(name="OK", folders=("/a",)),
            CustomCollection(name="FolderekVegyesen", folders=("/c",)),
        )


class TestCreateCollection:
    def test_creates_empty_collection(self):
        result = create_collection((), "Nyaralások")
        assert result == (CustomCollection(name="Nyaralások"),)

    def test_strips_whitespace(self):
        result = create_collection((), "  Munka  ")
        assert result[0].name == "Munka"

    def test_blank_name_is_rejected(self):
        assert create_collection((), "   ") == ()

    def test_duplicate_name_case_insensitive_is_rejected(self):
        existing = (CustomCollection(name="Nyaralások"),)
        assert create_collection(existing, "nyaralások") == existing

    def test_appends_after_existing(self):
        existing = (CustomCollection(name="Munka"),)
        result = create_collection(existing, "Nyaralások")
        assert result == (
            CustomCollection(name="Munka"),
            CustomCollection(name="Nyaralások"),
        )


class TestRenameCollection:
    def test_renames_and_keeps_folders(self):
        existing = (CustomCollection(name="Régi", folders=("/a",)),)
        result = rename_collection(existing, "Régi", "Új")
        assert result == (CustomCollection(name="Új", folders=("/a",)),)

    def test_blank_new_name_is_noop(self):
        existing = (CustomCollection(name="X"),)
        assert rename_collection(existing, "X", "  ") == existing

    def test_colliding_new_name_is_noop(self):
        existing = (
            CustomCollection(name="A"),
            CustomCollection(name="B"),
        )
        assert rename_collection(existing, "A", "b") == existing

    def test_renaming_to_own_current_name_is_allowed(self):
        existing = (CustomCollection(name="A"),)
        result = rename_collection(existing, "A", "A")
        assert result == existing


class TestDeleteCollection:
    def test_removes_matching_collection(self):
        existing = (
            CustomCollection(name="A"),
            CustomCollection(name="B"),
        )
        assert delete_collection(existing, "A") == (CustomCollection(name="B"),)

    def test_missing_name_is_noop(self):
        existing = (CustomCollection(name="A"),)
        assert delete_collection(existing, "nincs-ilyen") == existing


class TestMoveFolderToCollection:
    def test_moves_folder_into_target(self):
        existing = (CustomCollection(name="Nyaralások"),)
        result = move_folder_to_collection(existing, "/kepek/balaton", "Nyaralások")
        assert result == (
            CustomCollection(name="Nyaralások", folders=("/kepek/balaton",)),
        )

    def test_removes_folder_from_previous_collection_first(self):
        existing = (
            CustomCollection(name="Régi", folders=("/kepek/balaton",)),
            CustomCollection(name="Új"),
        )
        result = move_folder_to_collection(existing, "/kepek/balaton", "Új")
        assert result == (
            CustomCollection(name="Régi", folders=()),
            CustomCollection(name="Új", folders=("/kepek/balaton",)),
        )

    def test_empty_target_removes_from_all_collections(self):
        existing = (CustomCollection(name="Régi", folders=("/kepek/balaton",)),)
        result = move_folder_to_collection(existing, "/kepek/balaton", "")
        assert result == (CustomCollection(name="Régi", folders=()),)

    def test_moving_into_unknown_collection_still_removes_from_others(self):
        existing = (CustomCollection(name="Régi", folders=("/kepek/balaton",)),)
        result = move_folder_to_collection(
            existing, "/kepek/balaton", "nincs-ilyen"
        )
        assert result == (CustomCollection(name="Régi", folders=()),)

    def test_moving_already_member_folder_is_idempotent(self):
        existing = (CustomCollection(name="Nyaralások", folders=("/a",)),)
        result = move_folder_to_collection(existing, "/a", "Nyaralások")
        assert result == existing
