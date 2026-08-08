"""#26, 1. lépcső: „Detektálás + arc-indexkép (szemvonalra igazítva) →
Névtelenek album, csoportosítás nélkül."

A csomag TISZTÁN a saját (nem-Picasa) arc-detektálásért felel — a Picasa
`faces=`/`deferredface` mezői ezt a réteget SOHA nem hívják, és fordítva:
a saját detektorunk csak ott fut, ahol nincs már ember által adott
névcímke (ld. `picasapy.app.face_scan_controller`).

Motor: `cv2.FaceDetectorYN` (YuNet, MIT licenc, ~227 KB ONNX-modell) — az
OpenCV-be épített API, nulla új futásidejű függőség (issue #26, a javaslat
méréssel ellenőrzött 2026-08-07-én). A modellfájl NEM kerül a repóba;
hiányában a `FaceDetector` tisztán, naplózott üzenettel kikapcsol — a
hívó minden más része változatlanul működik.

Ami ebben a lépcsőben SZÁNDÉKOSAN NINCS benne (a terv 2–6. lépcsője, ld.
issue #26): lenyomat-számítás (SFace) és csoportosítás, elnevezés/
Emberek-albumok, javaslat-munkafolyamat, kézi arctéglalap, ignorálás,
XMP-export."""

from __future__ import annotations

from .align import AlignedFaceGeometry, compute_alignment_geometry, eye_aligned_face_crop
from .detector import (
    FaceDetection,
    FaceDetector,
    FaceLandmarks,
    default_model_path,
    download_model,
    resolve_model_path,
)

__all__ = [
    "AlignedFaceGeometry",
    "FaceDetection",
    "FaceDetector",
    "FaceLandmarks",
    "compute_alignment_geometry",
    "default_model_path",
    "download_model",
    "eye_aligned_face_crop",
    "resolve_model_path",
]
