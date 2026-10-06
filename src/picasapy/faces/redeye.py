"""YuNet arcpontokból számolt vörösszem-javítási szemterületek (#4261)."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from functools import lru_cache
from math import hypot

import numpy as np

from picasapy.cvimage import scale_down
from picasapy.faces.detector import (
    MAX_DETECTION_DIMENSION,
    FaceDetection,
    FaceDetector,
    rescale_face_detection,
    resolve_model_path,
)

_EYE_RADIUS_TO_DISTANCE = 0.2


@dataclass(frozen=True)
class EyeCircle:
    """Egy szem kör alakú területe képpont-koordinátákban."""

    x: float
    y: float
    radius: float


@lru_cache(maxsize=1)
def _default_detector() -> FaceDetector:
    """Megosztott YuNet-detektor; a konstruktor modell nélkül is hibamentes."""
    return FaceDetector()


def _current_detector() -> FaceDetector:
    detector = _default_detector()
    if detector.model_path is None and resolve_model_path() is not None:
        _default_detector.cache_clear()
        detector = _default_detector()
    return detector


def eye_circles_from_faces(
    faces: Iterable[FaceDetection],
) -> tuple[EyeCircle, ...]:
    """A két szempont köré a szemtávolság ötödének megfelelő sugarat ad."""
    circles: list[EyeCircle] = []
    for face in faces:
        right = face.landmarks.right_eye
        left = face.landmarks.left_eye
        radius = (
            hypot(right[0] - left[0], right[1] - left[1])
            * _EYE_RADIUS_TO_DISTANCE
        )
        if radius <= 0:
            continue
        circles.extend((EyeCircle(*right, radius), EyeCircle(*left, radius)))
    return tuple(circles)


def detect_eye_circles(
    image_rgb: np.ndarray,
    detector: FaceDetector | None = None,
) -> tuple[EyeCircle, ...] | None:
    """Szemterületek képen, vagy `None`, ha a YuNet-modell/API nem elérhető.

    A detektor BGR-t vár; a renderer RGB tömbjét ezért másolva alakítjuk át.
    Üres tuple azt jelenti, hogy a modell működik, de nem talált használható
    arcot — ilyenkor a vörös ruha nem kaphat teljes képes tartalék-kezelést.
    """
    if image_rgb is None or image_rgb.size == 0:
        return ()
    engine = detector if detector is not None else _current_detector()
    if not engine.available:
        return None
    image_bgr = np.ascontiguousarray(image_rgb[..., ::-1])
    detector_image = scale_down(image_bgr, MAX_DETECTION_DIMENSION)
    detections = engine.detect(detector_image)
    if detector_image.shape[:2] != image_rgb.shape[:2]:
        height, width = image_rgb.shape[:2]
        detector_height, detector_width = detector_image.shape[:2]
        detections = tuple(
            rescale_face_detection(
                detection,
                width / detector_width,
                height / detector_height,
            )
            for detection in detections
        )
    return eye_circles_from_faces(detections)
