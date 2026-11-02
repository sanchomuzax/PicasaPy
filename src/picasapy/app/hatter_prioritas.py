"""Alacsony prioritás beállítása az arckeresés háttérszálain."""

from __future__ import annotations

import ctypes
import os
import sys
import threading


#: Windowson nincs `os.PRIO_PROCESS`; a Linux-ág próbái ott is futnak (#6407).
_PRIO_PROCESS = getattr(os, "PRIO_PROCESS", 0)


def _platform() -> str:
    """A futó platform cserélhető fogantyúja (#1217)."""
    return sys.platform


def _linux_setpriority(which: int, who: int, priority: int) -> None:
    """Modulszintű standardfüggvény-fogantyú a próbákhoz (#1217)."""
    os.setpriority(which, who, priority)


def _native_thread_id() -> int:
    """A jelenlegi natív szálazonosító cserélhető lekérdezése."""
    return threading.get_native_id()


def _windows_kernel32():
    """A kernel32 betöltése a Windows-szálprioritás beállításához."""
    return ctypes.WinDLL("kernel32", use_last_error=True)


def _windows_thread_below_normal() -> None:
    """A jelenlegi Windows-szál prioritását a normál alá állítja."""
    kernel32 = _windows_kernel32()
    get_current_thread = kernel32.GetCurrentThread
    get_current_thread.restype = ctypes.c_void_p
    set_thread_priority = kernel32.SetThreadPriority
    set_thread_priority.argtypes = (ctypes.c_void_p, ctypes.c_int)
    set_thread_priority.restype = ctypes.c_int
    if not set_thread_priority(get_current_thread(), -1):
        raise OSError(ctypes.get_last_error(), "SetThreadPriority failed")


def kerjafonal_alacsony_prioritasa() -> None:
    """A jelenlegi szál alacsony prioritást kér; hiba esetén csendben továbblép."""
    try:
        platform = _platform()
        if platform.startswith("linux"):
            _linux_setpriority(_PRIO_PROCESS, _native_thread_id(), 10)
        elif platform.startswith("win"):
            _windows_thread_below_normal()
    except (AttributeError, OSError):
        # Néhány futtatókörnyezet nem engedi az ütemezési prioritás módosítását.
        pass


def arckeres_szal_elokeszitese() -> int:
    """Prioritás és egyszálú OpenCV a detektáló és lenyomat-worker számára.

    Az OpenCV szálszáma az egész folyamatra érvényes, ezért a korábbi értéket
    visszaadja: a keresés végén az `arckeres_szal_lezarasa()` visszaállítja,
    hogy a szerkesztő effektjei ne maradjanak egy szálon."""
    kerjafonal_alacsony_prioritasa()
    from picasapy.lazy_cv2 import cv2

    elozo = int(cv2.getNumThreads())
    cv2.setNumThreads(1)
    return elozo


def arckeres_szal_lezarasa(elozo: int | None) -> None:
    """A keresés előtti OpenCV-szálszám visszaállítása."""
    if elozo is None:
        return
    from picasapy.lazy_cv2 import cv2

    cv2.setNumThreads(elozo)
