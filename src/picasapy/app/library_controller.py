"""Könyvtár-felügyelet: figyelt mappák, élő figyelés (watchdog), háttér-
szinkron és a busy-állapot (#70, #505) — az AppController könyvtár-szelete
(#150).

Mixin-osztály: az `AppController` örökli; a jelzések (syncFinished stb.)
és a slotok a végső osztály meta-objektumába regisztrálódnak, így a QML és
a tesztek felülete változatlan.

#505: a szinkron-munkák busy-könyvelése (`_begin_sync_job`/`_on_sync_job_done`,
korábban itt élt) MEGSZŰNT — a `BackgroundWorkerMixin._start_background`
(minden szinkron-munka ezen indul) magától bejelentkezik/kijelentkezik a
közös `AppBusyRegistry`-ből (`busy_registry.py`), ezért itt már nincs
teendő. Az `isWorking`/`busyChanged` ezt a KÖZÖS nyilvántartást olvassa — a
bélyegkép-betöltés (`_on_thumb_active`) az egyetlen forrás, ami NEM
`_start_background`-on át fut (a `ThumbnailProvider` saját szálkészletet
használ, "aktív kérések száma" szintjelzéssel, nem job-onkénti indítással),
ezért ez marad az egyetlen hely, ahol egy controller KÉZZEL jelentkezik be
a regisztrátumba (él/lefut-szélenként, ld. lent)."""

from __future__ import annotations

import logging
import os
import sqlite3
import threading
import time
from pathlib import Path

from PySide6.QtCore import Property, Qt, Signal, Slot

from picasapy.index import (
    clear_removed_folders_under,
    folder_paths_under,
    folder_scan_stamps,
    move_folder_tree,
    open_index,
    remove_root,
    sync_folder,
)
from picasapy.index.dedup_folders import merge_duplicate_folders
from picasapy.paths import normalize_path, path_key
from picasapy.scanner import (
    LibraryWatcher,
    is_excluded,
    read_scan_list,
    write_exclude_folders,
    write_scan_list,
    write_watched_folders,
)

from .busy_registry import get_app_busy_registry
from .folder_freshness import next_sweep_batch, stale_folders
from .folder_manager_save_controller import FolderManagerSaveMixin
from .formatting import to_local_path
from .initial_scan import (
    SKIP_INITIAL_SCAN_KEY,
    folders_for_choice,
    migration_detected,
    needs_initial_scan,
)
from .worker_thread import BackgroundWorkerMixin

logger = logging.getLogger(__name__)

# #209: a worker-oldali jelzés-ritkítás minimuma (mp) — sok gyorsan kihagyott
# mappánál a queued jelzések ne árasszák el a GUI-szál eseménysorát.
_PROGRESS_EMIT_MIN_S = 0.25
# #209: a rács fokozatos frissítésének minimum-időköze (mp) — a köztes
# eredmények látszanak, de nem fut modell-újratöltés minden kötegnél.
_PROGRESS_RELOAD_MIN_S = 1.5


#: A LÁTOTT mappa célzott újraolvasásának időköze (#1275).
#:
#: ⚠️ Az eredeti Picasa **nem használ operációs rendszer-szintű
#: fájlfigyelést**: a bináris a `ReadDirectoryChangesW`-t és a
#: `SHChangeNotifyRegister`-t nem is importálja, a
#: `FindFirstChangeNotification`-re pedig NULLA hivatkozás van (a
#: `FindClose…` két helyen áll — védekező takarító ág). Helyette
#: újraolvas és összehasonlít (`ytDirScannerChangeList`), amit a beépített
#: `WriteDirscannerCSV` három pillanatképe is megerősít.
#: Levezetés: `docs/specs/picasa-mappakezelo.md` 16. szakasz.
#:
#: Ebből következik a mi felosztásunk: az esemény (watchdog) a
#: GYORSÍTÁS, a lekérdezés a GARANCIA. Hálózati megosztáson az esemény
#: notóriusan elmarad — ott ez az egyetlen út.
#:
#: Miért CSAK a látott mappa, és miért nem a teljes fa: egyetlen könyvtár
#: listázása olcsó, a teljes gyűjteményé nem. A tulajdonos gyűjteménye
#: NAS-on van, mért napló-korláttal — a teljes fa sűrű pásztázása ott
#: valódi kárt okozna. A teljes rescan ezért marad ötpercenként.
FOLDER_POLL_MS = 10_000

#: #1435 — hány TOVÁBBI (a feedben látszó, de nem kiválasztott) mappa
#: PECSÉTJÉT nézzük meg körönként.
#:
#: A rács feedje (#64) egyszerre több mappát mutat; a #1275 célzott
#: újraolvasása viszont csak a kiválasztottat nézte, így a többi mappa új
#: és törölt képei csak az ötperces körben jelentek meg (a helyben átírt
#: fájl pedig ott sem — a mappa mtime-ja nem lép, lemérve).
#:
#: A költség KORLÁTOS és független a könyvtár méretétől: mappánként
#: két-három fájlrendszer-művelet (`folder_freshness.directory_stamp` —
#: kettő, ha van `.picasa.ini`, három, ha a régi nevet is meg kell
#: néznünk). A jelen értékkel a PECSÉT-fázis legfeljebb 24 művelet / 10 mp
#: ≈ 2,4 művelet/mp — nagyságrendekkel a NAS mért 200/mp korlátja alatt.
#:
#: ⚠️ Ez a keret a pecsét-fázisra vonatkozik. Ami MÖGÖTTE jön, az már
#: mappánként változó: az eltérő pecsétű mappa teljes `sync_folder`-t kap
#: (mérve ~2 művelet FÁJLONKÉNT), és a `_on_folders_dirty` gyökér-keresése
#: is `Path.resolve()`-ol mappánként. Ezt a részt a pecsét kapuzza — épp
#: ezért nem szabad a pecsétnek tévesen elavultat jelentenie.
SWEEP_FOLDERS_PER_TICK = 8


def _dedupe_paths(paths: tuple[str, ...]) -> list[str]:
    """Sorrendtartó duplikátum-szűrés a szinkronra küldött mappalistára.

    A kiválasztott mappa és egy elavultnak mért mappa ugyanaz is lehet
    (eltérő alak, pl. záró elválasztó) — kétszer szinkronizálni fölösleges
    hálózati munka."""
    latott: set[str] = set()
    egyedi: list[str] = []
    for path in paths:
        if path not in latott:
            latott.add(path)
            egyedi.append(path)
    return egyedi


