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
import stat
import threading
import time
from pathlib import Path

from PySide6.QtCore import Property, Qt, Signal, Slot

from picasapy.fileops import FolderRenameError, rename_folder
from picasapy.fileops.rename_folder import restore_folder_rename
from picasapy.index import (
    delete_faces_in_folder,
    mark_folder_excluded,
    clear_removed_folders_under,
    folder_paths_under,
    folder_scan_stamps,
    move_folder_tree,
    open_index,
    remove_folder_tree,
    remove_root,
    sync_folder,
)
from picasapy.index.dedup_folders import merge_duplicate_folders
from picasapy.index.queries import carry_pending_hidden
from picasapy.paths import normalize_path, path_key
from picasapy.scanner import (
    DirectoryChange,
    LibraryWatcher,
    is_excluded,
    read_scan_list,
    write_exclude_folders,
    write_scan_list,
    write_watched_folders,
)
from picasapy.scanner.filetypes import RAW_EXTENSIONS

from .busy_registry import get_app_busy_registry
from .filetype_preferences import (
    enabled_filetypes as enabled_filetype_groups,
    file_type_enabled,
    set_file_type_enabled,
)
from .exported_folders import (
    EXPORTED_FOLDERS_SETTINGS_KEY,
    existing_exported_folders,
)
from .folder_freshness import next_sweep_batch, stale_folders
from .folder_manager_save_controller import FolderManagerSaveMixin
from .formatting import to_local_path
from .index_writer_queue import IndexWriterQueue
from .initial_scan import (
    SKIP_INITIAL_SCAN_KEY,
    folders_for_choice,
    migration_detected,
    needs_initial_scan,
)
from .worker_thread import BackgroundWorkerMixin
from .library_controller_activity import (
    _FILETYPE_SNAPSHOT_UNSET,  # noqa: F401 — régi importútvonal újraexportja
    _LibraryActivityMixin,
)
from .library_controller_folders import _LibraryFoldersMixin
from .library_controller_sync import _LibrarySyncMixin
from .library_controller_resync import _LibraryResyncMixin

logger = logging.getLogger(__name__)


def _sqlite_write_lock_error(error: sqlite3.OperationalError) -> bool:
    """Igaz, ha az `OperationalError` oka a SQLite írási zárütközése."""
    code = getattr(error, "sqlite_errorcode", None)
    if code is not None:
        base_code = int(code) & 0xFF
        if base_code in (sqlite3.SQLITE_BUSY, sqlite3.SQLITE_LOCKED):
            return True
    message = str(error).casefold()
    return "locked" in message or "busy" in message


def _coalesce_watcher_changes(changes) -> list[str | DirectoryChange]:
    """A könyvtáresemény lefedje a köteg azonos/leszármazott fájljelzéseit.

    Könyvtár törlésekor a watchdog a benne lévő médiafájlok `deleted`
    eseményeit is küldheti. Ezeket a könyvtár-indexművelet kezeli; egy
    ugyanoda irányuló `sync_folder` már fölösleges lemezolvasást indítana.
    """
    directory_changes: list[DirectoryChange] = []
    file_folders: list[str] = []
    for change in changes:
        if not isinstance(change, DirectoryChange):
            file_folders.append(str(change))
            continue

        same_path = next(
            (
                index
                for index, previous in enumerate(directory_changes)
                if Path(previous.path) == Path(change.path)
            ),
            None,
        )
        if same_path is None:
            directory_changes.append(change)
        elif directory_changes[same_path].action != change.action:
            # Törlés és újralétrehozás egy debounce-ablakba esett. A
            # jelenlegi állapot döntsön; hiba esetén a megőrző ág nyer.
            try:
                mode = Path(change.path).stat().st_mode
            except FileNotFoundError:
                action = "deleted"
            except OSError:
                action = "created"
            else:
                action = "created" if stat.S_ISDIR(mode) else "deleted"
            directory_changes[same_path] = DirectoryChange(change.path, action)

    # A szülőkönyvtár beolvasása/törlése lefedi a benne jelzett további
    # könyvtáreseményeket is. Az egyezés Path-alapú, Windows alatt is.
    filtered_directories = [
        change
        for change in directory_changes
        if not any(
            parent.action == change.action
            and Path(parent.path) != Path(change.path)
            and Path(change.path).is_relative_to(Path(parent.path))
            for parent in directory_changes
        )
    ]
    filtered_directories.sort(key=lambda change: len(Path(change.path).parts))
    directory_paths = [Path(change.path) for change in filtered_directories]
    return filtered_directories + [
        folder
        for folder in file_folders
        if not any(
            Path(folder) == directory or Path(folder).is_relative_to(directory)
            for directory in directory_paths
        )
    ]


