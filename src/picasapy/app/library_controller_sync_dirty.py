"""A könyvtárvezérlő célzott szinkronjának felelősségei (#6257)."""

from __future__ import annotations

import sqlite3
import stat
from pathlib import Path

from PySide6.QtCore import Slot
from picasapy.index import open_index, remove_folder_tree
from picasapy.scanner import DirectoryChange

from .busy_registry import get_app_busy_registry
from .library_controller_sync import _legacy


class _LibrarySyncDirtyMixin:
    @Slot(list)
    def _on_folders_dirty(self, folders, *, felhasznaloi: bool = False) -> None:
        """A watcher által jelzett mappák célzott frissítése (#143, #5177).

        A fájlváltozás mappa-pontos `sync_folder`-t kap. Új könyvtárnál csak
        az új út részfája kerül a rekurzív `sync_tree`-be; törlésnél az index
        törlő API-ja távolítja el az út alatti sorokat, lemezbejárás nélkül.
        A teljes gyökér-szinkron továbbra is a periodikus/kézi rescan feladata.

        ⚠️ #1440: ennek az ágnak SAJÁT futásjelzője van (`_dirty_running`).
        A `_sync_running` a `rescan()`-é, a `_sweep_running` (#1435) pedig
        a pecsét-köröké — egyik sem fedte a MÁSIK célzott szinkront. Egy
        hosszú, hálózati megosztáson futó dirty-worker mellé így egy
        következő jelzés (a tíz másodperccel későbbi lekérdezési kör vagy
        egy watcher-esemény) simán indított egy másodikat: két egyidejű
        index-íróból `sqlite3.OperationalError`, abból pedig a
        felhasználónak szóló `syncFailed` lett. A #1435 óta a worker akár
        kilenc mappát is visz, tehát sokkal tovább él — a kitettség nőtt."""
        paths = list(folders)
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
            # #1458: a FELHASZNÁLÓ kérése látszódjon is. A kérés nem vész el
            # (a halmaz megőrzi), de a felhasználó ebből semmit nem lát:
            # rákattint a „Frissítés"-re, és lassú hálózati köteten fél
            # percig nem történik semmi látható. A `_start_background`
            # bejelentkezne a foglaltság-nyilvántartóba, csakhogy ezen az
            # ágon nem indul szál — ezért itt jelentkezünk be, és a
            # `_flush_pending_dirty` zárja a bejegyzést.
            #
            # ⚠️ Az AUTOMATIKUS (figyelőből jövő) jelzés SZÁNDÉKOSAN nem
            # jelentkezik be: ott nincs kattintás, amire válaszolni kellene,
            # és a folyamatosan pörgő sáv zavaró lenne. A watcher a
            # `watcherDirty` kapcsolaton át hív, argumentum nélkül — tehát
            # az alapértelmezés a helyes viselkedése.
            if felhasznaloi:
                get_app_busy_registry().begin()
                self._pending_busy += 1
            return

        enabled_filetypes = getattr(self, "_filetype_scan_snapshot", None)

        def worker():
            errors = []
            locked_folders = []
            synced_folders = []
            try:
                with open_index(self._db_path) as conn:
                    for folder in _legacy()._coalesce_watcher_changes(paths):
                        change = folder if isinstance(folder, DirectoryChange) else None
                        folder_path = change.path if change is not None else str(folder)
                        root = self._root_for_folder(folder_path)
                        if root is None:
                            continue  # már nem figyelt gyökér alatt — kihagyva
                        if (
                            change is None or change.action != "deleted"
                        ) and self._folder_manager_path_excluded(folder_path, root):
                            continue
                        try:
                            sync_options = {}
                            if enabled_filetypes is not None:
                                sync_options["enabled_filetypes"] = enabled_filetypes
                            if change is not None and change.action == "deleted":
                                remove_folder_tree(conn, folder_path)
                            elif change is not None:
                                try:
                                    folder_mode = Path(folder_path).stat().st_mode
                                except FileNotFoundError:
                                    remove_folder_tree(conn, folder_path)
                                except OSError:
                                    # Elérhetetlen cél esetén a teljes rescan
                                    # dönt a mappa sorsáról.
                                    continue
                                else:
                                    if stat.S_ISDIR(folder_mode):
                                        self._sync_folder_manager_tree(
                                            conn,
                                            root,
                                            progress=self._make_progress_emitter(
                                                should_stop=self._make_should_stop(root)
                                            ),
                                            enabled_filetypes=enabled_filetypes,
                                            scan_root=folder_path,
                                        )
                                    else:
                                        remove_folder_tree(conn, folder_path)
                            else:
                                should_stop = self._make_should_stop(root)
                                # #216: eltávolított gyökér mappája már ne íródjon
                                _legacy().sync_folder(
                                    conn,
                                    root,
                                    folder_path,
                                    exclude=self._folder_manager_excludes_for_root(root),
                                    should_stop=should_stop,
                                    **sync_options,
                                )
                            synced_folders.append(folder_path)
                        except (OSError, RuntimeError):
                            pass  # eltűnt mappa — a periodikus rescan rendezi
                        except sqlite3.OperationalError as error:
                            if _legacy()._sqlite_write_lock_error(error):
                                # A másik író busy_timeout-on túl is fogta a
                                # DB-t. Ezt naplózzuk, de a felhasználónak
                                # kötegenként egy összesített jelzés megy; a
                                # mappák a syncFinished utáni körre kerülnek.
                                _legacy().logger.warning(
                                    "mappaszinkron zárütközés, később újrapróbáljuk: %s: %s",
                                    folder_path,
                                    error,
                                )
                                locked_folders.append(folder_path)
                                if conn.in_transaction:
                                    conn.rollback()
                            else:
                                errors.append(f"{folder_path}: {error}")
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
                    reported = getattr(self, "_reported_locked_sync_folders", set())
                    reported.difference_update(synced_folders)
                    uj_zarasok = set(locked_folders).difference(reported)
                    if locked_folders:
                        self._pending_dirty.update(locked_folders)
                        self._locked_dirty_retry_pending = True
                        reported.update(locked_folders)
                        self._reported_locked_sync_folders = reported
                    messages = []
                    if uj_zarasok:
                        darab = len(uj_zarasok)
                        messages.append(
                            f"{darab} mappa szinkronizálása később folytatódik."
                        )
                    if errors:
                        messages.append("; ".join(errors))
                    if messages:
                        self.syncFailed.emit("\n".join(messages))
                    self.syncFinished.emit()
                except RuntimeError:
                    # ugyanaz a védelem, mint a sweep-workerében (#1435):
                    # leállás közben a C++ oldal már eltűnhetett
                    _legacy().logger.debug(
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
            self._start_background(
                worker, name="picasapy-sync-dirty", cancel=self.cancelScan
            )
        except BaseException:
            # ⚠️ #550/#1435 mintája: a `start()` elbukhat (`RuntimeError:
            # can't start new thread`), és akkor a `worker` — vele a
            # `finally` ága — SOSEM fut le. Beragadt jelzővel innentől
            # MINDEN célzott frissítés a várólistára menne, és onnan soha
            # senki nem hozná be: a rács a munkamenet végéig NÉMÁN sosem
            # frissülne magától. Egyetlen tranziens hiba örökre elrontaná.
            self._dirty_running = False
            raise


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
        if getattr(self, "_locked_dirty_retry_pending", False):
            # A syncFinished a worker befejezésekor azonnal érkezik. A zárba
            # futott mappákat ne indítsuk újra ugyanabban a hibás állapotban:
            # egyetlen, rövid késleltetett kör után próbáljuk meg ismét.
            from PySide6.QtCore import QTimer

            timer = getattr(self, "_locked_dirty_retry_timer", None)
            if timer is None:
                timer = QTimer(self)
                timer.setSingleShot(True)
                timer.timeout.connect(self._retry_locked_dirty_folders)
                self._locked_dirty_retry_timer = timer
            if not timer.isActive():
                timer.start(_legacy()._LOCKED_SYNC_RETRY_MS)
            return
        folders = sorted(self._pending_dirty, key=str)
        self._pending_dirty = set()
        # #1458: a várakozás közben nyitott foglaltság-bejegyzések záródnak.
        # A `_on_folders_dirty` alább ÚJ bejegyzést nyithat (ha megint nem
        # tud indulni), ezért a lezárás ELŐBB történik — különben a két
        # bejegyzés egymásra torlódna, és a sáv sosem állna meg.
        varakozo, self._pending_busy = self._pending_busy, 0
        for _ in range(varakozo):
            get_app_busy_registry().end()
        try:
            self._on_folders_dirty(folders)
        except BaseException:
            self._pending_dirty.update(folders)
            raise


    @Slot()
    def _retry_locked_dirty_folders(self) -> None:
        """A rövid várakozás után újra sorra veszi a zár miatt félretett mappákat."""
        self._locked_dirty_retry_pending = False
        self._flush_pending_dirty()
