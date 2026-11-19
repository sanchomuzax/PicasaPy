"""FacesHelper: az arc-régiók (#147) QML-hídja — olvasás ÉS írás (#26,
2. kör: az arc-téglalap szerkesztő overlay ezen keresztül ér el).

A néző overlay-je a mentett régiókat a fotó mappájának `.picasa.ini`
`faces=` és `[Contacts2]` adataiból, a még névtelen detektálásokat pedig a
`face` indextáblából kéri le. A névvel mentett ini-régióval átfedő index-
találatot nem adja vissza második, névtelen arcként. A név és az arcmentés
továbbra is az ini API-n keresztül történik.

Az ÍRÁS a csillag/album-mintát követi (`photo_ops_controller.py`,
`ini.io.update_document`): azonos útvonalon soros, az előzetes ellenőrzésig
észlelt Picasa-írás esetén újrajátszott, atomikus, backuppal. A check/save
közti külső írás teljes kizárását nem garantálja. Index-UPDATE NEM kell (a `people.py`
minden híváskor újraolvassa az ini-t), ezért — a csillag/forgatással
ellentétben — nincs szükség háttérszálra/`_run_photo_write`-ra: az
ini-írás önmagában is gyors (kis fájl), a szinkron hívás itt egyszerűbb."""

from __future__ import annotations

import sqlite3
import threading
from pathlib import Path

from PySide6.QtCore import QMetaObject, QObject, Qt, Signal, Slot

from picasapy.ini import (
    UNIDENTIFIED_CONTACT,
    IniConflictError,
    IniSaveError,
    ContactNameResolver,
    central_contacts_path,
    ensure_contact,
    find_contact_id,
    generate_contact_id,
    has_ini_source,
    load_or_empty,
    parse_faces,
    remove_all_face_data,
    reset_all_faces,
    update_document,
    with_backuphash,
    with_face,
    with_reassigned_face,
    without_face,
    without_face_at_rect,
    without_faces,
)
from picasapy.ini.faces import Face
from picasapy.ini.rect64 import Rect64
from picasapy.index import open_index
from picasapy.scanner import PICASA_INI_NAME

from .face_ignore_ini import match_named_regions
from .worker_thread import BackgroundWorkerMixin
import picasapy.halozati_ut as _network_paths

# a csillag/album-írás mintája (photo_ops_controller.py): a tartós
# ütközés is kezelt hiba, nem néma adatvesztés/omlás
_WRITE_ERRORS = (OSError, IniSaveError, IniConflictError)
_NETWORK_INI_LOCK = threading.Lock()
_NETWORK_FACES_LOCK = threading.Lock()


