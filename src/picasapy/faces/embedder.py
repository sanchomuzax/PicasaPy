"""SFace arc-lenyomat (`cv2.FaceRecognizerSF`) — hiánytűrő becsomagolás
(issue #26, 2. lépcső).

Ugyanaz a KRITIKUS környezeti korlát érvényes, mint a `detector.py`
YuNet-becsomagolására: a CI-ben (Ubuntu ÉS Windows) nincs garantált
hálózat, és a modellfájl nincs jelen. A `FaceEmbedder` konstruktora ezért
SOHA nem dob kivételt és SOHA nem blokkol hálózatra — modell hiányában
`available=False`-ra áll, a `compute()` csendben `None`-t ad. A detektálás
és minden más a lenyomat-számítás nélkül is teljes értékűen működik (ld.
issue #26 terve: „a lenyomat-számítás külön, alacsonyabb prioritású sor,
mint a detektálás — előbb legyen meg minden arc HELYE, a felismerés
ráér”).

A modell beszerzése KÜLÖN, explicit lépés (`download_model`) — ez sem
hívódik automatikusan indításkor vagy tesztben."""

from __future__ import annotations

import logging
import os
import urllib.request
from pathlib import Path

import numpy as np

try:
    import cv2
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


def resolve_model_path() -> Path | None:
    """A ténylegesen a lemezen létező lenyomat-modell útvonala, vagy `None`.

    Sorrend: a `PICASAPY_FACE_EMBED_MODEL` környezeti változó (ha meg van
    adva és létezik), majd a felhasználói alapértelmezett hely — a
    `detector.resolve_model_path` mintáját követi."""
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
    """A lenyomat-modell letöltése a megadott (vagy alapértelmezett) helyre.

    SOHA nem hívódik automatikusan — sem induláskor, sem tesztben, sem a
    `FaceEmbedder`-ből. Hálózat/lemez-hiba esetén csendesen `False`-t ad
    vissza, nem dob kivételt (`detector.download_model` mintája)."""
    target = Path(dest) if dest is not None else default_model_path()
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        tmp = target.with_suffix(target.suffix + ".part")
        with urllib.request.urlopen(url, timeout=timeout) as response:  # noqa: S310
            payload = response.read()
        tmp.write_bytes(payload)
        tmp.replace(target)
        return True
    except (OSError, ValueError) as error:
        logger.warning(
            "Az arc-lenyomat modell letöltése sikertelen (%s) — a funkció "
            "kikapcsolva marad, a modell kézzel is elhelyezhető: %s",
            error,
            target,
        )
        return False


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
