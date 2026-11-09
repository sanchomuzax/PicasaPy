"""Az Időrend szórás-, vezetőpont- és feliratalfa-képletei (#6713)."""

from math import isclose
from pathlib import Path

from picasapy import timeline_motion


def test_stack_scatter_uses_a_stable_seed_and_the_original_range():
    first = timeline_motion.card_stack_offset(0, 0)
    assert first == timeline_motion.card_stack_offset(0, 0)
    assert all(
        isclose(actual, expected, rel_tol=0.0, abs_tol=1e-12)
        for actual, expected in zip(
            first,
            (-0.0371775510488078, -0.032783490931615235),
            strict=True,
        )
    )

    other = timeline_motion.card_stack_offset(0, 1)
    assert other == timeline_motion.card_stack_offset(0, 1)
    assert other != first
    assert all(-0.075 <= coordinate < 0.075 for coordinate in first + other)


def test_leader_curve_has_ten_original_cubic_bezier_samples():
    points = timeline_motion.timeline_leader_points((100.0, 200.0), (400.0, 300.0))

    assert len(points) == 10
    assert points[0] == (100.0, 200.0)
    assert points[-1] == (400.0, 300.0)
    assert isclose(points[1][0], 110.28806584362138, rel_tol=0.0, abs_tol=1e-12)
    assert isclose(points[1][1], 214.95198902606307, rel_tol=0.0, abs_tol=1e-12)
    assert isclose(points[5][0], 274.8971193415638, rel_tol=0.0, abs_tol=1e-12)
    assert isclose(points[5][1], 254.1838134430727, rel_tol=0.0, abs_tol=1e-12)


def test_label_and_shadow_alpha_use_the_original_integer_division():
    assert timeline_motion.timeline_text_alphas(0) == (0, 0)
    assert timeline_motion.timeline_text_alphas(128) == (127, 63)
    assert timeline_motion.timeline_text_alphas(256) == (255, 127)


def test_timeline_header_keeps_the_original_condensed_font_and_no_outline():
    qml = (
        Path(__file__).resolve().parents[2]
        / "src/picasapy/app/qml/PicasaPy/TimelinePanel.qml"
    ).read_text(encoding="utf-8")

    assert qml.count('font.family: "Helvetica Neue"') == 2
    assert 'font.styleName: "Medium Condensed"' in qml
    assert 'font.styleName: "Condensed"' in qml
    assert "style: Text.Outline" not in qml