class FacesHelper(BackgroundWorkerMixin, QObject):
    """QML-nek kitett lekérdező/író: fotó-útvonal → arc-régiók."""

    def __init__(self, index_path: str | Path | None = None, parent=None) -> None:
        super().__init__(parent)
        self._index_path = Path(index_path) if index_path is not None else None

    # a szerkesztő overlay ezt figyeli hibaüzenethez (a albumWriteFailed
    # mintája, photo_ops_controller.py)
    faceWriteFailed = Signal(str)
    networkFolderCacheChanged = Signal(str)

    @Slot(str, result="QVariantList")
    def facesFor(self, image_path: str) -> list[dict]:
        """A fotó nevesített ini-arcai és névtelen index-találatai.

        Minden elem: {left, top, right, bottom} relatív [0..1] koordináták
        (rect64) és `name`. Az indexből érkező elem `detected: True` és
        `faceId` mezőt is kap, hogy a néző a DB-n keresztül tudja elmenteni
        a ráírt nevet. A mellőzést (`ffffffffffffffff`) és a nulla
        contact_id-jú ini-bejegyzést kihagyja. Hiányzó ini/szekció/kulcs,
        illetve nem indexelt fotó esetén az adott adatforrásból üres lista
        jön. A hibás egyedi `faces=` bejegyzést a parser önállóan kihagyja."""
        if not image_path:
            return []
        if _network_paths.fajlrendszer_gyoker(image_path) is not None:
            cache = getattr(self, "_network_faces_cache", None)
            if cache is not None and image_path in cache:
                return list(cache[image_path])
            document, path = self._document_for_image_path(image_path)
            if document is not None:
                self._queue_network_faces_result(image_path, document, path)
            return []
        document, path = self._document_for_image_path(image_path)
        ini_faces = []
        named_faces = ()
        if document is not None:
            section = document.section(path.name)
            raw_faces = section.get("faces") if section is not None else None
            if raw_faces:
                try:
                    faces = parse_faces(raw_faces)
                except ValueError:
                    faces = ()
                named_faces = tuple(
                    face
                    for face in faces
                    if face.is_identified
                )
                names = self._contact_name_resolver().names_by_id(document)
                ini_faces = [
                    _face_to_dict(face, names)
                    for face in faces
                    if face.is_identified
                ]
        return ini_faces + self._unnamed_detected_faces(path, named_faces)

    def _queue_network_faces_result(self, image_path, document, path) -> None:
        cache = getattr(self, "_network_faces_cache", None)
        if cache is None:
            cache = self._network_faces_cache = {}
            self._network_faces_pending = set()
            self._network_faces_results = {}
        with _NETWORK_FACES_LOCK:
            if image_path in cache or image_path in self._network_faces_pending:
                return
            self._network_faces_pending.add(image_path)

        def worker() -> None:
            try:
                ini_faces, named_faces = self._faces_from_ini_document(
                    document, path
                )
                result = ini_faces + self._unnamed_detected_faces(
                    path, named_faces
                )
            except Exception:
                result = []
            with _NETWORK_FACES_LOCK:
                self._network_faces_results[image_path] = result
            QMetaObject.invokeMethod(
                self,
                "_apply_network_faces_results",
                Qt.ConnectionType.QueuedConnection,
            )

        self._start_background(
            worker, name="picasapy-network-face-query", busy=False
        )

    def _faces_from_ini_document(self, document, path: Path):
        if document is None:
            return [], ()
        section = document.section(path.name)
        raw_faces = section.get("faces") if section is not None else None
        if not raw_faces:
            return [], ()
        try:
            faces = parse_faces(raw_faces)
        except ValueError:
            faces = ()
        named_faces = tuple(face for face in faces if face.is_identified)
        names = self._contact_name_resolver().names_by_id(document)
        ini_faces = [
            _face_to_dict(face, names) for face in faces if face.is_identified
        ]
        return ini_faces, named_faces

    @Slot()
    def _apply_network_faces_results(self) -> None:
        with _NETWORK_FACES_LOCK:
            results = getattr(self, "_network_faces_results", None)
            if not results:
                return
            self._network_faces_cache.update(results)
            self._network_faces_pending.difference_update(results)
            self._network_faces_results = {}
        for image_path in results:
            self.networkFolderCacheChanged.emit(image_path)

    def _unnamed_detected_faces(
        self,
        image_path: Path,
        named_faces: tuple[Face, ...] = (),
    ) -> list[dict]:
        """A még névtelen, YuNet által felismert arcok a fotó indexsoraiból."""
        if self._index_path is None or not self._index_path.is_file():
            return []
        try:
            with open_index(self._index_path) as conn:
                photo = conn.execute(
                    "SELECT p.id, p.width, p.height FROM photos p "
                    "JOIN folders f ON f.id = p.folder_id "
                    "WHERE f.path = ? AND p.name = ?",
                    (str(image_path.parent), image_path.name),
                ).fetchone()
                if photo is None or not photo["width"] or not photo["height"]:
                    return []
                rows = conn.execute(
                    "SELECT id, rect_left, rect_top, rect_right, rect_bottom, state "
                    "FROM face WHERE photo_id = ? "
                    "ORDER BY id",
                    (photo["id"],),
                )
                detections = []
                for row in rows:
                    rect = (
                        row["rect_left"] / photo["width"],
                        row["rect_top"] / photo["height"],
                        row["rect_right"] / photo["width"],
                        row["rect_bottom"] / photo["height"],
                    )
                    detections.append((row, rect))
                matched = match_named_regions(
                    (
                        (int(row["id"]), rect)
                        for row, rect in detections
                        if row["state"] in {"unnamed", "named"}
                    ),
                    named_faces,
                )
                result = []
                for row, rect in detections:
                    if row["state"] != "unnamed" or int(row["id"]) in matched:
                        continue
                    result.append(
                        {
                            "left": rect[0],
                            "top": rect[1],
                            "right": rect[2],
                            "bottom": rect[3],
                            "name": "",
                            "detected": True,
                            "faceId": int(row["id"]),
                        }
                    )
                return result
        except (OSError, sqlite3.Error, RuntimeError):
            return []

    @Slot(str, result="QVariantList")
    def knownNames(self, image_path: str) -> list[str]:
        """A fotó mappájának `[Contacts2]`-jében ismert nevek, kis-nagybetű-
        tűrően rendezve — a névhozzárendelő mező javaslatlistájának
        (meglévő személy kiválasztása új helyett)."""
        if not image_path:
            return []
        document, _path = self._document_for_image_path(image_path)
        resolver = self._contact_name_resolver()
        names = (
            set(resolver.central_names())
            if document is None
            else set(resolver.names_by_id(document).values())
        )
        return sorted(names, key=str.casefold)

    @Slot(str, float, float, float, float, str, result=bool)
    def addFace(
        self, image_path: str, left: float, top: float, right: float, bottom: float, name: str
    ) -> bool:
        """Új, megnevezett arc-téglalap felvétele.

        Üres vagy szóközös névnél sikeres no-op: a Picasa nem ment névtelen
        kézi négyszöget.
        """
        if not image_path:
            return False
        clean_name = (name or "").strip()
        if not clean_name:
            return True

        def mutate(document, photo_name, rect):
            _document, contact_id = self._resolve_contact_id(document, clean_name)
            return with_face(_document, photo_name, Face(rect=rect, contact_id=contact_id))

        return self._mutate(image_path, mutate, left, top, right, bottom)

    # Szándékosan nem QML-slot: a mellőzés jelét kizárólag a
    # FaceScanController írhatja a felismert arcok elvetésekor (#3670).
    def addIgnoredFace(
        self, image_path: str, left: float, top: float, right: float, bottom: float
    ) -> bool:
        """A mellőzés-jel hozzáadása a megadott régióhoz."""
        return self._mutate(
            image_path,
            lambda document, photo_name, rect: with_face(
                document,
                photo_name,
                Face(rect=rect, contact_id=UNIDENTIFIED_CONTACT),
            ),
            left, top, right, bottom,
        )

    @Slot(str, float, float, float, float, str, result=bool)
    def renameFace(
        self, image_path: str, left: float, top: float, right: float, bottom: float, name: str
    ) -> bool:
        """A meglévő régió átnevezése; üres névnél a régió törlődik.

        Nem létező régiónál no-op (igaz eredménnyel — nem hiba).
        """
        clean_name = (name or "").strip()
        if not clean_name:
            return self._mutate(
                image_path,
                lambda document, photo_name, rect: without_face_at_rect(
                    document, photo_name, rect
                ),
                left, top, right, bottom,
            )

        def mutate(document, photo_name, rect):
            _document, contact_id = self._resolve_contact_id(document, clean_name)
            return with_reassigned_face(_document, photo_name, rect, contact_id)

        return self._mutate(image_path, mutate, left, top, right, bottom)

    @Slot(str, float, float, float, float, result=bool)
    def removeFace(
        self, image_path: str, left: float, top: float, right: float, bottom: float
    ) -> bool:
        """A `(left,top,right,bottom)` régió törlése (a contact_id nem
        számít — `without_face_at_rect`)."""
        return self._mutate(
            image_path,
            lambda document, photo_name, rect: without_face_at_rect(document, photo_name, rect),
            left, top, right, bottom,
        )

    # Szándékosan NEM `@Slot`: ezt csak a `FaceScanController` hívja Pythonból.
    def removeAllFaces(self, image_path: str) -> bool:  # noqa: N802 — QML-slot-stílus
        """A fotó arc-téglalapjainak törlése és backuphash írása (#5848)."""
        return self._mutate(
            image_path,
            lambda document, photo_name, _rect: with_backuphash(
                without_faces(document, photo_name), photo_name
            ),
        )

    def removeAllFaceData(self, image_paths) -> bool:  # noqa: N802 — belső API
        """A könyvtár fotóinak arcadatait törli a mappánkénti ini-fájlokból."""
        return self._mutate_face_folders(image_paths, remove_all_face_data)

    def resetAllFaces(self, image_paths) -> bool:  # noqa: N802 — belső API
        """A névazonosítókat nullázza, a régiókat és a facedata-t megtartja."""
        return self._mutate_face_folders(image_paths, reset_all_faces)

    # Szándékosan NEM `@Slot`: csak a Pythonból hívja a `FaceScanController`
    # (a `kepesseg_or.py` a QML-ből elérhetetlen slotot szakadásnak veszi).
    def removeIgnoredFace(
        self, image_path: str, left: float, top: float, right: float, bottom: float
    ) -> bool:
        """A mellőzés jelének (`faces=rect64(…),ffffffffffffffff`) törlése
        — CSAK a pontos (régió, `ffffffffffffffff`) pár megy (#3670, B3).

        A `removeFace` a keret alapján töröl, a `contact_id`-t nem nézi:
        ha a mellőzött régióra közben névcímke került, azt vinné el. Itt a
        névcímkés bejegyzés érintetlen marad (`ini.without_face`). A keret
        a `.picasa.ini`-ben tárolt, rect64-rácsú érték legyen."""
        return self._mutate(
            image_path,
            lambda document, photo_name, rect: without_face(
                document, photo_name, Face(rect=rect, contact_id=UNIDENTIFIED_CONTACT)
            ),
            left, top, right, bottom,
        )

    # -- belső segédek -----------------------------------------------------

    def _load(self, image_path: str):
        path = Path(image_path)
        ini_path = path.parent / PICASA_INI_NAME
        if not has_ini_source(ini_path):
            return None, path
        return load_or_empty(ini_path), path

    def _document_for_image_path(self, image_path: str):
        """Hálózati mappánál cache-t ad; a hiányt egy worker tölti be."""
        path = Path(image_path)
        folder = str(path.parent)
        if _network_paths.fajlrendszer_gyoker(path) is None:
            return self._load(image_path)
        cache = getattr(self, "_network_ini_documents", None)
        if cache is None:
            cache = self._network_ini_documents = {}
            self._network_ini_pending = set()
            self._network_ini_waiters = {}
            self._network_ini_results = {}
        with _NETWORK_INI_LOCK:
            if folder in cache:
                return cache[folder], path
            self._network_ini_waiters.setdefault(folder, set()).add(image_path)
            if folder not in self._network_ini_pending:
                self._network_ini_pending.add(folder)

                def worker() -> None:
                    ini_path = Path(folder) / PICASA_INI_NAME
                    try:
                        document = (
                            load_or_empty(ini_path)
                            if has_ini_source(ini_path)
                            else None
                        )
                    except (OSError, UnicodeError):
                        document = None
                    with _NETWORK_INI_LOCK:
                        self._network_ini_results[folder] = document
                    QMetaObject.invokeMethod(
                        self,
                        "_apply_network_ini_documents",
                        Qt.ConnectionType.QueuedConnection,
                    )

                self._start_background(
                    worker, name="picasapy-network-face-ini", busy=False
                )
        return None, path

    @Slot()
    def _apply_network_ini_documents(self) -> None:
        with _NETWORK_INI_LOCK:
            results = getattr(self, "_network_ini_results", None)
            if not results:
                return
            self._network_ini_documents.update(results)
            self._network_ini_pending.difference_update(results)
            waiters = {
                path
                for folder in results
                for path in self._network_ini_waiters.pop(folder, ())
            }
            self._network_ini_results = {}
        for path in waiters:
            self.networkFolderCacheChanged.emit(path)

    def _resolve_contact_id(self, document, name: str) -> tuple[object, str]:
        """A `name` személy contact_id-ja EBBEN a dokumentumban — meglévőt
        újrahasznosít (`find_contact_id`), újat csak akkor hoz létre, ha
        nincs ilyen nevű kontakt még (64 bites véletlen hex, a Picasa-
        formátum szerint). A hívó nem üres, levágott nevet ad."""
        clean_name = (name or "").strip()
        resolver = self._contact_name_resolver()
        # A központi névjegy az elsődleges névforrás. A mappa Contacts2
        # bejegyzését viszont csak a korábbi, pontos névegyezéssel használjuk:
        # a teljes names_by_id táblán végzett casefold keresés egy eltérő
        # kis-/nagybetűzésű helyi nevet is ugyanannak venné, így a frissen
        # begépelt név helyett a régi helyi címke maradna a panelen.
        for contact in resolver.central_contacts:
            if contact.name.casefold() == clean_name.casefold():
                return (
                    ensure_contact(document, contact.person_id, contact.name),
                    contact.person_id,
                )
        existing = find_contact_id(document, clean_name)
        if existing is not None:
            return document, existing
        new_id = generate_contact_id()
        return ensure_contact(document, new_id, clean_name), new_id

    def _contact_name_resolver(self) -> ContactNameResolver:
        central_path = (
            central_contacts_path(self._index_path)
            if self._index_path is not None
            else None
        )
        return ContactNameResolver(central_path)

    def _mutate(self, image_path: str, mutate, left=None, top=None, right=None, bottom=None) -> bool:
        """Közös írási keret: szerializált, best-effort `update_document` egyetlen
        atomi mutate-tal (a rekonstrukciós azonosító-lookup ÉS az arc-írás
        együtt, hogy ütközés-újrajátszásnál konzisztens maradjon)."""
        if not image_path:
            return False
        path = Path(image_path)
        ini_path = path.parent / PICASA_INI_NAME
        rect = Rect64(left, top, right, bottom) if left is not None else None

        def do_mutate(document):
            return mutate(document, path.name, rect)

        try:
            update_document(ini_path, do_mutate, backup=True)
        except _WRITE_ERRORS as error:
            self.faceWriteFailed.emit(str(error))
            return False
        return True

    def _mutate_face_folders(self, image_paths, mutate) -> bool:
        """Egy teljes mappa `.picasa.ini`-jét egyszer, az ini API-n át írja."""
        folders = dict.fromkeys(
            str(Path(image_path).parent)
            for image_path in image_paths or ()
            if image_path
        )
        success = True
        for folder in folders:
            ini_path = Path(folder) / PICASA_INI_NAME
            if not has_ini_source(ini_path):
                continue
            try:
                update_document(ini_path, mutate, backup=True)
            except _WRITE_ERRORS as error:
                self.faceWriteFailed.emit(str(error))
                success = False
        return success


def _face_to_dict(face: Face, names: dict[str, str]) -> dict:
    return {
        "left": face.rect.left,
        "top": face.rect.top,
        "right": face.rect.right,
        "bottom": face.rect.bottom,
        "name": names.get(face.contact_id.casefold(), "") if face.is_identified else "",
    }
