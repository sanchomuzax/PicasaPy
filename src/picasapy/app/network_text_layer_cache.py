"""A hálózati mappák Text-rétegeinek mappánkénti, aszinkron cache-e."""

from __future__ import annotations

import threading
from pathlib import Path

from PySide6.QtCore import QMetaObject, Qt

import picasapy.halozati_ut as _network_paths
from picasapy.ini import load_or_empty
from picasapy.ini.text_overlay import parse_text
from picasapy.scanner import PICASA_INI_NAME

_LOCK = threading.Lock()


def has_network_text_layer(owner, photo):
    """`None` helyi mappánál; távoli mappánál azonnali cache-eredmény."""
    if photo.kind == "video":
        return False
    folder = str(photo.folder_path)
    if _network_paths.fajlrendszer_gyoker(folder) is None:
        return None
    cache = getattr(owner, "_network_text_document_cache", None)
    if cache is None:
        cache = owner._network_text_document_cache = {}
        owner._network_text_document_pending = set()
        owner._network_text_document_results = {}
    with _LOCK:
        if folder in cache:
            document = cache[folder]
        else:
            document = None
            pending = owner._network_text_document_pending
            if folder not in pending:
                pending.add(folder)

                def worker() -> None:
                    try:
                        result = load_or_empty(Path(folder) / PICASA_INI_NAME)
                    except (OSError, UnicodeError):
                        result = None
                    with _LOCK:
                        owner._network_text_document_results[folder] = result
                    QMetaObject.invokeMethod(
                        owner,
                        "_emit_network_properties_changed",
                        Qt.ConnectionType.QueuedConnection,
                    )

                owner._start_background(
                    worker, name="picasapy-network-text-layer", busy=False
                )
            return False
    if document is None:
        return False
    section = document.section(photo.name)
    raw = section.get("text") if section is not None else None
    if not raw:
        return False
    try:
        overlay = parse_text(raw)
    except ValueError:
        return False
    return bool(overlay and any(block.content for block in overlay.blocks))


def apply_network_text_layer_results(owner) -> None:
    with _LOCK:
        results = getattr(owner, "_network_text_document_results", None)
        if not results:
            return
        owner._network_text_document_cache.update(results)
        owner._network_text_document_pending.difference_update(results)
        owner._network_text_document_results = {}
