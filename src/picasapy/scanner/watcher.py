"""Élő mappa-figyelés watchdog/inotify-jal.

A benchmark (docs/benchmarks/rpi5-sqlite-inotify.md) szerint az inotify
gond nélkül skálázódik a felhasználói könyvtárra; NAS-mounton (SMB/NFS)
viszont nem érkezik esemény távoli változásról — arra a hívó oldali
periodikus rescan a fallback.

A figyelő debounce-ol: a gyors esemény-sorozatokat (pl. fájlmásolás)
egyetlen jelzésbe gyűjti, és csak a releváns változásokra szól
(médiafájlok és .picasa.ini; a backup/temp fájlok és rejtett mappák nem).
"""

from __future__ import annotations

import threading
from pathlib import Path, PurePath

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from .filetypes import media_kind_of
from .walker import PICASA_INI_NAME


def _is_relevant(path_str: str) -> bool:
    path = PurePath(path_str)
    if any(part.startswith(".") for part in path.parts[1:-1]):
        return False  # rejtett mappában (pl. .picasaoriginals) történt
    name = path.name
    if name == PICASA_INI_NAME:
        return True
    if name.startswith("."):
        return False  # .picasa.ini.bak, rejtett/temp fájlok
    return media_kind_of(name) is not None


class _Handler(FileSystemEventHandler):
    def __init__(self, watcher: "LibraryWatcher"):
        self._watcher = watcher

    def on_any_event(self, event) -> None:
        if event.is_directory:
            return
        for path_str in (event.src_path, getattr(event, "dest_path", "")):
            if path_str and _is_relevant(path_str):
                self._watcher._mark_dirty(str(PurePath(path_str).parent))


class LibraryWatcher:
    """Figyelt gyökerek alatti változások debounce-olt jelzése.

    on_folders_changed(folders: set[str]) a debounce-ablak lejártakor,
    a watchdog megfigyelő szálából hívódik — a hívó felelőssége a
    szál-átvitel (Qt-nál: queued signal).
    """

    def __init__(
        self,
        roots: tuple[str, ...],
        on_folders_changed,
        debounce_seconds: float = 1.0,
    ):
        self._roots = roots
        self._callback = on_folders_changed
        self._debounce = debounce_seconds
        self._observer: Observer | None = None
        self._lock = threading.Lock()
        self._dirty: set[str] = set()
        self._timer: threading.Timer | None = None
        self._running = False

    def start(self) -> None:
        observer = Observer()
        handler = _Handler(self)
        scheduled = 0
        for root in self._roots:
            if Path(root).is_dir():
                observer.schedule(handler, root, recursive=True)
                scheduled += 1
        if scheduled:
            observer.start()
            self._observer = observer
        self._running = True

    def stop(self) -> None:
        self._running = False
        with self._lock:
            if self._timer is not None:
                self._timer.cancel()
                self._timer = None
            self._dirty.clear()
        if self._observer is not None:
            self._observer.stop()
            self._observer.join(timeout=5)
            self._observer = None

    def _mark_dirty(self, folder: str) -> None:
        with self._lock:
            if not self._running:
                return
            self._dirty.add(folder)
            if self._timer is not None:
                self._timer.cancel()
            self._timer = threading.Timer(self._debounce, self._flush)
            self._timer.daemon = True
            self._timer.start()

    def _flush(self) -> None:
        with self._lock:
            if not self._running or not self._dirty:
                return
            folders, self._dirty = self._dirty, set()
            self._timer = None
        self._callback(folders)
