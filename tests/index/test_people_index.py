"""#26: az „Emberek" gyűjtemény összesítése a `.picasa.ini`
`[Contacts2]` + `faces=` szakaszaiból.

Séma-bővítés NÉLKÜL: az összesítés minden híváskor közvetlenül olvassa a
`has_ini=1` mappák ini-jét (ld. `picasapy.index.people` modul-docstring).
"""

from __future__ import annotations

import pytest

from picasapy.index import open_index, sync_tree
from picasapy.index.people import people_in_index, people_with, person_photos
from support.jpeg_factory import make_jpeg

_ROY = "b8e4117cf1d6615b"
_ANNA = "a1a2a3a4a5a6a7a8"
_UNKNOWN = "ffffffffffffffff"
_RECT = "3f840000c3509f84"


@pytest.fixture
def library(tmp_path):
    """Két mappa: az egyikben Roy két fotón, Anna egy fotón; a másikban Roy
    (más `person_id`-vel — a Contacts2 „csak lokális") még egy fotón."""
    root = tmp_path / "kepek"
    (root / "nyaralas").mkdir(parents=True)
    (root / "varos").mkdir()

    make_jpeg(root / "nyaralas" / "a.jpg")
    make_jpeg(root / "nyaralas" / "b.jpg")
    make_jpeg(root / "nyaralas" / "c.jpg")
    make_jpeg(root / "varos" / "d.jpg")

    (root / "nyaralas" / ".picasa.ini").write_text(
        f"[Contacts2]\n"
        f"{_ROY}=Roy Avery;;\n"
        f"{_ANNA}=Anna Kis;;\n"
        f"[a.jpg]\n"
        f"faces=rect64({_RECT}),{_ROY};\n"
        f"[b.jpg]\n"
        f"faces=rect64({_RECT}),{_ANNA};rect64({_RECT}),{_UNKNOWN};\n"
        f"[c.jpg]\n"
        f"star=yes\n",
        encoding="utf-8",
    )
    # más mappa, más helyi id ugyanarra a névre (Contacts2 "csak lokális")
    _ROY_LOCAL2 = "c9c8c7c6c5c4c3c2"
    (root / "varos" / ".picasa.ini").write_text(
        f"[Contacts2]\n"
        f"{_ROY_LOCAL2}=Roy Avery;;\n"
        f"[d.jpg]\n"
        f"faces=rect64({_RECT}),{_ROY_LOCAL2};\n",
        encoding="utf-8",
    )
    return root


@pytest.fixture
def conn(tmp_path, library):
    with open_index(tmp_path / "index.db") as connection:
        sync_tree(connection, library)
        yield connection


class TestPeopleCatalogue:
    def test_named_people_are_listed(self, conn):
        names = {p.name for p in people_in_index(conn)}
        assert names == {"Roy Avery", "Anna Kis"}

    def test_unidentified_face_is_not_a_person(self, conn):
        names = {p.name for p in people_in_index(conn)}
        assert "" not in names
        assert len(names) == 2

    def test_photo_counts_span_folders(self, conn):
        by_name = {p.name: p for p in people_in_index(conn)}
        assert by_name["Roy Avery"].photo_count == 2  # a.jpg + d.jpg
        assert by_name["Anna Kis"].photo_count == 1  # b.jpg

    def test_two_names_on_one_photo_count_once_each(self, conn, library):
        # b.jpg-n Anna egyszer szerepel — nincs duplikáció esélye itt, de
        # ha ugyanaz a név kétszer szerepelne egy fotón, egyszer számítson:
        ini = library / "nyaralas" / ".picasa.ini"
        ini.write_text(
            ini.read_text(encoding="utf-8").replace(
                f"faces=rect64({_RECT}),{_ANNA};rect64({_RECT}),{_UNKNOWN};",
                f"faces=rect64({_RECT}),{_ANNA};rect64({_RECT}),{_ANNA};",
            ),
            encoding="utf-8",
        )
        from picasapy.index import sync_tree as _sync

        _sync(conn, library, incremental=False)
        by_name = {p.name: p for p in people_in_index(conn)}
        assert by_name["Anna Kis"].photo_count == 1

    def test_sorted_by_name_casefold(self, conn):
        names = [p.name for p in people_in_index(conn)]
        assert names == sorted(names, key=str.casefold)

    def test_no_named_contacts_gives_empty_list(self, tmp_path):
        root = tmp_path / "ures"
        root.mkdir()
        make_jpeg(root / "x.jpg")
        with open_index(tmp_path / "index2.db") as connection:
            sync_tree(connection, root)
            assert people_in_index(connection) == ()


class TestPersonPhotos:
    def test_photos_of_a_person_span_folders(self, conn):
        names = sorted(p.name for p in person_photos(conn, "Roy Avery"))
        assert names == ["a.jpg", "d.jpg"]

    def test_photos_of_another_person(self, conn):
        names = sorted(p.name for p in person_photos(conn, "Anna Kis"))
        assert names == ["b.jpg"]

    def test_unknown_name_gives_nothing(self, conn):
        assert person_photos(conn, "Nincs Ilyen") == ()

    def test_empty_name_gives_nothing(self, conn):
        assert person_photos(conn, "") == ()


class TestResync:
    def test_removed_face_tag_drops_the_photo(self, conn, library):
        ini = library / "nyaralas" / ".picasa.ini"
        ini.write_text(
            ini.read_text(encoding="utf-8").replace(
                f"[a.jpg]\nfaces=rect64({_RECT}),{_ROY};\n", "[a.jpg]\n"
            ),
            encoding="utf-8",
        )
        from picasapy.index import sync_tree as _sync

        _sync(conn, library, incremental=False)
        names = sorted(p.name for p in person_photos(conn, "Roy Avery"))
        assert names == ["d.jpg"]


class TestPeopleWith:
    """#26: „Named People who appear WITH the currently selected person
    will be listed here." — az Emberek-panel negyedik állapota."""

    @pytest.fixture
    def shared_photo(self, library):
        """Roy és Anna EGYÜTT a c.jpg-n — a többi fotón külön-külön."""
        ini = library / "nyaralas" / ".picasa.ini"
        ini.write_text(
            ini.read_text(encoding="utf-8").replace(
                "[c.jpg]\nstar=yes\n",
                f"[c.jpg]\nfaces=rect64({_RECT}),{_ROY};"
                f"rect64({_RECT}),{_ANNA};\n",
            ),
            encoding="utf-8",
        )
        return library

    def test_it_lists_who_appears_together(self, tmp_path, shared_photo):
        with open_index(tmp_path / "egyutt.db") as conn:
            sync_tree(conn, shared_photo)
            together = people_with(conn, "Roy Avery")

        assert [(p.name, p.photo_count) for p in together] == [("Anna Kis", 1)]

    def test_the_person_is_not_listed_with_themselves(self, tmp_path, shared_photo):
        with open_index(tmp_path / "egyutt.db") as conn:
            sync_tree(conn, shared_photo)
            together = people_with(conn, "Roy Avery")

        assert all(p.name != "Roy Avery" for p in together)

    def test_someone_who_is_always_alone_has_nobody(self, conn):
        # az alap-könyvtárban Roy és Anna sosem szerepel közös fotón
        assert people_with(conn, "Roy Avery") == ()

    def test_an_unknown_name_is_not_an_error(self, conn):
        assert people_with(conn, "Nincs Ilyen") == ()
        assert people_with(conn, "") == ()
