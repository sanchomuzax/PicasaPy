"""A könyvtár-vezérlő folders felelősségei (#6137)."""

from __future__ import annotations

import importlib
import sys

import sqlite3
from pathlib import Path

from PySide6.QtCore import Slot
from picasapy.index import (
    clear_removed_folders_under,
    delete_faces_in_folder,
    mark_folder_excluded,
    open_index,
    remove_root,
)
from picasapy.paths import normalize_path, path_key
from picasapy.scanner import (
    LibraryWatcher,
    is_excluded,
    read_scan_list,
    write_exclude_folders,
    write_watched_folders,
)
from picasapy.scanner.filetypes import RAW_EXTENSIONS

from .filetype_preferences import (
    enabled_filetypes as enabled_filetype_groups,
    file_type_enabled,
    set_file_type_enabled,
)
from .formatting import to_local_path
from .index_writer_queue import IndexWriterQueue
from .initial_scan import (
    SKIP_INITIAL_SCAN_KEY,
    folders_for_choice,
    migration_detected,
)
from .library_controller_activity import _FILETYPE_SNAPSHOT_UNSET


def _legacy():
    """A régi modulból olvassa az örökölt, tesztek által foltozható neveket."""
    return sys.modules.get(
        f"{__package__}.library_controller"
    ) or importlib.import_module(".library_controller", __package__)


