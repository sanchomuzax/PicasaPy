"""#26: saját (nem-Picasa) arcfelismerés — 1. lépcső: „Detektálás +
arc-indexkép (szemvonalra igazítva) → Névtelenek album, csoportosítás
nélkül.” 2. lépcső: „Lenyomat (SFace) + csoportosítás.”

A csomag TISZTÁN a saját arcfelismerésért felel — a Picasa
`faces=`/`deferredface` mezői ezt a réteget SOHA nem hívják, és fordítva:
a saját detektorunk csak ott fut, ahol nincs már ember által adott
névcímke (ld. `picasapy.app.face_scan_controller`).

Motor:
- **detektálás + 5 pont**: `cv2.FaceDetectorYN` (YuNet, MIT licenc,
  ~227 KB ONNX-modell).
- **lenyomat**: `cv2.FaceRecognizerSF` (SFace, Apache 2.0 licenc, ~37 MB
  ONNX-modell) — 128 float32/arc.

Mindkettő az OpenCV-be épített API, NULLA új futásidejű függőség (issue
#26, méréssel ellenőrizve: 2026-08-07). A modellfájlok NEM kerülnek a
repóba; hiányukban a `FaceDetector`/`FaceEmbedder` tisztán, naplózott
üzenettel kikapcsol — a hívó minden más része változatlanul működik.

A csoportosítás (`clustering.py`) tiszta matematika — klaszterező
könyvtár NÉLKÜL, koszinusz-hasonlóság + inkrementális centroid.

Ami ebben a lépcsőben SZÁNDÉKOSAN NINCS benne (a terv 3–6. lépcsője, ld.
issue #26): elnevezés/Emberek-albumok, javaslat-munkafolyamat (a
javaslatok DB-perzisztenciája/UI-ja), kézi arctéglalap, ignorálás,
XMP-export."""

from __future__ import annotations

from .align import AlignedFaceGeometry, compute_alignment_geometry, eye_aligned_face_crop
from .clustering import (
    DEFAULT_CLUSTER_THRESHOLD,
    DEFAULT_SUGGEST_THRESHOLD,
    PICASA_STEPS,
    AssignmentResult,
    FaceGroupCentroid,
    assign_face,
    cosine_similarity,
    step_to_threshold,
)
from .detector import (
    FaceDetection,
    FaceDetector,
    FaceLandmarks,
    default_model_path,
    download_model,
    resolve_model_path,
)
from .embedder import EMBEDDING_DIM, FaceEmbedder
from .model_download import (
    MODEL_SPECS,
    DownloadResult,
    ModelSpec,
    download_missing,
    download_spec,
    missing_specs,
    total_missing_bytes,
)

__all__ = [
    "DEFAULT_CLUSTER_THRESHOLD",
    "DEFAULT_SUGGEST_THRESHOLD",
    "EMBEDDING_DIM",
    "MODEL_SPECS",
    "PICASA_STEPS",
    "AlignedFaceGeometry",
    "AssignmentResult",
    "DownloadResult",
    "FaceDetection",
    "FaceDetector",
    "FaceEmbedder",
    "FaceGroupCentroid",
    "FaceLandmarks",
    "ModelSpec",
    "assign_face",
    "compute_alignment_geometry",
    "cosine_similarity",
    "default_model_path",
    "download_missing",
    "download_model",
    "download_spec",
    "eye_aligned_face_crop",
    "missing_specs",
    "resolve_model_path",
    "step_to_threshold",
    "total_missing_bytes",
]
