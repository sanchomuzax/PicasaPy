"""A teljes képernyős Időrend binárisból mért képletei (#5377)."""

from math import isclose

from picasapy.timeline_motion import (
    blend_channel,
    frame_transforms,
    rational_cubic_bezier,
    random_slide_offsets,
    slider_index,
    slider_thumb_x,
    slideshow_easing,
    timeline_dot_positions,
)


_CONTROL_POINTS = (
    (-3.0, -3.0, 10.0),
    (-1.0, -0.5, 4.0),
    (-0.3, 0.9, 0.6),
    (0.9, 0.75, 1.1),
)


def _close_tuple(actual, expected, *, abs_tol=1e-6):
    assert len(actual) == len(expected)
    for got, want in zip(actual, expected, strict=True):
        assert isclose(got, want, rel_tol=0.0, abs_tol=abs_tol)


def test_rational_cubic_bezier_matches_picasa_qemu_points():
    # docs/specs/picasa-idorend-bemutato-kutatas.md 38.2.61.
    expected = (
        (0.150000006, 0.150000006, 0.100000001),
        (0.0983935595, 0.297188729, 0.321285158),
        (0.863636315, 0.727272749, 0.909090877),
    )
    for t, point in zip((0.0, 0.5, 1.0), expected, strict=True):
        _close_tuple(rational_cubic_bezier(t, _CONTROL_POINTS), point)


def test_frame_transforms_match_picasa_qemu_points():
    # docs/specs/picasa-idorend-bemutato-kutatas.md 38.2.62.
    frame = frame_transforms(
        0.5,
        current_offset=(0.25, -0.125),
        previous_offset=(-0.5, 0.25),
    )
    _close_tuple(
        (frame["current"]["scale"], frame["current"]["tx"], frame["current"]["ty"]),
        (0.906817794, 1.0390625, 0.98046875),
    )
    _close_tuple(
        (frame["previous"]["scale"], frame["previous"]["tx"], frame["previous"]["ty"]),
        (0.851463497, 0.578125, 1.2109375),
    )
    assert frame["alpha"] == 0

    at_three_quarters = frame_transforms(
        0.75,
        current_offset=(0.25, -0.125),
        previous_offset=(-0.5, 0.25),
    )
    _close_tuple(
        (
            at_three_quarters["current"]["scale"],
            at_three_quarters["current"]["tx"],
            at_three_quarters["current"]["ty"],
        ),
        (0.901464462, 1.07910156, 0.960449219),
    )
    _close_tuple(
        (
            at_three_quarters["previous"]["scale"],
            at_three_quarters["previous"]["tx"],
            at_three_quarters["previous"]["ty"],
        ),
        (0.820868850, 0.521484375, 1.23925781),
    )
    assert at_three_quarters["alpha"] == 55
    at_one = frame_transforms(
        1.0,
        current_offset=(0.25, -0.125),
        previous_offset=(-0.5, 0.25),
    )
    _close_tuple(
        (
            at_one["current"]["scale"],
            at_one["current"]["tx"],
            at_one["current"]["ty"],
        ),
        (0.891218841, 1.125, 0.9375),
    )
    _close_tuple(
        (
            at_one["previous"]["scale"],
            at_one["previous"]["tx"],
            at_one["previous"]["ty"],
        ),
        (0.783410192, 0.5, 1.25),
    )
    assert at_one["alpha"] == 256


