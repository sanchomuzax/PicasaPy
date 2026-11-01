"""A #6386 stockfotó-mérései a tényleges YuNet-modellel.

A szabad felhasználású képek forrása és licencük a fixture-könyvtár
`FORRASOK.md` fájljában található. A próba kifejezetten azt az esetet őrzi,
amikor a teljes képen talált arc szoros kivágása az első menetben kimarad.
"""

from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np
import pytest

from picasapy.cvimage import scale_down
from picasapy.faces.detector import (
    MAX_DETECTION_DIMENSION,
    FaceDetector,
    resolve_model_path,
)

_FIXTURES = Path(__file__).parents[1] / "fixtures" / "arcok_6386"
_REAL_MODEL = resolve_model_path()

pytestmark = pytest.mark.skipif(
    _REAL_MODEL is None,
    reason="A valódi YuNet-modell nem érhető el; a képes mérés kihagyva.",
)


def _load(name: str) -> np.ndarray:
    image = cv2.imread(str(_FIXTURES / name), cv2.IMREAD_COLOR)
    assert image is not None, f"Nem olvasható tesztkép: {name}"
    return scale_down(image, MAX_DETECTION_DIMENSION)


def test_whole_portrait_and_its_tight_crop_are_both_detected() -> None:
    """A `portre-5` egészben ad találatot, a 10%-kal bővített kivágás nem.

    Ez a teljes képes/kivágott pár a tulajdonos által leírt esetet követi.
    """
    detector = FaceDetector(model_path=_REAL_MODEL)

    whole = detector.detect(_load("portre-5.jpg"))
    crop_image = _load("portre-5-kivagas.jpg")
    crop = detector.detect(crop_image)

    assert whole, "A stockportré teljes képén legyen arc."
    assert crop, "Ugyanannak a portrénak a szoros kivágásán is legyen arc."
    height, width = crop_image.shape[:2]
    for face in crop:
        assert 0 <= face.left < face.right <= width
        assert 0 <= face.top < face.bottom <= height
        points = (
            face.landmarks.right_eye,
            face.landmarks.left_eye,
            face.landmarks.nose,
            face.landmarks.mouth_right,
            face.landmarks.mouth_left,
        )
        assert all(0 <= x <= width and 0 <= y <= height for x, y in points)


def test_second_pass_detects_other_large_close_portraits() -> None:
    """A teljes képes első menetben kimaradó arcokat is újra kell próbálni."""
    detector = FaceDetector(model_path=_REAL_MODEL)
    missing = {
        name: detector.detect(_load(name))
        for name in ("portre-4.jpg", "portre-6.jpg")
    }

    assert all(missing.values()), {
        name: len(faces) for name, faces in missing.items() if not faces
    }


def test_tight_and_stylized_portrait_crops_are_detected() -> None:
    """Hat közeli és két színes/monokróm poszterizált szemüveges kép."""
    detector = FaceDetector(model_path=_REAL_MODEL)
    names = [
        *(f"portre-{index}-kivagas.jpg" for index in (1, 3, 4, 5, 7, 8)),
        "portre-5-280-poszter-szemuveg.jpg",
        "portre-8-280-poszter-szemuveg.jpg",
    ]
    missing = {
        name: detector.detect(_load(name))
        for name in names
    }

    assert all(missing.values()), {
        name: len(faces) for name, faces in missing.items() if not faces
    }


def test_face_free_controls_remain_without_detections() -> None:
    """A meglévő üres képkontroll és színábra nem adhat téves találatot."""
    detector = FaceDetector(model_path=_REAL_MODEL)
    blank = np.zeros((200, 200, 3), dtype=np.uint8)
    colour_chart = _load("../golden_colab/forras.jpg")

    assert detector.detect(blank) == ()
    assert detector.detect(colour_chart) == ()
