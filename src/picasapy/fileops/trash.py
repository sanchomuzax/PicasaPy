"""Fájl törlése a lomtárba — freedesktop.org Trash specifikáció (#15, #457).

A törölt fájl nem vész el visszavonhatatlanul: a desktopkörnyezet lomtár-
nézete (Nautilus, Dolphin stb.) ugyanígy olvassa vissza. A "home trash"
(`$XDG_DATA_HOME/Trash`) mellett a más fájlrendszeren lévő mappák (pl. NAS-
mountok) mount-specifikus lomtárát (`$topdir/.Trash/$uid` majd
`$topdir/.Trash-$uid`) is megkeressük — így a törlés a hálózati meghajtón
marad, nem másolódik át a home lomtárba. Ha egyik sem elérhető (a mountpoint
nem írható), a hívónak explicit döntést kell hoznia: `delete_to_trash`
`TrashUnavailableError`-t dob, NEM töröl csendben véglegesen."""

from __future__ import annotations

import os
import shutil
import sys
import stat as stat_module
import urllib.parse
from datetime import datetime
from pathlib import Path


class TrashUnavailableError(OSError):
    """A megadott fájlhoz nincs elérhető lomtár — sem a home trash (mert más
    fájlrendszeren van), sem a mount-specifikus `$topdir/.Trash[-uid]` (mert
    a topdir nem írható). Ilyenkor a hívónak explicit kell döntenie a
    végleges törlésről (`delete_permanently`) — ez a kivétel soha nem vezet
    csendes, visszavonhatatlan törléshez."""


def _platform() -> str:
    """A futó platform — külön függvény, hogy a teszt helyettesíthesse."""
    return sys.platform


def _windows_lomtarba(path: Path) -> None:
    """A fájl a Windows LOMTÁRÁBA (`SHFileOperationW`, `FOF_ALLOWUNDO`).

    ⚠️ #1182: a modul többi része a **freedesktop.org** Trash-specifikációt
    valósítja meg (`$XDG_DATA_HOME/Trash`, `files/` + `info/` páros) — az
    LINUXOS szabvány. Windowson emiatt a fájl egy rejtett mappába került,
    amiről a Lomtár nem tud: a felhasználó számára ELTŰNT, és nem tudta
    visszaállítani. A tulajdonos pontosan ezt jelentette.

    Az EREDETI Picasa ugyanezt az API-t hívja: a `Picasa3.exe` importálja a
    `SHELL32.DLL` → `SHFileOperationW` függvényt
    (`referencia/binary-index/imports.csv:11282`, `0x009b1d50`).

    A `FOF_ALLOWUNDO` az, ami a törlést Lomtárba helyezéssé teszi; enélkül
    a shell VÉGLEGESEN törölne.

    ⚠️ A forrás-útvonalat KETTŐS nullával kell lezárni: az API
    nullával elválasztott listát vár, és a lista végét egy második nulla
    jelzi. Enélkül a hívás a memóriában olvasna tovább.
    """
    import ctypes
    from ctypes import wintypes

    FO_DELETE = 3
    FOF_ALLOWUNDO = 0x0040
    FOF_NOCONFIRMATION = 0x0010
    FOF_SILENT = 0x0004

    class SHFILEOPSTRUCTW(ctypes.Structure):
        _fields_ = [
            ("hwnd", wintypes.HWND),
            ("wFunc", wintypes.UINT),
            ("pFrom", wintypes.LPCWSTR),
            ("pTo", wintypes.LPCWSTR),
            ("fFlags", ctypes.c_uint16),
            ("fAnyOperationsAborted", wintypes.BOOL),
            ("hNameMappings", ctypes.c_void_p),
            ("lpszProgressTitle", wintypes.LPCWSTR),
        ]

    muvelet = SHFILEOPSTRUCTW(
        hwnd=None,
        wFunc=FO_DELETE,
        pFrom=str(Path(path).resolve()) + "\0\0",
        pTo=None,
        fFlags=FOF_ALLOWUNDO | FOF_NOCONFIRMATION | FOF_SILENT,
        fAnyOperationsAborted=False,
        hNameMappings=None,
        lpszProgressTitle=None,
    )
    eredmeny = ctypes.windll.shell32.SHFileOperationW(ctypes.byref(muvelet))
    if eredmeny != 0 or muvelet.fAnyOperationsAborted:
        raise OSError(
            f"A Lomtárba helyezés nem sikerült (SHFileOperationW={eredmeny}): {path}"
        )


