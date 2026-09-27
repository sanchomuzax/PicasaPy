"""PassportPhotoController: az Útlevélkép (#1401) — arcfelismerés a
KIJELÖLT képen, a `picasapy.faces.passport` képlete szerinti négyzet-
kivágás, majd a nyomtatási nézet megnyitása rögzített `ePassport` mérettel
(2,0 × 2,0 hüvelyk), 1-es kezdő példányszámmal.

Önálló QObject — a `PrintController`/`FaceScanController` mintáját követve
NEM az `AppController` mixinje, hogy a `controller.py`/`Main.qml` (forró
fájlok, ld. CONTRIBUTING.md) csak a végleges, minimális bekötést kapja: a
tényleges nyomtatást a KÜLÖN `PrintController.printPassportPhoto`/
`renderPassportPreviewPdf` végzi, ezt a QML köti össze (ld.
`PassportPrintDialog.qml`) — ugyanaz a mintázat, mint a
`printContactSheetRequested` → `openContactSheetPrint` láncé.

A KÉP MAGA NEM MÓDOSUL: a kivágott változat a nyomtatási előnézet
gyorstárában (felhasználói gyorstár-könyvtár, minden híváskor felülírva)
él, nem a fotókönyvtárban és nem a `.picasa.ini`-ben — ez felel meg a jegy
negyedik feltételének („a kép maga nem módosul, tartós adat nem íródik")."""

from __future__ import annotations

import logging
from collections.abc import Callable, Sequence
from pathlib import Path

from PySide6.QtCore import QObject, QStandardPaths, QUrl, Signal, Slot

from picasapy.cvimage import dekodolj_forrast
from picasapy.faces.detector import FaceDetector
from picasapy.faces.passport import (
    MULTIPLE_FACES,
    NO_FACE,
    classify_face_count,
    passport_crop_rect,
)
from picasapy.index import PhotoRecord
from picasapy.lazy_cv2 import cv2

_log = logging.getLogger(__name__)


class PassportPhotoController(QObject):
    """A `PhotoRecord`-ok listájából (a látható mappa/album, ugyanaz a
    forrás, mint a `PrintController`-é) a KIJELÖLT sor arc-felismerése és
    -kivágása."""

    #: `CThumbUI::Passport0` — „Nem találhatók arcok"; a hívó a hibaablak
    #: FIX címével (`CThumbUI::Passportfail`) együtt jeleníti meg.
    passportNoFace = Signal()
    #: `CThumbUI::Passport1` — „Úgy tűnik, több arc van a képen."
    passportMultipleFaces = Signal()
    #: a kivágott, ideiglenes fájl URL-je — a hívó ezzel nyitja a
    #: nyomtatási nézetet, `ePassport` mérettel, 1-es példányszámmal.
    passportReady = Signal(str)

    def __init__(
        self,
        photo_source: Callable[[], Sequence[PhotoRecord]],
        parent: QObject | None = None,
        detector: FaceDetector | None = None,
    ) -> None:
        """`photo_source`: hívható, ami a jelenleg megnyitott mappa/album
        `PhotoRecord`-jait adja vissza (a `PrintController` mintájára) —
        a `row` ebbe a listába mutat.

        `detector`: tesztbeli lecserélhetőség; hiányában lustán, az első
        híváskor épül fel (ld. `FaceDetector` — modell nélkül is biztonságos,
        `available=False`-ra áll, `detect()` üres tuple-t ad)."""
        super().__init__(parent)
        self._photo_source = photo_source
        self._detector = detector

    def _get_detector(self) -> FaceDetector:
        if self._detector is None:
            self._detector = FaceDetector()
        return self._detector

    @staticmethod
    def _cache_path() -> Path:
        """A kivágott előnézet HELYE — a `PrintController.previewImageUrl`
        mintáját követve a Qt gyorstár-könyvtárában, EGYETLEN, felülírt
        fájlként (nem szemetel a fotók mellé, a rendszer magától takarít)."""
        base = QStandardPaths.writableLocation(
            QStandardPaths.StandardLocation.CacheLocation
        )
        if not base:
            base = str(Path.home())
        folder = Path(base) / "print-preview"
        folder.mkdir(parents=True, exist_ok=True)
        return folder / "passport.png"

    @Slot(int)
    def preparePassportPhoto(self, row: int) -> None:  # noqa: N802 — QML-stílus
        """A `row`-adik fotó arcfelismerése és kivágása (#1401).

        Érvénytelen sor, olvashatatlan kép, vagy hiányzó/több arc esetén a
        megfelelő jelzés megy ki (ld. az osztály docstringjét) — a hívó
        (QML) ebből nyitja a hibaablakot. Pontosan EGY arcnál a kivágott
        kép a gyorstárba kerül, és a `passportReady` viszi tovább az URL-t."""
        photos = tuple(self._photo_source())
        if not 0 <= int(row) < len(photos):
            self.passportNoFace.emit()
            return
        record = photos[int(row)]
        path = Path(record.folder_path) / record.name
        image = dekodolj_forrast(path)
        if image is None:
            # olvashatatlan/hiányzó fájl — ugyanaz a végfelhasználói
            # üzenet, mint a „nincs arc" eset: a kivágáshoz úgysem
            # jutnánk el, és külön hibaszöveget a jegy nem kér.
            _log.warning("Útlevélkép: nem dekódolható kép — %s", path)
            self.passportNoFace.emit()
            return
        detector = self._get_detector()
        faces = detector.detect(image)
        outcome = classify_face_count(len(faces))
        if outcome == NO_FACE:
            self.passportNoFace.emit()
            return
        if outcome == MULTIPLE_FACES:
            self.passportMultipleFaces.emit()
            return

        face = faces[0]
        height, width = image.shape[:2]
        rect = passport_crop_rect(
            face.left, face.top, face.right, face.bottom, width, height
        )
        if rect.width <= 0 or rect.height <= 0:
            # elméleti védőháló: a felismerő a kép határain kívüli
            # téglalapot adna — a kivágás emiatt üres lenne
            _log.warning(
                "Útlevélkép: üres kivágás (arc a kép szélén?) — %s", path
            )
            self.passportNoFace.emit()
            return
        cropped = image[rect.top : rect.bottom, rect.left : rect.right]
        target = self._cache_path()
        if not cv2.imwrite(str(target), cropped):
            _log.warning("Útlevélkép: a kivágás nem írható ki — %s", target)
            self.passportNoFace.emit()
            return
        self.passportReady.emit(QUrl.fromLocalFile(str(target)).toString())


__all__ = ["PassportPhotoController"]
