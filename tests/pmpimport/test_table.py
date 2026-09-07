"""read_table: logikai PMP-tábla sparse oszlopokkal (#1)."""

import pytest

from picasapy.pmpimport.pmp_column import PmpFormatError
from picasapy.pmpimport.table import read_table
from support.pmp_factory import build_pmp_column


class TestReadTable:
    def test_joins_columns_by_name(self, tmp_path):
        # #2521: a hiteles típus mindkét oszlopnál `0x00` (ytString) —
        # a `rotate` is a `.picasa.ini`-beli `rotate(N)` alakot tárolja.
        (tmp_path / "imagedata_caption.pmp").write_bytes(
            build_pmp_column(0x0, ["első", "második", "harmadik"])
        )
        (tmp_path / "imagedata_rotate.pmp").write_bytes(
            build_pmp_column(0x0, ["rotate(0)", "rotate(1)", "rotate(3)"])
        )
        table = read_table(tmp_path, "imagedata")
        assert table.row_count == 3
        assert table.column("caption") == ("első", "második", "harmadik")
        assert table.column("rotate") == ("rotate(0)", "rotate(1)", "rotate(3)")

    def test_sparse_columns_padded_with_none(self, tmp_path):
        # élesben pl. filters=140661 vs facerect=7044 rekord — a rövidebb
        # oszlop hiányzó értékei None-ok
        (tmp_path / "imagedata_filters.pmp").write_bytes(
            build_pmp_column(0x0, ["enhance=1;", "", "crop64=1,abc;", ""])
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
            build_pmp_column(0x0, ["a", "b"])
        )
        table = read_table(tmp_path, "imagedata")
        assert table.value("star", 0) == 1
        assert table.value("star", 1) is None  # sparse kipótolás
        assert table.value("nincs-ilyen", 0) is None
        assert table.value("caption", 99) is None

    def test_ignores_other_tables_files(self, tmp_path):
        (tmp_path / "imagedata_caption.pmp").write_bytes(
            build_pmp_column(0x0, ["a"])
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

    def test_columns_field_is_immutable(self, tmp_path):
        # immutability-elv: a frozen dataclass NE tartalmazzon mutálható
        # dict mezőt — a `columns`-nak írásvédettnek kell lennie
        (tmp_path / "imagedata_caption.pmp").write_bytes(
            build_pmp_column(0x0, ["a"])
        )
        table = read_table(tmp_path, "imagedata")
        with pytest.raises(TypeError):
            table.columns["caption"] = ("modositva",)
