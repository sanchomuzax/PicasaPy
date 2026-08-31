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

from typing import TYPE_CHECKING

# #1611: LUSTA ÚJRAEXPORT. A csomag korábban a betöltésekor behúzta az
# `align`-t, az pedig a **cv2**-t — MÉRVE 3150 ms MINDEN induláskor, akkor
# is, ha a felhasználó egyetlen arcot sem keres. A csapda az volt, hogy ez
# akkor is lefutott, ha valaki csak egy adatosztályt kért innen
# (`from picasapy.faces.detector import FaceDetection`): a Python az
# almodul importjához MINDIG lefuttatja a csomag `__init__`-jét.
#
# ⚠️ Ezért bukott a #1601 kísérlete: ott csak az `index/__init__.py`
# `face_groups`-importja lett lusta, a csomag `__init__`-je viszont maradt
# mohó — a lánc a másik ágon (`index/faces_detected.py` →
# `picasapy.faces.detector`) változatlanul behúzta a cv2-t. A halasztás
# csak akkor ér valamit, ha a csomag `__init__` sem importál semmit.
#
# A PEP 562 `__getattr__` az első NÉV-hivatkozáskor tölti be az almodult,
# tehát a `from picasapy.faces import FaceDetector` továbbra is működik —
# csak akkor fizet, amikor tényleg kell. A `TYPE_CHECKING` ág miatt a
# típusellenőrzés és a szerkesztő is látja a neveket.

if TYPE_CHECKING:  # pragma: no cover - csak a típusellenőrzőnek
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

#: név → az almodul, ami adja (a lusta betöltés térképe)
_NEV_MODULJA = {
    "AlignedFaceGeometry": "align",
    "AssignmentResult": "clustering",
    "DEFAULT_CLUSTER_THRESHOLD": "clustering",
    "DEFAULT_SUGGEST_THRESHOLD": "clustering",
    "EMBEDDING_DIM": "embedder",
    "FaceDetection": "types",
    "FaceDetector": "detector",
    "FaceEmbedder": "embedder",
    "FaceGroupCentroid": "clustering",
    "FaceLandmarks": "types",
    "PICASA_STEPS": "clustering",
    "assign_face": "clustering",
    "compute_alignment_geometry": "align",
    "cosine_similarity": "clustering",
    "default_model_path": "detector",
    "download_model": "detector",
    "eye_aligned_face_crop": "align",
    "resolve_model_path": "detector",
    "step_to_threshold": "clustering",
}


def __getattr__(nev: str):
    """PEP 562: a nevet adó almodult csak az első hivatkozáskor töltjük be."""
    modul_neve = _NEV_MODULJA.get(nev)
    if modul_neve is None:
        raise AttributeError(f"module {__name__!r} has no attribute {nev!r}")
    from importlib import import_module

    ertek = getattr(import_module(f".{modul_neve}", __name__), nev)
    globals()[nev] = ertek  # a következő hivatkozás már nem megy a __getattr__-en
    return ertek


def __dir__() -> list[str]:
    return sorted(__all__)


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
