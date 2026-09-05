"""read_thumb_index / resolve_path: thumbindex.db olvasása (#1)."""

import logging
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
    """#2404: sérült szülő-hivatkozásnál NEM dobunk — az eredeti sem.

    Korábban `ThumbIndexFormatError`-t adtunk. Egy kivétel viszont az EGÉSZ
    importot megállítaná egyetlen sérült bejegyzés miatt, miközben a többi
    ezer hibátlan. Az eredeti tartalék szövegre esik vissza; mi a bejegyzés
    saját nevét adjuk, és naplózunk — a hiba tehát nem lesz néma.
    """

    def test_a_tartomanyon_kivuli_szulo_NEM_dob(self, tmp_path, caplog):
        path = tmp_path / "thumbindex.db"
        path.write_bytes(build_thumb_index([("C:\\kepek\\", None), ("a.jpg", 99)]))
        entries = read_thumb_index(path)

        with caplog.at_level(logging.WARNING):
            eredmeny = resolve_path(entries, entries[1])

        assert eredmeny == "a.jpg"
        assert any("99" in r.getMessage() for r in caplog.records), (
            "a sérült szülőindexet naplózni KELL — némán elnyelni rosszabb, "
            "mint a régi kivétel"
        )

    def test_az_URES_slot_szulo_sem_dob(self, tmp_path, caplog):
        """`kind == 0` = üres slot: nincs mit a név elé fűzni."""
        path = tmp_path / "thumbindex.db"
        path.write_bytes(
            build_thumb_index([("", None, 0, 1), ("a.jpg", 0, 2, 1)])
        )
        entries = read_thumb_index(path)

        with caplog.at_level(logging.WARNING):
            eredmeny = resolve_path(entries, entries[1])

        assert eredmeny == "a.jpg"
        assert any("ÜRES" in r.getMessage() for r in caplog.records)


class TestATipusmezoDont2404:
    """A mért szabály: a `valid` bájt és a TÍPUS dönt, nem a szülőindex."""

    @pytest.mark.parametrize("tipus", [1, 5, 25, 1001])
    def test_a_teljes_utvonal_tipusoknal_a_nev_all(self, tmp_path, tipus):
        """A `25` jelentése NINCS MEG — a halmaz attól még a binárisé."""
        path = tmp_path / "thumbindex.db"
        path.write_bytes(
            build_thumb_index(
                [("C:\\kepek\\", None), ("mar_teljes.jpg", 0, tipus, 1)]
            )
        )
        entries = read_thumb_index(path)
        assert resolve_path(entries, entries[1]) == "mar_teljes.jpg"

    def test_a_valid_nulla_eseten_is_a_nev_all(self, tmp_path):
        path = tmp_path / "thumbindex.db"
        path.write_bytes(
            build_thumb_index([("C:\\kepek\\", None), ("a.jpg", 0, 2, 0)])
        )
        entries = read_thumb_index(path)
        assert resolve_path(entries, entries[1]) == "a.jpg"

    def test_a_RENDES_eset_valtozatlan(self, tmp_path):
        """Ami eddig is működött, annak működnie kell: `valid=1`, `kind=2`."""
        path = tmp_path / "thumbindex.db"
        path.write_bytes(
            build_thumb_index([("C:\\kepek\\", None), ("a.jpg", 0, 2, 1)])
        )
        entries = read_thumb_index(path)
        assert resolve_path(entries, entries[1]) == "C:\\kepek\\a.jpg"

    def test_az_arcsablon_a_TIPUSROL_ismerheto_fel(self, tmp_path):
        """`kind == 1001` — a szülőlekérdező ennél rövidre zár (FUN_004e2990),
        tehát a `parent_index` mezője ott nem is szülőindex."""
        path = tmp_path / "thumbindex.db"
        path.write_bytes(
            build_thumb_index(
                [("C:\\kepek\\", None), ("van_neve", 0, 1001, 1)]
            )
        )
        entries = read_thumb_index(path)

        assert entries[1].is_face_record is True, (
            "a típus akkor is arcsablont jelent, ha a névmező NEM üres — "
            "a régi heurisztika (üres név) ezt nem fogta meg"
        )

    def test_az_ures_nev_masodlagos_tartalek_marad(self, tmp_path):
        path = tmp_path / "thumbindex.db"
        path.write_bytes(
            build_thumb_index([("C:\\kepek\\", None), ("", 0, 2, 1)])
        )
        entries = read_thumb_index(path)
        assert entries[1].is_face_record is True


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
