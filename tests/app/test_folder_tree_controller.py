"""FolderTreeController: a Mappakezelő fájának lusta, HÁTTÉRSZÁLAS
könyvtár-listázása (#231) — valódi ideiglenes könyvtárfán, mock nélkül."""

import pytest
from PySide6.QtCore import QEventLoop, QTimer


def _quit_on(signal):
    loop = QEventLoop()
    signal.connect(loop.quit)
    QTimer.singleShot(5000, loop.quit)
    return loop


@pytest.fixture
def make_controller(qt_app):
    """`FolderTreeController`-gyár, ami a teszt végén MEGVÁRJA a listázó
    háttérszálakat (#438, a #430 SIGSEGV-osztály elkerülése — a
    `test_webexport_controller.py` mintája)."""
    from picasapy.app.folder_tree_controller import FolderTreeController

    created = []

    def _make():
        controller = FolderTreeController()
        created.append(controller)
        return controller

    yield _make

    for controller in created:
        assert controller.waitForBackgroundWorkers(30.0), (
            "a mappalista háttérszála nem állt le"
        )


class TestRequestChildren:
    def test_lists_only_direct_subdirectories_sorted_by_name(
        self, make_controller, tmp_path
    ):
        (tmp_path / "zeta").mkdir()
        (tmp_path / "alfa").mkdir()
        (tmp_path / "alfa" / "melyebb").mkdir()
        (tmp_path / "fajl.txt").write_text("nem mappa")

        controller = make_controller()
        results = []
        controller.childrenLoaded.connect(
            lambda path, children: results.append((path, list(children)))
        )
        loop = _quit_on(controller.childrenLoaded)
        controller.requestChildren(str(tmp_path))
        loop.exec()

        assert len(results) == 1
        path, children = results[0]
        assert path == str(tmp_path)
        names = [c["name"] for c in children]
        assert names == ["alfa", "zeta"]  # ábécésorrend, a fájl kihagyva

    def test_has_children_true_only_when_subdirectory_exists(
        self, make_controller, tmp_path
    ):
        (tmp_path / "ures").mkdir()
        (tmp_path / "tele").mkdir()
        (tmp_path / "tele" / "gyerek").mkdir()

        controller = make_controller()
        results = []
        controller.childrenLoaded.connect(
            lambda path, children: results.append((path, list(children)))
        )
        loop = _quit_on(controller.childrenLoaded)
        controller.requestChildren(str(tmp_path))
        loop.exec()

        by_name = {c["name"]: c for c in results[0][1]}
        assert by_name["ures"]["hasChildren"] is False
        assert by_name["tele"]["hasChildren"] is True

    def test_hidden_directories_are_visible(self, make_controller, tmp_path):
        (tmp_path / ".rejtett").mkdir()
        (tmp_path / "lathato").mkdir()

        controller = make_controller()
        results = []
        controller.childrenLoaded.connect(
            lambda path, children: results.append((path, list(children)))
        )
        loop = _quit_on(controller.childrenLoaded)
        controller.requestChildren(str(tmp_path))
        loop.exec()

        names = [c["name"] for c in results[0][1]]
        assert names == [".rejtett", "lathato"]

    def test_picasa_root_order_starts_with_user_folders_then_root(self, tmp_path):
        from picasapy.app.folder_tree_controller import _root_entries

        roots = _root_entries(home=tmp_path, user="nemletezo-teszt-user")
        assert [(item["name"], item["path"]) for item in roots[:4]] == [
            ("Desktop", str(tmp_path / "Desktop")),
            ("Pictures", str(tmp_path / "Pictures")),
            ("Documents", str(tmp_path / "Documents")),
            ("/", "/"),
        ]

    def test_missing_directory_yields_empty_list_not_crash(
        self, make_controller, tmp_path
    ):
        missing = tmp_path / "nincs-ilyen"

        controller = make_controller()
        results = []
        controller.childrenLoaded.connect(
            lambda path, children: results.append((path, list(children)))
        )
        loop = _quit_on(controller.childrenLoaded)
        controller.requestChildren(str(missing))
        loop.exec()

        assert results == [(str(missing), [])]

    def test_children_are_plain_lists_of_dicts(self, make_controller, tmp_path):
        """QML-nek adott adat mindig `list` legyen, soha `tuple` (a projekt
        szabálya) — itt a jelzés paramétereinek típusát ellenőrizzük."""
        (tmp_path / "a").mkdir()

        controller = make_controller()
        results = []
        controller.childrenLoaded.connect(
            lambda path, children: results.append(children)
        )
        loop = _quit_on(controller.childrenLoaded)
        controller.requestChildren(str(tmp_path))
        loop.exec()

        assert isinstance(results[0], list)
        assert all(isinstance(item, dict) for item in results[0])


class TestBackgroundThreadTeardown:
    """#438 (a #430 SIGSEGV-osztály maradéka): a listázó háttérszál
    bevárható legyen, mielőtt a controller megsemmisül."""

    def test_wait_without_a_run_returns_immediately(self, make_controller):
        controller = make_controller()
        assert controller.waitForBackgroundWorkers(0.0)

    def test_wait_joins_the_worker_thread(self, make_controller, tmp_path):
        controller = make_controller()
        loop = _quit_on(controller.childrenLoaded)
        controller.requestChildren(str(tmp_path))
        loop.exec()
        assert controller.waitForBackgroundWorkers(30.0)
        assert not controller.backgroundWorkersRunning()
