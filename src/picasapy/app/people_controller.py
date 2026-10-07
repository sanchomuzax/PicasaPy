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
írás a `faces_helper.py` mintáját követi (`update_document`, útvonalankénti
szerializálással és észlelt változáskor újrapróbálással; atomikus, backuppal),
csak több képre, mappánként egy ini-írással."""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime
import secrets
import time
from pathlib import Path

from PySide6.QtCore import Property, QLocale, Signal, Slot

from picasapy.index import all_photos, open_index, unnamed_faces_for_photos
from picasapy.index.faces_detected import (
    suggested_album_photos,
    suggested_faces_for,
)
from picasapy.index.people import (
    PEOPLE_SORT_MODES,
    people_in_index,
    person_movie_photos,
    person_photos,
    rendezd_szemelyeket,
)
from picasapy.ini import (
    UNIDENTIFIED_CONTACT,
    Contact,
    IniConflictError,
    IniSaveError,
    ContactXmlEntry,
    contacts_of,
    ensure_contact,
    find_contact_id,
    load_contacts_xml,
    load_document,
    parse_faces,
    save_contacts_xml,
    update_document,
    with_contact,
    with_reassigned_face,
    without_contact,
    without_face,
    without_face_at_rect,
)
from picasapy.scanner import PICASA_INI_NAME

from . import formatting
from .models import _thumb_url

# a csillag/album-írás mintája (photo_ops_controller.py): a tartós ütközés
# és a lemezhiba is KEZELT hiba, nem néma adatvesztés
_WRITE_ERRORS = (OSError, IniSaveError, IniConflictError)


class PeopleMixin:
    """A bal hasáb Emberek gyűjteménye: a könyvtárban névvel taggelt
    személyek listája, és egy névre kattintva a rá kitaggelt fotók."""

    peopleChanged = Signal()
    # #1608: a NÉZET váltása (mappa ↔ album ↔ személy). Külön jel, mert a
    # `currentPersonName` a nézettől függ, nem az Emberek-LISTÁTÓL — a
    # `peopleChanged`-re kötve a QML-kötés némán elavult (ld. `_init_people`).
    personViewChanged = Signal()

    @Property("QVariant", notify=peopleChanged)
    def people(self):
        """A bal hasábnak: `[{name, count}, ...]` — LISTA, nem tuple (#232,
        a QML-ben a tuple nem tömb), a `albums` property mintájára."""
        # #1767: a rendezés a MEGJELENÍTÉSNÉL történik, nem a
        # begyűjtésnél — az `people_in_index` eredményét a Projektek
        # gyűjtemény is használja (`index/side_pane.py`), és annak a
        # sorrendje nem a hasáb beállításától függ.
        return [
            {"name": person.name, "count": person.photo_count}
            for person in rendezd_szemelyeket(self._people, self.peopleSort)
        ]

    @Slot(result="QVariantList")
    def personMovieSourceUrls(self):  # noqa: N802 — QML-slot-stílus
        """A nem üres személyalbumok képei a tárolt lista sorrendjében."""
        with open_index(self._db_path) as conn:
            records = person_movie_photos(conn, self._people)
        return [
            formatting.to_file_url(str(Path(record.folder_path) / record.name))
            .toString()
            for record in records
        ]

    @Property(str, notify=peopleChanged)
    def peopleSort(self) -> str:
        """A Személyek lista rendezési módja (#1767).

        Az eredetiben a `Preferences\\peoplesort` őrzi (0 = név,
        1 = darabszám, 2 = Top 10); nálunk `view/peopleSort`. Ismeretlen
        tárolt értékre a NÉV szerinti alapértékre esünk vissza — egy
        elrontott beállításból ne legyen üres hasáb."""
        tarolt = self._get_settings().value("view/peopleSort", "name")
        return tarolt if tarolt in PEOPLE_SORT_MODES else "name"

    @Slot(str)
    def setPeopleSort(self, mode: str) -> None:
        """A három menütétel („Sort People by Name / Amount / Top 10")."""
        if mode not in PEOPLE_SORT_MODES:
            return
        self._get_settings().setValue("view/peopleSort", mode)
        self.peopleChanged.emit()

    @Property(str, notify=personViewChanged)
    def currentPersonName(self):
        """Az aktív személy neve (a bal hasáb kijelöléséhez) — a
        `currentAlbumToken` mintájára, a jelzése is (ld. `_init_people`)."""
        mode, param = self._view_mode
        return param if mode == "person" else ""

    @Slot(result="QVariantList")
    def peopleManagerContacts(self) -> list[dict]:  # noqa: N802
        """A központi névjegytár és a mappák kontaktjainak uniója.

        A központi id mellett a listában minden mappánkénti `[Contacts2]` id
        is megmarad. A mappák között név szerint egyesítünk, mert a helyi id
        eltérhet; az album képszáma a `faces=` hivatkozásokból származik.
        """
        with open_index(self._db_path) as conn:
            photos = all_photos(conn)
        by_folder: dict[str, list] = {}
        for photo in photos:
            by_folder.setdefault(photo.folder_path, []).append(photo)

        contacts_by_name: dict[str, dict] = {}
        central_id_to_name: dict[str, str] = {}
        try:
            central_contacts = load_contacts_xml(self._people_contacts_path())
        except (OSError, ValueError):
            central_contacts = ()
        for contact in central_contacts:
            if not contact.name or not contact.person_id:
                continue
            key = contact.name.casefold()
            row = contacts_by_name.setdefault(
                key,
                {
                    "name": contact.name,
                    "email": "",
                    "contactIds": [],
                    "localContactIds": [],
                    "photoCount": 0,
                },
            )
            if contact.person_id not in row["contactIds"]:
                row["contactIds"].append(contact.person_id)
            central_id_to_name[contact.person_id.casefold()] = key

        for folder_path, folder_photos in by_folder.items():
            try:
                document = load_document(Path(folder_path) / PICASA_INI_NAME)
            except (OSError, ValueError):
                continue
            contacts = tuple(
                contact
                for contact in contacts_of(document)
                if contact.name
                and contact.person_id.casefold() != UNIDENTIFIED_CONTACT
            )
            names: dict[str, str] = {}
            for contact in contacts:
                key = central_id_to_name.get(
                    contact.person_id.casefold(), contact.name.casefold()
                )
                row = contacts_by_name.setdefault(
                    key,
                    {
                        "name": contact.name,
                        "email": "",
                        "contactIds": [],
                        "localContactIds": [],
                        "photoCount": 0,
                    },
                )
                if not row["email"]:
                    row["email"] = contact.email
                if contact.person_id not in row["contactIds"]:
                    row["contactIds"].append(contact.person_id)
                if contact.person_id not in row["localContactIds"]:
                    row["localContactIds"].append(contact.person_id)
                names[contact.person_id.casefold()] = key

            for photo in folder_photos:
                section = document.section(photo.name)
                raw_faces = section.get("faces") if section is not None else None
                if not raw_faces:
                    continue
                try:
                    faces = parse_faces(raw_faces)
                except ValueError:
                    continue
                names_on_photo = {
                    names[face.contact_id.casefold()]
                    for face in faces
                    if face.is_identified
                    and face.contact_id.casefold() in names
                }
                for name in names_on_photo:
                    contacts_by_name[name]["photoCount"] += 1

        return sorted(
            contacts_by_name.values(), key=lambda contact: contact["name"].casefold()
        )

    def _people_contacts_path(self) -> Path:
        """A PicasaPy központi tárának contacts/contacts.xml fájlja."""
        return Path(self._db_path).parent / "contacts" / "contacts.xml"

    @Slot("QVariantList", result=bool)
    def savePeopleManagerChanges(self, changes) -> bool:  # noqa: N802
        """A kontaktmódosítások kiírása `[Contacts2]`/`faces=` sorokba.

        Az Új személyt a központi tárba menti; a névváltoztatás a központi
        bejegyzések mellett csak az érintett mappák `[Contacts2]` sorait
        frissíti, így az arckapcsolatok id-je megmarad. A törlés a központi
        bejegyzést, valamint az érintett mappák névjegyeit és `faces=`
        hivatkozásait távolítja el. Mappánként egy útvonalanként szerializált,
        best-effort konkurenciakezelésű ini-frissítés történik.
        """
        if not changes:
            return True
        tiszta_valtozasok = []
        for change in changes:
            if not isinstance(change, dict):
                return False
            action = str(change.get("action", ""))
            name = str(change.get("name", "")).strip()
            email = str(change.get("email", "")).strip()
            old_name = str(change.get("oldName", "")).strip()
            if action not in {"create", "update", "delete"}:
                return False
            if action == "delete":
                if not old_name:
                    return False
            elif (
                not name
                or not old_name and action == "update"
                or any(char in name or char in email for char in ";\r\n")
            ):
                return False
            tiszta_valtozasok.append(
                {
                    "action": action,
                    "oldName": old_name,
                    "name": name,
                    "email": email,
                }
            )

        if any(
            change["action"] == "create" and change["email"]
            for change in tiszta_valtozasok
        ):
            # A mért központi XML-formátumban nincs e-mail mező; emailt csak
            # olyan személyhez mentünk, akinek van mappabeli Contacts2 sora.
            return False
        email_updates = {
            change["oldName"].casefold()
            for change in tiszta_valtozasok
            if change["action"] == "update" and change["email"]
        }
        if email_updates:
            local_names = {
                row["name"].casefold()
                for row in self.peopleManagerContacts()
                if row["localContactIds"]
            }
            if not email_updates <= local_names:
                return False

        try:
            central_path = self._people_contacts_path()
            entries = list(load_contacts_xml(central_path))
            now = datetime.now().astimezone().isoformat(timespec="seconds")
            changed_central = False
            for change in tiszta_valtozasok:
                action = change["action"]
                old_key = change["oldName"].casefold()
                if action == "create":
                    if any(
                        c.name.casefold() == change["name"].casefold()
                        for c in entries
                    ):
                        continue
                    used_ids = {c.person_id.casefold() for c in entries}
                    person_id = secrets.token_hex(8)
                    while person_id.casefold() in used_ids:
                        person_id = secrets.token_hex(8)
                    entries.append(
                        ContactXmlEntry(
                            person_id=person_id,
                            name=change["name"],
                            modified_time=now,
                            local_contact="1",
                        )
                    )
                    changed_central = True
                elif action == "update":
                    matched = False
                    updated_entries = []
                    for contact in entries:
                        if contact.name.casefold() == old_key:
                            updated_entries.append(
                                replace(
                                    contact,
                                    name=change["name"],
                                    modified_time=now,
                                )
                            )
                            matched = True
                        else:
                            updated_entries.append(contact)
                    if not matched:
                        used_ids = {c.person_id.casefold() for c in entries}
                        person_id = secrets.token_hex(8)
                        while person_id.casefold() in used_ids:
                            person_id = secrets.token_hex(8)
                        updated_entries.append(
                            ContactXmlEntry(
                                person_id=person_id,
                                name=change["name"],
                                modified_time=now,
                                local_contact="1",
                            )
                        )
                    entries = updated_entries
                    changed_central = True
                else:
                    kept = [c for c in entries if c.name.casefold() != old_key]
                    changed_central |= len(kept) != len(entries)
                    entries = kept

            if changed_central:
                save_contacts_xml(central_path, tuple(entries))

            with open_index(self._db_path) as conn:
                photos = all_photos(conn)
            by_folder: dict[str, list] = {}
            for photo in photos:
                by_folder.setdefault(photo.folder_path, []).append(photo)

            for folder_path, _folder_photos in sorted(by_folder.items()):
                ini_path = Path(folder_path) / PICASA_INI_NAME
                try:
                    current = load_document(ini_path)
                except (OSError, ValueError):
                    continue
                if not any(
                    contact.name.casefold()
                    == change["oldName"].casefold()
                    for contact in contacts_of(current)
                    for change in tiszta_valtozasok
                    if change["action"] in {"update", "delete"}
                ):
                    continue

                def mutate(document, changes=tiszta_valtozasok):
                    for change in changes:
                        action = change["action"]
                        if action == "create":
                            # Az új személy még nem albumtag; csak a központi
                            # névjegy jön létre. Az ini-be az első arctagelés
                            # ír majd `[Contacts2]` + `faces=` adatot.
                            continue
                        matches = tuple(
                            contact
                            for contact in contacts_of(document)
                            if contact.name.casefold()
                            == change["oldName"].casefold()
                        )
                        if action == "update":
                            for contact in matches:
                                document = with_contact(
                                    document,
                                    Contact(
                                        person_id=contact.person_id,
                                        name=change["name"],
                                        email=change["email"],
                                        gaia_id=contact.gaia_id,
                                    ),
                                )
                            continue

                        person_ids = {contact.person_id.casefold() for contact in matches}
                        if not person_ids:
                            continue
                        for section in document.file_sections():
                            raw_faces = section.get("faces")
                            if not raw_faces:
                                continue
                            try:
                                faces = parse_faces(raw_faces)
                            except ValueError:
                                continue
                            for face in faces:
                                if face.contact_id.casefold() in person_ids:
                                    document = without_face(document, section.name, face)
                        for contact in matches:
                            document = without_contact(document, contact.person_id)
                    return document

                update_document(ini_path, mutate, backup=True)
        except (*_WRITE_ERRORS, OSError, ValueError) as error:
            self.syncFailed.emit(str(error))
            return False

        self._reload_after_sync()
        return True

    def _init_people(self) -> None:
        """A konstruktorból hívandó kezdeti állapot (a `people` mezőé)."""
        self._people: tuple = ()
        #: #2187: a javaslat-szűrő (`sug_filter`) állapota. Nézetenként
        #: NEM tartjuk meg: a személy-album minden megnyitása a teljes
        #: listával indul, ahogy az eredeti fejléce is.
        self._csak_javaslatok = False
        #: #2187: az arc ↔ teljes kép nagyításváltó (`face_zoom` ↔
        #: `picture_zoom`) állása. A javaslat-szűrővel ellentétben a NÉZET
        #: beállítása, nem az albumé: a következő személy-album is így nyílik.
        #: Alapból a teljes kép — a váltó bevezetése előtti viselkedés.
        self._arc_nagyitas = False
        #: a személy-album legutóbb betöltött sorai — a váltó ezekre számol
        #: keretet, új index-olvasás nélkül
        self._szemely_rekordok: tuple = ()
        # #1608: a `currentPersonName` a NÉZETTEL változik, a `peopleChanged`
        # viszont csak az Emberek-LISTA frissülésekor megy ki
        # (`_load_people`). Emiatt a rá épülő QML-kötések a nézetváltás után
        # NÉMÁN elavultak: a menüsáv és a helyi menü a régi (jellemzően üres)
        # nevet látta, amíg egy háttér-szinkron véletlenül helyre nem tette.
        # A nézetváltás közös jele a `statusChanged`: minden `_show()` végén
        # kimegy (`_update_status`) — ugyanaz, amire a `currentAlbumToken`
        # épül, ezért a kettő ettől kezdve EGYSZERRE frissül.
        # A `getattr` azért kell, mert a mixin ÖNÁLLÓAN is tesztelt egy
        # minimális hoston (`tests/app/test_people_controller.py`), ahol
        # `statusChanged` nincs.
        status_changed = getattr(self, "statusChanged", None)
        if status_changed is not None:
            status_changed.connect(self.personViewChanged)

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
        mappa-kontextus megmarad a `clearFilter`-es visszaváltáshoz.

        #2187: a rács a MEGERŐSÍTETT képek mellett a függő JAVASLATOKAT is
        mutatja — az eredeti személy-albuma is ezekre kínálja a pipát és az
        x-et. A megnyitás mindig a teljes listával indul, a szűrő kikapcsolt
        állapotából."""
        if not name:
            return
        self._view_mode = ("person", name)
        self._csak_javaslatok = False
        self._szemely_betoltese(name)

    def _szemely_betoltese(self, name: str) -> None:
        """A személy-album rácsának feltöltése a szűrő MOSTANI állása
        szerint (#2187). A `showPerson` és a javaslat-szűrő közös útja."""
        started = time.perf_counter()
        with open_index(self._db_path) as conn:
            javaslatok = suggested_album_photos(conn, name)
            if self._csak_javaslatok:
                records = javaslatok
            else:
                records = self._osszefuzve(person_photos(conn, name), javaslatok)
        elapsed = time.perf_counter() - started
        self._filter_active = True
        self._filter_status = formatting.filter_status_text(
            records, elapsed, QLocale(), formatting.fordit
        )
        self._show(records)
        self._arc_nagyitas_atvezetese(name, records)

    @staticmethod
    def _osszefuzve(
        megerositett: tuple, javasolt: tuple
    ) -> tuple:
        """A két halmaz egyesítése úgy, hogy egy kép EGYSZER szerepeljen.

        A rács sora a FOTÓ, nem az arc: ugyanazon a képen lehet a személy
        megerősítve és — egy másik arcon — javasolva is. A sorrend a
        megerősítetteké marad, a javaslatok a végére kerülnek; mindkét
        lekérdezés `f.path, p.name` szerint rendez."""
        latott = {(r.folder_path, r.name) for r in megerositett}
        return megerositett + tuple(
            r for r in javasolt if (r.folder_path, r.name) not in latott
        )

    @Slot()
    def refreshPersonAlbum(self) -> None:  # noqa: N802 — QML-slot-stílus
        """A nyitott személy-album újratöltése a szűrő MOSTANI állásával.

        A jóváhagyás és az elvetés után a rácsnak frissülnie kell (a
        jóváhagyott arc ettől kerül a személy képei közé), de a
        javaslat-szűrő állását ilyenkor megtartjuk — a `showPerson`
        ezzel szemben új albumot nyit, és tiszta lappal indul."""
        mode, param = self._view_mode
        if mode != "person" or not param:
            return
        self._szemely_betoltese(param)

    @Property(bool, notify=personViewChanged)
    def personSuggestionsOnly(self) -> bool:
        """A javaslat-szűrő (`sug_filter`) állása — MÉRT súgó: „Csak a
        javaslatok megjelenítése (ha be van kapcsolva)"."""
        return self._csak_javaslatok

    @Slot(bool)
    def setPersonSuggestionsOnly(self, csak: bool) -> None:  # noqa: N802
        """A javaslat-szűrő átkapcsolása.

        Csak személy-album nézetben hat: máshol nincs mit szűrni, és a
        rácsot sem szabad átírnia. Azonos értékre nem olvas újra indexet —
        a kapcsoló minden átkapcsolása egy teljes ini-söprés."""
        csak = bool(csak)
        mode, param = self._view_mode
        if mode != "person" or not param or csak == self._csak_javaslatok:
            return
        self._csak_javaslatok = csak
        self._szemely_betoltese(param)
        self.personViewChanged.emit()

    @Property(bool, notify=personViewChanged)
    def personFaceZoom(self) -> bool:
        """Az arc-nagyítás (`face_zoom`) állása — MÉRT súgók: „Megjelenítés
        az arcra közelítve" / „Megjelenítés a teljes képre távolítva"."""
        return self._arc_nagyitas

    @Slot(bool)
    def setPersonFaceZoom(self, arc: bool) -> None:  # noqa: N802
        """Az arc ↔ teljes kép váltó (#2187).

        Csak személy-album nézetben hat: máshol nincs „a személy arca", amire
        közelíteni lehetne. Azonos értékre nem nyúl a rácshoz."""
        arc = bool(arc)
        mode, param = self._view_mode
        if mode != "person" or not param or arc == self._arc_nagyitas:
            return
        self._arc_nagyitas = arc
        self._arc_nagyitas_atvezetese(param, self._szemely_rekordok)
        self.personViewChanged.emit()

    def _arc_nagyitas_atvezetese(self, name: str, records) -> None:
        """A váltó állásának átadása a rács modelljének: arc-módban a sorok
        a személy arcának keretét kapják, különben a teljes kép jön."""
        self._szemely_rekordok = tuple(records)
        modell = getattr(self, "_photos", None)
        if modell is None or not hasattr(modell, "set_face_zoom"):
            return
        if not self._arc_nagyitas:
            modell.set_face_zoom(None)
            return
        modell.set_face_zoom(self._szemely_arc_keretei(name, records))

    def _szemely_arc_keretei(self, name: str, records) -> dict[int, tuple]:
        """`{fotó-azonosító: (bal, fent, jobb, lent)}` a személy arcára.

        A MEGERŐSÍTETT arc a `.picasa.ini` `faces=` sorából jön (a Picasa
        döntése szent, ezért ez nyer), a FÜGGŐ javaslat a saját `face`
        táblánkból. Egy képen több arcnál az első számít. A `.picasa.ini`-t
        mappánként egyszer olvassuk (#1146)."""
        keretek: dict[int, tuple] = {}
        with open_index(self._db_path) as conn:
            for face in suggested_faces_for(conn, name):
                if face.rect is not None:
                    keretek.setdefault(face.photo_id, tuple(face.rect))
        dokumentumok: dict[str, object | None] = {}
        for photo in records:
            kulcs = str(photo.folder_path)
            if kulcs not in dokumentumok:
                try:
                    dokumentumok[kulcs] = load_document(
                        Path(photo.folder_path) / PICASA_INI_NAME
                    )
                except (OSError, ValueError):
                    dokumentumok[kulcs] = None
            document = dokumentumok[kulcs]
            if document is None:
                continue
            contact_id = find_contact_id(document, name)
            if contact_id is None:
                continue
            rects = self._person_faces(document, photo.name, contact_id)
            if rects:
                rect = rects[0]
                keretek[photo.id] = (rect.left, rect.top, rect.right, rect.bottom)
        return keretek

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
        return [
            person
            for person in sorted(
                people.values(),
                key=lambda entry: (-entry["count"], entry["name"].casefold()),
            )
        ]

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

        result = []
        for face in sorted(
            faces,
            key=lambda item: (
                photo_order[item.photo_id],
                item.rect[1] if item.rect else 1.0,
                item.rect[0] if item.rect else 1.0,
                item.id,
            ),
        ):
            photo = by_id.get(face.photo_id)
            if photo is None or face.rect is None:
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
        with open_index(self._db_path) as conn:
            records = person_photos(conn, param)
        self._show(records)
        #: #2187: az új tartalom törli a modell arc-kereteit — újra kell adni
        self._arc_nagyitas_atvezetese(param, records)
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
