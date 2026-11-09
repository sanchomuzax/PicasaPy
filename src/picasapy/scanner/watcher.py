"""Élő mappa-figyelés watchdog/inotify-jal.

A benchmark (docs/benchmarks/rpi5-sqlite-inotify.md) szerint az inotify
gond nélkül skálázódik a felhasználói könyvtárra; NAS-mounton (SMB/NFS)
viszont nem érkezik esemény távoli változásról — arra a hívó oldali
periodikus rescan a fallback.

A figyelő debounce-ol: a gyors esemény-sorozatokat (pl. fájlmásolás)
egyetlen jelzésbe gyűjti. A fájlesemények közül a médiafájlok és a
`.picasa.ini` relevánsak; a látható mappák létrehozása, törlése, áthelyezése
és módosítása szintén jelzést ad. A backup/temp fájlok és rejtett mappák
fájleseményeit kihagyja.
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

from picasapy.halozati_ut import halozati_gyoker

from .filetypes import media_kind_of
from .walker import PICASA_INI_NAME

#: A debounce időzítő osztálya; modulszintű fogantyú, hogy a teszt ezt
#: cserélje, ne a globális `threading.Timer`-t (#1375).
_Timer = threading.Timer
_CHANGE_EVENT_TYPES = {"created", "deleted", "moved", "modified", "closed"}


@dataclass(frozen=True)
class DirectoryChange:
    """Egy könyvtár létrehozása vagy törlése, külön szinkronmóddal (#5177).

    A létrehozás rekurzív szinkront kér az adott könyvtárra; a törlés csak
    indexből törlést kér, lemezbejárás nélkül. A `refresh` kérés a teljes
    részfát inkrementális kihagyás nélkül egyezteti. Átnevezés két esemény.
    """

    path: str
    action: Literal["created", "deleted", "refresh"]


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
        if event.event_type not in _CHANGE_EVENT_TYPES:
            return
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
            elif event.event_type in {"modified", "closed"}:
                path_str = _directory_change_path(
                    event.src_path, self._watcher._roots
                )
                if path_str is not None:
                    self._watcher._mark_dirty(
                        DirectoryChange(path_str, "refresh")
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

#: #1457, #6696: ennyit várunk egy háttérszálra a leállításkor. Bőkezű, hogy
#: a szokásos leállás biztosan bevárja, de véges, hogy egy beragadt (például
#: hálózati meghajtón álló) szál ne akassza meg a program bezárását.
_JOIN_TIMEOUT_S = 30


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
        self._start_generation = 0
        self._startup_thread: threading.Thread | None = None

    def start(self) -> None:
        current_thread = threading.current_thread()
        with self._lock:
            if self._running:
                return
            self._running = True
            self._start_generation += 1
            generation = self._start_generation
            if current_thread is not threading.main_thread():
                self._startup_thread = current_thread

        self._start_observer(generation)

    def _start_background(self) -> threading.Thread | None:
        """A watchdog rekurzív felállítása saját háttérszálon (#6696)."""
        with self._lock:
            if self._running:
                return self._startup_thread
            self._running = True
            self._start_generation += 1
            generation = self._start_generation
            thread = threading.Thread(
                target=self._start_observer_background,
                args=(generation,),
                name="picasapy-inotify-start",
                daemon=True,
            )
            self._startup_thread = thread
            try:
                thread.start()
            except BaseException:
                self._running = False
                self._start_generation += 1
                self._startup_thread = None
                raise
            return thread

    def _start_observer_background(self, generation: int) -> None:
        try:
            self._start_observer(generation)
        except Exception:
            _log.exception("a mappafigyelő indítása nem sikerült")

    def _start_observer(self, generation: int) -> None:
        observer = None
        handler = _Handler(self)
        scheduled = 0
        try:
            observer = Observer()
            for root in self._roots:
                with self._lock:
                    if not self._running or generation != self._start_generation:
                        return
                # UNC-megosztáson az inotify nem látja a távoli módosítást,
                # a hívó oldali időzített rescan kezeli (#6696).
                if halozati_gyoker(root) is not None:
                    continue
                if Path(root).is_dir():
                    observer.schedule(handler, root, recursive=True)
                    scheduled += 1
            with self._lock:
                if not self._running or generation != self._start_generation:
                    return
                if scheduled:
                    # A watchdog itt hozza létre a rekurzív inotify-figyelőket;
                    # ezt a hívó (a vezérlőnél háttérszál) nem blokkolja.
                    observer.start()
                    self._observer = observer
        except Exception:
            with self._lock:
                if generation == self._start_generation:
                    self._running = False
                    if observer is not None and self._observer is observer:
                        self._observer = None
            raise

    def stop(self) -> None:
        with self._lock:
            self._running = False
            self._start_generation += 1
            startup_thread = self._startup_thread
            timers = tuple(self._timers)
            for timer in timers:
                timer.cancel()
            self._timer = None
            self._dirty.clear()
            self._first_dirty_at = None
        # A felállító szál rekurzív ütemezés közben nem tarthatja a zárat.
        # Előbb bevárjuk: a generációszám miatt így már nem indíthat később
        # Observer-szálat vagy callbacket egy újratöltés / QObject-bontás után.
        if (
            startup_thread is not None
            and startup_thread is not threading.current_thread()
        ):
            startup_thread.join(timeout=_JOIN_TIMEOUT_S)
        with self._lock:
            if (
                self._startup_thread is startup_thread
                and startup_thread is not threading.current_thread()
            ):
                self._startup_thread = None
            observer = self._observer
        if observer is not None:
            observer.stop()
            observer.join(timeout=_JOIN_TIMEOUT_S)
            # #1457: a referenciát CSAK akkor engedjük el, ha a szál
            # tényleg leállt. Korábban minden esetben eldobtuk — ha a join
            # időtúllépéssel tért vissza, a szál tovább futott egy olyan
            # kezelővel, ami a lebontás alatt álló figyelőre (és rajta át a
            # hívó vezérlőre) mutat. A CI jel nélküli összeomlásai
            # kivétel nélkül a valódi figyelőt indító tesztfájlokban
            # jelentek meg. A bőkezű join a szokásos leállást bevárja; ha a
            # szál mégis tovább fut, a referencia megmarad (lent).
            if not self._szal_el(observer):
                with self._lock:
                    if self._observer is observer:
                        self._observer = None
            else:
                _log.warning(
                    "a mappa-figyelő szála %s s alatt nem állt le, a referenciát megtartjuk",
                    _JOIN_TIMEOUT_S,
                )
        # A késleltető Timer külön szál, nem a watchdog Observeré. A cancel()
        # a már elindult callbacket nem állítja meg, ezért minden időzítőszálat
        # bevárunk, mielőtt a hívó elengedné a callbackben használt vezérlőt
        # (#6087). Önmagát nem várja be, ha a callback állítja le a figyelőt.
        current_thread = threading.current_thread()
        for timer in timers:
            if timer is not current_thread:
                timer.join(timeout=_JOIN_TIMEOUT_S)
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
            startup_stopped = (
                self._startup_thread is None
                or not self._startup_thread.is_alive()
            )
        return observer_stopped and timers_stopped and startup_stopped

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
            timer = _Timer(wait, self._flush)
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
