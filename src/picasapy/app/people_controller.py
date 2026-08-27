"""#26: az „Emberek" gyűjtemény — controller-szelet (a `custom_collections_
controller`/`showAlbum` mintáját követő mixin, #150).

Mixin-osztály: a végleges `AppController` örökli majd (a bekötés — az
öröklés-lista bővítése és az `_reload()`/`_refresh_view()`-beli "people"
nézetmód-ág felvétele a `controller.py`-ban — FORRÓ fájl, az integrátor
dolga, ld. jelentés). A személy-választás a `showAlbum` mintáját követi:
szűrt nézet, a mappa-kontextus megmarad a `clearFilter`-es visszaváltáshoz.

A #26 1. köre csak OLVASOTT; a #422 4. lépcsőjével két KÖTEGELT írás is
ide került (az Emberek-album kép-szintű parancsai): egy személy arc-
címkéjének levétele, illetve átvitele másik névre a kijelölt képeken. Az
írás a `faces_helper.py` mintáját követi (ütközésbiztos `update_document`,
atomikus, backuppal), csak több képre, mappánként egy ini-írással."""

from __future__ import annotations

import secrets
import time
from pathlib import Path

from PySide6.QtCore import Property, QLocale, Signal, Slot

from picasapy.index import open_index
from picasapy.index.people import people_in_index, people_with, person_photos
from picasapy.ini import (
    IniConflictError,
    IniSaveError,
    contacts_of,
    ensure_contact,
    find_contact_id,
    load_document,
    parse_faces,
    update_document,
    with_reassigned_face,
    without_face_at_rect,
)
from picasapy.scanner import PICASA_INI_NAME

from . import formatting

# a csillag/album-írás mintája (photo_ops_controller.py): a tartós ütközés
# és a lemezhiba is KEZELT hiba, nem néma adatvesztés
_WRITE_ERRORS = (OSError, IniSaveError, IniConflictError)


class PeopleMixin:
    """A bal hasáb Emberek gyűjteménye: a könyvtárban névvel taggelt
    személyek listája, és egy névre kattintva a rá kitaggelt fotók."""

    peopleChanged = Signal()

    @Property("QVariant", notify=peopleChanged)
    def people(self):
        """A bal hasábnak: `[{name, count}, ...]` — LISTA, nem tuple (#232,
        a QML-ben a tuple nem tömb), a `albums` property mintájára."""
        return [
            {"name": person.name, "count": person.photo_count}
            for person in self._people
        ]

    @Property(str, notify=peopleChanged)
    def currentPersonName(self):
        """Az aktív személy neve (a bal hasáb kijelöléséhez) — a
        `currentAlbumToken` mintájára."""
        mode, param = self._view_mode
        return param if mode == "person" else ""

    def _init_people(self) -> None:
        """A konstruktorból hívandó kezdeti állapot (a `people` mezőé)."""
        self._people: tuple = ()

    def _load_people(self, conn) -> None:
        """CSAK az Emberek-lista frissítése, saját ini-söpréssel.

        ⚠️ #1601: a `_reload()` már NEM ezt hívja, hanem a
        `SidePaneMixin._load_side_pane`-t — az a Projektek gyűjteménnyel
        KÖZÖS, egyetlen `.picasa.ini`-söprésből állítja elő mindkettőt (a
        két külön hívás minden ini-t kétszer olvasott végig). Ez a metódus
        akkor való, ha tényleg csak az Emberek lista változott."""
        self._people = people_in_index(conn)
        self.peopleChanged.emit()

    @Slot(str)
    def showPerson(self, name: str) -> None:
        """Személy-szűrő be — a `showAlbum` mintáját követi: szűrt nézet, a
        mappa-kontextus megmarad a `clearFilter`-es visszaváltáshoz."""
        if not name:
            return
        self._view_mode = ("person", name)
        started = time.perf_counter()
        with open_index(self._db_path) as conn:
            records = person_photos(conn, name)
        elapsed = time.perf_counter() - started
        self._filter_active = True
        self._filter_status = formatting.filter_status_text(
            records, elapsed, QLocale(), self.tr
        )
        self._show(records)

    @Slot(str, result="QVariantList")
    def peopleWith(self, name: str):  # noqa: N802 — QML-slot-stílus
        """Akik EGYÜTT szerepelnek a megadott személlyel: `[{name, count}]`.

        Az eredeti Emberek-panel negyedik állapota: *„Named People who
        appear WITH the currently selected person will be listed here."* —
        a családi gyűjtemények természetes navigációja („ki van még rajta
        ezeken a képeken?"), onnan egy kattintással a másik személy
        albumába. LISTA, nem tuple (a `people` property mintája)."""
        with open_index(self._db_path) as conn:
            return [
                {"name": person.name, "count": person.photo_count}
                for person in people_with(conn, name)
            ]

    @Slot(list, result="QVariantList")
    def peopleOfRows(self, rows):  # noqa: N802 — QML-slot-stílus
        """A megadott sorokon NÉVVEL szereplő emberek: `[{name, count}]`.

        Az eredeti Emberek-paneljének első szakasza („In this photo:" egy
        képnél, „People in these photos:" többnél). A darabszám itt azt
        mondja, a kijelölés HÁNY képén szerepel az illető."""
        counts: dict[str, int] = {}
        # ⚠️ #1146: MAPPÁNKÉNT olvasunk ini-t, nem képenként. A régi ág
        # soronként hívott `load_document()`-et — 2 002 soros kijelölésnél
        # 6 006 ini-beolvasás egyetlen billentyűleütésre, hálózati
        # megosztáson mindegyik egy-egy hálózati kör.
        dokumentumok: dict[str, object | None] = {}
        for photo in self._rows_to_photos(rows):
            folder = Path(photo.folder_path)
            kulcs = str(folder)
            if kulcs not in dokumentumok:
                try:
                    dokumentumok[kulcs] = load_document(folder / PICASA_INI_NAME)
                except OSError:
                    dokumentumok[kulcs] = None
            document = dokumentumok[kulcs]
            if document is None:
                continue
            names = {
                contact.person_id.casefold(): contact.name
                for contact in contacts_of(document)
                if contact.name
            }
            section = document.section(photo.name)
            raw = section.get("faces") if section is not None else None
            if not raw:
                continue
            try:
                faces = parse_faces(raw)
            except ValueError:
                continue
            on_photo = {
                names[face.contact_id.casefold()]
                for face in faces
                if face.is_identified and face.contact_id.casefold() in names
            }
            for name in on_photo:
                counts[name] = counts.get(name, 0) + 1
        return [
            {"name": name, "count": count}
            for name, count in sorted(
                counts.items(), key=lambda kv: (-kv[1], kv[0].casefold())
            )
        ]

    def _refresh_people_view(self, mode: str, param: str) -> bool:
        """A `_refresh_view()` "person" ágának kiszervezett teste — igazat ad
        vissza, ha kezelte a módot (a hívó `elif`-lánca ez alapján dönt)."""
        if mode != "person":
            return False
        with open_index(self._db_path) as conn:
            self._show(person_photos(conn, param))
        return True

    # -- #422 4. lépcső: az Emberek-album kép-szintű parancsai -------------

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
                        target_id = secrets.token_hex(8)
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