def test_first_timeline_frame_uses_the_measured_identity_previous_matrix():
    frame = frame_transforms(
        0.0,
        current_offset=(0.25, -0.125),
        previous_offset=(-0.5, 0.25),
        previous_present=False,
    )
    _close_tuple(
        (
            frame["previous"]["scale"],
            frame["previous"]["tx"],
            frame["previous"]["ty"],
        ),
        (1.0, 0.0, 0.0),
    )
    _close_tuple(
        (
            frame["current"]["scale"],
            frame["current"]["tx"],
            frame["current"]["ty"],
        ),
        (0.909090877, 1.0, 1.0),
    )
    halfway = frame_transforms(
        0.5,
        current_offset=(0.25, -0.125),
        previous_offset=(-0.5, 0.25),
        previous_present=False,
    )
    _close_tuple(
        (
            halfway["current"]["scale"],
            halfway["current"]["tx"],
            halfway["current"]["ty"],
        ),
        (0.906817794, 1.0390625, 0.98046875),
    )
    with_previous = frame_transforms(
        0.0,
        current_offset=(0.25, -0.125),
        previous_offset=(-0.5, 0.25),
        previous_present=True,
    )
    _close_tuple(
        (
            with_previous["previous"]["scale"],
            with_previous["previous"]["tx"],
            with_previous["previous"]["ty"],
        ),
        (0.891218841, 0.75, 1.125),
    )


def test_easing_matches_picasa_qemu_points():
    # picasa-idorend-viselkedes.md 38.2.32, 0x0072df60.
    expected = (
        (0.0, 0.0),
        (-0.25, 0.0),
        (0.125, 0.368091643),
        (0.25, 0.76789844),
        (0.5, 0.969087183),
        (0.75, 0.996315122),
        (0.875, 0.999008954),
        (1.0, 1.0),
    )
    for progress, value in expected:
        assert isclose(
            slideshow_easing(progress), value, rel_tol=0.0, abs_tol=1e-6
        )


def test_alpha_blend_matches_picasa_qemu_bytes():
    # A forráscsatornák: X=(20, 40), Y=(220, 200), 38.2.64 §3.
    assert [blend_channel(20, 220, alpha) for alpha in (0, 1)] == [219, 219]
    assert [blend_channel(20, 220, alpha) for alpha in (128, 255, 256)] == [119, 20, 19]
    assert [blend_channel(40, 200, alpha) for alpha in (0, 128, 255, 256)] == [199, 119, 40, 39]


def test_random_slide_offsets_match_picasa_qemu_points_and_keep_previous():
    previous = (0.25, -0.125)
    samples = (
        (0, 0, (0.0, 0.0)),
        (32767, 32767, (95.9970550537, 35.9988975525)),
        (16384, 32767, (95.9970550537, 17.9999961853)),
    )
    for rand_y, rand_x, expected in samples:
        current, old = random_slide_offsets(
            previous,
            rand_y=rand_y,
            rand_x=rand_x,
            width=640,
            height=480,
        )
        _close_tuple(current, expected)
        assert old == previous


def test_slider_mapping_matches_picasa_qemu_edges_and_ties():
    values = [0.0, 0.25, 0.5, 1.0]
    samples = ((50, 0), (100, 0), (150, 0), (200, 1), (300, 2), (400, 2), (500, 3), (550, 3))
    for x, expected_index in samples:
        ratio = min(1.0, max(0.0, (x - 100) / 400))
        assert slider_index(values, ratio) == expected_index
    assert [slider_thumb_x(x, left=100, width=400, thumb_width=24) for x in (50, 100, 150, 200, 300, 400, 500, 550)] == [85, 85, 135, 185, 285, 385, 485, 485]


def test_timeline_dot_positions_match_picasa_qemu_duplicate_branches():
    common = dict(
        x_start=200,
        track_span_minus_four=100,
        dot_width=10,
        y_top=40,
        track_spacing=5,
        dot_height=10,
    )
    two = timeline_dot_positions([0.125, 0.5], **common)
    assert (two[-1]["x"], two[-1]["y"], two[-1]["draw"]) == (295, 20, True)
    three = timeline_dot_positions([0.125, 0.5, 0.5], **common)
    assert (three[-1]["x"], three[-1]["y"], three[-1]["draw"]) == (295, 13, True)
    four = timeline_dot_positions([0.125, 0.5, 0.5, 0.5], **common)
    assert (four[-1]["x"], four[-1]["y"], four[-1]["draw"]) == (295, 13, False)
    five = timeline_dot_positions([0.125, 0.5, 0.5, 0.5, 0.5], **common)
    assert (five[-1]["x"], five[-1]["y"], five[-1]["draw"]) == (295, 6, True)