# #209: a worker-oldali jelzés-ritkítás minimuma (mp) — sok gyorsan kihagyott
# mappánál a queued jelzések ne árasszák el a GUI-szál eseménysorát.
_PROGRESS_EMIT_MIN_S = 0.25
# #209: a rács fokozatos frissítésének minimum-időköze (mp) — a köztes
# eredmények látszanak, de nem fut modell-újratöltés minden kötegnél.
_PROGRESS_RELOAD_MIN_S = 1.5
# Tartós SQLite-zárnál várjunk egy kört, mielőtt a mappákat újrapróbáljuk.
_LOCKED_SYNC_RETRY_MS = 5_000


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

#: #1123 — a Picasa PROJEKT-mappái, amelyeket az IDEGEN Picasa is ír.
#:
#: A tulajdonos bejelentése: „létrehoztam egy kollázst a Picasa 3-mal,
#: miközben fut a PicasaPy, és a PicasaPy alatt nem jelent meg" — másfél
#: perc után sem (mérve, 2026-09-05), CIFS-mounton.
#:
#: MIÉRT nem hozta be egyik meglévő út sem:
#:
#: 1. **inotify**: CIFS/SMB-mounton a távoli gép írásáról egyáltalán nem
#:    érkezik esemény (`docs/benchmarks/rpi5-sqlite-inotify.md`, mérve).
#: 2. **a tízmásodperces pecsét-kör** (#1275/#1435): a KIVÁLASZTOTT mappát
#:    és a rács feedjében látszó mappákat nézi. A feed a BETÖLTÖTT
#:    fotó-rekordokból épül (`_update_feed_groups`), tehát egy fotó nélküli
#:    (frissen létrehozott) Kollázsok mappa oda nem is kerülhet be; ami
#:    pedig bekerül, az a körbeforgó kurzor miatt csak `ceil(N/8)`
#:    körönként jön sorra — 500 mappánál tíz percenként.
#: 3. **az ötperces teljes rescan**: ez hozta be — a tulajdonos szava
#:    szerint „használhatatlanul lassú".
#:
#: A #1539 a MI kimenetünkre már megoldotta ezt (`noteOutputWritten`
#: bejelentővel); idegen program írására bejelentő nem létezik, ott csak
#: lekérdezés van. Ezért ez a KORLÁTOS, PRIORITÁSOS készlet: a kollázs- és
#: film-célmappa MINDEN körben sorra kerül, a feedtől és a kurzortól
#: függetlenül. Költsége mappánként két-három művelet, tehát a pecsét-kör
#: kerete legfeljebb 24-ről 30 műveletre nő (≈3 művelet/mp) — a NAS mért
#: 200/mp korlátja alatt marad.


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


