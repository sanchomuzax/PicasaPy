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
import time
from pathlib import Path

from PySide6.QtCore import Property, QLocale, Signal, Slot

from picasapy.index import (
    all_photos,
    open_index,
    photo_by_id,
    person_thumbnail_face,
    person_thumbnails,
    set_person_thumbnail,
    unnamed_faces_for_photos,
)
from picasapy.index.faces_detected import (
    faces_for_photo,
    suggested_album_photos,
    suggested_faces_for,
)
from picasapy.index.people import (
    PEOPLE_SORT_MODES,
    PersonRecord,
    people_in_index,
    person_movie_photos,
    person_photos,
    rendezd_szemelyeket,
)
from picasapy.ini import (
    UNIDENTIFIED_CONTACT,
    Contact,
    ContactNameResolver,
    IniConflictError,
    IniSaveError,
    ContactXmlEntry,
    contacts_of,
    central_contacts_path,
    ensure_contact,
    find_contact_id,
    generate_contact_id,
    load_contacts_xml,
    ini_source_path,
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
from .face_ignore_ini import ini_faces_of, match_named_regions
from .models import _thumb_url
from .people_name_matching import filter_and_sort_people

from .people_album_controller import PeopleAlbumMixin
from .people_faces_controller import PeopleFacesMixin
from .people_manager_controller import PeopleManagerMixin

# a csillag/album-írás mintája (photo_ops_controller.py): a tartós ütközés
# és a lemezhiba is KEZELT hiba, nem néma adatvesztés
_WRITE_ERRORS = (OSError, IniSaveError, IniConflictError)



def _load_ini(ini_path: Path):
    """Olvasáshoz: a `.picasa.ini`, hiányában a régi `Picasa.ini` (#4819).

    A `load_document` modulszintű név marad (a tesztek ezt számolják)."""
    return load_document(ini_source_path(ini_path) or ini_path)


def _arckep_hivatkozas(person: PersonRecord, saved) -> tuple:
    """A személy arcképének (fotó-azonosító, arc-régió) párja: a mentett
    választás, ha van, különben az első arc (ld. `PersonRecord`).

    Ugyanazt a szabályt használja a bal sáv sora (`people`) és a tálca
    személy-tokenje (#5331), hogy a két kép ne térhessen el."""
    if saved is not None:
        return saved.photo_id, saved.rect
    return person.thumbnail_photo_id, person.thumbnail_rect


__all__ = (
    'Contact',
    'ContactNameResolver',
    'ContactXmlEntry',
    'IniConflictError',
    'IniSaveError',
    'PEOPLE_SORT_MODES',
    'PICASA_INI_NAME',
    'Path',
    'PeopleAlbumMixin',
    'PeopleFacesMixin',
    'PeopleManagerMixin',
    'PeopleMixin',
    'PersonRecord',
    'Property',
    'QLocale',
    'Signal',
    'Slot',
    'UNIDENTIFIED_CONTACT',
    '_WRITE_ERRORS',
    '_arckep_hivatkozas',
    '_load_ini',
    '_thumb_url',
    'all_photos',
    'central_contacts_path',
    'contacts_of',
    'datetime',
    'ensure_contact',
    'faces_for_photo',
    'filter_and_sort_people',
    'find_contact_id',
    'formatting',
    'generate_contact_id',
    'ini_faces_of',
    'ini_source_path',
    'load_contacts_xml',
    'load_document',
    'match_named_regions',
    'open_index',
    'parse_faces',
    'people_in_index',
    'person_movie_photos',
    'person_photos',
    'person_thumbnail_face',
    'person_thumbnails',
    'photo_by_id',
    'rendezd_szemelyeket',
    'replace',
    'save_contacts_xml',
    'set_person_thumbnail',
    'suggested_album_photos',
    'suggested_faces_for',
    'time',
    'unnamed_faces_for_photos',
    'update_document',
    'with_contact',
    'with_reassigned_face',
    'without_contact',
    'without_face',
    'without_face_at_rect',
)

class PeopleMixin(PeopleManagerMixin, PeopleAlbumMixin, PeopleFacesMixin):
    """A bal hasáb Emberek gyűjteménye: a könyvtárban névvel taggelt
    személyek listája, és egy névre kattintva a rá kitaggelt fotók."""

    peopleChanged = Signal()
    # #1608: a NÉZET váltása (mappa ↔ album ↔ személy). Külön jel, mert a
    # `currentPersonName` a nézettől függ, nem az Emberek-LISTÁTÓL — a
    # `peopleChanged`-re kötve a QML-kötés némán elavult (ld. `_init_people`).

    @Property("QVariant", notify=peopleChanged)
    def people(self):
        """A bal hasáb személy-sorai névvel, darabszámmal és arcképpel."""
        # #1767: a rendezés a MEGJELENÍTÉSNÉL történik, nem a
        # begyűjtésnél — az `people_in_index` eredményét a Projektek
        # gyűjtemény is használja (`index/side_pane.py`), és annak a
        # sorrendje nem a hasáb beállításától függ.
        people = rendezd_szemelyeket(self._people, self.peopleSort)
        with open_index(self._db_path) as conn:
            saved = person_thumbnails(conn, (person.name for person in people))
            result = []
            for person in people:
                photo_id, rect = _arckep_hivatkozas(
                    person, saved.get(person.name.casefold())
                )
                photo = photo_by_id(conn, photo_id) if photo_id is not None else None
                result.append(
                    {
                        "name": person.name,
                        "person_id": person.person_id or "",
                        "count": person.photo_count,
                        "thumbUrl": _thumb_url(photo, arc=rect)
                        if photo is not None and rect is not None
                        else "",
                        "headerThumbUrl": _thumb_url(photo)
                        if photo is not None
                        else "",
                    }
                )
        return result

    @Slot(result="QVariantList")
    def personMovieSourceUrls(self):  # noqa: N802 — QML-slot-stílus
        """A nem üres személyalbumok képei a tárolt lista sorrendjében."""
        with open_index(self._db_path) as conn:
            records = person_movie_photos(
                conn,
                self._people,
                central_path=central_contacts_path(self._db_path),
            )
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

    def _szemely_tokenadat(self, conn, name: str) -> tuple:
        """A `name` személy tálca-tokenjének adatai (#5331): darabszám,
        borító-fotó, arc-régió. A bal sáv sorának (`people`) ADATAIT adja
        vissza, így a tálca nem olvassa végig újra az ini-ket minden
        kijelöléskor. A `TrayMixin` hívja, ugyanazon az objektumon.
        `(0, None, None)`, ha a személy nincs a listában."""
        person = next(
            (p for p in self._people if p.name.casefold() == name.casefold()),
            None,
        )
        if person is None:
            return 0, None, None
        saved = person_thumbnails(conn, (name,)).get(name.casefold())
        photo_id, rect = _arckep_hivatkozas(person, saved)
        return person.photo_count, photo_id, rect
