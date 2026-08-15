"""A fa-mappanézet adatszerkezete — #702.

A `folder_hierarchy` modul Qt nélküli, tiszta függvényeket ad, ezért itt
QML és szálkezelés nélkül mérhető az a viselkedés, amit az eredeti Picasa
mutat (bizonyíték: `docs/specs/ui-audit-mainwindow.md` 1.4/1.7).
"""

from __future__ import annotations

from picasapy.app.folder_hierarchy import (
    ROOT_PATH,
    build_hierarchy,
    expandable_paths,
    flatten,
)

_FOLDERS = [
    {"path": "/mnt/photo/Kepek/wallpapers/space", "count": 7},
    {"path": "/mnt/photo/Kepek/wallpapers", "count": 18},
    {"path": "/mnt/photo/Kepek/AI", "count": 92},
    {"path": "/mnt/photo/Videok", "count": 3},
]


def _by_path(node):
    """Az egész fa útvonal → csomópont szótárként (könnyebb állításokhoz)."""
    result = {node.path: node}
    for child in node.children:
        result.update(_by_path(child))
    return result


class TestTheIntermediateLevelsExist:
    """A lapos listában nem szereplő köztes mappák is sorok lesznek — enélkül
    nem fa, hanem csoportosított lista lenne."""

    def test_unlisted_parents_become_nodes(self):
        nodes = _by_path(build_hierarchy(_FOLDERS))

        assert "/mnt/photo" in nodes
        assert "/mnt/photo/Kepek" in nodes

    def test_an_unlisted_parent_has_no_photos_of_its_own(self):
        nodes = _by_path(build_hierarchy(_FOLDERS))

        assert nodes["/mnt/photo/Kepek"].own == 0


class TestTheCountIsAggregated:
    """`Sajátgép (1 072)` = 227 + 842 + 3 — a fában a részfa összege áll."""

    def test_a_branch_sums_its_whole_subtree(self):
        nodes = _by_path(build_hierarchy(_FOLDERS))

        assert nodes["/mnt/photo/Kepek/wallpapers"].total == 25   # 18 + 7
        assert nodes["/mnt/photo/Kepek"].total == 117             # 25 + 92
        assert nodes[ROOT_PATH].total == 120                      # 117 + 3


class TestSiblingOrder:
    def test_siblings_are_sorted_case_insensitively(self):
        nodes = _by_path(build_hierarchy(_FOLDERS))
        kepek = nodes["/mnt/photo/Kepek"]

        assert [child.name for child in kepek.children] == ["AI", "wallpapers"]


class TestTheSimplifiedTreeView:
    """`SimplifiedHierarchy`: az egygyermekes, fotó nélküli köztes szintek
    összevonása."""

    def test_the_empty_chain_becomes_a_single_row(self):
        root = build_hierarchy(_FOLDERS, simplified=True)

        assert [child.path for child in root.children] == ["/mnt/photo"]
        assert root.children[0].name == "/mnt/photo"

    def test_a_branching_level_is_never_merged(self):
        root = build_hierarchy(_FOLDERS, simplified=True)
        photo = root.children[0]

        assert sorted(child.name for child in photo.children) == ["Kepek", "Videok"]

    def test_a_level_with_its_own_photos_is_never_merged(self):
        # a `wallpapers` egygyermekes, de VAN saját fotója (18) — a
        # felhasználó választhatja, tehát nem olvadhat össze
        folders = [
            {"path": "/mnt/photo/Kepek/wallpapers", "count": 18},
            {"path": "/mnt/photo/Kepek/wallpapers/space", "count": 7},
        ]
        nodes = _by_path(build_hierarchy(folders, simplified=True))

        assert "/mnt/photo/Kepek/wallpapers" in nodes
        assert "/mnt/photo/Kepek/wallpapers/space" in nodes


class TestWindowsPaths:
    """Importált Windows-útvonalak is előfordulnak a `folders` táblában."""

    def test_the_indexed_folder_keeps_its_exact_path(self):
        # a visszafelé alkotott alak (`C:/Users`) nem egyezne az index
        # `folders.path` értékével, és a sorra kattintás némán nem találna
        # mappát
        nodes = _by_path(
            build_hierarchy([{"path": r"C:\Users\Bob\Kepek", "count": 4}])
        )

        assert r"C:\Users\Bob\Kepek" in nodes


class TestFlattening:
    def test_a_closed_branch_hides_its_children(self):
        root = build_hierarchy(_FOLDERS)

        rows = flatten(root, frozenset())

        assert [row["path"] for row in rows] == [ROOT_PATH]

    def test_an_open_branch_shows_exactly_one_more_level(self):
        root = build_hierarchy(_FOLDERS)

        rows = flatten(root, frozenset({ROOT_PATH, "/"}))

        assert [row["path"] for row in rows] == [ROOT_PATH, "/", "/mnt"]

    def test_the_root_row_is_marked_so_qml_can_label_it(self):
        # a „My Computer" (`ViewRoot::All`) felirat a QML-ben él (qsTr),
        # nem Pythonban — ezért kell a sornak típusjelölés
        rows = flatten(build_hierarchy(_FOLDERS), frozenset())

        assert rows[0]["kind"] == "root"
        assert rows[0]["name"] == ""

    def test_depth_grows_by_one_per_level(self):
        rows = flatten(build_hierarchy(_FOLDERS), frozenset({ROOT_PATH, "/"}))

        assert [row["depth"] for row in rows] == [0, 1, 2]

    def test_expandable_paths_covers_every_branch(self):
        root = build_hierarchy(_FOLDERS)

        paths = expandable_paths(root)

        assert "/mnt/photo/Kepek" in paths
        # a levélnek nincs mit kinyitni
        assert "/mnt/photo/Videok" not in paths


class TestDegenerateInput:
    def test_an_empty_list_gives_a_lone_root(self):
        root = build_hierarchy([])

        assert root.children == ()
        assert root.total == 0

    def test_a_missing_count_is_treated_as_zero(self):
        root = build_hierarchy([{"path": "/a/b"}])

        assert root.total == 0

    def test_an_empty_path_is_ignored(self):
        root = build_hierarchy([{"path": "", "count": 5}])

        assert root.children == ()
