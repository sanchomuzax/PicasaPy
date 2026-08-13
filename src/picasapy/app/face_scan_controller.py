"""FaceScanController: a SAJÁT (YuNet) arc-detektálás háttérfolyamata és a
„Névtelenek" album QML-hídja (issue #26, javasolt 1. lépcső: „Detektálás +
arc-indexkép (szemvonalra igazítva) → Névtelenek album, csoportosítás
nélkül").

Önálló QObject — a `DedupController`/`FolderTreeController` mintáját
követve NEM az `AppController` mixinje, hogy a `controller.py` (forró
fájl, ld. CONTRIBUTING.md) csak a végleges, minimális bekötést kapja; a
bekötés (öröklés-lista/context-property, Main.qml gomb, a bal hasáb
„Névtelenek" sora) az integrátor feladata — pontosan úgy, ahogy a
`PeopleMixin` is önállóan, host-osztályos teszttel készült (#397), és a
`controller.py`-beli bekötésére vár.

MODELL NÉLKÜL a szkennelés TISZTÁN kikapcsol: a `modelUnavailable` jelzés
megy ki, a meglévő index/alkalmazás-működés érintetlen (ld.
`picasapy.faces.detector` modul-docstringje — a CI-ben nincs garantált
hálózat és a modellfájl nincs jelen).

IMPORTNÁL A PICASA DÖNTÉSEI SZENTEK: a saját detektorunk KIHAGYJA azokat a
fotókat, amelyeken már van EMBER ÁLTAL adott névcímke (`faces=` legalább
egy azonosított bejegyzéssel) — ezeket SOHA nem értékeljük újra.

#26 (2. lépcső): a `computeEmbeddings()` a lenyomat-számítás (SFace) +
csoportosítás KÜLÖN, ALACSONYABB PRIORITÁSÚ sora — a terv szerint „előbb
legyen meg minden arc HELYE, a felismerés ráér”. Ez a metódus SOHA nem fut
automatikusan a `scanForFaces()` részeként — a hívó (a jövőbeli integráció)
dönti el, mikor indítja (pl. a detektálás befejezése UTÁN, üresjáratban).
Modell nélkül ugyanúgy tisztán kikapcsol (`embeddingModelUnavailable`).

#26 (3. lépcső, bekötés): `unnamedGroups()` adja a „Névtelenek" album
CSOPORTOSÍTOTT nézetét (Picasa „Group by face"/„Expand groups"), az
`assignNameToFaces()` pedig a tömeges névadást („Add a name") — a MEGLÉVŐ
`FacesHelper.addFace()` úton, majd a sikeresen megírt arcokat `'named'`
állapotba állítva (`index.mark_faces_named`), hogy se ez az album, se a
jövőbeli csoportosítás ne értékelje újra."""

from __future__ import annotations

import logging
import threading
from pathlib import Path

import cv2
from PySide6.QtCore import Property, QObject, Signal, Slot

from picasapy.cvimage import read_image_bytes, reduced_color_flag
from picasapy.faces.detector import FaceDetector
from picasapy.faces.embedder import FaceEmbedder
from picasapy.index import (
    all_photos,
    faces_missing_embedding,
    ignored_faces,
    group_unnamed_faces,
    mark_faces_ignored,
    set_suggested_name,
    unignore_faces,
    mark_faces_named,
    open_index,
    replace_faces,
    store_embedding,
    sync_tree,
    unnamed_album_photos,
    unnamed_faces,
)
from picasapy.ini import load_document, parse_faces
from picasapy.scanner import PICASA_INI_NAME
from picasapy.scanner.filetypes import VIDEO_EXTENSIONS

from .faces_helper import FacesHelper
from .worker_thread import BackgroundWorkerMixin

_log = logging.getLogger(__name__)

# A detektálás bemenetének célmérete — a thumbs-cache alapértelmezett
# méreténél (256) nagyobb, hogy a kisebb arcok is megtalálhatók legyenek,
# de nem a teljes felbontás (nagy fotóknál ez percekre lassítaná a
# szkennelést). A YuNet kis felbontáson is jól teljesít (issue #26).
_DETECT_MAX_DIMENSION = 960

# Ennyi feldolgozott fotónként commitolunk — a dedup-hash-scan mintáját
# követve (megszakított futás munkája sem vész el, ld. dedup_controller.py).
_COMMIT_BATCH_SIZE = 50

