"""SFace arc-lenyomat (`cv2.FaceRecognizerSF`) — hiánytűrő becsomagolás.

A modellt a program csomagolja, így a tiszta telepítés hálózat nélkül is
képes csoportosítani. A kifejezett `PICASAPY_FACE_EMBED_MODEL` felülbírálás
után a csomagolt modell következik, majd a korábban letöltött felhasználói
modell. A letöltés csak tartalék útvonal marad.

A `FaceEmbedder` konstruktora modell/API-hiba esetén `available=False`-ra
áll, a `compute()` pedig `None`-t ad; a konstruktor soha nem kezdeményez
hálózati kérést."""

from __future__ import annotations

import logging
import os
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
    # függősége (thumbs/scanner/detector), ez az ág csak extra védelem
    cv2 = None  # type: ignore[assignment]

from .detector import FaceDetection, default_model_dir

logger = logging.getLogger(__name__)

#: Ezzel a környezeti változóval a modellfájl útvonala felülbírálható —
#: külön a YuNet-detektor `PICASAPY_FACE_MODEL`-jétől, mert két különböző
#: ONNX-fájlról van szó.
MODEL_ENV_VAR = "PICASAPY_FACE_EMBED_MODEL"

MODEL_FILENAME = "face_recognition_sface_2021dec.onnx"

# A hivatalos, Apache 2.0 licencű forrás (OpenCV Zoo) — a licenc GPL-3.0-
# kompatibilitása az issue #26 kommentjében ellenőrizve (2026-08-07-i mérés:
# YuNet MIT, SFace Apache 2.0, mindkettő permisszív).
MODEL_DOWNLOAD_URL = (
    "https://github.com/opencv/opencv_zoo/raw/main/models/"
    "face_recognition_sface/face_recognition_sface_2021dec.onnx"
)

#: Az SFace kimenete 1×128 float32 (issue #26, 2026-08-07-i mérés: ténylegesen
#: lefuttatva, `nbytes=512`) — ez a hossz a tárolt lenyomatok ellenőrzésére.
EMBEDDING_DIM = 128


def default_model_path() -> Path:
    """Ugyanaz a felhasználói modell-mappa, mint a YuNet-nél — csak más
    fájlnévvel (`detector.default_model_dir`, SOHA nem a repóban)."""
    return default_model_dir() / MODEL_FILENAME


def bundled_model_path() -> Path | None:
    """A programmal csomagolt SFace-modell útvonala, ha jelen van."""
    candidate = Path(__file__).resolve().parent / "models" / MODEL_FILENAME
    return candidate if candidate.is_file() else None


def resolve_model_path() -> Path | None:
    """A ténylegesen a lemezen létező lenyomat-modell útvonala, vagy `None`.

    Sorrend: a `PICASAPY_FACE_EMBED_MODEL` környezeti változó (ha meg van
    adva és létezik), a programmal csomagolt modell, majd a felhasználói
    alapértelmezett hely, amely a tartalék letöltés célja."""
    override = os.environ.get(MODEL_ENV_VAR)
    candidates: list[Path] = [Path(override)] if override else []
    bundled = bundled_model_path()
    if bundled is not None:
        candidates.append(bundled)
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
    """A lenyomat-modell letöltése a megadott (vagy alapértelmezett) helyre.

    A csomagolt modell szokásos használatához nincs szükség rá; hiányzó
    modell esetén a vezérlő ellenőrzött tartalék útként hívhatja. Hálózat/
    lemez-hiba esetén csendesen `False`-t ad vissza, nem dob kivételt
    (`detector.download_model` mintája).

    #1496: a törzse ma az ELLENŐRZŐ letöltőé (méret + SHA-256) — az
    indoklás a `detector.download_model` docstringjében."""
    from .model_download import EMBEDDER_SPEC, download_spec

    return download_spec(EMBEDDER_SPEC, dest=dest, url=url, timeout=timeout).ok


def _detection_to_row(detection: FaceDetection) -> np.ndarray:
    """`FaceDetection` → az OpenCV `alignCrop`/YuNet-sor formátuma
    (keret(4) + 5 pont(10) + pontszám) — pontosan az az elrendezés, amit a
    `FaceDetectorYN.detect` ad, és amit a `FaceRecognizerSF.alignCrop` vár.
    Az oszloprend a `detector._parse_row` fordítottja."""
    width = detection.right - detection.left
    height = detection.bottom - detection.top
    landmarks = detection.landmarks
    values = [
        detection.left,
        detection.top,
        width,
        height,
        *landmarks.right_eye,
        *landmarks.left_eye,
        *landmarks.nose,
        *landmarks.mouth_right,
        *landmarks.mouth_left,
        detection.score,
    ]
    return np.array(values, dtype=np.float32).reshape(1, -1)


class FaceEmbedder:
    """`cv2.FaceRecognizerSF` hiánytűrő becsomagolása.

    Modell/API hiányában `available=False`, a `compute()` `None`-t ad —
    NINCS kivétel, NINCS crash a hívóig (ld. modul-docstring)."""

    def __init__(self, model_path: Path | None = None) -> None:
        self.available = False
        self._recognizer = None
        self.model_path = model_path if model_path is not None else resolve_model_path()
        if self.model_path is None:
            logger.info(
                "Arc-lenyomat modell nem található — a funkció kikapcsolva "
                "(a %s környezeti változóval vagy a %s helyre másolva "
                "adható meg; ld. picasapy.faces.embedder.download_model).",
                MODEL_ENV_VAR,
                default_model_path(),
            )
            return
        if cv2 is None or not hasattr(cv2, "FaceRecognizerSF"):
            logger.warning(
                "A telepített OpenCV build nem tartalmazza a "
                "FaceRecognizerSF API-t — a lenyomat-számítás kikapcsolva."
            )
            return
        try:
            self._recognizer = cv2.FaceRecognizerSF.create(str(self.model_path), "")
        except cv2.error as error:  # pragma: no cover — sérült modellfájl
            logger.warning(
                "Az arc-lenyomat modell betöltése sikertelen (%s) — a "
                "funkció kikapcsolva.",
                error,
            )
            self._recognizer = None
            return
        self.available = True

    def compute(
        self, image_bgr: np.ndarray | None, detection: FaceDetection
    ) -> np.ndarray | None:
        """Lenyomat a MÁR dekódolt BGR képen és a hozzá tartozó
        `FaceDetection`-ön — nincs extra fájlolvasás/újradetektálás.

        Modell hiányában, vagy hibás/üres bemenetre `None` (nem hiba)."""
        if not self.available or self._recognizer is None:
            return None
        if image_bgr is None or image_bgr.size == 0:
            return None
        row = _detection_to_row(detection)
        try:
            aligned = self._recognizer.alignCrop(image_bgr, row)
            feature = self._recognizer.feature(aligned)
        except cv2.error as error:  # pragma: no cover — hibás kép/pontok
            logger.warning("Arc-lenyomat számítása sikertelen: %s", error)
            return None
        return np.asarray(feature, dtype=np.float32).reshape(-1)