class LibraryMixin(
    _LibraryActivityMixin,
    _LibraryFoldersMixin,
    _LibrarySyncMixin,
    _LibraryResyncMixin,
    FolderManagerSaveMixin,
    BackgroundWorkerMixin,
):
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
    #: #2966: a futó háttérmunka MEGSZAKÍTHATÓSÁGA változott — a
    #: jobb-felső sarki jelző megszakítás-gombjának láthatósága erre köt.
    activityCancellableChanged = Signal()
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

    @Property(bool, notify=activityCancellableChanged)
    def activityCancellable(self):  # noqa: N802 — QML-property-stílus
        """Leállítható-e a futó háttérmunka (#2966).

        A jelző maga az `isWorking`-re látszik; a megszakítás GOMBJA erre.
        A kettő szándékosan külön: a bélyegkép-betöltés például fut, de
        nincs értelmes leállítója — ilyenkor a jelző pörög, gomb nélkül,
        ahogy az eredeti szerkesztő-panel példánya is gomb nélküli
        (`editpanelactivity`, #3112)."""
        return get_app_busy_registry().cancellable


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


    # -- leállítási jelzők (#216) --------------------------------------------


    # -- életciklus ----------------------------------------------------------


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


    # -- Arcfelismerés-kizárás (#449, NEGYEDIK, a Scan Always/Once/Remove
    # hármastól FÜGGETLEN kapcsoló) -------------------------------------


    # -- háttér-szinkron -----------------------------------------------------


    #: #1977: a `@Slot()` NÉLKÜL a QML `controller.rescan()` hívása
    #: `TypeError: … is not a function`-nel elszáll — a „Frissítés"
    #: menüpont némán nem csinál semmit. A dekorátor a #150-es
    #: mixin-felbontáskor még megvolt (`8de1358e`), azóta kiesett.


    # SZÁNDÉKOSAN nincs `@Slot`: a hívó a `wire_fileops` PYTHON-oldali
    # kötése (`photoDeleted` → itt), a QML soha nem hívja.


    # SZÁNDÉKOSAN nincs `@Slot`: a hívó a `wire_fileops` PYTHON-oldali
    # kötése (`folderMoved` → itt), a QML soha nem hívja. Slotként a
    # `kepesseg_or.py` joggal jelezné felületről elérhetetlen képességnek.


    # SZÁNDÉKOSAN nincs `@Slot` — ugyanazért, amiért a `resyncMovedFolder`-en
    # sincs: a hívó a `wire_fileops` PYTHON-oldali kötése (`folderDeleted` →
    # itt), a QML soha nem hívja. Slotként a `kepesseg_or.py` joggal jelezné
    # felületről elérhetetlen képességnek — a CI el is bukott rajta.


    # -- #1539: a FRISSEN KIÍRT kimenet célzott újraolvasása -----------------
    #
    # A hibaosztály ugyanaz, mint a #1522-nél és a #1538-nál: a fájl a
    # lemezen van, de az INDEX nem tud róla, a `selectFolder` pedig kizárólag
    # az indexből olvas — a felhasználó üres mappát lát. A #1275 lekérdezés
    # itt nem segít: az a LÁTOTT mappát nézi, a kimenet viszont épp egy
    # MÁSIKBA megy.


    # SZÁNDÉKOSAN nincs `@Slot`: a hívók PYTHON-oldaliak (a vezérlő saját
    # szeletei és a `wire_dedup`), a QML soha nem hívja. Slotként a
    # `kepesseg_or.py` joggal jelezné felületről elérhetetlen képességnek —
    # ugyanaz a döntés, mint a `resyncMovedFolder`-nél (#1538).


    # SZÁNDÉKOSAN nincs `@Slot`: a hívó PYTHON-oldali (`_on_output_written`),
    # a QML soha nem hívja — ugyanaz a döntés, mint a `resyncOutputFolder`-nél.


__all__ = (
    'BackgroundWorkerMixin',
    'DirectoryChange',
    'EXPORTED_FOLDERS_SETTINGS_KEY',
    'FOLDER_POLL_MS',
    'FolderManagerSaveMixin',
    'FolderRenameError',
    'IndexWriterQueue',
    'LibraryMixin',
    'LibraryWatcher',
    'Path',
    'Property',
    'Qt',
    'RAW_EXTENSIONS',
    'SKIP_INITIAL_SCAN_KEY',
    'SWEEP_FOLDERS_PER_TICK',
    'Signal',
    'Slot',
    'annotations',
    'carry_pending_hidden',
    'clear_removed_folders_under',
    'delete_faces_in_folder',
    'enabled_filetype_groups',
    'existing_exported_folders',
    'file_type_enabled',
    'folder_paths_under',
    'folder_scan_stamps',
    'folders_for_choice',
    'get_app_busy_registry',
    'is_excluded',
    'logger',
    'logging',
    'mark_folder_excluded',
    'merge_duplicate_folders',
    'migration_detected',
    'move_folder_tree',
    'needs_initial_scan',
    'next_sweep_batch',
    'normalize_path',
    'open_index',
    'os',
    'path_key',
    'read_scan_list',
    'remove_folder_tree',
    'remove_root',
    'rename_folder',
    'restore_folder_rename',
    'set_file_type_enabled',
    'sqlite3',
    'stale_folders',
    'stat',
    'sync_folder',
    'threading',
    'time',
    'to_local_path',
    'write_exclude_folders',
    'write_scan_list',
    'write_watched_folders',
)
