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
egy azonosított bejegyzéssel) — ezeket SOHA nem értékeljük újra."""

from __future__ import annotations

import logging
import threading
from pathlib import Path

import cv2
from PySide6.QtCore import QObject, Signal, Slot

from picasapy.cvimage import read_image_bytes, reduced_color_flag
from picasapy.faces.detector import FaceDetector
from picasapy.index import (
    all_photos,
    open_index,
    replace_faces,
    unnamed_album_photos,
)
from picasapy.ini import load_document, parse_faces
from picasapy.scanner import PICASA_INI_NAME
from picasapy.scanner.filetypes import VIDEO_EXTENSIONS

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

    def __init__(self, db_path: str | Path, detector: FaceDetector | None = None) -> None:
        super().__init__()
        self._db_path = Path(db_path)
        # Tesztben/CI-ben injektálható helyettesítő detektor is lehet —
        # alapból a valódi (modell nélkül önmagát kikapcsoló) YuNet-becsomagolás.
        self._detector = detector if detector is not None else FaceDetector()
        self._stop_event: threading.Event | None = None

    @Slot(result=bool)
    def isAvailable(self) -> bool:
        """Igaz, ha a modell betöltve, tehát a szkennelés ténylegesen futna."""
        return self._detector.available

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
                        self.scanProgress.emit(done, total)
                        continue
                    if photo_path.suffix.lower() in VIDEO_EXTENSIONS:
                        self.scanProgress.emit(done, total)
                        continue
                    faces = self._detect(photo_path)
                    replace_faces(conn, photo.id, faces)
                    found += len(faces)
                    scanned += 1
                    if scanned % _COMMIT_BATCH_SIZE == 0:
                        conn.commit()
                    self.scanProgress.emit(done, total)
                conn.commit()
        except Exception as error:  # noqa: BLE001 — index-hiba se fagyassza a UI-t
            _log.exception("arc-detektálás hiba: %s", self._db_path)
            self.scanFailed.emit(str(error))
            return
        finally:
            if self._stop_event is stop_event:
                self._stop_event = None
        self.scanFinished.emit(found, scanned)

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
