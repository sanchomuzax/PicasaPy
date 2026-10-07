"""Fizikai mappa átnevezése a teljes tartalmával (#4482)."""

from __future__ import annotations

import os
import re
import uuid
from pathlib import Path

from .move_folder import is_system_path
from .new_folder import InvalidFolderNameError, validate_folder_name

# A fájlrendszer-művelet fogantyúja: a tesztek csak ezt cserélik.
_rename = os.rename

_WINDOWS_DEVICE_NAME = re.compile(
    r"^(?:CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(?:\..*)?$", re.IGNORECASE
)


class FolderRenameError(RuntimeError):
    """A mappát nem sikerült átnevezni — felületen megjeleníthető okkal."""


def rename_folder(folder: str | Path, new_name: str) -> Path:
    """A mappa átnevezése a szülőkönyvtárán belül.

    A könyvtár egészét nevezi át, ezért a képek, almappák és a
    `.picasa.ini` is vele marad. Létező célra nem ír felül.
    """
    source = Path(folder)
    if not source.is_dir():
        raise FolderRenameError(f"A mappa nem található: {source}")
    if is_system_path(source):
        raise FolderRenameError("Rendszermappa nem nevezhető át.")

    if new_name == source.name:
        return source
    try:
        name = validate_folder_name(new_name)
    except InvalidFolderNameError as error:
        raise FolderRenameError(str(error)) from error
    _validate_windows_name(name)

    target = source.with_name(name)
    case_only = name != source.name and name.casefold() == source.name.casefold()
    if os.path.lexists(target) and not case_only:
        raise FolderRenameError("Ilyen nevű mappa már létezik.")
    if case_only:
        return _rename_folder_case_only(source, target)
    try:
        _rename(str(source), str(target))
    except OSError as error:
        raise FolderRenameError(
            f"A mappa átnevezése nem sikerült: {error}"
        ) from error
    return target


def _rename_folder_case_only(source: Path, target: Path) -> Path:
    """Kis-/nagybetű-cserét két külön lemezes lépéssel végez (#4482).

    Windows és macOS alatt a fájlrendszer a forrást és a célt ugyanannak a
    névnek tekintheti. Az egyedi köztes név elkerüli ezt, hiba esetén pedig
    visszaállítjuk az eredeti nevet.
    """
    while True:
        temporary = source.with_name(
            f".picasapy-rename-{uuid.uuid4().hex}.tmp"
        )
        if not os.path.lexists(temporary):
            break

    try:
        _rename(str(source), str(temporary))
    except OSError as error:
        raise FolderRenameError(
            f"A mappa átnevezése nem sikerült: {error}"
        ) from error

    try:
        if os.path.lexists(target):
            raise FolderRenameError("Ilyen nevű mappa már létezik.")
        _rename(str(temporary), str(target))
    except (FolderRenameError, OSError) as error:
        try:
            if os.path.lexists(source):
                raise OSError("az eredeti név időközben foglalt lett")
            _rename(str(temporary), str(source))
        except OSError as rollback_error:
            raise FolderRenameError(
                "A mappa átnevezése nem sikerült, és az eredeti név "
                f"visszaállítása is hibázott: {rollback_error}. Részlet: {error}"
            ) from error
        if isinstance(error, FolderRenameError):
            raise error
        raise FolderRenameError(
            f"A mappa átnevezése nem sikerült: {error}"
        ) from error
    return target


def restore_folder_rename(folder: str | Path, original: str | Path) -> Path:
    """Egy félbemaradt magasabb szintű átnevezés fájlrendszeres visszaállítása.

    Itt a már létező eredeti név karaktereit nem validáljuk újra: egy régi
    könyvtár neve olyan lehet, amit az új névszabály már nem engedne be.
    """
    source = Path(folder)
    target = Path(original)
    if not source.is_dir():
        raise FolderRenameError(f"A visszaállítandó mappa nem található: {source}")
    if source.parent != target.parent:
        raise FolderRenameError("A mappa csak ugyanazon a szülőn belül állítható vissza.")
    if target.exists():
        raise FolderRenameError(
            f"Az eredeti mappanév időközben foglalt lett: {target.name}"
        )
    try:
        _rename(str(source), str(target))
    except OSError as error:
        raise FolderRenameError(
            f"A mappa eredeti nevét nem sikerült visszaállítani: {error}"
        ) from error
    return target


def _validate_windows_name(name: str) -> None:
    if name in (".", ".."):
        raise FolderRenameError("A mappanév nem lehet pont vagy két pont.")
    if name.endswith((".", " ")):
        raise FolderRenameError(
            "A mappanév nem végződhet ponttal vagy szóközzel."
        )
    if any(ord(char) < 32 for char in name):
        raise FolderRenameError(
            "A mappanév nem tartalmazhat vezérlőkaraktert."
        )
    if _WINDOWS_DEVICE_NAME.fullmatch(name):
        raise FolderRenameError(
            "Ez a név a Windows rendszerben fenntartott, ezért nem használható."
        )


__all__ = ["FolderRenameError", "rename_folder", "restore_folder_rename"]
