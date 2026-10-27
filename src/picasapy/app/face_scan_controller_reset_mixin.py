"""Mellőzés, arcadatok visszaállítása és mellőzött arcok kezelése."""

from __future__ import annotations

from .face_scan_controller_signals import FaceScanControllerSignalsMixin as _Signals
from .face_scan_controller_shared import (
    Path,
    Property,
    QGuiApplication,
    Qt,
    Slot,
    UnnamedFace,
    _group_payload,
    _ini_face_payload,
    _ini_only,
    _path_key,
    _photo_paths,
    all_photos,
    best_region,
    clear_faces,
    forget_face_scan,
    hidden_folders_visible,
    ignored_faces,
    ignored_ini_faces,
    ignored_regions,
    ini_faces_of,
    mark_faces_ignored,
    open_index,
    parse_ini_face_key,
    quantize_rect,
    reset_all_faces_in_index,
    unignore_faces,
    unnamed_faces,
)


class FaceScanControllerResetMixin:
    """Mellőzés, arcadatok visszaállítása és mellőzött arcok kezelése."""


    @Slot(list, result=int)
    def ignoreFaces(self, face_ids) -> int:  # noqa: N802 — QML-slot-stílus
        """A kijelölt arcok MELLŐZÉSE — a „Mellőzött emberek" album (#26).

        Az eredetiben ez nem törlés volt: *„Are you sure you want to move
        this person to the ignored people album?"* — a személy egy külön
        albumba került, tehát visszavehető. Nálunk ugyanez: az arc-sor
        megmarad, csak `state = 'ignored'` lesz, így sem a „Névtelenek"
        albumban, sem a csoportosításban nem bukkan fel újra.

        #3670: élőben mérve (picasa-arcfelismeres.md 15.3/b.1) a mellőzés a
        `.picasa.ini`-be is beír — a `faces=` kulcs érintett régiójának
        személy-mezőjébe `ffffffffffffffff` kerül, a fotó többi arca
        érintetlen marad. Enélkül az elvetés más gépre másolt könyvtárban,
        vagy egy friss újraindexelés után elveszne, mert csak a saját
        SQLite-indexünkben élt. Az írás a `FacesHelper.addIgnoredFace()`
        műveleten át megy; `None` `FacesHelper` mellett csak az index
        frissül.

        A mellőzött arcok száma a visszatérési érték."""
        ids = [int(face_id) for face_id in face_ids]
        if not ids:
            return 0
        with open_index(self._db_path) as conn:
            by_id = {face.id: face for face in unnamed_faces(conn) if face.rect is not None}
            mark_faces_ignored(conn, ids)
            conn.commit()
        self._write_ignore_markers([by_id[i] for i in ids if i in by_id])
        self._ini_ignored_cache = None
        self.unnamedCountChanged.emit()
        return len(ids)


    def _write_ignore_markers(self, targets: list[UnnamedFace]) -> None:
        """A `faces=rect64(…),ffffffffffffffff` bejegyzések írása (#3670).

        A keret a rect64 tartományára vágva és rácsára kerekítve megy (J1:
        a kereten túllógó arc különben `ValueError`-t dobna, és a köteg
        többi arca kimaradna). Ha a Picasa ugyanezt az arcot már mellőzte
        (saját, eltérő keretével), nem írunk mellé egy második bejegyzést.
        `None` `FacesHelper` mellett csak az index frissül."""
        if self._faces_helper is None:
            return
        for face in targets:
            rect = quantize_rect(face.rect)
            existing = ignored_regions(ini_faces_of(face.photo_path))
            if best_region(rect, existing) is not None:
                continue
            self._faces_helper.addIgnoredFace(str(face.photo_path), *rect)


    @Slot(list, result=int)
    def resetFacesForPhotos(self, image_paths) -> int:  # noqa: N802 — QML-slot-stílus
        """A kijelölt képek arcadatainak törlése és újrakeresése (#4510).

        A `.picasa.ini` írása kizárólag a `FacesHelper`/`ini` API-n megy.
        Az index saját találatai és átnézettségi jelölése az `index/`
        API-ján keresztül törlődik. A következő keresés a már meglévő
        automatikus háttérúton fut; futó keresés esetén annak biztonságos
        leállása után indul újra.

        Visszatérési értéke a kijelölt, érvényes útvonalak száma."""
        if not image_paths:
            return 0
        paths = tuple(dict.fromkeys(str(path) for path in image_paths if path))
        if not paths:
            return 0

        modifiers = QGuiApplication.keyboardModifiers()
        if modifiers & Qt.KeyboardModifier.ControlModifier:
            self.faceResetConfirmationRequested.emit("removeAllFaceData")
            return 0
        if modifiers & Qt.KeyboardModifier.ShiftModifier:
            self.faceResetConfirmationRequested.emit("resetAllFaces")
            return 0

        for image_path in paths:
            if self._faces_helper is not None:
                self._faces_helper.removeAllFaces(image_path)

        return self._schedule_face_reset(paths)


    @Slot(result=int)
    def removeAllFaceData(self) -> int:  # noqa: N802 — QML-slot-stílus
        """A Ctrl-ág: teljes ini-/index-törlés, majd teljes újra-arcfelismerés."""
        paths = self._all_photo_paths()
        if not paths:
            return 0
        if self._faces_helper is not None and not self._faces_helper.removeAllFaceData(
            paths
        ):
            return 0
        self._ini_ignored_cache = None
        self._schedule_face_reset(paths, force_scan=True)
        return len(paths)


    @Slot(result=int)
    def resetAllFaces(self) -> int:  # noqa: N802 — QML-slot-stílus
        """A Shift-ág: a névhozzárendeléseket törli, az arcokat megtartja."""
        paths = self._all_photo_paths()
        if self._faces_helper is not None and not self._faces_helper.resetAllFaces(
            paths
        ):
            return 0
        with open_index(self._db_path) as conn:
            affected = reset_all_faces_in_index(conn)
            conn.commit()
        self._ini_ignored_cache = None
        self.unnamedCountChanged.emit()
        return affected


    def _all_photo_paths(self) -> tuple[str, ...]:
        """A jelenleg indexelt könyvtár összes fotójának abszolút útvonala."""
        with open_index(self._db_path) as conn:
            # #4887: belső (nem megjelenítő) út — a rejtett mappák is
            return tuple(
                str(Path(photo.folder_path) / photo.name)
                for photo in all_photos(conn, include_hidden_folders=True)
            )


    def _schedule_face_reset(
        self, paths: tuple[str, ...], *, force_scan: bool = False
    ) -> int:
        """Az index törlése és az érintett fotók újra-arcfelismerése."""
        if self._stop_event is not None or self._pending_face_reset_paths:
            self._pending_face_reset_paths.extend(
                path
                for path in paths
                if path not in self._pending_face_reset_paths
            )
            self._resume_scan_after_reset = True
            self._resume_face_reset_force_scan |= force_scan
            self.cancelScan()
            return len(paths)

        self._reset_index_faces(paths)
        if not self._detector.available:
            self.modelUnavailable.emit()
        elif force_scan:
            self._start_face_scan(automatic=False)
        else:
            self.scanNewFaces()
        return len(paths)


    def _reset_index_faces(self, image_paths: tuple[str, ...] | list[str]) -> int:
        """A kijelölt fotók származtatott arcadatait üríti az `index/` API-val."""
        with open_index(self._db_path) as conn:
            photos_by_path = {
                _path_key(Path(photo.folder_path) / photo.name): photo.id
                for photo in all_photos(conn, include_hidden_folders=True)
            }
            photo_ids = {
                photos_by_path[_path_key(path)]
                for path in image_paths
                if _path_key(path) in photos_by_path
            }
            if photo_ids and photo_ids == set(photos_by_path.values()):
                # A teljes könyvtár resetjénél a korábbi klaszter-centroidok
                # is elavulnak. Az index API előbb leválasztja és törli őket;
                # a részleges, kijelöléses ág érintetlen marad.
                reset_all_faces_in_index(conn)
            for photo_id in photo_ids:
                clear_faces(conn, photo_id)
                forget_face_scan(conn, photo_id=photo_id)
            conn.commit()
        if photo_ids:
            self._ini_ignored_cache = None
            self.unnamedCountChanged.emit()
        return len(photo_ids)


    @Slot()
    def _finish_reset_after_scan(self) -> None:
        """A futó szkennelés után érvényesíti a függő reseteket és újraindít."""
        if not self._resume_scan_after_reset:
            return
        paths = tuple(self._pending_face_reset_paths)
        self._pending_face_reset_paths.clear()
        self._resume_scan_after_reset = False
        force_scan = self._resume_face_reset_force_scan
        self._resume_face_reset_force_scan = False
        self._reset_index_faces(paths)
        if not self._detector.available:
            self.modelUnavailable.emit()
        elif force_scan:
            self._start_face_scan(automatic=False)
        else:
            self.scanNewFaces()


    @Property(int, notify=_Signals.unnamedCountChanged)
    def ignoredCount(self) -> int:  # noqa: N802 - QML-tulajdonság
        """Hány arc van a „Mellőzött emberek" albumban — a saját indexben
        mellőzöttek és az eredeti Picasa által mellőzöttek (#3670) együtt.

        #5323: tulajdonság, `unnamedCountChanged` NOTIFY-jal (mint a
        `unnamedCount`). Metódusként a QML-kötés nem figyelt a mellőzésre,
        a bal sáv sora nullát mutatott."""
        # #4887: a gyorstár a rejtett mappák láthatóságához kötött — a
        # kapcsoló átváltása után a darabszám nem maradhat a régin
        lathato = hidden_folders_visible(self._db_path)
        with open_index(self._db_path) as conn:
            own = ignored_faces(conn)
            if (
                self._ini_ignored_cache is None
                or getattr(self, "_ini_ignored_lathato", None) != lathato
            ):
                self._ini_ignored_cache = ignored_ini_faces(conn)
                self._ini_ignored_lathato = lathato
        return len(own) + len(_ini_only(own, self._ini_ignored_cache))


    @Slot(result="QVariantList")
    def ignoredGroups(self) -> list[dict]:  # noqa: N802 — QML-slot-stílus
        """A „Mellőzött emberek" album tartalma — az `unnamedGroups()`
        alakjában, egyetlen csoportban.

        Az eredetiben ez egy ALBUM volt (`CAlbumLabel::Ignored` =
        „Ignored people"), nem egy elrejtett szemetes: meg lehetett nézni,
        tehát vissza is lehetett venni belőle.

        #3670 (B2): az eredeti Picasa által mellőzött arcok
        (`faces=…,ffffffffffffffff`) is itt vannak. Ha egy saját, mellőzött
        találat átfedi (`face_ignore_ini.match_regions`), a saját sor
        képviseli; különben az ini-régió önálló elemként, `ini:` kulcsú
        `faceId`-vel jelenik meg."""
        with open_index(self._db_path) as conn:
            faces = [face for face in ignored_faces(conn) if face.rect is not None]
            self._ini_ignored_cache = ignored_ini_faces(conn)
            self._ini_ignored_lathato = hidden_folders_visible(self._db_path)
        extra = _ini_only(faces, self._ini_ignored_cache)
        total = len(faces) + len(extra)
        if not total:
            return []
        payload = _group_payload(faces, self.tr("Ignored people ({0})").format(total))
        return [
            {
                **payload,
                "faces": [*payload["faces"], *(_ini_face_payload(item) for item in extra)],
            }
        ]


    @Slot(list, result=int)
    def unignoreFaces(self, face_ids) -> int:  # noqa: N802 — QML-slot-stílus
        """A mellőzés VISSZAVONÁSA: az arcok újra a „Névtelenek" albumba
        kerülnek.

        #3670: a `.picasa.ini`-ben ez a mellőzés jelének törlése (mérve: „a
        visszavétel a névtelenek közé törli a `faces=` bejegyzést"). CSAK a
        pontos (régió, `ffffffffffffffff`) pár megy (`FacesHelper.
        removeIgnoredFace`, B3): ha a régióra közben névcímke került, az
        ember által adott név marad. A saját archoz az átfedés szerint
        illeszkedő ini-régió tartozik (a Picasa kerete eltér a miénktől);
        az `ini:` kulcsú elem a saját ini-régióját viszi."""
        own_ids: list[int] = []
        ini_items: list[tuple[int, tuple[float, float, float, float]]] = []
        for key in face_ids:
            parsed = parse_ini_face_key(key)
            if parsed is not None:
                ini_items.append(parsed)
            else:
                own_ids.append(int(key))
        if not own_ids and not ini_items:
            return 0
        with open_index(self._db_path) as conn:
            by_id = {face.id: face for face in ignored_faces(conn) if face.rect is not None}
            unignore_faces(conn, own_ids)
            conn.commit()
            paths = _photo_paths(conn, {photo_id for photo_id, _rect in ini_items})
        targets = [
            (face.photo_path, best_region(
                quantize_rect(face.rect), ignored_regions(ini_faces_of(face.photo_path))
            ))
            for face in (by_id[i] for i in own_ids if i in by_id)
        ]
        targets += [(paths[pid], rect) for pid, rect in ini_items if pid in paths]
        if self._faces_helper is not None:
            for path, region in targets:
                if region is not None:
                    self._faces_helper.removeIgnoredFace(str(path), *region)
        self._ini_ignored_cache = None
        self.unnamedCountChanged.emit()
        return len(own_ids) + len(ini_items)