class _LibraryFoldersMixin:
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
            _legacy().write_scan_list(
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

    @Slot(str, result=bool)
    def fileTypeEnabled(self, group: str) -> bool:  # noqa: N802 — QML-slot
        """A Beállítások ▸ Fájltípusok fül kiválasztott állapota."""
        return file_type_enabled(self._get_settings(), group)

    @Slot(str, bool)
    def setFileTypeEnabled(self, group: str, enabled: bool) -> None:  # noqa: N802
        """Ment egy formátumkapcsolót, és frissíti a következő scan pillanatképét."""
        settings = self._get_settings()
        set_file_type_enabled(settings, group, enabled)
        self._filetype_scan_snapshot = enabled_filetype_groups(settings)

    @Slot(result=list)
    def supportedRawExtensions(self) -> list[str]:  # noqa: N802 — QML-slot
        """A Fájltípusok fül által is használt RAW-kiterjesztések."""
        return sorted(RAW_EXTENSIONS)

    def _sync_folder_manager_tree(
        self,
        conn,
        root: str,
        progress=None,
        enabled_filetypes=_FILETYPE_SNAPSHOT_UNSET,
        *,
        scan_root: str | None = None,
    ) -> None:
        target = root if scan_root is None else scan_root
        excludes = self._folder_manager_excludes_for_root(root)
        if enabled_filetypes is _legacy()._FILETYPE_SNAPSHOT_UNSET:
            enabled_filetypes = getattr(self, "_filetype_scan_snapshot", None)
        if not excludes:
            kwargs = {"progress": progress}
            if enabled_filetypes is not None:
                kwargs["enabled_filetypes"] = enabled_filetypes
            self._sync_tree(conn, target, **kwargs)
            return
        kwargs = {"exclude": excludes}
        if progress is not None:
            kwargs["progress"] = progress
        if enabled_filetypes is not None:
            kwargs["enabled_filetypes"] = enabled_filetypes
        from . import controller as controller_module

        controller_module.sync_tree(conn, target, **kwargs)

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

    @property
    def _index_iro_sor(self) -> IndexWriterQueue:
        """A KÖZVETLEN FELHASZNÁLÓI index-írások sora (#2389).

        Lusta: a legtöbb munkamenetben egyetlen mappát sem vesznek fel, és
        akkor szál sem indul. A `_start_background` NEM közvetlenül megy át,
        hanem lambdán keresztül — a tesztek a vezérlő attribútumát cserélik
        ki (`monkeypatch.setattr(controller, "_start_background", …)`), és a
        korai kötés ezt megkerülné.
        """
        sor = getattr(self, "_iro_sor", None)
        if sor is None:
            sor = IndexWriterQueue(
                lambda munka, *, name: self._start_background(munka, name=name),
                is_busy=self._fut_mas_index_iro,
            )
            self._iro_sor = sor
        return sor

    def _fut_mas_index_iro(self) -> bool:
        """Fut-e NEM a soron indult index-író (a másik három belépési pont)."""
        return bool(
            getattr(self, "_sync_running", False)
            or getattr(self, "_dirty_running", False)
            or getattr(self, "_sweep_running", False)
        )

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
        enabled_filetypes = getattr(self, "_filetype_scan_snapshot", None)

        def worker():
            try:
                with open_index(self._db_path) as conn:
                    self._sync_folder_manager_tree(
                        conn,
                        path,
                        progress=progress,
                        enabled_filetypes=enabled_filetypes,
                    )
            finally:
                self.syncFinished.emit()

        # #438/#505: nyilvántartott daemon-szál (BackgroundWorkerMixin, #430) —
        # a busy-bejelentkezés is ITT, a mixinben történik (ld. worker_thread.py)
        # #2389: SOROSÍTVA, nem kihagyva. Futó író mellett a munka
        # várólistára kerül és a sorára kerülve lefut — a mappa tehát
        # biztosan bekerül. A kék sáv a beadástól a sor kiürüléséig pörög
        # (a `_start_background` bejelentkezik a busy-registrybe), így a
        # késleltetés sem néma.
        self._index_iro_sor.submit(worker, name="picasapy-sync-addfolder")

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
        enabled_filetypes = getattr(self, "_filetype_scan_snapshot", None)

        def worker():
            try:
                with open_index(self._db_path) as conn:
                    self._sync_folder_manager_tree(
                        conn,
                        path,
                        progress=progress,
                        enabled_filetypes=enabled_filetypes,
                    )
            finally:
                self.syncFinished.emit()

        # #438/#505: nyilvántartott daemon-szál (BackgroundWorkerMixin, #430) —
        # a busy-bejelentkezés is ITT, a mixinben történik (ld. worker_thread.py)
        # #2389: SOROSÍTVA, nem kihagyva. Futó író mellett a munka
        # várólistára kerül és a sorára kerülve lefut — a mappa tehát
        # biztosan bekerül. A kék sáv a beadástól a sor kiürüléséig pörög
        # (a `_start_background` bejelentkezik a busy-registrybe), így a
        # késleltetés sem néma.
        self._index_iro_sor.submit(worker, name="picasapy-sync-scanonce")

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

        A `FaceScanController` ezt minden automatikus háttérdetektálás
        előtt ellenőrzi. A kizárás a megadott mappára és az őseire is
        érvényes, a lista a Picasa-kompatibilis `FRExcludeFolders.txt`-ből
        érkezik."""
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

        A felhasználó felé megjelenő megerősítő kérdés (eredeti
        Picasa-szöveg) a `FolderManagerDialog.qml`-ben él, ezt a metódust
        csak a megerősítés UTÁN hívja a QML.

        **Kikapcsoláskor (#2519) a mappa ÉS az alfái fotói jelölést kapnak**
        (`face_scan.ok = 'kizarva'`), a saját, származtatott arc-találataink
        pedig törlődnek. A jelölés az eredeti `facerect = 1`-ének
        megfelelője: a Picasában a téglalap írója csak nulla értékre ír
        (`0x00480de7`), tehát a jelző megvédi a képet az
        újra-detektálástól. Nálunk ugyanígy: a jelölést a **visszaengedés
        sem** oldja fel — enélkül a következő szkennelés kérdés nélkül
        újra végigfutna a képeken.

        ⛔ A `.picasa.ini` `faces=` / `[Contacts2]` sorait NEM töröljük,
        pedig az eredeti megerősítő kérdés a névcímkékről is szól. Az a
        felhasználó SAJÁT, a Picasában felvett adata („a Picasa döntései
        szentek"), és egy visszavonhatatlan törlés nem fér bele egy
        kapcsolóba. A származtatott (`face` tábla) találatok viszont
        bármikor újraszámolhatók, azokat töröljük."""
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
        if not enabled:
            self._jeloljuk_kizartnak(path)
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

    def _jeloljuk_kizartnak(self, path: str) -> None:
        """A kizárt mappa (és alfái) fotóinak megjelölése + a saját
        találataink törlése (#2519, ld. `setFaceDetectionEnabled`).

        Index-hiba nem akaszthatja meg a kapcsolót: a kizárási szándék a
        `FRExcludeFolders.txt`-ben akkor is rögzül."""
        try:
            with open_index(self._db_path) as conn:
                delete_faces_in_folder(conn, path)
                mark_folder_excluded(conn, path)
                conn.commit()
        except sqlite3.Error:
            _legacy().logger.exception(
                "az arcfelismerés-kizárás jelölése nem sikerült: %s", path
            )

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
