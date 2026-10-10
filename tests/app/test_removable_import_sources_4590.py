"""A #4590 Linuxon és Windowson is importforrásként kínálja a kártyákat."""

from __future__ import annotations

from PySide6.QtCore import QSettings


class _Volume:
    def __init__(
        self, root: str, name: str = "", *, ready: bool = True
    ) -> None:
        self._root = root
        self._name = name
        self._ready = ready

    def rootPath(self) -> str:  # noqa: N802
        return self._root

    def name(self) -> str:
        return self._name

    def isReady(self) -> bool:  # noqa: N802
        return self._ready


class _NetworkVolume(_Volume):
    def isReady(self) -> bool:  # noqa: N802
        raise AssertionError("a hálózati kötet állapotát nem szabad lekérdezni")

    def name(self) -> str:
        raise AssertionError("a hálózati kötet címkéjét nem szabad lekérdezni")


def test_refresh_lists_ready_volumes_beneath_linux_media_mount_roots(
    qt_app, monkeypatch, tmp_path
):
    from picasapy.app import import_source_controller as module

    mountinfo = "\n".join(
        (
            r"1 0 0:1 / /media/Photo\040Card rw - ext4 /dev/card rw",
            "2 0 0:2 / /run/media/sancho/SDXC rw - vfat /dev/sdcard rw",
            "3 0 0:3 / /media/not-ready rw - ext4 /dev/not-ready rw",
            "4 0 0:4 / /media rw - ext4 /dev/root rw",
            "5 0 0:5 / /media-backup/card rw - ext4 /dev/backup rw",
            "6 0 0:6 / /var/lib/photos rw - ext4 /dev/ordinary rw",
        )
    )
    by_path = {
        "/media/Photo Card": _Volume("/media/Photo Card", "Picasa photos"),
        "/run/media/sancho/SDXC": _Volume("/run/media/sancho/SDXC"),
        "/media/not-ready": _Volume("/media/not-ready", ready=False),
    }
    queried_paths = []

    class _StorageInfo:
        def __new__(cls, path):
            queried_paths.append(path)
            return by_path[path]

    monkeypatch.setattr(module, "QStorageInfo", _StorageInfo)
    monkeypatch.setattr(module, "_platform", lambda: "linux")
    monkeypatch.setattr(module, "_read_mountinfo", lambda: mountinfo)

    controller = module.ImportSourceController(
        None,
        add_folder=lambda _path: None,
        settings=QSettings(
            str(tmp_path / "settings.ini"), QSettings.Format.IniFormat
        ),
    )
    controller.refreshMountedSources()

    assert list(controller.mountedSources) == [
        {"path": "/media/Photo Card", "name": "Picasa photos"},
        {"path": "/run/media/sancho/SDXC", "name": "SDXC"},
    ]
    assert queried_paths == [
        "/media/Photo Card",
        "/media/not-ready",
        "/run/media/sancho/SDXC",
    ]


def test_windows_refresh_lists_removable_and_dcim_volumes_without_scanning_network(
    qt_app, monkeypatch, tmp_path
):
    from picasapy.app import import_source_controller as module

    volumes = [
        _Volume("E:/", "SD Card"),
        _Volume("F:/", "Camera"),
        _NetworkVolume("Z:/", "Network photos"),
        _Volume("C:/", "System"),
        _Volume("G:/", "Unavailable", ready=False),
    ]

    class _StorageInfo:
        @staticmethod
        def mountedVolumes():  # noqa: N802
            return volumes

    drive_types = {
        "E:/": 2,  # DRIVE_REMOVABLE
        "F:/": 3,  # DRIVE_FIXED, but contains DCIM
        "Z:/": 4,  # DRIVE_REMOTE
        "C:/": 3,  # DRIVE_FIXED without DCIM
        "G:/": 2,  # not ready
    }
    dcim_checks = []

    monkeypatch.setattr(module, "_platform", lambda: "win32")
    monkeypatch.setattr(module, "QStorageInfo", _StorageInfo)
    monkeypatch.setattr(
        module,
        "_windows_drive_type",
        lambda root: drive_types[root],
    )

    def _has_dcim(root):
        dcim_checks.append(root)
        return root == "F:/"

    monkeypatch.setattr(
        module, "_has_dcim_directory", _has_dcim
    )

    controller = module.ImportSourceController(
        None,
        add_folder=lambda _path: None,
        settings=QSettings(
            str(tmp_path / "settings.ini"), QSettings.Format.IniFormat
        ),
    )
    controller.refreshMountedSources()

    assert list(controller.mountedSources) == [
        {"path": "F:/", "name": "Camera"},
        {"path": "E:/", "name": "SD Card"},
    ]
    assert dcim_checks == ["F:/", "C:/"]
