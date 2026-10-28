from pathlib import Path

from PySide6.QtCore import Slot

from picasapy.index import (
    faces_for_photo,
    open_index,
    photo_by_id,
    person_thumbnails,
    unnamed_faces_for_photos,
)
from picasapy.ini import (
    ContactNameResolver,
    central_contacts_path,
    ensure_contact,
    find_contact_id,
    parse_faces,
    with_reassigned_face,
    without_face_at_rect,
)
from picasapy.scanner import PICASA_INI_NAME

from .face_ignore_ini import ini_faces_of, match_named_regions
from .models import _thumb_url
from .people_controller_compat import (
    WRITE_ERRORS as _WRITE_ERRORS,
    generate_contact_id,
    load_ini as _load_ini,
    update_document,
)


class PeopleFacesMixin:
    """A kijelölt fotók Emberek- és névtelenarc-adatai."""

    @Slot(list, result="QVariantList")
    def peopleOfRows(self, rows):  # noqa: N802 — QML-slot-stílus
        """A megadott sorokon NÉVVEL szereplő emberek: `[{name, count,
        photo_id, rect, thumbUrl}]`.

        A `count` azt mondja, a kijelölés hány képén szerepel az illető; a
        főnézetben minden rekord egy megjelenő személy-sort ad a panelnek
        (#4045). Több fotón előforduló személynél az első kijelölt fotó
        arcát használjuk az ikonképhez."""
        people: dict[str, dict] = {}
        # ⚠️ #1146: MAPPÁNKÉNT olvasunk ini-t, nem képenként. A régi ág
        # soronként hívott `load_document()`-et — 2 002 soros kijelölésnél
        # 6 006 ini-beolvasás egyetlen billentyűleütésre, hálózati
        # megosztáson mindegyik egy-egy hálózati kör.
        dokumentumok: dict[str, object | None] = {}
        resolver = self._people_name_resolver()
        for photo in self._rows_to_photos(rows):
            folder = Path(photo.folder_path)
            kulcs = str(folder)
            if kulcs not in dokumentumok:
                try:
                    dokumentumok[kulcs] = _load_ini(folder / PICASA_INI_NAME)
                except OSError:
                    dokumentumok[kulcs] = None
            document = dokumentumok[kulcs]
            if document is None:
                continue
            names = resolver.names_by_id(document)
            section = document.section(photo.name)
            raw = section.get("faces") if section is not None else None
            if not raw:
                continue
            try:
                faces = parse_faces(raw)
            except ValueError:
                continue
            on_photo = {}
            for face in faces:
                name = names.get(face.contact_id.casefold())
                if face.is_identified and name and name not in on_photo:
                    on_photo[name] = face
            for name, face in on_photo.items():
                entry = people.setdefault(
                    name,
                    {
                        "name": name,
                        "count": 0,
                        "photo_id": photo.id,
                        "rect": None,
                        "thumbUrl": "",
                    },
                )
                entry["count"] += 1
                if entry["rect"] is None:
                    rect = (
                        face.rect.left,
                        face.rect.top,
                        face.rect.right,
                        face.rect.bottom,
                    )
                    entry["photo_id"] = photo.id
                    entry["rect"] = list(rect)
                    entry["thumbUrl"] = _thumb_url(photo, arc=rect)
        result = [
            person
            for person in sorted(
                people.values(),
                key=lambda entry: (-entry["count"], entry["name"].casefold()),
            )
        ]
        if result:
            with open_index(self._db_path) as conn:
                saved = person_thumbnails(
                    conn, (person["name"] for person in result)
                )
                for person in result:
                    thumbnail = saved.get(person["name"].casefold())
                    if thumbnail is None:
                        continue
                    photo = photo_by_id(conn, thumbnail.photo_id)
                    if photo is None:
                        continue
                    person["photo_id"] = thumbnail.photo_id
                    person["rect"] = list(thumbnail.rect)
                    person["thumbUrl"] = _thumb_url(photo, arc=thumbnail.rect)
        return result

    def _people_name_resolver(self) -> ContactNameResolver:
        """Közös feloldó; könnyű, DB nélküli tesztgazdánál csak a mappát nézi."""
        db_path = getattr(self, "_db_path", None)
        central_path = central_contacts_path(db_path) if db_path is not None else None
        return ContactNameResolver(central_path)

    @Slot(list, result="QVariantList")
    def unnamedFacesOfRows(self, rows):  # noqa: N802 — QML-slot-stílus
        """A kijelölt fotók saját, még névtelen arcai a jobb oldali panelhez.

        A névadás és mellőzés meglévő `FaceScanController`-műveleteihez
        szükséges `faceId`-t és a közös bélyegkép-szolgáltató URL-jét adja.
        A fotó sorrendje a kijelölést követi, az azonos fotón lévő arcoké
        felülről, majd balról lefelé determinisztikus.
        """
        photos = self._rows_to_photos(rows)
        by_id = {photo.id: photo for photo in photos}
        if not by_id:
            return []
        photo_order = {photo.id: index for index, photo in enumerate(photos)}
        with open_index(self._db_path) as conn:
            faces = unnamed_faces_for_photos(conn, by_id)
            ordered_faces = sorted(
                faces,
                key=lambda item: (
                    photo_order[item.photo_id],
                    item.rect[1] if item.rect else 1.0,
                    item.rect[0] if item.rect else 1.0,
                    item.id,
                ),
            )
            faces_by_photo = {}
            ini_cache = {}
            matched_named_ids = set()
            for face in ordered_faces:
                if face.rect is not None:
                    faces_by_photo.setdefault(face.photo_path, []).append(face)
            for photo_path, photo_faces in faces_by_photo.items():
                ini_faces = ini_faces_of(photo_path, ini_cache)
                all_index_faces = faces_for_photo(conn, photo_faces[0].photo_id)
                matches = match_named_regions(
                    (
                        (face.id, face.rect)
                        for face in all_index_faces
                        if face.rect is not None
                        and face.state in {"unnamed", "named"}
                    ),
                    ini_faces,
                )
                matched_named_ids.update(matches)

        result = []
        for face in ordered_faces:
            photo = by_id.get(face.photo_id)
            if photo is None or face.rect is None:
                continue
            if face.id in matched_named_ids:
                continue
            result.append(
                {
                    "faceId": face.id,
                    "photo_id": face.photo_id,
                    "rect": list(face.rect),
                    "thumbUrl": _thumb_url(photo, arc=face.rect),
                    "suggestedName": face.suggested_name or "",
                }
            )
        return result

    def _refresh_people_view(self, mode: str, param: str) -> bool:
        """A `_refresh_view()` "person" ágának kiszervezett teste — igazat ad
        vissza, ha kezelte a módot (a hívó `elif`-lánca ez alapján dönt)."""
        if mode != "person":
            return False
        self._szemely_betoltese(param)
        return True

    @staticmethod
    def _person_faces(document, photo_name: str, contact_id: str):
        """Az adott kontakthoz tartozó arc-régiók egy fotón.

        Hiányzó/sérült `faces=`-nél üres — a #301-elv szerint idegen adat nem
        szökhet ki kivétellel."""
        section = document.section(photo_name)
        raw = section.get("faces") if section is not None else None
        if not raw:
            return ()
        try:
            faces = parse_faces(raw)
        except ValueError:
            return ()
        wanted = contact_id.casefold()
        return tuple(
            face.rect
            for face in faces
            if face.is_identified and face.contact_id.casefold() == wanted
        )

    def _rewrite_person_faces(self, rows, person: str, new_name: str | None) -> bool:
        """Az adott személy arc-címkéinek átírása a kijelölt képeken.

        `new_name is None` esetén a régió TÖRLŐDIK (az eredeti „Eltávolítás
        az Emberek albumból" is az arcot veszi le, nem csak a nevet);
        egyébként a régió marad, csak másik névhez kerül.

        Mappánként EGY ini-írás (a `clearAllEffectsMany` mintája), így egy
        nagy kijelölés sem ír fájlonként újra és újra.
        """
        if not person:
            return False
        by_folder: dict[str, list[str]] = {}
        for photo in self._rows_to_photos(rows):
            by_folder.setdefault(photo.folder_path, []).append(photo.name)
        if not by_folder:
            return False

        for folder, names in by_folder.items():
            def mutate(document, names=names, person=person, new_name=new_name):
                # a forrás-kontakt EBBEN a dokumentumban (mappánként más
                # azonosító tartozhat ugyanahhoz a névhez — a Picasa is így
                # tárol); ha nincs, ebben a mappában nincs mit átírni
                source_id = find_contact_id(document, person)
                if source_id is None:
                    return document
                target_id = None
                if new_name:
                    target_id = find_contact_id(document, new_name)
                    if target_id is None:
                        target_id = generate_contact_id()
                        document = ensure_contact(document, target_id, new_name)
                for photo_name in names:
                    for rect in self._person_faces(document, photo_name, source_id):
                        if target_id is not None:
                            document = with_reassigned_face(
                                document, photo_name, rect, target_id
                            )
                        else:
                            document = without_face_at_rect(
                                document, photo_name, rect
                            )
                return document

            try:
                update_document(
                    Path(folder) / PICASA_INI_NAME, mutate, backup=True
                )
            except _WRITE_ERRORS as error:
                # Az AppController `syncFailed` jelzését a Main.qml már a
                # látható globális hibasávra köti. Külön jelzés itt csak
                # néma zsákutca volt (#1003).
                self.syncFailed.emit(str(error))
                return False
        self._refresh_view()
        return True

    @Slot(list, str, result=bool)
    def removePersonFromRows(self, rows, person: str) -> bool:
        """„Eltávolítás az Emberek albumból" (#422): az adott személy
        arc-címkéje (a régióval együtt) lekerül a kijelölt képekről."""
        return self._rewrite_person_faces(rows, person, None)

    @Slot(list, str, str, result=bool)
    def movePersonOnRows(self, rows, person: str, new_name: str) -> bool:
        """„Áthelyezés új személyhez…" (#422): az adott személy arc-címkéje
        a kijelölt képeken ÁTKERÜL a megadott névre — a régió változatlan.

        Üres új névnél no-op (a hívó dialógus üres nevet nem enged; ez a
        nem-UI hívók védőkorlátja)."""
        if not new_name.strip():
            return False
        return self._rewrite_person_faces(rows, person, new_name.strip())
