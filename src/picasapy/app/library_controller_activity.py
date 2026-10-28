"""A könyvtár-vezérlő activity felelősségei (#6137)."""

from __future__ import annotations

import importlib
import sys

from pathlib import Path
import threading
import time

from PySide6.QtCore import Slot
from picasapy.index import open_index
from picasapy.index.dedup_folders import merge_duplicate_folders
from picasapy.paths import normalize_path, path_key
from picasapy.scanner import LibraryWatcher

from .busy_registry import get_app_busy_registry


def _legacy():
    """A régi modulból olvassa az örökölt, tesztek által foltozható neveket."""
    return sys.modules.get(
        f"{__package__}.library_controller"
    ) or importlib.import_module(".library_controller", __package__)


class LibraryActivityMixin:
    @Slot()
    def cancelActivity(self) -> None:  # noqa: N802 — QML-slot-stílus
        """A futó, leállítható háttérmunkák megszakítása (#2966).

        A jelző gombja hívja, a megerősítő kérdés IGEN ága után. Minden
        bejelentkezett munkát leállít: a felhasználó a felületen egyetlen
        „dolgozik" jelzést lát, tehát egyetlen kattintásra számít."""
        get_app_busy_registry().request_cancel()

    @Slot(int)
    def _on_thumb_active(self, count: int) -> None:
        """A thumbnail-provider aktív kéréseinek száma (a provider szálából
        jelezve; a Qt a főszálra sorolja) — SZINT, nem esemény, ezért a
        közös regisztrátumba ÉL-alapon (0 -> pozitív / pozitív -> 0
        átmenetkor) jelentkezünk be/ki, nem minden hívásnál."""
        was_active = self._thumb_active > 0
        self._thumb_active = count
        is_active = count > 0
        if is_active and not was_active:
            get_app_busy_registry().begin()
        elif was_active and not is_active:
            get_app_busy_registry().end()

    # -- „Importálás" folyamat-panel (#209) ----------------------------------


























    @Slot()
    def dismissImportPanel(self) -> None:
        """Kézi bezárás — a panel a futó szkennelés végéig nem tér vissza
        (a következő szkennelés újra megjelenítheti)."""
        self._import_dismissed = True
        self.importChanged.emit()

    @Slot(str, int, int, int)
    def _on_sync_progress(self, folder, done, total, new_photos) -> None:
        """Sync-haladás a GUI-szálon (queued jelzés a workerből).

        #216 — késői jelzések védelme: eltávolított (már nem figyelt)
        gyökér alatti mappa haladása nem frissít semmit — se panelt, se
        rácsot. A worker queued jelzései az eltávolítás UTÁN is beeshetnek
        még; ezek itt csendben elnyelődnek.

        A panel automatikusan akkor jelenik meg, ha a szkennelés érdemi:
        új gyökér importja (forced), vagy új fotók kerültek elő — a csendes,
        mindent-kihagyó 5 perces rescan nem villogtatja. A rács fokozatos
        frissítése ritkított (max ~1,5 mp-enként), és a meglévő
        megőrzött-görgetésű újratöltési úton fut, nem kötegenkénti
        modell-resettel."""
        if self._root_for_folder(folder) is None:
            return  # #216: eltávolított gyökér késői jelzése — ignorálva
        self._import_folder = folder
        self._import_done = done
        self._import_total = total
        self._import_new = new_photos
        if not self._import_visible and (self._import_forced or new_photos > 0):
            self._import_visible = True
        self.importChanged.emit()
        now = time.monotonic()
        if (
            new_photos > self._import_new_at_reload
            and now - self._import_last_reload >= _legacy()._PROGRESS_RELOAD_MIN_S
        ):
            self._import_last_reload = now
            self._import_new_at_reload = new_photos
            # a már feldolgozott (commitolt) mappák fotói jelenjenek meg
            self._reload(preserve_scroll=True)

    @Slot()
    def _on_import_finished(self) -> None:
        """A sync vége (syncFinished): a panel eltűnik, az állapot nulláz —
        a záró teljes frissítést a meglévő _reload_after_sync út végzi."""
        self._import_folder = ""
        self._import_done = 0
        self._import_total = 0
        self._import_new = 0
        self._import_visible = False
        self._import_forced = False
        self._import_dismissed = False
        self._import_new_at_reload = 0
        self.importChanged.emit()

    def _make_progress_emitter(self, should_stop=None):
        """WORKER-SZÁLON futó progress-callback (ld. SyncProgressCallback):
        a jelzés-emisszió ritkított — új fotót hozó mappa és az utolsó mappa
        mindig átmegy, a gyors (kihagyott) mappák max ~4/s ütemben.

        #216: a visszatérési érték megszakítás-kérés a `sync_tree` felé —
        igaz, ha a `should_stop` hívható igazat ad (pl. a gyökér leállítási
        jelzője be van állítva). A ritkítástól függetlenül MINDEN híváskor
        kiértékelődik, így a leállás mappa-határon, másodpercen belül él."""
        state = {"last": 0.0, "new": -1}

        def progress(folder: str, done: int, total: int, new_photos: int) -> bool:
            now = time.monotonic()
            if (
                new_photos != state["new"]
                or done == total
                or now - state["last"] >= _PROGRESS_EMIT_MIN_S
            ):
                state["last"] = now
                state["new"] = new_photos
                self.syncProgress.emit(folder, done, total, new_photos)
            return should_stop() if should_stop is not None else False

        return progress

    # -- leállítási jelzők (#216) --------------------------------------------

    def _cancel_event(self, root: str) -> threading.Event:
        """A gyökér leállítási jelzője (lustán létrehozva — a mixinnek nincs
        __init__-je, a szótár első használatkor születik). Beállítja a
        `removeWatchedFolder`; a worker-oldali should_stop olvassa; az
        újra-hozzáadás (`addWatchedFolder`) törli."""
        try:
            events = self._sync_cancel_events
        except AttributeError:
            events = self._sync_cancel_events = {}
        if root not in events:
            events[root] = threading.Event()
        return events[root]

    def cancelScan(self) -> None:  # noqa: N802 — a QML-stílusú nevekhez igazítva
        """A futó indexelés/szinkron megszakítása (#2966).

        A jobb-felső sarki jelző gombja hívja (a közös nyilvántartáson át).
        A pásztázás-generáció léptetése a `_make_should_stop`-on keresztül
        MINDEN futó pásztázást leállít a következő mappahatáron — és
        SEMMILYEN tartós nyomot nem hagy: az ezután induló szinkron a friss
        generációt veszi fel, tehát rendesen lefut. (A gyökerenkénti
        leállítási jelző, `_cancel_event`, ehhez nem jó: az bent MARADNA, és
        a mappát a következő körben is kihagyná.)

        A már beindexelt mappák munkája nem vész el: a `sync_folder`
        mappánként commitol."""
        self._ensure_folder_manager_scan_state()
        self._folder_scan_generation += 1

    def _make_should_stop(self, root: str):
        """Worker-oldali leállás-predikátum egy gyökérhez: igaz, ha a
        leállítási jelző be van állítva VAGY a gyökér már nem figyelt —
        a kettős ellenőrzés a jelző-törlés versenyhelyzetét is lefedi."""
        event = self._cancel_event(root)
        self._ensure_folder_manager_scan_state()
        scan_generation = self._folder_scan_generation
        return lambda: (
            event.is_set()
            or root not in self._roots
            or scan_generation != self._folder_scan_generation
        )

    # -- életciklus ----------------------------------------------------------

    def start(self) -> None:
        """Indulás: modellek betöltése, háttér-szinkron, élő figyelés.

        Az inotify-figyelő az azonnali frissülést adja; NAS-mounton
        (SMB/NFS) nem érkezik esemény, ezért 5 percenként periodikus
        rescan fut fallbackként (a Picasa is folyamatosan pásztázott)."""
        from PySide6.QtCore import QTimer

        self._dedupe_roots()
        with open_index(self._db_path) as conn:
            report = merge_duplicate_folders(conn)
        if report.merged:
            _legacy().logger.info(
                "#507: induláskor %d mappa-duplikátum-csoport összevonva",
                len(report.merged),
            )
        if report.skipped:
            _legacy().logger.warning(
                "#507: %d mappa-duplikátum-csoport ÖSSZEVONÁSA KIHAGYVA "
                "(ütköző szerkesztés — a duplikátum megmarad, adatvesztés "
                "helyett): %s",
                len(report.skipped),
                ", ".join(key for key, _reason in report.skipped),
            )
        # #1601: a hasáb két ini-alapú gyűjteménye (Emberek, Projektek) itt
        # SZÁNDÉKOSAN kimarad. Mérve ez volt az induláskori szinkron munka
        # 94%-a — mindkettő a `has_ini=1` mappák `.picasa.ini`-jét olvassa
        # végig, tehát a könyvtár méretével romlik („egyre lassabb"). A
        # betöltést az alább induló háttér-szinkron szála végzi el, és a
        # `syncFinished` → `_reload_after_sync()` hozza be (a lista addig
        # üres, ugyanúgy, ahogy egy frissen felvett mappa esetén is).
        self._reload(defer_collections=True)
        if not self._current_folder:
            self.restoreSession()
        self.rescan()
        self._watcher = LibraryWatcher(
            tuple(self._roots),
            lambda folders: self.watcherDirty.emit(list(folders)),
        )
        self._watcher.start()
        self._rescan_timer = QTimer(self)
        self._rescan_timer.setInterval(5 * 60 * 1000)
        self._rescan_timer.timeout.connect(self.rescan)
        self._rescan_timer.start()
        # #1275: a LÁTOTT mappa célzott, olcsó újraolvasása — ez az, ami
        # hálózati megosztáson egyáltalán működik (ld. FOLDER_POLL_MS).
        self._folder_poll_timer = QTimer(self)
        self._folder_poll_timer.setInterval(_legacy().FOLDER_POLL_MS)
        self._folder_poll_timer.timeout.connect(self._poll_current_folder)
        self._folder_poll_timer.start()

    def _dedupe_roots(self) -> None:
        """#507: a betöltött (esetleg régi, még nem normalizált
        `WatchedFolders.txt`-ből származó) figyelt gyökerek normalizálása
        és duplikátum-szűrése — az elsőként látott alak marad meg
        (kanonikus, `path_key` szerint egyedi). Csak akkor ír, ha
        ténylegesen változott valami (ne piszkítsuk 








     if self._rescan_timer is not None:
            self._rescan_timer.stop()
        if getattr(self, "_folder_poll_timer", None) is not None:
            self._folder_poll_timer.stop()
            self._folder_poll_timer = None
        if getattr(self, "_locked_dirty_retry_timer", None) is not None:
            self._locked_dirty_retry_timer.stop()
            self._locked_dirty_retry_timer = None
        if self._watcher is not None:
            self._watcher.stop()
            # #1457: a figyelő MAGA dönti el, elengedhető-e. Ha a
          










