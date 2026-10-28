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

import logging
import sys
import threading
import time
from dataclasses import dataclass
from pathlib import Path, PurePath
from typing import Literal

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from .filetypes import media_kind_of
from .walker import PICASA_INI_NAME


@dataclass(frozen=True)
class DirectoryChange:
    """Egy könyvtár létrehozása vagy törlése, külön szinkronmóddal (#5177).

    A létrehozás rekurzív szinkront kér az adott könyvtárra; a törlés csak
    indexből törlést kér, lemezbejárás nélkül. Átnevezés két ilyen esemény.
    """

    path: str
    action: Literal["created", "deleted"]


def _relative_parts(path: PurePath, roots: tuple[str, ...]) -> tuple[str, ...]:
    """A `path` a hozzá tartozó figyelt gyökérhez képesti komponensei.

    A rejtett-mappa szűrésnek a gyökérhez KÉPEST relatív útra kell
    vonatkoznia, nem az abszolút út minden komponensére — különben egy
    rejtett könyvtár alatti gyökérnél (pl. `/home/user/.photos/...`)
    minden esemény némán eldobódna."""
    for root in roots:
        root_path = PurePath(root)
        try:
            return path.relative_to(root_path).parts
        except ValueError:
            continue
    return path.parts  # nem várt eset: nincs egyező gyökér


def _is_relevant(path_str: str, roots: tuple[str, ...]) -> bool:
    path = PurePath(path_str)
    relative_parts = _relative_parts(path, roots)
    if any(part.startswith(".") for part in relative_parts[:-1]):
        return False  # rejtett mappában (pl. .picasaoriginals) történt
    name = path.name
    if name == PICASA_INI_NAME:
        return True
    if name.startswith("."):
        return False  # .picasa.ini.bak, rejtett/temp fájlok
    return media_kind_of(name) is not None


def _directory_change_path(path_str: str, roots: tuple[str, ...]) -> str | None:
    """Kanonikus eseményút, ha az a látható részfán belül van.

    Az összevetés Path-alapú, nem szöveges előtaggal: ez a Windows
    elválasztóit és útvonal-komponens határait is helyesen kezeli.
    """
    path = Path(path_str)
    for root in roots:
        root_path = Path(root)
        try:
            relative_parts = path.relative_to(root_path).parts
        except ValueError:
            continue
        if not relative_parts or any(part.startswith(".") for part in relative_parts):
            return None
        return str(path)
    return None


def _platform() -> str:
    """A platform-fogantyú (#1217): a teszt ezt rögzíti, nem a globális `sys`-t."""
    return sys.platform


class _Handler(FileSystemEventHandler):
    def __init__(self, watcher: "LibraryWatcher"):
        self._watcher = watcher

    def on_any_event(self, event) -> None:
        if event.is_directory:
            if event.event_type in {"created", "deleted"}:
                path_str = _directory_change_path(
                    event.src_path, self._watcher._roots
                )
                if path_str is not None:
                    self._watcher._mark_dirty(
                        DirectoryChange(path_str, event.event_type)
                    )
            elif event.event_type == "moved":
                for path_str, action in (
                    (event.src_path, "deleted"),
                    (getattr(event, "dest_path", ""), "created"),
                ):
                    if not path_str:
                        continue
                    changed_path = _directory_change_path(
                        path_str, self._watcher._roots
                    )
                    if changed_path is not None:
                        self._watcher._mark_dirty(
                            DirectoryChange(changed_path, action)
                        )
            return
        # Windowson a watchdog a törölt mappát is fájlként jelzi (#5177): a
        # `ReadDirectoryChangesW` törlésnél nem mondja meg, mappa volt-e, a törölt
        # út pedig már nem kérdezhető le. Linuxon az inotify megbízhatóan jelzi.
        if (
            event.event_type == "deleted"
            and _platform().startswith("win")
            and not _is_relevant(event.src_path, self._watcher._roots)
        ):
            changed_path = _directory_change_path(event.src_path, self._watcher._roots)
            if changed_path is not None:
                self._watcher._mark_dirty(DirectoryChange(changed_path, "deleted"))
            return
        for path_str in (event.src_path, getattr(event, "dest_path", "")):
            if path_str and _is_relevant(path_str, self._watcher._roots):
                self._watcher._mark_dirty(str(PurePath(path_str).parent))


_log = logging.getLogger(__name__)

#: #1457: ennyit várunk a megfigyelő szálára a leállításkor.
_JOIN_TIMEOUT_S = 5


