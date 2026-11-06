"""#6617: a colorfix natív filters-sorrendje és régi mentések migrációja."""

from __future__ import annotations

import numpy as np
import pytest

from picasapy.app.effect_params import effect_params, format_param_values
from picasapy.edit.session import EditSession
from picasapy.ini.filters import (
    FilterOp,
    parse_filters,
    parse_filters_prefix,
    serialize_filters_for_write,
)
from picasapy.render.autocolor_matrix import (
    apply_autocolor_matrix,
    autocolor_matrix_16_16,
)
from picasapy.render.chain import apply_filters
from picasapy.render.native_colortemp import apply_native_colortemp
from picasapy.render.tinting import parse_rgb_hex


def _photo() -> np.ndarray:
    return np.array(
        [
            [[35, 90, 155], [80, 130, 205]],
            [[145, 175, 220], [215, 205, 185]],
        ],
        dtype=np.uint8,
    )


# A #6585 job-407 mért táblázat colorfix-sorai. A Picasa csak a két
# numerikus első mezőjű sort alkalmazta; a hexadecimális első mező a korábbi
# PicasaPy-mentések sorrendje, ezért ezeket olvasáskor migráljuk.
MEASURED_COLORFIX_ROWS = (
    ("colorfix=1,ffca3cff,-0.164578;", False, ("1", "-0.164578", "ffca3cff"), True),
    ("colorfix=1,ffca3cff,0.000000;", False, ("1", "0.000000", "ffca3cff"), True),
    ("colorfix=1,ffffffff,-0.164578;", False, ("1", "-0.164578", "ffffffff"), True),
    ("colorfix=1,ffffffff,0.400000;", False, ("1", "0.400000", "ffffffff"), True),
    ("colorfix=1,ffca3cff;", False, ("1", "0.000000", "ffca3cff"), True),
    ("colorfix=1,00ca3cff,-0.164578;", False, ("1", "-0.164578", "00ca3cff"), True),
    ("colorfix=1,ff4060ff,0.300000;", False, ("1", "0.300000", "ff4060ff"), True),
    ("colorfix=1;", False, ("1",), False),
    ("colorfix=1,0.500000,0.125000;", True, ("1", "0.500000", "0.125000"), True),
    ("colorfix=1,-0.164578,ffca3cff;", True, ("1", "-0.164578", "ffca3cff"), True),
)


def _native_result(image: np.ndarray, params: tuple[str, ...]) -> np.ndarray:
    """Független elvárt kép a már natív sorrendű rekordparaméterekből."""
    temperature = float(params[1]) if len(params) > 1 and params[1] else 0.0
    color = params[2] if len(params) > 2 else ""
    result = image
    if color:
        try:
            rgb = parse_rgb_hex(color)
        except ValueError:
            rgb = None
        if rgb is not None and rgb != (0, 0, 0):
            result = apply_autocolor_matrix(result, autocolor_matrix_16_16(*rgb))
    if temperature != 0.0:
        result = apply_native_colortemp(result, temperature, 0.0)
    return result.copy() if result is image else result


def _measured_picasa_applies(row: str) -> bool:
    fields = row.partition("=")[2].rstrip(";").split(",")
    if len(fields) < 2:
        return False
    try:
        float(fields[1])
    except ValueError:
        return False
    return True


@pytest.mark.parametrize(
    ("row", "picasa_applies", "native_params", "picasapy_applies"),
    MEASURED_COLORFIX_ROWS,
)
def test_measurement_rows_are_read_in_native_order(
    row, picasa_applies, native_params, picasapy_applies
):
    image = _photo()
    op, = parse_filters(row)

    assert op.params == native_params
    # A job-407 mintában a Picasa csak numerikus első paraméternél dolgozott.
    assert picasa_applies is _measured_picasa_applies(row)

    report = apply_filters(image, parse_filters_prefix(row))
    assert report.skipped == ()
    expected = _native_result(image, native_params)
    np.testing.assert_array_equal(report.image, expected)
    assert (not np.array_equal(report.image, image)) is picasapy_applies


def test_old_picasapy_order_is_written_back_as_native_order():
    old = "colorfix=1,ffca3cff,-0.164578;"

    session = EditSession.from_value(old)

    assert session.to_value() == "colorfix=1,-0.164578,ffca3cff;"
    assert serialize_filters_for_write(
        (FilterOp("colorfix", ("1", "ffca3cff", "-0.164578")),)
    ) == "colorfix=1,-0.164578,ffca3cff;"


def test_effect_panel_and_parameter_writer_use_native_order():
    params = effect_params("colorfix")

    assert tuple(param.key for param in params) == ("temperature", "whitepoint")
    assert tuple(param.kind for param in params) == ("slider", "color")
    formatted = format_param_values((0.3, "#336699"), params, effect="colorfix")
    assert formatted == ("0.300000", "ff336699")
    session = EditSession(ops=(FilterOp("colorfix", ("1", *formatted)),))
    assert session.to_value() == "colorfix=1,0.300000,ff336699;"


def test_whitept_measurement_control_still_applies_with_a_hex_color():
    image = _photo()
    report = apply_filters(image, parse_filters_prefix("whitept=1,ffca3cff;"))

    assert report.skipped == ()
    assert not np.array_equal(report.image, image)
