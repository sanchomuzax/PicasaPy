"""A detektor ADATOSZTÁLYAI — cv2 nélkül (#1611).

**Miért külön modul.** A `detector.py` a betöltésekor importálja a **cv2**-t
(hiánytűrően, `try/except`-ben) — MÉRVE 895 ms. Az `index/faces_detected.py`
viszont csak ezt a két adatosztályt kérte tőle, amikhez a cv2-nek semmi köze:
a rekordokat az indexbe írja, nem detektál. Így minden induláskor betöltődött
az OpenCV, akkor is, ha a felhasználó egyetlen arcot sem keresett.

A `detector.py` változatlanul újraexportálja mindkét nevet, tehát a
`from picasapy.faces.detector import FaceDetection` továbbra is működik.
"""

from __future__ import annotations

from dataclasses import dataclass


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
