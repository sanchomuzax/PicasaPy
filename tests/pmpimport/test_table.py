"""Logikai PMP-tábla összeállítása oszlopfájlokból (sparse oszlopok)."""

import pytest

from picasapy.pmpimport import PmpFormatError, read_table
from support.pmp_factory import build_pmp


@pytest.fixture()
def db_dir(tmp_path):
    (tmp_path / "imagedata_caption.pmp").write_bytes(build_pmp(0x0, ["első", "második"]))
    (tmp_path / "imagedata_rotate.pmp").write_bytes(build_pmp(0x1, [1, 2, 3]))
    (tmp_path / "imagedata_edit_width.pmp").write_bytes(build_pmp(0x1, [640]))
    (tmp_path / "albumdata_name.pmp").write_bytes(build_pmp(0x0, ["Album"]))
    return tmp_path


class TestReadTable:
    def test_collects_only_own_columns(self, db_dir):
        table = read_table(db_dir, "imagedata")
        assert set(table.columns) == {"caption", "rotate", "edit_width"}

    def test_row_count_is_longest_column(self, db_dir):
        # Sparse táblák: a tábla hossza = a leghosszabb oszlop.
        assert read_table(db_dir, "imagedata").row_count == 3

    def test_row_skips_missing_sparse_values(self, db_dir):
        table = read_table(db_dir, "imagedata")
        assert table.row(0) == {"caption": "első", "rotate": 1, "edit_width": 640}
        assert table.row(2) == {"rotate": 3}

    def test_row_out_of_range_raises(self, db_dir):
        with pytest.raises(IndexError):
            read_table(db_dir, "imagedata").row(3)

    def test_missing_table_is_empty(self, db_dir):
        table = read_table(db_dir, "catdata")
        assert table.row_count == 0
        assert table.columns == {}

    def test_corrupt_column_raises_with_filename(self, db_dir):
        (db_dir / "imagedata_broken.pmp").write_bytes(b"\x00" * 8)
        with pytest.raises(PmpFormatError, match="imagedata_broken.pmp"):
            read_table(db_dir, "imagedata")
