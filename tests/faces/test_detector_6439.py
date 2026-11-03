"""#6439: a 0,9 küszöb alatt, de a második menettel egyező jelöltek.

A stilizált (poszterizált, sötét szemüveges) kis portrék első menetben
0,85-0,90 közé esnek, és a kicsinyített, paddingelt második menetben ugyanott
jelennek meg. A nyilvános #6386 képek forrása és licencük a fixture-könyvtár
`FORRASOK.md` fájljában van.
"""

from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np
import pytest

from picasapy.cvimage import scale_down
from picasapy.faces.detector import (
    MAX_DETECTION_DIMENSION,
    FaceDetection,
    FaceDetector,
    FaceLandmarks,
    resolve_model_path,
)

_FIXTURES = Path(__file__).parents[1] / "fixtures" / "arcok_6386"
_REAL_MODEL = resolve_model_path()


def _load(name: str) -> np.ndarray:
    image = cv2.imread(str(_FIXTURES / name), cv2.IMREAD_COLOR)
    assert image is not None, f"Nem olvasható tesztkép: {name}"
    return scale_down(image, MAX_DETECTION_DIMENSION)


def _landmarks() -> FaceLandmarks:
    return FaceLandmarks(
        right_eye=(0.0, 0.0),
        left_eye=(0.0, 0.0),
        nose=(0.0, 0.0),
        mouth_right=(0.0, 0.0),
        mouth_left=(0.0, 0.0),
    )


def _face(left: float, top: float, size: float, score: float) -> FaceDetection:
    return FaceDetection(
        left=left,
        top=top,
        right=left + size,
        bottom=top + size,
        score=score,
        landmarks=_landmarks(),
    )


@pytest.mark.skipif(_REAL_MODEL is None, reason="A valódi YuNet-modell nem érhető el.")
@pytest.mark.parametrize(
    "name",
    ["portre-4-280-poszter-szemuveg.jpg", "portre-7-280-poszter-szemuveg.jpg"],
)
def test_stylized_small_portrait_confirmed_by_second_pass_is_detected(name: str) -> None:
    """Két nyilvános, poszterizált és szemüveges 280-as portré: legyen arc.

    Mindkettő első menete 0,85-0,90 közötti jelöltet ad, a második menet
    ugyanazt a helyet 0,85 fölött megerősíti. A 0,9-es küszöbbel ma egyik
    sincs találat.
    """
    detector = FaceDetector(model_path=_REAL_MODEL)
    image = _load(name)

    faces = detector.detect(image)

    assert faces, f"{name}: a második menettel megerősített arc kimaradt."
    height, width = image.shape[:2]
    for face in faces:
        assert 0 <= face.left < face.right <= width
        assert 0 <= face.top < face.bottom <= height


@pytest.mark.skipif(_REAL_MODEL is None, reason="A valódi YuNet-modell nem érhető el.")
def test_synthetic_grass_like_texture_stays_without_detections() -> None:
    """Zajos, zöldes textúra (fű-jelleg) nem adhat arcot a bővített úton sem."""
    rng = np.random.default_rng(6439)
    noise = rng.integers(0, 255, size=(640, 960, 3), dtype=np.uint8)
    grass = cv2.GaussianBlur(noise, (0, 0), 3.0)
    grass[..., 1] = np.clip(grass[..., 1].astype(int) + 40, 0, 255).astype(np.uint8)
    detector = FaceDetector(model_path=_REAL_MODEL)

    assert detector.detect(grass) == ()


def _detector_with_fake_passes(
    monkeypatch: pytest.MonkeyPatch,
    *,
    first: tuple[FaceDetection, ...],
    band_first: tuple[FaceDetection, ...],
    band_padded: tuple[FaceDetection, ...],
) -> tuple[FaceDetector, dict[str, int]]:
    """A menetek eredményét rögzíti; a sávos menetek a 0,8-as küszöb szerint szűrnek.

    A modell nélküli példány csak a döntési láncot futtatja: a motor-objektum
    jelzés (`None`-tól eltérő), a valódi OpenCV-hívás nincs.
    """
    detector = FaceDetector(model_path=Path("nincs-6439.onnx"))
    detector.available = True
    detector._detector = object()
    counts = {"strict_first": 0, "band_first": 0, "band_padded": 0}
    band_engine = object()

    def fake_once(image, engine=None):
        if engine is None:
            counts["strict_first"] += 1
            return tuple(c for c in first if c.score >= 0.9)
        counts["band_first"] += 1
        return tuple(c for c in band_first if c.score >= 0.8)

    def fake_padding(image, engine=None):
        if engine is None:
            return ()
        counts["band_padded"] += 1
        return tuple(c for c in band_padded if c.score >= 0.8)

    monkeypatch.setattr(detector, "_detect_once", fake_once)
    monkeypatch.setattr(detector, "_detect_with_padding", fake_padding)
    monkeypatch.setattr(detector, "_consensus_detector", lambda: band_engine)
    return detector, counts


def test_band_candidate_confirmed_by_second_pass_is_accepted(monkeypatch) -> None:
    """0,87-es első menet, ugyanott 0,86-os második menet: arc."""
    image = np.zeros((280, 280, 3), dtype=np.uint8)
    band = _face(60, 50, 150, 0.87)
    confirmed = _face(62, 52, 148, 0.86)
    detector, _counts = _detector_with_fake_passes(
        monkeypatch,
        first=(),
        band_first=(band,),
        band_padded=(confirmed,),
    )

    faces = detector.detect(image)

    assert len(faces) == 1
    assert faces[0].score == pytest.approx(0.87)


def test_band_candidate_without_second_pass_match_is_rejected(monkeypatch) -> None:
    """A második menet máshol lát arcot: az első menet 0,87-es jelöltje kimarad."""
    image = np.zeros((280, 280, 3), dtype=np.uint8)
    band = _face(60, 50, 150, 0.87)
    elsewhere = _face(200, 180, 60, 0.88)
    detector, _counts = _detector_with_fake_passes(
        monkeypatch,
        first=(),
        band_first=(band,),
        band_padded=(elsewhere,),
    )

    assert detector.detect(image) == ()


def test_second_pass_below_floor_does_not_confirm(monkeypatch) -> None:
    """A megerősítésnek is a sávküszöb fölött kell lennie (0,79 nem elég)."""
    image = np.zeros((280, 280, 3), dtype=np.uint8)
    band = _face(60, 50, 150, 0.87)
    weak = _face(60, 50, 150, 0.79)
    detector, _counts = _detector_with_fake_passes(
        monkeypatch,
        first=(),
        band_first=(band,),
        band_padded=(weak,),
    )

    assert detector.detect(image) == ()


def test_strict_hit_is_returned_without_consulting_the_band(monkeypatch) -> None:
    """A 0,9 fölötti találat változatlanul az első menetből jön, a sáv nem fut."""
    image = np.zeros((280, 280, 3), dtype=np.uint8)
    strict = _face(60, 50, 150, 0.95)
    detector, counts = _detector_with_fake_passes(
        monkeypatch,
        first=(strict,),
        band_first=(_face(10, 10, 40, 0.86),),
        band_padded=(_face(10, 10, 40, 0.86),),
    )

    faces = detector.detect(image)

    assert faces == (strict,)
    assert counts["band_first"] == 0
    assert counts["band_padded"] == 0
