"""A könyvtár-vezérlő sync felelősségei (#6137)."""

from __future__ import annotations

import importlib
import sys

import sqlite3
import stat
from pathlib import Path

from PySide6.QtCore import Slot
from picasapy.index import folder_scan_stamps, open_index, remove_folder_tree
from picasapy.scanner import DirectoryChange

from .busy_registry import get_app_busy_registry
from .folder_freshness import next_sweep_batch, stale_folders


def _legacy():
    """A régi modulból olvassa az örökölt, tesztek által foltozható neveket."""
    return sys.modules.get(
        f"{__package__}.library_controller"
    ) or importlib.import_module(".library_controller", __package__)


class LibrarySyncMixin:
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
        # #1123: a projekt-célmappák a feedtől és a körbeforgó kurzortól
        # FÜGGETLENÜL, minden körben sorra kerülnek — az idegen Picasa oda ír.
        batch = tuple(
            _legacy()._dedupe_paths(
                (*self._sweep_candidates(mappa), *self._projekt_kimeneti_mappak())
            )
        )
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
                _legacy().logger.exception("#1435: a frissesség-sweep elhasalt")
            finally:
                self._sweep_running = False
                try:
                    # a jelzés a watchdog-éval azonos úton megy a GUI-szálra
                    # (queued `watcherDirty`) — onnan a jól bejáratott
                    # `_on_folders_dirty` végzi a koaleszálást és a szinkront
                    self.watcherDirty.emit(_legacy()._dedupe_paths((mappa, *elavult)))
                except RuntimeError:
                    # leállás közben a C++ oldal már eltűnhetett
                    _legacy().logger.debug("#1435: a sweep jelzése elmaradt", exc_info=True)

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

    def _projekt_kimeneti_mappak(self) -> tuple[str, ...]:
        """A Picasa projekt-célmappái, amelyeket körönként megnézünk (#1123).

        Gyorstárazott: a feloldás fájlrendszert ér (a célmappa neve
        honosított, ezért `letezo_vagy_honos_mappa` megnézi, melyik alak
        létezik — ld. `collage_output.output_dir`), ezt pedig nem akarjuk
        tíz másodpercenként megfizetni. A gyorstárat a `rescan()` üríti,
        tehát legkésőbb öt perc múlva átveszi a megváltozott beállítást
        vagy az újonnan létrejött mappát.

        A szűrés SZÁNDÉKOSAN itt van, nem a pecsét-fázisban: a
        `stale_folders` a tárolt pecsét nélküli mappát elavultnak
        minősíti, a `_on_folders_dirty` pedig a gyökéren kívülit kihagyja
        — a kettő együtt azt adná, hogy minden körben elindul egy
        szinkron-szál, ami semmit nem tesz."""
        gyorstar = getattr(self, "_projekt_kimenet_cache", None)
        if gyorstar is None:
            gyorstar = self._projekt_kimenet_felmeres()
            self._projekt_kimenet_cache = gyorstar
        return gyorstar

    def _projekt_kimenet_felmeres(self) -> tuple[str, ...]:
        """A célmappák feloldása és szűrése (létezik · figyelt gyökér alatt
        · nincs kizárva) — a `_projekt_kimeneti_mappak` gyorstárának
        tartalma.

        Hiba esetén ÜRES eredmény: ez kényelmi gyorsítás, nem törhet meg
        tőle a körönkénti alapfrissítés (a #1435 kivétel-hálójának
        mintája)."""
        from . import collage_output, collage_prefs, movie_output

        try:
            beallitasok = self._get_settings()
            jeloltek = (
                collage_output.output_dir(
                    beallitasok.value(collage_prefs.OUTPUT_DIR_KEY)
                ),
                movie_output.output_dir(beallitasok.value(movie_output.OUTPUT_DIR_KEY)),
            )
        except Exception:
            _legacy().logger.debug("#1123: a projekt-célmappák feloldása nem sikerült",
                         exc_info=True)
            return ()
        talalt: list[str] = []
        for jelolt in jeloltek:
            ut = str(jelolt)
            try:
                if not jelolt.is_dir():
                    continue  # még létre sem hozták — nincs mit megnézni
            except OSError:
                continue  # elérhetetlen (lecsatolt mount)
            gyoker = self._root_for_folder(ut)
            if gyoker is None:
                continue  # a figyelt gyökéren kívül: a szinkron kihagyná
            if self._folder_manager_path_excluded(ut, gyoker):
                continue  # a Mappakezelő kizárta — a szinkron kihagyná
            talalt.append(ut)
        return tuple(talalt)

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
            candidates, cursor, _legacy().SWEEP_FOLDERS_PER_TICK
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
            _legacy().logger.debug(
                "#1435: a frissesség-ellenőrzés nem sikerült", exc_info=True
            )
            return ()

    #: #1977: a `@Slot()` NÉLKÜL a QML `controller.rescan()` hívása
    #: `TypeError: … is not a function`-nel elszáll — a „Frissítés"
    #: menüpont némán nem csinál semmit. A dekorátor a #150-es
    #: mixin-felbontáskor még megvolt (`8de1358e`), azóta kiesett.
    @Slot()
    def rescan(self) -> None:
        """Teljes újrapásztázás — az ötperces időzítő és a „Frissítés" menü.

        #1456: a `_dirty_running`-ot IS nézi. Enélkül a célzott szinkron
        (`_on_folders_dirty`, #1440) mellé indult egy második index-író, és
        a felhasználó `sqlite3.OperationalError` → `syncFailed` hibát
        látott — ugyanaz a hibaosztály, mint a #1440-ben, csak másik
        belépési ponton.

        **Kihagy, nem várólistáz.** A #1440 `_pending_dirty` várólistája ott
        azért kell, mert egy KONKRÉT mappa jelzése veszne el; itt nincs
        ilyen: a rescan az egészet nézi, az időzítő öt perc múlva újra
        próbál, és a futó szinkron végén amúgy is frissül a nézet.
        """
        if self._sync_running or self._dirty_running:
            return  # egy író elég; a futó szinkron végén úgyis frissülünk
        self._sync_running = True
        self._sync_worker_filetype_snapshot = getattr(
            self, "_filetype_scan_snapshot", None
        )
        # #438/#505: nyilvántartott daemon-szál (BackgroundWorkerMixin, #430) —
        # a busy-bejelentkezés is ITT, a mixinben történik (ld. worker_thread.py)
        # #1123: a projekt-célmappák gyorstára itt ürül — így a beállítás
        # megváltozása vagy egy újonnan létrejött célmappa legkésőbb öt
        # perc múlva bekerül a tízmásodperces körbe.
        self._projekt_kimenet_cache = None
        self._start_background(
            self._sync_worker,
            name="picasapy-sync-rescan",
            cancel=self.cancelScan,
        )

    def _sync_worker(
        self, enabled_filetypes=_legacy()._FILETYPE_SNAPSHOT_UNSET
    ) -> None:
        """Háttér-szinkron. Egy rossz gyökér (pl. elavult Windows-útvonal a
        WatchedFolders-ből) nem nyelhet el mindent némán: hibánként jelzünk,
        a többi gyökér feldolgozása folytatódik, és a vége mindig
        syncFinished."""
        if enabled_filetypes is _legacy()._FILETYPE_SNAPSHOT_UNSET:
            enabled_filetypes = getattr(
                self,
                "_sync_worker_filetype_snapshot",
                getattr(self, "_filetype_scan_snapshot", None),
            )
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
                        self._sync_folder_manager_tree(
                            conn,
                            root,
                            progress=progress,
                            enabled_filetypes=enabled_filetypes,
                        )
                    except (OSError, RuntimeError, sqlite3.OperationalError) as error:
                        errors.append(f"{root}: {error}")
                # #1601: a hasáb ini-alapú gyűjteményei MÉG ITT, a
                # háttérszálon állnak elő — a `syncFinished` utáni
                # `_reload()` így csak átveszi őket, és a felület szála
                # egyetlen `.picasa.ini`-t sem olvas. A söprés a szinkron
                # UTÁN fut, hogy a frissen felvett mappák is benne legyenek.
                self._precompute_side_pane(conn)
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

    @Slot(int)
    def resyncFolderOfRow(self, row: int) -> None:
        """A sorhoz tartozó mappa resyncje — a néző bezárásakor hívjuk:
        a feedben (#64) a néző át is léphetett másik mappába, ezért nem a
        kiválasztott, hanem az épp nézett kép mappáját frissítjük."""
        photos = self._photos.photos
        if 0 <= row < len(photos):
            self.resyncFolder(photos[row].folder_path)

    # SZÁNDÉKOSAN nincs `@Slot`: a hívó a `wire_fileops` PYTHON-oldali
    # kötése (`photoDeleted` → itt), a QML soha nem hívja.
    def removeDeletedRow(self, path: str) -> bool:  # noqa: N802
        """A törölt kép sorának AZONNALI kivétele a rácsból (#1227).

        Eddig a sor eltűnése a célzott újraszinkronon múlt
        (`photoDeleted` → `resyncFolder` → háttérszál → `syncFinished`),
        tehát csak a szinkron VÉGÉN tűnt el — nagy könyvtárnál másodpercek
        vagy percek múlva. Az eredetiben a rács maga végzi a törlést
        (`CThumbUI::DeleteProgress`, `0x00894fb4`).

        A resync ezután is elindul: az utólag EGYEZTET (más program is
        nyúlhatott a mappához), ez a lépés csak előrehozza a látható
        hatást.

        ⚠️ A mappa-csoportokat (`feedGroups`) is frissíteni kell, különben
        a rács csoporthatárai elcsúsznak — a lasszó, a Shift-tartomány és
        a nyilas léptetés mind ezekre épül (#1219). Szerencsés szerkezet:
        a `build_feed_groups` a REKORDOKBÓL számol, tehát a sor kivétele
        után a `start`/`count` maguktól helyes.
        """
        if not self._photos.remove_by_path(path):
            return False
        self._update_feed_groups(self._photos.photos)
        self._update_status(self._photos.photos)
        return True

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
        # #1458: ez a felhasználó KATTINTÁSA (Frissítés menüpont, néző
        # bezárása) — futó író mellett a kérés várólistára kerül, és a
        # visszajelzés nélkül úgy néz ki, mintha semmi nem történt volna.
        self._on_folders_dirty([folder_path], felhasznaloi=True)

    def set_edit_controllers(self, *edit_controllers) -> None:
        """Az aktív képek útvonalát adó szerkesztőrekeszek bekötése (#4482)."""
        self._edit_controllers = tuple(edit_controllers)
