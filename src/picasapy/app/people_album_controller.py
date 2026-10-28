import time
from pathlib import Path

from PySide6.QtCore import Property, QLocale, Signal, Slot

from picasapy.index import (
    open_index,
    person_thumbnail_face,
    set_person_thumbnail,
)
from picasapy.index.faces_detected import (
    suggested_album_photos,
    suggested_faces_for,
)
from picasapy.index.people import people_in_index, person_photos
from picasapy.ini import central_contacts_path
from picasapy.scanner import PICASA_INI_NAME

from . import formatting
from .models import _thumb_url
from .people_controller_compat import load_ini as _load_ini


class PeopleAlbumMixin:
    """A személyalbum, az arc-kivágás és a borítókép felelőssége."""

    # A személyalbum QML-tulajdonságainak értesítő jele (#1608).
    personViewChanged = Signal()

    def _init_people(self) -> None:
        """A konstruktorból hívandó kezdeti állapot (a `people` mezőé)."""
        self._people: tuple = ()
        self._people_manager_contacts_cache: tuple[dict, ...] | None = None
        #: #2187: a javaslat-szűrő (`sug_filter`) állapota. Nézetenként
        #: NEM tartjuk meg: a személy-album minden megnyitása a teljes
        #: listával indul, ahogy az eredeti fejléce is.
        self._csak_javaslatok = False
        #: #2187: az arc ↔ teljes kép nagyításváltó (`face_zoom` ↔
        #: `picture_zoom`) állása. A javaslat-szűrővel ellentétben a NÉZET
        #: beállítása, nem az albumé: a következő személy-album is így nyílik.
        #: A #5330 Picasa 3.9 referenciaképe a teljes képes módot mutatja.
        self._arc_nagyitas = False
        self._szemely_arc_rects: dict[int, tuple] = {}
        #: a személy-album legutóbb betöltött sorai: az arcsáv és a váltó
        #: ezekből dolgozik új index-olvasás nélkül
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
        # A side-pane betöltésének/újrarendezésének és a mappák
        # újraolvasásának jelzései érvénytelenítik a névjegy-pillanatképet.
        people_changed = getattr(self, "peopleChanged", None)
        if people_changed is not None:
            people_changed.connect(self._invalidate_people_manager_contacts_cache)
        sync_finished = getattr(self, "syncFinished", None)
        if sync_finished is not None:
            sync_finished.connect(self._invalidate_people_manager_contacts_cache)

    def _load_people(self, conn) -> None:
        """CSAK az Emberek-lista frissítése, saját ini-söpréssel.

        ⚠️ #1601: a `_reload()` már NEM ezt hívja, hanem a
        `SidePaneMixin._load_side_pane`-t — az a Projektek gyűjteménnyel
        KÖZÖS, egyetlen `.picasa.ini`-söprésből állítja elő mindkettőt (a
        két külön hívás minden ini-t kétszer olvasott végig). Ez a metódus
        akkor való, ha tényleg csak az Emberek lista változott."""
        self._people = people_in_index(
            conn, central_path=central_contacts_path(self._db_path)
        )
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

    @Property(str, notify=personViewChanged)
    def currentPersonName(self):
        """Az aktív személy neve (a bal hasáb kijelöléséhez) — a
        `currentAlbumToken` mintájára, a jelzése is (ld. `_init_people`)."""
        mode, param = self._view_mode
        return param if mode == "person" else ""

    def _szemely_betoltese(self, name: str) -> None:
        """A személy-album rácsának feltöltése a szűrő MOSTANI állása
        szerint (#2187). A `showPerson` és a javaslat-szűrő közös útja."""
        started = time.perf_counter()
        with open_index(self._db_path) as conn:
            javaslatok = suggested_album_photos(conn, name)
            if self._csak_javaslatok:
                person_records = javaslatok
            else:
                person_records = self._osszefuzve(
                    person_photos(
                        conn, name, central_path=central_contacts_path(self._db_path)
                    ),
                    javaslatok,
                )
            feed_records = self._feed_records(conn)
        elapsed = time.perf_counter() - started
        self._filter_active = True
        self._filter_status = formatting.filter_status_text(
            person_records, elapsed, QLocale(), formatting.fordit
        )
        self._szemely_rekordok = tuple(person_records)
        self._show(feed_records)
        self._arc_nagyitas_atvezetese(name, person_records)
        # A rács a teljes könyvtári feedet jeleníti meg a személyfotók külön
        # arcsávja alatt, az állapotsor viszont továbbra is a személyalbumot
        # írja le.
        self._status = formatting.status_text(
            person_records, QLocale(), formatting.fordit, self.tr
        )
        self.statusChanged.emit()
        self.personViewChanged.emit()

    @Property("QVariantList", notify=personViewChanged)
    def personAlbumPhotos(self):
        """A személyfotók aktuális bélyegképei, a teljes feed soraihoz kötve."""
        modell = getattr(self, "_photos", None)
        if modell is None:
            return []
        result = []
        for photo in getattr(self, "_szemely_rekordok", ()):
            row = modell.rowOfPath(str(Path(photo.folder_path) / photo.name))
            if row >= 0:
                item = modell.itemAt(row)
                item["row"] = row
                if self._arc_nagyitas:
                    rect = self._szemely_arc_rects.get(photo.id)
                    if rect is not None:
                        item["thumbUrl"] = _thumb_url(photo, arc=rect)
                result.append(item)
        return result

    @Slot(int, str, result=bool)
    def canSetPersonThumbnail(self, photo_id: int, person_name: str) -> bool:  # noqa: N802
        """Csak az aktuális személy arcát tartalmazó fotó választható."""
        if (
            not person_name
            or self.currentPersonName.casefold() != person_name.strip().casefold()
        ):
            return False
        with open_index(self._db_path) as conn:
            return person_thumbnail_face(conn, person_name, photo_id) is not None

    @Slot(int, str, result=bool)
    def setPersonThumbnail(self, photo_id: int, person_name: str) -> bool:  # noqa: N802
        """A jelenlegi személy albumképének beállítása, indexbe mentve."""
        if (
            not person_name
            or self.currentPersonName.casefold() != person_name.strip().casefold()
        ):
            return False
        with open_index(self._db_path) as conn:
            if not set_person_thumbnail(conn, person_name, photo_id):
                return False
            conn.commit()
        self.peopleChanged.emit()
        return True

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
        """A külön arcsáv kivágásait frissíti; a mappa-feed teljes képeket tart."""
        self._szemely_rekordok = tuple(records)
        self._szemely_arc_rects = self._szemely_arc_keretei(name, records)

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
        resolver = self._people_name_resolver()
        for photo in records:
            kulcs = str(photo.folder_path)
            if kulcs not in dokumentumok:
                try:
                    dokumentumok[kulcs] = _load_ini(
                        Path(photo.folder_path) / PICASA_INI_NAME
                    )
                except (OSError, ValueError):
                    dokumentumok[kulcs] = None
            document = dokumentumok[kulcs]
            if document is None:
                continue
            names = resolver.names_by_id(document)
            contact_ids = tuple(
                person_id
                for person_id, resolved_name in names.items()
                if resolved_name.casefold() == name.casefold()
            )
            for contact_id in contact_ids:
                rects = self._person_faces(document, photo.name, contact_id)
                if rects:
                    rect = rects[0]
                    keretek[photo.id] = (
                        rect.left, rect.top, rect.right, rect.bottom
                    )
                    break
        return keretek
