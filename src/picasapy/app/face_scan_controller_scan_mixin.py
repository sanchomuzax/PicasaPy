"""Arcfelismerési keresés, állapotkövetés és detektor-worker."""

from __future__ import annotations

from .face_scan_controller_signals import FaceScanControllerSignalsMixin as _Signals
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
    album_photos,
    all_photos,
    dekodolj_forrast,
    face_scan_done,
    ini_faces_of,
    mark_face_scan,
    open_index,
    photos_in_folder,
    replace_faces,
    rescale_face_detection,
    scale_down,
    threading,
)


class FaceScanControllerScanMixin:
    """Arcfelismerési keresés, állapotkövetés és detektor-worker."""


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


    def _build_pending(self, conn, photos) -> set[str]:
        """A worker átlépési feltételei szerint a ciklus ELŐTT felépített
        halmaz: engedélyezett mappa, nem videó, nincs lefutott keresés, és
        nincs azonosított arc az ini-ben."""
        pending: set[str] = set()
        ini_cache: dict = {}
        for photo in photos:
            photo_path = Path(photo.folder_path) / photo.name
            if not self._face_detection_enabled(str(photo_path.parent)):
                continue
            if photo_path.suffix.lower() in VIDEO_EXTENSIONS:
                continue
            if face_scan_done(
                conn, photo.id, mtime_ns=photo.mtime_ns, size=photo.size
            ):
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
        if not self._detector.available:
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
            self._run_scan, args=(stop_event, photos), name="picasapy-face-scan"
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
        meglévő `computeEmbeddings()` híváson keresztül veszi át.
        """
        if self.suggestionsEnabled():
            self.computeEmbeddings()


    @Slot()
    def cancelScan(self) -> None:
        """A folyamatban lévő szkennelés megszakítása mappa/fotó-határon —
        a már elmentett találatok az indexben maradnak."""
        if self._stop_event is not None:
            self._stop_event.set()


    # -- worker-szál törzse -------------------------------------------------

    def _run_scan(
        self,
        stop_event: threading.Event,
        scoped_photos: tuple[PhotoRecord, ...] | None = None,
    ) -> None:
        try:
            with open_index(self._db_path) as conn:
                # #4887: a szkennelés a rejtett mappák képein is fut (az
                # eredménye a megjelenítéskor szűrődik)
                photos = (
                    all_photos(conn, include_hidden_folders=True)
                    if scoped_photos is None
                    else scoped_photos
                )
                total = len(photos)
                pending = self._build_pending(conn, photos)
                with self._pending_lock:
                    if not self._owns_scan(stop_event):
                        # közben újabb keresés indult: az övé a halmaz
                        pending = set()
                    self._pending_paths = pending
                self._set_unchecked_files(len(pending))
                found = 0
                scanned = 0
                for done, photo in enumerate(photos, start=1):
                    if stop_event.is_set():
                        conn.commit()
                        self.scanCancelled.emit()
                        return
                    try:
                        photo_path = Path(photo.folder_path) / photo.name
                        if not self._face_detection_enabled(str(photo_path.parent)):
                            self._report_scan(done, total)
                            continue
                        ini_faces = ini_faces_of(photo_path)
                        if any(face.is_identified for face in ini_faces):
                            # a Picasa döntése szent — nem értékeljük újra
                            self._report_scan(done, total)
                            continue
                        if photo_path.suffix.lower() in VIDEO_EXTENSIONS:
                            self._report_scan(done, total)
                            continue
                        # #2519: már lefutott ezen a fájlállapoton — a `face`
                        # tábla ürességéből ez nem látszana (arc nélküli fotó =
                        # nulla sor), ezért kell a külön nyom. A `kizarva`
                        # jelölést a fájl változása sem oldja fel.
                        if face_scan_done(
                            conn, photo.id, mtime_ns=photo.mtime_ns, size=photo.size
                        ):
                            # #3670: a Picasa a mi keresésünk UTÁN is mellőzhette
                            _mark_previously_ignored(conn, photo.id, ini_faces)
                            conn.commit()
                            self._report_scan(done, total)
                            continue
                        faces = self._detect(
                            photo_path,
                            source_width=photo.width,
                            source_height=photo.height,
                        )
                        replace_faces(conn, photo.id, faces)
                        _mark_previously_ignored(conn, photo.id, ini_faces)
                        mark_face_scan(
                            conn, photo.id, mtime_ns=photo.mtime_ns, size=photo.size
                        )
                        found += len(faces)
                        scanned += 1
                        # A következő kép detektálása több másodperc lehet; ne
                        # tartsa addig az SQLite írási zárát.
                        conn.commit()
                        self._mark_checked(photo_path, stop_event)
                        if faces:
                            # a commit UTÁN: a panel már a mentett arcot látja
                            self.facesStored.emit()
                        self._report_scan(done, total)
                    finally:
                        # a `continue` ágak is kivéve a függők közül (#4586)
                        self._mark_checked(photo_path, stop_event)
                conn.commit()
        except Exception as error:  # noqa: BLE001 — index-hiba se fagyassza a UI-t
            _log.exception("arc-detektálás hiba: %s", self._db_path)
            self.scanFailed.emit(str(error))
            return
        finally:
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
    ):
        image = self._decode(photo_path)
        if image is None:
            return ()
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
