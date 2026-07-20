"""JSONL diagnosztikai napló a teljesítmény-monitorhoz (#211).

## Formátum

Soronként EGY JSON-objektum (JSONL — "JSON Lines"). Az ELSŐ sor mindig
egy `"session"` fejléc, utána `"sample"` sorok következnek mintavételi
sorrendben. Példa:

    {"type": "session", "app_version": "v0.7.0 (81.3706d78)", "platform": "Linux-6.6-aarch64", "python_version": "3.12.4", "qt_version": "6.7.2", "started_at": "2026-07-20T21:10:00+00:00"}
    {"type": "sample", "ts": "2026-07-20T21:10:01+00:00", "cpu_percent": 12.3, "rss_bytes": 104857600, "thumb_active": 2, "thumb_queue": 0, "sync_folder": "2018", "sync_done": 120, "sync_total": 400, "gui_stall_ms": 3.2}

A fájl a `~/.cache/picasapy/perf/` alá kerül (XDG_CACHE_HOME-ot
tiszteletben tartva), névmintája `perf-<ÉÉÉÉHHNN-óópp>.jsonl`.

## Adatvédelem (#211 DoD)

A napló NEM tartalmaz fájlnevet vagy teljes elérési utat: a
`sync_folder` mező kizárólag a mappa NEVE (az utolsó útvonal-elem), nem
a teljes útvonal — a mappaszerkezet (NAS-útvonalak, felhasználónév a
home-útvonalban stb.) így nem szivárog a küldhető diagnosztikába."""

from __future__ import annotations

import json
import os
import platform as _platform
import time
from collections import deque
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

from .collector import PerfSample

# ~10 perc puffer 1 Hz-es mintavételnél — a memóriacsere elég nagy ablakot
# ad egy tipikus diagnosztikai mentéshez, mégsem nő korlátlanul.
_MAX_BUFFERED_SAMPLES = 600


def default_log_dir() -> Path:
    """`~/.cache/picasapy/perf/` (vagy `$XDG_CACHE_HOME/picasapy/perf/`)."""
    base = os.environ.get("XDG_CACHE_HOME", str(Path.home() / ".cache"))
    return Path(base) / "picasapy" / "perf"


def _iso(ts: float) -> str:
    return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()


def session_header(app_version: str, qt_version: str = "") -> dict:
    """A napló első sora: az futtatási környezet azonosítása (#211 DoD:
    „session-fejléccel" — verzió, platform, Python/Qt-verzió, időbélyeg)."""
    return {
        "type": "session",
        "app_version": app_version,
        "platform": _platform.platform(),
        "python_version": _platform.python_version(),
        "qt_version": qt_version,
        "started_at": _iso(time.time()),
    }


def sample_to_dict(sample: PerfSample) -> dict:
    """Egy `PerfSample` JSON-szótárrá alakítva — a `ts` ISO-8601 stringgé."""
    data = asdict(sample)
    data["ts"] = _iso(sample.ts)
    return {"type": "sample", **data}


class PerfLogWriter:
    """Mintákat gyűjt memóriában (korlátos FIFO-puffer), és kérésre egy
    session-fejléces JSONL-fájlba írja ki (`saveDiagnostics` a QML-nek —
    ld. `app/perf_controller.py`)."""

    def __init__(
        self,
        app_version: str,
        qt_version: str = "",
        max_samples: int = _MAX_BUFFERED_SAMPLES,
    ):
        self._app_version = app_version
        self._qt_version = qt_version
        self._buffer: deque[PerfSample] = deque(maxlen=max_samples)

    def record(self, sample: PerfSample) -> None:
        self._buffer.append(sample)

    def clear(self) -> None:
        """A puffer ürítése — pl. a monitor újra-bekapcsolásakor, hogy a
        mentés csak az aktuális futamot tartalmazza."""
        self._buffer.clear()

    @property
    def sample_count(self) -> int:
        return len(self._buffer)

    def save(self, directory: Path | None = None) -> Path:
        """A puffer session-fejléccel egy JSONL-fájlba írva; a fájl
        útvonalát adja vissza (a QML „Diagnosztika mentése" gombja ezt
        jeleníti meg)."""
        directory = directory or default_log_dir()
        directory.mkdir(parents=True, exist_ok=True)
        filename = f"perf-{datetime.now().strftime('%Y%m%d-%H%M%S')}.jsonl"
        path = directory / filename
        lines = [
            json.dumps(
                session_header(self._app_version, self._qt_version),
                ensure_ascii=False,
            )
        ]
        lines.extend(
            json.dumps(sample_to_dict(sample), ensure_ascii=False)
            for sample in self._buffer
        )
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return path
