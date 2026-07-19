"""Mappánként csoportosított találati modell (#7) — tiszta függvények."""

from picasapy.app.search_results import group_by_folder, groups_to_qml
from picasapy.index.queries import PhotoRecord


def _rec(folder: str, name: str, taken_at: str | None = None) -> PhotoRecord:
    return PhotoRecord(
        id=hash((folder, name)) & 0xFFFF,
        folder_path=folder,
        name=name,
        kind="jpeg",
        size=100,
        mtime_ns=0,
        star=False,
        caption=None,
        keywords=None,
        rotate_steps=0,
        filters=None,
        taken_at=taken_at,
        orientation=1,
        width=8,
        height=6,
    )


class TestGroupByFolder:
    def test_groups_follow_record_order(self):
        records = (
            _rec("/kepek/a", "1.jpg"),
            _rec("/kepek/a", "2.jpg"),
            _rec("/kepek/b", "3.jpg"),
        )
        groups = group_by_folder(records)
        assert [g.folder_path for g in groups] == ["/kepek/a", "/kepek/b"]
        assert [len(g.photos) for g in groups] == [2, 1]

    def test_folder_name_is_last_segment(self):
        groups = group_by_folder((_rec("/kepek/nyaralas", "1.jpg"),))
        assert groups[0].folder_name == "nyaralas"

    def test_windows_path_name(self):
        groups = group_by_folder((_rec("C:\\Kepek\\Nyaralas", "1.jpg"),))
        assert groups[0].folder_name == "Nyaralas"

    def test_first_row_of_each_group_recorded(self):
        # A QML-rácsnak kell: melyik sorindexnél kezdődik a csoport.
        records = (
            _rec("/a", "1.jpg"),
            _rec("/a", "2.jpg"),
            _rec("/b", "3.jpg"),
        )
        groups = group_by_folder(records)
        assert [g.first_row for g in groups] == [0, 2]

    def test_group_date_from_earliest_photo(self):
        records = (
            _rec("/a", "1.jpg", "2025-06-02T10:00:00"),
            _rec("/a", "2.jpg", "2025-05-01T09:00:00"),
        )
        groups = group_by_folder(records)
        assert groups[0].earliest_taken_at == "2025-05-01T09:00:00"

    def test_no_dates_gives_none(self):
        groups = group_by_folder((_rec("/a", "1.jpg"),))
        assert groups[0].earliest_taken_at is None

    def test_empty_input(self):
        assert group_by_folder(()) == ()

    def test_groups_are_immutable(self):
        groups = group_by_folder((_rec("/a", "1.jpg"),))
        assert isinstance(groups, tuple)
        assert isinstance(groups[0].photos, tuple)


class TestGroupsToQml:
    def test_row_offsets_are_global(self, qt_app):
        records = (
            _rec("/a", "1.jpg"),
            _rec("/a", "2.jpg"),
            _rec("/b", "3.jpg"),
        )
        groups = group_by_folder(records)
        qml_groups = groups_to_qml(groups)
        assert [g["folderName"] for g in qml_groups] == ["a", "b"]
        assert [p["row"] for p in qml_groups[0]["photos"]] == [0, 1]
        assert [p["row"] for p in qml_groups[1]["photos"]] == [2]
        assert qml_groups[0]["photos"][0]["name"] == "1.jpg"

    def test_empty_groups(self, qt_app):
        assert groups_to_qml(()) == []


class TestHasEditsField:
    def test_groups_to_qml_carries_has_edits(self):
        # #100: a keresési találat-rács is viszi a szerkesztettség-jelet
        edited = _rec("/kepek/a", "1.jpg")
        from dataclasses import replace

        edited = replace(edited, filters="enhance=1;")
        plain = _rec("/kepek/a", "2.jpg")
        groups = groups_to_qml(group_by_folder((edited, plain)))
        photos = groups[0]["photos"]
        assert photos[0]["hasEdits"] is True
        assert photos[1]["hasEdits"] is False
