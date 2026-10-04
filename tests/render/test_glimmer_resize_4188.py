"""A Glimmer Resize legközelebbi-szomszéd útjának 16.16-os mintavétele (#4188)."""

from __future__ import annotations

import numpy as np
import pytest

from picasapy.render.glimmer_ops import resize_image


def _spec_szerinti_legkozelebbi(image: np.ndarray, width: int, height: int) -> np.ndarray:
    """Független NumPy-referencia a filterdesc-registry.md 5/d képletéhez."""
    source_height, source_width = image.shape[:2]
    scale_x = np.float32(source_width / width)
    scale_y = np.float32(source_height / height)

    start_x = np.float32(np.float32(0.5) * scale_x)
    q0 = int(np.trunc(start_x * np.float32(65536.0)))
    dx = int(np.trunc(scale_x * np.float32(65536.0)))
    q_x = q0 + np.arange(width, dtype=np.int64) * dx
    source_x = q_x >> 16

    target_centers_y = np.arange(height, dtype=np.float32) + np.float32(0.5)
    source_centers_y = target_centers_y * scale_y
    q_y = np.trunc(source_centers_y * np.float32(65536.0)).astype(np.int64)
    source_y = q_y >> 16
    return image[source_y[:, None], source_x[None, :]]


@pytest.mark.parametrize(
    ("source_width", "source_height", "width", "height"),
    [(5, 3, 3, 2), (4, 2, 7, 5), (8, 6, 4, 3), (5, 3, 8, 6)],
)
def test_smoothing_false_spec_szerinti_es_a_simitott_kimenet_valtozatlan(
    source_width: int, source_height: int, width: int, height: int
) -> None:
    image = np.arange(source_height * source_width * 3, dtype=np.uint8).reshape(
        source_height, source_width, 3
    )

    if (source_width, width) == (4, 7):
        scale_x = np.float32(source_width / width)
        q0 = int(np.trunc(np.float32(np.float32(0.5) * scale_x) * np.float32(65536.0)))
        dx = int(np.trunc(scale_x * np.float32(65536.0)))
        assert (q0, dx) == (18724, 37449)
        assert (q0 + 3 * dx) >> 16 == 1

    # A simított út 5/c-s regressziós mintája: ennek a jegynek változatlanul
    # kell hagynia az eredményt adó ytResampler-ágat.
    smooth_source = np.repeat(
        np.array([[0, 60], [120, 255]], dtype=np.uint8)[..., None], 3, axis=2
    )
    smooth_expected = np.array([[0, 28, 58], [59, 108, 157], [119, 188, 255]], dtype=np.uint8)
    np.testing.assert_array_equal(
        resize_image(smooth_source, 3, 3, smoothing=True)[..., 0], smooth_expected
    )

    expected = _spec_szerinti_legkozelebbi(image, width, height)
    actual = resize_image(image, width, height, smoothing=False)
    np.testing.assert_array_equal(actual, expected)
