"""DiscoveryController: meglévő Picasa-telepítés felismerése + átvétele
(#146) — a felderítés-API-t (scanner/discovery.py, #199) mockolva teszteljük,
a valós Wine/NAS-környezet nélkül."""

import pytest
from PySide6.QtCore import QEventLoop, QTimer


def _quit_on(signal):
    """QEventLoop, ami a `signal` érkezésekor (vagy 5 s vészfékkel) kilép —
    a `discoverPicasa` háttérszálas jelzésére váró tesztekhez (a
    test_controller.py mintáját követve)."""
    loop = QEventLoop()
    signal.connect(loop.quit)
    QTimer.singleShot(5000, loop.quit)
    return loop


@pytest.fixture
def added(monkeypatch):
    """A `discoverPicasa`-t háttérszál helyett szinkronban futtatjuk-e vagy
    sem — itt csak az `adoptWatchedFolders`-hez kellő gyűjtő-lista."""
    return []


@pytest.fixture
def controller(qt_app, added):
    from picasapy.app.discovery_controller import DiscoveryController

    return DiscoveryController(add_folder=added.append)


class TestDiscoverPicasa:
    def test_emits_proposed_folders_from_found_installations(
        self, controller, monkeypatch
    ):
        from picasapy.scanner import PicasaInstallation

        installation = PicasaInstallation(
            label="Wine (~/.wine), anna",
            picasa2_dir=None,
            picasa2albums_dir=None,
            watched_folders_file=None,
        )
        monkeypatch.setattr(
            "picasapy.app.discovery_controller.discover_installations",
            lambda: (installation,),
        )
        monkeypatch.setattr(
            "picasapy.app.discovery_controller.propose_watched_folders",
            lambda inst, remap: ("/mnt/nas/fotok", "/mnt/nas/videok"),
        )
        results = []
        controller.discoveryFinished.connect(
            lambda folders, count: results.append((list(folders), count))
        )
        loop = _quit_on(controller.discoveryFinished)
        controller.discoverPicasa()
        loop.exec()
        assert results == [(["/mnt/nas/fotok", "/mnt/nas/videok"], 1)]

    def test_deduplicates_proposed_folders_across_installations(
        self, controller, monkeypatch
    ):
        from picasapy.scanner import PicasaInstallation

        inst_a = PicasaInstallation("A", None, None, None)
        inst_b = PicasaInstallation("B", None, None, None)
        monkeypatch.setattr(
            "picasapy.app.discovery_controller.discover_installations",
            lambda: (inst_a, inst_b),
        )

        def fake_propose(inst, remap):
            return ("/mnt/nas/fotok",)

        monkeypatch.setattr(
            "picasapy.app.discovery_controller.propose_watched_folders",
            fake_propose,
        )
        results = []
        controller.discoveryFinished.connect(
            lambda folders, count: results.append((list(folders), count))
        )
        loop = _quit_on(controller.discoveryFinished)
        controller.discoverPicasa()
        loop.exec()
        assert results == [(["/mnt/nas/fotok"], 2)]

    def test_emits_empty_when_nothing_found(self, controller, monkeypatch):
        monkeypatch.setattr(
            "picasapy.app.discovery_controller.discover_installations",
            lambda: (),
        )
        results = []
        controller.discoveryFinished.connect(
            lambda folders, count: results.append((list(folders), count))
        )
        loop = _quit_on(controller.discoveryFinished)
        controller.discoverPicasa()
        loop.exec()
        assert results == [([], 0)]


class TestAdoptWatchedFolders:
    def test_forwards_each_path_to_add_folder(self, controller, added):
        controller.adoptWatchedFolders(["/mnt/nas/fotok", "/mnt/nas/videok"])
        assert added == ["/mnt/nas/fotok", "/mnt/nas/videok"]

    def test_repeated_call_is_safe_when_add_folder_dedupes(self, qt_app):
        """A tényleges dedup-ot az `addWatchedFolder` végzi (path in
        self._roots) — itt csak azt ellenőrizzük, hogy a controller minden
        hívást változatlanul továbbad, ismételt hívás sem dob hibát."""
        from picasapy.app.discovery_controller import DiscoveryController

        roots: list[str] = []

        def add_folder(path: str) -> None:
            if path not in roots:
                roots.append(path)

        controller = DiscoveryController(add_folder=add_folder)
        controller.adoptWatchedFolders(["/mnt/nas/fotok"])
        controller.adoptWatchedFolders(["/mnt/nas/fotok"])
        assert roots == ["/mnt/nas/fotok"]

    def test_ignores_empty_paths(self, controller, added):
        controller.adoptWatchedFolders(["", "/mnt/nas/fotok"])
        assert added == ["/mnt/nas/fotok"]


class TestOpenImportDialog:
    def test_emits_dialog_requested(self, controller):
        events = []
        controller.dialogRequested.connect(lambda: events.append(True))
        controller.openImportDialog()
        assert events == [True]
