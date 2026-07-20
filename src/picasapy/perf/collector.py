"""Alacsony rezsijű teljesítmény-mintavételező (#211).

A `PerfCollector` a saját (nem-Qt) háttér-daemon szálán fut, ~1 Hz-en —
SOHA a GUI-szálon. Célzottan `psutil` NÉLKÜL: Linuxon a `/proc/<pid>`
alól olvassuk a processz CPU-idejét és RSS-ét; nem-Linux platformon a
beépített `resource` modulra esik vissza (durvább, de függőségmentes
becslés — a peak-RSS-t adja a pillanatnyi helyett).

A mintavétel logikája (`_tick`) tisztán tesztelhető: a CPU/RSS-forrás, az
óra és az „aktivitás" (thumbnail/sync-állapot) mind befecskendezhető
függvények — a tesztek valódi szál/processz nélkül, mock-olt forrásokkal
futtatják."""

from __future__ import annotations

import os
import sys
import threading
import time
from dataclasses import dataclass
from typing import Callable

try:
    import resource  # csak POSIX-on érhető el
except ImportError:  # pragma: no cover - Windows
    resource = None  # type: ignore[assignment]


@dataclass(frozen=True)
class PerfSample:
    """Egy mintavétel eredménye — a mezőnevek a JSONL-formátum (logwriter)
    kulcsaival egyeznek."""

    ts: float
    cpu_percent: float
    rss_bytes: int
    thumb_active: int
    thumb_queue: int
    sync_folder: str
    sync_done: int
    sync_total: int
    gui_stall_ms: float


def _read_proc_stat_status(pid: int) -> tuple[float, int]:
    """Linux: (kumulatív cpu-idő mp-ben, RSS byte-ban) a /proc alól.

    A cpu-idő KUMULATÍV a processz indulása óta (utime+stime jiffies-ben,
    HZ-cel osztva) — a hívó két mintavétel közti különbségéből számol
    %-os terhelést, a rendelkezésre álló magok számával normálva."""
    with open(f"/proc/{pid}/stat", encoding="utf-8") as handle:
        fields = handle.read().split()
    utime = int(fields[13])
    stime = int(fields[14])
    hz = os.sysconf("SC_CLK_TCK")
    cpu_time = (utime + stime) / hz
    rss_bytes = 0
    with open(f"/proc/{pid}/status", encoding="utf-8") as handle:
        for line in handle:
            if line.startswith("VmRSS:"):
                rss_bytes = int(line.split()[1]) * 1024
                break
    return cpu_time, rss_bytes


def _windows_cpu_rss() -> tuple[float, int]:
    """Windows: pillanatnyi RSS a psapi `GetProcessMemoryInfo`-ból
    (WorkingSetSize), kumulatív CPU-idő az `os.times()`-ból — mindkettő
    a standard könyvtárból, `psutil` nélkül."""
    import ctypes
    import ctypes.wintypes

    class _PMC(ctypes.Structure):  # PROCESS_MEMORY_COUNTERS
        _fields_ = [
            ("cb", ctypes.wintypes.DWORD),
            ("PageFaultCount", ctypes.wintypes.DWORD),
            ("PeakWorkingSetSize", ctypes.c_size_t),
            ("WorkingSetSize", ctypes.c_size_t),
            ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
            ("QuotaPagedPoolUsage", ctypes.c_size_t),
            ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
            ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
            ("PagefileUsage", ctypes.c_size_t),
            ("PeakPagefileUsage", ctypes.c_size_t),
        ]

    pmc = _PMC()
    pmc.cb = ctypes.sizeof(_PMC)
    handle = ctypes.windll.kernel32.GetCurrentProcess()
    ok = ctypes.windll.psapi.GetProcessMemoryInfo(
        handle, ctypes.byref(pmc), pmc.cb
    )
    rss_bytes = int(pmc.WorkingSetSize) if ok else 0
    times = os.times()  # Windowson: (user, system, 0, 0, elapsed)
    return times.user + times.system, rss_bytes