# #26 (3. lépcső): egy csoportban ennyi arcot mutatunk „Expand groups"
# kikapcsolt állapotban — a teljes csoport a bekapcsolt állapotban látszik
# (ld. `unnamedGroups()`). Csak megjelenítési korlát, a kijelölés/névadás
# a NEM mutatott arcokat is eléri (a hívó a mutatott faceId-kat kapja meg,
# tehát ez a korlát a gyakorlatban a kijelölhető halmazt is szűkíti —
# szándékosan: „Expand groups" nélkül a felhasználó a reprezentatív
# részhalmazt nevezi el, ami a Picasa csoport-előnézetének felel meg).
_COLLAPSED_GROUP_PREVIEW = 12


class FaceScanController(BackgroundWorkerMixin, QObject):
    """A „Névtelenek" album feltöltése: saját arc-detektálás háttérszálon,
    majd a találatok lekérdezése a QML-nek."""

    scanStarted = Signal()
    scanProgress = Signal(int, int)  # (kész, összes)
    scanFinished = Signal(int, int)  # (talált arc, átvizsgált fotó)
    scanCancelled = Signal()
    scanFailed = Signal(str)
    # A modell hiányzik/nem tölthető be — a szkennelés el sem indul, ez
    # NEM hiba (a funkció tervezett, hiánytűrő kikapcsolása).
    modelUnavailable = Signal()

    # #26 (2. lépcső): lenyomat-számítás + csoportosítás — a detektálásnál
    # ALACSONYABB PRIORITÁSÚ, KÜLÖN indítható sor (ld. osztály-docstring).
    embeddingStarted = Signal()
    embeddingProgress = Signal(int, int)  # (kész, összes)
    embeddingFinished = Signal(int, int)  # (lenyomatolt arc, csoportba került arc)
    embeddingCancelled = Signal()
    embeddingFailed = Signal(str)
    embeddingModelUnavailable = Signal()

    # #26 (3. lépcső): a „Névtelenek" album mérete változott (szkennelés,
    # csoportosítás, vagy sikeres tömeges névadás után) — a bal hasáb
    # sorának darabszáma ezt figyeli.
    unnamedCountChanged = Signal()

    # #449: a háttér-beolvasás haladása az ALBUMLISTÁBAN jelenik meg
    # („Scanning for faces… %d%% complete"), nem modális ablakban — semmi
    # nem blokkolja a felhasználót. A `scanProgress` jelzés erre kevés: a
    # bal hasáb sorának DEKLARATÍV kötés kell, ezért a százalék NOTIFY-
    # property is (−1 = épp nem fut).
    scanPercentChanged = Signal()

    def __init__(
        self,
        db_path: str | Path,
        detector: FaceDetector | None = None,
        embedder: FaceEmbedder | None = None,
        faces_helper: FacesHelper | None = None,
    ) -> None:
        super().__init__()
        self._db_path = Path(db_path)
        # Tesztben/CI-ben injektálható helyettesítő detektor/embedder is
        # lehet — alapból a valódi (modell nélkül önmagát kikapcsoló)
        # YuNet/SFace-becsomagolás.
        self._detector = detector if detector is not None else FaceDetector()
        self._embedder = embedder if embedder is not None else FaceEmbedder()
        # #26 (3. lépcső): a tömeges névadás EZEN keresztül írja a
        # `faces=`/`[Contacts2]`-t — a MEGLÉVŐ `FacesHelper.addFace()` úton,
        # nem új írási logikával (ld. jegy). `None`-nal is működik (pl. a
        # `unnamedGroups`-ot önmagában tesztelő esetekben) — ekkor
        # `assignNameToFaces` egyszerűen hamis eredményt ad, nem hibázik.
        self._faces_helper = faces_helper
        self._stop_event: threading.Event | None = None
        self._embedding_stop_event: threading.Event | None = None
        #: #449: a futó szkennelés haladása százalékban, −1 ha nem fut
        self._scan_percent = -1

    @Slot(result=bool)
    def isAvailable(self) -> bool:
        """Igaz, ha a modell betöltve, tehát a szkennelés ténylegesen futna."""
        return self._detector.available

    @Slot(result=bool)
    def isEmbeddingAvailable(self) -> bool:
        """Igaz, ha a lenyomat-modell (SFace) betöltve."""
        return self._embedder.available

    @Property(int, notify=scanPercentChanged)
    def scanPercent(self) -> int:  # noqa: N802 — QML-property-stílus
        """A futó arc-beolvasás haladása (0–100), vagy −1, ha nem fut.

        A bal hasáb „Scanning for faces…" sora ezt köti (#449) — modális
        ablak SEHOL, a munka a háttérben marad."""
        return self._scan_percent

    def _set_scan_percent(self, percent: int) -> None:
        if percent != self._scan_percent:
            self._scan_percent = percent
            self.scanPercentChanged.emit()

    @Slot()
    def scanForFaces(self) -> None:
        """A teljes indexelt könyvtár átvizsgálása SAJÁT arc-detektálással.

        Modell hiányában azonnal `modelUnavailable`-t ad és nem indít
        szálat — a hívó UI ekkor a funkciót eleve rejtve/inaktívan
        tarthatja."""
        if not self._detector.available:
            self.modelUnavailable.emit()
            return
        self.cancelScan()
        stop_event = threading.Event()
        self._stop_event = stop_event
        self._set_scan_percent(0)
        self.scanStarted.emit()
        self._start_background(
            self._run_scan, args=(stop_event,), name="picasapy-face-scan"
        )

    @Slot()
    def cancelScan(self) -> None:
        """A folyamatban lévő szkennelés megszakítása mappa/fotó-határon —
        a már elmentett találatok az indexben maradnak."""
        if self._stop_event is not None:
            self._stop_event.set()

    @Slot(result="QVariantList")
    def unnamedAlbum(self) -> list[dict]:
        """A „Névtelenek" album QML-nek: `[{path, name}, ...]` — LISTA, nem
        tuple (a `people`/`albums` property mintája, MEMORY 2026-07-22)."""
        with open_index(self._db_path) as conn:
            records = unnamed_album_photos(conn)
        return [
            {"path": str(Path(record.folder_path) / record.name), "name": record.name}
            for record in records
        ]

    @Property(int, notify=unnamedCountChanged)
    def unnamedCount(self) -> int:
        """A „Névtelenek" album mérete — hány fotón van legalább egy még
        névtelen SAJÁT találat. A bal hasáb sora ezt mutatja (0 esetén a
        sor rejtve marad — modell nélkül ez a szám mindig 0, a szkennelés
        el sem indul, ld. `scanForFaces`)."""
        with open_index(self._db_path) as conn:
            row = conn.execute(
                "SELECT COUNT(DISTINCT photo_id) AS n FROM face WHERE state = 'unnamed'"
            ).fetchone()
        return int(row["n"]) if row is not None else 0

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
            faces = [face for face in unnamed_faces(conn) if face.rect is not None]
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
        album, se a jövőbeli csoportosítás ne lássa többé — az ALAPSZABÁLY
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
            by_id = {face.id: face for face in unnamed_faces(conn) if face.rect is not None}
        written_ids: list[int] = []
        touched_folders: set[str] = set()
        all_ok = True
        for face_id in ids:
            face = by_id.get(face_id)
            if face is None:
                all_ok = False
                continue
            left, top, right, bottom = face.rect
            written = self._faces_helper.addFace(
                str(face.photo_path), left, top, right, bottom, clean_name
            )
            if written:
                written_ids.append(face_id)
                touched_folders.add(str(face.photo_path.parent))
            else:
                all_ok = False
        if written_ids:
            with open_index(self._db_path) as conn:
                mark_faces_named(conn, written_ids)
                # a `people_in_index` a `folders.has_ini` alapján dönt,
                # melyik mappa `.picasa.ini`-jét olvassa (ld.
                # `index/people.py`) — az ÚJONNAN írt ini (első névadás egy
                # eddig ini nélküli mappában) e nélkül csak a KÖVETKEZŐ
                # háttér-szinkronnál látszana. A `photo_ops_controller`
                # mintáját követve azonnal újraszinkronizáljuk az érintett
                # mappákat, hogy az Emberek-gyűjtemény rögtön frissüljön.
                for folder in touched_folders:
                    sync_tree(conn, folder)
                conn.commit()
            self.unnamedCountChanged.emit()
        return all_ok and bool(written_ids)

    @Slot(int, result=bool)
    def acceptSuggestion(self, face_id: int) -> bool:  # noqa: N802
        """A név-javaslat ELFOGADÁSA (pipa): a javasolt nevet ténylegesen
        ráírjuk az arcra — ugyanazon az úton, mint a kézi névadás."""
        with open_index(self._db_path) as conn:
            row = conn.execute(
                "SELECT suggested_name FROM face WHERE id = ?", (int(face_id),)
            ).fetchone()
            name = row["suggested_name"] if row is not None else None
        if not name:
            return False
        return self.assignNameToFaces([int(face_id)], name)

    @Slot(int)
    def rejectSuggestion(self, face_id: int) -> None:  # noqa: N802
        """A név-javaslat ELVETÉSE (x): a javaslat eltűnik, az arc marad
        névtelen. Az arcot magát NEM mellőzzük — az külön döntés."""
        with open_index(self._db_path) as conn:
            set_suggested_name(conn, int(face_id), None)
            conn.commit()

    @Slot(list, result=int)
    def ignoreFaces(self, face_ids) -> int:  # noqa: N802 — QML-slot-stílus
        """A kijelölt arcok MELLŐZÉSE — a „Mellőzött emberek" album (#26).

        Az eredetiben ez nem törlés volt: *„Are you sure you want to move
        this person to the ignored people album?"* — a személy egy külön
        albumba került, tehát visszavehető. Nálunk ugyanez: az arc-sor
        megmarad, csak `state = 'ignored'` lesz, így sem a „Névtelenek"
        albumban, sem a csoportosításban nem bukkan fel újra.

        A mellőzött arcok száma a visszatérési érték."""
        ids = [int(face_id) for face_id in face_ids]
        if not ids:
            return 0
        with open_index(self._db_path) as conn:
            mark_faces_ignored(conn, ids)
            conn.commit()
        self.unnamedCountChanged.emit()
        return len(ids)

    @Slot(result=int)
    def ignoredCount(self) -> int:  # noqa: N802 — QML-slot-stílus
        """Hány arc van a „Mellőzött emberek" albumban."""
        with open_index(self._db_path) as conn:
            return len(ignored_faces(conn))

    @Slot(result="QVariantList")
    def ignoredGroups(self) -> list[dict]:  # noqa: N802 — QML-slot-stílus
        """A „Mellőzött emberek" album tartalma — az `unnamedGroups()`
        alakjában, egyetlen csoportban.

        Az eredetiben ez egy ALBUM volt (`CAlbumLabel::Ignored` =
        „Ignored people"), nem egy elrejtett szemetes: meg lehetett nézni,
        tehát vissza is lehetett venni belőle."""
        with open_index(self._db_path) as conn:
            faces = [face for face in ignored_faces(conn) if face.rect is not None]
        if not faces:
            return []
        return [
            _group_payload(
                faces, self.tr("Ignored people ({0})").format(len(faces))
            )
        ]

    @Slot(list, result=int)
    def unignoreFaces(self, face_ids) -> int:  # noqa: N802 — QML-slot-stílus
        """A mellőzés VISSZAVONÁSA: az arcok újra a „Névtelenek" albumba
        kerülnek."""
        ids = [int(face_id) for face_id in face_ids]
        if not ids:
            return 0
        with open_index(self._db_path) as conn:
            unignore_faces(conn, ids)
            conn.commit()
        self.unnamedCountChanged.emit()
        return len(ids)

    @Slot()
    def computeEmbeddings(self) -> None:
        """Lenyomat-számítás (SFace) a még lenyomat nélküli arcokon, majd a
        névtelen arcok inkrementális csoportosítása — KÜLÖN, a detektálásnál
        alacsonyabb prioritású sor (ld. osztály-docstring). Modell hiányában
        azonnal `embeddingModelUnavailable`-t ad és nem indít szálat."""
        if not self._embedder.available:
            self.embeddingModelUnavailable.emit()
            return
        self.cancelEmbedding()
        stop_event = threading.Event()
        self._embedding_stop_event = stop_event
        self.embeddingStarted.emit()
        self._start_background(
            self._run_embedding, args=(stop_event,), name="picasapy-face-embed"
        )

    @Slot()
    def cancelEmbedding(self) -> None:
        """A folyamatban lévő lenyomat-számítás megszakítása arc-határon —
        a már elmentett lenyomatok/csoportok az indexben maradnak."""
        if self._embedding_stop_event is not None:
            self._embedding_stop_event.set()

    # -- worker-szál törzse -------------------------------------------------

    def _run_scan(self, stop_event: threading.Event) -> None:
        try:
            with open_index(self._db_path) as conn:
                photos = all_photos(conn)
                total = len(photos)
                found = 0
                scanned = 0
                for done, photo in enumerate(photos, start=1):
                    if stop_event.is_set():
                        conn.commit()
                        self.scanCancelled.emit()
                        return
                    photo_path = Path(photo.folder_path) / photo.name
                    if _has_named_face(photo_path):
                        # a Picasa döntése szent — nem értékeljük újra
                        self._report_scan(done, total)
                        continue
                    if photo_path.suffix.lower() in VIDEO_EXTENSIONS:
                        self._report_scan(done, total)
                        continue
                    faces = self._detect(photo_path)
                    replace_faces(conn, photo.id, faces)
                    found += len(faces)
                    scanned += 1
                    if scanned % _COMMIT_BATCH_SIZE == 0:
                        conn.commit()
                    self._report_scan(done, total)
                conn.commit()
        except Exception as error:  # noqa: BLE001 — index-hiba se fagyassza a UI-t
            _log.exception("arc-detektálás hiba: %s", self._db_path)
            self.scanFailed.emit(str(error))
            return
        finally:
            if self._stop_event is stop_event:
                self._stop_event = None
            # a sor eltűnik a bal hasábból — akkor is, ha megszakadt vagy
            # hibára futott (#449)
            self._set_scan_percent(-1)
        self.unnamedCountChanged.emit()
        self.scanFinished.emit(found, scanned)

    def _report_scan(self, done: int, total: int) -> None:
        """Haladás-jelzés + a bal hasáb sorának százaléka (#449)."""
        self._set_scan_percent(round(100 * done / total) if total else 100)
        self.scanProgress.emit(done, total)

    def _run_embedding(self, stop_event: threading.Event) -> None:
        try:
            with open_index(self._db_path) as conn:
                pending = faces_missing_embedding(conn)
                total = len(pending)
                embedded = 0
                for done, face in enumerate(pending, start=1):
                    if stop_event.is_set():
                        conn.commit()
                        self.embeddingCancelled.emit()
                        return
                    image = self._decode(face.photo_path)
                    embedding = (
                        self._embedder.compute(image, face.detection)
                        if image is not None
                        else None
                    )
                    if embedding is not None:
                        store_embedding(conn, face.id, embedding)
                        embedded += 1
                    if done % _COMMIT_BATCH_SIZE == 0:
                        conn.commit()
                    self.embeddingProgress.emit(done, total)
                conn.commit()
                grouped = group_unnamed_faces(conn)
                conn.commit()
        except Exception as error:  # noqa: BLE001 — index-hiba se fagyassza a UI-t
            _log.exception("arc-lenyomat/csoportosítás hiba: %s", self._db_path)
            self.embeddingFailed.emit(str(error))
            return
        finally:
            if self._embedding_stop_event is stop_event:
                self._embedding_stop_event = None
        self.embeddingFinished.emit(embedded, grouped)

    def _detect(self, photo_path: Path):
        image = self._decode(photo_path)
        if image is None:
            return ()
        return self._detector.detect(image)

    @staticmethod
    def _decode(photo_path: Path):
        """A fotó redukált dekódolása — a thumbs-cache/dedup mintáját
        követi (`cvimage.read_image_bytes` + `reduced_color_flag`), hogy
        ne épüljön új I/O-út a projektbe."""
        payload = read_image_bytes(photo_path)
        if payload is None:
            return None
        flag = reduced_color_flag(payload, _DETECT_MAX_DIMENSION)
        return cv2.imdecode(payload, flag)