def delete_to_trash(path: Path, *, trash_dir: Path | None = None) -> Path:
    """A `path` fájl áthelyezése a lomtárba.

    Args:
        path: A törlendő fájl elérési útja.
        trash_dir: Teszteléshez felülírható lomtár-gyökér; alapból a
            `find_trash_dir` által kiválasztott (home vagy mount-
            specifikus) lomtár.

    Returns:
        A fájl új elérési útja a lomtár `files/` alkönyvtárában.

    Raises:
        FileNotFoundError: Ha `path` nem létezik.
        TrashUnavailableError: Ha sem a home, sem a mount-specifikus lomtár
            nem érhető el (pl. írásvédett hálózati megosztás) — ilyenkor a
            hívónak `delete_permanently`-vel kell döntenie, nem hallgatólagos
            véglegesítéssel.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"A fájl nem létezik: {path}")

    # ⚠️ #1182: Windowson a RENDSZER Lomtára a cél, nem a freedesktop-mappa.
    # A `trash_dir` felülírás (teszt) továbbra is erősebb — azzal a
    # freedesktop-ág mérhető marad minden platformon.
    if trash_dir is None and _platform() == "win32":
        _windows_lomtarba(path)
        return path

    trash = trash_dir if trash_dir is not None else find_trash_dir(path)
    if trash is None:
        raise TrashUnavailableError(
            f"Nincs elérhető lomtár ehhez a fájlhoz: {path}"
        )
    files_dir = trash / "files"
    info_dir = trash / "info"
    files_dir.mkdir(parents=True, exist_ok=True)
    info_dir.mkdir(parents=True, exist_ok=True)

    original = str(path.resolve())
    content = (
        "[Trash Info]\n"
        f"Path={urllib.parse.quote(original)}\n"
        f"DeletionDate={datetime.now().strftime('%Y-%m-%dT%H:%M:%S')}\n"
    ).encode("utf-8")

    # freedesktop-spec: az info-fájlnak a MOVE ELŐTT kell léteznie,
    # kizárólagos létrehozással (O_EXCL) — így félbeszakadt/tele lemezes
    # move esetén sosem marad "árva" fájl visszaállítási info nélkül.
    trashed_path, info_path = _create_trashinfo_exclusively(
        path.name, files_dir, info_dir, content
    )

    try:
        shutil.move(str(path), str(trashed_path))
    except Exception:
        info_path.unlink(missing_ok=True)
        raise
    return trashed_path


def delete_permanently(path: Path) -> None:
    """A `path` VÉGLEGES, visszavonhatatlan törlése (nincs lomtár-út).

    Csak akkor hívandó, ha a felhasználó a `trash_available(path)` False
    eredménye után is explicit módon a végleges törlést választotta — ld.
    `FileOpsDialogs.qml` `deleteConfirmDialog`, ami ilyenkor külön,
    hangsúlyos szöveggel kérdez.

    Args:
        path: A törlendő fájl vagy mappa elérési útja.

    Raises:
        FileNotFoundError: Ha `path` nem létezik.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"A fájl nem létezik: {path}")
    if path.is_dir() and not path.is_symlink():
        shutil.rmtree(path)
    else:
        path.unlink()


def find_trash_dir(path: Path, *, trash_dir: Path | None = None) -> Path | None:
    """A `path`-hoz tartozó lomtár-gyökér a freedesktop.org Trash-spec
    szerint, vagy `None`, ha nincs elérhető lomtár.

    Sorrend:
      1. `trash_dir` felülírás (teszteléshez) — ha meg van adva, ez jön
         vissza változtatás nélkül.
      2. "Home trash" (`$XDG_DATA_HOME/Trash`), ha `path` ugyanazon a
         fájlrendszeren van, mint a home trash.
      3. Mount-specifikus megosztott lomtár: `$topdir/.Trash/$uid`, DE csak
         ha a `$topdir/.Trash` létezik, NEM symlink, ÉS sticky bit van
         rajta (ezt a spec írja elő, hogy más felhasználó ne tudja
         kicserélni/eltávolítani mások lomtár-mappáját).
      4. Mount-specifikus, felhasználónkénti lomtár: `$topdir/.Trash-$uid`
         — ezt akár létre is hozhatjuk, ha a `$topdir` írható.
      5. Ha egyik feltétel sem teljesül (a topdir nem írható) → `None`.

    A `$topdir` a `path`-ot tartalmazó mountpoint: felfelé megyünk a
    szülőkönyvtárakon, amíg az `os.stat().st_dev` meg nem változik.
    """
    if trash_dir is not None:
        return trash_dir

    path = Path(path)
    file_dev = _device_of(path)
    home_trash = _trash_home()
    home_dev = _device_of(home_trash)
    if file_dev is not None and file_dev == home_dev:
        return home_trash

    topdir = _mount_point(path)
    if not hasattr(os, "getuid"):
        # A mount-specifikus `$topdir/.Trash[-uid]` a freedesktop.org
        # (POSIX) szabvány fogalma — Windowson nem létezik, és a Lomtár
        # feltérképezése egészen más (shell-API) úton menne. Amíg az nincs
        # megírva, ott a #457 ELŐTTI viselkedés marad érvényben: mindig a
        # home trash. Így Windowson nem jelenik meg a NAS-figyelmeztetés,
        # de nem is romlik el semmi, ami eddig működött.
        return home_trash
    uid = os.getuid()

    shared = topdir / ".Trash"
    if _is_valid_shared_trash(shared):
        return shared / str(uid)

    per_user = topdir / f".Trash-{uid}"
    if per_user.is_dir():
        return per_user
    if os.access(topdir, os.W_OK):
        return per_user

    return None


