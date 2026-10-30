"""Az importforrás-vezérlő forrásfelderítési és előnézeti segédei."""

from __future__ import annotations

import ctypes
import sqlite3
from collections.abc import Sequence
from ctypes import wintypes
from pathlib import Path, PurePosixPath, PureWindowsPath

from picasapy.importsource import ImportCandidate, duplicate_paths
from picasapy.index import IndexFastKeySource, PhotoRecord, all_photos
from picasapy.scanner import media_kind_of

from .display_mode_paint import current_display_mode_suffix


def _controller_module():
    """A régi modulon keresztül feloldott patch-pontokhoz."""
    from . import import_source_controller

    return import_source_controller


class _FacadeAttribute:
    """A patch-elt függőséget futásidőben a homlokzatról olvassa."""

    __slots__ = ("name",)

    def __init__(self, name: str) -> None:
        self.name = name

    def __call__(self, *args, **kwargs):
        return getattr(_controller_module(), self.name)(*args, **kwargs)

    def __getattr__(self, name: str):
        return getattr(getattr(_controller_module(), self.name), name)


# Ezeket a tesztek a korábbi importútvonalon helyettesítik.
_platform = _FacadeAttribute("_platform")
_read_mountinfo = _FacadeAttribute("_read_mountinfo")
QStorageInfo = _FacadeAttribute("QStorageInfo")
open_index = _FacadeAttribute("open_index")

_DRIVE_REMOVABLE = 2
_DRIVE_REMOTE = 4


def _linux_media_mount_points(mountinfo: str) -> list[str]:
    """A mountinfóból csak a felhasználói médiagyökerek alatti pontokat adja."""
    mount_roots = (PurePosixPath("/media"), PurePosixPath("/run/media"))
    mount_points: set[str] = set()
    for line in mountinfo.splitlines():
        fields = line.split()
        if len(fields) < 6:
            continue
        # A mountinfo a szóközt, tabot, sortörést és backslash-t oktális
        # escape-ként tárolja a mountpont mezőben.
        raw_path = fields[4]
        decoded_path = (
            raw_path.replace("\\040", " ")
            .replace("\\011", "\t")
            .replace("\\012", "\n")
            .replace("\\134", "\\")
        )
        mount_path = PurePosixPath(decoded_path)
        if not mount_path.is_absolute():
            continue
        if any(
            mount_path != root and mount_path.is_relative_to(root)
            for root in mount_roots
        ):
            mount_points.add(str(mount_path))
    return sorted(mount_points)

def discover_linux_mounted_sources() -> list[dict[str, str]]:
    """A Linux felhasználói médiagyökerei alatti mountokat adja vissza.

    A helyi mountlistából először csak a `/media` és `/run/media` alatti
    pontokat választjuk ki, utána a QStorageInfo ezek kész állapotát és
    címkéjét adja meg. Így más csatolt fájlrendszert (például hálózati
    meghajtót) nem kérdezünk le.
    """
    by_path: dict[str, dict[str, str]] = {}
    try:
        mountinfo = _read_mountinfo()
    except OSError:
        return []

    for path in _linux_media_mount_points(mountinfo):
        volume = QStorageInfo(path)
        if not volume.isReady():
            continue
        root = PurePosixPath(str(volume.rootPath()))
        # Csak a mountlistában felsorolt tényleges csatolási pontot fogadjuk
        # el; egy közönséges almappa saját QStorageInfo-ja a szülő mountot
        # adná vissza.
        if root != PurePosixPath(path):
            continue

        name = str(volume.name() or "").strip() or root.name
        if not name:
            continue
        by_path[path] = {"path": path, "name": name}

    return sorted(
        by_path.values(), key=lambda source: (source["name"].casefold(), source["path"])
    )

def _windows_drive_type(root_path: str) -> int:
    """A Windows meghajtótípusát adja vissza a GetDriveTypeW hívással."""
    get_drive_type = ctypes.windll.kernel32.GetDriveTypeW
    get_drive_type.argtypes = [wintypes.LPCWSTR]
    get_drive_type.restype = wintypes.UINT
    return int(get_drive_type(root_path))

def _has_dcim_directory(root_path: str) -> bool:
    """Megnézi, hogy a helyi meghajtó gyökerében van-e DCIM mappa."""
    return (Path(root_path) / "DCIM").is_dir()

_windows_drive_type_original = _windows_drive_type
_has_dcim_directory_original = _has_dcim_directory
_windows_drive_type = _FacadeAttribute("_windows_drive_type")
_has_dcim_directory = _FacadeAttribute("_has_dcim_directory")

