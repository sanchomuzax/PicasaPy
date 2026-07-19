"""read_table: logikai PMP-tábla sparse oszlopokkal (#1)."""

import pytest

from picasapy.pmpimport.pmp_column import PmpFormatError
from picasapy.pmpimport.table import read_table
from support.pmp_factory import build_pmp_column


class TestReadTable:
    def test_joins_columns_by_name(self, tmp_path):
        (tmp_path / "imagedata_caption.pmp").write_bytes(
            build_pmp_column(0x6, ["első", "második", "harmadik"])
        )
        (tmp_path / "imagedata_rotate.pmp").write_bytes(
            build_pmp_column(0x1, [0, 90, 270])
        )
        table = read_table(tmp_path, "imagedata")
        assert table.row_count == 3
        assert table.column("caption") == ("első", "második", "harmadik")
        assert table.column("rotate") == (0, 90, 270)

    def test_sparse_columns_padded_with_none(self, tmp_path):
        # élesben pl. filters=140661 vs facerect=7044 rekord — a rövidebb
        # oszlop hiányzó értékei None-ok
        (tmp_path / "imagedata_filters.pmp").write_bytes(
            build_pmp_column(0x6, ["enhance=1;", "", "crop64=1,abc;", ""])
        )
        (tmp_path / "imagedata_facerect.pmp").write_bytes(
            build_pmp_column(0x4, [0x1])
        )
        table = read_table(tmp_path, "imagedata")
        assert table.row_count == 4
        assert table.column("facerect") == (0x1, None, None, None)

    def test_value_accessor(self, tmp_path):
        (tmp_path / "imagedata_star.pmp").write_bytes(build_pmp_column(0x3, [1]))
        (tmp_path / "imagedata_caption.pmp").write_bytes(
            build_pmp_column(0x6, ["a", "b"])
        )
        table = read_table(tmp_path, "imagedata")
        assert table.value("star", 0) == 1
        assert table.value("star", 1) is None  # sparse kipótolás
        assert table.value("nincs-ilyen", 0) is None
        assert table.value("caption", 99) is None

    def test_ignores_other_tables_files(self, tmp_path):
        (tmp_path / "imagedata_caption.pmp").write_bytes(
            build_pmp_column(0x6, ["a"])
        )
        (tmp_path / "albumdata_name.pmp").write_bytes(
            build_pmp_column(0x6, ["Album"])
        )
        table = read_table(tmp_path, "imagedata")
        assert set(table.columns) == {"caption"}

    def test_missing_dir_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            read_table(tmp_path / "nincs", "imagedata")

    def test_no_columns_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            read_table(tmp_path, "imagedata")

    def test_corrupt_column_propagates(self, tmp_path):
        (tmp_path / "imagedata_caption.pmp").write_bytes(b"\x00" * 30)
        with pytest.raises(PmpFormatError):
            read_table(tmp_path, "imagedata")
