"""Külön folyamatú Windows-csomagcsere és visszaállítás (#6340).

A segéd a főfolyamat kilépésére vár. A kicsomagolás külön, szomszédos
mappába történik; a telepített mappa csak teljes staging után cserélődik.
"""

from __future__ import annotations

import argparse
import errno
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
import zipfile

_kill = os.kill


def _safe_member_path(root: Path, member: str) -> Path:
    path = Path(member)
    if path.is_absolute() or ".." in path.parts:
        raise ValueError(f"A frissítési zip érvénytelen útvonalat tartalmaz: {member}")
    destination = (root / path).resolve()
    if root.resolve() not in destination.parents and destination != root.resolve():
        raise ValueError(f"A frissítési zip útvonala kilép a staging mappából: {member}")
    return destination


def extract_update_archive(archive: Path, stage: Path) -> Path:
    """A zipet biztonságosan kicsomagolja, és a program gyökerét adja vissza."""
    if stage.exists():
        shutil.rmtree(stage)
    stage.mkdir(parents=True)
    try:
        with zipfile.ZipFile(archive) as source:
            members = source.infolist()
            for member in members:
                destination = _safe_member_path(stage, member.filename)
                if member.is_dir():
                    destination.mkdir(parents=True, exist_ok=True)
                    continue
                destination.parent.mkdir(parents=True, exist_ok=True)
                with source.open(member) as reader, destination.open("wb") as writer:
                    shutil.copyfileobj(reader, writer)
    except Exception:
        shutil.rmtree(stage, ignore_errors=True)
        raise

    nested = stage / "PicasaPy"
    if nested.is_dir():
        return nested
    if not (stage / "PicasaPy.exe").is_file():
        shutil.rmtree(stage, ignore_errors=True)
        raise ValueError("A frissítési zip nem tartalmaz PicasaPy.exe fájlt")
    return stage


def swap_update_directory(
    staged_dir: Path,
    install_dir: Path,
    *,
    launch,
) -> bool:
    """Mappát cserél, indítást ellenőriz, és hibánál visszaállít.

    A `launch` visszatérési értéke azt jelzi, hogy az új program elérte-e az
    indulási egészségjelzőt. Tesztekben a folyamatindítás helyettesíthető.
    """
    staged_dir = Path(staged_dir).resolve()
    install_dir = Path(install_dir).resolve()
    backup_dir = install_dir.with_name(f"{install_dir.name}.previous")
    failed_dir = install_dir.with_name(f"{install_dir.name}.failed")
    if not staged_dir.is_dir():
        raise ValueError("A staging mappa nem létezik")
    if failed_dir.exists():
        shutil.rmtree(failed_dir)
    if backup_dir.exists():
        shutil.rmtree(backup_dir)
    had_previous = install_dir.exists()
    if had_previous:
        install_dir.rename(backup_dir)
    try:
        staged_dir.rename(install_dir)
        if not launch():
            if install_dir.exists():
                install_dir.rename(failed_dir)
            if had_previous and backup_dir.exists():
                backup_dir.rename(install_dir)
            if failed_dir.exists():
                shutil.rmtree(failed_dir, ignore_errors=True)
            return False
    except Exception:
        if install_dir.exists():
            install_dir.rename(failed_dir)
        if had_previous and backup_dir.exists():
            backup_dir.rename(install_dir)
        if failed_dir.exists():
            shutil.rmtree(failed_dir, ignore_errors=True)
        raise
    return True


def wait_for_process(pid: int, *, poll_interval: float = 0.2) -> None:
    """Megvárja a főfolyamat kilépését; a helper külön folyamatban fut."""
    if pid <= 0 or pid == os.getpid():
        raise ValueError("Érvénytelen főfolyamat-azonosító")
    if _platform() == "win32":
        _wait_for_windows_process(pid)
        return
    while True:
        try:
            _kill(pid, 0)
        except ProcessLookupError:
            return
        except PermissionError:
            # Az azonos felhasználó segédjének ez szokatlan, de nem szabad
            # élő folyamatot kilépettnek tekinteni egy hozzáférési hibából.
            time.sleep(poll_interval)
            continue
        except OSError as error:
            if error.errno == errno.ESRCH:
                return
            raise
        time.sleep(poll_interval)


def _platform() -> str:
    """Kis platformfogantyú a folyamatvárás teszteléséhez."""
    return sys.platform


