"""Arcfelismerési keresés, állapotkövetés és detektor-worker."""

from __future__ import annotations

import sqlite3
import time
from collections.abc import Callable, Iterator
from contextlib import closing, contextmanager, nullcontext

from .busy_activity import munka_neve
from .busy_registry import get_app_busy_registry
from .face_scan_controller_signals import FaceScanControllerSignalsMixin as _Signals
from .hatter_prioritas import arckeres_szal_elokeszitese, arckeres_szal_lezarasa
from .face_scan_controller_shared import (
    Path,
    PhotoRecord,
    Property,
    Slot,
    VIDEO_EXTENSIONS,
    _DETECT_MAX_DIMENSION,
    _log,
    _mark_previously_ignored,
    _path_key,
    _remember_decoded_image,
    album_photos,
    all_photos,
    dekodolj_forrast,
    face_scan_done,  # noqa: F401 — legacy module namespace
    ini_faces_of,
    mark_face_scan,
    open_index,
    photos_in_folder,
    replace_faces,
    rescale_face_detection,
    scale_down,
    threading,
)

_AUTOMATIC_SCAN_UNPAUSED_LIMIT = 20


class FaceScanControllerScanMixin:
    """Arcfelismerési keresés, állapotkövetés és detektor-worker."""

    _SCAN_COMMIT_BATCH_SIZE = 32


    @staticmethod
    def _read_face_scan_states(conn) -> dict[int, tuple[int, int, str]]:
        """Egy lekérdezésből adja vissza a már vizsgált fotók állapotát."""
        return {
            int(row[0]): (int(row[1]), int(row[2]), str(row[3]))
            for row in conn.execute(
                "SELECT photo_id, mtime_ns, size, ok FROM face_scan"
            )
        }


    @staticmethod
    def _face_scan_is_done(states, photo: PhotoRecord) -> bool:
        state = states.get(photo.id)
        if state is None:
            return False
        mtime_ns, size, ok = state
        return ok == "kizarva" or (
            mtime_ns == int(photo.mtime_ns) and size == int(photo.size)
        )


    @staticmethod
    def _ini_signature(folder: Path) -> tuple[int, int] | None:
        try:
            stat = (folder / ".picasa.ini").stat()
        except OSError:
            return None
        return int(stat.st_mtime_ns), int(stat.st_size)


    def _changed_ini_directories(self, photos):
        """Egy `.picasa.ini`-stat mappánként; csak változáskor kell #3670-et futtatni."""
        signatures: dict[str, tuple[int, int] | None] = {}
        changed: set[str] = set()
        for photo in photos:
            folder = Path(photo.folder_path)
            key = _path_key(folder)
            if key in signatures:
                continue
            signature = self._ini_signature(folder)
            signatures[key] = signature
            if key not in self._face_ini_signatures or (
                self._face_ini_signatures[key] != signature
            ):
                changed.add(key)
        return changed, signatures


    @Property(int, notify=_Signals.scanPercentChanged)
    def scanPercent(self) -> int:  # noqa: N802 — QML-property-stílus
        """A futó arc-beolvasás haladása (0–100), vagy −1, ha nem fut.

        A bal hasáb „Scanning for faces…" sora ezt köti (#449) — modális
        ablak SEHOL, a munka a háttérben marad."""
        return self._scan_percent


    def _set_scan_percent(self, percent: int) -> None:
        if percent != self._scan_percent:
            self._scan_percent = percent
            self.scanPercentChanged.emit()


    @Property(int, notify=_Signals.uncheckedFilesChanged)
    def uncheckedFiles(self) -> int:  # noqa: N802 — QML-property-stílus
        """#4586: a futó keresés még nem ellenőrzött fájljainak száma
        (`PeoplePanel::Unchecked`); 0, ha nem fut."""
        return self._unchecked_files


    def _set_unchecked_files(self, count: int) -> None:
        if count != self._unchecked_files:
            self._unchecked_files = count
            self.uncheckedFilesChanged.emit()


    @Slot("QVariantList", result=int)
    def pendingAmong(self, paths) -> int:  # noqa: N802 — QML-slot-stílus
        """#4586: a megadott fotóútvonalak közül hányat fog még detektálni a
        futó keresés (`PeoplePanel` betöltés / ellenőrizetlen fájlok). Az
        Emberek panel kapuja a KIJELÖLÉSRE vonatkozik, nem a könyvtárra:
        egy már átvizsgált képnél nincs „betöltés". Nem futó keresésnél 0."""
        keys = [_path_key(str(path)) for path in paths]
        with self._pending_lock:
            if not self._pending_paths:
                return 0
            return sum(1 for key in keys if key in self._pending_paths)


    def _build_pending(
        self,
        conn,
        photos,
        *,
        scan_states=None,
        ini_cache=None,
        enabled_cache=None,
    ) -> set[str]:
        """A worker átlépési feltételei szerint a ciklus ELŐTT felépített
        halmaz: engedélyezett mappa, nem videó, nincs lefutott keresés, és
        nincs azonosított arc az ini-ben."""
        pending: set[str] = set()
        if scan_states is None:
            scan_states = self._read_face_scan_states(conn)
        if ini_cache is None:
            ini_cache = {}
        if enabled_cache is None:
            enabled_cache = {}
        for photo in photos:
            photo_path = Path(photo.folder_path) / photo.name
            folder_key = _path_key(photo_path.parent)
            if folder_key not in enabled_cache:
                enabled_cache[folder_key] = self._face_detection_enabled(
                    str(photo_path.parent)
                )
            if not enabled_cache[folder_key]:
                continue
            if photo_path.suffix.lower() in VIDEO_EXTENSIONS:
                continue
            if self._face_scan_is_done(scan_states, photo):
                continue
            if any(
                face.is_identified
                for face in ini_faces_of(photo_path, ini_cache)
            ):
                continue
            pending.add(_path_key(photo_path))
        return pending


    def _owns_scan(self, stop_event: threading.Event) -> bool:
        """Ez a szál a JELENLEGI keresés (vagy nincs másik futó)? A
        `_pending_lock` alatt hívandó. Egy újabb keresés a régi szál
        megszakítása után indul, ezért a régi szál `finally`-je és haladása
        nem írhat az újabb állapotába (#4586)."""
        return self._stop_event is None or self._stop_event is stop_event


    def _mark_checked(self, photo_path: Path, stop_event: threading.Event) -> None:
        """A kép kikerül a függők közül — de CSAK a saját keresésének
        halmazából: egy újabb keresés halmazát a régi szál nem bántja."""
        key = _path_key(photo_path)
        with self._pending_lock:
            if not self._owns_scan(stop_event):
                return
            self._pending_paths.discard(key)
            remaining = len(self._pending_paths)
        self._set_unchecked_files(remaining)


    @contextmanager
    def _open_index_for_scan(self) -> Iterator[sqlite3.Connection]:
        """Adatbázishibánál még a kapcsolat lezárása előtt naplóz."""
        yielded = False
        try:
            with open_index(self._db_path) as conn:
                yielded = True
                try:
                    yield conn
                except sqlite3.DatabaseError:
                    self._log_database_error_diagnostics(conn)
                    raise
        except sqlite3.DatabaseError:
            # Ha maga az index megnyitása/sémabetöltése hibázott, nincs élő
            # kapcsolat, amelynek állapotát átadhatnánk.
            if not yielded:
                self._log_database_error_diagnostics()
            raise


    def _log_database_error_diagnostics(
        self, conn: sqlite3.Connection | None = None
    ) -> None:
        """Rögzíti az index állapotát útvonalak nélkül egy arcindex-hibánál."""
        db_path = Path(self._db_path)
        journal_mode = "nem olvasható"
        quick_check = "nem futott le"
        meretek: list[str] = []

        fajlok = (
            ("index.db", db_path),
            ("-wal", Path(f"{db_path}-wal")),
            ("-shm", Path(f"{db_path}-shm")),
        )

        def meretpillanat() -> list[str]:
            allapot = []
            for cimke, fajl in fajlok:
                try:
                    allapot.append(f"{cimke}={fajl.stat().st_size} bájt")
                except FileNotFoundError:
                    allapot.append(f"{cimke}=nincs")
                except OSError:
                    allapot.append(f"{cimke}=nem olvasható")
            return allapot

        try:
            kapcsolat = (
                nullcontext(conn)
                if conn is not None
                else closing(sqlite3.connect(db_path, timeout=0.5))
            )
            with kapcsolat as diagnostic_conn:
                try:
                    row = diagnostic_conn.execute("PRAGMA journal_mode").fetchone()
                    journal_mode = str(row[0]) if row else "nincs eredmény"
                except Exception as diagnostic_error:  # noqa: BLE001 — az őr ne fedje el az eredeti hibát
                    journal_mode = f"nem olvasható ({type(diagnostic_error).__name__})"
                meretek = meretpillanat()
                try:
                    rows = [
                        str(row[0])
                        for row in diagnostic_conn.execute("PRAGMA quick_check")
                    ]
                    quick_check = "; ".join(rows) if rows else "nincs eredmény"
                except Exception as diagnostic_error:  # noqa: BLE001 — az őr ne fedje el az eredeti hibát
                    quick_check = f"nem futott le ({type(diagnostic_error).__name__})"
        except Exception as diagnostic_error:  # noqa: BLE001 — az őr ne fedje el az eredeti hibát
            if journal_mode == "nem olvasható":
                journal_mode = f"nem olvasható ({type(diagnostic_error).__name__})"
            if quick_check == "nem futott le":
                quick_check = f"nem futott le ({type(diagnostic_error).__name__})"
            if not meretek:
                meretek = meretpillanat()
        _log.error("arc-index journal_mode: %s", journal_mode)
        _log.error(
            "arc-index quick_check (SQLite %s): %s", sqlite3.sqlite_version, quick_check
        )
        _log.error("arc-index fájlméretek: %s", ", ".join(meretek))

        try:
            from .worker_thread import running_background_workers

            munkak = running_background_workers()
            nevek = ", ".join(munkak) if munkak else "nincs"
        except Exception as diagnostic_error:  # noqa: BLE001 — diagnosztikai hiba esetén is őrizzük az eredetit
            nevek = f"nem olvasható ({type(diagnostic_error).__name__})"
        _log.error("élő háttérmunkák: %s", nevek)


    @Slot()
    def scanForFaces(self) -> None:
        """A teljes indexelt könyvtár átvizsgálása SAJÁT arc-detektálással.

        Modell hiányában azonnal `modelUnavailable`-t ad és nem indít
        szálat — a hívó UI ekkor a funkciót eleve rejtve/inaktívan
        tarthatja."""
        self._start_face_scan(automatic=False)


    @Slot(str)
    def scanFolder(self, folder_path: str) -> None:  # noqa: N802 — QML-slot-stílus
        """A helyi mappamenüből csak a megadott mappa képeit vizsgálja."""
        with open_index(self._db_path) as conn:
            photos = photos_in_folder(conn, folder_path)
        self._start_face_scan(automatic=False, photos=photos)


    @Slot(str)
    def scanAlbum(self, token: str) -> None:  # noqa: N802 — QML-slot-stílus
        """A helyi albummenüből csak az adott album tagképeit vizsgálja."""
        with open_index(self._db_path) as conn:
            photos = album_photos(conn, token)
        self._start_face_scan(automatic=False, photos=photos)


    def _start_face_scan(
        self,
        *,
        automatic: bool,
        photos: tuple[PhotoRecord, ...] | None = None,
    ) -> None:
        if not automatic and not self._detector.available:
            # #4517: a felület jelzése mellett a hibanaplóba is kerüljön,
            # különben a „nem talál arcot” okát semmi nem rögzíti.
            if not self._unavailable_logged:
                self._unavailable_logged = True
                _log.warning(
                    "az arcfelismerés nem indul: %s", self.unavailableReason()
                )
            self.modelUnavailable.emit()
            return
        if automatic and self._stop_event is not None:
            return
        self.cancelScan()
        self._automatic_scan = automatic
        stop_event = threading.Event()
        self._stop_event = stop_event
        self._set_scan_percent(0)
        self.scanStarted.emit()
        self._start_background(
            self._run_scan,
            args=(stop_event, photos),
            kwargs={"automatic": automatic},
            name="picasapy-face-scan",
            busy=not automatic,
        )


    @Slot()
    def scanNewFaces(self) -> None:  # noqa: N802 — QML-slot-stílus
        """Az újonnan indexelt képek automatikus háttérvizsgálata.

        A könyvtárszinkron `syncFinished` jelzése hívja. Az indexben már
        vizsgált fájlok mtime/méret alapján kimaradnak; párhuzamos
        szinkronjelzés nem szakítja félbe a futó detektálást."""
        if not self.automaticDetectionEnabled() or self._stop_event is not None:
            return
        self._start_face_scan(automatic=True)


    @Slot(int, int)
    def _auto_group_after_scan(self, _found: int, _scanned: int) -> None:
        """Sikeres keresés után automatikusan indítja a 2. lépést (#4619).

        Az eredeti `FRAddSuggesetions` kapcsolója az egész csoportosítási/
        javaslati lépést kapuzza. A kézi csoportosítás változatlanul elérhető
        kikapcsolt beállítás mellett; az automatikus út a küszöböket a már
        meglévő `computeEmbeddings()` híváson keresztül veszi át. Üres
        keresési eredménynél nincs új csoportosítandó adat, ezért ne indítsuk
        el az SFace/OpenCV betöltését sem.
        """
        if not _found and not _scanned:
            return
        if self.suggestionsEnabled():
            self.computeEmbeddings()


    @Slot()
    def cancelScan(self) -> None:
        """A folyamatban lévő szkennelés megszakítása mappa/fotó-határon —
        a már elmentett találatok az indexben maradnak."""
        if self._stop_event is not None:
            self._stop_event.set()


    # -- worker-szál törzse -------------------------------------------------

    def _wait_for_scan_slot(
        self,
        stop_event: threading.Event,
        *,
        automatic: bool,
        delay_seconds: float = 0.0,
        pause_for_activity: bool = True,
        on_busy_changed: Callable[[bool], None] | None = None,
    ) -> bool:
        """Aktivitás alatt vár, különben a detektálási idővel arányosan fékez."""
        remaining = max(0.0, delay_seconds)
        paused = False
        while not stop_event.is_set():
            if (
                automatic
                and pause_for_activity
                and self._scan_should_pause()
            ):
                if not paused and on_busy_changed is not None:
                    on_busy_changed(False)
                paused = True
                stop_event.wait(0.25)
                continue
            if paused and on_busy_changed is not None:
                on_busy_changed(True)
            paused = False
            if remaining <= 0:
                return True
            started = time.perf_counter()
            if stop_event.wait(min(remaining, 0.25)):
                return False
            remaining = max(0.0, remaining - (time.perf_counter() - started))
        return False


    def _run_scan(
        self,
        stop_event: threading.Event,
        scoped_photos: tuple[PhotoRecord, ...] | None = None,
        *,
        automatic: bool | None = None,
    ) -> None:
        elozo_szalszam: int | None = None
        found = 0
        scanned = 0
        if automatic is None:
            automatic = self._automatic_scan
        scan_started = time.perf_counter()
        phase_times = {
            "index": 0.0,
            "ini_stat": 0.0,
            "pending": 0.0,
            "ini_reconcile": 0.0,
            "decode_detect": 0.0,
            "database_save": 0.0,
            "activity_wait": 0.0,
        }
        pending_total = 0
        busy_ticket: int | None = None

        def set_scan_busy(active: bool) -> None:
            nonlocal busy_ticket
            if not automatic:
                return
            if active and busy_ticket is None:
                busy_ticket = get_app_busy_registry().begin(
                    munka_neve("picasapy-face-scan")
                )
            elif not active and busy_ticket is not None:
                get_app_busy_registry().end(busy_ticket)
                busy_ticket = None

        try:
            with self._open_index_for_scan() as conn:
                phase_started = time.perf_counter()
                # #4887: a szkennelés a rejtett mappák képein is fut (az
                # eredménye a megjelenítéskor szűrődik)
                photos = (
                    all_photos(conn, include_hidden_folders=True)
                    if scoped_photos is None
                    else scoped_photos
                )
                scan_states = self._read_face_scan_states(conn)
                phase_times["index"] += time.perf_counter() - phase_started
                ini_cache: dict = {}
                enabled_cache: dict[str, bool] = {}
                phase_started = time.perf_counter()
                changed_ini_dirs, current_ini_signatures = (
                    self._changed_ini_directories(photos)
                )
                phase_times["ini_stat"] += time.perf_counter() - phase_started
                phase_started = time.perf_counter()
                detection_pending = self._build_pending(
                    conn,
                    photos,
                    scan_states=scan_states,
                    ini_cache=ini_cache,
                    enabled_cache=enabled_cache,
                )
                phase_times["pending"] += time.perf_counter() - phase_started
                with self._pending_lock:
                    if not self._owns_scan(stop_event):
                        detection_pending = set()
                    self._pending_paths = detection_pending
                pending_total = len(detection_pending)
                self._set_unchecked_files(pending_total)

                reconcile_photos = []
                phase_started = time.perf_counter()
                if changed_ini_dirs:
                    for photo in photos:
                        folder = Path(photo.folder_path)
                        folder_key = _path_key(folder)
                        if folder_key not in changed_ini_dirs:
                            continue
                        if not enabled_cache.get(folder_key, False):
                            continue
                        if Path(photo.name).suffix.lower() in VIDEO_EXTENSIONS:
                            continue
                        if self._face_scan_is_done(scan_states, photo):
                            reconcile_photos.append(photo)

                # A változatlan könyvtár üres köre itt megáll: nincs ini-olvasás,
                # képenkénti SQL, detektor- vagy útvonal-felbontási munka.
                if not detection_pending and not reconcile_photos:
                    self._face_ini_signatures.update(current_ini_signatures)
                    phase_times["ini_reconcile"] += (
                        time.perf_counter() - phase_started
                    )
                else:
                    reconcile_batch = 0
                    for photo in reconcile_photos:
                        if stop_event.is_set():
                            if reconcile_batch:
                                conn.commit()
                            self.scanCancelled.emit()
                            return
                        photo_path = Path(photo.folder_path) / photo.name
                        ini_faces = ini_faces_of(photo_path, ini_cache)
                        _mark_previously_ignored(conn, photo.id, ini_faces)
                        reconcile_batch += 1
                        if reconcile_batch >= self._SCAN_COMMIT_BATCH_SIZE:
                            conn.commit()
                            reconcile_batch = 0
                    if reconcile_batch:
                        conn.commit()
                    phase_times["ini_reconcile"] += (
                        time.perf_counter() - phase_started
                    )

                    if detection_pending and not self._detector.available:
                        if not self._unavailable_logged:
                            self._unavailable_logged = True
                            _log.warning(
                                "az arcfelismerés nem indul: %s",
                                self.unavailableReason(),
                            )
                        self.modelUnavailable.emit()
                        return

                    pending_photos = [
                        photo
                        for photo in photos
                        if _path_key(Path(photo.folder_path) / photo.name)
                        in detection_pending
                    ]
                    if pending_photos:
                        elozo_szalszam = arckeres_szal_elokeszitese()
                    batch: list[tuple[PhotoRecord, tuple, tuple]] = []

                    def commit_batch() -> None:
                        nonlocal found, scanned
                        if not batch:
                            return
                        save_started = time.perf_counter()
                        for photo, faces, ini_faces in batch:
                            replace_faces(conn, photo.id, faces)
                            _mark_previously_ignored(conn, photo.id, ini_faces)
                            mark_face_scan(
                                conn,
                                photo.id,
                                mtime_ns=photo.mtime_ns,
                                size=photo.size,
                            )
                            found += len(faces)
                            scanned += 1
                        conn.commit()
                        phase_times["database_save"] += (
                            time.perf_counter() - save_started
                        )
                        for done, (_photo, faces, _ini_faces) in enumerate(
                            batch, start=scanned - len(batch) + 1
                        ):
                            if faces:
                                self.facesStored.emit()
                            if automatic:
                                self._report_scan(done, pending_total)
                        batch.clear()

                    processed = 0
                    pause_for_activity = (
                        automatic
                        and pending_total > _AUTOMATIC_SCAN_UNPAUSED_LIMIT
                    )
                    for photo in pending_photos:
                        wait_started = time.perf_counter()
                        slot_available = self._wait_for_scan_slot(
                            stop_event,
                            automatic=automatic,
                            pause_for_activity=pause_for_activity,
                            on_busy_changed=set_scan_busy,
                        )
                        phase_times["activity_wait"] += (
                            time.perf_counter() - wait_started
                        )
                        if not slot_available:
                            commit_batch()
                            conn.commit()
                            self.scanCancelled.emit()
                            return
                        set_scan_busy(True)
                        photo_path = Path(photo.folder_path) / photo.name
                        try:
                            ini_faces = ini_faces_of(photo_path, ini_cache)
                            started = time.perf_counter()
                            faces = self._detect(
                                photo_path,
                                source_width=photo.width,
                                source_height=photo.height,
                                source_mtime_ns=photo.mtime_ns,
                                source_size=photo.size,
                            )
                            elapsed = time.perf_counter() - started
                            phase_times["decode_detect"] += elapsed
                            batch.append((photo, faces, ini_faces))
                            self._mark_checked(photo_path, stop_event)
                            processed += 1
                            if not automatic:
                                # A kézi keresés a korábbi módon, minden sikeres
                                # detektálás után frissíti a haladást; a DB-írás
                                # ettől függetlenül kötegelt marad.
                                self._report_scan(processed, pending_total)
                            if len(batch) >= self._SCAN_COMMIT_BATCH_SIZE:
                                commit_batch()
                            wait_started = time.perf_counter()
                            slot_available = self._wait_for_scan_slot(
                                stop_event,
                                automatic=automatic,
                                delay_seconds=elapsed if automatic else 0.0,
                                pause_for_activity=pause_for_activity,
                                on_busy_changed=set_scan_busy,
                            )
                            phase_times["activity_wait"] += (
                                time.perf_counter() - wait_started
                            )
                            if not slot_available:
                                commit_batch()
                                conn.commit()
                                self.scanCancelled.emit()
                                return
                        except Exception:
                            commit_batch()
                            raise
                    commit_batch()
                    if not stop_event.is_set():
                        conn.commit()
                        with self._pending_lock:
                            owner = self._owns_scan(stop_event)
                        if owner:
                            self._face_ini_signatures.update(
                                current_ini_signatures
                            )
        except sqlite3.DatabaseError as error:
            _log.exception("arc-detektálás adatbázishiba")
            self.scanFailed.emit(str(error))
            return
        except Exception as error:  # noqa: BLE001 — index-hiba se fagyassza a UI-t
            _log.exception("arc-detektálás hiba")
            self.scanFailed.emit(str(error))
            return
        finally:
            set_scan_busy(False)
            _log.info(
                "arckeres fázisidők: index=%.3fs, .picasa.ini stat=%.3fs, "
                "függőlista=%.3fs, ini-egyeztetés=%.3fs, "
                "dekódolás/detektálás=%.3fs, indexmentés=%.3fs, "
                "aktivitásvárakozás=%.3fs, teljes=%.3fs; függő=%d, "
                "feldolgozott=%d",
                phase_times["index"],
                phase_times["ini_stat"],
                phase_times["pending"],
                phase_times["ini_reconcile"],
                phase_times["decode_detect"],
                phase_times["database_save"],
                phase_times["activity_wait"],
                time.perf_counter() - scan_started,
                pending_total,
                scanned,
            )
            arckeres_szal_lezarasa(elozo_szalszam)
            self._ini_ignored_cache = None
            with self._pending_lock:
                owner = self._owns_scan(stop_event)
                if owner:
                    self._stop_event = None
                    self._automatic_scan = False
                    self._pending_paths = set()
            if owner:
                # a sor eltűnik a bal hasábból — akkor is, ha megszakadt vagy
                # hibára futott (#449). Egy közben indult ÚJABB keresés
                # állapotát (százalék, függők) a régi szál nem bántja.
                self._set_scan_percent(-1)
                self._set_unchecked_files(0)
            self._scanWorkerStopped.emit()
        self.unnamedCountChanged.emit()
        self.scanFinished.emit(found, scanned)


    def _report_scan(self, done: int, total: int) -> None:
        """Haladás-jelzés + a bal hasáb sorának százaléka (#449)."""
        self._set_scan_percent(round(100 * done / total) if total else 100)
        self.scanProgress.emit(done, total)


    def _detect(
        self,
        photo_path: Path,
        *,
        source_width: int | None = None,
        source_height: int | None = None,
        source_mtime_ns: int | None = None,
        source_size: int | None = None,
    ):
        image = self._decode(photo_path)
        if image is None:
            return ()
        if source_mtime_ns is not None and source_size is not None:
            _remember_decoded_image(
                photo_path,
                source_mtime_ns,
                source_size,
                _DETECT_MAX_DIMENSION,
                image,
            )
        # A JPEG dekóder minőségi tartaléka a kért 960 px helyett teljes
        # vagy annál még mindig nagyobb képet adhat. A YuNet bemenetét ezért
        # itt is kötelező a határra kicsinyíteni.
        detector_image = scale_down(image, _DETECT_MAX_DIMENSION)
        detections = self._detector.detect(detector_image)
        decoded_height, decoded_width = image.shape[:2]
        if source_width and source_height:
            target_width, target_height = source_width, source_height
        else:
            target_width, target_height = decoded_width, decoded_height
        detector_height, detector_width = detector_image.shape[:2]
        scale_x = target_width / detector_width
        scale_y = target_height / detector_height
        if scale_x == 1 and scale_y == 1:
            return detections
        return tuple(
            rescale_face_detection(detection, scale_x, scale_y)
            for detection in detections
        )


    @staticmethod
    def _decode(photo_path: Path):
        """A fotó redukált dekódolása — a thumbs-cache/dedup mintáját
        követi (`cvimage.read_image_bytes` + `reduced_color_flag`), hogy
        ne épüljön új I/O-út a projektbe."""
        #: #3120: a KÖZÖS belépőn megy — a `cv2.imdecode`-nak nincs nyers
        #: dekódere, tehát a RAW fájlokban nem kerestünk arcot.
        return dekodolj_forrast(photo_path, goal=_DETECT_MAX_DIMENSION)
