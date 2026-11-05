"""Az Időrend hátterének képpontos lépéssora (#6577)."""

import numpy as np
from PySide6.QtCore import QSize
from PySide6.QtGui import QImage

from picasapy.app.timeline_background import (
    TimelineBackgroundProvider,
    create_timeline_overlay,
    prepare_timeline_background,
    render_timeline_background,
)
from picasapy.render.native_tone import native_gamma_lut
from picasapy.render.ops_levels import apply_enhance


def _rgb_to_qimage(image: np.ndarray) -> QImage:
    height, width = image.shape[:2]
    return QImage(
        image.data, width, height, width * 3, QImage.Format.Format_RGB888
    ).copy()


def test_background_steps_match_center_green_enhance_then_gamma_bytes():
    source = np.array(
        [
            [[10, 20, 240], [20, 70, 230], [30, 130, 220], [40, 240, 210]],
            [[50, 35, 200], [60, 95, 190], [70, 180, 180], [80, 225, 170]],
        ],
        dtype=np.uint8,
    )

    # A cél 2×2 képpont, így a 4×2 forrásból a két középső oszlop kerül be.
    centered = source[:, 1:3]
    green_gray = np.repeat(centered[:, :, 1:2], 3, axis=2)
    enhanced = apply_enhance(green_gray)
    expected = native_gamma_lut(3.0)[enhanced]

    actual = prepare_timeline_background(source, 2, 2)

    np.testing.assert_array_equal(actual, expected)
    assert np.array_equal(actual[:, :, 0], actual[:, :, 1])
    assert np.array_equal(actual[:, :, 1], actual[:, :, 2])


def test_overlay_is_drawn_and_keeps_source_alpha_in_native_range():
    overlay = create_timeline_overlay(96, 72)

    assert overlay.shape == (72, 96, 4)
    alpha = overlay[:, :, 3]
    assert int(alpha.min()) >= 179
    assert int(alpha.max()) <= 255
    assert len(np.unique(alpha)) > 1


def test_render_composites_the_overlay_after_gamma_processing():
    source = np.array(
        [
            [[10, 40, 240], [20, 100, 220]],
            [[30, 160, 200], [40, 220, 180]],
        ],
        dtype=np.uint8,
    )
    prepared = prepare_timeline_background(source, 2, 2)
    overlay = create_timeline_overlay(2, 2)
    alpha = overlay[:, :, 3:4].astype(np.uint16)
    expected = (
        prepared.astype(np.uint16) * (255 - alpha)
        + overlay[:, :, :3].astype(np.uint16) * alpha
        + 127
    ) // 255

    actual = render_timeline_background(source, 2, 2)

    np.testing.assert_array_equal(actual, expected.astype(np.uint8))


def test_provider_reuses_a_paused_background_for_the_same_photo_and_size():
    class ThumbnailSource:
        calls = 0

        def requestImage(self, photo_id, size, requested_size):  # noqa: N802
            self.calls += 1
            assert photo_id == "selected-photo"
            return _rgb_to_qimage(
                np.array(
                    [
                        [[15, 35, 240], [45, 125, 200]],
                        [[75, 185, 160], [105, 225, 120]],
                    ],
                    dtype=np.uint8,
                )
            )

    thumbnails = ThumbnailSource()
    provider = TimelineBackgroundProvider(thumbnails)
    size = QSize()
    requested_size = QSize(2, 2)

    first = provider.requestImage("selected-photo", size, requested_size)
    second = provider.requestImage("selected-photo", size, requested_size)

    assert not first.isNull()
    assert first == second
    assert size == QSize(2, 2)
    assert thumbnails.calls == 1


def test_overlay_matches_the_measured_original_layer_values():
    """Az eredeti `overlays/overlay` mért értékei: átlátszatlan 138-as alap,
    a jobb felső oválison (52, 57, 68) színű, 179-es alfájú áttetsző mező."""
    overlay = create_timeline_overlay(640, 480)

    assert overlay[60, 20].tolist() == [138, 138, 138, 255]
    assert overlay[150, 432].tolist() == [52, 57, 68, 179]
    assert overlay[200, 600].tolist() == [52, 57, 68, 179]
    # az ovális bal széle a mért 68. oszlopnál, alsó széle a 352. sornál
    assert overlay[150, 60, 3] == 255
    assert overlay[150, 80, 3] == 179
    assert overlay[340, 432, 3] == 179
    assert overlay[365, 432, 3] == 255
    # az alsó sáv legvilágosabb sora (408) és alja (186); a színátmenet
    # kerekítése legfeljebb 2 szint (a mért alap maga is 135-142 között szór)
    assert np.all(np.abs(overlay[408, 320, :3].astype(int) - 211) <= 2)
    assert np.all(np.abs(overlay[470, 320, :3].astype(int) - 186) <= 2)


def test_photo_shows_through_only_the_oval():
    """A kép csak az áttetsző oválison át változtatja a kimenetet."""
    dark = np.zeros((480, 640, 3), dtype=np.uint8)
    bright = np.full((480, 640, 3), 255, dtype=np.uint8)
    out_dark = render_timeline_background(dark, 640, 480)
    out_bright = render_timeline_background(bright, 640, 480)

    assert out_dark[60, 20].tolist() == out_bright[60, 20].tolist()
    assert out_dark[150, 432].tolist() != out_bright[150, 432].tolist()