class LibraryWatcher:
    """Figyelt gyökerek alatti változások debounce-olt jelzése.

    on_folders_changed(folders: set[str | DirectoryChange]) a debounce-ablak
    lejártakor, a watchdog megfigyelő szálából hívódik — a hívó felelőssége
    a szál-átvitel (Qt-nál: queued signal).
    """

    def __init__(
        self,
        roots: tuple[str, ...],
        on_folders_changed,
        debounce_seconds: float = 1.0,
        max_debounce_seconds: float = 30.0,
    ):
        self._roots = roots
        self._callback = on_folders_changed
        self._debounce = debounce_seconds
        self._max_debounce = max_debounce_seconds
        self._observer: Observer | None = None
        self._lock = threading.Lock()
        self._dirty: set[str | DirectoryChange] = set()
        self._timer: threading.Timer | None = None
        self._timers: set[threading.Timer] = set()
        self._first_dirty_at: float | None = None
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
        with self._lock:
            self._running = False
            timers = tuple(self._timers)
            for timer in timers:
                timer.cancel()
            self._timer = None
            self._dirty.clear()
            self._first_dirty_at = None
        if self._observer is not None:
            self._observer.stop()
            self._observer.join(timeout=_JOIN_TIMEOUT_S)
            # #1457: a referenciát CSAK akkor engedjük el, ha a szál
            # tényleg leállt. Korábban minden esetben eldobtuk — ha a join
            # időtúllépéssel tért vissza, a szál tovább futott egy olyan
            # kezelővel, ami a lebontás alatt álló figyelőre (és rajta át a
            # hívó vezérlőre) mutat. A CI jel nélküli összeomlásai
            # kivétel nélkül a valódi figyelőt indító tesztfájlokban
            # jelentek meg; hogy ez az OK is, azt a következő összeomlás
            # veremképe dönti el (a futtató most már kiírja).
            if self._szal_el(self._observer):
                _log.warning(
                    "a mappa-figyelő szála %s s alatt nem állt le — a "
                    "referenciát megtartjuk, hogy ne egy felszabadított "
                    "objektumra dolgozzon tovább",
                    _JOIN_TIMEOUT_S,
                )
            else:
                self._observer = None
        # A késleltető Timer külön szál, nem a watchdog Observeré. A cancel()
        # a már elindult callbacket nem állítja meg, ezért minden időzítőszálat
        # bevárunk, mielőtt a hívó elengedné a callbackben használt vezérlőt
        # (#6087). Önmagát nem várja be, ha a callback állítja le a figyelőt.
        current_thread = threading.current_thread()
        for timer in timers:
            if timer is not current_thread:
                timer.join()
        with self._lock:
            self._timers.difference_update(
                timer for timer in timers if not timer.is_alive()
            )

    @staticmethod
    def _szal_el(megfigyelo) -> bool:
        """Fut-e még a megfigyelő szála (#1457).

        A watchdog `Observer`-e `threading.Thread` leszármazott, tehát
        ismeri az `is_alive`-ot; ha egy próba mégis olyan objektumot ad,
        ami nem, az NEM dönthet le semmit — ilyenkor leállítottnak
        tekintjük."""
        elet = getattr(megfigyelo, "is_alive", None)
        if elet is None:
            return False
        try:
            return bool(elet())
        except Exception:  # noqa: BLE001 — a leállítás nem bukhat el ezen
            return False

    def leallt(self) -> bool:
        """Leállt-e az Observer és az összes debounce-szál (#1457, #6087).

        `False`, ha bármelyik háttérszál még fut — a hívó (teszt-teardown,
        alkalmazás-kilépés) így nem engedi el a callbackben használt vezérlőt."""
        with self._lock:
            observer_stopped = (
                self._observer is None or not self._szal_el(self._observer)
            )
            timers_stopped = not any(timer.is_alive() for timer in self._timers)
        return observer_stopped and timers_stopped

    def _mark_dirty(self, folder: str | DirectoryChange) -> None:
        with self._lock:
            if not self._running:
                return
            now = time.monotonic()
            if not self._dirty:
                self._first_dirty_at = now
            self._dirty.add(folder)
            if self._timer is not None:
                self._timer.cancel()
            # A korábban cancel-elt Timer nem feltétlen jut el a _flush()-ig,
            # ezért a befejezett szálak referenciáját itt is takarítjuk.
            for timer in tuple(self._timers):
                if not timer.is_alive():
                    self._timers.discard(timer)
            # max. ablak: hosszú (folyamatos) másolás alatt a callback ne
            # halasztódjon a végtelenbe — a debounce-ot az első piszkos
            # jelzés óta eltelt idő korlátozza
            elapsed = now - self._first_dirty_at
            remaining = max(0.0, self._max_debounce - elapsed)
            wait = min(self._debounce, remaining)
            timer = threading.Timer(wait, self._flush)
            self._timer = timer
            self._timers.add(timer)
            self._timer.daemon = True
            timer.start()

    def _flush(self) -> None:
        timer = threading.current_thread()
        try:
            with self._lock:
                if not self._running or not self._dirty:
                    return
                folders, self._dirty = self._dirty, set()
                if self._timer is timer:
                    self._timer = None
                self._first_dirty_at = None
            self._callback(folders)
        finally:
            with self._lock:
                if self._timer is timer:
                    self._timer = None
                self._timers.discard(timer)
