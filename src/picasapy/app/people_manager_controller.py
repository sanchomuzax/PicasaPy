from dataclasses import replace
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import Slot

from picasapy.index import all_photos, open_index
from picasapy.ini import (
    UNIDENTIFIED_CONTACT,
    Contact,
    ContactNameResolver,
    ContactXmlEntry,
    contacts_of,
    central_contacts_path,
    load_contacts_xml,
    parse_faces,
    save_contacts_xml,
    with_contact,
    without_contact,
    without_face,
)
from picasapy.scanner import PICASA_INI_NAME

from .people_controller_compat import (
    WRITE_ERRORS as _WRITE_ERRORS,
    generate_contact_id,
    load_ini as _load_ini,
    update_document,
)
from .people_name_matching import filter_and_sort_people


class PeopleManagerMixin:
    """A People-kezelő és a névjavaslat-cache felelőssége."""

    @Slot()
    def prepareNameSuggestions(self) -> None:  # noqa: N802
        """A csempe-javaslatok közös névjegy-cache-ét tölti fel.

        A QML a Név nélküliek nézet megnyitásakor hívja, így az első
        leütéskor már csak a memóriabeli listát kell szűrnie.
        """
        if getattr(self, "_people_manager_contacts_cache", None) is None:
            self._people_manager_contacts_cache = tuple(
                self._build_people_manager_contacts()
            )

    @Slot(str, result="QVariantList")
    def nameSuggestions(self, prefix: str) -> list[dict]:  # noqa: N802
        """Bináris névszavas javaslatok a már betöltött cache-ből.

        Ez a leütésenként hívott út szándékosan nem tölti fel a cache-t és
        nem érinti a tárolót. A nézet megnyitásakor a
        `prepareNameSuggestions()` készíti elő az adatot.
        """
        needle = str(prefix or "").strip()
        if not needle:
            return []
        contacts = getattr(self, "_people_manager_contacts_cache", None)
        if contacts is None:
            return []
        return [
            dict(contact)
            for contact in filter_and_sort_people(contacts, needle)
        ]

    @Slot("QVariantList", str, result="QVariantList")
    def filterPeopleManagerEntries(self, entries, typed: str):  # noqa: N802
        """A People-ablak keresője is ugyanazt az egyezést és sorrendet kéri."""
        return [
            dict(entry)
            for entry in filter_and_sort_people(entries or (), typed)
        ]

    @Slot(result="QVariantList")
    def peopleManagerContacts(self) -> list[dict]:  # noqa: N802
        """A központi névjegytár és a mappák kontaktjainak gyorsítótárazott
        uniója.

        A People-kezelő és a csempe-javaslatok ugyanazt az egy példányt
        használják. A visszatérő sorok másolatai nem engedik, hogy egy QML
        fogyasztó módosítsa a közös cache-t.
        """
        self.prepareNameSuggestions()
        return [
            dict(contact)
            for contact in self._people_manager_contacts_cache
        ]

    def _build_people_manager_contacts(self) -> list[dict]:
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
        resolver = ContactNameResolver(self._people_contacts_path())
        central_contacts = resolver.central_contacts
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

        for folder_path, folder_photos in by_folder.items():
            try:
                document = _load_ini(Path(folder_path) / PICASA_INI_NAME)
            except (OSError, ValueError):
                continue
            contacts = tuple(
                contact
                for contact in contacts_of(document)
                if contact.name
                and contact.person_id.casefold() != UNIDENTIFIED_CONTACT
            )
            resolved_names = resolver.names_by_id(document)
            names = {
                person_id: name
                for person_id, name in resolved_names.items()
                if name and person_id != UNIDENTIFIED_CONTACT
            }
            for contact in contacts:
                name = names.get(contact.person_id.casefold(), contact.name)
                key = name.casefold()
                row = contacts_by_name.setdefault(
                    key,
                    {
                        "name": name,
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
                    names[face.contact_id.casefold()].casefold()
                    for face in faces
                    if face.is_identified
                    and face.contact_id.casefold() in names
                }
                for name in names_on_photo:
                    contacts_by_name[name]["photoCount"] += 1

        contacts = sorted(
            contacts_by_name.values(), key=lambda contact: contact["name"].casefold()
        )
        thumbnail_urls = {}
        if hasattr(self, "_people"):
            thumbnail_urls = {
                person["name"].casefold(): person["thumbUrl"]
                for person in self.people
            }
        for contact in contacts:
            contact["thumbUrl"] = thumbnail_urls.get(
                contact["name"].casefold(), ""
            )
        return contacts

    def _invalidate_people_manager_contacts_cache(self) -> None:
        """Névjegy-, arcadat- vagy mappa-frissítés után újraépíti a cache-t.

        Csak akkor olvas újra, ha a cache-t már használtuk; így az indulás
        nem kap újabb, szükségtelen ini-söprést. A `peopleChanged` a
        betöltött People-lista, a `syncFinished` a mappák újraolvasásának
        meglévő jelzése.
        """
        was_loaded = getattr(self, "_people_manager_contacts_cache", None) is not None
        self._people_manager_contacts_cache = None
        if was_loaded:
            self.prepareNameSuggestions()

    def _people_contacts_path(self) -> Path:
        """A PicasaPy központi tárának contacts/contacts.xml fájlja."""
        return central_contacts_path(self._db_path)

    @Slot("QVariantList", result=bool)
    def savePeopleManagerChanges(self, changes) -> bool:  # noqa: N802
        """A kontaktmódosítások kiírása `[Contacts2]`/`faces=` sorokba.

        Az Új személyt a központi tárba menti; a névváltoztatás a központi
        bejegyzések mellett csak az érintett mappák `[Contacts2]` sorait
        frissíti, így az arckapcsolatok id-je megmarad. A törlés a központi
        bejegyzést, valamint az érintett mappák névjegyeit és `faces=`
        hivatkozásait távolítja el. A `remove_album` csak az album arcait
        törli; a névjegyet megtartja. Mappánként egy útvonalanként
        szerializált, best-effort konkurenciakezelésű ini-frissítés történik.
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
            if action not in {"create", "update", "delete", "remove_album"}:
                return False
            if action in {"delete", "remove_album"}:
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
                    person_id = generate_contact_id()
                    while person_id.casefold() in used_ids:
                        person_id = generate_contact_id()
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
                        person_id = generate_contact_id()
                        while person_id.casefold() in used_ids:
                            person_id = generate_contact_id()
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
                elif action == "delete":
                    kept = [c for c in entries if c.name.casefold() != old_key]
                    changed_central |= len(kept) != len(entries)
                    entries = kept

            if changed_central:
                save_contacts_xml(central_path, tuple(entries))

            # #4887: az átnevezés/törlés a rejtett mappák ini-jébe is írjon —
            # ez nem megjelenítés, a név különben ott elavulna
            with open_index(self._db_path) as conn:
                photos = all_photos(conn, include_hidden_folders=True)
            by_folder: dict[str, list] = {}
            for photo in photos:
                by_folder.setdefault(photo.folder_path, []).append(photo)

            for folder_path, _folder_photos in sorted(by_folder.items()):
                ini_path = Path(folder_path) / PICASA_INI_NAME
                try:
                    current = _load_ini(ini_path)
                except (OSError, ValueError):
                    continue
                if not any(
                    contact.name.casefold()
                    == change["oldName"].casefold()
                    for contact in contacts_of(current)
                    for change in tiszta_valtozasok
                    if change["action"] in {"update", "delete", "remove_album"}
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
                        if action == "remove_album":
                            continue
                        for contact in matches:
                            document = without_contact(document, contact.person_id)
                    return document

                update_document(ini_path, mutate, backup=True)
        except (*_WRITE_ERRORS, OSError, ValueError) as error:
            self.syncFailed.emit(str(error))
            return False

        self._reload_after_sync()
        self._invalidate_people_manager_contacts_cache()
        return True
