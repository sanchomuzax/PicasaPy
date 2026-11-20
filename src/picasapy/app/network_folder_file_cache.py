"""Hálózati mappák projektfájl-neveinek mappánkénti, aszinkron cache-e."""

from __future__ import annotations

import os
import threading
import time
from pathlib import Path

from PySide6.QtCore import QMetaObject, Qt

import picasapy.halozati_ut as _network_paths

_LOCK = threading.Lock()
_CACHE_TTL_S = 15.0


def network_folder_file_names(owner, image_path: str | Path):
    """`(hálózati, nevek)`; cache missnél a lemezműveletet worker indítja."""
    path = Path(str(image_path or ""))
    if not image_path or _network_paths.fajlrendszer_gyoker(path) is None:
        return False, None
    folder = str(path.parent)
    now = time.monotonic()
    with _LOCK:
        cache = getattr(owner, "_network_folder_file_cache", None)
        if cache is None:
            cache = owner._network_folder_file_cache = {}
            owner._network_folder_file_pending = set()
            owner._network_folder_file_results = {}
        cached = cache.get(folder)
        if cached is not None and now < cached[0]:
            return True, cached[1]
        pending = owner._network_folder_file_pending
        if folder not in pending:
            pending.add(folder)

            def worker() -> None:
                failed = False
                try:
                    with os.scandir(folder) as entries:
                        names = frozenset(
                            entry.name.casefold()
                            for entry in entries
                            if entry.is_file()
                        )
                except OSError:
                    names = frozenset()
                    failed = True
                expires = time.monotonic() + (2.0 if failed else _CACHE_TTL_S)
                with _LOCK:
                    owner._network_folder_file_results[folder] = (expires, names)
                QMetaObject.invokeMethod(
                    owner,
                    "_emit_network_properties_changed",
                    Qt.ConnectionType.QueuedConnection,
                )

            owner._start_background(
                worker, name="picasapy-network-folder-files", busy=False
            )
        return True, None


def apply_network_folder_file_cache(owner) -> bool:
    """A worker-eredményeket a GUI-szálon átveszi; igaz, ha volt változás."""
    with _LOCK:
        results = getattr(owner, "_network_folder_file_results", None)
        if not results:
            return False
        owner._network_folder_file_cache.update(results)
        owner._network_folder_file_pending.difference_update(results)
        owner._network_folder_file_results = {}
    return True
