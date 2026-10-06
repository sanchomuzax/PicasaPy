"""Vörösszem-javítás csak az app által átadott YuNet-szemkörökön (#4261)."""

from pathlib import Path

import numpy as np

from picasapy.edit.session import EditSession
from picasapy.ini.filters import FilterOp
from picasapy.ini.redeye import EyeCircle64
from picasapy.ini.filters import serialize_filters
from picasapy.render.chain import apply_filters
from picasapy.render.ops import apply_redeye


def _mixed_eye_and_dress_image() -> np.ndarray:
    image = np.full((80, 100, 3), (120, 110, 105), dtype=np.uint8)
    image[16:24, 16:24] = (200, 20, 30)
    image[16:24, 36:44] = (210, 25, 35)
    image[58:72, 58:76] = (220, 30, 40)
    return image


def test_auto_eye_circles_correct_eyes_and_preserve_red_dress() -> None:
    image = _mixed_eye_and_dress_image()
    # A középpontok és sugarak normalizált eye64 adatok az app eredményéből.
    session = EditSession().set_redeye_regions(
        (),
        eye_circles=(EyeCircle64(0.2, 0.25, 0.1), EyeCircle64(0.4, 0.25, 0.1)),
    )
    assert serialize_filters(session.ops) == (
        "redeye=1,eye64(33334000199a),eye64(66664000199a);"
    )

    result = apply_filters(image, session.ops).image

    np.testing.assert_array_equal(result[19, 19], (20, 20, 20))
    np.testing.assert_array_equal(result[19, 39], (25, 25, 25))
    np.testing.assert_array_equal(result[58:72, 58:76], image[58:72, 58:76])


def test_legacy_redeye_flag_is_identity_for_every_image() -> None:
    image = _mixed_eye_and_dress_image()

    result = apply_filters(image, (FilterOp("redeye", ("1",)),)).image

    np.testing.assert_array_equal(result, image)


def test_model_missing_fallback_is_explicit_and_still_corrects_whole_image() -> None:
    image = _mixed_eye_and_dress_image()
    session = EditSession().set_redeye_regions((), full_image_fallback=True)
    assert serialize_filters(session.ops) == "redeye=1,autofull64();"

    result = apply_filters(image, session.ops).image

    np.testing.assert_array_equal(result[19, 19], (20, 20, 20))
    np.testing.assert_array_equal(result[62, 62], (30, 30, 30))


def test_empty_user_model_dir_uses_bundled_yunet_for_red_eye(monkeypatch, tmp_path):
    from picasapy.faces import redeye
    from picasapy.faces.detector import FaceDetection, FaceLandmarks

    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))
    monkeypatch.delenv("PICASAPY_FACE_MODEL", raising=False)
    redeye._default_detector.cache_clear()

    class _PackagedDetector:
        def __init__(self):
            from picasapy.faces.detector import resolve_model_path

            self.model_path = resolve_model_path()
            self.available = self.model_path is not None

        def detect(self, _image):
            return (
                FaceDetection(
                    left=10,
                    top=10,
                    right=50,
                    bottom=50,
                    score=0.99,
                    landmarks=FaceLandmarks(
                        right_eye=(20.0, 20.0),
                        left_eye=(40.0, 20.0),
                        nose=(30.0, 30.0),
                        mouth_right=(25.0, 40.0),
                        mouth_left=(35.0, 40.0),
                    ),
                ),
            )

    monkeypatch.setattr(redeye, "FaceDetector", _PackagedDetector)
    redeye._default_detector.cache_clear()
    try:
        image = _mixed_eye_and_dress_image()
        circles = redeye.detect_eye_circles(image)

        assert circles is not None
        result = apply_redeye(
            image,
            eye_circles=tuple(
                (circle.x, circle.y, circle.radius) for circle in circles
            ),
        )

        np.testing.assert_array_equal(result[19, 19], (20, 20, 20))
        np.testing.assert_array_equal(result[19, 39], (25, 25, 25))
        np.testing.assert_array_equal(result[58:72, 58:76], image[58:72, 58:76])
    finally:
        redeye._default_detector.cache_clear()


def test_render_chain_never_imports_face_detection() -> None:
    from picasapy.render import chain

    render_root = Path(chain.__file__).parent
    offenders = [
        str(path.relative_to(render_root))
        for path in render_root.rglob("*.py")
        if "picasapy.faces" in path.read_text(encoding="utf-8")
    ]

    assert offenders == []
