"""A Picasa mappák kézi sorrendjének átvétele a wordhash.dat-ból (#4889)."""

from __future__ import annotations

import logging
import struct

import pytest

from picasapy.pmpimport import PathRemapper, iter_photo_records
from picasapy.pmpimport.db3_atvetel import rekordokat_atvesz
from support.pmp_factory import build_pmp_column, build_thumb_index

_FOLDER_TOKEN = "]album:folder-token"
_ALBUM_TOKEN = "]album:album-token"
_FOLDER = r"C:\Users\felhasznalo\Pictures"


def _wordhash_bytes(entity_count: int, entries: tuple[tuple[str, tuple[int, ...]], ...]) -> bytes:
    """A #4884 spec szerinti kis, egy poolos, little-endian fájl."""
    pool = bytearray(0x10000)
    offsets: dict[str, int] = {}
    used = 0
    for word, _rows in entries:
        encoded = word.encode("utf-8") + b"\x00"
        offsets[word] = used
        pool[used : used + len(encoded)] = encoded
        used += len(encoded)

    blob = bytearray(
        struct.pack("<fIIII", 1.6, entity_count, 1, 0x10000, used)
    )
    blob.extend(pool)
    blob.extend(struct.pack("<I", len(entries)))
    for word, rows in entries:
        blob.extend(struct.pack("<II", offsets[word], len(rows)))
        blob.extend(struct.pack(f"<{len(rows)}I", *rows))
    return bytes(blob)


def _db3(tmp_path, *, wordhash: bytes | None = None):
    (tmp_path / "thumbindex.db").write_bytes(
        build_thumb_index(
            [
                (_FOLDER + "\\", None),  # 0: mappa
                ("a.jpg", 0),              # 1: fájl
                ("b.jpg", 0),              # 2: fájl
                ("c.jpg", 0),              # 3: fájl
                ("", 0),                   # 4: arcrekord, nem fájl
                ("", None),                # 5: törölt rekord, nem fájl
                ("other.jpg", None),       # 6: másik gyökér, nincs remap
            ]
        )
    )
    (tmp_path / "imagedata_caption.pmp").write_bytes(
        build_pmp_column(0x0, [""] * 7)
    )
    (tmp_path / "albumdata_filename.pmp").write_bytes(
        build_pmp_column(0x0, [_FOLDER, _FOLDER + "\\album"])
    )
    (tmp_path / "albumdata_token.pmp").write_bytes(
        build_pmp_column(0x0, [_FOLDER_TOKEN, _ALBUM_TOKEN])
    )
    (tmp_path / "albumdata_category.pmp").write_bytes(
        build_pmp_column(0x1, [2, 0])
    )
    if wordhash is not None:
        (tmp_path / "wordhash.dat").write_bytes(wordhash)


@pytest.fixture
def remapper(tmp_path):
    local_folder = tmp_path / "photos"
    local_folder.mkdir()
    for name in ("a.jpg", "b.jpg", "c.jpg"):
        (local_folder / name).write_bytes(b"synthetic photo")
    return PathRemapper.from_dict({_FOLDER: str(local_folder)})


def _rendezett_db3(tmp_path):
    _db3(
        tmp_path,
        wordhash=_wordhash_bytes(
            7,
            (
                (_FOLDER_TOKEN, (2, 1, 4, 3, 99)),
                # A kategória 0 albumlistája ebben a körben nem importálandó.
                (_ALBUM_TOKEN, (1, 2)),
            ),
        ),
    )


def _priority_ini(path):
    values = {}
    for section in path.read_text(encoding="utf-8").split("[")[1:]:
        name, _, body = section.partition("]")
        for line in body.splitlines():
            if line.startswith("priority="):
                values[name] = line.partition("=")[2]
    return values


def test_a_wordhash_az_entitasok_sorrendjet_orizve_olvassa(tmp_path):
    from picasapy.pmpimport.wordhash import read_wordhash

    path = tmp_path / "wordhash.dat"
    path.write_bytes(_wordhash_bytes(7, ((_FOLDER_TOKEN, (2, 1, 3)),)))

    assert read_wordhash(path, expected_entity_count=7) == {
        _FOLDER_TOKEN: (2, 1, 3)
    }


def test_a_mappalista_thumbindex_utvonalakbol_priority_sorrendet_ad(
    tmp_path, remapper, caplog
):
    _rendezett_db3(tmp_path)
    with caplog.at_level(logging.WARNING):
        records = iter_photo_records(tmp_path, remapper)

    priorities = {
        record.local_path.rsplit("/", 1)[-1]: record.manual_priority
        for record in records
    }
    assert priorities == {"a.jpg": 1.0, "b.jpg": 0.0, "c.jpg": 2.0}
    assert any("kihagyott" in record.getMessage().casefold() for record in caplog.records)

    report = rekordokat_atvesz(records, backup=False)
    assert report.sorrend == 3
    assert _priority_ini(tmp_path / "photos" / ".picasa.ini") == {
        "b.jpg": "0.0",
        "a.jpg": "1.0",
        "c.jpg": "2.0",
    }


def test_a_meglevo_mappasorrendet_teljesen_erintetlenul_hagyja(
    tmp_path, remapper
):
    _rendezett_db3(tmp_path)
    records = iter_photo_records(tmp_path, remapper)
    ini_path = tmp_path / "photos" / ".picasa.ini"
    ini_path.write_text(
        "[a.jpg]\npriority=40.0\n[b.jpg]\npriority=20.0\n", encoding="utf-8"
    )

    report = rekordokat_atvesz(records, backup=False)

    assert report.sorrend == 0
    assert _priority_ini(ini_path) == {"a.jpg": "40.0", "b.jpg": "20.0"}


def test_hibas_wordhash_nem_allitja_le_az_importot_es_naplozza(
    tmp_path, remapper, caplog
):
    _db3(tmp_path, wordhash=b"\xcd\xcc\xcc\x3f\x07\x00")

    with caplog.at_level(logging.WARNING):
        records = iter_photo_records(tmp_path, remapper)

    assert [record.local_path.rsplit("/", 1)[-1] for record in records] == [
        "a.jpg",
        "b.jpg",
        "c.jpg",
    ]
    assert all(record.manual_priority is None for record in records)
    assert any("wordhash" in record.getMessage().casefold() for record in caplog.records)


def test_csonka_wordhash_fajlt_format_hibakent_elutasitja(tmp_path):
    from picasapy.pmpimport.wordhash import WordHashFormatError, read_wordhash

    path = tmp_path / "wordhash.dat"
    path.write_bytes(_wordhash_bytes(7, ((_FOLDER_TOKEN, (2, 1)),))[:-1])

    with pytest.raises(WordHashFormatError):
        read_wordhash(path, expected_entity_count=7)
