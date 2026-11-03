"""A frissítési csere előtt a telepítési mappát fogó folyamatok kezelése (#6458).

A tulajdonos céges gépén (2026-11-03) a csere háromszor `[WinError 32]`-vel
állt vissza: a program egyik fájlját egy másik folyamat fogta. Két forrás
lehetséges: a program saját, még élő folyamata (másik ablak, videó-bélyegkép
dolgozó), vagy egy rövid ideig olvasó víruskereső / indexelő. Az elsőt a segéd
megvárja, majd leállítja; a másodikra újrapróbálkozik.
"""

from __future__ import annotations

import os
import sys
import time
from collections.abc import Callable
from pathlib import Path

#: modulszintű fogantyúk (#1375): a teszt ezeket cseréli, nem a globális `os`/`time`-ot
_rename = os.rename
_alszik = time.sleep
_ora = time.monotonic

#: Windows: ERROR_ACCESS_DENIED (5) és ERROR_SHARING_VIOLATION (32).
_FOGLALT_WINERROR = frozenset({5, 32})
ATNEVEZESI_HATARIDO_MP = 60.0
FOLYAMAT_HATARIDO_MP = 20.0


def foglalt_hiba(hiba: BaseException) -> bool:
    """Igaz, ha a hiba azt jelenti: a fájlt egy másik folyamat fogja."""
    if getattr(hiba, "winerror", None) in _FOGLALT_WINERROR:
        return True
    return isinstance(hiba, PermissionError)


def atnevez_ujraprobalva(
    forras: Path,
    cel: Path,
    *,
    hatarido: float = ATNEVEZESI_HATARIDO_MP,
    rename: Callable[[Path, Path], None] | None = None,
    alszik: Callable[[float], None] | None = None,
    ora: Callable[[], float] | None = None,
) -> None:
    """Átnevez; foglalt fájlnál növekvő szünetekkel újrapróbál a határidőig."""
    rename = rename or _rename
    alszik = alszik or _alszik
    ora = ora or _ora
    kezdet = ora()
    szunet = 0.25
    while True:
        try:
            rename(forras, cel)
            return
        except OSError as hiba:
            if not foglalt_hiba(hiba) or ora() - kezdet >= hatarido:
                raise
        alszik(szunet)
        szunet = min(szunet * 2, 5.0)


def varj_vagy_allitsd_le(
    install_dir: Path,
    *,
    sajat_pid: int | None = None,
    hatarido: float = FOLYAMAT_HATARIDO_MP,
    lista: Callable[[Path, int], list[int]] | None = None,
    leallit: Callable[[int], None] | None = None,
    alszik: Callable[[float], None] | None = None,
    ora: Callable[[], float] | None = None,
) -> int:
    """Megvárja a telepítési mappából futó folyamatokat; a határidő után leállítja őket.

    A visszatérési érték a leállított folyamatok száma."""
    sajat_pid = os.getpid() if sajat_pid is None else sajat_pid
    lista = lista or telepitesi_folyamatok
    leallit = leallit or _leallit
    alszik = alszik or _alszik
    ora = ora or _ora
    kezdet = ora()
    while lista(install_dir, sajat_pid):
        if ora() - kezdet >= hatarido:
            break
        alszik(0.5)
    maradek = lista(install_dir, sajat_pid)
    for pid in maradek:
        try:
            leallit(pid)
        except OSError:
            pass
    return len(maradek)


def _platform() -> str:
    """Platformfogantyú (#1217): a teszt ezt írja át, nem a `sys.platform`-ot."""
    return sys.platform


def telepitesi_folyamatok(install_dir: Path, sajat_pid: int) -> list[int]:
    """A telepítési mappán belüli programfájlból futó folyamatok (csak Windowson)."""
    if _platform() != "win32":
        return []
    try:
        gyoker = os.path.normcase(str(Path(install_dir).resolve())) + os.sep
    except OSError:
        return []
    talalt = []
    for pid in _windows_pidek():
        if pid in (0, sajat_pid):
            continue
        kep = _windows_kep_utvonal(pid)
        if kep and os.path.normcase(kep).startswith(gyoker):
            talalt.append(pid)
    return talalt


def _windows_pidek() -> list[int]:  # pragma: no cover - csak Windowson fut
    import ctypes
    from ctypes import wintypes

    meret = 4096
    while True:
        tomb = (wintypes.DWORD * meret)()
        kapott = wintypes.DWORD()
        if not ctypes.windll.psapi.EnumProcesses(
            ctypes.byref(tomb), ctypes.sizeof(tomb), ctypes.byref(kapott)
        ):
            return []
        db = kapott.value // ctypes.sizeof(wintypes.DWORD)
        if db < meret:
            return list(tomb[:db])
        meret *= 2


def _windows_kep_utvonal(pid: int) -> str:  # pragma: no cover - csak Windowson fut
    import ctypes
    from ctypes import wintypes

    process_query_limited_information = 0x1000
    kernel32 = ctypes.windll.kernel32
    fogantyu = kernel32.OpenProcess(process_query_limited_information, False, pid)
    if not fogantyu:
        return ""
    try:
        puffer = ctypes.create_unicode_buffer(32768)
        hossz = wintypes.DWORD(len(puffer))
        if not kernel32.QueryFullProcessImageNameW(fogantyu, 0, puffer, ctypes.byref(hossz)):
            return ""
        return puffer.value
    finally:
        kernel32.CloseHandle(fogantyu)


def _leallit(pid: int) -> None:  # pragma: no cover - csak Windowson fut
    import ctypes

    process_terminate = 0x0001
    synchronize = 0x00100000
    kernel32 = ctypes.windll.kernel32
    fogantyu = kernel32.OpenProcess(process_terminate | synchronize, False, pid)
    if not fogantyu:
        return
    try:
        kernel32.TerminateProcess(fogantyu, 1)
        kernel32.WaitForSingleObject(fogantyu, 5000)
    finally:
        kernel32.CloseHandle(fogantyu)
