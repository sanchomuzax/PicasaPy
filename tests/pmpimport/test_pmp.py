"""PMP oszlopfájl-olvasó — spec: docs/reference-repos-audit.md."""

from datetime import datetime

import pytest

from picasapy.pmpimport import PmpFormatError, decode_ole_date, parse_pmp, read_pmp
from support.pmp_factory import build_pmp


class TestHeader:
    def test_field_type_and_count(self):
        column = parse_pmp(build_pmp(0x1, [10, 20, 30]), name="rotate")
        assert column.name == "rotate"
        assert column.field_type == 0x1
        assert column.values == (10, 20, 30)

    def test_bad_magic_raises(self):
        data = build_pmp(0x1, [1], magic=0xDEADBEEF)
        with pytest.raises(PmpFormatError):
            parse_pmp(data, name="rotate")

    def test_type_mismatch_raises(self):
        # A fejléc kétszer hordozza a típust — eltérés = sérült fájl.
        data = build_pmp(0x1, [1], type2=0x4)
        with pytest.raises(PmpFormatError):
            parse_pmp(data, name="rotate")

    def test_unknown_field_type_raises(self):
        data = build_pmp(0x1, [1], type2=0x9)
        data = data[:4] + b"\x09\x00" + data[6:]
        with pytest.raises(PmpFormatError):
            parse_pmp(data, name="rotate")

    def test_truncated_header_raises(self):
        with pytest.raises(PmpFormatError):
            parse_pmp(b"\xcd\xcc\xcc\x3f\x00", name="x")


class TestStringColumn:
    def test_null_terminated_utf8(self):
        data = build_pmp(0x0, ["alma", "körte", ""])
        column = parse_pmp(data, name="caption")
        assert column.values == ("alma", "körte", "")

    def test_type_6_is_also_string(self):
        column = parse_pmp(build_pmp(0x6, ["a", "b"]), name="tags")
        assert column.values == ("a", "b")

    def test_truncated_records_raise(self):
        data = build_pmp(0x0, ["a", "b"], count=3)
        with pytest.raises(PmpFormatError):
            parse_pmp(data, name="caption")


class TestNumericColumns:
    @pytest.mark.parametrize(
        ("field_type", "values"),
        [
            (0x1, (0, 4294967295)),
            (0x3, (0, 255)),
            (0x4, (0, 2**64 - 1)),
            (0x5, (0, 65535)),
            (0x7, (7, 42)),
        ],
    )
    def test_integer_types(self, field_type, values):
        column = parse_pmp(build_pmp(field_type, values), name="col")
        assert column.values == values

    def test_double_column(self):
        column = parse_pmp(build_pmp(0x2, [25569.0, 0.5]), name="date")
        assert column.values == (25569.0, 0.5)

    def test_truncated_numeric_raises(self):
        data = build_pmp(0x4, [1, 2])[:-3]
        with pytest.raises(PmpFormatError):
            parse_pmp(data, name="uid64")


class TestReadPmp:
    def test_reads_file_and_names_column(self, tmp_path):
        path = tmp_path / "imagedata_rotate.pmp"
        path.write_bytes(build_pmp(0x1, [1, 2]))
        column = read_pmp(path)
        assert column.name == "rotate"
        assert column.values == (1, 2)

    def test_name_keeps_extra_underscores(self, tmp_path):
        path = tmp_path / "imagedata_edit_width.pmp"
        path.write_bytes(build_pmp(0x1, [640]))
        assert read_pmp(path).name == "edit_width"


class TestOleDate:
    def test_epoch_1899_12_30(self):
        assert decode_ole_date(0.0) == datetime(1899, 12, 30)

    def test_unix_epoch(self):
        assert decode_ole_date(25569.0) == datetime(1970, 1, 1)

    def test_fractional_day(self):
        assert decode_ole_date(25569.5) == datetime(1970, 1, 1, 12, 0, 0)
