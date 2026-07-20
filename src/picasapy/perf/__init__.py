"""Kapcsolható teljesítmény-monitor (#211): alacsony rezsijű mintavételező
+ menthető JSONL diagnosztikai log.

KIKAPCSOLT állapotban (alapértelmezés) ebből a csomagból SEMMI nem fut —
sem háttérszál, sem hook — az importálás önmagában nulla-költségű."""

from __future__ import annotations

from .collector import PerfCollector, PerfSample, read_proc_cpu_rss
from .logwriter import PerfLogWriter, default_log_dir, sample_to_dict, session_header

__all__ = [
    "PerfCollector",
    "PerfSample",
    "read_proc_cpu_rss",
    "PerfLogWriter",
    "default_log_dir",
    "sample_to_dict",
    "session_header",
]