def _wait_for_windows_process(pid: int) -> None:
    """Win32 folyamathandle-en vár; az ``os.kill(pid, 0)`` nem hordozható."""
    import ctypes
    from ctypes import wintypes

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    process_synchronize = 0x00100000
    infinite = 0xFFFFFFFF
    wait_object_0 = 0
    wait_failed = 0xFFFFFFFF

    open_process = kernel32.OpenProcess
    open_process.argtypes = (wintypes.DWORD, wintypes.BOOL, wintypes.DWORD)
    open_process.restype = wintypes.HANDLE
    handle = open_process(process_synchronize, False, pid)
    if not handle:
        error_code = ctypes.get_last_error()
        # Windows ERROR_INVALID_PARAMETER: a PID már nem létezik.
        if error_code == 87:
            return
        raise ctypes.WinError(error_code)

    try:
        wait_for_single_object = kernel32.WaitForSingleObject
        wait_for_single_object.argtypes = (wintypes.HANDLE, wintypes.DWORD)
        wait_for_single_object.restype = wintypes.DWORD
        result = wait_for_single_object(handle, infinite)
        if result == wait_failed:
            raise ctypes.WinError(ctypes.get_last_error())
        if result != wait_object_0:
            raise OSError(f"Váratlan Win32 folyamateredmény: {result}")
    finally:
        close_handle = kernel32.CloseHandle
        close_handle.argtypes = (wintypes.HANDLE,)
        close_handle.restype = wintypes.BOOL
        close_handle(handle)


def _onellenorzes(executable: Path, *, timeout: float = 180.0) -> bool:
    """Az új változat felépíti-e a felületét — ablak nélkül (#6340).

    A program saját `--onellenorzes` kapcsolója a teljes indulási utat
    végigjárja (Qt-bővítmények, QML-fa, fordítás), és eseményciklus nélkül
    kilép; ugyanezt futtatja a CI a csomagon. Ablakot nem nyit, tehát a
    rendszergazdai jogú segéd is futtathatja anélkül, hogy a felhasználó
    elé rendszergazdaként futó program kerülne."""
    env = os.environ.copy()
    env["QT_QPA_PLATFORM"] = "offscreen"
    env["QT_QUICK_BACKEND"] = "software"
    try:
        eredmeny = subprocess.run(
            [str(executable), "--onellenorzes"],
            env=env,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=timeout,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    return eredmeny.returncode == 0


def _rendszergazda() -> bool:
    """Rendszergazdai (emelt) jogokkal fut-e a segéd — csak Windowson igaz."""
    if _platform() != "win32":
        return False
    try:
        import ctypes

        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except (AttributeError, OSError):
        return False


#: a folyamatindítás fogantyúja — a teszt ezt cseréli (#1375)
_popen = subprocess.Popen


def inditsd_a_felhasznalonak(executable: Path) -> None:
    """A frissített program indítása a felhasználó NORMÁL jogaival (#6340).

    Ha a segéd rendszergazdaként fut (UAC), a közvetlen indítás az új
    PicasaPy-t is rendszergazdaként futtatná: a létrehozott fájlok a
    rendszergazdáé lennének, és az Intézőből húzás sem működne. A Windows
    héja (`explorer.exe`) a bejelentkezett felhasználó jogaival indít."""
    if _rendszergazda():
        _popen(["explorer.exe", str(executable)], close_fds=True)
    else:
        _popen([str(executable)], close_fds=True)


def install_after_exit(pid: int, archive: Path, install_dir: Path, executable: str) -> bool:
    """Vár, kicsomagol, cserél, ellenőriz, szükség esetén visszaáll, majd indít."""
    wait_for_process(pid)
    install_dir = Path(install_dir).resolve()
    work_dir = install_dir.parent
    stage_root = Path(tempfile.mkdtemp(prefix="PicasaPy-update-", dir=work_dir))
    sikerult = False
    try:
        staged = extract_update_archive(Path(archive), stage_root / "new")
        sikerult = swap_update_directory(
            staged,
            install_dir,
            launch=lambda: _onellenorzes(install_dir / executable),
        )
    finally:
        shutil.rmtree(stage_root, ignore_errors=True)
        # sikernél az új, minden más esetben a megmaradt régi változat
        # indul — mindkettő a felhasználó jogaival; a program tehát a
        # frissítés kudarca után sem marad bezárva
        try:
            inditsd_a_felhasznalonak(install_dir / executable)
        except OSError:
            pass
    return sikerult


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="PicasaPy frissítés telepítő segéd")
    parser.add_argument("--pid", type=int, required=True)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--install-dir", type=Path, required=True)
    parser.add_argument("--executable", required=True)
    args = parser.parse_args(argv)
    try:
        install_after_exit(args.pid, args.archive, args.install_dir, args.executable)
    except Exception as error:  # noqa: BLE001 - az elkülönített helper hibája konzolra kerül
        print(f"A PicasaPy-frissítés nem sikerült: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
