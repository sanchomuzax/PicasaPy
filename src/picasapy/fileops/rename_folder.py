"""Fizikai mappa átnevezése a teljes tartalmával (#4482)."""

from __future__ import annotations

import os
import re
import sys
import time
import uuid
from pathlib import Path

from .move_folder import is_system_path

# A fájlrendszer-művelet fogantyúja: a tesztek csak ezt cserélik.
_rename = os.rename
# Az újrapróbálás várakozásának és óráinak fogantyúi (#7153): a teszt ezeket
# cseréli, valódi várakozás nélkül, a globális `time` érintése nélkül.
_sleep = time.sleep
_monotonic = time.monotonic


def _platform() -> str:
    """A futó platform, külön függvény, hogy a teszt helyettesíthesse (#1217)."""
    return sys.platform


_WINDOWS_DEVICE_NAME = re.compile(
    r"^(?:CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(?:\..*)?$", re.IGNORECASE
)
_PICASA_FORBIDDEN = frozenset('<>:"/\\|?*')
_PICASA_RESERVED_NAMES = frozenset({"aux", "con", "nul", "prn"})


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
    # #7108: az ismert felhasználói mappák tiltása az ÁTHELYEZÉSRE vonatkozik,
    # az átnevezés védelme a mai rendszerutak és a home maradt
    if is_system_path(source, known_folders=False):
        raise FolderRenameError("Rendszermappa nem nevezhető át.")

    name = sanitize_folder_rename_name(new_name)
    if not name:
        raise FolderRenameError("A mappanév nem lehet üres.")
    if name == source.name:
        return source
    _validate_windows_name(name)

    target = source.with_name(name)
    case_only = name != source.name and name.casefold() == source.name.casefold()
    if os.path.lexists(target) and not case_only:
        raise FolderRenameError("Ilyen nevű mappa már létezik.")
    if case_only:
        return _rename_folder_case_only(source, target)
    try:
        _rename_with_access_retry(source, target)
    except OSError as error:
        raise FolderRenameError(
            f"A mappa átnevezése nem sikerült: {error}"
        ) from error
    return target


#: A Windows ERROR_ACCESS_DENIED hibakódja (a `PermissionError.winerror`-ja).
_WINERROR_ACCESS_DENIED = 5
#: Az eredeti `0x00994400`: 500 ezredmásodpercenként, legfeljebb 5 másodpercig.
_RETRY_INTERVAL_SECONDS = 0.5
_RETRY_WINDOW_SECONDS = 5.0


def _is_access_denied(error: OSError) -> bool:
    return (
        isinstance(error, PermissionError)
        and getattr(error, "winerror", None) == _WINERROR_ACCESS_DENIED
    )


def _rename_with_access_retry(source: Path, target: Path) -> None:
    """Egy átnevezés; Windowson hozzáférési hibánál időkorlátig újrapróbál (#7153).

    Az eredeti `0x00994400` a `MoveFileExW` 5-ös hibakódjánál, ha a forrás
    létezik, 500 ezredmásodpercenként újrapróbálja, legfeljebb 5 másodpercig.
    Az első hiba után a ciklus bármely hibára folytatódik az időkorlátig, az
    időkorlát után az utolsó hiba megy tovább a hívónak (ő adja a felhasználói
    üzenetet). Más platformon és más első hibánál egyetlen próba van.

    A várakozás a hívó szálán fut, ugyanúgy, mint az eredetiben: a hívó
    (`renameFolder`) szinkron QML-slot, tehát a felületi szál legfeljebb
    ugyanannyi ideig vár, mint az eredetinél.
    """
    try:
        _rename(str(source), str(target))
        return
    except OSError as error:
        if (
            _platform() != "win32"
            or not _is_access_denied(error)
            or not source.exists()
        ):
            raise
        last_error = error

    deadline = _monotonic() + _RETRY_WINDOW_SECONDS
    while _monotonic() < deadline:
        _sleep(_RETRY_INTERVAL_SECONDS)
        try:
            _rename(str(source), str(target))
            return
        except OSError as error:
            last_error = error
    raise last_error


def sanitize_folder_rename_name(name: str) -> str:
    """A meglévő mappa Picasa-tulajdonságablakának névtisztítása."""
    characters = []
    for character in str(name):
        if character in _PICASA_FORBIDDEN:
            continue
        if ord(character) < 32 and not character.isspace():
            continue
        characters.append(" " if character.isspace() else character)
    cleaned = "".join(characters).strip(" .")
    if cleaned.casefold() in _PICASA_RESERVED_NAMES:
        cleaned += "_"
    return cleaned


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