def discover_windows_mounted_sources() -> list[dict[str, str]]:
    """Windows cserélhető meghajtókat és DCIM-et tartalmazó köteteket ad vissza.

    A távoli meghajtót a meghajtótípus alapján még azelőtt kihagyjuk, hogy
    készültséget, címkét vagy DCIM könyvtárat kérdeznénk le róla.
    """
    by_path: dict[str, dict[str, str]] = {}
    for volume in QStorageInfo.mountedVolumes():
        root_path = str(volume.rootPath() or "").strip()
        if not root_path:
            continue

        drive_type = _windows_drive_type(root_path)
        if drive_type == _DRIVE_REMOTE or not volume.isReady():
            continue
        if drive_type != _DRIVE_REMOVABLE and not _has_dcim_directory(root_path):
            continue

        path_key = root_path.casefold()
        name = str(volume.name() or "").strip()
        if not name:
            name = PureWindowsPath(root_path).drive or root_path
        by_path[path_key] = {"path": root_path, "name": name}

    return sorted(
        by_path.values(),
        key=lambda source: (source["name"].casefold(), source["path"].casefold()),
    )

def discover_mounted_sources() -> list[dict[str, str]]:
    """A támogatott platformokon felderített kártya- és USB-források.

    A PTP/MTP kamerák külön termékdöntésig nem kerülnek ebbe a listába.
    """
    active_platform = _platform()
    if active_platform.startswith("linux"):
        return discover_linux_mounted_sources()
    if active_platform == "win32":
        return discover_windows_mounted_sources()
    return []

def _thumb_url(photo_id: int) -> str:
    # #1656: a megjelenítési mód cimkéje (üres a no-op módokra)
    return f"image://thumbs/{photo_id}{current_display_mode_suffix()}"

def _preview_photo_record(index: int, candidate: ImportCandidate) -> PhotoRecord:
    """Ideiglenes rekord a forrás-előnézethez.

    NEGATÍV id-tartományt használ (a valódi indexbeli fotók mindig pozitív,
    autoincrement id-jűek) — a thumbnail-provider `register_additional_
    photos` regisztrációja így SOSE ütközhet valódi könyvtárbeli fotóval."""
    try:
        stat = candidate.path.stat()
        size, mtime_ns = stat.st_size, stat.st_mtime_ns
    except OSError:
        size, mtime_ns = 0, 0
    return PhotoRecord(
        id=-(index + 1),
        folder_path=str(candidate.path.parent),
        name=candidate.path.name,
        kind=media_kind_of(candidate.path.name) or "photo",
        size=size,
        mtime_ns=mtime_ns,
        star=False,
        caption=None,
        keywords=None,
        rotate_steps=0,
        filters=None,
        taken_at=candidate.date.isoformat() if candidate.date else None,
        orientation=1,
        width=None,
        height=None,
    )

def _library_paths(conn: sqlite3.Connection) -> tuple[Path, ...]:
    """A jelenleg indexelt könyvtár teljes fájl-útvonalai (#441 duplikátum-
    kizárás forrása). #4887: a rejtett mappák képei is — ez nem
    megjelenítés, hanem a „már a könyvtárban van-e” döntés."""
    return tuple(
        Path(record.folder_path) / record.name
        for record in all_photos(conn, include_hidden_folders=True)
    )

def _duplikatumok(
    index_path: str | Path, candidates: Sequence[ImportCandidate]
) -> frozenset[Path]:
    """A könyvtárral tartalom-egyező jelöltek (#441), index-hátterű
    gyorskulccsal (#1494).

    A kapcsolat az ÖSSZEVETÉS TELJES idejére nyitva marad — ezért tud a
    könyvtárbeli fájlok gyorskulcsa az indexből jönni, és ezért kerülhet
    az újonnan számolt kulcs mindjárt vissza is oda. A második importálási
    kör így a könyvtár változatlan képeinek fájlvégeit sem olvassa be újra.

    Hiányzó/olvashatatlan indexnél üres halmaz — az "Exclude Duplicates"
    ekkor egyszerűen nem talál semmit, NEM hibázik.

    ⚠️ A gyorstár mentése a KÉSZ eredményt nem ronthatja el: a `flush()`
    maga commitol és maga nyeli el a saját index-hibáit (ld. ott), ezért
    állhat a `finally`-ben. Csupasz `conn.commit()` itt SOHA ne legyen —
    zárolt vagy tele indexen az a külső `except`-be esne, és az "Exclude
    Duplicates" szótlanul nem találna semmit, a felhasználó pedig
    újraimportálná a már meglévő képeit (#1494 átnézés, 1. lelet)."""
    try:
        with open_index(index_path) as conn:
            kulcsforras = IndexFastKeySource(conn)
            try:
                return duplicate_paths(
                    candidates,
                    _library_paths(conn),
                    library_key_source=kulcsforras,
                )
            finally:
                kulcsforras.flush()
    except (OSError, sqlite3.Error):
        return frozenset()
