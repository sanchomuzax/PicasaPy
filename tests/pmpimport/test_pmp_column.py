"""read_pmp_column: .pmp oszlopfájl olvasása (#1)."""

import struct

import pytest

from picasapy.pmpimport.pmp_column import PmpFormatError, read_pmp_column
from support.pmp_factory import build_pmp_column


class TestStringColumn:
    def test_reads_values_in_order(self, tmp_path):
        path = tmp_path / "caption.pmp"
        path.write_bytes(build_pmp_column(0x6, ["első kép", "második", ""]))
        column = read_pmp_column(path)
        assert column.field_type == 0x6
        assert column.values == ("első kép", "második", "")
        assert len(column) == 3


class TestUint32Column:
    def test_reads_values_in_order(self, tmp_path):
        path = tmp_path / "rotate.pmp"
        path.write_bytes(build_pmp_column(0x1, [0, 90, 180, 270]))
        column = read_pmp_column(path)
        assert column.values == (0, 90, 180, 270)


class TestUint64Column:
    def test_reads_crop64_style_values(self, tmp_path):
        path = tmp_path / "crop64.pmp"
        path.write_bytes(build_pmp_column(0x4, [0, 0x1999333366668000]))
        column = read_pmp_column(path)
        assert column.values == (0, 0x1999333366668000)


class TestDoubleColumn:
    def test_reads_ole_time_style_values(self, tmp_path):
        path = tmp_path / "date.pmp"
        path.write_bytes(build_pmp_column(0x2, [45000.5]))
        column = read_pmp_column(path)
        assert column.values == (45000.5,)


class TestUint8AndUint16Columns:
    def test_uint8(self, tmp_path):
        path = tmp_path / "star.pmp"
        path.write_bytes(build_pmp_column(0x3, [0, 1, 1]))
        assert read_pmp_column(path).values == (0, 1, 1)

    def test_uint16(self, tmp_path):
        path = tmp_path / "colorspace.pmp"
        path.write_bytes(build_pmp_column(0x5, [1, 2, 3]))
        assert read_pmp_column(path).values == (1, 2, 3)


class TestEmptyColumn:
    def test_zero_records_is_fine(self, tmp_path):
        path = tmp_path / "facerect.pmp"
        path.write_bytes(build_pmp_column(0x4, []))
        column = read_pmp_column(path)
        assert column.values == ()
        assert len(column) == 0


class TestNonUtf8Names:
    def test_invalid_utf8_logs_warning(self, tmp_path, caplog):
        # nem-UTF-8 bájtsorozat: errors="replace" csendben ne rontsa el —
        # legalább egy WARNING szintű naplóbejegyzés kell
        path = tmp_path / "caption.pmp"
        header = struct.pack(
            "<IHHIHHI", 0x3FCCCCCD, 0x6, 0x1332, 0x00000002, 0x6, 0x1332, 1
        )
        body = b"\xff\xfe\x00"  # ervenytelen UTF-8 + lezaro 0x00
        path.write_bytes(header + body)
        with caplog.at_level("WARNING"):
            column = read_pmp_column(path)
        assert "�" in column.values[0]
        assert any(
            record.levelname == "WARNING" for record in caplog.records
        )


class TestCorruptHeader:
    def test_wrong_magic_raises(self, tmp_path):
        path = tmp_path / "bad.pmp"
        raw = bytearray(build_pmp_column(0x1, [1, 2]))
        raw[0:4] = struct.pack("<I", 0xDEADBEEF)
        path.write_bytes(bytes(raw))
        with pytest.raises(PmpFormatError):
            read_pmp_column(path)

    def test_mismatched_type_repeat_raises(self, tmp_path):
        path = tmp_path / "bad.pmp"
        raw = bytearray(build_pmp_column(0x1, [1, 2]))
        raw[12:14] = struct.pack("<H", 0x9)  # type1-ismétlés eltér
        path.write_bytes(bytes(raw))
        with pytest.raises(PmpFormatError):
            read_pmp_column(path)

    def test_truncated_header_raises(self, tmp_path):
        path = tmp_path / "bad.pmp"
        path.write_bytes(b"\x00" * 10)
        with pytest.raises(PmpFormatError):
            read_pmp_column(path)

    def test_truncated_records_raises(self, tmp_path):
        path = tmp_path / "bad.pmp"
        full = build_pmp_column(0x1, [1, 2, 3, 4])
        path.write_bytes(full[:-2])  # az utolsó rekord csonka
        with pytest.raises(PmpFormatError):
            read_pmp_column(path)

    def test_unterminated_string_raises(self, tmp_path):
        path = tmp_path / "bad.pmp"
        full = build_pmp_column(0x6, ["a", "b"])
        path.write_bytes(full[:-1])  # az utolsó lezáró 0x00 hiányzik
        with pytest.raises(PmpFormatError):
            read_pmp_column(path)

    def test_unknown_field_type_raises(self, tmp_path):
        path = tmp_path / "bad.pmp"
        header = struct.pack(
            "<IHHIHHI", 0x3FCCCCCD, 0x9, 0x1332, 0x00000002, 0x9, 0x1332, 0
        )
        path.write_bytes(header)
        with pytest.raises(PmpFormatError):
            read_pmp_column(path)
