"""YuNet arc-detektor (`cv2.FaceDetectorYN`) — hiánytűrő becsomagolás.

KRITIKUS KÖRNYEZETI KORLÁT (issue #26): a CI-ben (Ubuntu ÉS Windows) nincs
garantált hálózat, és a modellfájl nincs jelen. Ezért a `FaceDetector`
konstruktora SOHA nem dob kivételt és SOHA nem blokkol hálózatra — ha a
modell hiányzik, vagy a telepített OpenCV build nem tartalmazza az API-t,
`available=False`-ra áll és naplózott üzenettel kikapcsol. A hívó
(`FaceScanController`) ez alapján dönt: modell nélkül a funkció csendben
nem csinál semmit, az alkalmazás minden más része változatlan marad.

A modell beszerzése KÜLÖN, explicit lépés (`download_model`) — ez sem
hívódik automatikusan indításkor vagy tesztben, hogy egy hálózat nélküli
környezet (CI) ne akadjon el rajta."""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from pathlib import Path

import numpy as np

try:
    # #1611: a lusta helyettes — az OpenCV csak az első tényleges
    # használatkor töltődik be. A `faces` csomag az INDULÁSI láncban van
    # (`index/__init__` → `index/face_groups` → `faces/__init__`), tehát
    # az itteni felső szintű `import cv2` egymaga behozta a teljes
    # ~1,5 másodperces költséget minden induláskor.
    from picasapy.lazy_cv2 import cv2
except ImportError:  # pragma: no cover — az OpenCV már a projekt kemény
    # függősége (thumbs/scanner), ez az ág csak extra védelem
    cv2 = None  # type: ignore[assignment]

logger = logging.getLogger(__name__)

#: Ezzel a környezeti változóval a modellfájl útvonala felülbírálható —
#: elsősorban a felhasználó saját letöltéséhez / teszthez.
MODEL_ENV_VAR = "PICASAPY_FACE_MODEL"

MODEL_FILENAME = "face_detection_yunet_2023mar.onnx"

# A hivatalos, MIT licencű forrás (OpenCV Zoo) — a licenc GPL-3.0-
# kompatibilitása az issue #26 kommentjében ellenőrizve (2026-08-07).
MODEL_DOWNLOAD_URL = (
    "https://github.com/opencv/opencv_zoo/raw/main/models/"
    "face_detection_yunet/face_detection_yunet_2023mar.onnx"
)

# YuNet ajánlott alapértékei (OpenCV Zoo mintakód).
_DEFAULT_SCORE_THRESHOLD = 0.7
_DEFAULT_NMS_THRESHOLD = 0.3
_DEFAULT_TOP_K = 5000


def default_model_dir() -> Path:
    """A letöltött modellek felhasználói mappája — SOHA nem a repóban."""
    base = os.environ.get("XDG_DATA_HOME") or str(Path.home() / ".local" / "share")
    return Path(base) / "picasapy" / "models"


def default_model_path() -> Path:
    return default_model_dir() / MODEL_FILENAME


def resolve_model_path() -> Path | None:
    """A ténylegesen a lemezen létező modellfájl útvonala, vagy `None`.

    Sorrend: a `PICASAPY_FACE_MODEL` környezeti változó (ha meg van adva
    és létezik), majd a felhasználói alapértelmezett hely. Egyik sem
    létezés-ellenőrzés nélküli — ez a hívó (`FaceDetector`) tiszta
    kikapcsolásának alapja."""
    override = os.environ.get(MODEL_ENV_VAR)
    candidates: list[Path] = [Path(override)] if override else []
    candidates.append(default_model_path())
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    return None


def download_model(
    dest: Path | str | None = None,
    url: str = MODEL_DOWNLOAD_URL,
    timeout: float = 30.0,
) -> bool:
    """A modell letöltése a megadott (vagy alapértelmezett) helyre.

    SOHA nem hívódik automatikusan — sem induláskor, sem tesztben, sem a
    `FaceDetector`-ből. Hálózat/lemez-hiba esetén csendesen `False`-t ad
    vissza, nem dob kivételt.

    #1496: a törzse ma az ELLENŐRZŐ letöltőé
    (`model_download.download_spec`) — méret + SHA-256 nélkül egy csonka
    vagy elcserélt fájl némán a modell helyére kerülne, és a felismerés
    rosszul, de LÁTSZÓLAG működne. A korábbi változat semmit nem
    ellenőrzött. A felületi út (`FaceScanController.downloadModels`)
    ugyanide fut be: nincs második, ellenőrizetlen letöltő a fában.

    Az import SZÁNDÉKOSAN a függvény törzsében van: a `model_download`
    ezt a modult importálja (`MODEL_FILENAME`, `default_model_dir`),
    modul-szinten tehát körbe érne."""
    from .model_download import DETECTOR_SPEC, download_spec

    return download_spec(DETECTOR_SPEC, dest=dest, url=url, timeout=timeout).ok


