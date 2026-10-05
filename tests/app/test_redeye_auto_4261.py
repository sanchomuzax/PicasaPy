"""Az automatikus vörösszem-találatszám ugyanazt a szemterületet használja (#4261)."""

from types import SimpleNamespace

import numpy as np
import pytest

from picasapy.faces.detector import FaceDetector
from picasapy.faces.redeye import EyeCircle
from picasapy.faces.redeye import detect_eye_circles, eye_circles_from_faces


@pytest.fixture
def provider(qt_app):
    from picasapy.app.edit_preview import EditPreviewProvider

    return EditPreviewProvider()


def _image_with_two_eyes_and_red_dress() -> np.ndarray:
    image = np.full((80, 100, 3), (120, 110, 105), dtype=np.uint8)
    image[16:24, 16:24] = (200, 20, 30)
    image[16:24, 36:44] = (210, 25, 35)
    image[58:72, 58:76] = (220, 30, 40)
    return image


def test_eye_circle_radius_uses_interpupillary_distance() -> None:
    face = SimpleNamespace(
        landmarks=SimpleNamespace(right_eye=(20.0, 30.0), left_eye=(60.0, 30.0))
    )

    assert eye_circles_from_faces((face,)) == (
        EyeCircle(20.0, 30.0, 8.0),
        EyeCircle(60.0, 30.0, 8.0),
    )


def test_missing_yunet_model_returns_fallback_signal_without_error(tmp_path) -> None:
    detector = FaceDetector(model_path=tmp_path / "missing-yunet.onnx")

    assert detect_eye_circles(_image_with_two_eyes_and_red_dress(), detector) is None


def test_auto_result_keeps_normalized_eye_circles(provider, monkeypatch, tmp_path) -> None:
    from picasapy.app import edit_preview

    image = _image_with_two_eyes_and_red_dress()
    monkeypatch.setattr(
        provider,
        "_resolve_source",
        lambda *_args, **_kwargs: image,
    )
    monkeypatch.setattr(
        provider,
        "_render_cached",
        lambda _key, source, _ops: source,
    )
    monkeypatch.setattr(edit_preview, "detect_eye_circles", lambda _image: (
        EyeCircle(20, 20, 8), EyeCircle(40, 20, 8)
    ))

    count, circles = provider.redeye_auto_result(
        "photo", tmp_path / "photo.png", ()
    )

    assert count == 2
    np.testing.assert_allclose(circles, ((0.2, 0.25, 0.1), (0.4, 0.25, 0.1)))


def test_feedback_uses_whole_image_fallback_when_model_is_missing(
    provider, monkeypatch, tmp_path
) -> None:
    from picasapy.app import edit_preview

    image = _image_with_two_eyes_and_red_dress()
    monkeypatch.setattr(
        provider,
        "_resolve_source",
        lambda *_args, **_kwargs: image,
    )
    monkeypatch.setattr(
        provider,
        "_render_cached",
        lambda _key, source, _ops: source,
    )
    monkeypatch.setattr(edit_preview, "detect_eye_circles", lambda _image: None)

    count, circles = provider.redeye_auto_result(
        "photo", tmp_path / "photo.png", ()
    )

    assert count == 3
    assert circles is None
