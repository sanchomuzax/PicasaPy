"""read_thumb_index / resolve_path: thumbindex.db olvasása (#1)."""

import struct

import pytest

from picasapy.pmpimport.thumbindex import (
    ThumbIndexFormatError,
    read_thumb_index,
    resolve_path,
)
from support.pmp_factory import build_thumb_index


class TestReadThumbIndex:
    def test_reads_entries_in_order(self, tmp_path):
        path = tmp_path / "thumbindex.db"
        path.write_bytes(
            build_thumb_index(
                [
                    ("C:\\Users\\anna\\Pictures\\", None),
                    ("IMG_0001.jpg", 0),
                    ("IMG_0002.jpg", 0),
                ]
            )
        )
        entries = read_thumb_index(path)
        assert [e.name for e in entries] == [
            "C:\\Users\\anna\\Pictures\\",
            "IMG_0001.jpg",
            "IMG_0002.jpg",
        ]
        assert entries[0].is_directory is True
        assert entries[1].is_directory is False
        assert entries[1].parent_index == 0

    def test_face_record_detection(self, tmp_path):
        # üres név + érvényes szülőindex = arc-rekord; üres név érvénytelen
        # szülővel = törölt fájl
        path = tmp_path / "thumbindex.db"
        path.write_bytes(
            build_thumb_index(
                [("C:\\kepek\\", None), ("a.jpg", 0), ("", 1), ("", None)]
            )
        )
        entries = read_thumb_index(path)
        assert entries[2].is_face_record is True
        assert entries[3].is_face_record is False  # törölt fájl

    def test_utf8_names(self, tmp_path):
        path = tmp_path / "thumbindex.db"
        path.write_bytes(
            build_thumb_index([("C:\\képek\\nyaralás\\", None), ("tópart.jpg", 0)])
        )
        entries = read_thumb_index(path)
        assert entries[1].name == "tópart.jpg"

    def test_empty_index(self, tmp_path):
        path = tmp_path / "thumbindex.db"
        path.write_bytes(build_thumb_index([]))
        assert read_thumb_index(path) == ()


class TestResolvePath:
    def test_file_joins_parent_directory(self, tmp_path):
        path = tmp_path / "thumbindex.db"
        path.write_bytes(
            build_thumb_index([("C:\\Users\\anna\\Pictures\\", None), ("a.jpg", 0)])
        )
        entries = read_thumb_index(path)
        assert resolve_path(entries, entries[1]) == "C:\\Users\\anna\\Pictures\\a.jpg"

    def test_directory_resolves_to_own_name(self, tmp_path):
        path = tmp_path / "thumbindex.db"
        path.write_bytes(build_thumb_index([("C:\\kepek\\", None)]))
        entries = read_thumb_index(path)
        assert resolve_path(entries, entries[0]) == "C:\\kepek\\"

    def test_parent_without_trailing_separator_gets_backslash(self, tmp_path):
        path = tmp_path / "thumbindex.db"
        path.write_bytes(build_thumb_index([("C:\\kepek", None), ("a.jpg", 0)]))
        entries = read_thumb_index(path)
        assert resolve_path(entries, entries[1]) == "C:\\kepek\\a.jpg"


class TestResolvePathBounds:
    def test_out_of_range_parent_index_raises(self, tmp_path):
        # sérült db3-nál a szülőindex kimutathat a bejegyzések tömbjéből —
        # nyers IndexError helyett dokumentált ThumbIndexFormatError kell
        path = tmp_path / "thumbindex.db"
        path.write_bytes(build_thumb_index([("C:\\kepek\\", None), ("a.jpg", 99)]))
        entries = read_thumb_index(path)
        with pytest.raises(ThumbIndexFormatError):
            resolve_path(entries, entries[1])


class TestNonUtf8Names:
    def test_invalid_utf8_name_logs_warning(self, tmp_path, caplog):
        # nem-UTF-8 fájlnév: errors="replace" csendben ne rontsa el —
        # legalább egy WARNING szintű naplóbejegyzés kell
        path = tmp_path / "thumbindex.db"
        header = struct.pack("<II", 0x40466666, 1)
        entry = (
            b"\x80\x81"  # ervenytelen UTF-8 nev (lone continuation byte-ok)
            + b"\x00"
            + b"\x00" * 26
            + struct.pack("<I", 0xFFFFFFFF)
        )
        path.write_bytes(header + entry)
        with caplog.at_level("WARNING"):
            entries = read_thumb_index(path)
        assert "�" in entries[0].name
        assert any(
            record.levelname == "WARNING" for record in caplog.records
        )


class TestCorruptIndex:
    def test_wrong_magic_raises(self, tmp_path):
        path = tmp_path / "thumbindex.db"
        raw = bytearray(build_thumb_index([("C:\\kepek\\", None)]))
        raw[0:4] = struct.pack("<I", 0xDEADBEEF)
        path.write_bytes(bytes(raw))
        with pytest.raises(ThumbIndexFormatError):
            read_thumb_index(path)

    def test_truncated_header_raises(self, tmp_path):
        path = tmp_path / "thumbindex.db"
        path.write_bytes(b"\x00" * 4)
        with pytest.raises(ThumbIndexFormatError):
            read_thumb_index(path)

    def test_truncated_entry_raises(self, tmp_path):
        path = tmp_path / "thumbindex.db"
        full = build_thumb_index([("C:\\kepek\\", None), ("a.jpg", 0)])
        path.write_bytes(full[:-3])  # az utolsó szülőindex csonka
        with pytest.raises(ThumbIndexFormatError):
            read_thumb_index(path)