@dataclass(frozen=True)
class FaceLandmarks:
    """A YuNet öt jellegzetes pontja, KÉPPIXELBEN — a detektor kimenetének
    igazolt sorrendjében (issue #26, 2026-08-07-i mérés): jobb szem, bal
    szem, orrhegy, száj jobb sarka, száj bal sarka."""

    right_eye: tuple[float, float]
    left_eye: tuple[float, float]
    nose: tuple[float, float]
    mouth_right: tuple[float, float]
    mouth_left: tuple[float, float]


@dataclass(frozen=True)
class FaceDetection:
    """Egy detektált arc — a keret KÉPPIXELBEN (nem [0..1] relatív, szemben
    a Picasa rect64-gyel; a hívó normalizál, ha kell)."""

    left: float
    top: float
    right: float
    bottom: float
    score: float
    landmarks: FaceLandmarks


class FaceDetector:
    """`cv2.FaceDetectorYN` hiánytűrő becsomagolása.

    Modell/API hiányában `available=False`, a `detect()` üres tuple-t ad —
    NINCS kivétel, NINCS crash a hívóig (ld. modul-docstring)."""

    def __init__(
        self,
        model_path: Path | None = None,
        score_threshold: float = _DEFAULT_SCORE_THRESHOLD,
        nms_threshold: float = _DEFAULT_NMS_THRESHOLD,
        top_k: int = _DEFAULT_TOP_K,
    ) -> None:
        self.available = False
        self._detector = None
        self.model_path = model_path if model_path is not None else resolve_model_path()
        if self.model_path is None:
            logger.info(
                "Arcfelismerő modell nem található — a funkció kikapcsolva "
                "(a %s környezeti változóval vagy a %s helyre másolva "
                "adható meg; ld. picasapy.faces.download_model).",
                MODEL_ENV_VAR,
                default_model_path(),
            )
            return
        if cv2 is None or not hasattr(cv2, "FaceDetectorYN"):
            logger.warning(
                "A telepített OpenCV build nem tartalmazza a FaceDetectorYN "
                "API-t — az arcfelismerés kikapcsolva."
            )
            return
        try:
            self._detector = cv2.FaceDetectorYN.create(
                str(self.model_path),
                "",
                (0, 0),
                score_threshold=score_threshold,
                nms_threshold=nms_threshold,
                top_k=top_k,
            )
        except cv2.error as error:  # pragma: no cover — sérült modellfájl
            logger.warning(
                "Az arcfelismerő modell betöltése sikertelen (%s) — a "
                "funkció kikapcsolva.",
                error,
            )
            self._detector = None
            return
        self.available = True

    def detect(self, image_bgr: np.ndarray | None) -> tuple[FaceDetection, ...]:
        """Detektálás a MÁR dekódolt BGR képen — nincs extra fájlolvasás.

        Modell hiányában, vagy hibás/üres bemenetre üres tuple (nem hiba).
        """
        if not self.available or self._detector is None:
            return ()
        if image_bgr is None or image_bgr.size == 0:
            return ()
        height, width = image_bgr.shape[:2]
        try:
            self._detector.setInputSize((width, height))
            _count, faces = self._detector.detect(image_bgr)
        except cv2.error as error:  # pragma: no cover — hibás kép/dekódolás
            logger.warning("Arc-detektálás sikertelen: %s", error)
            return ()
        if faces is None:
            return ()
        return tuple(_parse_row(row) for row in faces)


def _parse_row(row: np.ndarray) -> FaceDetection:
    """Egy YuNet-sor (keret(4) + 5 pont(10) + pontszám) → `FaceDetection`.

    Oszloprend (igazolva, issue #26 2026-08-07-i mérése): x,y,w,h,
    jobb_szem(x,y), bal_szem(x,y), orr(x,y), száj_jobb(x,y), száj_bal(x,y),
    pontszám."""
    x, y, w, h = (float(v) for v in row[0:4])
    (
        rx, ry, lx, ly, nx, ny, mrx, mry, mlx, mly,
    ) = (float(v) for v in row[4:14])
    score = float(row[14])
    return FaceDetection(
        left=x,
        top=y,
        right=x + w,
        bottom=y + h,
        score=score,
        landmarks=FaceLandmarks(
            right_eye=(rx, ry),
            left_eye=(lx, ly),
            nose=(nx, ny),
            mouth_right=(mrx, mry),
            mouth_left=(mlx, mly),
        ),
    )
