"""thumbindex.db olvasó — spec: docs/reference-repos-audit.md."""

import pytest

from picasapy.pmpimport import EntryKind, PmpFormatError, parse_thumbindex, read_thumbindex
from support.pmp_factory import build_thumbindex


def _sample() -> bytes:
    return build_thumbindex(
        [
            ("C:\\Users\\anna\\Képek\\", None),  # 0: mappa
            ("nyaralás.jpg", 0),  # 1: fájl
            ("tél.jpg", 0),  # 2: fájl
            ("", None),  # 3: törölt
            ("", 1),  # 4: arc-rekord az 1-es képhez
        ]
    )


class TestParse:
    def test_entry_kinds(self):
        index = parse_thumbindex(_sample())
        kinds = [entry.kind for entry in index.entries]
        assert kinds == [
            EntryKind.FOLDER,
            EntryKind.FILE,
            EntryKind.FILE,
            EntryKind.DELETED,
            EntryKind.FACE,
        ]

    def test_path_resolution(self):
        index = parse_thumbindex(_sample())
        assert index.path_of(1) == "C:\\Users\\anna\\Képek\\nyaralás.jpg"
        assert index.path_of(0) == "C:\\Users\\anna\\Képek\\"

    def test_deleted_and_face_have_no_path(self):
        index = parse_thumbindex(_sample())
        assert index.path_of(3) is None
        # Az arc-rekord útvonala a szülőképé.
        assert index.path_of(4) == "C:\\Users\\anna\\Képek\\nyaralás.jpg"

    def test_bad_magic_raises(self):
        data = build_thumbindex([("x", None)], magic=0x12345678)
        with pytest.raises(PmpFormatError):
            parse_thumbindex(data)

    def test_truncated_raises(self):
        with pytest.raises(PmpFormatError):
            parse_thumbindex(_sample()[:-10])

    def test_ff_terminated_name(self):
        # Élesben 0xff-terminált nevek is előfordulnak.
        data = build_thumbindex([("mappa\\", None)], terminator=b"\xff")
        index = parse_thumbindex(data)
        assert index.entries[0].name == "mappa\\"

    def test_out_of_range_parent_raises(self):
        data = build_thumbindex([("kép.jpg", 7)])
        with pytest.raises(PmpFormatError):
            parse_thumbindex(data)


class TestReadFile:
    def test_reads_from_disk(self, tmp_path):
        path = tmp_path / "thumbindex.db"
        path.write_bytes(_sample())
        index = read_thumbindex(path)
        assert len(index.entries) == 5
