"""A fa-mappanézet vezérlője — #702.

Itt az ÁLLAPOT viselkedését mérjük (mely ágak nyitottak, mikor szól a
jelzés), a kirajzolást a
`tests/app/qml_functional/test_folder_hierarchy_view_702.py` méri.
"""

from __future__ import annotations

import pytest

from picasapy.app.folder_hierarchy_controller import FolderHierarchyController

_FOLDERS = [
    {"path": "/mnt/photo/Kepek/wallpapers", "count": 18},
    {"path": "/mnt/photo/Kepek/AI", "count": 92},
    {"path": "/mnt/photo/Videok", "count": 3},
]


@pytest.fixture
def controller(qt_app):
    ctrl = FolderHierarchyController()
    ctrl.setFolders(_FOLDERS)
    return ctrl


def _paths(controller) -> list[str]:
    return [row["path"] for row in controller.rows]


class TestTheInitialState:
    def test_only_the_view_root_is_listed(self, controller):
        assert _paths(controller) == [""]

    def test_the_root_knows_it_can_be_opened(self, controller):
        assert controller.rows[0]["hasChildren"] is True


class TestToggling:
    def test_toggle_opens_then_closes(self, controller):
        controller.toggle("")
        assert _paths(controller) == ["", "/"]

        controller.toggle("")
        assert _paths(controller) == [""]

    def test_expand_is_idempotent(self, controller):
        controller.expand("")
        before = _paths(controller)
        controller.expand("")

        assert _paths(controller) == before


class TestTheTwoHierFolderCommands:
    """`Folder::ID_HIER_FOLDER_EXPAND` / `..._COLLAPSE`."""

    def test_expand_all_lists_every_folder(self, controller):
        controller.expandAll()

        for folder in _FOLDERS:
            assert folder["path"] in _paths(controller)

    def test_collapse_all_returns_to_the_root(self, controller):
        controller.expandAll()
        controller.collapseAll()

        assert _paths(controller) == [""]


class TestRevealPath:
    """Máshonnan (keresés, rács) érkező kijelölésnél a fa nyisson odáig."""

    def test_every_ancestor_of_the_target_opens(self, controller):
        controller.revealPath("/mnt/photo/Kepek/AI")

        assert "/mnt/photo/Kepek/AI" in _paths(controller)

    def test_the_siblings_along_the_way_become_visible(self, controller):
        # a kinyitott ősök testvérei is látszanak — ez a fa természetes
        # következménye, nem hiba (a felhasználó látja, hova nyílt ki)
        controller.revealPath("/mnt/photo/Kepek/AI")

        assert "/mnt/photo/Videok" in _paths(controller)
        assert "/mnt/photo/Kepek/wallpapers" in _paths(controller)


class TestTheSimplifiedSwitch:
    """`eMenuView::ID_VIEW_WATCHED` — a `SimplifiedHierarchy` kulcs."""

    def test_it_is_off_by_default(self, controller):
        assert controller.simplified is False

    def test_switching_it_on_shortens_the_chain(self, controller):
        controller.setSimplified(True)
        controller.toggle("")

        assert _paths(controller) == ["", "/mnt/photo"]

    def test_setting_the_same_value_emits_nothing(self, controller):
        seen: list[int] = []
        controller.simplifiedChanged.connect(lambda: seen.append(1))

        controller.setSimplified(False)

        assert seen == []

    def test_toggling_flips_the_switch(self, controller):
        """#1454: a menütétel ezt hívja — az eredeti is logikai tagadással
        írja vissza a `SimplifiedHierarchy` kulcsot (`0x005cc63f`)."""
        controller.toggleSimplified()
        assert controller.simplified is True

        controller.toggleSimplified()
        assert controller.simplified is False


class TestTheViewMode:
    """#1454: Egyszerű ↔ Fa — az eredetiben EGYETLEN bájt (`[+0x9d]`) két
    állapota, tehát kizáró pár (`0x00574b70`)."""

    def test_the_flat_list_is_the_default(self, controller):
        assert controller.treeView is False

    def test_switching_to_the_tree_emits_once(self, controller):
        seen: list[int] = []
        controller.treeViewChanged.connect(lambda: seen.append(1))

        controller.setTreeView(True)

        assert controller.treeView is True
        assert seen == [1]

    def test_setting_the_same_value_emits_nothing(self, controller):
        seen: list[int] = []
        controller.treeViewChanged.connect(lambda: seen.append(1))

        controller.setTreeView(False)

        assert seen == []

    def test_the_view_mode_does_not_touch_the_rows(self, controller):
        """A lapos és a fás nézet UGYANABBÓL a mappalistából él — a váltás
        nem építi újra a sorokat (az eredeti sem indexel újra, spec 4.3)."""
        controller.expandAll()
        elotte = _paths(controller)
        seen: list[int] = []
        controller.rowsChanged.connect(lambda: seen.append(1))

        controller.setTreeView(True)

        assert _paths(controller) == elotte
        assert seen == []

    def test_the_two_switches_are_independent(self, controller):
        """Az „Egyszerűsített fanézet" pipája a `[+0x9d]`-től FÜGGETLEN."""
        controller.toggleSimplified()
        controller.setTreeView(True)
        assert controller.simplified is True

        controller.setTreeView(False)
        assert controller.simplified is True


