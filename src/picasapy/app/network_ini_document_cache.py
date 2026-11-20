"""Hálózati mappák Picasa INI-dokumentumainak mappánkénti cache-e."""

from __future__ import annotations

import threading
import time
from pathlib import Path

from PySide6.QtCore import QMetaObject, Qt

import picasapy.halozati_ut as _network_paths
from picasapy.ini import load_or_empty
from picasapy.scanner import PICASA_INI_NAME

_LOCK = threading.Lock()
_CACHE_TTL_S = 3.0


def network_ini_document(owner, folder: str | Path):
    """`(hálózati, dokumentum)`; cache missnél a betöltés háttérszálra kerül."""
    folder = str(folder)
    if _network_paths.fajlrendszer_gyoker(folder) is None:
        return False, None

    now = time.monotonic()
    with _LOCK:
        cache = getattr(owner, "_network_ini_document_cache", None)
        if cache is None:
            cache = owner._network_ini_document_cache = {}
            owner._network_ini_document_pending = set()
            owner._network_ini_document_results = {}

        cached = cache.get(folder)
        if cached is not None:
            expires, document = cached
            if now < expires:
                return True, document

        pending = owner._network_ini_document_pending
        if folder not in pending:
            start_background = getattr(owner, "_start_background", None)
            if start_background is None:
                return True, cached[1] if cached is not None else None
            pending.add(folder)

            def worker() -> None:
                try:
                    document = load_or_empty(Path(folder) / PICASA_INI_NAME)
                except (OSError, UnicodeError):
                    document = None
                with _LOCK:
                    owner._network_ini_document_results[folder] = document
                QMetaObject.invokeMethod(
                    owner,
                    "_emit_network_properties_changed",
                    Qt.ConnectionType.QueuedConnection,
                )

            try:
                start_background(
                    worker, name="picasapy-network-ini-document", busy=False
                )
            except Exception:
                pending.discard(folder)
                raise
        return True, cached[1] if cached is not None else None


def apply_network_ini_document_results(owner) -> bool:
    """A workereredményeket átveszi; igaz, ha érkezett új dokumentum."""
    with _LOCK:
        results = getattr(owner, "_network_ini_document_results", None)
        if not results:
            return False
        expires = time.monotonic() + _CACHE_TTL_S
        owner._network_ini_document_cache.update(
            (folder, (expires, document)) for folder, document in results.items()
        )
        owner._network_ini_document_pending.difference_update(results)
        owner._network_ini_document_results = {}
    return True
