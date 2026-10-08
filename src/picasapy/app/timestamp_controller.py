"""A kijelölt képek dátumának módosítása az EXIF-ben (#4332, #4693)."""

from __future__ import annotations

import ctypes
import os
import sys
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import Slot

from picasapy.index import open_index, sync_tree
from picasapy.metadata import read_exif_details
from picasapy.metadata.tiff_helyben import (
    Valtozas,
    ascii_ertek,
    frissitett_tiff,
)


_JPEG_SOI = b"\xff\xd8"
_EXIF_APP1_PREFIX = b"Exif\x00\x00"
_STANDALONE_MARKERS = {0x01, 0xD8, 0xD9, *range(0xD0, 0xD8)}


def _jpeg_segments(data: bytes) -> tuple[list[tuple[int, bytes]], bytes]:
    """A JPEG fejlécszegmensei és az SOS-tól kezdődő változatlan farok."""
    if not data.startswith(_JPEG_SOI):
        raise ValueError("a forrás nem JPEG")
    segments: list[tuple[int, bytes]] = []
    pos = len(_JPEG_SOI)
    while pos < len(data):
        kezdet = pos
        if data[pos] != 0xFF:
            break
        marker_pos = pos + 1
        while marker_pos < len(data) and data[marker_pos] == 0xFF:
            marker_pos += 1
        if marker_pos >= len(data):
            break
        marker = data[marker_pos]
        if marker == 0xDA:
            break
        if marker in _STANDALONE_MARKERS:
            pos = marker_pos + 1
        else:
            length_pos = marker_pos + 1
            if length_pos + 2 > len(data):
                raise ValueError("csonka JPEG-szegmens")
            length = int.from_bytes(data[length_pos : length_pos + 2], "big")
            if length < 2:
                raise ValueError("hibás JPEG-szegmenshossz")
            pos = length_pos + length
            if pos > len(data):
                raise ValueError("csonka JPEG-szegmens")
        segments.append((marker, data[kezdet:pos]))
    return segments, data[pos:]


def _exif_app1(tiff: bytes) -> bytes:
    """EXIF TIFF-blokk JPEG APP1 szegmensben."""
    payload = _EXIF_APP1_PREFIX + tiff
    length = len(payload) + 2
    if length > 0xFFFF:
        raise ValueError("az EXIF-szegmens túllépi a JPEG-határt")
    return b"\xff\xe1" + length.to_bytes(2, "big") + payload


def _write_exif_datetime_original(path: str | Path, target: datetime) -> None:
    """A DateTimeOriginal-t biztonságos TIFF-frissítéssel, .tmp cserével írja."""
    source = Path(path)
    temp = source.with_suffix(source.suffix + ".tmp")
    try:
        original = source.read_bytes()
        segments, suffix = _jpeg_segments(original)
        exif_index = next(
            (
                index
                for index, (marker, segment) in enumerate(segments)
                if marker == 0xE1 and segment[4:].startswith(_EXIF_APP1_PREFIX)
            ),
            None,
        )
        exif_tiff = (
            segments[exif_index][1][4 + len(_EXIF_APP1_PREFIX) :]
            if exif_index is not None
            else None
        )
        changes = [
            Valtozas(
                "Exif",
                0x9003,
                ascii_ertek(target.strftime("%Y:%m:%d %H:%M:%S")),
            )
        ]
        updated_segment = _exif_app1(frissitett_tiff(exif_tiff, changes))
        if exif_index is None:
            app0_index = next(
                (index for index, (marker, _segment) in enumerate(segments) if marker == 0xE0),
                None,
            )
            segments.insert(
                (app0_index + 1) if app0_index is not None else 0,
                (0xE1, updated_segment),
            )
        else:
            segments[exif_index] = (0xE1, updated_segment)

        with temp.open("wb") as output:
            output.write(_JPEG_SOI)
            for _marker, segment in segments:
                output.write(segment)
            output.write(suffix)
            output.flush()
            os.fsync(output.fileno())
        os.replace(temp, source)
    finally:
        temp.unlink(missing_ok=True)


def _platform() -> str:
    """A futó platform — külön függvény, hogy a teszt helyettesíthesse (#1217)."""
    return sys.platform


