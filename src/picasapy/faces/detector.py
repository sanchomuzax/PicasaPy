"""YuNet arc-detektor (`cv2.FaceDetectorYN`) — hiánytűrő becsomagolás.

KRITIKUS KÖRNYEZETI KORLÁT (issue #26): a CI-ben nincs garantált hálózat. A YuNet-modell ezért a program részeként érkezik; a `FaceDetector` konstruktora hálózat nélkül is betölti. Ha a modell hiányzik, vagy az OpenCV build nem tartalmazza az API-t, `available=False`-ra áll és naplózott üzenettel kikapcsol."""

from __future__ import annotations

import logging
import os
import threading
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

# YuNet alapértékei; a küszöb az OpenCV Zoo mintakódjáé (#4348: arc nélküli
# tájképen a téves jelöltek 0,71–0,76-ot, a valódi arcok 0,91–0,93-at kapnak).
_DEFAULT_SCORE_THRESHOLD = 0.9
_DEFAULT_NMS_THRESHOLD = 0.3
_DEFAULT_TOP_K = 5000

# A háttér-arc- és a vörösszem-detektálás ugyanazon a korlátozott méreten
# fusson; a hívók a visszaadott képpont-koordinátákat a saját képméretükre
# skálázzák vissza.
MAX_DETECTION_DIMENSION = 960

# Ha az első menet üres, egy kisebb arcot mutató, körben kipótolt képen is
# próbálunk. A 720-as vászon a 960 pixeles fő bemenetnél 0,75-ös méretet ad;
# kisebb kivágásoknál a 80%-os előkicsinyítés és a padding marad a mérvadó.
_SECOND_PASS_SCALE = 0.8
_SECOND_PASS_PADDING = 0.4
_SECOND_PASS_MAX_DIMENSION = MAX_DETECTION_DIMENSION * 3 // 4

# #6439: a 0,9 alatti jelölt akkor is arc, ha a második menet ugyanott,
# ugyanilyen alsó küszöbbel is talál arcot. A kis, stilizált vagy részben
# takart arcok első menetben gyakran 0,85-0,90 közé esnek; az arc nélküli
# képek legjobb jelöltjei ennél jóval alatta maradnak (a mérés: tájképek
# és fű-minták legfeljebb 0,7). A két független menet egyezése a védelem,
# a küszöb önmagában nem.
_CONSENSUS_SCORE_FLOOR = 0.8
_CONSENSUS_MIN_IOU = 0.3


def default_model_dir() -> Path:
    """A letöltött modellek felhasználói mappája — SOHA nem a repóban."""
    base = os.environ.get("XDG_DATA_HOME") or str(Path.home() / ".local" / "share")
    return Path(base) / "picasapy" / "models"


def default_model_path() -> Path:
    return default_model_dir() / MODEL_FILENAME


def bundled_model_path() -> Path | None:
    """A programmal csomagolt YuNet-modell útvonala, ha jelen van."""
    candidate = Path(__file__).resolve().parent / "models" / MODEL_FILENAME
    return candidate if candidate.is_file() else None


def resolve_model_path() -> Path | None:
    """A ténylegesen a lemezen létező modellfájl útvonala, vagy `None`.

    Sorrend: a `PICASAPY_FACE_MODEL` környezeti változó (ha meg van adva
    és létezik), a felhasználói modellmappa, majd a programmal csomagolt
    modell. Minden útvonal létezését ellenőrzi."""
    override = os.environ.get(MODEL_ENV_VAR)
    candidates: list[Path] = [Path(override)] if override else []
    candidates.append(default_model_path())
    packaged = bundled_model_path()
    if packaged is not None:
        candidates.append(packaged)
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

    A letöltés felhasználói kérésre történik, kivéve hogy a vezérlő az
    SFace-csoportosítás első indításakor automatikusan is elindítja, ha sem
    a csomagban, sem a felhasználói modellmappában nem található modell.
    Hálózat/lemez-hiba esetén csendesen `False`-t ad vissza, nem dob kivételt.

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


def rescale_face_detection(
    detection: FaceDetection, scale_x: float, scale_y: float
) -> FaceDetection:
    """Detektált keret és arcpontok átváltása másik képpont-rácsra."""
    landmarks = detection.landmarks
    return FaceDetection(
        left=detection.left * scale_x,
        top=detection.top * scale_y,
        right=detection.right * scale_x,
        bottom=detection.bottom * scale_y,
        score=detection.score,
        landmarks=FaceLandmarks(
            right_eye=(
                landmarks.right_eye[0] * scale_x,
                landmarks.right_eye[1] * scale_y,
            ),
            left_eye=(
                landmarks.left_eye[0] * scale_x,
                landmarks.left_eye[1] * scale_y,
            ),
            nose=(landmarks.nose[0] * scale_x, landmarks.nose[1] * scale_y),
            mouth_right=(
                landmarks.mouth_right[0] * scale_x,
                landmarks.mouth_right[1] * scale_y,
            ),
            mouth_left=(
                landmarks.mouth_left[0] * scale_x,
                landmarks.mouth_left[1] * scale_y,
            ),
        ),
    )