class TestSignals:
    def test_reloading_identical_folders_emits_nothing(self, controller):
        seen: list[int] = []
        controller.rowsChanged.connect(lambda: seen.append(1))

        controller.setFolders(_FOLDERS)

        assert seen == [], (
            "azonos adatnál a jelzés fölösleges lista-újraépítést és "
            "görgetés-ugrást okozna (a FolderListModel is ezért hallgat)"
        )

    def test_a_new_folder_emits_once(self, controller):
        seen: list[int] = []
        controller.rowsChanged.connect(lambda: seen.append(1))

        controller.setFolders([*_FOLDERS, {"path": "/mnt/photo/Uj", "count": 1}])

        assert seen == [1]

    def test_open_branches_survive_a_reload(self, controller):
        controller.expandAll()
        opened = _paths(controller)

        controller.setFolders([*_FOLDERS, {"path": "/mnt/photo/Uj", "count": 1}])

        assert set(opened) <= set(_paths(controller)), (
            "szinkron után a fa ott legyen, ahol a felhasználó hagyta"
        )


class TestAncestorMatching:
    """Az előtag-egyezés nem elég: a határon elválasztónak kell állnia."""

    def test_a_similarly_named_sibling_is_not_an_ancestor(self, qt_app):
        ctrl = FolderHierarchyController()
        ctrl.setFolders(
            [
                {"path": "/mnt/photoXYZ/mely", "count": 1},
                {"path": "/mnt/photo/Kepek", "count": 1},
            ]
        )

        ctrl.revealPath("/mnt/photoXYZ/mely")

        assert "/mnt/photo/Kepek" not in _paths(ctrl), (
            "a /mnt/photo ág nyílt ki, pedig a cél a /mnt/photoXYZ alatt van"
        )


class TestTheIndexFeedsTheTree:
    """A bekötés varrata (#702): a hasáb a fát az INDEX `folders` táblájából
    tölti, a `sorted_folder_rows()` során át — ugyanabból a forrásból, mint
    a lapos listát. Ezt a seamet külön meg kell mérni: a `setFolders()`
    `{"path", "count"}` alakot vár, a `sorted_folder_rows()` viszont hét
    mezős tuple-öket ad, és egy elcsúszott mező NÉMÁN üres fát okozna.
    """

    def test_a_valodi_index_soraibol_all_a_fa(self, qt_app, tmp_path):
        from picasapy.app.models import sorted_folder_rows
        from picasapy.index import open_index, sync_tree
        from support.jpeg_factory import make_jpeg

        gyoker = tmp_path / "kepek"
        for nev, darab in (("nyar", 2), ("tel", 1)):
            mappa = gyoker / nev
            mappa.mkdir(parents=True)
            for index in range(darab):
                make_jpeg(mappa / f"{index}.jpg", size=(20, 20))

        with open_index(tmp_path / "index.db") as conn:
            sync_tree(conn, gyoker)
            # pontosan az a kifejezés, amit az `application.py` bekötése használ
            folders = [
                {"path": path, "count": count}
                for _name, path, count, *_rest in sorted_folder_rows(conn)
            ]

        ctrl = FolderHierarchyController()
        ctrl.setFolders(folders)
        ctrl.expandAll()
        sorok = {row["path"]: row for row in ctrl.rows}

        assert str(gyoker / "nyar") in sorok, (
            f"a fa nem ismerte fel az indexelt mappákat: {sorted(sorok)}"
        )
        assert sorok[str(gyoker / "nyar")]["count"] == 2
        # a nézet-gyökér a RÉSZFA összes fotóját összegzi
        assert sorok[""]["count"] == 3


class TestOsLancWindowsUtvonallal:
    """A fanézetre váltás Windowson is kinyitja a kijelölt ősláncát (#1477).

    A fa csomópontjai `/`-rel épülnek, a kijelölt mappa útvonala viszont a
    rendszertől jön — Windowson `\\`-rel. A nyers `startswith` emiatt a
    második szint után elhasal.

    ⚠️ Ez a hiba a CI windows-lábán bukott ki, és a #1454 saját őre fogta
    meg: a kirajzolt sorok `['', 'C:', 'C:/Users']` maradtak, a kijelölt
    mappa nem látszott. Linuxon a teszt zöld volt — ezért kell ez az őr
    KIFEJEZETTEN a vegyes elválasztójú esetre, platformtól függetlenül.
    """

    @staticmethod
    def _osok(cel: str) -> set[str]:
        from picasapy.app.folder_hierarchy_controller import _is_ancestor

        jeloltek = ("C:", "C:/Users", "C:/Users/sancho", "C:/Users/sanchoXYZ")
        return {j for j in jeloltek if _is_ancestor(j, cel)}

    def test_a_windows_elvalaszto_nem_szakitja_meg_a_lancot(self):
        osok = self._osok("C:\\Users\\sancho\\Kepek")
        assert osok == {"C:", "C:/Users", "C:/Users/sancho"}, (
            "a `\\`-es célútvonalnál megszakadt az ősLánc — pontosan ez "
            f"buktatta a CI windows-lábát; kapott: {sorted(osok)}"
        )

    def test_a_hasonlo_nevu_testver_NEM_os(self):
        """A határon elválasztónak kell állnia — a régi garancia marad."""
        assert "C:/Users/sanchoXYZ" not in self._osok("C:\\Users\\sancho\\Kepek")

    def test_a_posix_ut_valtozatlanul_mukodik(self):
        from picasapy.app.folder_hierarchy_controller import _is_ancestor

        assert _is_ancestor("/mnt/photo", "/mnt/photo/2011")
        assert not _is_ancestor("/mnt/photo", "/mnt/photoXYZ")
