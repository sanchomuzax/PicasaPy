"""FolderTreeController: a Mappakezelő fájának lusta, HÁTTÉRSZÁLAS
könyvtár-listázása (#231) — valódi ideiglenes könyvtárfán, mock nélkül."""

from PySide6.QtCore import QEventLoop, QTimer


def _quit_on(signal):
    loop = QEventLoop()
    signal.connect(loop.quit)
    QTimer.singleShot(5000, loop.quit)
    return loop


class TestRequestChildren:
    def test_lists_only_direct_subdirectories_sorted_by_name(self, qt_app, tmp_path):
        from picasapy.app.folder_tree_controller import FolderTreeController

        (tmp_path / "zeta").mkdir()
        (tmp_path / "alfa").mkdir()
        (tmp_path / "alfa" / "melyebb").mkdir()
        (tmp_path / "fajl.txt").write_text("nem mappa")

        controller = FolderTreeController()
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

    def test_has_children_true_only_when_subdirectory_exists(self, qt_app, tmp_path):
        from picasapy.app.folder_tree_controller import FolderTreeController

        (tmp_path / "ures").mkdir()
        (tmp_path / "tele").mkdir()
        (tmp_path / "tele" / "gyerek").mkdir()

        controller = FolderTreeController()
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

    def test_hidden_directories_are_skipped(self, qt_app, tmp_path):
        from picasapy.app.folder_tree_controller import FolderTreeController

        (tmp_path / ".rejtett").mkdir()
        (tmp_path / "lathato").mkdir()

        controller = FolderTreeController()
        results = []
        controller.childrenLoaded.connect(
            lambda path, children: results.append((path, list(children)))
        )
        loop = _quit_on(controller.childrenLoaded)
        controller.requestChildren(str(tmp_path))
        loop.exec()

        names = [c["name"] for c in results[0][1]]
        assert names == ["lathato"]

    def test_missing_directory_yields_empty_list_not_crash(self, qt_app, tmp_path):
        from picasapy.app.folder_tree_controller import FolderTreeController

        missing = tmp_path / "nincs-ilyen"

        controller = FolderTreeController()
        results = []
        controller.childrenLoaded.connect(
            lambda path, children: results.append((path, list(children)))
        )
        loop = _quit_on(controller.childrenLoaded)
        controller.requestChildren(str(missing))
        loop.exec()

        assert results == [(str(missing), [])]

    def test_children_are_plain_lists_of_dicts(self, qt_app, tmp_path):
        """QML-nek adott adat mindig `list` legyen, soha `tuple` (a projekt
        szabálya) — itt a jelzés paramétereinek típusát ellenőrizzük."""
        from picasapy.app.folder_tree_controller import FolderTreeController

        (tmp_path / "a").mkdir()

        controller = FolderTreeController()
        results = []
        controller.childrenLoaded.connect(
            lambda path, children: results.append(children)
        )
        loop = _quit_on(controller.childrenLoaded)
        controller.requestChildren(str(tmp_path))
        loop.exec()

        assert isinstance(results[0], list)
        assert all(isinstance(item, dict) for item in results[0])