def _unpad_point(
    point: tuple[float, float],
    offset_x: float,
    offset_y: float,
    width: int,
    height: int,
) -> tuple[float, float]:
    """Egy pont a padding nélküli kép koordinátáira, a képbe vágva."""
    return (
        min(float(width), max(0.0, point[0] - offset_x)),
        min(float(height), max(0.0, point[1] - offset_y)),
    )


def _box_area(face: FaceDetection) -> float:
    return max(0.0, face.right - face.left) * max(0.0, face.bottom - face.top)


def _boxes_overlap(first: FaceDetection, second: FaceDetection) -> bool:
    """Két keret IoU-ja eléri a `_CONSENSUS_MIN_IOU` küszöböt (#6439)."""
    inter_width = min(first.right, second.right) - max(first.left, second.left)
    inter_height = min(first.bottom, second.bottom) - max(first.top, second.top)
    if inter_width <= 0 or inter_height <= 0:
        return False
    intersection = inter_width * inter_height
    union = _box_area(first) + _box_area(second) - intersection
    return union > 0 and intersection / union >= _CONSENSUS_MIN_IOU


class FaceDetector:
    """`cv2.FaceDetectorYN` hiánytűrő becsomagolása.

    Modell/API hiányában `available=False`, a `detect()` üres tuple-t ad —
    az elérhetőség ellenőrzése és a modell betöltése csak első kéréskor fut.
    NINCS kivétel, NINCS crash a hívóig (ld. modul-docstring). Ha az első
    YuNet-menet nem talál arcot, a képet kisebb méretben, élismétlő paddinggel
    egyszer újrapróbálja, majd a találatokat visszateszi a bemenet
    koordinátáira. Ha a két 0,9-es menet is üres, a 0,8-0,9 közti jelöltek
    csak akkor számítanak arcnak, ha a második menet ugyanott megerősíti őket
    (#6439, `_detect_consensus`)."""

    def __init__(
        self,
        model_path: Path | None = None,
        score_threshold: float = _DEFAULT_SCORE_THRESHOLD,
        nms_threshold: float = _DEFAULT_NMS_THRESHOLD,
        top_k: int = _DEFAULT_TOP_K,
    ) -> None:
        self._initialized = False
        self._available = False
        self._init_lock = threading.Lock()
        self._detector = None
        self._consensus_engine = None
        self._score_threshold = score_threshold
        self._nms_threshold = nms_threshold
        self._top_k = top_k
        self.model_path = model_path if model_path is not None else resolve_model_path()
        if self.model_path is None:
            self._initialize()

    @property
    def available(self) -> bool:
        """Igaz, ha a modell ténylegesen betölthető.

        Az alkalmazás induláskor létrehozza ezt a szolgáltatót, de a
        könyvtárnézethez nincs szükség OpenCV-re; a kérdés első megválaszolása
        indítja el a modell/API ellenőrzését.
        """
        self._initialize()
        return self._available

    @available.setter
    def available(self, value: bool) -> None:
        self._available = bool(value)
        self._initialized = True

    def _initialize(self) -> None:
        with self._init_lock:
            if self._initialized:
                return
            self._initialized = True
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
                    score_threshold=self._score_threshold,
                    nms_threshold=self._nms_threshold,
                    top_k=self._top_k,
                )
            except cv2.error as error:  # pragma: no cover — sérült modellfájl
                logger.warning(
                    "Az arcfelismerő modell betöltése sikertelen (%s) — a "
                    "funkció kikapcsolva.",
                    error,
                )
                self._detector = None
                return
            self._available = True

    def detect(self, image_bgr: np.ndarray | None) -> tuple[FaceDetection, ...]:
        """Detektálás a MÁR dekódolt BGR képen — nincs extra fájlolvasás.

        Modell hiányában, vagy hibás/üres bemenetre üres tuple (nem hiba).
        """
        if not self.available or self._detector is None:
            return ()
        if image_bgr is None or image_bgr.size == 0:
            return ()
        try:
            return self._detect_any(image_bgr)
        except cv2.error as error:  # pragma: no cover — hibás kép/dekódolás
            logger.warning("Arc-detektálás sikertelen: %s", error)
            return ()

    def _detect_any(self, image_bgr: np.ndarray) -> tuple[FaceDetection, ...]:
        """Az 0,9-es menetek, majd az egyetértési sáv (#6439). Az első
        nem üres eredmény nyer; a sáv csak akkor fut, ha a két 0,9-es menet
        üres."""
        return (
            self._detect_once(image_bgr)
            or self._detect_with_padding(image_bgr)
            or self._detect_consensus(image_bgr)
        )

    def _detect_consensus(self, image_bgr: np.ndarray) -> tuple[FaceDetection, ...]:
        """#6439: a 0,8 és 0,9 közötti első menetbeli jelölt csak akkor számít
        arcnak, ha a kicsinyített, paddingelt második menet ugyanott, ugyanilyen
        alsó küszöbön is talál arcot. Egyetlen menet bizonyítéka nem elég."""
        engine = self._consensus_detector()
        candidates = self._detect_once(image_bgr, engine)
        if not candidates:
            return ()
        confirmations = self._detect_with_padding(image_bgr, engine)
        return tuple(
            candidate
            for candidate in candidates
            if any(_boxes_overlap(candidate, other) for other in confirmations)
        )

    def _consensus_detector(self):
        """A `_CONSENSUS_SCORE_FLOOR` küszöbű motor, az első szükség esetén
        példányosítva. A 0,9-es motor (és a default konstruktor) változatlan
        marad; a sáv csak az üres képeken kerül elő, így a költség is csak
        ott nő."""
        if self._consensus_engine is None:
            self._consensus_engine = cv2.FaceDetectorYN.create(
                str(self.model_path),
                "",
                (0, 0),
                score_threshold=_CONSENSUS_SCORE_FLOOR,
                nms_threshold=_DEFAULT_NMS_THRESHOLD,
                top_k=_DEFAULT_TOP_K,
            )
        return self._consensus_engine

    def _detect_once(
        self, image_bgr: np.ndarray, engine=None
    ) -> tuple[FaceDetection, ...]:
        engine = self._detector if engine is None else engine
        height, width = image_bgr.shape[:2]
        engine.setInputSize((width, height))
        _count, faces = engine.detect(image_bgr)
        if faces is None:
            return ()
        return tuple(_parse_row(row) for row in faces)

    def _detect_with_padding(
        self, image_bgr: np.ndarray, engine=None
    ) -> tuple[FaceDetection, ...]:
        """Az üres első menet kisebb, élismétléssel kipótolt bemenete.

        A keret és az öt jellegzetes pont koordinátáját visszaváltja az
        eredeti BGR kép rácsára, és a padding területéről érkező találatot
        eldobja.
        """
        height, width = image_bgr.shape[:2]
        small_width = max(1, round(width * _SECOND_PASS_SCALE))
        small_height = max(1, round(height * _SECOND_PASS_SCALE))
        smaller = cv2.resize(
            image_bgr,
            (small_width, small_height),
            interpolation=cv2.INTER_AREA,
        )
        pad_x = max(1, round(small_width * _SECOND_PASS_PADDING))
        pad_y = max(1, round(small_height * _SECOND_PASS_PADDING))
        padded = cv2.copyMakeBorder(
            smaller,
            pad_y,
            pad_y,
            pad_x,
            pad_x,
            cv2.BORDER_REPLICATE,
        )

        padded_height, padded_width = padded.shape[:2]
        target_dimension = min(
            _SECOND_PASS_MAX_DIMENSION,
            max(1, int(max(width, height) * 0.99)),
        )
        scale = min(1.0, target_dimension / max(padded_width, padded_height))
        if scale < 1.0:
            detector_width = max(1, round(padded_width * scale))
            detector_height = max(1, round(padded_height * scale))
            detector_image = cv2.resize(
                padded,
                (detector_width, detector_height),
                interpolation=cv2.INTER_AREA,
            )
        else:
            detector_image = padded
            detector_height, detector_width = padded_height, padded_width

        detections = self._detect_once(detector_image, engine)
        if not detections:
            return ()

        scale_x = (padded_width / detector_width) * (width / small_width)
        scale_y = (padded_height / detector_height) * (height / small_height)
        offset_x = pad_x * (width / small_width)
        offset_y = pad_y * (height / small_height)
        mapped: list[FaceDetection] = []
        for detection in detections:
            unpadded = rescale_face_detection(detection, scale_x, scale_y)
            left = unpadded.left - offset_x
            top = unpadded.top - offset_y
            right = unpadded.right - offset_x
            bottom = unpadded.bottom - offset_y
            if right <= 0 or bottom <= 0 or left >= width or top >= height:
                continue

            left = max(0.0, left)
            top = max(0.0, top)
            right = min(float(width), right)
            bottom = min(float(height), bottom)
            if right <= left or bottom <= top:
                continue

            landmarks = unpadded.landmarks
            mapped.append(
                FaceDetection(
                    left=left,
                    top=top,
                    right=right,
                    bottom=bottom,
                    score=unpadded.score,
                    landmarks=FaceLandmarks(
                        right_eye=_unpad_point(
                            landmarks.right_eye, offset_x, offset_y, width, height
                        ),
                        left_eye=_unpad_point(
                            landmarks.left_eye, offset_x, offset_y, width, height
                        ),
                        nose=_unpad_point(
                            landmarks.nose, offset_x, offset_y, width, height
                        ),
                        mouth_right=_unpad_point(
                            landmarks.mouth_right, offset_x, offset_y, width, height
                        ),
                        mouth_left=_unpad_point(
                            landmarks.mouth_left, offset_x, offset_y, width, height
                        ),
                    ),
                )
            )
        return tuple(mapped)


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
