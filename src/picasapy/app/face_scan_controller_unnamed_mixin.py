"""Névtelen arcok albuma, névadás és XMP-írás."""

from __future__ import annotations

from .face_scan_controller_signals import FaceScanControllerSignalsMixin as _Signals
from .face_scan_controller_shared import (
    Path,
    Property,
    Slot,
    UnnamedFace,
    _COLLAPSED_GROUP_PREVIEW,
    _group_payload,
    export_sidecar_for_photo,
    faces_for_photo,
    ignored_faces,
    ini_faces_of,
    load_enabled_filetypes,
    mark_faces_named,
    match_named_regions,
    open_index,
    quantize_rect,
    sync_tree,
    unnamed_album_photos,
    unnamed_faces,
)


class FaceScanControllerUnnamedMixin:
    """Névtelen arcok albuma, névadás és XMP-írás."""


    @staticmethod
    def _unnamed_faces_without_named_ini(conn) -> tuple[UnnamedFace, ...]:
        """Az index névtelen arcai közül kihagyja az ini-ben már megnevezetteket."""
        faces = unnamed_faces(conn)
        faces_by_photo = {}
        ini_cache = {}
        matched_named_ids = set()
        for face in faces:
            if face.rect is not None:
                faces_by_photo.setdefault(face.photo_path, []).append(face)
        for photo_path, photo_faces in faces_by_photo.items():
            ini_faces = ini_faces_of(photo_path, ini_cache)
            all_index_faces = faces_for_photo(conn, photo_faces[0].photo_id)
            matched = match_named_regions(
                (
                    (face.id, face.rect)
                    for face in all_index_faces
                    if face.rect is not None and face.state in {"unnamed", "named"}
                ),
                ini_faces,
            )
            matched_named_ids.update(matched)
        return tuple(face for face in faces if face.id not in matched_named_ids)


    @Slot(result="QVariantList")
    def unnamedAlbum(self) -> list[dict]:
        """A „Névtelenek" album QML-nek: `[{path, name}, ...]` — LISTA, nem
        tuple (a `people`/`albums` property mintája, MEMORY 2026-07-22)."""
        with open_index(self._db_path) as conn:
            face_photo_ids = {
                face.photo_id for face in self._unnamed_faces_without_named_ini(conn)
            }
            records = [
                record
                for record in unnamed_album_photos(conn)
                if record.id in face_photo_ids
            ]
        return [
            {"path": str(Path(record.folder_path) / record.name), "name": record.name}
            for record in records
        ]


    @Property(int, notify=_Signals.unnamedCountChanged)
    def unnamedCount(self) -> int:
        """A bal hasábban látható névtelen arcok száma."""
        with open_index(self._db_path) as conn:
            return len(self._unnamed_faces_without_named_ini(conn))


    @Slot(result=bool)
    def unnamedWelcomeHasBeenShown(self) -> bool:  # noqa: N802
        """A Név nélküliek üdvözlése már bezárult-e ebben a profilban."""
        return self._beallitas_bool(self.UNNAMED_WELCOME_SHOWN_KEY, False)


    @Slot()
    def markUnnamedWelcomeShown(self) -> None:  # noqa: N802
        """A bezárt üdvözlőablak megjegyzése a közös QSettings-tárban."""
        self._settings.setValue(self.UNNAMED_WELCOME_SHOWN_KEY, True)
        self._settings.sync()


    @Slot(bool, bool, result="QVariantList")
    def unnamedGroups(self, group_by_face: bool, expand_groups: bool) -> list[dict]:
        """A „Névtelenek" album QML-nek, CSOPORTOSÍTVA (issue #26, 3.
        lépcső) — `[{label, faces: [{faceId, thumbUrl}, ...]}, ...]`.

        `group_by_face=False`: egyetlen csoport, az összes névtelen arc (a
        Picasa „Group by face" kikapcsolt állapota — nincs csoportosítás,
        csak lista).

        `group_by_face=True`: egy csoport a `face_group`-onként (`id`
        szerint), plusz egy utolsó „még csoportosítatlan" csoport a
        `group_id IS NULL` araoknak (pl. lenyomat-számítás előtt/modell
        nélkül minden ide kerül). `expand_groups=False` esetén csoportonként
        legfeljebb `_COLLAPSED_GROUP_PREVIEW` arc látszik (a Picasa
        csoport-előnézete) — a lista maga is CSAK ennyi arcot ad vissza,
        tehát a kijelölés/névadás is erre a részhalmazra korlátozódik,
        amíg a felhasználó be nem kapcsolja a teljes listát.

        Hiányzó fotóméret (width/height az indexben) esetén az adott arc
        kimarad — `addFace()`-hez relatív (rect64) koordináta kell, amit
        méret nélkül nem lehet számolni (ld. `UnnamedFace.rect`)."""
        with open_index(self._db_path) as conn:
            faces = [
                face
                for face in self._unnamed_faces_without_named_ini(conn)
                if face.rect is not None
            ]
        if not group_by_face:
            return [_group_payload(faces, self.tr("All unnamed faces ({0})").format(len(faces)))]
        buckets: dict[int | None, list] = {}
        order: list[int | None] = []
        for face in faces:
            if face.group_id not in buckets:
                buckets[face.group_id] = []
                order.append(face.group_id)
            buckets[face.group_id].append(face)
        ordered_keys = sorted(key for key in order if key is not None)
        if None in buckets:
            ordered_keys.append(None)
        result = []
        for key in ordered_keys:
            members = buckets[key]
            shown = members if expand_groups else members[:_COLLAPSED_GROUP_PREVIEW]
            if key is None:
                label = self.tr("Not yet grouped ({0})").format(len(members))
            else:
                label = self.tr("Group {0} ({1})").format(key, len(members))
            if not expand_groups and len(shown) < len(members):
                label = f"{label}…"
            result.append(_group_payload(shown, label))
        return result


    @Slot("QVariantList", str, result=bool)
    def assignNameToFaces(self, face_ids, name: str) -> bool:
        """Tömeges névadás — a Picasa „Add a name" gombja: *„Assign a name
        to all of the selected faces"*. A MEGLÉVŐ `FacesHelper.addFace()`
        útján ír (nem új logika), majd a sikeresen megírt arcokat `'named'`
        állapotba állítja (`mark_faces_named`), hogy se a „Névtelenek"
        album, se a „Mellőzött emberek" albumban, se a jövőbeli
        csoportosításban ne lássa többé — az ALAPSZABÁLY
        (a Picasa döntései szentek) innentől erre a friss, EMBER által
        adott névre is vonatkozik.

        Üres névnél/arclistánál, vagy ha nincs bekötött `FacesHelper`,
        hamis eredmény, írás nélkül. Igaz eredmény csak akkor, ha MINDEN
        kért arcot sikerült megírni — részleges sikernél (pl. egy fájl
        közben törlődött) a sikeres részt megtartjuk, de a visszatérési
        érték hamis, hogy a hívó UI jelezhesse a hiányosságot."""
        clean_name = (name or "").strip()
        if self._faces_helper is None or not face_ids or not clean_name:
            return False
        ids = {int(face_id) for face_id in face_ids}
        with open_index(self._db_path) as conn:
            kijelolheto = (*unnamed_faces(conn), *ignored_faces(conn))
            by_id = {
                face.id: face
                for face in kijelolheto
                if face.rect is not None
            }
        written_ids: list[int] = []
        touched_folders: set[str] = set()
        #: #1403: az érintett FOTÓK (nem mappák) — ezekhez írjuk ki az XMP-t
        written_paths: list[str] = []
        all_ok = True
        for face_id in ids:
            face = by_id.get(face_id)
            if face is None:
                all_ok = False
                continue
            # J1: a kereten túllógó arc keretét a rect64 tartományára vágjuk
            left, top, right, bottom = quantize_rect(face.rect)
            written = self._faces_helper.addFace(
                str(face.photo_path), left, top, right, bottom, clean_name
            )
            if written:
                written_ids.append(face_id)
                touched_folders.add(str(face.photo_path.parent))
                written_paths.append(str(face.photo_path))
            else:
                all_ok = False
        if written_ids:
            with open_index(self._db_path) as conn:
                mark_faces_named(conn, written_ids, clean_name)
                # a `people_in_index` a `folders.has_ini` alapján dönt,
                # melyik mappa `.picasa.ini`-jét olvassa (ld.
                # `index/people.py`) — az ÚJONNAN írt ini (első névadás egy
                # eddig ini nélküli mappában) e nélkül csak a KÖVETKEZŐ
                # háttér-szinkronnál látszana. A `photo_ops_controller`
                # mintáját követve azonnal újraszinkronizáljuk az érintett
                # mappákat, hogy az Emberek-gyűjtemény rögtön frissüljön.
                enabled_filetypes = load_enabled_filetypes(self._settings)
                for folder in touched_folders:
                    if enabled_filetypes is None:
                        sync_tree(conn, folder)
                    else:
                        sync_tree(
                            conn, folder, enabled_filetypes=enabled_filetypes
                        )
                conn.commit()
            self.unnamedCountChanged.emit()
            self._irj_xmp_ha_kell(written_paths)
        return all_ok and bool(written_ids)


    @Slot(result=bool)
    def persistFaceToFile(self) -> bool:  # noqa: N802 — QML-slot-stílus
        """Az arcnév XMP-oldalkocsiba írásának beállítása."""
        return self._beallitas_bool(self.XMP_ON_NAME_KEY, True)


    @Slot(bool)
    def setPersistFaceToFile(self, enabled: bool) -> None:  # noqa: N802 — QML-slot-stílus
        """Az arcnév XMP-oldalkocsiba írásának beállítása."""
        self._settings.setValue(self.XMP_ON_NAME_KEY, bool(enabled))


    def _xmp_iras_bekapcsolva(self) -> bool:
        return self.persistFaceToFile()


    def _irj_xmp_ha_kell(self, utak) -> None:
        """Az elnevezett arcok fotóihoz XMP-sidecar (#1403).

        Az eredeti az arc elnevezése után MAGÁTÓL kiírja az arc-adatot
        (`0x004852e0`, alapérték BE) — ez a parancs második belépési pontja a
        menüpont mellett. A csak olvasható fájl megnevezett hibaeset, ezért a
        hibát jelezzük, de a többi fotót megírjuk."""
        if not utak or not self._xmp_iras_bekapcsolva():
            return
        for ut in dict.fromkeys(utak):
            try:
                export_sidecar_for_photo(Path(ut))
            except OSError as hiba:
                self.xmpAutoWriteFailed.emit(f"{Path(ut).name}: {hiba}")