def _set_creation_time_ns(path: str | Path, timestamp_ns: int) -> None:
    """Windows alatt beállítja a létrehozási időt; POSIX-on nincs ilyen API."""
    if _platform() != "win32":
        return

    class _FileTime(ctypes.Structure):
        _fields_ = [("low", ctypes.c_uint32), ("high", ctypes.c_uint32)]

    epoch_ticks = 116_444_736_000_000_000
    filetime = timestamp_ns // 100 + epoch_ticks
    creation = _FileTime(filetime & 0xFFFFFFFF, filetime >> 32)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.CreateFileW.restype = ctypes.c_void_p
    kernel32.CreateFileW.argtypes = [
        ctypes.c_wchar_p,
        ctypes.c_uint32,
        ctypes.c_uint32,
        ctypes.c_void_p,
        ctypes.c_uint32,
        ctypes.c_uint32,
        ctypes.c_void_p,
    ]
    kernel32.SetFileTime.argtypes = [
        ctypes.c_void_p,
        ctypes.POINTER(_FileTime),
        ctypes.POINTER(_FileTime),
        ctypes.POINTER(_FileTime),
    ]
    kernel32.CloseHandle.argtypes = [ctypes.c_void_p]
    handle = kernel32.CreateFileW(
        str(path),
        0x0100,  # FILE_WRITE_ATTRIBUTES
        0x00000001 | 0x00000002 | 0x00000004,  # read/write/delete sharing
        None,
        3,  # OPEN_EXISTING
        0x00000080,  # FILE_ATTRIBUTE_NORMAL
        None,
    )
    invalid_handle = ctypes.c_void_p(-1).value
    if handle in (None, invalid_handle):
        raise ctypes.WinError(ctypes.get_last_error())
    try:
        if not kernel32.SetFileTime(handle, ctypes.byref(creation), None, None):
            raise ctypes.WinError(ctypes.get_last_error())
    finally:
        kernel32.CloseHandle(handle)


def _adjust_photo_file_date(path: str | Path, target: datetime) -> bool:
    """EXIF-írás és a mért DateTime/fájlrendszeridő ágak.

    Visszatérés: sikerült-e a DateTimeOriginal kiírása. Írási hiba esetén az
    eredeti tartalékág kizárólag a létrehozási időt állítja.
    """
    source = Path(path)
    before = source.stat()
    modified_at = read_exif_details(source).datetime_modified
    try:
        _write_exif_datetime_original(source, target)
    except Exception:  # noqa: BLE001 — az eredeti tartalékág csak fájlidőt ír
        _set_creation_time_ns(source, round(target.timestamp() * 1_000_000_000))
        return False

    try:
        old_datetime = datetime.fromisoformat(modified_at) if modified_at else None
    except (TypeError, ValueError):
        old_datetime = None
    delta_ns = (
        round((target - old_datetime).total_seconds() * 1_000_000_000)
        if old_datetime is not None
        else 0
    )
    os.utime(
        source,
        ns=(before.st_atime_ns + delta_ns, before.st_mtime_ns + delta_ns),
    )
    _set_creation_time_ns(source, before.st_ctime_ns)
    return True


def _photo_datetime(photo) -> datetime:
    """A jelenlegi felvételi idő, az indexelt fájlidőre visszaesve."""
    if photo.taken_at:
        return datetime.fromisoformat(photo.taken_at)
    return datetime.fromtimestamp(photo.sort_mtime_ns / 1_000_000_000)


class TimestampAdjustmentMixin:
    """A PhotoOpsMixin háttéríró útját használó indexművelet."""

    @Slot(int, result="QVariantMap")
    def adjustTimestampPreview(self, row: int) -> dict[str, str]:
        photos = self._photos.photos
        if not 0 <= int(row) < len(photos):
            return {"dateTime": "", "thumbnailUrl": ""}
        photo = photos[int(row)]
        return {
            "dateTime": _photo_datetime(photo).strftime("%Y-%m-%d %H:%M:%S"),
            "thumbnailUrl": f"image://thumbs/{photo.id}",
        }

    @Slot(list, str, str, bool, result=bool)
    def adjustPhotoDates(
        self, rows: list, current_date: str, new_date: str, relative: bool
    ) -> bool:
        """A kijelölt képek EXIF `DateTimeOriginal` mezőjét módosítja.

        Relatív módban az első kép régi és új dátuma közti eltérést adja
        hozzá minden kijelölt kép saját idejéhez. Abszolút módban minden kép
        ugyanazt az időt kapja. A képek a lemezre íródnak, a `.picasa.ini`
        nem változik.
        """
        photos = self._rows_to_photos(rows)
        if not photos:
            return False
        try:
            displayed_current = datetime.fromisoformat(current_date.strip())
            target = datetime.fromisoformat(new_date.strip())
            delta = target - displayed_current
            updates = [
                (
                    photo,
                    _photo_datetime(photo) + delta if relative else target,
                )
                for photo in photos
            ]
        except (TypeError, ValueError, OverflowError):
            return False

        self._ensure_photo_ops_wired()
        last_folder_photo = {
            photo.folder_path: index for index, (photo, _value) in enumerate(updates)
        }
        jobs = []
        for index, (photo, value) in enumerate(updates):
            def write_file(photo=photo, value=value, index=index):
                _adjust_photo_file_date(Path(photo.folder_path) / photo.name, value)
                if last_folder_photo[photo.folder_path] == index:
                    with open_index(self._db_path) as conn:
                        sync_tree(
                            conn,
                            photo.folder_path,
                            incremental=False,
                            enabled_filetypes=self._filetype_scan_snapshot,
                        )
                return {"taken_at_override": None}

            jobs.append((photo.id, write_file))
        # A teljes újraszkennelés az EXIF-ből olvassa vissza a dátumot, a
        # végső lekérdezés pedig újraszámolja az aktív dátum szerinti sorrendet.
        self._run_photo_writes(jobs, after=self._refresh_view)
        return True
