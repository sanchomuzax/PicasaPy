"""A könyvtárvezérlő frissességi söprésének felelősségei (#6257)."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Slot
from picasapy.index import folder_scan_stamps, open_index

from .folder_freshness import next_sweep_batch, stale_folders
from .library_controller_sync import _legacy


class _LibrarySyncSweepMixin:
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