def _group_payload(faces, label: str) -> dict:
    """Egy `unnamedGroups()`-csoport QML-alakja — a bélyegkép ugyanazt a
    `image://thumbs/<photo_id>` szolgáltatót használja, mint a fő rács
    (ld. `app/models.py:_thumb_url`), forgatás-/szűrő-érzékeny cache-
    buster NÉLKÜL (a Névtelenek albumban ez nem kritikus)."""
    return {
        "label": label,
        "faces": [
            {
                "faceId": face.id,
                "thumbUrl": f"image://thumbs/{face.photo_id}",
                # #26 (4. lépcső): a MÉG EL NEM DÖNTÖTT név-javaslat. Az
                # eredeti kérdésként vetette fel (`PeoplePanel::
                # SuggestionFmt` = „%s?"), pipa/x gombbal.
                "suggestedName": face.suggested_name or "",
            }
            for face in faces
        ],
    }


def _has_named_face(photo_path: Path) -> bool:
    """Igaz, ha a fotóhoz MÁR van ember által adott névcímke a
    `.picasa.ini`-ben — ilyenkor a saját detektorunk kihagyja a fotót
    (a Picasa döntései szentek, ld. modul-docstring). Hiányzó/olvashatatlan
    ini esetén hamis (nincs mit tiszteletben tartani)."""
    ini_path = photo_path.parent / PICASA_INI_NAME
    if not ini_path.exists():
        return False
    try:
        document = load_document(ini_path)
    except (OSError, ValueError):
        return False
    section = document.section(photo_path.name)
    if section is None:
        return False
    raw_faces = section.get("faces")
    if not raw_faces:
        return False
    try:
        faces = parse_faces(raw_faces)
    except ValueError:
        return False
    return any(face.is_identified for face in faces)
