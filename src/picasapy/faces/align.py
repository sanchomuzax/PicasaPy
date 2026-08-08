"""Szemvonalra igazított arc-indexkép — a Picasa „Emberek" nézetének
jellegzetes kinézete (issue #26, 1. lépcső).

A geometria TISZTA matematika: a szemkoordináta-párból (jobb szem, bal
szem) forgatás+eltolás+skálázás számolódik, hogy a kimeneten a két szem
mindig ugyanott, vízszintesen üljön — függetlenül attól, hogy a pontok a
saját (YuNet) detektorunkból vagy a Picasa importált `leye`/`reye`
mezőiből származnak (ld. issue #26 kommentje: importált fotóknál a
Picasa-adatot kell használni a pontos egyezéshez).

`compute_alignment_geometry` a modelltől TELJESEN független — csak két
koordinátapárt és egy célméretet vár, ezért modell nélkül is tesztelhető
(a #26 kötelező-teszt szabálya)."""

from __future__ import annotations

import math
from dataclasses import dataclass

import cv2
import numpy as np

#: A két szem közti táv a kimeneti szélesség hányadaként (Picasa-szerű
#: arc-indexkép: a szemek nem a szélen, hanem a felső harmadban ülnek).
DEFAULT_EYE_DISTANCE_FRACTION = 0.35
#: A szemvonal magassága a kimeneti kép tetejétől, a magasság hányadaként.
DEFAULT_EYE_LINE_FRACTION = 0.38


@dataclass(frozen=True)
class AlignedFaceGeometry:
    """A szemvonalra igazító affin transzformáció paraméterei."""

    #: A két szem középpontja az EREDETI képen (pixel).
    center: tuple[float, float]
    #: A szemvonal elfordulása a vízszintestől, FOKBAN (óramutató járásával
    #: megegyező irány pozitív, `cv2.getRotationMatrix2D` konvenciója).
    angle_deg: float
    #: Az eredeti kép → kimeneti kép nagyítási tényezője.
    scale: float
    #: A kimeneti kép mérete (négyzet oldalhossza, pixelben).
    output_size: int
    #: A szemvonal célmagassága a kimeneten (a `output_size` hányadaként).
    eye_line_fraction: float


def compute_alignment_geometry(
    right_eye: tuple[float, float],
    left_eye: tuple[float, float],
    output_size: int = 256,
    eye_distance_fraction: float = DEFAULT_EYE_DISTANCE_FRACTION,
    eye_line_fraction: float = DEFAULT_EYE_LINE_FRACTION,
) -> AlignedFaceGeometry:
    """A szemvonalra igazítás geometriája — kizárólag a két szemkoordinátából
    és a kívánt kimeneti méretből, kép/modell nélkül.

    `right_eye`/`left_eye`: a detektor SAJÁT elnevezése szerint (a jobb
    szem a képen jellemzően a BAL oldalon van — ez nem számít a
    geometriának, csak a két pont relatív helyzete).
    """
    dx = left_eye[0] - right_eye[0]
    dy = left_eye[1] - right_eye[1]
    distance = math.hypot(dx, dy)
    angle_deg = math.degrees(math.atan2(dy, dx))
    target_distance = output_size * eye_distance_fraction
    scale = target_distance / distance if distance > 1e-6 else 1.0
    center = (
        (right_eye[0] + left_eye[0]) / 2.0,
        (right_eye[1] + left_eye[1]) / 2.0,
    )
    return AlignedFaceGeometry(
        center=center,
        angle_deg=angle_deg,
        scale=scale,
        output_size=output_size,
        eye_line_fraction=eye_line_fraction,
    )


def alignment_matrix(geometry: AlignedFaceGeometry) -> np.ndarray:
    """A `geometry` 2×3 affin mátrixa (`cv2.warpAffine`-nak közvetlenül
    átadható) — a szemközéppontot a kimenet vízszintes közepére és a
    `eye_line_fraction` magasságára viszi, a szemvonalat vízszintesre
    forgatva és a kívánt méretre skálázva."""
    matrix = cv2.getRotationMatrix2D(geometry.center, geometry.angle_deg, geometry.scale)
    target_x = geometry.output_size / 2.0
    target_y = geometry.output_size * geometry.eye_line_fraction
    matrix[0, 2] += target_x - geometry.center[0]
    matrix[1, 2] += target_y - geometry.center[1]
    return matrix


def eye_aligned_face_crop(
    image_bgr: np.ndarray,
    right_eye: tuple[float, float],
    left_eye: tuple[float, float],
    output_size: int = 256,
    eye_distance_fraction: float = DEFAULT_EYE_DISTANCE_FRACTION,
    eye_line_fraction: float = DEFAULT_EYE_LINE_FRACTION,
) -> np.ndarray:
    """A Picasa-szerű, szemvonalra igazított négyzetes arc-indexkép.

    A pontok PARAMÉTERKÉNT jönnek (saját detektor VAGY a Picasa importált
    `leye`/`reye` mezői) — a függvény maga nem detektál, ezért szintetikus
    képpel/kézzel megadott pontokkal modell nélkül is tesztelhető."""
    geometry = compute_alignment_geometry(
        right_eye, left_eye, output_size, eye_distance_fraction, eye_line_fraction
    )
    matrix = alignment_matrix(geometry)
    return cv2.warpAffine(
        image_bgr, matrix, (output_size, output_size), flags=cv2.INTER_LINEAR
    )