def _fallback_cpu_rss() -> tuple[float, int]:
    """Nem-Linux (vagy /proc nélküli) tartalék. Windowson psapi/os.times
    (pillanatnyi RSS); POSIX-on a `resource` modul — ott a RSS a
    CSÚCS-RSS (`ru_maxrss`), nem a pillanatnyi érték; jobb híján ez a
    legolcsóbb, függőségmentes becslés."""
    if sys.platform == "win32":
        try:
            return _windows_cpu_rss()
        except (OSError, AttributeError):
            return 0.0, 0
    if resource is None:
        return 0.0, 0
    usage = resource.getrusage(resource.RUSAGE_SELF)
    cpu_time = usage.ru_utime + usage.ru_stime
    # macOS-en byte-ban, Linuxon KB-ban adja vissza a kernel
    rss_bytes = usage.ru_maxrss * (1 if sys.platform == "darwin" else 1024)
    return cpu_time, rss_bytes


def read_proc_cpu_rss(pid: int | None = None) -> tuple[float, int]:
    """(kumulatív cpu-idő mp, RSS byte) — Linuxon /proc-ból, máshol
    fokozatos visszaesés a `resource` modulra."""
    pid = pid if pid is not None else os.getpid()
    try:
        return _read_proc_stat_status(pid)
    except (OSError, IndexError, ValueError):
        return _fallback_cpu_rss()


# A mintavétel alapütemezése (~1 Hz, ld. #211 elvárt viselkedés).
DEFAULT_INTERVAL_S = 1.0


class PerfCollector:
    """Saját háttérszálon futó mintavételező.

    `start()`-ig/`stop()`-ig semmi nem fut — a felhasználó által ki/be
    kapcsolható monitor (#211) ezen a két hívásán keresztül vezérelhető."""

    def __init__(
        self,
        interval: float = DEFAULT_INTERVAL_S,
        cpu_rss_fn: Callable[[], tuple[float, int]] = read_proc_cpu_rss,
        clock: Callable[[], float] = time.monotonic,
        wall_clock: Callable[[], float] = time.time,
        activity_fn: Callable[[], dict] | None = None,
        on_sample: Callable[[PerfSample], None] | None = None,
        cpu_count: int | None = None,
    ):
        self._interval = interval
        self._cpu_rss_fn = cpu_rss_fn
        self._clock = clock
        self._wall_clock = wall_clock
        self._activity_fn = activity_fn
        self._on_sample = on_sample
        self._cpu_count = max(cpu_count or os.cpu_count() or 1, 1)
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None

    @property
    def is_running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def start(self) -> None:
        """A háttérszál indítása — idempotens (kétszeri hívás no-op)."""
        if self._thread is not None:
            return
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._run, name="picasapy-perf", daemon=True
        )
        self._thread.start()

    def stop(self, timeout: float = 2.0) -> None:
        """A háttérszál leállítása — a hívás visszatéréséig bevárja
        (max `timeout` mp), hogy `stop()` után garantáltan ne fusson
        több mintavétel."""
        if self._thread is None:
            return
        self._stop_event.set()
        self._thread.join(timeout)
        self._thread = None

    def _run(self) -> None:  # pragma: no cover - a logika a _tick-ben tesztelt
        cpu_time, _ = self._cpu_rss_fn()
        wall = self._clock()
        while not self._stop_event.wait(self._interval):
            sample, cpu_time, wall = self._tick(cpu_time, wall)
            if self._on_sample is not None:
                self._on_sample(sample)

    def _tick(
        self, prev_cpu_time: float, prev_wall: float
    ) -> tuple[PerfSample, float, float]:
        """Egy mintavételi lépés tiszta logikája — a `_run` hívja
        ismételten, a tesztek pedig közvetlenül, mock-olt forrásokkal."""
        cpu_time, rss_bytes = self._cpu_rss_fn()
        wall = self._clock()
        elapsed = max(wall - prev_wall, 1e-6)
        cpu_delta = max(cpu_time - prev_cpu_time, 0.0)
        cpu_percent = 100.0 * cpu_delta / elapsed / self._cpu_count
        activity = self._activity_fn() if self._activity_fn is not None else {}
        sample = PerfSample(
            ts=self._wall_clock(),
            cpu_percent=cpu_percent,
            rss_bytes=rss_bytes,
            thumb_active=int(activity.get("thumb_active", 0)),
            thumb_queue=int(activity.get("thumb_queue", 0)),
            sync_folder=str(activity.get("sync_folder", "")),
            sync_done=int(activity.get("sync_done", 0)),
            sync_total=int(activity.get("sync_total", 0)),
            gui_stall_ms=float(activity.get("gui_stall_ms", 0.0)),
        )
        return sample, cpu_time, wall