def trash_available(path: Path, *, trash_dir: Path | None = None) -> bool:
    """True, ha `path`-hoz van elérhető lomtár (home vagy mount-
    specifikus) — a `deleteConfirmDialog` ez alapján dönt a szöveg és a
    hívandó slot (`deletePhoto` vs `deletePhotoPermanently`) között."""
    # ⚠️ #1182: Windowson MINDIG van Lomtár — a rendszer sajátja. A
    # `find_trash_dir` freedesktop-logikája (`$XDG_DATA_HOME`,
    # `.Trash-$uid`) ott értelmetlen, és ha nem talál semmit, a program a
    # VÉGLEGES törlés ágára megy (#457): a felhasználó azt a szöveget
    # kapná, hogy nincs visszaút — holott a Lomtár működik.
    if trash_dir is None and _platform() == "win32":
        return True
    return find_trash_dir(path, trash_dir=trash_dir) is not None


def _is_valid_shared_trash(shared: Path) -> bool:
    """A `$topdir/.Trash` a spec szerint csak akkor használható, ha
    létezik, NEM symlink, ÉS sticky bit (`S_ISVTX`) van rajta."""
    try:
        if shared.is_symlink() or not shared.is_dir():
            return False
        mode = shared.stat().st_mode
    except OSError:
        return False
    return bool(mode & stat_module.S_ISVTX)


def _trash_home() -> Path:
    xdg_data_home = os.environ.get("XDG_DATA_HOME")
    base = Path(xdg_data_home) if xdg_data_home else Path.home() / ".local" / "share"
    return base / "Trash"


def _nearest_existing(path: Path) -> Path:
    """A `path` legközelebbi létező őse — magára `path`-ra, ha az már
    létezik. Törlés előtti ellenőrzéshez kell, amikor `path` maga még nem
    (vagy már nem) létezik a fájlrendszeren."""
    current = path if path.is_absolute() else Path.cwd() / path
    while not current.exists():
        parent = current.parent
        if parent == current:
            break
        current = parent
    return current


def _device_of(path: Path) -> int | None:
    try:
        return _nearest_existing(path).stat().st_dev
    except OSError:
        return None


def _mount_point(path: Path) -> Path:
    """A `path`-ot tartalmazó mountpoint: a legfelső ős, amelyik még
    ugyanazon a fájlrendszeren (`st_dev`) van, mint `path` maga."""
    current = _nearest_existing(path)
    try:
        dev = current.stat().st_dev
    except OSError:
        return current
    while True:
        parent = current.parent
        if parent == current:
            return current
        try:
            parent_dev = parent.stat().st_dev
        except OSError:
            return current
        if parent_dev != dev:
            return current
        current = parent


def _candidate_name(name: str, suffix: int) -> str:
    """Ütközésmentes célnév-jelölt (Picasa/Nautilus-minta: `_1`, `_2`, …
    utótag a kiterjesztés elé)."""
    if suffix == 0:
        return name
    stem, dot, ext = name.partition(".")
    return f"{stem}_{suffix}{dot}{ext}" if dot else f"{name}_{suffix}"


def _create_trashinfo_exclusively(
    name: str, files_dir: Path, info_dir: Path, content: bytes
) -> tuple[Path, Path]:
    """Az info-fájl kizárólagos (O_EXCL) létrehozása egy még szabad
    célnévvel. Ha a `files/`-ben már foglalt a név (korábbi, be nem
    fejezett törlés maradványa), a jelölt is kimarad — így a `files/` és
    az `info/` pár mindig összetartozik."""
    suffix = 0
    while True:
        candidate = _candidate_name(name, suffix)
        trashed_path = files_dir / candidate
        info_path = info_dir / f"{candidate}.trashinfo"
        if trashed_path.exists():
            suffix += 1
            continue
        try:
            fd = os.open(info_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
        except FileExistsError:
            suffix += 1
            continue
        try:
            os.write(fd, content)
        finally:
            os.close(fd)
        return trashed_path, info_path
