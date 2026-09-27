"""PassportPhotoController: az Útlevélkép (#1401) — arcfelismerés a
KIJELÖLT képen, a `picasapy.faces.passport` képlete szerinti négyzet-
kivágás, majd a kivágott fájl átadása a MEGLÉVŐ nyomtatási nézetnek
(`PrintDialog.openForPassport`), `ePassport` mérettel.

A keresés és a kivágás HÁTTÉRSZÁLON fut (`BackgroundWorkerMixin`), a
`FaceScanController` mintájára: az arcot csökkentett felbontáson keressük
(`_DETECT_MAX_DIMENSION`), a talált keretet a teljes képre skálázzuk vissza,
és a kivágás a TELJES felbontású képből készül. A Picasa `rotate_steps`
forgatása mindkét lépés ELŐTT érvényesül — a felhasználó a forgatott képet
látja, az arc is abban áll.

A KÉP MAGA NEM MÓDOSUL: a kivágott változat egy gyorstár-könyvtárban
(felhasználói gyorstár, minden híváskor felülírva) él, nem a
fotókönyvtárban és nem a `.picasa.ini`-ben."""

from __future__ import annotations

import logging
from collections.abc import Callable, Sequence
from pathlib import Path

import numpy as np
from PySide6.QtCore import QObject, QStandardPaths, QUrl, Signal, Slot

from picasapy.app.face_scan_controller import _DETECT_MAX_DIMENSION
from picasapy.app.worker_thread import BackgroundWorkerMixin
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

#: A `passportFailed` két oka — a QML ezekhez választ szöveget.
FAILED_READ = "read"
FAILED_WRITE = "write"


def _forgatva(image: np.ndarray, rotate_steps: int) -> np.ndarray:
    """A Picasa `rotate_steps` negyedfordulata, az óramutató járásával
    megegyezően (ugyanaz a leképezés, mint az exportálóé)."""
    lepes = int(rotate_steps or 0) % 4
    if lepes == 0:
        return image
    forgatas = {
        1: cv2.ROTATE_90_CLOCKWISE,
        2: cv2.ROTATE_180,
        3: cv2.ROTATE_90_COUNTERCLOCKWISE,
    }[lepes]
    return cv2.rotate(image, forgatas)


class PassportPhotoController(BackgroundWorkerMixin, QObject):
    """A `PhotoRecord`-ok listájából (a látható mappa/album, ugyanaz a
    forrás, mint a `PrintController`-é) a KIJELÖLT sor arc-felismerése és
    -kivágása."""

    #: `CThumbUI::Passport0` — „Nem találhatók arcok"
    passportNoFace = Signal()
    #: `CThumbUI::Passport1` — „Úgy tűnik, több arc van a képen."
    passportMultipleFaces = Signal()
    #: a kép nem olvasható (`FAILED_READ`), vagy a kivágás nem írható ki
    #: (`FAILED_WRITE`) — ez NEM arc-hiba, a felület külön mondja ki
    passportFailed = Signal(str)
    #: a kivágott, ideiglenes fájl URL-je — a hívó ezzel nyitja a
    #: nyomtatási nézetet
    passportReady = Signal(str)

    def __init__(
        self,
        photo_source: Callable[[], Sequence[PhotoRecord]],
        parent: QObject | None = None,
        detector: FaceDetector | None = None,
        cache_dir: Path | None = None,
    ) -> None:
        """`photo_source`: a jelenleg megnyitott mappa/album `PhotoRecord`-
        jai — a `row` ebbe a listába mutat.

        `detector`: lecserélhető (teszt); hiányában lustán, az első
        híváskor épül fel. `cache_dir`: a kivágás helye; hiányában a Qt
        gyorstár-könyvtárának `print-preview` alkönyvtára."""
        super().__init__(parent)
        self._photo_source = photo_source
        self._detector = detector
        self._cache_dir = cache_dir

    def use_detector(self, detector) -> None:
        """A detektor cseréje (a felületi tesztek hamis detektora)."""
        self._detector = detector

    def _get_detector(self):
        if self._detector is None:
            self._detector = FaceDetector()
        return self._detector

    def _cache_path(self) -> Path:
        """A kivágott kép HELYE — egyetlen, felülírt fájl."""
        if self._cache_dir is not None:
            folder = Path(self._cache_dir)
        else:
            base = QStandardPaths.writableLocation(
                QStandardPaths.StandardLocation.CacheLocation
            ) or str(Path.home())
            folder = Path(base) / "print-preview"
        return folder / "passport.png"

    @Slot(int)
    def preparePassportPhoto(self, row: int) -> None:  # noqa: N802 — QML-stílus
        """A `row`-adik fotó arcfelismerése és kivágása, háttérszálon.

        Érvénytelen sornál nem indul semmi (a menüpont kijelölés nélkül
        úgyis tiltott); futó kérés közben a második kérés elmarad."""
        photos = tuple(self._photo_source())
        if not 0 <= int(row) < len(photos):
            _log.warning("Útlevélkép: érvénytelen sor — %s", row)
            return
        if self.backgroundWorkersRunning():
            return
        record = photos[int(row)]
        path = Path(record.folder_path) / record.name
        steps = int(getattr(record, "rotate_steps", 0) or 0)
        self._start_background(
            self._run, args=(path, steps), name="picasapy-passport"
        )

    def _run(self, path: Path, rotate_steps: int) -> None:
        small = dekodolj_forrast(path, goal=_DETECT_MAX_DIMENSION)
        if small is None:
            _log.warning("Útlevélkép: nem dekódolható kép — %s", path)
            self.passportFailed.emit(FAILED_READ)
            return
        small = _forgatva(small, rotate_steps)
        faces = self._get_detector().detect(small)
        outcome = classify_face_count(len(faces))
        if outcome == NO_FACE:
            self.passportNoFace.emit()
            return
        if outcome == MULTIPLE_FACES:
            self.passportMultipleFaces.emit()
            return

        full = dekodolj_forrast(path)
        if full is None:
            _log.warning("Útlevélkép: nem dekódolható kép — %s", path)
            self.passportFailed.emit(FAILED_READ)
            return
        full = _forgatva(full, rotate_steps)
        height, width = full.shape[:2]
        sx = width / small.shape[1]
        sy = height / small.shape[0]
        face = faces[0]
        rect = passport_crop_rect(
            face.left * sx, face.top * sy, face.right * sx, face.bottom * sy,
            width, height,
        )
        if rect.width <= 0 or rect.height <= 0:
            # a felismerő a kép határain kívüli keretet adott
            _log.warning("Útlevélkép: üres kivágás — %s", path)
            self.passportNoFace.emit()
            return
        cropped = full[rect.top : rect.bottom, rect.left : rect.right]
        target = self._cache_path()
        if not self._write_png(cropped, target):
            self.passportFailed.emit(FAILED_WRITE)
            return
        self.passportReady.emit(QUrl.fromLocalFile(str(target)).toString())

    @staticmethod
    def _write_png(image: np.ndarray, target: Path) -> bool:
        ok, buf = cv2.imencode(".png", image)
        if not ok:
            _log.warning("Útlevélkép: a kivágás nem kódolható — %s", target)
            return False
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(buf.tobytes())
        except OSError:
            _log.exception("Útlevélkép: a kivágás nem írható ki — %s", target)
            return False
        return True


__all__ = ["FAILED_READ", "FAILED_WRITE", "PassportPhotoController"]