class LibraryMixin(FolderManagerSaveMixin, BackgroundWorkerMixin):
    """Figyelt gyökerek kezelése + szinkron-munkák könyvelése."""

    syncFinished = Signal()
    syncFailed = Signal(str)
    # a watchdog szálából érkezik — a Qt automatikusan sorba állítja
    watcherDirty = Signal(list)
    # #70: a háttérmunka (indexelés/thumbnail) állapota változott — a QML
    # busy-animációjának triggere; CSAK tényleges átmenetnél megy ki
    busyChanged = Signal()
    # #209: mappánkénti sync-haladás (mappa, kész, összes, új fotók) — a
    # worker-szálból emittálva; a Qt queued kapcsolattal hozza a GUI-szálra
    syncProgress = Signal(str, int, int, int)
    # #209: a lebegő „Importálás" panel állapota változott
    importChanged = Signal()
    # #449: az első indítás kérdésének állapota (figyelt mappa lett/nem lett)
    initialScanChanged = Signal()

    #: #1207: a figyelt mappa hozzáadása ELUTASÍTVA — (útvonal, ok).
    #
    # ⚠️ A hozzáadás két ágon fordulhat vissza, és mindkettő NÉMA
    # volt: a tulajdonos beállítása eltűnt, és nem tudta meg, miért
    # („Nem értem…"). A duplikáció-védelem némasága a #507 óta
    # szándékos a háttérhívásoknál (első indítás, importálás) —
    # ezért JELZÉST adunk, nem hibaüzenetet: aki kifejezetten kérte
    # (Mappakezelő), az megjeleníti; a többi hívó figyelmen kívül
    # hagyja.
    watchedFolderRejected = Signal(str, str)

    # #1539: EGY frissen kiírt fájl útja — BELSŐ jelzés, a `noteOutputWritten`
    # bocsátja ki, a `_on_output_written` fogadja. Azért jelzés és nem
    # közvetlen hívás, mert a kiírás HÁTTÉRSZÁLON történik (kollázs,
    # filmexport, másolat-mentés), az index-munkát viszont a GUI-szálon kell
    # elindítani: a `_on_folders_dirty` futásjelzőt állít és saját
    # worker-szálat indít, két szálból hívva ezek versenyeznének. A
    # `QueuedConnection` pontosan ezt a szálváltást végzi el — ugyanaz a
    # minta, amit a `collage_save.py` `_workerOutcome`-ja használ.
    _outputWritten = Signal(str)

    # -- busy-állapot (#70, #505) --------------------------------------------

    @Property(bool, notify=busyChanged)
    def isWorking(self):
        """Fut-e háttérmunka (bármelyik, a közös `AppBusyRegistry`-be
        bejelentkezett munka — szinkron, kötegelt effekt, export, import-
        forrás, duplikátum-keresés, arc-szkennelés, adatbázis-áthelyezés
        stb., ld. `busy_registry.py`) — az alsó sáv animációja erre köt.
        Küszöbölt/minimális-láthatóságú érték (a nyilvántartás intézi, ne
        villogjon), nem a nyers "fut-e valami" jel."""
        return get_app_busy_registry().visible

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

    @Property(bool, notify=importChanged)
    def importPanelVisible(self):
        """Látszódjon-e a lebegő panel: fut érdemi szkennelés (új gyökér
        importja, vagy a rescan új fotókat talált), és a felhasználó nem
        zárta be kézzel."""
        return self._import_visible and not self._import_dismissed

    @Property(str, notify=importChanged)
    def importFolderName(self):
        """Az éppen feldolgozott mappa neve (nem a teljes útvonal)."""
        return Path(self._import_folder).name if self._import_folder else ""

    @Property(int, notify=importChanged)
    def importDoneCount(self):
        return self._import_done

    @Property(int, notify=importChanged)
    def importTotalCount(self):
        return self._import_total

    @Property(int, notify=importChanged)
    def importNewCount(self):
        """Az eddig talált ÚJ képek kumulált száma."""
        return self._import_new

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
            and now - self._import_last_reload >= _PROGRESS_RELOAD_MIN_S
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
            logger.info(
                "#507: induláskor %d mappa-duplikátum-csoport összevonva",
                len(report.merged),
            )
        if report.skipped:
            logger.warning(
                "#507: %d mappa-duplikátum-csoport ÖSSZEVONÁSA KIHAGYVA "
                "(ütköző szerkesztés — a duplikátum megmarad, adatvesztés "
                "helyett): %s",
                len(report.skipped),
                ", ".join(key for key, _reason in report.skipped),
            )
        self._reload()
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
        self._folder_poll_timer.setInterval(FOLDER_POLL_MS)
        self._folder_poll_timer.timeout.connect(self._poll_current_folder)
        self._folder_poll_timer.start()

    def _dedupe_roots(self) -> None:
        """#507: a betöltött (esetleg régi, még nem normalizált
        `WatchedFolders.txt`-ből származó) figyelt gyökerek normalizálása
        és duplikátum-szűrése — az elsőként látott alak marad meg
        (kanonikus, `path_key` szerint egyedi). Csak akkor ír, ha
        ténylegesen változott valami (ne piszkítsuk a fájlt feleslegesen)."""
        seen: dict[str, str] = {}
        for root in self._roots:
            normalized = normalize_path(root)
            if not normalized:
                continue
            key = path_key(normalized)
            seen.setdefault(key, normalized)
        deduped = list(seen.values())
        if deduped != self._roots:
            self._roots = deduped
            self._persist_roots()

    def shutdown(self) -> None:
        """Leállítás: figyelő és időzítő leállítása (kilépéskor hívandó)."""
        if self._rescan_timer is not None:
            self._rescan_timer.stop()
        if getattr(self, "_folder_poll_timer", None) is not None:
            self._folder_poll_timer.stop()
            self._folder_poll_timer = None
        if self._watcher is not None:
            self._watcher.stop()
            self._watcher = None

    # -- A Mappakezelő OK-jának MENTÉSI ÚTJA (#1334) -------------------------
    #
    # A szelet külön fájlban él: `folder_manager_save_controller.py`
    # (`FolderManagerSaveMixin`, a `LibraryMixin` őse) — a sorrend- és
    # kapu-szabály pedig Qt nélkül a `folder_manager_save.py`-ban.
    #
    # Ami itt látszik belőle: a `_persist_roots`, a `setFaceDetectionEnabled`
    # és a `removeFolder` OK-fázisban nem ír azonnal, hanem a piszkozatba
    # gyűjt (`_folder_manager_draft`).

    # -- Mappakezelő ---------------------------------------------------------

    def _ensure_folder_manager_scan_state(self) -> None:
        if hasattr(self, "_folder_scan_excluded"):
            return
        self._folder_scan_file = (
            self._watched_file.with_name("scanlist.txt")
            if self._watched_file is not None
            else None
        )
        if self._folder_scan_file is None:
            scanned, excluded, included = (), (), ()
        else:
            scanned, excluded, included = read_scan_list(self._folder_scan_file)
        self._folder_scan_scanned = list(scanned)
        self._folder_scan_excluded = list(excluded)
        self._folder_scan_included = list(included)
        self._folder_scan_generation = 0

    @Slot(str, result=str)
    def folderManagerStateFor(self, path: str) -> str:
        """A scanlist legspecifikusabb, öröklődő felülírása QML-nek."""
        self._ensure_folder_manager_scan_state()
        normalized = normalize_path(path)
        if not normalized:
            return ""
        best_state = ""
        best_length = -1
        for state, roots in (
            ("none", self._folder_scan_excluded),
            ("always", self._folder_scan_included),
        ):
            for root in roots:
                root_normalized = normalize_path(root)
                if (
                    normalized == root_normalized
                    or Path(normalized).is_relative_to(root_normalized)
                ) and len(root_normalized) > best_length:
                    best_state = state
                    best_length = len(root_normalized)
        if normalized in self._folder_scan_scanned and len(normalized) > best_length:
            return "once"
        return best_state

    @Slot(str, str)
    def setFolderManagerState(self, path: str, state: str) -> None:
        """Egy állapot tartós átvezetése, a scanlist teljes újraírásával."""
        self._ensure_folder_manager_scan_state()
        normalized = normalize_path(path)
        if not normalized or state not in {"always", "once", "none"}:
            return
        for values in (
            self._folder_scan_scanned,
            self._folder_scan_excluded,
            self._folder_scan_included,
        ):
            while normalized in values:
                values.remove(normalized)
        target = {
            "always": self._folder_scan_included,
            "once": self._folder_scan_scanned,
            "none": self._folder_scan_excluded,
        }[state]
        target.append(normalized)
        # A már futó teljes sync a következő mappahatáron álljon le: az
        # induláskor kapott exclude-pillanatkép az új döntés után elavult.
        self._folder_scan_generation += 1
        if self._folder_scan_file is not None:
            write_scan_list(
                self._folder_scan_file,
                tuple(self._folder_scan_scanned),
                tuple(self._folder_scan_excluded),
                tuple(self._folder_scan_included),
            )
        self.statusChanged.emit()

    def _folder_manager_excludes_for_root(self, root: str) -> tuple[str, ...]:
        self._ensure_folder_manager_scan_state()
        root_path = Path(normalize_path(root))
        # Egy explicit befoglaló gyökér felülírhat egy kizárt őságat.
        result = []
        for item in self._folder_scan_excluded:
            item_path = Path(normalize_path(item))
            if item_path == root_path or item_path.is_relative_to(root_path):
                result.append(str(item_path))
        return tuple(result)

    def _folder_manager_path_excluded(self, path: str, root: str) -> bool:
        path_obj = Path(normalize_path(path))
        return any(
            path_obj == Path(item) or path_obj.is_relative_to(item)
            for item in self._folder_manager_excludes_for_root(root)
        )

    def _sync_folder_manager_tree(self, conn, root: str, progress=None) -> None:
        excludes = self._folder_manager_excludes_for_root(root)
        if not excludes:
            self._sync_tree(conn, root, progress=progress)
            return
        from . import controller as controller_module

        kwargs = {"exclude": excludes}
        if progress is not None:
            kwargs["progress"] = progress
        controller_module.sync_tree(conn, root, **kwargs)

    def _find_root(self, path: str) -> str | None:
        """#507: a `path`-hoz tartozó, MÁR figyelt gyökér — `path_key`
        szerinti (normalizált, platformhelyes kis-nagybetű-kezelésű)
        egyezéssel, nem nyers szövegösszehasonlítással. `None`, ha nincs
        ilyen figyelt gyökér."""
        key = path_key(path)
        for root in self._roots:
            if path_key(root) == key:
                return root
        return None

    # -- #449: első indítás — egyetlen kérdés, egyetlen OK gomb -----------

    @Property(bool, notify=initialScanChanged)
    def needsInitialScan(self) -> bool:  # noqa: N802 — QML property-konvenció
        """Fel kell-e tenni az első indítás kérdését?

        Csak akkor, ha MÉG NINCS figyelt mappa (a program ilyenkor üres
        lenne), és a felhasználó nem kérte a varázsló kihagyását
        (`skipinitialscan` — az eredetiben is volt erre kulcs)."""
        skip = str(
            self._get_settings().value(SKIP_INITIAL_SCAN_KEY, "false")
        ).lower() in ("true", "1", "yes")
        return needs_initial_scan(tuple(self._roots), skip)

    @Slot(result=bool)
    def initialScanMigration(self) -> bool:  # noqa: N802
        """A MIGRÁCIÓS szövegkészlet kell-e (#1167) — van-e korábbi
        Picasa-telepítés (az eredetiben `0x0040d450`, felderítő
        `0x00406c00`; nálunk a `scanner.discovery`, #146)."""
        return migration_detected()

    @Slot(str, result="QVariant")
    def initialScanFolders(self, choice: str):  # noqa: N802
        """A választáshoz tartozó mappák — a párbeszéd ebből mutatja meg
        ELŐRE, mit fog beolvasni (az eredeti is kiírta a hatókört)."""
        return list(folders_for_choice(choice))

    @Slot(str)
    def applyInitialScan(self, choice: str) -> None:  # noqa: N802
        """Az első indítás választásának végrehajtása: a mappák felvétele
        figyelt gyökérként. A varázsló ezután nem jön elő többé."""
        for folder in folders_for_choice(choice):
            self.addWatchedFolder(folder)
        self._get_settings().setValue(SKIP_INITIAL_SCAN_KEY, "true")
        self.initialScanChanged.emit()

    @Slot(str)
    def addWatchedFolder(self, path_or_url: str) -> None:
        """Új figyelt mappa (Mappakezelő / első indítás). file:// URL-t is
        elfogad (a QML FolderDialog azt ad).

        #507: a duplikáció-védelem `path_key`-alapú (a normalizált,
        platformhelyes kis-nagybetű-kezelésű alakra nézve egyedi) —
        záró perjel, `..`/`.` szegmens, szimbolikus link vagy (Windowson)
        eltérő kis-nagybetűzés SEM vezet duplikátumhoz."""
        path = normalize_path(to_local_path(path_or_url))
        # ⚠️ #1207: az elutasítás OKÁT megnevezzük. Némán visszafordulni azt
        # a látszatot kelti, hogy sikerült — a tulajdonos beállítása így
        # tűnt el nyomtalanul, és nem tudta meg, miért.
        if not path:
            self.watchedFolderRejected.emit(str(path_or_url), "ures-utvonal")
            return
        if self._find_root(path) is not None:
            self.watchedFolderRejected.emit(path, "mar-figyelt")
            return
        if not Path(path).is_dir():
            self.watchedFolderRejected.emit(path, "nem-mappa")
            return
        # #1249: az újra felvett mappa (és alfái) sírkövei feloldódnak —
        # különben a beolvasás némán hagyná ki, és senki nem tudná, miért
        with open_index(self._db_path) as conn:
            clear_removed_folders_under(conn, path)
        self._roots.append(path)
        self._persist_roots()
        self._restart_watcher()
        self.statusChanged.emit()
        # #216: újra-hozzáadásnál a korábbi eltávolítás leállítási jelzője
        # már nem érvényes — törölni kell, különben a sync azonnal leállna
        self._cancel_event(path).clear()
        # #209: új gyökér importja mindig „nagy" szkennelés — a lebegő
        # panel az első haladás-jelzéstől látszik (forced)
        self._import_forced = True
        progress = self._make_progress_emitter(
            should_stop=self._make_should_stop(path)
        )

        def worker():
            try:
                with open_index(self._db_path) as conn:
                    self._sync_folder_manager_tree(conn, path, progress=progress)
            finally:
                self.syncFinished.emit()

        # #438/#505: nyilvántartott daemon-szál (BackgroundWorkerMixin, #430) —
        # a busy-bejelentkezés is ITT, a mixinben történik (ld. worker_thread.py)
        self._start_background(worker, name="picasapy-sync-addfolder")

    @Slot(str)
    def scanFolderOnce(self, path_or_url: str) -> None:
        """„Keresés egyszer" (#231, Mappakezelő-fa): a mappa (és almappái)
        egyszeri, azonnali beolvasása az indexbe — a figyelt gyökerek
        (self._roots) és a WatchedFolders.txt-persistencia NÉLKÜL. A valódi
        Picasa is így viselkedik: a fotók bekerülnek a könyvtárba, de a
        mappa nem marad figyelve — újraindítás (vagy a Mappakezelő
        újranyitása) után ismét „nem figyelt"-ként látszik.

        Már figyelt gyökérnél nincs teendő (a folyamatos figyelés úgyis
        lefedi) — a hívás ekkor csendben kimarad.

        #1213: a néma őr-sor szétbontva. Az eredeti Mappakezelő
        (`0x007c27d0`) EGYETLEN üzenetet ismer (`CFolderMgrDialog::warning`,
        a teljes meghajtó figyeléséről), és nála a „Keresés egyszer" nem
        azonnali művelet, hanem a mappa ÁLLAPOTA (`foldermgr/scan_once`
        rádió) — elutasítás-üzenet tehát nincs hozzá. Nálunk azonnali
        művelet, ezért csak azt jelezzük, amitől a felhasználó kérése
        ténylegesen ELMARAD; a „már figyelt" eset nem ilyen (a két rádió
        az eredetiben is kizárja egymást)."""
        path = normalize_path(to_local_path(path_or_url))
        if not path:
            self.watchedFolderRejected.emit(str(path_or_url), "ures-utvonal")
            return
        if self._find_root(path) is not None:
            return  # értelmes no-op: a folyamatos figyelés lefedi
        if not Path(path).is_dir():
            self.watchedFolderRejected.emit(path, "nem-mappa")
            return
        # #1249: az egyszeri keresés is feloldja a sírkövet — a felhasználó
        # kifejezetten ezt a mappát kérte
        with open_index(self._db_path) as conn:
            clear_removed_folders_under(conn, path)
        # nincs leállítási-jelző kötés (nem figyelt gyökér): egyszeri,
        # meg nem szakítható munka
        progress = self._make_progress_emitter()

        def worker():
            try:
                with open_index(self._db_path) as conn:
                    self._sync_folder_manager_tree(conn, path, progress=progress)
            finally:
                self.syncFinished.emit()

        # #438/#505: nyilvántartott daemon-szál (BackgroundWorkerMixin, #430) —
        # a busy-bejelentkezés is ITT, a mixinben történik (ld. worker_thread.py)
        self._start_background(worker, name="picasapy-sync-scanonce")

    @Slot(str)
    def removeFolder(self, path: str) -> None:
        """„Eltávolítás a Picasából" a Mappakezelő fájából (#231): figyelt
        gyökérnél a teljes meglévő logika (`removeWatchedFolder` —
        leállítási jelző, watcher-újraindítás, nézet-frissítés); egyszer
        beolvasott (nem figyelt) mappánál elég az index-takarítás, nincs
        se watcher, se leállítási jelző, amit kezelni kellene."""
        path = normalize_path(path)
        if not path:
            return
        # #1249: SÍRKŐ mindkét ágon — az eredetiben a mappa nem törlődik,
        # hanem `]album:removed` jelöléssel marad (`0x004b9200`), és a
        # beolvasó nem veszi fel újra. Enélkül az almappa a következő
        # rescan()-nél visszajött (a jegy gépi mérése).
        watched_root = self._find_root(path)
        if watched_root is not None:
            # #1334: OK-fázisban a sírkő a mentési út 2. lépésében íródik
            # (a figyelt mappák fájlja UTÁN), egyébként azonnal
            self._add_tombstone(watched_root)
            self.removeWatchedFolder(watched_root)
            return
        with open_index(self._db_path) as conn:
            remove_root(conn, path)
        self._add_tombstone(path)
        self._reload()

    @Slot(str)
    def removeWatchedFolder(self, path: str) -> None:
        """„Eltávolítás a Picasából": a gyökér kikerül a figyeltek közül és
        az indexből is (a fájlokhoz természetesen nem nyúlunk).

        #216 — futó szkennelés közben is konzisztens: (1) a leállítási
        jelző beállítása — a gyökér futó syncje a következő mappa-határon
        tisztán leáll; (2) azonnali index-takarítás (`remove_root`,
        SQL-oldali prune); (3) az Importálás-panel eltüntetése, ha épp az
        eltávolított gyökér mappáját mutatta; (4) nézet-frissítés. A worker
        késői jelzéseit a `_on_sync_progress` gyökér-ellenőrzése nyeli el."""
        watched_root = self._find_root(path)
        if watched_root is None:
            return
        path = watched_root
        # a jelző MÉG a gyökér-lista módosítása előtt áll be — a worker
        # should_stop-ja bármelyik feltételen (jelző VAGY lista) elkapja
        self._cancel_event(path).set()
        self._roots.remove(path)
        self._persist_roots()
        self._restart_watcher()
        with open_index(self._db_path) as conn:
            remove_root(conn, path)
        # a panel ne ragadjon be: ha az eltávolított gyökér mappáját
        # mutatta, azonnal tűnjön el (állapot-nullázással)
        if self._import_folder and self._root_for_folder(self._import_folder) is None:
            self._on_import_finished()
        if self._current_folder and (
            self._current_folder == path
            or Path(self._current_folder).is_relative_to(path)
        ):
            self._current_folder = ""
            self._view_mode = ("folder", "")
            self._show(())
        self._reload()

    # -- Arcfelismerés-kizárás (#449, NEGYEDIK, a Scan Always/Once/Remove
    # hármastól FÜGGETLEN kapcsoló) -------------------------------------

    @Slot(str, result=bool)
    def faceDetectionEnabledFor(self, path: str) -> bool:
        """Igaz, ha a mappa NINCS az arcfelismerésből kizárva (nincs a
        `FRExcludeFolders.txt`-ben, és egyik őse sincs) — ld.
        `scanner/exclude.py`. Ez a kapcsoló TELJESEN FÜGGETLEN a
        `stateFor`/`setState` (Scan Always/Once/Remove) hármastól: egy
        mappa lehet egyszerre figyelt ÉS arcfelismerésből kizárt.

        ŐSZINTESÉG: a projektben MÉG NINCS arcfelismerés-motor — ez a
        property egyelőre csak a felhasználó SZÁNDÉKÁT tükrözi (a
        Picasa-kompatibilis fájlba írva); életbe akkor lép majd, amikor
        az arcfelismerés-fázis megérkezik."""
        if not path:
            return True
        return not is_excluded(path, tuple(self._face_excluded_roots))

    @Slot(str, bool)
    def setFaceDetectionEnabled(self, path: str, enabled: bool) -> None:
        """Arcfelismerés be/ki egy mappára és az alfáira (#449) — a három
        scan-állapottól FÜGGETLENÜL. Kikapcsoláskor a mappa felkerül a
        `FRExcludeFolders.txt`-be, bekapcsoláskor lekerül róla; a fájl
        Picasa-kompatibilis formátumban íródik (`write_exclude_folders`,
        a `write_watched_folders` mintájára).

        ŐSZINTESÉG: ez a metódus MA nem töröl semmilyen tényleges arc-
        adatot vagy név-címkét (arcfelismerés-motor még nincs a
        projektben) — kizárólag a kizárási szándékot rögzíti. A
        felhasználó felé megjelenő megerősítő kérdés (eredeti Picasa-
        szöveg) a `FolderStatePanel.qml`-ben él, ezt a metódust csak a
        megerősítés UTÁN hívja a QML."""
        path = str(path)
        if not path:
            return
        roots = list(self._face_excluded_roots)
        if enabled:
            if path in roots:
                roots.remove(path)
        else:
            if path not in roots:
                roots.append(path)
        if roots == self._face_excluded_roots:
            return
        self._face_excluded_roots = roots
        # #1334: OK-fázisban a fájl a mentési út 3. lépésében íródik, és
        # csak akkor, ha a két lista bármelyike nem üres (a KAPU) — a
        # szándékot addig a piszkozat tartja
        draft = self._folder_manager_draft()
        if draft is not None:
            self._fm_draft = draft.with_face_change(path, enabled)
        elif self._exclude_file is not None:
            write_exclude_folders(self._exclude_file, tuple(roots))
        self.statusChanged.emit()

    def _persist_roots(self) -> None:
        # #1334: OK-fázisban a figyelt mappák fájlja a mentési út 1.
        # lépésében íródik — EGYSZER, nem mappánként
        if self._folder_manager_draft() is not None:
            return
        if self._watched_file is not None:
            write_watched_folders(self._watched_file, tuple(self._roots))

    def _restart_watcher(self) -> None:
        if self._watcher is None:
            return  # a start() még nem futott (tesztek, korai hívás)
        self._watcher.stop()
        self._watcher = LibraryWatcher(
            tuple(self._roots),
            lambda folders: self.watcherDirty.emit(list(folders)),
        )
        self._watcher.start()

    # -- háttér-szinkron -----------------------------------------------------

    @Slot(list)
    def _on_folders_dirty(self, folders) -> None:
        """A watcher által jelzett (esetleg több) mappa célzott, nem-
        rekurzív szinkronja EGY háttérszálon (#143).

        A `sync_tree` helyett a mappa-pontos `sync_folder`-t hívjuk: a
        watcher konkrét mappát jelez, nincs ok a teljes részfa
        újrajárására. A jelzett mappák koaleszálva, egyetlen worker-
        szálban dolgozódnak fel — a watcher amúgy is debounce-ol
        (`scanner/watcher.py`), így egy jelzésben több mappa is jöhet.

        ⚠️ #1440: ennek az ágnak SAJÁT futásjelzője van (`_dirty_running`).
        A `_sync_running` a `rescan()`-é, a `_sweep_running` (#1435) pedig
        a pecsét-köröké — egyik sem fedte a MÁSIK célzott szinkront. Egy
        hosszú, hálózati megosztáson futó dirty-worker mellé így egy
        következő jelzés (a tíz másodperccel későbbi lekérdezési kör vagy
        egy watcher-esemény) simán indított egy másodikat: két egyidejű
        index-íróból `sqlite3.OperationalError`, abból pedig a
        felhasználónak szóló `syncFailed` lett. A #1435 óta a worker akár
        kilenc mappát is visz, tehát sokkal tovább él — a kitettség nőtt."""
        paths = [str(f) for f in folders]
        if not paths:
            return  # üres jelzés: nincs mit szinkronizálni, jelzőt sem fogunk
        if self._sync_running or self._dirty_running:
            # #1181: NEM dobjuk el. A korábbi „a futó teljes szinkron
            # úgyis lefedi" feltevés hamis: ha a szinkron az adott mappán
            # MÁR túlment, a változás (pl. egy törlés) a következő
            # periodikus rescanig láthatatlan marad — a bejelentő ezt
            # látta „az indexkép ottmarad"-ként. Ehelyett feljegyezzük, és
            # a szinkron végén (`_flush_pending_dirty`) behozzuk.
            #
            # #1440: ugyanez a várólista fogadja a FUTÓ CÉLZOTT szinkron
            # alatt érkező jelzéseket is. Halmaz, tehát egyetlen mappa sem
            # veszhet el akkor sem, ha közben több jelzés fut be.
            self._pending_dirty.update(paths)
            return

        def worker():
            errors = []
            try:
                with open_index(self._db_path) as conn:
                    for folder in paths:
                        root = self._root_for_folder(folder)
                        if root is None:
                            continue  # már nem figyelt gyökér alatt — kihagyva
                        if self._folder_manager_path_excluded(folder, root):
                            continue
                        try:
                            # #216: eltávolított gyökér mappája már ne íródjon
                            sync_folder(
                                conn,
                                root,
                                folder,
                                exclude=self._folder_manager_excludes_for_root(root),
                                should_stop=self._make_should_stop(root),
                            )
                        except (OSError, RuntimeError):
                            pass  # eltűnt mappa — a periodikus rescan rendezi
                        except sqlite3.OperationalError as error:
                            # busy_timeout lejárt (párhuzamos író) — ez NEM
                            # nyelhető el némán: a felhasználó jelzést kap,
                            # a maradék mappák feldolgozása folytatódik.
                            errors.append(f"{folder}: {error}")
            finally:
                # #1440: a jelzőt az EMITEK ELŐTT engedjük el.
                #
                # ⚠️ NEM azért, mert a `_flush_pending_dirty` különben zárt
                # kapuba futna: az a `syncFinished`-re fut, ami innen, a
                # munkásszálról QUEUED módon ér a GUI-szálra, tehát
                # mindenképp ez után a `finally` után hívódik — a sorrend a
                # kapu szempontjából közömbös.
                #
                # Az ok: maga az EMIT dobhat. Leállás közben a C++ oldal már
                # eltűnhet, és a `RuntimeError` a jelzőt igazon hagyná —
                # onnantól minden célzott frissítés némán a várólistán
                # ragadna. A kapcsoló itt már biztonságos is: az
                # `open_index` blokk lezárult, ez a szál nem ír többé.
                self._dirty_running = False
                try:
                    if errors:
                        self.syncFailed.emit("; ".join(errors))
                    self.syncFinished.emit()
                except RuntimeError:
                    # ugyanaz a védelem, mint a sweep-workerében (#1435):
                    # leállás közben a C++ oldal már eltűnhetett
                    logger.debug(
                        "#1440: a célzott szinkron jelzése elmaradt", exc_info=True
                    )

        # A jelző a szálindítás ELŐTT áll be: a hívások mind a GUI-szálon
        # érkeznek (queued `watcherDirty`, időzítő, QML-slot), tehát a
        # beállítás és az ellenőrzés között nincs másik hívó. A kezdőérték
        # a `controller.py`-ban, a `_sync_running` mellett születik.
        self._dirty_running = True
        try:
            # #438/#505: nyilvántartott daemon-szál (BackgroundWorkerMixin,
            # #430) — a busy-bejelentkezés is ITT, a mixinben történik
            # (ld. worker_thread.py)
            self._start_background(worker, name="picasapy-sync-dirty")
        except BaseException:
            # ⚠️ #550/#1435 mintája: a `start()` elbukhat (`RuntimeError:
            # can't start new thread`), és akkor a `worker` — vele a
            # `finally` ága — SOSEM fut le. Beragadt jelzővel innentől
            # MINDEN célzott frissítés a várólistára menne, és onnan soha
            # senki nem hozná be: a rács a munkamenet végéig NÉMÁN sosem
            # frissülne magától. Egyetlen tranziens hiba örökre elrontaná.
            self._dirty_running = False
            raise

    def _root_for_folder(self, folder: str) -> str | None:
        """A jelzett mappához tartozó figyelt gyökér (a `sync_folder`
        védőkorlátjához) — a leghosszabb egyező előtag, ha van ilyen."""
        folder_path = Path(folder).resolve()
        best: str | None = None
        for root in self._roots:
            root_path = Path(root).resolve()
            if folder_path == root_path or folder_path.is_relative_to(root_path):
                if best is None or len(root) > len(best):
                    best = root
        return best

    @Slot()
    def _poll_current_folder(self) -> None:
        """A LÁTOTT mappa célzott újraolvasása (#1275).

        Nem a teljes fa: egyetlen könyvtár listázása olcsó, és a
        felhasználó azt a mappát nézi, ahova a képet másolja. A munkát a
        watcher-ág végzi (`_on_folders_dirty`), tehát a koaleszálás, a
        sírkövek és a kizárások ugyanúgy érvényesek.

        Futó szinkron alatt kihagyjuk: az úgyis frissít, és két egyidejű
        író fölöslegesen versengene az indexen.

        #1435: a kiválasztott mappa mellé a feedben LÁTSZÓ többi mappa
        olcsó frissesség-ellenőrzése is belefér (`_sweep_candidates` +
        `_stale_feed_folders`) — teljes újraolvasást csak az a mappa kap,
        amelyik tényleg megváltozott.

        ⚠️ A pecsét-ellenőrzés HÁTTÉRSZÁLON fut, két okból: (1) a statok
        hálózati megosztáson lassúak, a GUI-szálon akadást okoznának;
        (2) a végén EGYETLEN `watcherDirty` megy ki a kiválasztott és az
        elavult mappákkal együtt, tehát EGY TICKBŐL egy szinkron-worker
        lesz — két egyidejű index-író `OperationalError`-t és a
        felhasználónak szóló hibajelzést eredményezne.

        ⚠️ #1440: a TICKEK KÖZÖTTI átfedést két külön kapu zárja ki, és
        ez a kettő NEM ugyanaz:

        * `_sweep_running` — a pecsét-körök átfedése. Akadó hálózati
          mounton a kör túlfuthat a 10 másodpercen; kapu nélkül a
          következő időzítő-jelzés újabb pecsét-szálat indítana.
        * `_dirty_running` (`_on_folders_dirty`) — a célzott szinkronok,
          vagyis az INDEX-ÍRÓK átfedése. A #1440 előtt ez hiányzott: egy
          hosszú (a #1435 óta akár kilenc mappás) szinkron mellé a
          következő tick simán indított egy másodikat.

        Mivel az írók átfedését már a `_dirty_running` zárja ki, a futó
        pecsét-kör alatt is kimehet a kiválasztott mappa jelzése — a
        #1275 alapgaranciája így akkor sem esik ki egyetlen körre sem, ha
        a sweep egy lassú mounton bent ragad."""
        mappa = self._current_folder
        if not mappa or self._sync_running:
            return
        if getattr(self, "_sweep_running", False):
            # #1440: az előző kör pecsétjei még futnak (lassú mount), de a
            # #1275 alapgaranciája — a LÁTOTT mappa újraolvasása — ettől
            # nem eshet ki. A pecsét-kör csak OLVAS; az írók átfedése ellen
            # a `_on_folders_dirty` saját jelzője véd, tehát ez a jelzés
            # legrosszabb esetben is csak a várólistára kerül.
            self._on_folders_dirty([mappa])
            return
        batch = self._sweep_candidates(mappa)
        if not batch:
            # nincs más látszó mappa: a #1275 útja változatlanul
            self._on_folders_dirty([mappa])
            return
        self._sweep_running = True

        def worker():
            # ⚠️ A kiválasztott mappa jelzése AKKOR IS ki kell hogy menjen,
            # ha a pecsét-ellenőrzés elhasal — különben a #1435 kényelmi
            # gyorsítása megbénítaná a #1275 alapgaranciáját.
            elavult: tuple[str, ...] = ()
            try:
                elavult = self._stale_feed_folders(batch)
            except Exception:
                # a daemon-szálról kiszökő kivétel tíz másodpercenként
                # köpne tracebacket a stderr-re — naplózzuk és megyünk
                logger.exception("#1435: a frissesség-sweep elhasalt")
            finally:
                self._sweep_running = False
                try:
                    # a jelzés a watchdog-éval azonos úton megy a GUI-szálra
                    # (queued `watcherDirty`) — onnan a jól bejáratott
                    # `_on_folders_dirty` végzi a koaleszálást és a szinkront
                    self.watcherDirty.emit(_dedupe_paths((mappa, *elavult)))
                except RuntimeError:
                    # leállás közben a C++ oldal már eltűnhetett
                    logger.debug("#1435: a sweep jelzése elmaradt", exc_info=True)

        try:
            # #438/#505: nyilvántartott daemon-szál (BackgroundWorkerMixin, #430)
            self._start_background(worker, name="picasapy-frissesseg-sweep")
        except BaseException:
            # ⚠️ #550 mintája: a `start()` elbukhat (`RuntimeError: can't
            # start new thread`), és akkor a `worker` — vele a `finally`
            # ága — SOSEM fut le. A kapu a metódus ELEJÉN áll, tehát egy
            # beragadt jelző után nemcsak a sweep halna meg, hanem a
            # `_on_folders_dirty` alapág is: a rács a munkamenet végéig
            # NÉMÁN sosem frissülne magától. Pont a jegy ellentéte.
            self._sweep_running = False
            raise

    def _sweep_candidates(self, current: str) -> tuple[str, ...]:
        """A körönként megnézendő adag a feedben látszó, KIVÁLASZTOTTON
        KÍVÜLI mappákból (#1435) — tiszta válogatás, fájlrendszert NEM ér.

        Körönként legfeljebb `SWEEP_FOLDERS_PER_TICK` mappa kerül sorra,
        körbeforgó kurzorral: a költség így korlátos marad akkor is, ha a
        feed több száz mappát mutat.

        A jelenleg NEM ELÉRHETŐ (offline, #459/5) mappák kimaradnak: a
        pecsétjük úgyis None volna, tehát minden körben elavultnak
        látszanának, és a lecsatolt NAS-mount örökös, hiábavaló teljes
        újraolvasás-kísérleteket kapna.

        ⚠️ Ennek ára van: a VISSZATÉRŐ mount csak akkor kerül vissza a
        sweep látókörébe, amikor az ötperces rescan (vagy a mappa
        kiválasztása) levette róla az offline jelölést."""
        offline = self._folders.offline_paths()
        candidates = tuple(
            group["path"]
            for group in self._feed_groups
            if group.get("path")
            and group["path"] != current
            and group["path"] not in offline
        )
        if not candidates:
            return ()
        # a kurzor lustán születik: a mixinnek nincs saját __init__-je
        cursor = getattr(self, "_sweep_cursor", 0)
        batch, self._sweep_cursor = next_sweep_batch(
            candidates, cursor, SWEEP_FOLDERS_PER_TICK
        )
        return batch

    def _stale_feed_folders(self, batch: tuple[str, ...]) -> tuple[str, ...]:
        """Az adagból azok a mappák, amelyek pecsétje eltér az indexben
        tároltól (#1435) — mappánként két-három fájlrendszer-művelet.

        ⚠️ HÁTTÉRSZÁLON hívandó (ld. `_poll_current_folder`).

        Hiba esetén üres eredmény: a frissesség-ellenőrzés kényelmi
        gyorsítás, nem törhet meg tőle a körönkénti alapfrissítés.

        ⚠️ A kivétel-háló SZÁNDÉKOSAN széles. Az `open_index` nem csak
        `sqlite3.Error`-t dob: túl régi SQLite-nál és újabb sémaverziónál
        `RuntimeError` jön (`index/database.py`). Ha az kiszökne, a
        daemon-szálon traceback lenne belőle tíz másodpercenként, a
        `watcherDirty` pedig sosem menne ki — tehát a #1275
        alapgaranciája is elveszne."""
        if not batch:
            return ()
        try:
            with open_index(self._db_path) as conn:
                stored = folder_scan_stamps(conn, batch)
            return stale_folders(batch, stored)
        except Exception:
            logger.debug(
                "#1435: a frissesség-ellenőrzés nem sikerült", exc_info=True
            )
            return ()

    def rescan(self) -> None:
        if self._sync_running:
            return  # egy író elég; a futó szinkron végén úgyis frissülünk
        self._sync_running = True
        # #438/#505: nyilvántartott daemon-szál (BackgroundWorkerMixin, #430) —
        # a busy-bejelentkezés is ITT, a mixinben történik (ld. worker_thread.py)
        self._start_background(self._sync_worker, name="picasapy-sync-rescan")

    def _sync_worker(self) -> None:
        """Háttér-szinkron. Egy rossz gyökér (pl. elavult Windows-útvonal a
        WatchedFolders-ből) nem nyelhet el mindent némán: hibánként jelzünk,
        a többi gyökér feldolgozása folytatódik, és a vége mindig
        syncFinished."""
        errors = []
        try:
            with open_index(self._db_path) as conn:
                # pillanatkép: a lista a főszálon menet közben módosulhat
                # (#216, removeWatchedFolder) — az iteráció ettől független
                for root in tuple(self._roots):
                    should_stop = self._make_should_stop(root)
                    if should_stop():
                        continue  # már az indulás előtt eltávolították
                    # gyökerenkénti emitter: a megszakítás-kérés (a progress
                    # visszatérési értéke) csak a saját gyökerére áll be
                    progress = self._make_progress_emitter(should_stop=should_stop)
                    try:
                        self._sync_folder_manager_tree(conn, root, progress=progress)
                    except (OSError, RuntimeError, sqlite3.OperationalError) as error:
                        errors.append(f"{root}: {error}")
        except Exception as error:  # pl. index-migrációs hiba
            errors.append(str(error))
        finally:
            self._sync_running = False
            if errors:
                self.syncFailed.emit("; ".join(errors))
            self.syncFinished.emit()

    @Slot()
    def _flush_pending_dirty(self) -> None:
        """A szinkron alatt elhalasztott mappa-frissítések behozása (#1181).

        A `syncFinished`-re fut. A halmazt ELŐBB ürítjük ki, hogy az
        újraindított szinkron ne dolgozza fel kétszer ugyanazt, és hogy egy
        közben érkező jelzés a KÖVETKEZŐ körbe kerüljön.

        ⚠️ #1440: az átadás DOBHAT — a `_on_folders_dirty` újradobja a
        bukott szálindítást (`RuntimeError: can't start new thread`). Az
        előre kiürített halmazba ilyenkor senki nem tenné vissza a
        mappákat, a kivétel pedig a slotból kiszökve csak tracebacket ír:
        a lemaradás némán elveszne az ötperces rescanig. Ezért dobás
        esetén visszatesszük őket — a következő `syncFinished` behozza."""
        if not self._pending_dirty:
            return
        folders = sorted(self._pending_dirty)
        self._pending_dirty = set()
        try:
            self._on_folders_dirty(folders)
        except BaseException:
            self._pending_dirty.update(folders)
            raise

    @Slot(int)
    def resyncFolderOfRow(self, row: int) -> None:
        """A sorhoz tartozó mappa resyncje — a néző bezárásakor hívjuk:
        a feedben (#64) a néző át is léphetett másik mappába, ezért nem a
        kiválasztott, hanem az épp nézett kép mappáját frissítjük."""
        photos = self._photos.photos
        if 0 <= row < len(photos):
            self.resyncFolder(photos[row].folder_path)

    @Slot(str)
    def resyncFolder(self, folder_path: str) -> None:
        """Egy mappa újraszinkronja + nézetfrissítés — a néző bezárásakor
        hívjuk (#59): a szerkesztések (filters=) így NAS-on is rögtön
        látszanak a rácson, nem az 5 perces rescanre várva.

        #86: a szinkron HÁTTÉRSZÁLON fut (a _on_folders_dirty útján), így a
        hívó nézetváltás — „Vissza a könyvtárhoz" — hálózati meghajtón sem
        blokkolja a UI-szálat; a végén a syncFinished frissíti a nézetet."""
        if not folder_path:
            return
        self._on_folders_dirty([folder_path])

    # SZÁNDÉKOSAN nincs `@Slot`: a hívó a `wire_fileops` PYTHON-oldali
    # kötése (`folderMoved` → itt), a QML soha nem hívja. Slotként a
    # `kepesseg_or.py` joggal jelezné felületről elérhetetlen képességnek.
    def resyncMovedFolder(self, old_path: str, new_path: str) -> None:  # noqa: N802
        """Egy ÁTHELYEZETT MAPPA két végének célzott újraolvasása (#1538).

        A `resyncFolder` itt két okból nem elég:

        1. **A mappa MAGA az érintett**, nem a szülője. A `wire_fileops`
           `refresh()`-e fájlutakra van szabva (`_watched_folder_of` a
           `.parent`-et veszi) — mappára alkalmazva a SZÜLŐT olvasná újra,
           az pedig nem-rekurzív, tehát az áthelyezett mappa sora létre sem
           jönne.
        2. **A részfa is mozdul.** A `sync_folder` egyetlen mappát olvas,
           az almappák sorai a régi (már nem létező) út alatt ragadnának.

        Ezért mindkét oldal RÉSZFAKÉNT megy be a szokásos célzott
        szinkronba (`_on_folders_dirty`):

        * az ÚJ oldal a lemezről (az indexben még nincs benne),
        * a RÉGI oldal az indexből (a lemezen már nincs meg).

        A takarítás így is mappánként, a `sync_folder` `folder_looks_offline`
        próbáján át történik: elérhetetlen (nem eltűnt) mappa sorai
        megmaradnak, offline jelöléssel — nem törlünk olyan sort, amiről
        nem tudjuk, hogy elavult.

        Mérés a javítás előtt (valódi vezérlő, produkciós időzítők; a
        részletek a `tests/app/test_mappa_athelyezes_resync_1538.py`
        docstringjében): figyelő nélkül az ÚJ hely 25 s alatt sem jelent
        meg, miközben a #1275 lekérdezés a RÉGI helyet 4,7 s alatt kiszedte
        az indexből — a felhasználó képei tehát az ötperces rescanig SEHOL
        nem voltak meg. Ugyanez EGY KÉPPEL 0,11 s."""
        regi = normalize_path(to_local_path(old_path))
        uj = normalize_path(to_local_path(new_path))
        if not regi or not uj:
            return
        # #1542: ha MAGA a figyelt gyökér mozdult el, előbb a HORGONYT
        # állítjuk helyre (index + `_roots` + `WatchedFolders.txt`), és
        # csak utána megy a szokásos célzott újraolvasás — különben az új
        # hely egyetlen gyökér alá sem esne, tehát a `_on_folders_dirty`
        # némán kihagyná.
        self._kovesd_a_gyoker_athelyezeset(regi, uj)
        mappak = _dedupe_paths(
            (*self._reszfa_a_lemezen(uj), *self._reszfa_az_indexbol(regi))
        )
        if mappak:
            self._on_folders_dirty(mappak)

    def _kovesd_a_gyoker_athelyezeset(self, regi: str, uj: str) -> bool:
        """A FIGYELT GYÖKÉR áthelyezésének követése (#1542).

        Mérés a javítás előtt (valódi `AppController`, produkciós
        `FOLDER_POLL_MS`, kétszintű könyvtár, három kép; részletek a
        `tests/app/test_gyoker_athelyezes_kovetes_1542.py` docstringjében):
        a gyökér áthelyezése után a `_roots` és a `WatchedFolders.txt` a
        régi helyre mutatott, és **a produkciós alapbeállításban (figyelő
        és #1275 lekérdezés bekapcsolva) az index KIÜRÜLT: 3 mappa/3 fotó
        → 0/0**, a bal hasáb üres lett. A jegy leírásának az az állítása,
        hogy „nem vész el index", tehát HAMIS volt: a #1538 védelme csak a
        saját ágát fogja vissza, a lekérdezési kör viszont a látott (a
        lemezen valóban eltűnt) mappákat függetlenül kiveszi.

        A sorrend kötött, és mindegyik lépés az előző sikerére épül:

        1. az INDEX részfájának ÁTÍRÁSA az új útra (`move_folder_tree`) —
           sort nem töröl és nem hoz létre;
        2. a `_roots` és a `WatchedFolders.txt` átállítása;
        3. a figyelő újraindítása az új gyökérre;
        4. a látott mappa átvezetése, ha épp a mozgatott fát nézte.

        ## Mikor NEM követünk

        **Ha a régi hely helyén (ugyanazon a néven) MÁS mappa áll.** Ez nem
        elméleti: a felhasználó fájlkezelővel is mozgathat, és egy
        szinkron-kliens vagy az XDG újra létrehozhatja a nevet. A gyökér az
        egész könyvtár horgonya — ha a régi néven ÚJRA létezik mappa, akkor
        a figyelt út egy VALÓDI helyet nevez meg, és az átállítás azt
        jelentené, hogy némán abbahagyjuk egy létező mappa figyelését,
        ráadásul a régi mappa indexsorait egy MÁSIK fizikai mappára
        akasztjuk (útvonal szerint a kettő megkülönböztethetetlen). Ilyenkor
        inkább nem írunk, csak naplózunk — és marad a #1538 védelme: a régi
        oldal takarítása kimarad (`_reszfa_az_indexbol`).

        Ugyanígy nem követünk, ha az ÚJ hely nem létező mappa, vagy ha az
        index átírása ütközésbe fut — üres vagy hibás gyökérlistát semmilyen
        ágon nem írunk ki.

        Igazat ad, ha a gyökér ténylegesen követve lett."""
        gyoker = self._find_root(regi)
        if gyoker is None:
            return False  # nem a gyökér mozdult — a #1538 útja változatlan
        if not Path(uj).is_dir():
            logger.warning(
                "#1542: a figyelt gyökér új helye nem létező mappa (%s) — a "
                "horgony változatlanul marad: %s",
                uj,
                gyoker,
            )
            return False
        if Path(regi).exists():
            logger.warning(
                "#1542: a figyelt gyökér régi helyén (%s) ISMÉT áll valami — "
                "a horgonyt NEM állítjuk át %s-ra, mert az egy létező mappa "
                "figyelését hagyná abba némán.",
                regi,
                uj,
            )
            return False
        try:
            with open_index(self._db_path) as conn:
                move_folder_tree(conn, regi, uj)
        except (ValueError, sqlite3.Error, OSError):
            # az index érintetlen maradt (a `move_folder_tree` vagy mindent
            # átír, vagy semmit) — horgonyt sem írunk át, hogy a kettő ne
            # csússzon szét
            logger.exception(
                "#1542: az áthelyezett gyökér indexsorait nem sikerült "
                "átírni (%s → %s) — a horgony változatlan marad", regi, uj
            )
            return False
        # a lista ÚJ példányként áll össze (immutabilitás): a sorrend és a
        # többi gyökér érintetlen marad
        self._roots = [uj if root == gyoker else root for root in self._roots]
        try:
            self._persist_roots()
        except OSError:
            # az index már az új útra mutat, a memóriabeli lista is — a
            # fájl kiírása bukott meg. NEM némítjuk el: enélkül a következő
            # indulás a régi helyet keresné.
            logger.exception(
                "#1542: a figyelt mappák fájlja nem íródott ki az áthelyezett "
                "gyökérrel (%s)", uj
            )
        self._restart_watcher()
        # #216: a régi úthoz tartozó leállítási jelző az új úton már nem
        # érvényes — enélkül az új gyökér első syncje azonnal leállna
        self._cancel_event(uj).clear()
        self._athelyezett_gyoker_nezete(regi, uj)
        self.statusChanged.emit()
        logger.info("#1542: a figyelt gyökér követve: %s → %s", gyoker, uj)
        return True

    def _athelyezett_gyoker_nezete(self, regi: str, uj: str) -> None:
        """A LÁTOTT mappa átvezetése az áthelyezett gyökér alatt (#1542).

        Enélkül a rács a régi, már nem létező úton maradna (üres rács), és
        a `session/lastFolder` is oda mutatna — a következő indítás megint
        a semmit nyitná meg. Csak sima mappanézetben nyúlunk hozzá: keresés
        vagy album nézetben a bal hasáb mást mutat, ott nincs mit
        átvezetni."""
        latott = self._current_folder
        if not latott or self._view_mode[0] != "folder":
            return
        latott_path = Path(latott)
        regi_path = Path(regi)
        if latott_path != regi_path and not latott_path.is_relative_to(regi_path):
            return
        self.selectFolder(str(Path(uj) / latott_path.relative_to(regi_path)))

    def _reszfa_a_lemezen(self, folder: str) -> tuple[str, ...]:
        """Az áthelyezett mappa ÚJ oldala: maga a mappa és az almappái.

        A bejárás a GUI-szálon fut, de csak könyvtárbejegyzéseket olvas
        (fájlonkénti `stat` nélkül) — és ugyanez a hívási lánc épp az imént
        MOZGATTA át a teljes fát ugyanezen a szálon
        (`fileops_controller.moveFolder` → `shutil.move`), tehát a séta ára
        ehhez képest elenyésző. Hibás/eltűnt ágon az `os.walk` csendben
        kihagy — a hiányzó mappát a következő rescan rendezi."""
        utak = [folder]
        for szulo, alkonyvtarak, _fajlok in os.walk(folder):
            utak.extend(str(Path(szulo) / nev) for nev in alkonyvtarak)
        return tuple(utak)

    def _reszfa_az_indexbol(self, folder: str) -> tuple[str, ...]:
        """Az áthelyezett mappa RÉGI oldala: amit az index még ott tud.

        ⚠️ Ha MAGÁT a figyelt gyökeret helyezték át, a takarítás KIMARAD.
        A gyökér útvonala ilyenkor a figyelt mappák közt (és a
        `WatchedFolders.txt`-ben) még a régi helyre mutat: a teljes
        könyvtárat azon az alapon üríteni, hogy a program saját
        nyilvántartása szerint ott KELL lennie, kockázatosabb, mint egy
        ideig elavult sorokat mutatni.

        #1542: ez a védelem MEGMARAD, csak a hatóköre szűkült. A gyökér
        áthelyezését azóta a `_kovesd_a_gyoker_athelyezeset` KÖVETI — ha ez
        sikerül, a régi utak már át vannak írva, tehát ez a lekérdezés
        magától üres halmazt ad. A `_find_root`-os kapu így pontosan arra
        az esetre marad, amikor a követés NEM sikerült (a régi néven ismét
        áll egy mappa, az új hely nem létezik, vagy az index átírása
        ütközött) — ott továbbra sem takarítunk. Mutációval mérve: e kapu
        nélkül a bal hasáb ilyenkor teljesen kiürül."""
        if self._find_root(folder) is not None:
            return ()
        with open_index(self._db_path) as conn:
            return folder_paths_under(conn, folder)

    # -- #1539: a FRISSEN KIÍRT kimenet célzott újraolvasása -----------------
    #
    # A hibaosztály ugyanaz, mint a #1522-nél és a #1538-nál: a fájl a
    # lemezen van, de az INDEX nem tud róla, a `selectFolder` pedig kizárólag
    # az indexből olvas — a felhasználó üres mappát lát. A #1275 lekérdezés
    # itt nem segít: az a LÁTOTT mappát nézi, a kimenet viszont épp egy
    # MÁSIKBA megy.

    def _ensure_output_resync_wired(self) -> None:
        """A belső kimenet-jelzés bekötése — SORBA ÁLLÍTOTT kapcsolattal.

        A GUI-szálon hívandó, a háttérszál indítása ELŐTT (a
        `collage_save._ensure_worker_bridge` mintája). Idempotens."""
        if getattr(self, "_output_resync_wired", False):
            return
        self._output_resync_wired = True
        self._outputWritten.connect(
            self._on_output_written, Qt.ConnectionType.QueuedConnection
        )

    def noteOutputWritten(self, path) -> None:  # noqa: N802 — QML-stílusú név
        """Bejelenti, hogy egy FRISSEN KIÍRT fájl a lemezen van (#1539).

        HÁTTÉRSZÁLBÓL IS hívható: csak jelzést bocsát ki, az érdemi munka a
        GUI-szálon fut (`_on_output_written`). A hívónak előbb a GUI-szálon
        meg kell hívnia a `_ensure_output_resync_wired()`-et."""
        if not path:
            return
        self._outputWritten.emit(str(path))

    def _on_output_written(self, path: str) -> None:
        """A kimenet-jelzés fogadója — már a GUI-szálon."""
        self.resyncOutputFolder(path)

    # SZÁNDÉKOSAN nincs `@Slot`: a hívók PYTHON-oldaliak (a vezérlő saját
    # szeletei és a `wire_dedup`), a QML soha nem hívja. Slotként a
    # `kepesseg_or.py` joggal jelezné felületről elérhetetlen képességnek —
    # ugyanaz a döntés, mint a `resyncMovedFolder`-nél (#1538).
    def resyncOutputFolder(self, path) -> None:  # noqa: N802 — QML-stílusú név
        """Egy frissen kiírt FÁJL MAPPÁJÁNAK célzott újraolvasása (#1539).

        ⚠️ A paraméter **fájlút**, nem mappa — a `.parent` itt tehát HELYES,
        szemben a #1538-cal, ahol ugyanez a lépés csapda volt. Ott egy MAPPA
        érkezett, és a `.parent` a SZÜLŐJÉT olvasta volna újra; itt a
        kollázs, a film, a másolat és az elmozgatott duplikátum mind
        konkrét fájl, aminek a mappája pontosan a megváltozott könyvtár.
        Rekurzióra sincs szükség (a #1538 másik csapdája): a művelet
        EGYETLEN mappába ír, nem részfát mozgat.

        A figyelt körön kívülre írt kimenet SZÁNDÉKOSAN kimarad (a #1522
        azonos szabálya): egy exportcél miatt nem bővítjük a felhasználó
        figyelt mappáit, és a `sync_folder`-nek amúgy is kell egy gyökér,
        ami alá a mappa tartozik.

        ⚠️ Az itteni kapu KORAI KILÉPÉS, nem a helyesség őre: ugyanezt a
        `_root_for_folder` próbát a `_on_folders_dirty` worker-ága is
        elvégzi, tehát a sor kivétele a NYILVÁNTARTÁST nem rontaná el
        (mutációval mérve: mind a tíz teszt zöld marad nélküle). Azért van
        mégis itt, mert enélkül MINDEN figyelt körön kívüli export
        fölöslegesen ütemezne egy háttérszálat és egy index-megnyitást —
        és épp az a gyakori eset (az export alapértelmezett célja a figyelt
        gyökereken kívülre mutat). Ezt az `_on_folders_dirty` szintjén
        őrizzük teszttel (`test_a_kivulre_irt_kimenet_nem_utemez_munkat`).

        Ez a `wire_fileops.refresh()` vezérlő-oldali párja. Azért van két
        helyen, mert a `wire_fileops` egy KÜLSŐ QObject (`FileOpsController`)
        jelzéseit köti be, és csak a `watchedFolders` + `resyncFolder`
        felületet használja belőlünk; a kollázs, a film és a mentés viszont
        MAGÁNAK a vezérlőnek a szeletei, azoknak nincs mit bekötni."""
        helyi = to_local_path(path) or str(path)
        mappa = str(Path(normalize_path(helyi)).parent)
        if self._root_for_folder(mappa) is None:
            return  # figyelt körön kívül — nem indexeljük
        self.resyncFolder(mappa)
